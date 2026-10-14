"""
StudentSignals: Shared UI Theme & Design System
Provides consistent CSS, sidebar, KPI cards, and reusable components
across Admin, Staff, and Student portals.
"""

import streamlit as st
from typing import Dict, Any, Optional


# ─────────────────────────────────────────────────────────────────
# DESIGN TOKENS
# ─────────────────────────────────────────────────────────────────
COLORS = {
    "bg":          "#F5F7FB",
    "sidebar":     "#14233F",
    "sidebar_hover":"#1E3A5F",
    "topbar":      "#FFFFFF",
    "accent":      "#2878F0",
    "accent_light":"#E8F0FE",
    "card":        "#FFFFFF",
    "border":      "#E4E9F0",
    "text_primary":"#0F172A",
    "text_muted":  "#64748B",
    "red":         "#EF4444",
    "red_light":   "#FEE2E2",
    "amber":       "#F59E0B",
    "amber_light": "#FEF3C7",
    "green":       "#10B981",
    "green_light": "#D1FAE5",
    "purple":      "#8B5CF6",
    "purple_light":"#EDE9FE",
    "blue_light":  "#EFF6FF",
}

FULL_CSS = """
<style>
/* ── Google Fonts ─────────────────────────────────────────── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Base reset ───────────────────────────────────────────── */
html, body, [class*="css"], .stMarkdown, .stText, .stCaption,
section[data-testid="stSidebar"] * {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
}

/* ── App background ───────────────────────────────────────── */
.stApp { background-color: #F5F7FB; }

/* ── Sidebar ──────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
    background-color: #14233F !important;
    border-right: 1px solid #1E3A5F;
}
section[data-testid="stSidebar"] .css-1d391kg,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] div {
    color: #CBD5E1 !important;
}
/* Sidebar radio nav items */
section[data-testid="stSidebar"] div[data-testid="stRadio"] > div[role="radiogroup"] {
    background: transparent !important;
    border: none !important;
    padding: 0 !important;
    gap: 2px !important;
    display: flex;
    flex-direction: column;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label {
    padding: 10px 14px !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
    font-size: 0.88rem !important;
    color: #94A3B8 !important;
    cursor: pointer;
    transition: all 0.15s ease;
    display: flex;
    align-items: center;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] label:hover {
    background: #1E3A5F !important;
    color: #E2E8F0 !important;
}
/* Active sidebar item */
section[data-testid="stSidebar"] div[data-testid="stRadio"] label[data-baseweb="radio"] input:checked + div {
    background: #2878F0 !important;
}
section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] label:has(input:checked) {
    background: #2878F0 !important;
    color: #FFFFFF !important;
}
/* Hide radio button circle in sidebar */
section[data-testid="stSidebar"] div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}
/* Hide radio button circle in main content pill nav too */
div[data-testid="stRadio"] div[role="radiogroup"] > label > div:first-child {
    display: none !important;
}

/* ── Topbar / Header area ─────────────────────────────────── */
.ss-topbar {
    background: #FFFFFF;
    border-bottom: 1px solid #E4E9F0;
    padding: 12px 20px;
    border-radius: 0;
    margin-bottom: 0;
    display: flex;
    align-items: center;
    justify-content: space-between;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}

/* ── Page heading ─────────────────────────────────────────── */
.ss-page-title {
    font-size: 1.5rem;
    font-weight: 800;
    color: #0F172A;
    margin: 0 0 2px 0;
    line-height: 1.2;
}
.ss-page-subtitle {
    font-size: 0.84rem;
    color: #64748B;
    margin: 0;
    font-weight: 400;
}

/* ── KPI Cards ────────────────────────────────────────────── */
.ss-kpi-card {
    background: #FFFFFF;
    border: 1px solid #E4E9F0;
    border-radius: 12px;
    padding: 18px 20px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    display: flex;
    align-items: flex-start;
    gap: 14px;
    min-height: 90px;
}
.ss-kpi-icon {
    width: 42px;
    height: 42px;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    flex-shrink: 0;
}
.ss-kpi-body { flex: 1; }
.ss-kpi-label {
    font-size: 0.75rem;
    font-weight: 600;
    color: #64748B;
    text-transform: uppercase;
    letter-spacing: 0.04em;
    margin: 0 0 4px 0;
}
.ss-kpi-value {
    font-size: 1.75rem;
    font-weight: 800;
    color: #0F172A;
    line-height: 1;
    margin: 0;
}
.ss-kpi-sub {
    font-size: 0.74rem;
    color: #94A3B8;
    margin: 4px 0 0 0;
}

/* ── White content card ───────────────────────────────────── */
.ss-card {
    background: #FFFFFF;
    border: 1px solid #E4E9F0;
    border-radius: 12px;
    padding: 20px 22px;
    box-shadow: 0 1px 4px rgba(0,0,0,0.04);
    margin-bottom: 18px;
}
.ss-card-title {
    font-size: 1.0rem;
    font-weight: 700;
    color: #0F172A;
    margin: 0 0 14px 0;
    padding-bottom: 10px;
    border-bottom: 1px solid #F1F5F9;
}

/* ── Status badges ────────────────────────────────────────── */
.ss-badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.03em;
}
.ss-badge-red    { background:#FEE2E2; color:#B91C1C; }
.ss-badge-amber  { background:#FEF3C7; color:#92400E; }
.ss-badge-green  { background:#D1FAE5; color:#065F46; }
.ss-badge-blue   { background:#DBEAFE; color:#1E40AF; }
.ss-badge-purple { background:#EDE9FE; color:#5B21B6; }
.ss-badge-gray   { background:#F1F5F9; color:#475569; }

/* ── Main content metrics override ───────────────────────── */
div[data-testid="stMetricValue"] {
    font-size: 1.6rem !important;
    font-weight: 800 !important;
    color: #0F172A !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 0.76rem !important;
    font-weight: 600 !important;
    color: #64748B !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}
[data-testid="stMetricDeltaIcon-Up"],
[data-testid="stMetricDeltaIcon-Down"] { font-size: 0.8rem !important; }

/* ── Main nav radio pills (horizontal) ───────────────────── */
div[data-testid="stRadio"] > div[role="radiogroup"] {
    background: #FFFFFF;
    padding: 4px;
    border-radius: 10px;
    border: 1px solid #E4E9F0;
    gap: 4px;
    display: inline-flex;
}
div[data-testid="stRadio"] label {
    padding: 6px 16px !important;
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.82rem !important;
    cursor: pointer;
}
div[data-testid="stRadio"] label:has(input:checked) {
    background: #2878F0 !important;
    color: #FFFFFF !important;
}

/* ── Buttons ──────────────────────────────────────────────── */
.stButton > button {
    border-radius: 8px !important;
    font-weight: 600 !important;
    font-size: 0.84rem !important;
    transition: all 0.15s ease !important;
}
.stButton > button[kind="primary"] {
    background: #2878F0 !important;
    border-color: #2878F0 !important;
}
.stButton > button[kind="primary"]:hover {
    background: #1E5FD4 !important;
    border-color: #1E5FD4 !important;
}

/* ── Dataframes & tables ──────────────────────────────────── */
.stDataFrame { border-radius: 8px; overflow: hidden; }
.stDataFrame thead tr th {
    background: #F8FAFC !important;
    font-size: 0.78rem !important;
    font-weight: 700 !important;
    color: #475569 !important;
    text-transform: uppercase;
    letter-spacing: 0.04em;
}

/* ── Form elements ────────────────────────────────────────── */
.stTextInput input, .stSelectbox select, .stTextArea textarea {
    border-radius: 8px !important;
    border-color: #E4E9F0 !important;
    font-size: 0.88rem !important;
}
.stTextInput input:focus, .stSelectbox select:focus, .stTextArea textarea:focus {
    border-color: #2878F0 !important;
    box-shadow: 0 0 0 3px rgba(40,120,240,0.1) !important;
}

/* ── Alerts & info boxes ──────────────────────────────────── */
.stAlert { border-radius: 8px !important; }

/* ── Expanders ────────────────────────────────────────────── */
details { border-radius: 8px !important; border: 1px solid #E4E9F0 !important; }

/* ── Sidebar brand ────────────────────────────────────────── */
.ss-sidebar-brand {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 0 4px 20px 4px;
    border-bottom: 1px solid #1E3A5F;
    margin-bottom: 16px;
}
.ss-sidebar-logo {
    width: 38px;
    height: 38px;
    background: #2878F0;
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.3rem;
    flex-shrink: 0;
}
.ss-sidebar-name {
    font-size: 1.0rem;
    font-weight: 800;
    color: #E2E8F0 !important;
    margin: 0;
}
.ss-sidebar-sub {
    font-size: 0.68rem;
    color: #64748B !important;
    margin: 1px 0 0 0;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.06em;
}

/* ── Quick action cards ───────────────────────────────────── */
.ss-action-card {
    background: #FFFFFF;
    border: 1px solid #E4E9F0;
    border-radius: 10px;
    padding: 14px 16px;
    cursor: pointer;
    transition: all 0.15s ease;
    text-align: center;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
}
.ss-action-card:hover {
    border-color: #2878F0;
    box-shadow: 0 4px 12px rgba(40,120,240,0.1);
    transform: translateY(-1px);
}
.ss-action-icon { font-size: 1.4rem; margin-bottom: 6px; }
.ss-action-label {
    font-size: 0.78rem;
    font-weight: 600;
    color: #0F172A;
    margin: 0;
}

/* ── Login gateway ────────────────────────────────────────── */
.ss-login-card {
    background: #FFFFFF;
    border: 1px solid #E4E9F0;
    border-radius: 16px;
    padding: 36px;
    box-shadow: 0 10px 40px rgba(0,0,0,0.07);
    max-width: 480px;
    margin: 0 auto;
}

/* ── Demo mode badge ──────────────────────────────────────── */
.ss-demo-badge {
    background: #FEF3C7;
    color: #92400E;
    border: 1px solid #FDE68A;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: inline-block;
}
.ss-supabase-badge {
    background: #D1FAE5;
    color: #065F46;
    border: 1px solid #6EE7B7;
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.06em;
    display: inline-block;
}

/* ── Scrollbar ────────────────────────────────────────────── */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #F1F5F9; }
::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 3px; }

/* ── Footer ───────────────────────────────────────────────── */
.ss-footer {
    text-align: center;
    color: #94A3B8;
    font-size: 0.74rem;
    padding: 28px 0 14px 0;
    border-top: 1px solid #E4E9F0;
    margin-top: 36px;
}
</style>
"""


