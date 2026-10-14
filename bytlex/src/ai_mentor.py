"""
CampusIQ: AI Academic Mentor & Placement Assistance Center
Provides interactive academic concept explanations, syllabus problem solving,
quizzes, career roadmaps, skill gap analysis, text mock interviews, and resume building.
"""

from typing import Dict, List, Any, Optional
import random
from math import isnan

# ==============================================================================
# 1. ACADEMIC MENTOR CONCEPT & QUIZ KNOWLEDGE BASE
# ==============================================================================
SUBJECT_TOPICS: Dict[str, Dict[str, Any]] = {
    "Data Structures & Algorithms": {
        "topics": [
            "Arrays & Two Pointers",
            "Linked Lists & Fast/Slow Pointers",
            "Stacks & Queues (Monotonic Stack)",
            "Binary Trees & BST Traversals",
            "Graphs (BFS, DFS, Dijkstra)",
            "Dynamic Programming (0/1 Knapsack, Memoization)",
        ],
        "explanations": {
            "Arrays & Two Pointers": {
                "summary": "Two Pointers is an algorithmic pattern where two indices traverse a data structure toward each other or in parallel to solve searching problems in O(N) time with O(1) space.",
                "example": "To find two numbers that sum to a target in a sorted array: initialize left=0, right=len-1. If sum > target, decrement right; if sum < target, increment left.",
                "best_practices": ["Always sort array first if not already sorted.", "Watch out for off-by-one errors on loop termination (left < right vs left <= right)."],
            },
            "Dynamic Programming (0/1 Knapsack, Memoization)": {
                "summary": "Dynamic Programming decomposes complex problems into overlapping subproblems with optimal substructure, caching intermediate results to avoid exponential recalculation.",
                "example": "Fibonacci or 0/1 Knapsack: at item i with capacity w, either take item (val + dp[i-1][w-wt]) or skip item (dp[i-1][w]).",
                "best_practices": ["Identify state variables clearly (e.g. current index, remaining capacity).", "Write top-down recursive formula first, then add memoization cache."],
            },
        },
        "quiz": [
            {
                "question": "What is the average and worst-case time complexity of QuickSort?",
                "options": ["O(N log N) average, O(N^2) worst-case", "O(N) average, O(N log N) worst-case", "O(N log N) for both", "O(N^2) for both"],
                "correct_index": 0,
                "explanation": "QuickSort averages O(N log N) when pivot partitions array evenly. In the worst case (e.g. already sorted array with naive pivot selection), it degrades to O(N^2).",
            },
            {
                "question": "Which data structure is fundamentally used in Breadth-First Search (BFS)?",
                "options": ["Stack", "Queue", "Priority Queue", "Binary Search Tree"],
                "correct_index": 1,
                "explanation": "BFS explores nodes level by level using a FIFO Queue to visit neighbors in order of discovery.",
            },
        ],
    },
    "Database Management Systems": {
        "topics": [
            "ACID Properties & Transaction Isolation",
            "Relational Normalization (1NF, 2NF, 3NF, BCNF)",
            "Indexing (B+ Trees, Hash Indexes, Covering Index)",
            "SQL Query Optimization & EXPLAIN Plans",
            "Distributed Databases & CAP Theorem",
        ],
        "explanations": {
            "ACID Properties & Transaction Isolation": {
                "summary": "ACID ensures reliable database transaction processing: Atomicity (all-or-nothing), Consistency (rules preserved), Isolation (concurrency control), and Durability (committed data survives crashes).",
                "example": "Bank transfer: debiting Account A and crediting Account B must either both succeed or both rollback to maintain consistency.",
                "best_practices": ["Keep transactions short to prevent row-lock contention.", "Choose appropriate isolation level (Read Committed vs Serializable) based on consistency requirements."],
            },
            "Indexing (B+ Trees, Hash Indexes, Covering Index)": {
                "summary": "A database index is a data structure (typically a balanced B+ Tree) that optimizes query lookup from O(N) full table scans to O(log N) tree navigations.",
                "example": "Creating an index on `student_id` allows instantaneous lookups across 100,000 student records without disk-scanning every row.",
                "best_practices": ["Index high-cardinality foreign keys and search query columns.", "Avoid over-indexing write-heavy tables because indexes must be updated on every INSERT/UPDATE."],
            },
        },
        "quiz": [
            {
                "question": "What does a 3NF (Third Normal Form) relation guarantee?",
                "options": ["No transitive functional dependencies on non-prime attributes", "No multi-valued attributes", "All attributes depend on part of composite key", "No duplicate rows allowed"],
                "correct_index": 0,
                "explanation": "3NF requires the table to be in 2NF and eliminate transitive dependencies: every non-key attribute must depend directly on the primary key, and nothing but the primary key.",
            },
            {
                "question": "Why are B+ Trees preferred over Binary Search Trees in relational disk storage?",
                "options": ["B+ Trees have high fan-out, minimizing expensive disk I/O operations", "B+ Trees consume zero RAM", "Binary Search Trees cannot store numbers", "B+ Trees do not require sorting"],
                "correct_index": 0,
                "explanation": "B+ Trees have large branching factors (fan-out of hundreds of keys per node), keeping tree depth very shallow (3-4 levels) and drastically minimizing disk page reads.",
            },
        ],
    },
    "Operating Systems": {
        "topics": [
            "Process Scheduling (Round Robin, CFS, Priority)",
            "Concurrency, Mutexes, Semaphores & Deadlocks",
            "Virtual Memory & Paging (Page Replacement Algorithms)",
            "Inter-Process Communication (Pipes, Sockets, Shared Memory)",
        ],
        "explanations": {
            "Concurrency, Mutexes, Semaphores & Deadlocks": {
                "summary": "Concurrency allows multiple execution threads to share resources. Deadlock occurs when 4 Coffman conditions hold: Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait.",
                "example": "Dining Philosophers: if every philosopher picks up their left fork simultaneously, circular wait causes deadlock.",
                "best_practices": ["Always acquire locks in a globally defined, consistent order to break circular wait.", "Use lock timeouts or RAII wrappers to avoid leaking acquired locks."],
            },
        },
        "quiz": [
            {
                "question": "Which Coffman condition is eliminated by enforcing a strict global ordering on resource acquisition?",
                "options": ["Circular Wait", "Mutual Exclusion", "No Preemption", "Hold and Wait"],
                "correct_index": 0,
                "explanation": "Strict lock ordering prevents a circular dependency chain from forming, eliminating Circular Wait.",
            },
        ],
    },
}


