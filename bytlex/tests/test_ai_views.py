"""Streamlit smoke tests for optional AI student experiences."""

import pandas as pd
from streamlit.testing.v1 import AppTest

def _render_mentor():
    from src.views import student_view

    student_view.render_ai_academic_mentor({"student_id": "PRIVATE_STUDENT_ID"})


def _render_interview():
    from src.views import student_view

    student_view.render_mock_interview_studio({"student_id": "PRIVATE_STUDENT_ID"})


def _render_student_progress_with_missing_scores():
    from src.views import student_view

    student_view.render_student_progress_overview(
        {
            "student_id": "STU_NULL_SCORES",
            "success_score": None,
            "attendance_overall": 68.0,
            "cgpa": 5.2,
            "backlog_count": 2,
            "marks_percentage": 55.0,
            "lms_assignment_completion": 50.0,
            "coding_score": 42.0,
            "aptitude_score": 48.0,
            "mock_interview_score": 40.0,
        },
        {"student_id": "STU_NULL_SCORES"},
    )


def _render_admin_overview():
    import pandas as pd
    from src.views import admin_view

    students = pd.DataFrame(
        [
            {
                "student_id": "STU001",
                "name": "Demo Student",
                "department": "Computer Science",
                "semester": 5,
                "cgpa": 5.2,
                "backlog_count": 2,
                "attendance_overall": 68.0,
                "coding_score": 42.0,
                "success_score": 48.5,
                "risk_level": "High Risk",
                "academic_risk": "High Risk",
                "placement_risk": "High Risk",
                "segment": "Urgent Intervention Needed",
                "risk_reasons_str": "Low attendance; Active backlogs",
                "recommended_interventions": "Academic remediation",
            },
            {
                "student_id": "STU002",
                "name": "Steady Student",
                "department": "Computer Science",
                "semester": 5,
                "cgpa": 8.1,
                "backlog_count": 0,
                "attendance_overall": 91.0,
                "coding_score": 78.0,
                "success_score": 82.0,
                "risk_level": "Low Risk",
                "academic_risk": "Low Risk",
                "placement_risk": "Low Risk",
                "segment": "Placement Star",
                "risk_reasons_str": "No active risk alerts",
                "recommended_interventions": "Periodic mentoring",
            },
        ]
    )
    admin_view.render_institutional_overview(
        students,
        {"role": "admin", "student_id": None},
    )


def test_student_progress_handles_null_scores(monkeypatch):
    from src.views import student_view

    monkeypatch.setattr(
        student_view, "get_action_tasks_for_student", lambda *args, **kwargs: []
    )

    app = AppTest.from_function(_render_student_progress_with_missing_scores).run()

    assert not app.exception
    assert len(app.get("plotly_chart")) == 1
    assert any("Attendance is below 75%" in item.value for item in app.markdown)


def test_admin_overview_shows_interventions_segments_and_risk_queue(monkeypatch):
    from src.views import admin_view

    monkeypatch.setattr(
        admin_view,
        "get_interventions",
        lambda **kwargs: pd.DataFrame(
            [
                {
                    "id": "INT001",
                    "student_id": "STU001",
                    "status": "In Progress",
                    "intervention_type": "Academic Remediation",
                    "priority": "High",
                },
                {
                    "id": "INT002",
                    "student_id": "STU001",
                    "status": "Completed",
                    "intervention_type": "Attendance Follow-up",
                    "priority": "Urgent",
                },
            ]
        ),
    )

    app = AppTest.from_function(_render_admin_overview).run()

    assert not app.exception
    assert len(app.get("plotly_chart")) == 6
    assert any("High-risk follow-up queue" in item.value for item in app.markdown)
    assert any("Student segments" in item.value for item in app.markdown)
    assert any(metric.label == "Students Served" and metric.value == "1" for metric in app.metric)


def test_academic_mentor_keeps_local_guidance_without_provider(monkeypatch):
    from src.views import student_view

    monkeypatch.setattr(student_view, "available_ai_providers", lambda: [])

    app = AppTest.from_function(_render_mentor).run()

    assert not app.exception
    assert any("Local demo mode" in item.value for item in app.caption)


def test_academic_mentor_sends_question_only_after_consent(monkeypatch):
    from src.views import student_view

    requests = []
    monkeypatch.setattr(
        student_view, "available_ai_providers", lambda: ["OpenAI"]
    )
    monkeypatch.setattr(
        student_view,
        "generate_ai_response",
        lambda provider, system, prompt: (
            requests.append((provider, system, prompt)) or "AI guidance"
        ),
    )

    app = AppTest.from_function(_render_mentor).run()
    assert not app.exception

    app.text_input[0].set_value("Explain a graph traversal").run()
    app.checkbox[0].set_value(True).run()
    next(
        item
        for item in app.button
        if item.label == "Generate Step-by-Step Explanation"
    ).click().run()

    assert not app.exception
    assert len(requests) == 1
    assert requests[0][0] == "OpenAI"
    assert "Explain a graph traversal" in requests[0][2]
    assert "PRIVATE_STUDENT_ID" not in requests[0][2]


def test_mock_interview_renders_optional_provider_coaching(monkeypatch):
    from src.views import student_view

    monkeypatch.setattr(
        student_view, "available_ai_providers", lambda: ["Gemini"]
    )

    app = AppTest.from_function(_render_interview).run()

    assert not app.exception
    assert any(item.label == "AI coaching provider" for item in app.selectbox)
    assert any("Do not include personal" in item.value for item in app.info)
