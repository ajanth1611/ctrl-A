"""
CampusIQ: Staff / Faculty Portal Views — StudentSignals Design System
Provides Assigned Student Roster, Mentoring & Intervention Tracking,
and Evidence-Based Early Warning Insights.
"""

import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
from typing import Dict, Any

from src.database import (
    get_all_students,
    get_interventions,
    add_intervention,
    update_intervention_status,
)
from src.ui_theme import kpi_card, page_header


# ─── Navigation label → internal tab ────────────────────────────
_NAV_MAP = {
    "🏠  Dashboard":       "dashboard",
    "👥  Assigned Mentees": "mentees",
    "📋  Interventions":   "interventions",
    "💡  Early Warning":   "early_warning",
}


def render_staff_dashboard(current_user: Dict[str, Any], selected_nav: str = "") -> None:
    """Renders the Faculty & Mentoring suite driven by sidebar navigation."""
    tab = _NAV_MAP.get(selected_nav, "dashboard")
    df_assigned = get_all_students(current_user)

    if tab in ("dashboard", "mentees"):
        _render_assigned_students(df_assigned, current_user)
    elif tab == "interventions":
        _render_intervention_tracker(df_assigned, current_user)
    elif tab == "early_warning":
        _render_early_warning(df_assigned)
    else:
        _render_assigned_students(df_assigned, current_user)