# ==============================================================================
# 2. CAREER ROLES & SKILL GAP ENGINE
# ==============================================================================
CAREER_ROLES_DATA: Dict[str, Dict[str, Any]] = {
    "Full Stack Software Engineer": {
        "department": "Computer Science & Engineering",
        "description": "Architects, develops, and deploys scalable web applications across modern frontend frameworks, backend REST/GraphQL APIs, and relational databases.",
        "skills_required": {
            "Data Structures & Algorithms": 80,
            "Python / Node.js Backend": 75,
            "React / Modern Frontend": 80,
            "SQL & Database Design": 75,
            "System Design & Scalability": 70,
            "Git & CI/CD Pipelines": 70,
        },
        "target_benchmarks": {"aptitude": 70, "coding": 75, "mock_interview": 70},
        "salary_range": "₹8.5 - 18.0 LPA",
        "recommended_projects": [
            "Build an explainable analytics SaaS with role-based auth and automated CI/CD.",
            "Develop a real-time collaborative whiteboard using WebSockets and Redis Pub/Sub.",
        ],
    },
    "AI / Machine Learning Engineer": {
        "department": "Artificial Intelligence & Data Science",
        "description": "Researches, builds, fine-tunes, and deploys predictive machine learning models, neural networks, and generative AI pipelines into production systems.",
        "skills_required": {
            "Python & NumPy / Pandas": 90,
            "Machine Learning Algorithms": 85,
            "Deep Learning (PyTorch / TensorFlow)": 80,
            "NLP & LLM Architectures": 75,
            "Linear Algebra & Statistics": 80,
            "MLOps & Model Deployment": 70,
        },
        "target_benchmarks": {"aptitude": 75, "coding": 80, "mock_interview": 70},
        "salary_range": "₹10.0 - 22.0 LPA",
        "recommended_projects": [
            "Train and deploy an explainable student dropout risk classifier with SHAP explainability.",
            "Build a RAG (Retrieval-Augmented Generation) assistant indexing college syllabus PDFs with vector embeddings.",
        ],
    },
    "Data Analyst & Business Intelligence": {
        "department": "Information Technology",
        "description": "Transforms institutional and enterprise data into actionable visual insights, executive dashboards, and predictive trend reports.",
        "skills_required": {
            "Advanced SQL & Warehousing": 85,
            "PowerBI / Tableau Dashboarding": 80,
            "Python Data Analysis": 75,
            "Business Statistics": 75,
            "Excel Modeling": 80,
            "Stakeholder Presentation": 80,
        },
        "target_benchmarks": {"aptitude": 70, "coding": 60, "mock_interview": 75},
        "salary_range": "₹6.5 - 14.0 LPA",
        "recommended_projects": [
            "Create an executive student success dashboard analyzing semester trends and intervention ROI.",
            "Conduct cohort retention analysis on university LMS assignment completion records.",
        ],
    },
    "Cloud & DevOps Engineer": {
        "department": "Computer Science & Engineering",
        "description": "Automates deployment pipelines, cloud infrastructure provisioning, container orchestration, and site reliability monitoring.",
        "skills_required": {
            "Linux System Administration": 80,
            "Docker & Kubernetes": 80,
            "Cloud Infrastructure (AWS/Azure)": 85,
            "Terraform (IaC)": 75,
            "CI/CD Pipelines": 80,
            "Networking & Security": 75,
        },
        "target_benchmarks": {"aptitude": 70, "coding": 65, "mock_interview": 70},
        "salary_range": "₹9.0 - 19.5 LPA",
        "recommended_projects": [
            "Containerize a multi-tier microservice application and deploy with Kubernetes Helm charts.",
            "Provision zero-trust AWS infrastructure using Terraform and automated GitHub Actions.",
        ],
    },
}


