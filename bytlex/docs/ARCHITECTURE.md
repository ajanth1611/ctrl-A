# 🏗️ CampusIQ Platform Architecture

## 1. System Overview

CampusIQ is a **Python-first Streamlit application** with local SQLite demo persistence or Supabase Auth/PostgreSQL persistence, explainable analytics, and role-filtered views. The selected backend depends on whether real Supabase settings are configured.

```
┌───────────────────────────────────────────────────────────────┐
│                    STREAMLIT USER INTERFACE                   │
│   ┌──────────────────┬─────────────────┬──────────────────┐   │
│   │   Admin Portal   │  Staff Portal   │  Student Portal  │   │
│   └─────────┬────────┴────────┬────────┴────────┬─────────┘   │
└─────────────┼─────────────────┼─────────────────┼─────────────┘
              │                 │                 │
              ▼                 ▼                 ▼
┌───────────────────────────────────────────────────────────────┐
│            SERVER-SIDE LOGIC & AUTHORIZATION LAYER            │
│   • Role Verification Gateway (Admin / Staff / Student)      │
│   • Student Ownership & Staff Assignment Enforcement          │
│   • Centralized Scoring & Risk Engine (Pandas / NumPy)       │
│   • 10-Step CSV Ingestion, Validation & Upsert Engine         │
│   • AI Academic Mentor & Placement Studio                     │
└───────────────────────────────┬───────────────────────────────┘
                                │
                                ▼
┌───────────────────────────────────────────────────────────────┐
│          AUTHENTICATED DATA ACCESS (ONE BACKEND)               │
│   Local SQLite demo                 Supabase PostgreSQL       │
│   campusiq.db                       Auth + RLS                 │
└───────────────────────────────────────────────────────────────┘
```

---

## 2. Component Structure

- **`app.py`**: Streamlit application entrypoint. Enforces pre-authentication login gateway and routes authorized sessions to role-specific layouts.
- **`src/auth.py`**: Session state manager, credential verification, role-preference guard, and 1-click judge shortcuts.
- **`src/database.py`**: SQLite demo operations or authenticated Supabase Auth/PostgreSQL operations with role-filtered access.
- **`src/analytics.py`**: Centralized Pandas/NumPy calculation pipeline implementing normalization, score weighting, and risk triggers.
- **`src/csv_importer.py`**: Multi-source CSV ingestion engine with schema mapping, boundary validation, and row error reporting.
- **`src/ai_mentor.py`**: Academic tutor and placement center covering concepts, diagnostic quizzes, skill gap analysis, text mock interviews, and ATS resume generation.
- **`src/views/`**: Modular presentation views for Admin, Staff, and Student portals.
- **`tests/`**: Pytest test suites covering scoring, access control, and CSV validation.

---

## 3. Data Flow

1. **Ingestion**: Institutional datasets are uploaded via the CSV Ingestion Center.
2. **Validation**: Columns are fuzzy-matched to target schemas, and numeric fields are checked against boundary constraints.
3. **Upsert**: Records are merged into `students` table by `student_id`.
4. **Scoring**: The centralized engine recomputes normalized sub-scores, overall success scores, risk tiers, and student segments.
5. **Action**: Staff initiate and track targeted interventions, and students view personalized weekly action plans.

## 4. Current Integration Boundary

When configured, application requests use the signed-in user's Supabase session and are constrained by PostgreSQL RLS. Without Supabase credentials, the app initializes a local SQLite database and fictional demo accounts. The Supabase path is not verified against a live project in this workspace; apply and review the migrations, provision trusted profiles, and test all roles before importing institutional records.
