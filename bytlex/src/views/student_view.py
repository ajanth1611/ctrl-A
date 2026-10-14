"""
CampusIQ: Student Companion Portal Views — StudentSignals Design System
Provides Personal Progress Analytics, What-to-do-next prioritizer,
AI Academic Mentor, Placement Assistance Center, Skill Gap Analyzer,
Text Mock Interview Studio, Resume Builder, and Weekly Action Plan.
"""

import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import json
from typing import Dict, Any, List

from src.database import (
    get_student_by_id,
    get_action_tasks_for_student,
    toggle_action_task,
    get_interventions,
)
from src.ai_mentor import (
    SUBJECT_TOPICS,
    CAREER_ROLES_DATA,
    analyze_skill_gaps,
    build_career_roadmap,
    MOCK_INTERVIEW_BANK,
    evaluate_mock_interview_answer,
)
from src.ai_providers import (
    AIProviderError,
    available_ai_providers,
    generate_ai_response,
)
from src.ui_theme import page_header, kpi_card

# ─── Navigation label → internal tab ─────────────────────────────
_NAV_MAP = {
    "🏠  My Progress":             "progress",
    "🧠  AI Academic Mentor":      "ai_mentor",
    "💼  Placement & Career Hub":  "placement",
    "🎙️  Mock Interview Studio":   "interview",
    "📄  Resume Builder":          "resume",
}


def _numeric_or_default(value: Any, default: float) -> float:
    """Return a numeric value, using the supplied default for missing data."""
    if value is None or pd.isna(value):
        return default
    return float(value)


def render_student_dashboard(current_user: Dict[str, Any], selected_nav: str = "") -> None:
    """Renders personalized Student Companion suite driven by sidebar navigation."""
    student_id = current_user.get("student_id")
    if not student_id:
        st.error("This student account is not linked to a student record.")
        return
    student = get_student_by_id(student_id, current_user=current_user)

    if not student:
        st.error(f"Student profile not found for ID '{student_id}'.")
        return

    # Map sidebar nav to internal tab
    tab = _NAV_MAP.get(selected_nav, "progress")

    page_header(
        f"Welcome, {student['name']}",
        f"{student['department']} · Semester {student['semester']} · ID: {student['student_id']}",
    )

    # Horizontal sub-nav pills still available inside the page
    student_tabs = [
        "🎯 My Progress & Next Steps",
        "🧠 AI Academic Mentor",
        "💼 Placement & Career Hub",
        "🎙️ Mock Interview Studio",
        "📄 Smart Resume Builder",
    ]
    tab_default_idx = {
        "progress": 0, "ai_mentor": 1, "placement": 2, "interview": 3, "resume": 4,
    }.get(tab, 0)

    selected_tab = st.radio(
        "Student Hub", options=student_tabs, horizontal=True,
        label_visibility="collapsed", index=tab_default_idx,
    )
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    if "My Progress" in selected_tab:
        render_student_progress_overview(student, current_user)
    elif "AI Academic Mentor" in selected_tab:
        render_ai_academic_mentor(student)
    elif "Placement & Career Hub" in selected_tab:
        render_placement_hub(student)
    elif "Mock Interview Studio" in selected_tab:
        render_mock_interview_studio(student)
    elif "Smart Resume Builder" in selected_tab:
        render_resume_builder(student)