def inject_css() -> None:
    """Inject the full design-system CSS into the page."""
    st.markdown(FULL_CSS, unsafe_allow_html=True)


def kpi_card(icon: str, label: str, value: str, icon_bg: str, icon_color: str,
             sub: Optional[str] = None) -> str:
    """Return an HTML KPI card string."""
    sub_html = f'<p class="ss-kpi-sub">{sub}</p>' if sub else ""
    return f"""
    <div class="ss-kpi-card">
        <div class="ss-kpi-icon" style="background:{icon_bg}; color:{icon_color};">
            {icon}
        </div>
        <div class="ss-kpi-body">
            <p class="ss-kpi-label">{label}</p>
            <p class="ss-kpi-value">{value}</p>
            {sub_html}
        </div>
    </div>
    """


def card_open(title: str = "") -> str:
    title_html = f'<p class="ss-card-title">{title}</p>' if title else ""
    return f'<div class="ss-card">{title_html}'


def card_close() -> str:
    return "</div>"


def page_header(title: str, subtitle: str = "") -> None:
    sub = f'<p class="ss-page-subtitle">{subtitle}</p>' if subtitle else ""
    st.markdown(
        f"""
        <div style="margin-bottom:18px;">
            <h1 class="ss-page-title">{title}</h1>
            {sub}
        </div>
        """,
        unsafe_allow_html=True,
    )


