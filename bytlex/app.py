"""
CampusIQ / StudentSignals: AI-Powered Student Analytics and Success Platform
HacXLerate 2026 Challenge | KPMG in India

Master Application Entrypoint — redesigned with the StudentSignals Design System.
"""

import os
import streamlit as st
import pandas as pd

from src.database import (
    init_database,
    sync_students_to_db,
    get_all_students,
    is_using_supabase,
)
from src.auth import (
    init_session_state,
    render_login_gateway,
)
from src.ui_theme import inject_css, render_sidebar, render_topbar
from src.views.admin_view import render_admin_dashboard
from src.views.staff_view import render_staff_dashboard
from src.views.student_view import render_student_dashboard
from src.sample_data import (
    DEFAULT_DATA_PATH,
    ensure_demo_student_records,
    generate_synthetic_students,
)
from src.analytics import process_student_pipeline, DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS

# ─────────────────────────────────────────────────────────────────
# 1. Page Config
# ─────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="StudentSignals | AI-Powered Student Success Platform",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────────────
# 2. Inject Design System CSS
# ─────────────────────────────────────────────────────────────────
inject_css()

# ─────────────────────────────────────────────────────────────────
# 3. Initialize Database & Seed Records
# ─────────────────────────────────────────────────────────────────
try:
    init_database()
    if not is_using_supabase():
        existing_students = get_all_students()
        if existing_students.empty:
            if os.path.exists(DEFAULT_DATA_PATH):
                df_seed = pd.read_csv(DEFAULT_DATA_PATH)
            else:
                df_seed = generate_synthetic_students(150, DEFAULT_DATA_PATH)
        else:
            df_seed = existing_students

        existing_ids = set(
            existing_students.get("student_id", pd.Series(dtype=str)).astype(str)
        )
        df_seed = ensure_demo_student_records(df_seed)
        students_to_seed = df_seed[
            ~df_seed["student_id"].astype(str).isin(existing_ids)
        ]
        if not students_to_seed.empty:
            scored_seed, _ = process_student_pipeline(
                students_to_seed, DEFAULT_WEIGHTS, DEFAULT_THRESHOLDS
            )
            sync_students_to_db(scored_seed)
except Exception as e:
    st.error(
        f"Database initialization failed. The application cannot continue safely: {e}"
    )
    st.stop()

# ─────────────────────────────────────────────────────────────────
# 4. Authentication lifecycle
# ─────────────────────────────────────────────────────────────────
init_session_state()

if not st.session_state.get("authenticated", False):
    render_login_gateway()
else:
    current_user = st.session_state.get("current_user", {})
    user_role = current_user.get("role", "student")

    # ── Sidebar (dark navy) ───────────────────────────────────
    selected_nav = render_sidebar(current_user)

    # ── Top bar (white) ───────────────────────────────────────
    render_topbar(current_user)
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

    # ── Route to correct dashboard ────────────────────────────
    if user_role == "admin":
        render_admin_dashboard(current_user, selected_nav)
    elif user_role == "staff":
        render_staff_dashboard(current_user, selected_nav)
    elif user_role == "student":
        render_student_dashboard(current_user, selected_nav)
    else:
        st.error(f"Unknown authorization role '{user_role}'.")
        if st.button("Return to Login Gateway"):
            st.session_state["authenticated"] = False
            st.rerun()

    # ── Footer ────────────────────────────────────────────────
    st.markdown(
        """
        <div class="ss-footer">
            StudentSignals &bull; AI-Powered Student Analytics &amp; Success Platform
            &bull; KPMG in India Challenge &bull; HacXLerate 2026
        </div>
        """,
        unsafe_allow_html=True,
    )
