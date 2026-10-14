"""
Pytest Test Suite: Centralized Scoring Engine, Risk Rules, and Indicators
"""

import pytest
import pandas as pd
import numpy as np

from src.analytics import (
    DEFAULT_WEIGHTS,
    DEFAULT_THRESHOLDS,
    validate_weights,
    compute_indicators,
    calculate_success_score,
    evaluate_risk_and_flags,
    assign_student_segments,
    process_student_pipeline,
)
from src.ai_mentor import build_career_roadmap


def test_weight_validation_valid():
    is_valid, norm_sum, err = validate_weights(DEFAULT_WEIGHTS)
    assert is_valid is True
    assert pytest.approx(norm_sum, 0.1) == 100.0
    assert err is None


def test_weight_validation_invalid_sum():
    bad_weights = {"academic": 0.5, "attendance": 0.2}
    is_valid, norm_sum, err = validate_weights(bad_weights)
    assert is_valid is False
    assert "Weights must total 100%" in err


def test_weight_validation_negative():
    bad_weights = {"academic": -0.1, "attendance": 1.1}
    is_valid, _, err = validate_weights(bad_weights)
    assert is_valid is False
    assert "cannot be negative" in err


def test_success_score_includes_all_six_weighted_contributions():
    df = pd.DataFrame([{
        "student_id": "STU006",
        "name": "Weighted Score Test",
        "cgpa": 8.0,
        "marks_percentage": 80.0,
        "backlog_count": 0,
        "attendance_overall": 80.0,
        "lms_login_frequency": 10,
        "lms_assignment_completion": 60.0,
        "technical_skills_score": 70.0,
        "aptitude_score": 60.0,
        "coding_score": 75.0,
        "mock_interview_score": 65.0,
        "extracurricular_score": 50.0,
        "student_feedback_score": 4.0,
    }])

    scored = calculate_success_score(compute_indicators(df))
    contribution_columns = [
        "pts_academic",
        "pts_attendance",
        "pts_lms",
        "pts_placement",
        "pts_skills",
        "pts_engagement_feedback",
    ]
    expected_score = round(scored[contribution_columns].sum(axis=1).iloc[0], 1)

    assert scored["success_score"].iloc[0] == expected_score
    assert scored["pts_lms"].iloc[0] > 0


def test_indicator_normalization_boundaries():
    df = pd.DataFrame([{
        "student_id": "STU001",
        "name": "Test Student",
        "cgpa": 9.5,
        "marks_percentage": 92.0,
        "backlog_count": 0,
        "attendance_overall": 95.0,
        "lms_login_frequency": 25,  # above 20 benchmark
        "lms_assignment_completion": 105.0,  # exceeds 100
        "technical_skills_score": 90.0,
        "aptitude_score": 85.0,
        "coding_score": 90.0,
        "mock_interview_score": 88.0,
        "extracurricular_score": 90.0,
        "student_feedback_score": 5.0,
    }])

    ind_df = compute_indicators(df)
    assert ind_df["indicator_academic"].iloc[0] <= 100.0
    assert ind_df["indicator_attendance"].iloc[0] <= 100.0
    assert ind_df["indicator_lms"].iloc[0] <= 100.0
    assert ind_df["indicator_placement"].iloc[0] <= 100.0
    assert ind_df["indicator_skills"].iloc[0] <= 100.0


def test_backlog_penalty_clipping():
    df = pd.DataFrame([{
        "student_id": "STU002",
        "name": "Backlog Heavy",
        "cgpa": 4.5,
        "marks_percentage": 40.0,
        "backlog_count": 6,  # 6 * 12 = 72 penalty
        "attendance_overall": 50.0,
        "lms_login_frequency": 2,
        "lms_assignment_completion": 40.0,
        "technical_skills_score": 30.0,
        "aptitude_score": 30.0,
        "coding_score": 25.0,
        "mock_interview_score": 30.0,
        "extracurricular_score": 20.0,
        "student_feedback_score": 2.0,
    }])

    ind_df = compute_indicators(df)
    # 0.70*(45) + 0.30*(40) - 72 = 31.5 + 12 - 72 = -28.5 -> clipped to 0.0
    assert ind_df["indicator_academic"].iloc[0] == 0.0


def test_separate_academic_and_placement_risks():
    # Asymmetric student: high CGPA, low coding/interview
    df = pd.DataFrame([{
        "student_id": "STU003",
        "name": "Exam Genius Placement Anxious",
        "cgpa": 9.2,
        "marks_percentage": 94.0,
        "backlog_count": 0,
        "attendance_overall": 92.0,
        "lms_login_frequency": 18,
        "lms_assignment_completion": 95.0,
        "technical_skills_score": 50.0,
        "aptitude_score": 45.0,  # low
        "coding_score": 35.0,    # low
        "mock_interview_score": 40.0,  # low
        "extracurricular_score": 40.0,
        "student_feedback_score": 4.0,
    }])

    ind_df = compute_indicators(df)
    scored_df = calculate_success_score(ind_df)
    risks_df = evaluate_risk_and_flags(scored_df)

    assert risks_df["academic_risk"].iloc[0] == "Low Risk"
    assert risks_df["placement_risk"].iloc[0] == "High Risk"
    assert "Academic-Placement Asymmetry" in risks_df["critical_rules_triggered"].iloc[0]


