"""
CampusIQ: Authentication, Role Authorization, and Session Management
Implements the professional login gateway, trusted role verification,
session state lifecycle, and 1-click hackathon demo access.
"""

import os
import streamlit as st
from typing import Optional, Dict, Any
from src.database import authenticate_user, is_using_supabase, sign_out_supabase_user


def demo_login_enabled() -> bool:
    """Enable demo shortcuts by default on local SQLite; allow explicit opt-out."""
    enabled = os.getenv("CAMPUSIQ_ENABLE_DEMO_LOGIN", "true").strip().lower()
    return enabled in {"1", "true", "yes"} and not is_using_supabase()


def init_session_state() -> None:
    """Initializes session variables for authentication and role guards."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "current_user" not in st.session_state:
        st.session_state["current_user"] = None
    if "selected_role_login" not in st.session_state:
        st.session_state["selected_role_login"] = None
    if "login_error" not in st.session_state:
        st.session_state["login_error"] = None
    if "logout_warning" not in st.session_state:
        st.session_state["logout_warning"] = None


def login_user(user_dict: Dict[str, Any]) -> None:
    """Sets authenticated session state."""
    st.session_state["authenticated"] = True
    st.session_state["current_user"] = user_dict
    st.session_state["login_error"] = None
    st.session_state["logout_warning"] = None
    st.rerun()


def logout_user() -> None:
    """Clears session and redirects to gateway."""
    user = st.session_state.get("current_user")
    if is_using_supabase() and user and not sign_out_supabase_user(user):
        st.session_state["logout_warning"] = (
            "You were signed out on this device, but the identity provider could not "
            "revoke the remote session. It will expire according to your Supabase Auth settings."
        )
    st.session_state["authenticated"] = False
    st.session_state["current_user"] = None
    st.session_state["selected_role_login"] = None
    st.session_state["login_error"] = None
    st.rerun()


def quick_demo_login(role: str, student_id: Optional[str] = None) -> None:
    """Authenticate a documented demo account when local demo shortcuts are enabled."""
    if not demo_login_enabled():
        st.session_state["login_error"] = (
            "One-click demo login is disabled. Sign in with your institutional credentials."
        )
        return

    if role == "admin":
        email = "admin@campus.edu"
        password = "AdminPass2026!"
    elif role == "staff":
        email = "dr.sharma@campus.edu"
        password = "StaffPass2026!"
    else:
        email = student_id if student_id else "STU2021004"
        password = "StudentPass2026!"

    ok, user_data, err = authenticate_user(email, password, role)
    if ok and user_data:
        login_user(user_data)
    else:
        st.session_state["login_error"] = err


def render_login_gateway() -> None:
    """
    Renders the premium login gateway matching the StudentSignals design system.
    Dark left panel + white form card on the right.
    """
    init_session_state()

    from src.ui_theme import inject_css
    inject_css()

    if st.session_state.get("logout_warning"):
        st.warning(st.session_state["logout_warning"])

    # Full-page two-panel layout via columns
    left_col, right_col = st.columns([1.1, 1])

    # ── LEFT: Dark branded panel ──────────────────────────────
    with left_col:
        st.markdown(
            """
            <div style="
                background: linear-gradient(145deg, #14233F 0%, #1a3a6b 100%);
                border-radius: 20px;
                padding: 60px 48px;
                min-height: 560px;
                display: flex;
                flex-direction: column;
                justify-content: center;
            ">
                <div style="display:flex;align-items:center;gap:14px;margin-bottom:32px;">
                    <div style="width:54px;height:54px;background:#2878F0;border-radius:14px;
                                display:flex;align-items:center;justify-content:center;font-size:1.8rem;">
                        🎓
                    </div>
                    <div>
                        <div style="font-size:1.6rem;font-weight:800;color:#FFFFFF;">StudentSignals</div>
                        <div style="font-size:0.76rem;color:#64748B;text-transform:uppercase;
                                    letter-spacing:0.08em;font-weight:600;">
                            AI-Powered Student Success
                        </div>
                    </div>
                </div>
                <h2 style="font-size:1.9rem;font-weight:800;color:#FFFFFF;margin:0 0 16px 0;line-height:1.2;">
                    Empower Every<br>Student's Journey
                </h2>
                <p style="color:#94A3B8;font-size:0.92rem;line-height:1.65;margin:0 0 32px 0;">
                    AI-driven early warning, personalized interventions,
                    and institution-wide student analytics for modern campuses.
                </p>
                <div style="display:flex;flex-direction:column;gap:12px;">
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:32px;height:32px;background:rgba(40,120,240,0.2);
                                    border-radius:8px;display:flex;align-items:center;
                                    justify-content:center;font-size:1rem;">🔍</div>
                        <span style="color:#CBD5E1;font-size:0.86rem;">Early-warning risk detection</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:32px;height:32px;background:rgba(40,120,240,0.2);
                                    border-radius:8px;display:flex;align-items:center;
                                    justify-content:center;font-size:1rem;">🤖</div>
                        <span style="color:#CBD5E1;font-size:0.86rem;">AI mentor & career guidance</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:32px;height:32px;background:rgba(40,120,240,0.2);
                                    border-radius:8px;display:flex;align-items:center;
                                    justify-content:center;font-size:1rem;">📊</div>
                        <span style="color:#CBD5E1;font-size:0.86rem;">Institution-wide analytics</span>
                    </div>
                    <div style="display:flex;align-items:center;gap:12px;">
                        <div style="width:32px;height:32px;background:rgba(40,120,240,0.2);
                                    border-radius:8px;display:flex;align-items:center;
                                    justify-content:center;font-size:1rem;">🎯</div>
                        <span style="color:#CBD5E1;font-size:0.86rem;">Smart intervention tracking</span>
                    </div>
                </div>
                <div style="margin-top:40px;padding-top:24px;border-top:1px solid #1E3A5F;">
                    <span style="color:#475569;font-size:0.74rem;">
                        HacXLerate 2026 Challenge &bull; KPMG in India
                    </span>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    # ── RIGHT: Login form card ────────────────────────────────
    with right_col:
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        selected_role = st.session_state.get("selected_role_login")

        if not selected_role:
            # ── Step 1: Role Selection ──
            st.markdown(
                """
                <div style="text-align:center;margin-bottom:28px;">
                    <h2 style="font-size:1.5rem;font-weight:800;color:#0F172A;margin:0 0 6px 0;">
                        Welcome Back
                    </h2>
                    <p style="color:#64748B;font-size:0.88rem;margin:0;">
                        Select your institutional role to continue
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("login_error"):
                st.error(st.session_state["login_error"])

            # Role cards
            r1, r2, r3 = st.columns(3)
            with r1:
                st.markdown(
                    """
                    <div style="background:#FFFFFF;border:1.5px solid #E4E9F0;border-radius:14px;
                                padding:22px 16px;text-align:center;cursor:pointer;">
                        <div style="font-size:2rem;margin-bottom:10px;">🛡️</div>
                        <div style="font-weight:700;color:#0F172A;font-size:0.92rem;">Admin</div>
                        <div style="color:#64748B;font-size:0.75rem;margin-top:4px;">
                            Dean &amp; Operations
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Select Admin", use_container_width=True, key="role_admin"):
                    st.session_state["selected_role_login"] = "admin"
                    st.session_state["login_error"] = None
                    st.rerun()

            with r2:
                st.markdown(
                    """
                    <div style="background:#FFFFFF;border:1.5px solid #E4E9F0;border-radius:14px;
                                padding:22px 16px;text-align:center;cursor:pointer;">
                        <div style="font-size:2rem;margin-bottom:10px;">👥</div>
                        <div style="font-weight:700;color:#0F172A;font-size:0.92rem;">Faculty</div>
                        <div style="color:#64748B;font-size:0.75rem;margin-top:4px;">
                            Mentors &amp; Advisors
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Select Faculty", use_container_width=True, key="role_staff"):
                    st.session_state["selected_role_login"] = "staff"
                    st.session_state["login_error"] = None
                    st.rerun()

            with r3:
                st.markdown(
                    """
                    <div style="background:#FFFFFF;border:1.5px solid #E4E9F0;border-radius:14px;
                                padding:22px 16px;text-align:center;cursor:pointer;">
                        <div style="font-size:2rem;margin-bottom:10px;">🎓</div>
                        <div style="font-weight:700;color:#0F172A;font-size:0.92rem;">Student</div>
                        <div style="color:#64748B;font-size:0.75rem;margin-top:4px;">
                            AI Mentor &amp; Progress
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                if st.button("Select Student", use_container_width=True, key="role_student"):
                    st.session_state["selected_role_login"] = "student"
                    st.session_state["login_error"] = None
                    st.rerun()

            # Demo shortcuts
            if demo_login_enabled():
                st.markdown(
                    """
                    <div style="margin:24px 0 10px;padding:14px 16px;background:#F8FAFC;
                                border:1px solid #E4E9F0;border-radius:10px;">
                        <div style="font-size:0.78rem;font-weight:700;color:#64748B;
                                    text-transform:uppercase;letter-spacing:0.05em;margin-bottom:10px;">
                            ⚡ Hackathon Quick Access
                        </div>
                    """,
                    unsafe_allow_html=True,
                )
                d1, d2 = st.columns(2)
                with d1:
                    if st.button("🛡️ Log in as Admin", use_container_width=True):
                        quick_demo_login("admin")
                    if st.button("🎓 Student – Karan (Academic Risk)", use_container_width=True):
                        quick_demo_login("student", "STU2021004")
                with d2:
                    if st.button("👥 Log in as Dr. Sharma (Faculty)", use_container_width=True):
                        quick_demo_login("staff")
                    if st.button("🎓 Student – Pranav (Placement Risk)", use_container_width=True):
                        quick_demo_login("student", "STU2021002")
                st.markdown("</div>", unsafe_allow_html=True)

        else:
            # ── Step 2: Credential form ──
            role_icons = {"admin": "🛡️", "staff": "👥", "student": "🎓"}
            st.markdown(
                f"""
                <div style="text-align:center;margin-bottom:24px;">
                    <div style="font-size:2.2rem;margin-bottom:8px;">{role_icons.get(selected_role, "🎓")}</div>
                    <h2 style="font-size:1.4rem;font-weight:800;color:#0F172A;margin:0 0 4px 0;">
                        {selected_role.capitalize()} Sign In
                    </h2>
                    <p style="color:#64748B;font-size:0.84rem;margin:0;">
                        Enter your institutional credentials
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            if st.session_state.get("login_error"):
                st.error(st.session_state["login_error"])

            default_email = (
                ""
                if is_using_supabase()
                else "admin@campus.edu"
                if selected_role == "admin"
                else "dr.sharma@campus.edu"
                if selected_role == "staff"
                else "STU2021004"
            )

            with st.form("login_form"):
                label_text = (
                    "Institutional Email:"
                    if is_using_supabase() or selected_role != "student"
                    else "Student ID or College Email:"
                )
                email_input = st.text_input(label_text, value=default_email, placeholder="your@campus.edu").strip()
                password_input = st.text_input("Password:", type="password", placeholder="••••••••")

                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    submit = st.form_submit_button("Sign In →", type="primary", use_container_width=True)
                with col_btn2:
                    back = st.form_submit_button("← Change Role", use_container_width=True)

                if back:
                    st.session_state["selected_role_login"] = None
                    st.session_state["login_error"] = None
                    st.rerun()

                if submit:
                    if not email_input:
                        st.session_state["login_error"] = (
                            "Please enter your institutional email."
                            if is_using_supabase()
                            else "Please enter your email or Student ID."
                        )
                        st.rerun()
                    if not password_input:
                        st.session_state["login_error"] = "Please enter your password."
                        st.rerun()

                    ok, user_data, err = authenticate_user(email_input, password_input, selected_role)
                    if ok and user_data:
                        login_user(user_data)
                    else:
                        st.session_state["login_error"] = err
                        st.rerun()

            if demo_login_enabled():
                if st.button(f"⚡ Quick Sign In as {selected_role.capitalize()}", use_container_width=True):
                    quick_demo_login(selected_role)
