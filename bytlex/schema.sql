-- ==============================================================================
-- CampusIQ Database Schema (SQLite)
-- AI-Powered Student Success and Analytics Platform
-- ==============================================================================

-- 1. Students Table
CREATE TABLE IF NOT EXISTS students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    cgpa REAL NOT NULL,
    marks_percentage REAL NOT NULL,
    backlog_count INTEGER DEFAULT 0,
    attendance_overall REAL NOT NULL,
    lms_assignment_completion REAL NOT NULL,
    lms_login_frequency INTEGER DEFAULT 0,
    extracurricular_score REAL DEFAULT 50.0,
    technical_skills_score REAL DEFAULT 50.0,
    aptitude_score REAL DEFAULT 50.0,
    coding_score REAL DEFAULT 50.0,
    mock_interview_score REAL DEFAULT 50.0,
    student_feedback_score REAL DEFAULT 4.0,
    success_score REAL,
    risk_level TEXT,
    segment TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Interventions Table
CREATE TABLE IF NOT EXISTS interventions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL,
    student_name TEXT NOT NULL,
    department TEXT NOT NULL,
    intervention_type TEXT NOT NULL,
    description TEXT,
    mentor_name TEXT NOT NULL,
    due_date TEXT NOT NULL,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed')),
    notes TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
);

-- 3. Indexes for fast query performance
CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department);
CREATE INDEX IF NOT EXISTS idx_students_risk ON students(risk_level);
CREATE INDEX IF NOT EXISTS idx_students_segment ON students(segment);
CREATE INDEX IF NOT EXISTS idx_interventions_student_id ON interventions(student_id);
CREATE INDEX IF NOT EXISTS idx_interventions_status ON interventions(status);