def test_critical_attendance_warning():
    df = pd.DataFrame([{
        "student_id": "STU004",
        "name": "Low Attendance",
        "cgpa": 7.8,
        "marks_percentage": 78.0,
        "backlog_count": 0,
        "attendance_overall": 64.0,  # below 75% cutoff
        "lms_login_frequency": 12,
        "lms_assignment_completion": 80.0,
        "technical_skills_score": 70.0,
        "aptitude_score": 70.0,
        "coding_score": 70.0,
        "mock_interview_score": 70.0,
        "extracurricular_score": 50.0,
        "student_feedback_score": 4.0,
    }])

    ind_df = compute_indicators(df)
    scored_df = calculate_success_score(ind_df)
    risks_df = evaluate_risk_and_flags(scored_df)

    assert "Critically low attendance" in risks_df["critical_rules_triggered"].iloc[0]
    assert "Attendance counseling" in risks_df["recommended_interventions"].iloc[0]


def test_hands_on_talent_alert_recommends_academic_support():
    df = pd.DataFrame([{
        "student_id": "STU_HANDS_ON",
        "name": "Practical Coder",
        "cgpa": 6.2,
        "marks_percentage": 62.0,
        "backlog_count": 0,
        "attendance_overall": 82.0,
        "lms_login_frequency": 12,
        "lms_assignment_completion": 75.0,
        "technical_skills_score": 78.0,
        "aptitude_score": 72.0,
        "coding_score": 84.0,
        "mock_interview_score": 70.0,
        "extracurricular_score": 50.0,
        "student_feedback_score": 4.0,
    }])

    processed, _ = process_student_pipeline(df)

    assert "Hands-on Talent Alert" in processed["critical_rules_triggered"].iloc[0]
    assert "Academic tutoring" in processed["recommended_interventions"].iloc[0]


def test_segment_assignment():
    df = pd.DataFrame([
        {
            "student_id": "STU_P", "name": "Placed", "cgpa": 8.0, "coding_score": 80,
            "success_score": 85.0, "placement_status": "Placed", "backlog_count": 0,
            "attendance_overall": 90, "indicator_placement": 85, "placement_risk": "Low Risk"
        },
        {
            "student_id": "STU_C", "name": "Coder", "cgpa": 6.2, "coding_score": 82,
            "success_score": 68.0, "placement_status": "Eligible", "backlog_count": 0,
            "attendance_overall": 80, "indicator_placement": 80, "placement_risk": "Low Risk"
        },
    ])

    segmented = assign_student_segments(df)
    assert segmented["segment"].iloc[0] == "Placed Champion"
    assert segmented["segment"].iloc[1] == "Practical Coder / Hands-on"


def test_career_roadmap_prioritizes_academic_risks_and_skill_gaps():
    student = {
        "coding_score": 35,
        "technical_skills_score": 45,
        "aptitude_score": 55,
        "mock_interview_score": 50,
        "attendance_overall": 64,
        "backlog_count": 2,
        "academic_risk": "High Risk",
        "placement_risk": "High Risk",
    }

    roadmap = build_career_roadmap(
        student,
        "Full Stack Software Engineer",
        duration_weeks=8,
        hours_per_week=5,
    )

    assert roadmap["readiness_score"] < 100
    assert [milestone["week_range"] for milestone in roadmap["milestones"]] == [
        "Weeks 1-2",
        "Weeks 3-4",
        "Weeks 5-6",
        "Weeks 7-8",
    ]
    first_actions = " ".join(roadmap["milestones"][0]["actions"])
    assert "attendance recovery plan" in first_actions
    assert "2 active backlog(s)" in first_actions
    assert "High Risk academic risk indicators" in first_actions
    assert "High Risk placement risk" in first_actions
    assert roadmap["milestones"][0]["focus_skill"]
    assert "mock interview" in " ".join(roadmap["milestones"][-1]["actions"]).lower()


def test_career_roadmap_flags_missing_assessments_and_validates_inputs():
    roadmap = build_career_roadmap(
        {
            "attendance_overall": None,
            "backlog_count": None,
            "coding_score": None,
        },
        "AI / Machine Learning Engineer",
        duration_weeks=4,
        hours_per_week=3,
    )

    assert len(roadmap["milestones"]) == 4
    assert "Coding assessment" in roadmap["missing_assessments"]
    assert roadmap["missing_academic_data"] == ["attendance", "backlog count"]
    first_actions = " ".join(roadmap["milestones"][0]["actions"])
    assert "baseline assessments" in first_actions
    assert "Confirm your current attendance and backlog count" in first_actions
    with pytest.raises(ValueError, match="Unknown career role"):
        build_career_roadmap({}, "Unknown Role")
    with pytest.raises(ValueError, match="duration"):
        build_career_roadmap({}, "AI / Machine Learning Engineer", duration_weeks=6)
