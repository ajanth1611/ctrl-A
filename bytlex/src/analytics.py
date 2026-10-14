"""
CampusIQ: Centralized Analytics, Scoring, and Risk Assessment Engine
Implements explainable formulas, risk flags, student segmentation, and intervention recommendations.
"""

from typing import Dict, List, Tuple, Any, Optional
import numpy as np
import pandas as pd


# ==============================================================================
# 1. DEFAULT WEIGHTS & THRESHOLDS CONFIGURATION
# ==============================================================================
# Transparent weights summing to 100% (1.0)
DEFAULT_WEIGHTS = {
    "academic": 0.30,
    "attendance": 0.20,
    "lms": 0.15,
    "placement": 0.20,
    "skills": 0.10,
    "engagement_feedback": 0.05,
}

DEFAULT_THRESHOLDS = {
    "cgpa_min": 6.5,
    "marks_min": 60.0,
    "attendance_min": 75.0,
    "lms_assign_min": 65.0,
    "lms_login_min": 5,
    "coding_min": 50.0,
    "aptitude_min": 50.0,
    "mock_interview_min": 50.0,
    "tech_skills_min": 55.0,
    "high_risk_max_score": 50.0,
    "medium_risk_max_score": 70.0,
}


def validate_weights(weights: Dict[str, float]) -> Tuple[bool, float, Optional[str]]:
    """
    Validates whether user-supplied weights are non-negative and sum to 100% (or 1.0).
    Returns (is_valid, normalized_sum, error_message).
    """
    total = sum(weights.values())
    norm_sum = total if total > 1.5 else total * 100.0
    
    for key, val in weights.items():
        if val < 0:
            return False, norm_sum, f"Weight for '{key}' cannot be negative."
            
    if abs(norm_sum - 100.0) > 0.5:
        return False, norm_sum, f"Weights must total 100% (currently {norm_sum:.1f}%)."
        
    return True, norm_sum, None