def render_student_progress_overview(
    student: Dict[str, Any],
    current_user: Dict[str, Any],
) -> None:
    """Renders score card, What to do next prioritizer, and personal tasks."""
    score_value = student.get("success_score")
    score_available = score_value is not None and not pd.isna(score_value)
    score = _numeric_or_default(score_value, 0.0)
    att = _numeric_or_default(student.get("attendance_overall"), 80.0)
    cgpa = _numeric_or_default(student.get("cgpa"), 7.5)
    backlogs = int(_numeric_or_default(student.get("backlog_count"), 0.0))
    coding_score = _numeric_or_default(student.get("coding_score"), 50.0)
    readiness_score = _numeric_or_default(student.get("coding_score"), 60.0)
    aptitude_score = _numeric_or_default(student.get("aptitude_score"), 50.0)
    interview_score = _numeric_or_default(student.get("mock_interview_score"), 50.0)
    lms_score = _numeric_or_default(student.get("lms_assignment_completion"), 0.0)
    marks_score = _numeric_or_default(student.get("marks_percentage"), 0.0)

    academic_risk = student.get("academic_risk")
    if academic_risk not in {"High Risk", "Medium Risk", "Low Risk"}:
        if backlogs >= 2 or cgpa < 5.5:
            academic_risk = "High Risk"
        elif backlogs > 0 or cgpa < 6.5:
            academic_risk = "Medium Risk"
        else:
            academic_risk = "Low Risk"

    placement_risk = student.get("placement_risk")
    if placement_risk not in {"High Risk", "Medium Risk", "Low Risk"}:
        if coding_score < 45 or aptitude_score < 50 or interview_score < 45:
            placement_risk = "High Risk"
        elif coding_score < 65 or aptitude_score < 60 or interview_score < 60:
            placement_risk = "Medium Risk"
        else:
            placement_risk = "Low Risk"

    overall_risk = student.get("risk_level")
    if overall_risk not in {"High Risk", "Medium Risk", "Low Risk"}:
        if "High Risk" in {academic_risk, placement_risk} or (
            score_available and score < 50
        ):
            overall_risk = "High Risk"
        elif "Medium Risk" in {academic_risk, placement_risk} or (
            score_available and score < 70
        ):
            overall_risk = "Medium Risk"
        else:
            overall_risk = "Low Risk"

    # Top Cards Row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        score_display = f"{score:.1f}/100" if score_available else "Pending"
        st.metric("Success Score", score_display, help="Explainable Student Success Score")
    with c2:
        st.metric("Cumulative CGPA", f"{cgpa:.2f}", f"{backlogs} Backlog(s)" if backlogs > 0 else "All Clear")
    with c3:
        st.metric("Class Attendance", f"{att:.1f}%", "-Low" if att < 75.0 else "Normal", delta_color="inverse" if att < 75.0 else "normal")
    with c4:
        st.metric("Placement Readiness", f"{readiness_score:.0f}/100", student.get("placement_status", "Eligible"))

    if not score_available:
        st.caption(
            "Your success score has not been calculated yet. The available measures "
            "below are shown independently."
        )

    st.markdown("#### 📊 Progress at a glance")
    progress_columns = st.columns(3)
    progress_items = [
        ("Attendance", att),
        ("Coding", coding_score),
        ("LMS completion", lms_score),
    ]
    if score_available:
        progress_items.insert(0, ("Success score", score))
        progress_items = progress_items[:4]
        progress_columns = st.columns(4)
    for column, (label, value) in zip(progress_columns, progress_items):
        with column:
            st.caption(f"{label}: {value:.1f}%")
            st.progress(int(min(max(value, 0.0), 100.0)))

    dimensions = [
        ("Marks", marks_score),
        ("Attendance", att),
        ("LMS completion", lms_score),
        ("Coding", coding_score),
        ("Aptitude", aptitude_score),
        ("Mock interview", interview_score),
    ]
    measure_fields = {
        "Marks": "marks_percentage",
        "Attendance": "attendance_overall",
        "LMS completion": "lms_assignment_completion",
        "Coding": "coding_score",
        "Aptitude": "aptitude_score",
        "Mock interview": "mock_interview_score",
    }
    chart_data = pd.DataFrame(
        [
            {"Measure": label, "Score": min(max(value, 0.0), 100.0)}
            for label, value in dimensions
            if pd.notna(student.get(measure_fields[label]))
        ]
    )
    if not chart_data.empty:
        figure = px.bar(
            chart_data.sort_values("Score"),
            x="Score",
            y="Measure",
            orientation="h",
            text="Score",
            range_x=[0, 100],
            title="Academic and placement indicators",
            labels={"Score": "Score (%)", "Measure": ""},
        )
        figure.update_traces(
            marker_color="#2563eb",
            texttemplate="%{text:.0f}%",
            textposition="outside",
            cliponaxis=False,
        )
        figure.update_layout(
            height=340,
            margin={"l": 10, "r": 35, "t": 55, "b": 20},
            xaxis={"showgrid": True, "gridcolor": "#e2e8f0", "range": [0, 108]},
            yaxis={"categoryorder": "total ascending"},
            showlegend=False,
        )
        st.plotly_chart(figure, use_container_width=True)

    st.markdown("#### 🩺 Status and recommended actions")
    status_message = (
        f"Overall status: **{overall_risk}** · Academic: **{academic_risk}** · "
        f"Placement: **{placement_risk}**"
    )
    if overall_risk == "High Risk":
        st.error(status_message)
    elif overall_risk == "Medium Risk":
        st.warning(status_message)
    else:
        st.success(status_message)

    recommendations = []
    if att < 75.0:
        recommendations.append(
            ("Attendance is below 75%.", "Attend upcoming classes consistently and contact your advisor to confirm your recovery plan.")
        )
    if backlogs > 0:
        recommendations.append(
            (f"You have {backlogs} active backlog(s).", "Ask your department about the next exam or remedial-support schedule, then plan weekly revision for each subject.")
        )
    if cgpa < 6.5:
        recommendations.append(
            (f"CGPA is {cgpa:.2f}, below the 6.5 progress benchmark.", "Meet your academic advisor and focus study time on the subjects with the lowest marks.")
        )
    if lms_score < 70.0:
        recommendations.append(
            (f"LMS assignment completion is {lms_score:.1f}%.", "Complete overdue LMS work first and set a recurring weekly time to check course deadlines.")
        )
    if coding_score < 65.0:
        recommendations.append(
            (f"Coding score is {coding_score:.1f}/100.", "Practice a small set of coding problems several times each week, then review solutions and retest weak topics.")
        )
    if aptitude_score < 60.0:
        recommendations.append(
            (f"Aptitude score is {aptitude_score:.1f}/100.", "Use timed practice for quantitative and reasoning questions, and review errors after each session.")
        )
    if interview_score < 60.0:
        recommendations.append(
            (f"Mock interview score is {interview_score:.1f}/100.", "Practice concise answers using the situation, action, and result format, then repeat a mock interview.")
        )
    if not recommendations:
        recommendations.append(
            ("No priority gaps were detected in the available measures.", "Keep attendance and assignments on track, and continue regular coding and interview practice.")
        )

    for index, (problem, solution) in enumerate(recommendations, start=1):
        st.markdown(f"**{index}. {problem}**  \n{solution}")

    # Personal Weekly Action Plan Checklist
    st.markdown("##### 📅 Weekly Action Plan Checklist")
    tasks = get_action_tasks_for_student(
        student["student_id"], current_user=current_user
    )

    for t in tasks:
        col_chk, col_info = st.columns([0.5, 9.5])
        with col_chk:
            is_done = bool(t.get("completed", 0))
            new_val = st.checkbox("", value=is_done, key=f"chk_{t['id']}")
            if new_val != is_done:
                toggle_action_task(t["id"], new_val, current_user=current_user)
                st.rerun()

        with col_info:
            strike = "text-decoration: line-through; color: #94a3b8;" if t.get("completed", 0) else ""
            st.markdown(f"""
            <div style="padding: 4px 0; {strike}">
                <strong>{t['title']}</strong> &bull; <span style="font-size: 0.8rem; color: #64748b;">Effort: {t.get('effort_hours', 2)}h &bull; Due: {t.get('due_date', 'Soon')}</span>
                <p style="font-size: 0.82rem; color: #475569; margin: 2px 0;">{t.get('description', '')}</p>
            </div>
            """, unsafe_allow_html=True)