def _assessment_score(student: Dict[str, Any], field: str) -> float:
    """Return a neutral score when an assessment is missing or unparsable."""
    try:
        score = float(student.get(field, 50.0))
    except (TypeError, ValueError):
        return 50.0
    return 50.0 if isnan(score) else score


def _is_missing_value(value: Any) -> bool:
    try:
        return value is None or isnan(float(value))
    except (TypeError, ValueError):
        return value is None


def analyze_skill_gaps(student: Dict[str, Any], role_name: str) -> Dict[str, Any]:
    """
    Compares student's actual assessed scores against target role requirements,
    calculating concrete deficits, readiness index, and recommended actions.
    """
    role = CAREER_ROLES_DATA.get(role_name, CAREER_ROLES_DATA["Full Stack Software Engineer"])
    reqs = role["skills_required"]

    student_coding = _assessment_score(student, "coding_score")
    student_tech = _assessment_score(student, "technical_skills_score")
    student_apt = _assessment_score(student, "aptitude_score")

    gaps = []
    strengths = []
    total_delta = 0

    for skill, target in reqs.items():
        # Map student proxies
        if "Coding" in skill or "Algorithm" in skill:
            actual = student_coding
        elif "Aptitude" in skill or "Statistics" in skill or "Algebra" in skill:
            actual = student_apt
        else:
            actual = student_tech

        delta = target - actual
        total_delta += max(0, delta)

        if delta > 10:
            gaps.append({
                "skill": skill,
                "current": round(actual, 1),
                "target": target,
                "deficit": round(delta, 1),
                "status": "Critical Gap",
            })
        elif delta > 0:
            gaps.append({
                "skill": skill,
                "current": round(actual, 1),
                "target": target,
                "deficit": round(delta, 1),
                "status": "Moderate Gap",
            })
        else:
            strengths.append({
                "skill": skill,
                "current": round(actual, 1),
                "target": target,
                "surplus": round(-delta, 1),
            })

    # Overall role readiness score
    max_possible_deficit = len(reqs) * 40.0
    readiness_score = max(20.0, min(100.0, 100.0 - (total_delta / max_possible_deficit * 80.0)))

    score_fields = {
        "coding_score": "Coding assessment",
        "technical_skills_score": "Technical skills assessment",
        "aptitude_score": "Aptitude assessment",
        "mock_interview_score": "Mock interview assessment",
    }
    missing_assessments = []
    for field, label in score_fields.items():
        if _is_missing_value(student.get(field)):
            missing_assessments.append(label)

    return {
        "role_title": role_name,
        "readiness_score": round(readiness_score, 1),
        "gaps": gaps,
        "strengths": strengths,
        "missing_assessments": missing_assessments,
        "salary_range": role["salary_range"],
        "recommended_projects": role["recommended_projects"],
        "benchmarks": role["target_benchmarks"],
    }


