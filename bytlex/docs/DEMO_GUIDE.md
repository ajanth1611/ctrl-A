# 🎬 CampusIQ: 3–5 Minute Hackathon Demonstration Script

## Overview
This walkthrough demonstrates the complete institutional cycle: **multi-source CSV data ingestion $\to$ explainable success scoring $\to$ early risk warnings $\to$ faculty intervention tracking $\to$ personalized student support**.

---

## Step-by-Step Demo Flow

### 1. The Role-Based Gateway (0:00 – 0:30)
1. Open the application at `http://localhost:8501`.
2. Point out that internal dashboards are locked until authentication.
3. Show the 3 distinct roles: **Admin**, **Faculty / Staff**, and **Student**.
4. Click **"Log In as Institutional Admin"** (using the 1-click judge shortcut).

### 2. Institutional Overview & Analytics (0:30 – 1:15)
1. Point out the concise **6 KPI Cards**: Total Students, Average Success Score (e.g. 71.4/100), Academic High Risks, Placement Risks, Average Attendance, and Open Interventions.
2. Show the **Score Distribution Histogram** and **Risk Tier Donut Chart** built with Plotly.
3. Highlight the **Department Comparisons** showing how departments perform on success score vs. classroom attendance.

### 3. CSV Data Ingestion & Row Validation (1:15 – 2:00)
1. Click the **"CSV Data Ingestion"** tab.
2. Click **"Load Dataset with Validation Errors (Auditor Test)"** or upload `sample-data/import_with_errors.csv`.
3. Show the automated column mapping.
4. Show the **Integrity Inspection**: point out how rows with CGPA $> 10$, attendance $> 100$, negative backlogs, or missing IDs are flagged and isolated without corrupting database state.
5. Click **"Download Invalid Rows (.csv)"** to show the auditor export.
6. Click **"Load Student Master Sample"** and click **"Confirm & Ingest"** to show a successful atomic upsert.

### 4. Student Directory & Explainable Score Breakdown (2:00 – 2:45)
1. Click the **"Student Directory"** tab.
2. Search for student `STU2021004` (Karan Pillai) or `STU2021002` (Pranav Deshmukh).
3. Open the **Student 360° Profile Drawer**.
4. Explain the formula:
   - Academics (30%): point contribution + raw value.
   - Attendance (20%): point contribution.
   - LMS Portal (15%): point contribution.
   - Placement (20%): point contribution.
5. Point out **Positive Drivers** vs **Negative Drags**.
6. Show the **Academic-Placement Asymmetry** warning for Pranav (CGPA 8.93 but placement risk high).

### 5. Staff Intervention Management (2:45 – 3:30)
1. Use the top bar Quick Switcher: select **"Faculty (Dr. Sharma)"**.
2. Note that the roster now filters exclusively to Dr. Sharma's assigned mentees.
3. Navigate to **"Intervention Tracker"**.
4. Demonstrate creating a **"Low Attendance Follow-up"** or **"Mock Interview Coaching"** intervention with a target date and measurable improvement goal.
5. Update an existing intervention's status from **Pending $\to$ In Progress $\to$ Completed**, adding dated meeting notes.

### 6. Student Companion Experience (3:30 – 4:30)
1. Switch to **"Student (Karan - Academic Risk)"** (`STU2021004`).
2. Show that Karan cannot access other students' files or administrative controls.
3. Show the **"What should I do next?"** prioritized action card with practical, high-yield guidance.
4. Open the **"AI Academic Mentor"** tab:
   - Select *Data Structures & Algorithms* $\to$ *Two Pointers*.
   - View step-by-step problem-solving.
   - Take a quick diagnostic quiz and submit answers.
5. Open the **"Placement & Career Hub"**:
   - Select *Full Stack Software Engineer*.
   - View the **Role Match Index (e.g. 74%)**, identified skill deficits, and recommended projects.
6. Open the **"Mock Interview Studio"**:
   - Type a response to a real interview question.
   - Click **"Evaluate Response"** to view transparent scoring on technical accuracy, relevance, and clarity alongside the benchmark model answer.
7. Open the **"Smart Resume Builder"** and show the live formatted preview.

---

## Key Talking Points for Judges
- **Transparency**: Rule-based, fully explainable scoring without black-box ML hallucinations.
- **Early Warning vs. Rearview Reporting**: Detects attendance drops and placement anxiety before semester examinations and placement drives begin.
- **Data Protection**: Strict student isolation and staff assignment rules enforced at the database and server layers.
- **Production Ready**: Fully functional CSV ingestion pipeline with atomic upserts and complete Pytest test coverage.
