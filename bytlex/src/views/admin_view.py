"""
CampusIQ: Administrator Portal Views — StudentSignals Design System
Provides Institutional Analytics, Student Directory & Deep Profiles,
Staff Management, CSV Ingestion Center, and Scoring Configuration.
"""

import io
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, Any, List

from src.database import (
    get_all_students,
    get_interventions,
    assign_mentor_to_student,
    get_import_history,
    sync_students_to_db,
)
from src.analytics import (
    DEFAULT_WEIGHTS,
    DEFAULT_THRESHOLDS,
    validate_weights,
    process_student_pipeline,
)
from src.csv_importer import (
    DATASET_SCHEMAS,
    auto_map_columns,
    validate_csv_rows,
    execute_csv_import,
)
from src.ui_theme import kpi_card, page_header, card_open, card_close

# ─── Navigation label → tab mapping ─────────────────────────────
_NAV_MAP = {
    "🏠  Dashboard":           "overview",
    "📥  Upload Data":         "csv",
    "👥  Student Risk List":   "directory",
    "📋  Interventions":       "interventions",
    "💡  AI Insights":         "overview",   # redirects to overview
    "🏫  School Comparison":   "overview",
    "📊  Reports & Analytics": "overview",
    "⚙️  Settings":            "scoring",
}


def render_admin_dashboard(current_user: Dict[str, Any], selected_nav: str = "") -> None:
    """Renders the Administrator Suite driven by the sidebar navigation."""
    # Map sidebar nav item to internal tab
    tab = _NAV_MAP.get(selected_nav, "overview")

    df_students = get_all_students(current_user)

    if tab == "overview":
        _render_overview(df_students, current_user)
    elif tab == "directory":
        _render_student_directory(df_students, current_user)
    elif tab == "csv":
        _render_csv_ingestion(current_user)
    elif tab == "scoring":
        _render_scoring_config(df_students, current_user)
    else:
        _render_overview(df_students, current_user)