def build_career_roadmap(
    student: Dict[str, Any],
    role_name: str,
    duration_weeks: int = 8,
    hours_per_week: int = 6,
) -> Dict[str, Any]:
    """Build a transparent, assessment-driven roadmap for a selected career role."""
    if role_name not in CAREER_ROLES_DATA:
        raise ValueError(f"Unknown career role: {role_name}")
    if duration_weeks not in {4, 8, 12}:
        raise ValueError("Roadmap duration must be 4, 8, or 12 weeks.")
    if not 1 <= hours_per_week <= 20:
        raise ValueError("Weekly study hours must be between 1 and 20.")

    analysis = analyze_skill_gaps(student, role_name)
    gaps = sorted(
        analysis["gaps"],
        key=lambda item: item["deficit"],
        reverse=True,
    )
    focus_skills = gaps[:3] or [
        {
            "skill": skill,
            "current": _assessment_score(student, "technical_skills_score"),
            "target": target,
            "deficit": 0.0,
            "status": "Maintain",
        }
        for skill, target in list(CAREER_ROLES_DATA[role_name]["skills_required"].items())[:3]
    ]

    phases = [
        ("Build foundations", 0.0, 0.25),
        ("Practice core skills", 0.25, 0.50),
        ("Apply skills in a project", 0.50, 0.75),
        ("Prepare and review", 0.75, 1.0),
    ]
    milestones = []

    attendance_missing = _is_missing_value(student.get("attendance_overall", 100.0))
    backlog_missing = _is_missing_value(student.get("backlog_count", 0))
    academic_risk = str(student.get("academic_risk") or "").casefold()
    placement_risk = str(student.get("placement_risk") or "").casefold()
    try:
        attendance = float(student.get("attendance_overall", 100.0))
    except (TypeError, ValueError):
        attendance = 100.0
    if isnan(attendance):
        attendance = 100.0
    try:
        backlogs = int(student.get("backlog_count", 0))
    except (TypeError, ValueError):
        backlogs = 0

    missing_academic_data = []
    if attendance_missing:
        missing_academic_data.append("attendance")
    if backlog_missing:
        missing_academic_data.append("backlog count")
    for index, (title, start_fraction, end_fraction) in enumerate(phases):
        first_week = int(start_fraction * duration_weeks) + 1
        last_week = max(first_week, int(end_fraction * duration_weeks))
        skill = focus_skills[index % len(focus_skills)]
        actions = [
            f"Study {skill['skill']} for {hours_per_week} focused hours each week.",
            f"Complete one role-relevant exercise or practical task and record the result.",
        ]
        if index == 0 and missing_academic_data:
            actions.insert(
                0,
                "Confirm your current "
                + " and ".join(missing_academic_data)
                + " with your faculty advisor before setting academic targets.",
            )
        if index == 0 and analysis["missing_assessments"]:
            actions.insert(
                0,
                "Complete baseline assessments: "
                + ", ".join(analysis["missing_assessments"])
                + ". Current skill-gap estimates use a neutral placeholder until then.",
            )
        if index == 0 and (attendance < 75.0 or backlogs > 0):
            academic_actions = []
            if attendance < 75.0:
                academic_actions.append(
                    f"Meet your faculty advisor and agree an attendance recovery plan "
                    f"(current attendance: {attendance:.1f}%)."
                )
            if backlogs > 0:
                academic_actions.append(
                    f"Schedule weekly remedial study for {backlogs} active backlog(s)."
                )
            actions = academic_actions + actions
        if index == 0 and academic_risk in {"high risk", "medium risk"}:
            actions.insert(
                0,
                f"Review your {student.get('academic_risk')} academic risk indicators "
                "with your faculty advisor and agree on a progress check-in.",
            )
        if index == 0 and placement_risk in {"high risk", "medium risk"}:
            actions.append(
                f"Review your {student.get('placement_risk')} placement risk and "
                "set a follow-up assessment date for the selected role."
            )
        if index == 2:
            actions.append(
                f"Build a portfolio project: "
                f"{CAREER_ROLES_DATA[role_name]['recommended_projects'][0]}"
            )
        if index == 3:
            actions.append(
                "Complete one mock interview, review feedback, and update your resume."
            )

        milestones.append(
            {
                "phase": title,
                "week_range": f"Weeks {first_week}-{last_week}",
                "focus_skill": skill["skill"],
                "current_score": skill["current"],
                "target_score": skill["target"],
                "actions": actions,
                "weekly_hours": hours_per_week,
                "completion_check": (
                    f"Review progress toward {skill['target']}/100 in {skill['skill']} "
                    "with a new practice assessment."
                ),
            }
        )

    return {
        "role_title": role_name,
        "duration_weeks": duration_weeks,
        "hours_per_week": hours_per_week,
        "readiness_score": analysis["readiness_score"],
        "missing_assessments": analysis["missing_assessments"],
        "missing_academic_data": missing_academic_data,
        "academic_risk": student.get("academic_risk"),
        "placement_risk": student.get("placement_risk"),
        "milestones": milestones,
        "disclaimer": (
            "This is a transparent planning aid based on the assessments currently on file. "
            "It is not an AI-generated prediction or a guarantee of placement."
        ),
    }


