# 🎓 CampusIQ — AI-Powered Student Analytics & Success Platform
### HacXLerate 2026 Challenge | KPMG in India

> **A production-minded, explainable multi-source student analytics and early-intervention platform built for college administrators, faculty mentors, and undergraduate students.**

CampusIQ unifies disconnected student data across **academic records, semester marks, backlogs, classroom attendance, LMS engagement, placement assessments, technical skills, and qualitative student feedback**. It calculates a transparent, deterministic **Student Success Score (0–100)**, identifies students at academic or placement risk, explains underlying root causes, and provides an integrated **Intervention Management System** and **AI Student Companion**.

The student Career Hub generates a transparent 4-, 8-, or 12-week plan from the selected target role, current assessment gaps, academic risk indicators, and the student's available study time. A browser-based speech reader can read the plan aloud. CampusIQ does not capture microphone audio; speech text handling depends on the browser and selected voice. It does not use a generative AI service.

---

## 🏗️ Project Architecture & Directory Structure

```
bytlex/
├── app.py                      # Master Streamlit entrypoint with role-based routing
├── requirements.txt            # Python dependencies (Streamlit, Pandas, Plotly, Supabase, Pytest)
├── .env.example                # Configuration template for Supabase and optional AI keys
├── schema.sql                  # SQLite relational schema
├── campusiq.db                 # SQLite persistent database (created automatically on startup)
├── sample-data/                # 7 sample CSV datasets for multi-source ingestion testing
│   ├── student_master.csv
│   ├── academic_records.csv
│   ├── attendance_records.csv
│   ├── lms_records.csv
│   ├── placement_assessments.csv
│   ├── skills_assessments.csv
│   ├── student_feedback.csv
│   └── import_with_errors.csv  # Synthetic dataset to test row validation error auditor
├── src/
│   ├── __init__.py
│   ├── analytics.py            # Centralized scoring, normalization, risk rules & segmentation
│   ├── database.py             # Authenticated Supabase/PostgreSQL and local SQLite access
│   ├── auth.py                 # Multi-role gateway, role verification & session management
│   ├── csv_importer.py         # 10-step CSV ingestion, fuzzy schema mapping & validation engine
│   ├── ai_mentor.py            # Academic mentor, quizzes, skill gap analyzer & mock studio
│   ├── sample_data.py          # Synthetic dataset generator covering performance archetypes
│   └── views/
│       ├── admin_view.py       # Institutional KPIs, Student Directory, CSV Center, Scoring Config
│       ├── staff_view.py       # Assigned mentees, Intervention tracker, Early warning alerts
│       └── student_view.py     # Personal progress, AI mentor, Placement hub, Resume builder
├── supabase/
│   └── migrations/
│       ├── 20260213000001_initial_schema.sql # Initial Supabase schema (legacy broad policies)
│       └── 20260301000002_secure_assigned_access.sql # Assignment-based Supabase RLS
├── docs/
│   ├── SCORING_METHODOLOGY.md  # Exact mathematical formulas, weights & risk rules
│   ├── ARCHITECTURE.md         # Full architectural specifications & component breakdown
│   ├── SECURITY.md             # Role-based access control, RLS & student data privacy
│   ├── DATA_DICTIONARY.md      # Detailed CSV columns, data types & constraints
│   └── DEMO_GUIDE.md           # 3-5 minute live demonstration script for hackathon judges
└── tests/
    ├── test_analytics.py       # Unit tests for scoring formulas, weights & risk flags
    ├── test_auth.py            # Access control & role mismatch tests
    └── test_csv_importer.py    # CSV validation & atomic upsert tests
```

---

## ⚡ Quickstart & Installation

### 1. Prerequisites
- Python 3.11+
- Git

### 2. Install Dependencies with Your Normal Python

```powershell
# Navigate to project directory
cd C:\Users\user\OneDrive\Desktop\bytlex

# Install required dependencies
python -m pip install -r requirements.txt
```

### 3. Environment Configuration
```powershell
# Copy environment configuration
Copy-Item .env.example .env
```

With the template values unchanged, CampusIQ uses local SQLite and the bundled fictional cohort. Supplying a real Supabase URL and public anon key switches authentication and application data access to Supabase Auth/PostgreSQL. The app does not fall back to SQLite if Supabase settings are incomplete or Supabase requests fail. It also never seeds demo records into Supabase.

To connect Supabase:
1. Create a Supabase project and apply the migrations in `supabase/migrations` in filename order using the Supabase SQL Editor (the second migration replaces department-wide staff access with explicit mentor assignment).
2. Create each user in **Authentication → Users**. Provision a corresponding `public.profiles` row whose `id` is that Auth user's UUID, whose `email` matches the Auth account, and whose role is assigned by a trusted administrator. Bootstrap the first admin profile through a trusted database-administrator process; never allow users to set their own role.
3. Assign students using `students.mentor_email` matching the staff profile email. Student profiles must link to the matching `students.student_id`.
4. Set the project API URL (`https://<project-ref>.supabase.co`) and `SUPABASE_ANON_KEY` in the server-side `.env`; do not use the Supabase dashboard URL. The anon/public key is intended for client libraries; never use or share the `service_role` key. The Supabase Python client keeps Auth tokens server-side in the Streamlit session.
5. Sign in using the Auth account's email and password. Verify RLS with separate admin, assigned staff, unassigned staff, and student test accounts before importing institutional records.

The app-side Supabase integration has not been verified against a live project in this workspace because no project URL, anon key, or Auth accounts were provided. Supabase SQL migrations must be applied by you; the app will report query, policy, and authentication failures rather than silently switching databases. Existing `campusiq.db` data is not automatically copied to Supabase; back it up and use the authenticated admin CSV import to migrate reviewed records.