def render_ai_academic_mentor(student: Dict[str, Any]) -> None:
    """Renders AI-assisted learning content and self-assessment quizzes."""
    st.markdown("#### 🧠 AI Academic Mentor & Tutor")
    providers = available_ai_providers()
    if providers:
        st.info(
            "AI requests send only the selected subject, topic, and question to the "
            "chosen provider. Student profile details are not included. Avoid entering "
            "names, contact details, grades, or other sensitive information."
        )
        selected_provider = st.selectbox(
            "AI provider",
            options=providers,
            key="academic_ai_provider",
        )
    else:
        selected_provider = None
        st.caption(
            "Local demo mode: bundled guidance is available. Add an OpenAI or Gemini "
            "API key to your local .env file to enable live AI explanations."
        )

    subjects = list(SUBJECT_TOPICS.keys())
    sel_subject = st.selectbox("Select Subject:", options=subjects)
    subj_data = SUBJECT_TOPICS[sel_subject]

    tab_concept, tab_quiz = st.tabs(["📖 Topic Explainer & Step-by-Step Solving", "📝 Diagnostic Practice Quiz"])

    with tab_concept:
        topics = subj_data["topics"]
        sel_topic = st.selectbox("Choose Syllabus Topic:", options=topics)

        # Show explanation if available or synthetic template
        expl = subj_data.get("explanations", {}).get(sel_topic, {
            "summary": f"Comprehensive exploration of {sel_topic} covering fundamental theory, execution flow, and edge cases.",
            "example": "Standard algorithmic implementation following university curriculum benchmarks.",
            "best_practices": ["Understand invariant conditions.", "Analyze Big-O time and space tradeoffs."],
        })

        st.markdown(f"##### Overview: {sel_topic}")
        st.write(expl["summary"])

        st.markdown("##### 💡 Example & Code Walkthrough")
        st.code(expl["example"], language="python")

        st.markdown("##### 🔑 Key Principles & Best Practices")
        for bp in expl["best_practices"]:
            st.markdown(f"- {bp}")

        st.markdown("---")
        st.markdown("##### 💬 Ask Academic Mentor a Question")
        user_q = st.text_input(
            "Ask about algorithm logic, exam questions, or homework hints:",
            placeholder="e.g. How do I optimize Two Pointers to find triplets?",
            max_chars=4000,
        ).strip()
        consent = False
        if selected_provider:
            consent = st.checkbox(
                f"I agree to send this question and topic to {selected_provider}.",
                key="academic_ai_consent",
            )
        if st.button("Generate Step-by-Step Explanation"):
            if user_q:
                if selected_provider:
                    if consent:
                        try:
                            with st.spinner(f"Getting guidance from {selected_provider}..."):
                                guidance = generate_ai_response(
                                    selected_provider,
                                    "You are a supportive university-level tutor. Explain "
                                    "concepts accurately and step by step, use a small "
                                    "example, mention relevant complexity when appropriate, "
                                    "and encourage learning rather than giving dishonest "
                                    "exam assistance. Never claim a prediction is certain.",
                                    f"Subject: {sel_subject}\nTopic: {sel_topic}\n"
                                    f"Student question: {user_q}",
                                )
                            st.markdown("**AI Mentor Guidance**")
                            st.markdown(guidance)
                            st.caption(
                                f"Generated by {selected_provider}; verify important details."
                            )
                        except AIProviderError as exc:
                            st.error(str(exc))
                    else:
                        st.warning(
                            "Confirm the disclosure above before sending your question."
                        )
                else:
                    st.markdown(f"**Local demo guidance on:** *'{user_q}'*")
                    st.markdown(f"""
                    1. **Problem Analysis:** Identify the input data structure and target condition.
                    2. **Approach for {sel_topic}:** Maintain clear state invariants and compare with a brute-force baseline.
                    3. **Complexity:** Analyze time and auxiliary space for your chosen approach.
                    4. **Next Step:** Test edge cases such as empty input, duplicates, and boundary values.
                    """)
            else:
                st.warning("Please type a question above.")

    with tab_quiz:
        quizzes = subj_data.get("quiz", [])
        if not quizzes:
            st.info("No practice quiz currently available for this subject.")
        else:
            for idx, q in enumerate(quizzes):
                st.markdown(f"**Question {idx + 1}:** {q['question']}")
                picked = st.radio(f"Options for Q{idx + 1}:", options=q["options"], key=f"q_{sel_subject}_{idx}", label_visibility="collapsed")
                if st.button(f"Submit Answer for Q{idx + 1}", key=f"btn_q_{idx}"):
                    correct_text = q["options"][q["correct_index"]]
                    if picked == correct_text:
                        st.success(f"✅ Correct! {q['explanation']}")
                    else:
                        st.error(f"❌ Incorrect. The correct answer is: **{correct_text}**.\n\nExplanation: {q['explanation']}")
                st.markdown("---")