# ══════════════════════════════════════════════════════════════════
# TAB 1 — INSTITUTIONAL OVERVIEW / DASHBOARD
# ══════════════════════════════════════════════════════════════════
def _render_overview(df_students: pd.DataFrame, current_user: Dict[str, Any]) -> None:

    # ── Metrics ──────────────────────────────────────────────
    total      = len(df_students)
    high_risk  = int(df_students["risk_level"].eq("High Risk").sum())  if "risk_level"         in df_students.columns else 0
    att_warn   = int(df_students["attendance_overall"].lt(75.0).sum()) if "attendance_overall"  in df_students.columns else 0
    grade_warn = int((df_students["academic_risk"].eq("High Risk") | df_students["academic_risk"].eq("Medium Risk")).sum()) if "academic_risk" in df_students.columns else 0
    disc_inc   = int(df_students["backlog_count"].gt(0).sum())          if "backlog_count"       in df_students.columns else 0
    avg_score  = df_students["success_score"].mean()                    if not df_students.empty and "success_score" in df_students.columns else 0.0
    avg_att    = df_students["attendance_overall"].mean()               if not df_students.empty and "attendance_overall" in df_students.columns else 0.0

    df_int = get_interventions(current_user=current_user)
    active_statuses = {"Pending", "In Progress", "Escalated"}
    open_int  = int(df_int["status"].isin(active_statuses).sum()) if not df_int.empty and "status" in df_int.columns else 0
    comp_int  = int(df_int["status"].eq("Completed").sum())        if not df_int.empty and "status" in df_int.columns else 0
    stu_served= int(df_int["student_id"].nunique())                  if not df_int.empty and "student_id" in df_int.columns else 0
    total_int = len(df_int)

    # ── Page heading ─────────────────────────────────────────
    head_col, btn_col = st.columns([3, 1])
    with head_col:
        page_header("Dashboard", "Student risk overview and key insights")
    with btn_col:
        st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
        if st.button("👥 View All Students", use_container_width=True, key="hdr_view_students"):
            st.session_state["sidebar_nav"] = "👥  Student Risk List"
            st.rerun()

    # ── KPI Row ───────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(kpi_card("👤", "Total Students", str(total), "#EFF6FF", "#2878F0", f"Avg score {avg_score:.0f}/100"), unsafe_allow_html=True)
    with c2:
        st.markdown(kpi_card("⚠️", "High-Risk Students", str(high_risk), "#FEE2E2", "#EF4444", f"{high_risk/total*100:.0f}% of total" if total else "—"), unsafe_allow_html=True)
    with c3:
        st.markdown(kpi_card("🕐", "Attendance Warnings", str(att_warn), "#FEF3C7", "#F59E0B", "Below 75% threshold"), unsafe_allow_html=True)
    with c4:
        st.markdown(kpi_card("📚", "Grade Warnings", str(grade_warn), "#D1FAE5", "#10B981", "Med or high academic risk"), unsafe_allow_html=True)
    with c5:
        st.markdown(kpi_card("🛡️", "Discipline / Backlogs", str(disc_inc), "#EDE9FE", "#8B5CF6", "Students with backlogs"), unsafe_allow_html=True)

    st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

    # ── Main + Right layout ───────────────────────────────────
    main_col, right_col = st.columns([2.2, 1])

    with main_col:
        # Intervention Overview Card
        st.markdown(
            f"""
            <div class="ss-card">
                <p class="ss-card-title">📋 Intervention Overview</p>
            """,
            unsafe_allow_html=True,
        )
        # 4 sub-KPI metrics
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.metric("Active", open_int)
        with m2:
            st.metric("Completed", comp_int)
        with m3:
            st.metric("Students Served", stu_served)
        with m4:
            st.metric("Total", total_int)
        st.markdown("</div>", unsafe_allow_html=True)

        # Charts inside intervention area
        if not df_int.empty:
            chart_col1, chart_col2 = st.columns(2)
            if "intervention_type" in df_int.columns:
                with chart_col1:
                    type_counts = (
                        df_int["intervention_type"]
                        .fillna("Unspecified")
                        .value_counts()
                        .rename_axis("Intervention")
                        .reset_index(name="Cases")
                        .sort_values("Cases")
                    )
                    fig = px.bar(
                        type_counts, x="Cases", y="Intervention",
                        orientation="h", text="Cases",
                        color_discrete_sequence=["#2878F0"],
                        title="Interventions by Type",
                    )
                    fig.update_layout(
                        template="plotly_white", height=max(260, 42*len(type_counts)),
                        margin=dict(l=10, r=30, t=40, b=10),
                        xaxis_title="", yaxis_title="", showlegend=False,
                        title_font_size=14, title_font_color="#0F172A",
                        paper_bgcolor="white", plot_bgcolor="white",
                    )
                    fig.update_traces(texttemplate="%{text}", textposition="outside")
                    st.plotly_chart(fig, use_container_width=True)

            if "risk_level" in df_students.columns and not df_students.empty:
                with chart_col2:
                    risk_counts = df_students["risk_level"].value_counts().reset_index()
                    risk_counts.columns = ["Tier", "Count"]
                    fig2 = px.pie(
                        risk_counts, values="Count", names="Tier", hole=0.6,
                        color="Tier",
                        color_discrete_map={
                            "High Risk": "#EF4444",
                            "Medium Risk": "#F59E0B",
                            "Low Risk": "#10B981",
                        },
                        title="Risk Tier Distribution",
                    )
                    fig2.update_layout(
                        height=280, template="plotly_white",
                        margin=dict(l=10, r=10, t=40, b=20),
                        title_font_size=14, title_font_color="#0F172A",
                        paper_bgcolor="white",
                        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                    )
                    st.plotly_chart(fig2, use_container_width=True)

        # Students Requiring Attention
        if not df_students.empty and "risk_level" in df_students.columns:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown(
                '<div class="ss-card"><p class="ss-card-title">🚨 Students Requiring Attention</p>',
                unsafe_allow_html=True,
            )
            high_risk_df = df_students[df_students["risk_level"] == "High Risk"].copy()
            if high_risk_df.empty:
                st.success("✅ No students currently classified as High Risk.")
            else:
                search = st.text_input("🔍 Search students:", placeholder="Name or ID", key="attn_search")
                if search:
                    high_risk_df = high_risk_df[
                        high_risk_df["name"].str.contains(search, case=False, na=False) |
                        high_risk_df["student_id"].str.contains(search, case=False, na=False)
                    ]

                show_cols = [c for c in ["student_id","name","department","semester","success_score","risk_level","risk_reasons_str"] if c in high_risk_df.columns]
                rename_map = {
                    "student_id": "ID", "name": "Student Name",
                    "department": "Department", "semester": "Semester",
                    "success_score": "Score", "risk_level": "Risk",
                    "risk_reasons_str": "Key Issues",
                }
                st.dataframe(
                    high_risk_df[show_cols].rename(columns=rename_map),
                    use_container_width=True, hide_index=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)

        # Score Distribution
        if not df_students.empty and "success_score" in df_students.columns:
            fig3 = px.histogram(
                df_students, x="success_score", nbins=20,
                color_discrete_sequence=["#2878F0"],
                labels={"success_score": "Success Score (0-100)"},
                title="Student Success Score Distribution",
            )
            fig3.update_layout(
                template="plotly_white", height=260,
                margin=dict(l=10, r=10, t=40, b=20),
                title_font_size=14, title_font_color="#0F172A",
                paper_bgcolor="white", plot_bgcolor="white",
                yaxis_title="Count", xaxis_title="Score",
            )
            st.plotly_chart(fig3, use_container_width=True)

    with right_col:
        # Risk Distribution donut
        if not df_students.empty and "risk_level" in df_students.columns:
            st.markdown('<div class="ss-card"><p class="ss-card-title">🎯 Risk Distribution</p>', unsafe_allow_html=True)
            risk_cnt = df_students["risk_level"].value_counts()
            fig_r = go.Figure(go.Pie(
                labels=risk_cnt.index.tolist(),
                values=risk_cnt.values.tolist(),
                hole=0.62,
                marker_colors=["#EF4444" if "High" in l else "#F59E0B" if "Medium" in l else "#10B981" for l in risk_cnt.index],
            ))
            fig_r.update_layout(
                height=220, margin=dict(l=10, r=10, t=10, b=10),
                showlegend=True, paper_bgcolor="white",
                legend=dict(font_size=11, orientation="v"),
            )
            st.plotly_chart(fig_r, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Recent Activities
        st.markdown('<div class="ss-card"><p class="ss-card-title">🕐 Recent Activities</p>', unsafe_allow_html=True)
        if not df_int.empty:
            recent = df_int.sort_values("created_at", ascending=False).head(5) if "created_at" in df_int.columns else df_int.head(5)
            for _, row in recent.iterrows():
                badge_cls = "ss-badge-amber" if row.get("status") in ("Pending","In Progress") else "ss-badge-green"
                st.markdown(
                    f"""
                    <div style="padding:8px 0;border-bottom:1px solid #F1F5F9;">
                        <div style="font-size:0.82rem;font-weight:600;color:#0F172A;">{row.get('student_name','—')}</div>
                        <div style="font-size:0.75rem;color:#64748B;">{row.get('intervention_type','—')}</div>
                        <span class="ss-badge {badge_cls}">{row.get('status','—')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
        else:
            st.caption("No recent interventions recorded.")
        st.markdown("</div>", unsafe_allow_html=True)

        # Quick Actions
        st.markdown('<div class="ss-card"><p class="ss-card-title">⚡ Quick Actions</p>', unsafe_allow_html=True)
        qa1, qa2 = st.columns(2)
        with qa1:
            if st.button("📥\nUpload Data", use_container_width=True, key="qa_upload"):
                st.session_state["sidebar_nav"] = "📥  Upload Data"
                st.rerun()
            if st.button("📋\nInterventions", use_container_width=True, key="qa_int"):
                st.session_state["sidebar_nav"] = "📋  Interventions"
                st.rerun()
        with qa2:
            if st.button("👥\nStudent List", use_container_width=True, key="qa_students"):
                st.session_state["sidebar_nav"] = "👥  Student Risk List"
                st.rerun()
            if st.button("⚙️\nSettings", use_container_width=True, key="qa_settings"):
                st.session_state["sidebar_nav"] = "⚙️  Settings"
                st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # Department comparison
    if not df_students.empty and "department" in df_students.columns:
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        st.markdown('<div class="ss-card"><p class="ss-card-title">🏫 Department Comparisons</p>', unsafe_allow_html=True)
        dept_summary = df_students.groupby("department").agg(
            avg_score=("success_score", "mean"),
            avg_attendance=("attendance_overall", "mean"),
            high_risk_count=("risk_level", lambda s: (s == "High Risk").sum()),
            student_count=("student_id", "count"),
        ).reset_index()
        fig_d = px.bar(
            dept_summary, x="department",
            y=["avg_score", "avg_attendance"],
            barmode="group",
            color_discrete_map={"avg_score": "#2878F0", "avg_attendance": "#10B981"},
            labels={"value": "Score / %", "variable": "Metric"},
        )
        fig_d.update_layout(
            template="plotly_white", height=280,
            margin=dict(l=10, r=10, t=10, b=20),
            xaxis_title="", paper_bgcolor="white", plot_bgcolor="white",
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_d, use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# TAB 2 — STUDENT DIRECTORY & PROFILES
# ══════════════════════════════════════════════════════════════════
def _render_student_directory(df_students: pd.DataFrame, current_user: Dict[str, Any]) -> None:
    page_header("Student Risk List", "Full directory with 360° profile & score explainability")

    if df_students.empty:
        st.info("No student records available.")
        return

    # Filter Bar
    f1, f2, f3, f4 = st.columns([2, 1.2, 1.2, 1.2])
    with f1:
        search_term = st.text_input("🔍 Search Name / Student ID:", placeholder="e.g. Karan or STU2021004").strip()
    with f2:
        dept_opts = ["All Departments"] + sorted(df_students["department"].dropna().unique().tolist())
        sel_dept = st.selectbox("Department:", options=dept_opts)
    with f3:
        sel_risk = st.selectbox("Risk Level:", ["All Risk Tiers", "High Risk", "Medium Risk", "Low Risk"])
    with f4:
        sem_opts = ["All Semesters"] + sorted(df_students["semester"].dropna().unique().tolist())
        sel_sem = st.selectbox("Semester:", options=sem_opts)

    filtered = df_students.copy()
    if search_term:
        filtered = filtered[
            filtered["name"].str.contains(search_term, case=False, na=False) |
            filtered["student_id"].str.contains(search_term, case=False, na=False)
        ]
    if sel_dept != "All Departments":
        filtered = filtered[filtered["department"] == sel_dept]
    if sel_risk != "All Risk Tiers":
        filtered = filtered[filtered["risk_level"] == sel_risk]
    if sel_sem != "All Semesters":
        filtered = filtered[filtered["semester"] == sel_sem]

    st.markdown(
        f"<span style='font-size:0.8rem;color:#64748B;font-weight:600;'>Showing {len(filtered)} of {len(df_students)} students</span>",
        unsafe_allow_html=True,
    )
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    cols_to_show = [c for c in [
        "student_id", "name", "department", "semester", "cgpa", "backlog_count",
        "attendance_overall", "coding_score", "success_score", "risk_level", "segment", "mentor_name",
    ] if c in filtered.columns]

    st.dataframe(
        filtered[cols_to_show].rename(columns={
            "student_id": "ID", "name": "Student Name", "department": "Department",
            "semester": "Sem", "cgpa": "CGPA", "backlog_count": "Backlogs",
            "attendance_overall": "Att %", "coding_score": "Coding",
            "success_score": "Score", "risk_level": "Risk Tier",
            "segment": "Cohort", "mentor_name": "Mentor",
        }),
        use_container_width=True,
        hide_index=True,
    )

    # Deep Profile
    st.markdown("---")
    st.markdown("#### 👤 Student 360° Profile & Score Explainability")
    stu_picker = {f"{r['student_id']} - {r['name']} ({r['department']})": r["student_id"] for _, r in filtered.iterrows()}

    if stu_picker:
        selected_key = st.selectbox("Select Student to Inspect:", options=list(stu_picker.keys()))
        s_id = stu_picker[selected_key]
        s_row = filtered[filtered["student_id"] == s_id].iloc[0]

        p1, p2 = st.columns([1.2, 1])
        with p1:
            risk_color = "#EF4444" if s_row.get("risk_level") == "High Risk" else "#F59E0B" if s_row.get("risk_level") == "Medium Risk" else "#10B981"
            st.markdown(
                f"""
                <div style="background:#F8FAFC;border:1px solid #E4E9F0;border-radius:12px;padding:20px;margin-bottom:14px;">
                    <div style="font-size:1.2rem;font-weight:800;color:#0F172A;">{s_row['name']}
                        <code style="font-size:0.78rem;color:#64748B;">{s_row['student_id']}</code>
                    </div>
                    <div style="font-size:0.84rem;color:#64748B;margin:4px 0 12px 0;">
                        {s_row['department']} &bull; Semester {s_row['semester']} &bull; {s_row.get('placement_status','Eligible')}
                    </div>
                    <div style="display:flex;gap:10px;align-items:center;">
                        <span style="font-size:2.4rem;font-weight:800;color:#0F172A;">{s_row.get('success_score',0.0):.1f}</span>
                        <div>
                            <div style="font-size:0.75rem;color:#64748B;font-weight:600;">Success Score / 100</div>
                            <div style="font-size:0.82rem;font-weight:700;color:{risk_color};">{s_row.get('risk_level','Low Risk')}</div>
                        </div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            with st.expander("✏️ Reassign Faculty Mentor"):
                new_mentor = st.selectbox("Assign New Mentor:", ["Dr. Ananya Sharma", "Prof. Rajesh Kulkarni"])
                new_email = "dr.sharma@campus.edu" if "Sharma" in new_mentor else "prof.rajesh@campus.edu"
                if st.button("Confirm Reassignment"):
                    assign_mentor_to_student(s_row["student_id"], new_mentor, new_email, current_user=current_user)
                    st.success(f"Assigned {new_mentor} to {s_row['name']}!")
                    st.rerun()

            st.markdown("##### ⚠️ Risk Diagnostic Flags")
            reasons = s_row.get("risk_reasons_str", "None identified.")
            for r in str(reasons).split("; "):
                st.markdown(f"- {r}")

        with p2:
            scored_row, _ = process_student_pipeline(pd.DataFrame([s_row.to_dict()]))
            if not scored_row.empty:
                scored = scored_row.iloc[0]
                dimensions = [
                    ("Academic", "indicator_academic", "pts_academic", DEFAULT_WEIGHTS["academic"]),
                    ("Attendance", "indicator_attendance", "pts_attendance", DEFAULT_WEIGHTS["attendance"]),
                    ("LMS Engagement", "indicator_lms", "pts_lms", DEFAULT_WEIGHTS["lms"]),
                    ("Placement Readiness", "indicator_placement", "pts_placement", DEFAULT_WEIGHTS["placement"]),
                    ("Skills & Extracurricular", "indicator_skills", "pts_skills", DEFAULT_WEIGHTS["skills"]),
                    ("Student Feedback", "indicator_engagement_feedback", "pts_engagement_feedback", DEFAULT_WEIGHTS["engagement_feedback"]),
                ]
                pillar_data = pd.DataFrame([
                    {
                        "Dimension": label,
                        "Indicator score": float(scored[indicator]),
                        "Weighted points": float(scored[points]),
                        "Weight": f"{weight:.0%}",
                    }
                    for label, indicator, points, weight in dimensions
                ])
                fig_p = px.bar(
                    pillar_data.sort_values("Indicator score"),
                    x="Indicator score", y="Dimension",
                    orientation="h", text="Indicator score",
                    range_x=[0, 100],
                    color_discrete_sequence=["#2878F0"],
                    title="Score Contributions",
                )
                fig_p.update_traces(texttemplate="%{text:.1f}", textposition="outside", cliponaxis=False)
                fig_p.update_layout(
                    template="plotly_white", height=320,
                    margin=dict(l=10, r=30, t=40, b=10),
                    xaxis_title="Indicator (0-100)", yaxis_title="",
                    showlegend=False, paper_bgcolor="white",
                    title_font_size=13, title_font_color="#0F172A",
                )
                st.plotly_chart(fig_p, use_container_width=True)


# ══════════════════════════════════════════════════════════════════
# TAB 3 — CSV INGESTION (Upload Data)
# ══════════════════════════════════════════════════════════════════
def _render_csv_ingestion(current_user: Dict[str, Any]) -> None:
    import os
    page_header("Upload Data", "CSV ingestion with automated schema mapping and validation")

    st.info("Packaged sample files contain synthetic demo records. Use only authorized, non-sensitive data.")

    dataset_keys   = list(DATASET_SCHEMAS.keys())
    dataset_labels = [DATASET_SCHEMAS[k]["label"] for k in dataset_keys]
    selected_idx   = st.selectbox("Target Dataset Schema:", range(len(dataset_keys)), format_func=lambda i: dataset_labels[i])
    current_key    = dataset_keys[selected_idx]
    current_schema = DATASET_SCHEMAS[current_key]
    st.caption(current_schema["description"])

    st.markdown("##### ⚡ Pre-Packaged Sample Datasets")
    q1, q2, q3 = st.columns(3)
    sample_to_load = None
    with q1:
        if st.button("Load Student Master Sample (50 rows)"):
            sample_to_load = "sample-data/student_master.csv"
    with q2:
        if st.button("Load Academic Records (CGPA & Backlogs)"):
            sample_to_load = "sample-data/academic_records.csv"
    with q3:
        if st.button("Load Dataset with Validation Errors"):
            sample_to_load = "sample-data/import_with_errors.csv"

    uploaded_file = st.file_uploader("Or Browse CSV from disk:", type=["csv"])
    df_raw, filename = None, "manual_upload.csv"
    if uploaded_file:
        df_raw   = pd.read_csv(uploaded_file)
        filename = uploaded_file.name
    elif sample_to_load:
        if os.path.exists(sample_to_load):
            df_raw   = pd.read_csv(sample_to_load)
            filename = sample_to_load.split("/")[-1]

    if df_raw is not None:
        st.markdown(f"##### Preview: `{filename}` ({len(df_raw)} rows)")
        st.dataframe(df_raw.head(5), use_container_width=True)

        st.markdown("##### 🔀 Column Mapping")
        headers  = df_raw.columns.tolist()
        auto_map = auto_map_columns(headers, current_key)
        mapping  = {}
        m_cols   = st.columns(min(len(current_schema["fields"]), 4))
        for idx, (target_field, spec) in enumerate(current_schema["fields"].items()):
            col_slot = m_cols[idx % len(m_cols)]
            with col_slot:
                default_match = auto_map.get(target_field, "")
                default_idx   = headers.index(default_match) if default_match in headers else 0
                chosen = st.selectbox(
                    f"{spec['label']} {'*' if spec.get('required') else ''}:",
                    options=["-- Ignore --"] + headers,
                    index=default_idx + 1 if default_match in headers else 0,
                    key=f"map_{target_field}",
                )
                if chosen != "-- Ignore --":
                    mapping[target_field] = chosen

        valid_rows, error_rows = validate_csv_rows(df_raw, mapping, current_key)
        v1, v2, v3 = st.columns(3)
        with v1:
            st.metric("Total Parsed", len(df_raw))
        with v2:
            st.metric("Valid Rows", len(valid_rows))
        with v3:
            st.metric("Invalid Rows", len(error_rows))

        if error_rows:
            st.error(f"⚠️ {len(error_rows)} row(s) contained errors and will be excluded.")
            err_df = pd.DataFrame(error_rows)[["row_index", "student_id", "error"]]
            st.dataframe(err_df, use_container_width=True, hide_index=True)
            err_csv = err_df.to_csv(index=False).encode("utf-8")
            st.download_button("📥 Download Invalid Rows", data=err_csv, file_name=f"invalid_{filename}", mime="text/csv")

        if st.button("🚀 Confirm & Ingest Valid Records", type="primary"):
            res = execute_csv_import(valid_rows, current_key, filename, len(df_raw), len(error_rows), current_user=current_user)
            st.success(f"Ingestion {res['status']}: +{res['inserted']} new, ~{res['updated']} updated.")
            st.rerun()

    st.markdown("---")
    st.markdown("##### 📜 Ingestion Audit History")
    hist = get_import_history(current_user=current_user)
    if not hist.empty:
        st.dataframe(hist, use_container_width=True, hide_index=True)
    else:
        st.caption("No historical import jobs recorded.")


# ══════════════════════════════════════════════════════════════════
# TAB 4 — SCORING CONFIGURATION (Settings)
# ══════════════════════════════════════════════════════════════════
def _render_scoring_config(df_students: pd.DataFrame, current_user: Dict[str, Any]) -> None:
    page_header("Settings", "Adjust scoring weights and risk thresholds")

    st.markdown("#### ⚙️ Student Success Scoring Formula")
    st.caption("Adjust dimension weights. Changes dynamically recalculate all institutional student scores.")

    w_acad  = st.slider("Academic Performance Weight (%):", 0, 100, 30, 5)
    w_att   = st.slider("Attendance Record Weight (%):", 0, 100, 20, 5)
    w_lms   = st.slider("LMS Activity Weight (%):", 0, 100, 15, 5)
    w_plac  = st.slider("Placement Readiness Weight (%):", 0, 100, 20, 5)
    w_skills= st.slider("Skills & Extracurricular Weight (%):", 0, 100, 10, 5)
    w_feed  = st.slider("Student Feedback Weight (%):", 0, 100, 5, 5)

    custom_weights = {
        "academic": w_acad / 100.0, "attendance": w_att / 100.0,
        "lms": w_lms / 100.0, "placement": w_plac / 100.0,
        "skills": w_skills / 100.0, "engagement_feedback": w_feed / 100.0,
    }

    is_valid, total_pct, err_msg = validate_weights(custom_weights)
    if is_valid:
        st.success(f"Weights Total: {total_pct:.1f}% ✓")
        if st.button("🔄 Recalculate All Student Scores", type="primary"):
            scored, _ = process_student_pipeline(df_students, custom_weights, DEFAULT_THRESHOLDS)
            sync_students_to_db(scored, current_user=current_user)
            st.success("All student scores and risk tiers successfully recomputed!")
            st.rerun()
    else:
        st.error(err_msg)

    # Staff Management section
    st.markdown("---")
    st.markdown("#### 👨‍🏫 Faculty & Mentor Directory")
    df_int = get_interventions(current_user=current_user)
    faculty_list = [
        {"name": "Dr. Ananya Sharma", "email": "dr.sharma@campus.edu", "department": "Computer Science & Engineering", "designation": "Associate Professor & Placement Coordinator"},
        {"name": "Prof. Rajesh Kulkarni", "email": "prof.rajesh@campus.edu", "department": "Mechanical Engineering", "designation": "Senior Faculty Mentor & HOD"},
    ]
    for f in faculty_list:
        assigned_students = df_students[df_students["mentor_email"] == f["email"]] if not df_students.empty and "mentor_email" in df_students.columns else pd.DataFrame()
        assigned_int = df_int[df_int["owner_email"] == f["email"]] if not df_int.empty and "owner_email" in df_int.columns else pd.DataFrame()
        pending_int = len(assigned_int[assigned_int["status"] != "Completed"]) if not assigned_int.empty else 0
        with st.expander(f"📌 {f['name']} — {f['department']}", expanded=True):
            cf1, cf2, cf3 = st.columns(3)
            with cf1:
                st.write(f"**Email:** `{f['email']}`")
                st.write(f"**Role:** {f['designation']}")
            with cf2:
                st.metric("Assigned Mentees", len(assigned_students))
            with cf3:
                st.metric("Pending Interventions", pending_int)