# ==============================================================================
# 3. TEXT-BASED MOCK INTERVIEW STUDIO
# ==============================================================================
MOCK_INTERVIEW_BANK: Dict[str, List[Dict[str, Any]]] = {
    "Full Stack Software Engineer": [
        {
            "id": 1,
            "category": "Technical (Database Architecture)",
            "question": "Explain the difference between SQL and NoSQL databases. When would you choose PostgreSQL over MongoDB for an enterprise student information system?",
            "expected_keywords": ["acid", "relational", "foreign key", "transaction", "integrity", "join", "scale"],
            "model_answer": "PostgreSQL is a relational database enforcing strict ACID compliance and referential integrity via foreign keys, making it ideal for institutional systems where grades, enrollments, and transactions must not diverge. MongoDB excels at horizontal scalability and flexible schemaless documents for unstructured feeds.",
        },
        {
            "id": 2,
            "category": "Technical (Frontend Optimization)",
            "question": "What causes unnecessary component re-renders in React, and what techniques do you use to optimize performance in a data-heavy dashboard?",
            "expected_keywords": ["virtual dom", "usememo", "usecallback", "react.memo", "state", "props", "reconciliation"],
            "model_answer": "Re-renders occur when component state or props change, or when parent components re-render creating new object/function references. We optimize using React.memo for pure components, useCallback/useMemo to stabilize references, and virtualized lists (react-window) for rendering large tables.",
        },
        {
            "id": 3,
            "category": "Behavioral (STAR Method)",
            "question": "Describe a situation where you had a tight deadline and discovered a critical bug in your code right before submission. How did you triage and resolve it?",
            "expected_keywords": ["situation", "task", "action", "result", "debug", "prioritize", "communicate", "fix"],
            "model_answer": "Using the STAR method: In our capstone project, an unindexed database query caused 5-second dashboard latency two days before our demo. I profiled network calls, identified the N+1 query loop, replaced it with a single indexed JOIN query, reducing render time to 150ms and ensuring a successful demo.",
        },
    ],
    "General / Campus Placement": [
        {
            "id": 1,
            "category": "Technical (Problem Solving)",
            "question": "How do you detect a cycle in a singly linked list with O(1) auxiliary space? Explain the intuition.",
            "expected_keywords": ["floyd", "slow", "fast", "pointers", "tortoise", "hare", "cycle"],
            "model_answer": "Using Floyd's Cycle-Finding Algorithm: maintain two pointers, slow moving 1 step and fast moving 2 steps. If a cycle exists, the fast pointer will eventually lap and meet the slow pointer within the loop. If fast reaches NULL, no cycle exists.",
        },
        {
            "id": 2,
            "category": "Behavioral",
            "question": "Why do you want to join KPMG, and how does your academic and practical project background align with our technology consulting practice?",
            "expected_keywords": ["consulting", "technology", "client", "problem solving", "impact", "innovation", "integrity"],
            "model_answer": "KPMG combines deep industry strategy with cutting-edge digital transformation. My experience building data-driven platforms with explainable AI, coupled with disciplined analytical rigor in academic projects, aligns with delivering transparent, secure solutions for enterprise clients.",
        },
    ],
}