def render_placement_hub(student: Dict[str, Any]) -> None:
    """Renders role readiness, assessed skill gaps, and a personalized career roadmap."""
    st.markdown("#### 💼 Placement Readiness & Career Roadmap")
    st.caption(
        "Role-fit estimates use the assessments currently on file. The roadmap is a "
        "transparent planning aid, not a hiring prediction."
    )

    roles = list(CAREER_ROLES_DATA.keys())
    sel_role = st.selectbox("Select Target Career Role:", options=roles)
    roadmap_col1, roadmap_col2 = st.columns(2)
    with roadmap_col1:
        duration_weeks = st.select_slider(
            "Roadmap duration",
            options=[4, 8, 12],
            value=8,
            format_func=lambda weeks: f"{weeks} weeks",
        )
    with roadmap_col2:
        hours_per_week = st.slider(
            "Time available each week",
            min_value=1,
            max_value=20,
            value=6,
            format="%d hours",
        )

    analysis = analyze_skill_gaps(student, sel_role)
    roadmap = build_career_roadmap(
        student,
        sel_role,
        duration_weeks=duration_weeks,
        hours_per_week=hours_per_week,
    )

    # Readiness Score Gauge
    r_col1, r_col2 = st.columns([1, 2])
    with r_col1:
        st.markdown(f"""
        <div style="background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 12px; padding: 20px; text-align: center;">
            <span style="font-size: 0.78rem; font-weight: 700; color: #64748b; text-transform: uppercase;">
                Role Match Index
            </span>
            <div style="font-size: 2.5rem; font-weight: 800; color: #0284c7; line-height: 1.1; margin-top: 4px;">
                {analysis['readiness_score']}%
            </div>
            <div style="font-size: 0.85rem; color: #475569; margin-top: 6px;">
                Expected Range: <strong>{analysis['salary_range']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with r_col2:
        st.markdown("##### 🎯 Identified Skill Gaps to Close")
        if analysis["gaps"]:
            for g in analysis["gaps"]:
                st.markdown(f"- **{g['skill']}:** Current {g['current']:.0f} / Target {g['target']} (Deficit: **-{g['deficit']:.0f} pts**)")
        else:
            st.success("No significant skill deficits detected for this role! You meet the target benchmarks.")
        if analysis["missing_assessments"]:
            st.warning(
                "Some placement assessments are missing "
                f"({', '.join(analysis['missing_assessments'])}). "
                "The roadmap starts by recommending these baselines; role-fit estimates "
                "use a neutral placeholder until scores are available."
            )

    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)
    st.markdown("##### 🛠️ Recommended Portfolio Projects")
    for proj in analysis["recommended_projects"]:
        st.markdown(f"- 📁 {proj}")

    st.markdown("---")
    st.markdown(f"##### 🧭 Your {duration_weeks}-Week Career Roadmap")
    st.caption(
        f"Designed for **{sel_role}**, using your current assessment scores and "
        f"{hours_per_week} available study hours per week."
    )
    roadmap_text = [
        f"Your {duration_weeks}-week roadmap for {sel_role}. "
        f"Current role readiness is {roadmap['readiness_score']} percent."
    ]
    for milestone in roadmap["milestones"]:
        with st.container(border=True):
            st.markdown(
                f"**{milestone['week_range']} · {milestone['phase']}**  \n"
                f"Focus: **{milestone['focus_skill']}** "
                f"({milestone['current_score']:.0f} now; target {milestone['target_score']}/100)"
            )
            for action in milestone["actions"]:
                st.markdown(f"- {action}")
            st.caption(milestone["completion_check"])
        roadmap_text.append(
            f"{milestone['week_range']}, {milestone['phase']}. "
            f"Focus on {milestone['focus_skill']}. "
            + " ".join(milestone["actions"])
        )

    st.caption(roadmap["disclaimer"])
    st.markdown("###### 🔊 Voice Assistant")
    st.caption(
        "Listen using your browser's speech synthesis. CampusIQ does not capture "
        "microphone audio; text handling depends on your browser and selected voice."
    )
    _render_roadmap_voice_assistant(" ".join(roadmap_text))


def _render_roadmap_voice_assistant(text: str) -> None:
    """Use browser speech synthesis to read the roadmap without transmitting audio."""
    safe_text = (
        json.dumps(text)
        .replace("<", "\\u003c")
        .replace(">", "\\u003e")
        .replace("&", "\\u0026")
        .replace("\u2028", "\\u2028")
        .replace("\u2029", "\\u2029")
    )
    components.html(
        f"""
        <div style="font-family: sans-serif;">
          <button id="speak" type="button">Read my roadmap</button>
          <button id="stop" type="button">Stop</button>
          <span id="status" role="status" aria-live="polite"></span>
        </div>
        <script>
          const root = document.currentScript.parentElement;
          const text = {safe_text};
          const speak = root.querySelector("#speak");
          const stop = root.querySelector("#stop");
          const status = root.querySelector("#status");
          speak.addEventListener("click", () => {{
            if (!("speechSynthesis" in window)) {{
              status.textContent = "Speech playback is not supported by this browser.";
              return;
            }}
            window.speechSynthesis.cancel();
            const utterance = new SpeechSynthesisUtterance(text);
            utterance.onstart = () => status.textContent = "Reading roadmap…";
            utterance.onend = () => status.textContent = "Roadmap finished.";
            utterance.onerror = () => status.textContent = "Speech playback could not start.";
            window.speechSynthesis.speak(utterance);
          }});
          stop.addEventListener("click", () => {{
            if ("speechSynthesis" in window) window.speechSynthesis.cancel();
            status.textContent = "Playback stopped.";
          }});
        </script>
        """,
        height=48,
        scrolling=False,
    )


def render_mock_interview_studio(student: Dict[str, Any]) -> None:
    """Renders text-based mock interview simulator with transparent scoring."""
    st.markdown("#### 🎙️ Text-Based Mock Interview Studio")
    providers = available_ai_providers()
    if providers:
        st.info(
            "AI coaching sends only the selected interview question and your typed "
            "answer to the provider. Do not include personal, confidential, or "
            "identifying information."
        )
        selected_provider = st.selectbox(
            "AI coaching provider",
            options=providers,
            key="interview_ai_provider",
        )
    else:
        selected_provider = None
        st.caption(
            "Practice with bundled questions. Scores use transparent local heuristics. "
            "Add an OpenAI or Gemini key to enable optional AI coaching."
        )

    role_tracks = list(MOCK_INTERVIEW_BANK.keys())
    sel_track = st.selectbox("Choose Interview Track:", options=role_tracks)
    questions = MOCK_INTERVIEW_BANK[sel_track]

    q_titles = [f"Question {q['id']}: {q['category']}" for q in questions]
    q_idx = st.selectbox("Select Question:", options=range(len(questions)), format_func=lambda i: q_titles[i])
    current_q = questions[q_idx]

    st.markdown(f"""
    <div style="background: #f8fafc; border-left: 4px solid #0284c7; padding: 16px; border-radius: 8px; margin-bottom: 16px;">
        <span style="font-size: 0.78rem; font-weight: 700; color: #0369a1; text-transform: uppercase;">
            {current_q['category']}
        </span>
        <h4 style="margin: 6px 0 0 0; color: #0f172a; font-size: 1.05rem;">
            {current_q['question']}
        </h4>
    </div>
    """, unsafe_allow_html=True)

    user_ans = st.text_area(
        "Type your interview response:",
        height=150,
        placeholder="Articulate your thought process clearly...",
        max_chars=5000,
    ).strip()
    consent = False
    if selected_provider:
        consent = st.checkbox(
            f"I agree to send this answer to {selected_provider} for coaching.",
            key="interview_ai_consent",
        )

    if st.button("Evaluate Response", type="primary"):
        eval_res = evaluate_mock_interview_answer(current_q, user_ans)

        st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
        st.markdown(f"### Performance Score: {eval_res['score']} / 100")

        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Technical Accuracy", f"{eval_res['technical_accuracy']}%")
        with s2:
            st.metric("Relevance", f"{eval_res['relevance']}%")
        with s3:
            st.metric("Clarity", f"{eval_res['clarity']}%")

        st.markdown(f"**Feedback:** {eval_res['feedback']}")

        with st.expander("💡 View Model Benchmark Answer"):
            st.write(eval_res["model_answer"])

        if selected_provider and user_ans:
            if consent:
                try:
                    with st.spinner(f"Getting coaching from {selected_provider}..."):
                        coaching = generate_ai_response(
                            selected_provider,
                            "You are a constructive interview coach. Give concise, "
                            "specific feedback on structure, accuracy, clarity, and one "
                            "actionable improvement. Do not invent facts about the candidate "
                            "or assign a hiring outcome.",
                            f"Interview track: {sel_track}\n"
                            f"Question: {current_q['question']}\n"
                            f"Candidate answer: {user_ans}",
                        )
                    st.markdown("#### AI Coaching")
                    st.markdown(coaching)
                    st.caption(
                        f"Generated by {selected_provider}. The numeric score above "
                        "remains the transparent local heuristic score."
                    )
                except AIProviderError as exc:
                    st.error(str(exc))
            else:
                st.warning("Confirm the disclosure above to request AI coaching.")


def render_resume_builder(student: Dict[str, Any]) -> None:
    """Renders interactive resume builder with live formatted preview."""
    st.markdown("#### 📄 Smart Resume Builder & ATS Checker")
    st.caption("Build an ATS-optimized technical resume using validated institutional credentials.")

    with st.form("resume_form"):
        r_col1, r_col2 = st.columns(2)
        with r_col1:
            full_name = st.text_input("Full Name:", value=student["name"])
            email = st.text_input("Email:", value=student.get("email", f"{student['student_id'].lower()}@student.campus.edu"))
            phone = st.text_input("Phone Number:", value="+91 98765 43210")
        with r_col2:
            dept = st.text_input("Degree & Major:", value=f"B.Tech in {student['department']}")
            cgpa_str = st.text_input("CGPA:", value=f"{student.get('cgpa', 8.0)} / 10.0")
            github = st.text_input("GitHub / Portfolio URL:", value=f"github.com/{student['student_id'].lower()}")

        summary = st.text_area(
            "Professional Summary:",
            value=f"Proactive engineering undergraduate with strong foundation in software engineering, academic CGPA of {student.get('cgpa', 8.0)}, and practical skills in data structures and full-stack development.",
        )

        skills = st.text_input("Key Technical Skills (comma separated):", value="C++, Python, SQL, React, Data Structures, Git, PostgreSQL")
        projects = st.text_area("Projects (Title & Description):", value="CampusIQ — AI Student Analytics Platform: Developed explainable scoring engine and intervention system.")

        st.form_submit_button("Update Resume Preview")

    # Formatted Live Preview
    st.markdown("---")
    st.markdown("##### 👁️ Live ATS-Friendly Resume Preview")
    st.markdown(f"""
    <div style="background: #ffffff; border: 1px solid #cbd5e1; border-radius: 8px; padding: 24px; font-family: sans-serif; box-shadow: 0 4px 6px rgba(0,0,0,0.02);">
        <h2 style="margin: 0; text-align: center; color: #0f172a;">{full_name}</h2>
        <p style="text-align: center; font-size: 0.85rem; color: #64748b; margin: 4px 0 16px 0;">
            {email} &bull; {phone} &bull; {github}
        </p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin-bottom: 12px;" />
        <h4 style="margin: 0 0 6px 0; color: #0284c7; text-transform: uppercase; font-size: 0.85rem;">Professional Summary</h4>
        <p style="font-size: 0.85rem; color: #334155; margin-bottom: 14px;">{summary}</p>
        <h4 style="margin: 0 0 6px 0; color: #0284c7; text-transform: uppercase; font-size: 0.85rem;">Education</h4>
        <p style="font-size: 0.85rem; color: #334155; margin-bottom: 14px;">
            <strong>KPMG Institute of Engineering & Technology</strong><br/>
            {dept} &bull; CGPA: {cgpa_str}
        </p>
        <h4 style="margin: 0 0 6px 0; color: #0284c7; text-transform: uppercase; font-size: 0.85rem;">Technical Skills</h4>
        <p style="font-size: 0.85rem; color: #334155; margin-bottom: 14px;">{skills}</p>
        <h4 style="margin: 0 0 6px 0; color: #0284c7; text-transform: uppercase; font-size: 0.85rem;">Key Projects</h4>
        <p style="font-size: 0.85rem; color: #334155; margin-bottom: 0;">{projects}</p>
    </div>
    """, unsafe_allow_html=True)