# ==============================================================================
# 2. DATA VALIDATION & CLEANING
# ==============================================================================
def validate_and_clean_data(df_raw: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Validates required columns, reports missing values, deduplicates student IDs,
    and imputes sensible institutional defaults for unpopulated fields.
    """
    report = {
        "initial_rows": len(df_raw),
        "duplicate_ids_removed": 0,
        "missing_values_imputed": {},
        "warnings": [],
        "is_valid": True,
    }

    if df_raw.empty:
        report["warnings"].append("Provided dataset is empty.")
        report["is_valid"] = False
        return pd.DataFrame(), report

    df = df_raw.copy()

    # Deduplicate student_id if present
    if "student_id" in df.columns:
        init_len = len(df)
        df = df.drop_duplicates(subset=["student_id"], keep="first")
        removed_dups = init_len - len(df)
        report["duplicate_ids_removed"] = removed_dups
        if removed_dups > 0:
            report["warnings"].append(f"Removed {removed_dups} duplicate student ID(s).")
    else:
        df["student_id"] = [f"STU{2021000 + i + 1}" for i in range(len(df))]
        report["warnings"].append("Missing 'student_id' column: Generated synthetic IDs.")

    # Required numeric fields with default institutional fallbacks
    numeric_defaults = {
        "cgpa": 7.0,
        "marks_percentage": 70.0,
        "backlog_count": 0,
        "attendance_overall": 80.0,
        "lms_assignment_completion": 80.0,
        "lms_login_frequency": 10,
        "extracurricular_score": 50.0,
        "technical_skills_score": 65.0,
        "aptitude_score": 65.0,
        "coding_score": 60.0,
        "mock_interview_score": 60.0,
        "student_feedback_score": 4.0,
    }

    for col, default_val in numeric_defaults.items():
        if col not in df.columns:
            df[col] = default_val
            report["missing_values_imputed"][col] = len(df)
        else:
            missing_count = int(df[col].isna().sum())
            if missing_count > 0:
                report["missing_values_imputed"][col] = missing_count
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default_val)

    # String defaults
    if "name" not in df.columns:
        df["name"] = [f"Student {i+1}" for i in range(len(df))]
    else:
        df["name"] = df["name"].fillna("Unknown Student")

    if "department" not in df.columns:
        df["department"] = "Computer Science & Engineering"
    else:
        df["department"] = df["department"].fillna("General Engineering")

    if "semester" not in df.columns:
        df["semester"] = 5
    else:
        df["semester"] = pd.to_numeric(df["semester"], errors="coerce").fillna(5).astype(int)

    report["final_rows"] = len(df)
    return df, report


# ==============================================================================
# 3. NORMALIZED INDICATOR SUB-SCORES
# ==============================================================================
def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalizes student performance dimensions to a transparent 0-100 scale:
      1. Academic: 70% normalized CGPA + 30% Marks % - (Backlogs * 12 penalty)
      2. Attendance: Overall attendance percentage
      3. LMS Activity: 40% Login score + 60% Assignment completion rate
      4. Placement Readiness: 35% Aptitude + 40% Coding + 25% Mock interview
      5. Skills & Extracurriculars: 60% Technical Skills + 40% Extracurricular
      6. Student Feedback: Normalized feedback score (1.0-5.0 scale to 0-100)
    """
    df = df.copy()

    # 1. Academic Indicator (0-100)
    cgpa_norm = df["cgpa"] * 10.0
    marks_norm = df["marks_percentage"]
    backlog_penalty = df["backlog_count"] * 12.0
    df["indicator_academic"] = np.clip(
        0.70 * cgpa_norm + 0.30 * marks_norm - backlog_penalty, 0.0, 100.0
    ).round(1)

    # 2. Attendance Indicator (0-100)
    df["indicator_attendance"] = np.clip(df["attendance_overall"], 0.0, 100.0).round(1)

    # 3. LMS Activity Indicator (0-100)
    # 20 logins/week represents full score benchmark
    login_norm = np.clip((df["lms_login_frequency"] / 20.0) * 100.0, 0.0, 100.0)
    assign_norm = np.clip(df["lms_assignment_completion"], 0.0, 100.0)
    df["indicator_lms"] = np.clip(0.40 * login_norm + 0.60 * assign_norm, 0.0, 100.0).round(1)

    # 4. Placement Readiness Indicator (0-100)
    apt = df["aptitude_score"]
    cod = df["coding_score"]
    mock = df["mock_interview_score"]
    df["indicator_placement"] = np.clip(
        0.35 * apt + 0.40 * cod + 0.25 * mock, 0.0, 100.0
    ).round(1)

    # 5. Skills & Extracurricular Indicator (0-100)
    tech = df["technical_skills_score"]
    extra = np.clip(df["extracurricular_score"], 0.0, 100.0)
    df["indicator_skills"] = np.clip(0.60 * tech + 0.40 * extra, 0.0, 100.0).round(1)

    # 6. Engagement & Feedback Indicator (0-100)
    feedback_norm = np.clip((df["student_feedback_score"] / 5.0) * 100.0, 0.0, 100.0)
    df["indicator_engagement_feedback"] = feedback_norm.round(1)

    return df


# ==============================================================================
# 4. STUDENT SUCCESS SCORE CALCULATION
# ==============================================================================
def calculate_success_score(df: pd.DataFrame, weights: Dict[str, float] = None) -> pd.DataFrame:
    """
    Calculates weighted explainable Student Success Score (0-100)
    and per-pillar contribution points.
    """
    if weights is None:
        weights = DEFAULT_WEIGHTS

    total_weight = sum(weights.values())
    if total_weight <= 0:
        total_weight = 1.0

    df = df.copy()

    # Exact weighted contribution points
    df["pts_academic"] = (df["indicator_academic"] * weights.get("academic", 0.30)).round(2)
    df["pts_attendance"] = (df["indicator_attendance"] * weights.get("attendance", 0.20)).round(2)
    df["pts_lms"] = (df["indicator_lms"] * weights.get("lms", 0.15)).round(2)
    df["pts_placement"] = (df["indicator_placement"] * weights.get("placement", 0.20)).round(2)
    df["pts_skills"] = (df["indicator_skills"] * weights.get("skills", 0.10)).round(2)
    df["pts_engagement_feedback"] = (
        df["indicator_engagement_feedback"] * weights.get("engagement_feedback", 0.05)
    ).round(2)

    raw_score = (
        df["pts_academic"]
        + df["pts_attendance"]
        + df["pts_lms"]
        + df["pts_placement"]
        + df["pts_skills"]
        + df["pts_engagement_feedback"]
    ) / total_weight

    df["success_score"] = np.clip(raw_score, 0.0, 100.0).round(1)
    return df


# ==============================================================================
# 5. AT-RISK IDENTIFICATION & EXPLAINABLE REASONING
# ==============================================================================
def evaluate_risk_and_flags(df: pd.DataFrame, thresholds: Dict[str, float] = None) -> pd.DataFrame:
    """
    Evaluates rule-based Academic Risk, Placement Risk, and Overall Risk.
    Generates explainable reason flags, critical rules, and actionable intervention prompts.
    """
    if thresholds is None:
        thresholds = DEFAULT_THRESHOLDS

    df = df.copy()

    academic_risks = []
    placement_risks = []
    overall_risks = []
    reasons_list = []
    positive_drivers_list = []
    negative_drags_list = []
    recommended_interventions_list = []
    critical_rules_list = []

    for _, row in df.iterrows():
        reasons = []
        positives = []
        negatives = []
        interventions = []
        critical_rules = []

        # --- A. Academic Risk Evaluation ---
        acad_score = row["indicator_academic"]
        backlogs = int(row.get("backlog_count", 0))
        cgpa = float(row.get("cgpa", 0.0))
        att = float(row.get("attendance_overall", 0.0))

        if backlogs >= 2 or cgpa < 5.5 or acad_score < 50.0:
            acad_risk = "High Risk"
            reasons.append(f"Severe Academic Risk: {backlogs} backlog(s), CGPA {cgpa:.2f}")
            negatives.append(f"Active Backlogs ({backlogs}) & Low CGPA ({cgpa:.2f})")
            interventions.append("Subject-specific remedial classes")
            interventions.append("Academic advisory & backlog recovery plan")
        elif backlogs == 1 or cgpa < thresholds.get("cgpa_min", 6.5) or acad_score < 65.0:
            acad_risk = "Medium Risk"
            reasons.append(f"Moderate Academic Alert: CGPA {cgpa:.2f} (< {thresholds.get('cgpa_min', 6.5)})")
            negatives.append(f"CGPA below 6.5 ({cgpa:.2f})")
            interventions.append("Academic peer tutoring session")
        else:
            acad_risk = "Low Risk"
            positives.append(f"Strong Academic Foundation (CGPA {cgpa:.2f}, Zero Backlogs)")

        # --- B. Placement Risk Evaluation ---
        plac_score = row["indicator_placement"]
        cod = float(row.get("coding_score", 50.0))
        apt = float(row.get("aptitude_score", 50.0))
        mock = float(row.get("mock_interview_score", 50.0))

        if plac_score < 50.0 or apt < thresholds.get("aptitude_min", 50.0) or cod < 45.0 or mock < 45.0:
            plac_risk = "High Risk"
            reasons.append(f"Placement Risk: Coding ({cod:.0f}) / Aptitude ({apt:.0f}) below benchmark")
            negatives.append(f"Placement Readiness Deficit ({plac_score:.1f}/100)")
            interventions.append("Intensive coding bootcamp & DSA problem solving")
            interventions.append("Placement cell mock interview coaching")
        elif plac_score < 65.0 or apt < 60.0 or cod < thresholds.get("coding_min", 50.0):
            plac_risk = "Medium Risk"
            reasons.append(f"Moderate Placement Alert: Coding ({cod:.0f}) or Aptitude ({apt:.0f}) needs reinforcement")
            negatives.append(f"Placement readiness ({plac_score:.1f}/100) needs enhancement")
            interventions.append("Aptitude practice & Resume optimization")
        else:
            plac_risk = "Low Risk"
            positives.append(f"Placement Ready (Coding {cod:.0f}, Aptitude {apt:.0f}, Mock {mock:.0f})")

        # --- C. Independent Critical Rules ---
        if att < 75.0:
            critical_rules.append(f"Critically low attendance ({att:.1f}%) - Below statutory 75% limit")
            reasons.append(f"Attendance Shortfall: {att:.1f}% (< 75% cutoff)")
            interventions.append("Attendance counseling & parental notification")
            negatives.append(f"Classroom Attendance Shortfall ({att:.1f}%)")
        else:
            positives.append(f"Satisfactory Attendance ({att:.1f}%)")

        if backlogs >= 2:
            critical_rules.append(f"Multiple Backlogs Alert: {backlogs} subjects uncleared")

        # Asymmetric Profile: High CGPA but critically low placement readiness
        if cgpa >= 8.0 and plac_score < 55.0:
            critical_rules.append("Academic-Placement Asymmetry: Outstanding CGPA but severely unready for placement interviews")
            reasons.append("High exam score coupled with low practical technical interview readiness")
            interventions.append("Technical interview simulator & soft-skills coaching")

        if cgpa < 6.5 and cod >= 80.0:
            critical_rules.append("Hands-on Talent Alert: High coding score with CGPA below 6.5")
            reasons.append("Strong coding ability may be constrained by academic eligibility")
            interventions.append("Academic tutoring to improve eligibility while sustaining coding practice")

        # --- D. Overall Aggregate Risk ---
        overall_score = row.get("success_score", 70.0)
        if acad_risk == "High Risk" or plac_risk == "High Risk" or overall_score < thresholds.get("high_risk_max_score", 50.0):
            overall_risk = "High Risk"
        elif acad_risk == "Medium Risk" or plac_risk == "Medium Risk" or overall_score < thresholds.get("medium_risk_max_score", 70.0):
            overall_risk = "Medium Risk"
        else:
            overall_risk = "Low Risk"

        if not interventions:
            interventions.append("Standard periodic mentoring check-in")

        academic_risks.append(acad_risk)
        placement_risks.append(plac_risk)
        overall_risks.append(overall_risk)
        reasons_list.append("; ".join(reasons) if reasons else "No active risk alerts; performing within expected parameters.")
        positive_drivers_list.append(positives)
        negative_drags_list.append(negatives)
        recommended_interventions_list.append(" | ".join(list(dict.fromkeys(interventions))))
        critical_rules_list.append("; ".join(critical_rules) if critical_rules else "None")

    df["academic_risk"] = academic_risks
    df["placement_risk"] = placement_risks
    df["risk_level"] = overall_risks
    df["risk_reasons_str"] = reasons_list
    df["positive_drivers"] = positive_drivers_list
    df["negative_drags"] = negative_drags_list
    df["recommended_interventions"] = recommended_interventions_list
    df["critical_rules_triggered"] = critical_rules_list

    return df


# ==============================================================================
# 6. ACTIONABLE STUDENT SEGMENTATION
# ==============================================================================
def assign_student_segments(df: pd.DataFrame) -> pd.DataFrame:
    """
    Segments students into intuitive institutional cohorts based on multi-pillar profiles.
    """
    df = df.copy()
    segments = []

    for _, row in df.iterrows():
        score = row.get("success_score", 50.0)
        cgpa = row.get("cgpa", 0.0)
        cod = row.get("coding_score", 50.0)
        backlogs = row.get("backlog_count", 0)
        plac = row.get("indicator_placement", 50.0)
        placement_status = row.get("placement_status", "Eligible")

        if placement_status == "Placed":
            seg = "Placed Champion"
        elif score >= 82.0 and cgpa >= 8.5:
            seg = "Academic High Flier"
        elif cod >= 75.0 and cgpa < 6.5:
            seg = "Practical Coder / Hands-on"
        elif cod >= 80.0 and (row.get("placement_risk") == "Low Risk" or score >= 70.0):
            seg = "Placement Star"
        elif cgpa >= 8.0 and (row.get("placement_risk") == "High Risk" or plac < 55.0):
            seg = "Theory-Oriented Scholar"
        elif backlogs >= 2 or row.get("attendance_overall", 100.0) < 70.0:
            seg = "Urgent Intervention Needed"
        elif score < 55.0:
            seg = "Comprehensive Academic Risk"
        elif score >= 70.0:
            seg = "Consistent Performer"
        else:
            seg = "Steady Progress"

        segments.append(seg)

    df["segment"] = segments
    return df


# ==============================================================================
# 7. UNIFIED PIPELINE RUNNER
# ==============================================================================
def process_student_pipeline(
    df_raw: pd.DataFrame,
    weights: Dict[str, float] = None,
    thresholds: Dict[str, float] = None,
) -> Tuple[pd.DataFrame, Dict[str, Any]]:
    """
    Executes end-to-end data processing: validation, indicator normalization,
    weighted success scoring, risk rule evaluation, and cohort segmentation.
    """
    cleaned_df, report = validate_and_clean_data(df_raw)
    if cleaned_df.empty:
        return cleaned_df, report

    with_indicators = compute_indicators(cleaned_df)
    with_scores = calculate_success_score(with_indicators, weights)
    with_risks = evaluate_risk_and_flags(with_scores, thresholds)
    final_df = assign_student_segments(with_risks)

    return final_df, report