def evaluate_mock_interview_answer(question_obj: Dict[str, Any], student_answer: str) -> Dict[str, Any]:
    """
    Transparently evaluates student's mock interview response based on
    relevance, expected concept coverage, completeness, and clarity.
    """
    if not student_answer.strip():
        return {
            "score": 0,
            "relevance": 0,
            "technical_accuracy": 0,
            "clarity": 0,
            "feedback": "No answer submitted. Please write a structured response.",
            "model_answer": question_obj.get("model_answer", ""),
        }

    text_lower = student_answer.lower()
    keywords = question_obj.get("expected_keywords", [])

    matched_keywords = [kw for kw in keywords if kw in text_lower]
    keyword_ratio = len(matched_keywords) / len(keywords) if keywords else 0.8

    word_count = len(student_answer.split())
    length_score = min(1.0, word_count / 40.0)

    # Component scores (0-100)
    relevance = min(100.0, (keyword_ratio * 70.0 + length_score * 30.0))
    technical_accuracy = min(100.0, (keyword_ratio * 85.0 + 15.0))
    clarity = 85.0 if word_count >= 25 else 55.0

    overall_score = round(0.40 * technical_accuracy + 0.35 * relevance + 0.25 * clarity, 1)

    feedback_points = []
    if matched_keywords:
        feedback_points.append(f"Demonstrated good technical concepts: {', '.join(matched_keywords[:4])}.")
    else:
        feedback_points.append("Key technical terminology was missing from your response.")

    if word_count < 25:
        feedback_points.append("Your answer was brief. In campus placement interviews, elaborate with concrete examples.")
    else:
        feedback_points.append("Good answer depth and structured articulation.")

    return {
        "score": overall_score,
        "relevance": round(relevance, 1),
        "technical_accuracy": round(technical_accuracy, 1),
        "clarity": round(clarity, 1),
        "matched_concepts": matched_keywords,
        "feedback": " ".join(feedback_points),
        "model_answer": question_obj.get("model_answer", ""),
    }