def risk_badge(risk_level: str) -> str:
    mapping = {
        "High Risk":   "ss-badge-red",
        "Medium Risk": "ss-badge-amber",
        "Low Risk":    "ss-badge-green",
    }
    cls = mapping.get(risk_level, "ss-badge-gray")
    return f'<span class="ss-badge {cls}">{risk_level}</span>'


def render_sidebar(current_user: Dict[str, Any], nav_key: str = "sidebar_nav") -> str:
    """
    Render the dark-navy sidebar with branding + navigation.
    Returns the selected nav item label.
    """
    role = current_user.get("role", "student")
    name = current_user.get("name", "User")
    initials = "".join(w[0].upper() for w in name.split()[:2])

    if role == "admin":
        nav_items = [
            "🏠  Dashboard",
            "📥  Upload Data",
            "👥  Student Risk List",
            "📋  Interventions",
            "💡  AI Insights",
            "🏫  School Comparison",
            "📊  Reports & Analytics",
            "⚙️  Settings",
        ]
    elif role == "staff":
        nav_items = [
            "🏠  Dashboard",
            "👥  Assigned Mentees",
            "📋  Interventions",
            "💡  Early Warning",
        ]
    else:
        nav_items = [
            "🏠  My Progress",
            "🧠  AI Academic Mentor",
            "💼  Placement & Career Hub",
            "🎙️  Mock Interview Studio",
            "📄  Resume Builder",
        ]

    with st.sidebar:
        # Brand
        st.markdown(
            f"""
            <div class="ss-sidebar-brand">
                <div class="ss-sidebar-logo">🎓</div>
                <div>
                    <p class="ss-sidebar-name">StudentSignals</p>
                    <p class="ss-sidebar-sub">AI-Powered Student Success</p>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Navigation
        selected = st.radio(
            "Navigation",
            options=nav_items,
            label_visibility="collapsed",
            key=nav_key,
        )

        # Spacer
        st.markdown("<div style='flex:1'></div>", unsafe_allow_html=True)
        st.markdown("---")

        # User info
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:10px; padding:4px 0;">
                <div style="width:34px;height:34px;background:#2878F0;border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            color:#fff;font-weight:700;font-size:0.82rem;flex-shrink:0;">
                    {initials}
                </div>
                <div>
                    <div style="font-size:0.84rem;font-weight:600;color:#E2E8F0;">{name}</div>
                    <div style="font-size:0.72rem;color:#64748B;text-transform:uppercase;">{role}</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        from src.auth import logout_user
        if st.button("🚪  Sign Out", use_container_width=True, key="sidebar_signout"):
            logout_user()

    return selected


def render_topbar(current_user: Dict[str, Any]) -> None:
    """Render the white top navigation bar."""
    from src.database import is_using_supabase
    from src.auth import demo_login_enabled

    role = current_user.get("role", "student")
    name = current_user.get("name", "User")
    is_supa = is_using_supabase()
    is_demo = demo_login_enabled()

    badge = (
        '<span class="ss-supabase-badge">🟢 Supabase Connected</span>'
        if is_supa
        else '<span class="ss-demo-badge">🔶 Demo Mode</span>'
    )

    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(
            f"""
            <div style="display:flex; align-items:center; gap:12px; padding:6px 0;">
                {badge}
                <span style="font-size:0.82rem; color:#64748B;">
                    Signed in as <strong style="color:#0F172A;">{name}</strong>
                    &nbsp;·&nbsp;<span style="text-transform:uppercase;font-size:0.75rem;
                    background:#EFF6FF;color:#1D4ED8;padding:2px 8px;border-radius:12px;
                    font-weight:700;">{role}</span>
                </span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with col2:
        if is_demo:
            from src.auth import quick_demo_login
            opts = [
                "Admin",
                "Faculty (Dr. Sharma)",
                "Student – Karan (Academic Risk)",
                "Student – Pranav (Placement Risk)",
                "Student – Simran (Placed)",
            ]
            idx = 0 if role == "admin" else 1 if role == "staff" else 2
            switch = st.selectbox(
                "Switch:",
                options=opts,
                index=idx,
                label_visibility="collapsed",
                key="topbar_role_switch",
            )
            if "Admin" in switch and role != "admin":
                quick_demo_login("admin")
            elif "Faculty" in switch and role != "staff":
                quick_demo_login("staff")
            elif "Karan" in switch and current_user.get("student_id") != "STU2021004":
                quick_demo_login("student", "STU2021004")
            elif "Pranav" in switch and current_user.get("student_id") != "STU2021002":
                quick_demo_login("student", "STU2021002")
            elif "Simran" in switch and current_user.get("student_id") != "STU2021007":
                quick_demo_login("student", "STU2021007")
