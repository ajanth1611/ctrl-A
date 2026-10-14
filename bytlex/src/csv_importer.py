"""
CampusIQ: CSV Ingestion, Schema Mapping, Validation, and Integration Engine
Handles multi-dataset ingestion with row-level auditing, data type checks,
and atomic database upserts.
"""

from typing import Dict, List, Tuple, Any, Optional
import io
import pandas as pd
import numpy as np
from src.database import sync_students_to_db, log_import_job, get_student_by_id, get_all_students
from src.analytics import process_student_pipeline, DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS

DATASET_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "student_master": {
        "label": "Student Master Data",
        "description": "Student ID, Name, Email, Department, and Semester.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "name": {"label": "Student Name", "required": True, "type": "str"},
            "email": {"label": "Email Address", "required": False, "type": "str"},
            "department": {"label": "Department", "required": True, "type": "str"},
            "semester": {"label": "Semester (1-8)", "required": True, "type": "int", "min": 1, "max": 8},
            "placement_status": {"label": "Placement Status", "required": False, "type": "str"},
        },
    },
    "academic_records": {
        "label": "Academic Records",
        "description": "Semester marks, cumulative CGPA (0.0-10.0), and active backlog counts.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "cgpa": {"label": "CGPA (0.0 - 10.0)", "required": True, "type": "float", "min": 0.0, "max": 10.0},
            "marks_percentage": {"label": "Marks % (0 - 100)", "required": True, "type": "float", "min": 0.0, "max": 100.0},
            "backlog_count": {"label": "Backlog Count", "required": False, "type": "int", "min": 0},
        },
    },
    "attendance_records": {
        "label": "Classroom Attendance Records",
        "description": "Overall attendance percentage (0.0-100.0) and subject breakdown.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "attendance_overall": {"label": "Overall Attendance %", "required": True, "type": "float", "min": 0.0, "max": 100.0},
            "attendance_math": {"label": "Math Attendance %", "required": False, "type": "float", "min": 0.0, "max": 100.0},
            "attendance_core": {"label": "Core Attendance %", "required": False, "type": "float", "min": 0.0, "max": 100.0},
            "attendance_lab": {"label": "Lab Attendance %", "required": False, "type": "float", "min": 0.0, "max": 100.0},
        },
    },
    "lms_records": {
        "label": "LMS Engagement Records",
        "description": "Weekly portal login frequency and assignment completion percentage.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "lms_login_frequency": {"label": "Weekly Logins", "required": True, "type": "int", "min": 0},
            "lms_assignment_completion": {"label": "Assignment Completion %", "required": True, "type": "float", "min": 0.0, "max": 100.0},
        },
    },
    "placement_assessments": {
        "label": "Placement Assessments",
        "description": "Quantitative aptitude, coding, and mock interview assessment scores.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "aptitude_score": {"label": "Aptitude Score", "required": True, "type": "float", "min": 0.0, "max": 100.0},
            "coding_score": {"label": "Coding Score", "required": True, "type": "float", "min": 0.0, "max": 100.0},
            "mock_interview_score": {"label": "Mock Interview Score", "required": True, "type": "float", "min": 0.0, "max": 100.0},
        },
    },
    "skills_assessments": {
        "label": "Technical Skills & Extracurriculars",
        "description": "Technical practical assessments and extracurricular involvement.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "technical_skills_score": {"label": "Technical Skills Score", "required": True, "type": "float", "min": 0.0, "max": 100.0},
            "extracurricular_score": {"label": "Extracurricular Score", "required": False, "type": "float", "min": 0.0, "max": 100.0},
        },
    },
    "student_feedback": {
        "label": "Student Feedback & Notes",
        "description": "Institutional feedback rating (1.0-5.0) and mentoring notes.",
        "fields": {
            "student_id": {"label": "Student ID", "required": True, "type": "str"},
            "student_feedback_score": {"label": "Satisfaction Rating (1-5)", "required": True, "type": "float", "min": 1.0, "max": 5.0},
            "faculty_notes": {"label": "Faculty Mentoring Notes", "required": False, "type": "str"},
        },
    },
}


def auto_map_columns(csv_headers: List[str], dataset_type: str) -> Dict[str, str]:
    """Generates fuzzy column mappings between CSV headers and expected target schema."""
    schema = DATASET_SCHEMAS.get(dataset_type, {}).get("fields", {})
    mapping = {}

    for target_key in schema.keys():
        cleaned_target = target_key.lower().replace("_", "").replace(" ", "")
        matched_header = ""
        for h in csv_headers:
            cleaned_h = h.lower().replace("_", "").replace(" ", "")
            if cleaned_h == cleaned_target or cleaned_target in cleaned_h or cleaned_h in cleaned_target:
                matched_header = h
                break
        if matched_header:
            mapping[target_key] = matched_header

    return mapping