def _render_assigned_students(df_assigned: pd.DataFrame, current_user: Dict[str, Any]) -> None:
    staff_name = current_user.get("name", "Faculty Mentor")
    staff_dept = current_user.get("department", "Engineering")

    page_header("Faculty & Mentoring Suite", f"{staff_name} · {staff_dept}")

    if df_assigned.empty:
        st.info("No assigned student records found for your account.")
        return

    # KPI Row
    tot          = len(df_assigned)
    acad_risk    = len(df_assigned[df_assigned["academic_risk"] == "High Risk"])   if "academic_risk"       in df_assigned.columns else 0
    att_warn     = len(df_assigned[df_assigned["attendance_overall"] < 75.0])       if "attendance_overall"  in df_assigned.columns else 0
    plac_risk    = len(df_assigned[df_assigned["placement_risk"] == "High Risk"])   if "placement_risk"      in df_assigned.columns else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(kpi_card("👥", "Assigned Mentees", str(tot), "#EFF6FF", "#2878F0"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("📚", "Academic Alerts", str(acad_risk), "#FEE2E2", "#EF4444", "CGPA < 5.5 or backlogs"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("🕐", "Attendance Warnings", str(att_warn), "#FEF3C7", "#F59E0B", "Below 75% threshold"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("💼", "Placement Needs", str(plac_risk), "#EDE9FE", "#8B5CF6", "Coding / interview prep"), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # Search & table
    search_q = st.text_input("🔍 Search Mentee by Name or ID:", placeholder="e.g. Karan").strip()
    table_df = df_assigned.copy()
    if search_q:
        table_df = table_df[
            table_df["name"].str.contains(search_q, case=False, na=False) |
            table_df["student_id"].str.contains(search_q, case=False, na=False)
        ]

    cols = [c for c in [
        "student_id", "name", "semester", "cgpa", "backlog_count",
        "attendance_overall", "coding_score", "success_score", "academic_risk", "placement_risk",
    ] if c in table_df.columns]

    st.dataframe(
        table_df[cols].rename(columns={
            "student_id": "ID", "name": "Mentee Name", "semester": "Sem", "cgpa": "CGPA",
            "backlog_count": "Backlogs", "attendance_overall": "Att %", "coding_score": "Coding",
            "success_score": "Score", "academic_risk": "Academic Risk", "placement_risk": "Placement Risk",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Quick Intervention Launcher
    st.markdown("---")
    st.markdown("##### ⚡ Quick Intervention Launcher")
    stu_opts = {f"{r['student_id']} - {r['name']}": r["student_id"] for _, r in table_df.iterrows()}
    if stu_opts:
        sel_name = st.selectbox("Select Mentee to Initiate Support Plan:", options=list(stu_opts.keys()))
        s_id = stu_opts[sel_name]
        s_row = table_df[table_df["student_id"] == s_id].iloc[0]

        with st.form("quick_int_form"):
            i_type = st.selectbox("Intervention Category:", [
                "Low Attendance Follow-up", "Academic Remediation", "Backlog Recovery Plan",
                "Assignment Completion Support", "Aptitude Practice", "Resume Improvement",
                "Mock Interview Practice", "Skill Development Recommendation",
            ])
            priority = st.selectbox("Priority Tier:", ["Urgent", "High", "Medium", "Low"], index=1)
            due = st.date_input("Target Due Date:", datetime.date.today() + datetime.timedelta(days=14))
            goal = st.text_input("Measurable Improvement Goal:", value=f"Improve performance in {s_row['department']} assessments.")
            desc = st.text_area("Mentoring Action Plan & Notes:", value=f"Identified warnings: {s_row.get('risk_reasons_str','General support')}")

            if st.form_submit_button("Record Intervention Plan", type="primary"):
                add_intervention(
                    s_row["student_id"], s_row["name"], s_row["department"],
                    i_type, desc, current_user.get("name", "Staff Mentor"), str(due),
                    priority, "In Progress", goal, current_user.get("email", "dr.sharma@campus.edu"),
                    current_user=current_user,
                )
                st.success(f"Successfully recorded {i_type} for {s_row['name']}!")
                st.rerun()


def _render_intervention_tracker(df_assigned: pd.DataFrame, current_user: Dict[str, Any]) -> None:
    page_header("Interventions", "Monitor progress, log meeting notes, and evaluate outcomes")

    df_ints = get_interventions(current_user=current_user)
    if df_ints.empty:
        st.info("No active interventions logged yet.")
        return

    status_filter = st.selectbox("Filter by Status:", ["All", "Pending", "In Progress", "Completed"])
    if status_filter != "All":
        df_ints = df_ints[df_ints["status"] == status_filter]

    show_cols = [c for c in [
        "id", "student_id", "student_name", "intervention_type",
        "priority", "status", "due_date", "goal", "outcome_measured",
    ] if c in df_ints.columns]

    st.dataframe(
        df_ints[show_cols].rename(columns={
            "id": "Case ID", "student_id": "Student ID", "student_name": "Name",
            "intervention_type": "Category", "priority": "Priority", "status": "Status",
            "due_date": "Due Date", "goal": "Measurable Goal", "outcome_measured": "Outcome",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown("##### ✏️ Update Intervention Progress")
    int_options = {f"{r['id']} - {r['student_name']} ({r['intervention_type']})": r["id"] for _, r in df_ints.iterrows()}

    if int_options:
        sel_int_key = st.selectbox("Select Case to Update:", options=list(int_options.keys()))
        case_id = int_options[sel_int_key]
        case_row = df_ints[df_ints["id"] == case_id].iloc[0]

        with st.form("update_int_form"):
            statuses = ["Pending", "In Progress", "Completed", "Escalated"]
            cur_idx = statuses.index(case_row["status"]) if case_row["status"] in statuses else 0
            new_status  = st.selectbox("Update Status:", statuses, index=cur_idx)
            new_outcome = st.text_input("Measured Outcome:", value=str(case_row.get("outcome_measured") or ""))
            new_notes   = st.text_area("Follow-up Meeting Notes:", value=str(case_row.get("notes") or ""))

            if st.form_submit_button("Save Progress", type="primary"):
                update_intervention_status(case_id, new_status, new_outcome, new_notes, current_user=current_user)
                st.success(f"Case {case_id} updated successfully!")
                st.rerun()


def _render_early_warning(df_assigned: pd.DataFrame) -> None:
    page_header("Early Warning", "Evidence-based recommendations from validated student indicators")

    if df_assigned.empty:
        st.info("No mentee data available.")
        return

    high_risk_mentees = df_assigned[df_assigned["risk_level"] == "High Risk"] if "risk_level" in df_assigned.columns else pd.DataFrame()

    if high_risk_mentees.empty:
        st.success("🎉 Excellent! None of your assigned mentees are currently in the High Risk tier.")
    else:
        for _, s in high_risk_mentees.iterrows():
            score = s.get("success_score", 0.0)
            risk_color = "#EF4444"
            st.markdown(
                f"""
                <div style="background:#FFFFFF;border:1px solid #FEE2E2;border-left:4px solid {risk_color};
                            border-radius:10px;padding:16px;margin-bottom:12px;
                            box-shadow:0 1px 4px rgba(239,68,68,0.08);">
                    <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;">
                        <span style="font-weight:700;color:#0F172A;font-size:0.95rem;">
                            {s['name']} <code style="font-size:0.76rem;color:#64748B;">{s['student_id']}</code>
                            &nbsp;·&nbsp; Sem {s['semester']}
                        </span>
                        <span style="background:#FEE2E2;color:#B91C1C;font-size:0.74rem;font-weight:700;
                                     padding:3px 10px;border-radius:20px;">
                            Score: {score:.1f}/100
                        </span>
                    </div>
                    <p style="font-size:0.82rem;color:{risk_color};font-weight:600;margin:0 0 4px 0;">
                        ⚠️ {s.get('risk_reasons_str','High risk indicators detected')}
                    </p>
                    <p style="font-size:0.8rem;color:#475569;margin:0;">
                        <strong>Recommended:</strong> {s.get('recommended_interventions','Academic and mentor review')}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )
