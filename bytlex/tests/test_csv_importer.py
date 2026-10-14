"""
Pytest Test Suite: CSV Ingestion, Validation Engine, and Upsert Integrity
"""

import pytest
import pandas as pd
from src.csv_importer import (
    auto_map_columns,
    validate_csv_rows,
    execute_csv_import,
)
from src.database import get_student_by_id, init_database


@pytest.fixture(autouse=True)
def setup_db(tmp_path):
    db_path = str(tmp_path / "campusiq-csv-test.db")
    init_database(db_path)
    return db_path


def test_auto_map_columns():
    headers = ["Student_ID", "Full_Name", "CGPA_Score", "Overall_Attendance"]
    mapping = auto_map_columns(headers, "academic_records")
    assert mapping.get("student_id") == "Student_ID"
    assert mapping.get("cgpa") == "CGPA_Score"


def test_validate_csv_valid_rows():
    df = pd.DataFrame([
        {"student_id": "TEST_001", "cgpa": "8.5", "marks_percentage": "85.0", "backlog_count": "0"},
        {"student_id": "TEST_002", "cgpa": "7.2", "marks_percentage": "72.0", "backlog_count": "1"},
    ])
    mapping = {"student_id": "student_id", "cgpa": "cgpa", "marks_percentage": "marks_percentage", "backlog_count": "backlog_count"}
    valid, errors = validate_csv_rows(df, mapping, "academic_records")

    assert len(valid) == 2
    assert len(errors) == 0
    assert valid[0]["cgpa"] == 8.5


def test_validate_csv_out_of_bounds_errors():
    df = pd.DataFrame([
        {"student_id": "TEST_003", "cgpa": "14.5", "marks_percentage": "70.0", "backlog_count": "0"},  # CGPA > 10
        {"student_id": "", "cgpa": "7.5", "marks_percentage": "75.0", "backlog_count": "0"},          # Empty ID
        {"student_id": "TEST_004", "cgpa": "8.0", "marks_percentage": "80.0", "backlog_count": "-2"}, # Negative backlogs
    ])
    mapping = {"student_id": "student_id", "cgpa": "cgpa", "marks_percentage": "marks_percentage", "backlog_count": "backlog_count"}
    valid, errors = validate_csv_rows(df, mapping, "academic_records")

    assert len(valid) == 0
    assert len(errors) == 3
    assert any("exceeds maximum" in e["error"] for e in errors)
    assert any("empty or invalid" in e["error"] for e in errors)
    assert any("below minimum" in e["error"] for e in errors)


def test_execute_csv_import_upsert(setup_db):
    admin_user = {"id": "user_admin_01", "email": "admin@campus.edu", "role": "admin"}
    # Ingest a new student
    rows = [{"student_id": "UPSERT_STU_99", "name": "Upsert Student", "cgpa": 8.75, "marks_percentage": 88.0, "attendance_overall": 92.0}]
    res = execute_csv_import(
        rows,
        "student_master",
        "test_import.csv",
        1,
        0,
        current_user=admin_user,
        db_path=setup_db,
    )

    assert res["status"] in ["Completed", "Partial"]
    record = get_student_by_id("UPSERT_STU_99", db_path=setup_db)
    assert record is not None
    assert record["name"] == "Upsert Student"

    # Now update the same student with new CGPA
    update_rows = [{"student_id": "UPSERT_STU_99", "cgpa": 9.10}]
    update_res = execute_csv_import(
        update_rows,
        "academic_records",
        "update_import.csv",
        1,
        0,
        current_user=admin_user,
        db_path=setup_db,
    )
    assert update_res["updated"] >= 1

    updated_record = get_student_by_id("UPSERT_STU_99", db_path=setup_db)
    assert updated_record["cgpa"] == 9.10


def test_csv_import_requires_administrator():
    with pytest.raises(PermissionError):
        execute_csv_import(
            [{"student_id": "NO_IMPORT", "name": "No Import"}],
            "student_master",
            "test.csv",
            1,
            0,
            current_user={"id": "staff", "role": "staff"},
        )