Optional live AI features are available in the Academic Mentor and Mock Interview Studio. Add `OPENAI_API_KEY`, `GEMINI_API_KEY`, or both to your **local `.env`**; provider model names can be overridden with `OPENAI_MODEL` and `GEMINI_MODEL`. The application sends a question/topic or interview answer only after the user agrees in the UI. It does not include a student name, ID, or profile in those requests. Use fictional sample data for demos, avoid entering personal or confidential information, and review each provider's data-retention terms before enabling it. If no AI key is configured, the local demo guidance and transparent interview scoring remain available. Provider errors are shown; a failed live request is not presented as an AI response.

For local development, leave Supabase values as placeholders. Login uses the documented local accounts. One-click shortcuts are enabled by default for synthetic demo records; set `CAMPUSIQ_ENABLE_DEMO_LOGIN=false` to disable them. Set `CAMPUSIQ_DB_PATH` to use a separate SQLite file for local testing. Startup adds only missing fictional student profiles and preserves existing records.

### 4. Run the Application

```powershell
python -m streamlit run app.py
```
The application will launch in your default web browser at `http://localhost:8501`.

---

## 🧪 Automated Testing

CampusIQ includes a comprehensive **Pytest** test suite covering mathematical normalization, weight sum validation, boundary handling, independent academic/placement risk rules, access control, and CSV validation:

```powershell
python -m pytest tests/ -v
```

The suite covers score/risk logic, roadmap generation, role isolation, SQLite authorization, and CSV validation. Run it locally to see the current result.

---

## 🔑 Pre-Configured Demo Accounts for Judges

| Role | Username / Email | Password | Persona & Key Features |
| :--- | :--- | :--- | :--- |
| **Institutional Admin** | `admin@campus.edu` | `AdminPass2026!` | Dean of Academic Operations &bull; KPIs, Ingestion Center, Scoring Config |
| **Faculty Mentor** | `dr.sharma@campus.edu` | `StaffPass2026!` | Associate Professor &bull; Assigned mentees, Intervention tracker |
| **Student (Academic Risk)** | `STU2021004` | `StudentPass2026!` | Karan Pillai &bull; Low attendance (54.3%), CGPA 5.16, "What to do next" |
| **Student (Placement Risk)**| `STU2021002` | `StudentPass2026!` | Pranav Deshmukh &bull; High CGPA (8.93), Interview anxiety, Skill gaps |
| **Student (Placed Champion)**| `STU2021007` | `StudentPass2026!` | Simran Gupta &bull; Placed at Tier-1 firm, AI Mock Interview Studio |

*Optional local-only shortcut: set `CAMPUSIQ_ENABLE_DEMO_LOGIN=true` in `.env` to show one-click demo access and role switching. This intentionally bypasses the credential prompt for the documented synthetic demo accounts and must never be enabled with real student records or on a shared deployment.*

---

## 📐 Scoring Formula & Risk Methodology

The **Student Success Score (0–100)** is an explainable weighted sum of 6 normalized dimensions:

$$\text{Student Success Score} = \sum_{i=1}^{6} (W_i \times I_i)$$

| Dimension | Default Weight | Formula & Normalization Logic |
| :--- | :---: | :--- |
| **Academic Performance** | **30%** (0.30) | $\text{clip}(0.70 \times (\text{CGPA} \times 10) + 0.30 \times \text{Marks} - (\text{Backlogs} \times 12), 0, 100)$ |
| **Attendance Record** | **20%** (0.20) | Classroom attendance percentage (warning threshold at 75%) |
| **LMS Engagement** | **15%** (0.15) | $0.40 \times \left(\min(20, \text{Logins})/20 \times 100\right) + 0.60 \times \text{Assignment Completion Rate}$ |
| **Placement Readiness** | **20%** (0.20) | $0.35 \times \text{Aptitude} + 0.40 \times \text{Coding Score} + 0.25 \times \text{Mock Interview Score}$ |
| **Technical Skills & Extra** | **10%** (0.10) | $0.60 \times \text{Technical Practical Assessment} + 0.40 \times \text{Extracurricular Engagement}$ |
| **Student Feedback** | **5%** (0.05) | $(\text{Student Satisfaction Rating} / 5.0) \times 100$ |

*Weights can be reconfigured dynamically by administrators with live 100% total validation.*

For full mathematical specifications, refer to [docs/SCORING_METHODOLOGY.md](file:///c:/Users/user/OneDrive/Desktop/bytlex/docs/SCORING_METHODOLOGY.md).

---

## 🚀 Deployment Instructions

### Option 1: Streamlit Community Cloud (Recommended for Hackathon Presentation)
1. Push this repository to GitHub.
2. Go to [share.streamlit.io](https://share.streamlit.io) and sign in with GitHub.
3. Select your repository, branch `main`, and main file `app.py`.
4. Add the Supabase URL and public anon key as server-side secrets only if using the Supabase backend. Do not add a `service_role` key. This project has not been deployed or tested on Streamlit Community Cloud.
5. Click **Deploy**.

### Option 2: Docker Container Deployment
```bash
# Build the Docker container
docker build -t campusiq .

# Run container on port 8501
docker run -p 8501:8501 campusiq
```

---

## 📜 License & Compliance
Built for the **HacXLerate 2026 Hackathon Challenge** sponsored by **KPMG in India**.
All synthetic datasets are generated without PII (Personally Identifiable Information) for demonstration and evaluation compliance.