def validate_csv_rows(
    df_raw: pd.DataFrame,
    mapping: Dict[str, str],
    dataset_type: str,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Validates CSV rows against schema constraints, data types, and range boundaries.
    Returns (valid_rows, error_rows).
    """
    schema = DATASET_SCHEMAS.get(dataset_type, {}).get("fields", {})
    valid_rows = []
    error_rows = []

    id_col = mapping.get("student_id")
    if not id_col or id_col not in df_raw.columns:
        # All rows invalid if student ID column not mapped
        for i, row in df_raw.iterrows():
            error_rows.append({
                "row_index": i + 1,
                "student_id": "UNKNOWN",
                "error": "Missing mapping for required 'student_id' column.",
                "raw_data": row.to_dict(),
            })
        return valid_rows, error_rows

    for i, row in df_raw.iterrows():
        row_num = i + 1
        s_id = str(row.get(id_col, "")).strip()

        if not s_id or s_id.lower() == "nan":
            error_rows.append({
                "row_index": row_num,
                "student_id": "MISSING",
                "error": "Student ID is empty or invalid.",
                "raw_data": row.to_dict(),
            })
            continue

        row_errors = []
        parsed_row = {"student_id": s_id}

        for target_field, spec in schema.items():
            if target_field == "student_id":
                continue

            csv_col = mapping.get(target_field)
            if not csv_col or csv_col not in df_raw.columns:
                if spec.get("required"):
                    row_errors.append(f"Required field '{spec['label']}' is not mapped.")
                continue

            val = row.get(csv_col)
            if pd.isna(val) or str(val).strip() == "":
                if spec.get("required"):
                    row_errors.append(f"Required field '{spec['label']}' is missing.")
                continue

            # Type & Range validation
            field_type = spec.get("type")
            try:
                if field_type in ["float", "int"]:
                    num_val = float(val) if field_type == "float" else int(float(val))
                    if "min" in spec and num_val < spec["min"]:
                        row_errors.append(f"{spec['label']} value ({num_val}) is below minimum {spec['min']}.")
                    if "max" in spec and num_val > spec["max"]:
                        row_errors.append(f"{spec['label']} value ({num_val}) exceeds maximum {spec['max']}.")
                    parsed_row[target_field] = num_val
                else:
                    parsed_row[target_field] = str(val).strip()
            except (ValueError, TypeError):
                row_errors.append(f"{spec['label']} must be a valid numeric {field_type} (got '{val}').")

        if row_errors:
            error_rows.append({
                "row_index": row_num,
                "student_id": s_id,
                "error": " | ".join(row_errors),
                "raw_data": row.to_dict(),
            })
        else:
            valid_rows.append(parsed_row)

    return valid_rows, error_rows


def execute_csv_import(
    valid_rows: List[Dict[str, Any]],
    dataset_type: str,
    filename: str,
    total_raw_count: int,
    invalid_count: int,
    current_user: Optional[Dict[str, Any]] = None,
    db_path: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executes conflict-safe upsert into database, re-runs the scoring pipeline,
    and logs the audit record.
    """
    if not current_user or current_user.get("role") != "admin":
        raise PermissionError("Only administrators can import student data.")

    database_path = db_path

    if not valid_rows:
        job_id = log_import_job(
            dataset_type,
            filename,
            total_raw_count,
            0,
            invalid_count,
            0,
            0,
            "Failed",
            **({"db_path": database_path} if database_path else {}),
            current_user=current_user,
        )
        return {
            "job_id": job_id,
            "status": "Failed",
            "inserted": 0,
            "updated": 0,
            "invalid": invalid_count,
            "total": total_raw_count,
        }

    valid_df = pd.DataFrame(valid_rows)
    existing_df = get_all_students(
        current_user=current_user,
        **({"db_path": database_path} if database_path else {}),
    )

    # Determine inserts vs updates
    existing_ids = set(existing_df["student_id"].astype(str)) if not existing_df.empty else set()
    import_ids = set(valid_df["student_id"].astype(str))

    updated_count = len(import_ids.intersection(existing_ids))
    inserted_count = len(import_ids - existing_ids)

    # Sync to database
    sync_students_to_db(
        valid_df,
        current_user=current_user,
        **({"db_path": database_path} if database_path else {}),
    )

    # Re-fetch merged students and recalculate all success scores
    all_merged = get_all_students(
        current_user=current_user,
        **({"db_path": database_path} if database_path else {}),
    )
    scored_df, _ = process_student_pipeline(all_merged, DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS)
    sync_students_to_db(
        scored_df,
        current_user=current_user,
        **({"db_path": database_path} if database_path else {}),
    )

    status = "Completed" if invalid_count == 0 else "Partial"
    job_id = log_import_job(
        dataset_type,
        filename,
        total_raw_count,
        len(valid_rows),
        invalid_count,
        inserted_count,
        updated_count,
        status,
        **({"db_path": database_path} if database_path else {}),
        current_user=current_user,
    )

    return {
        "job_id": job_id,
        "status": status,
        "inserted": inserted_count,
        "updated": updated_count,
        "invalid": invalid_count,
        "total": total_raw_count,
    }
