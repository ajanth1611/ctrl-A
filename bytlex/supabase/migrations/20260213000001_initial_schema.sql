-- ==============================================================================
-- CampusIQ: Supabase PostgreSQL Database Migration
-- KPMG AI-Powered Student Analytics and Success Platform
-- ==============================================================================

-- 1. Enable UUID Extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 2. Profiles Table (Auth & Institutional Role Mapping)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'student')),
    department TEXT,
    student_id TEXT,
    designation TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 3. Students Master Table
CREATE TABLE IF NOT EXISTS public.students (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    department TEXT NOT NULL,
    semester INTEGER NOT NULL,
    cgpa NUMERIC(4, 2) NOT NULL CHECK(cgpa >= 0.0 AND cgpa <= 10.0),
    marks_percentage NUMERIC(5, 2) NOT NULL CHECK(marks_percentage >= 0.0 AND marks_percentage <= 100.0),
    backlog_count INTEGER DEFAULT 0 CHECK(backlog_count >= 0),
    attendance_overall NUMERIC(5, 2) NOT NULL CHECK(attendance_overall >= 0.0 AND attendance_overall <= 100.0),
    attendance_math NUMERIC(5, 2),
    attendance_core NUMERIC(5, 2),
    attendance_lab NUMERIC(5, 2),
    lms_assignment_completion NUMERIC(5, 2) NOT NULL CHECK(lms_assignment_completion >= 0.0 AND lms_assignment_completion <= 100.0),
    lms_login_frequency INTEGER DEFAULT 0 CHECK(lms_login_frequency >= 0),
    extracurricular_score NUMERIC(5, 2) DEFAULT 50.0,
    technical_skills_score NUMERIC(5, 2) DEFAULT 50.0,
    aptitude_score NUMERIC(5, 2) DEFAULT 50.0,
    coding_score NUMERIC(5, 2) DEFAULT 50.0,
    mock_interview_score NUMERIC(5, 2) DEFAULT 50.0,
    student_feedback_score NUMERIC(3, 2) DEFAULT 4.0,
    placement_status TEXT DEFAULT 'Eligible' CHECK(placement_status IN ('Placed', 'Eligible', 'Needs Training', 'Not Eligible')),
    success_score NUMERIC(5, 2),
    academic_risk TEXT CHECK(academic_risk IN ('High Risk', 'Medium Risk', 'Low Risk')),
    placement_risk TEXT CHECK(placement_risk IN ('High Risk', 'Medium Risk', 'Low Risk')),
    risk_level TEXT CHECK(risk_level IN ('High Risk', 'Medium Risk', 'Low Risk')),
    segment TEXT,
    mentor_id TEXT,
    mentor_name TEXT,
    mentor_email TEXT,
    faculty_notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 4. Interventions Management Table
CREATE TABLE IF NOT EXISTS public.interventions (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES public.students(student_id) ON DELETE CASCADE,
    student_name TEXT NOT NULL,
    department TEXT NOT NULL,
    intervention_type TEXT NOT NULL,
    priority TEXT DEFAULT 'Medium' CHECK(priority IN ('Urgent', 'High', 'Medium', 'Low')),
    owner_name TEXT NOT NULL,
    owner_email TEXT,
    due_date DATE NOT NULL,
    status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Escalated')),
    description TEXT,
    goal TEXT,
    outcome_measured TEXT,
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 5. Data Ingestion Jobs Audit Table
CREATE TABLE IF NOT EXISTS public.data_import_jobs (
    id TEXT PRIMARY KEY,
    dataset_type TEXT NOT NULL,
    filename TEXT NOT NULL,
    total_rows INTEGER NOT NULL,
    valid_rows INTEGER NOT NULL,
    invalid_rows INTEGER NOT NULL,
    inserted_rows INTEGER NOT NULL,
    updated_rows INTEGER NOT NULL,
    status TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 6. Action Plan Tasks Table
CREATE TABLE IF NOT EXISTS public.action_plan_tasks (
    id TEXT PRIMARY KEY,
    student_id TEXT NOT NULL REFERENCES public.students(student_id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    description TEXT,
    category TEXT NOT NULL,
    priority TEXT NOT NULL,
    effort_hours NUMERIC(4, 1) DEFAULT 2.0,
    due_date TEXT,
    completed BOOLEAN DEFAULT FALSE,
    reason TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT timezone('utc'::text, now()) NOT NULL
);

-- 7. High-Performance Indexes
CREATE INDEX IF NOT EXISTS idx_students_dept ON public.students(department);
CREATE INDEX IF NOT EXISTS idx_students_risk ON public.students(risk_level);
CREATE INDEX IF NOT EXISTS idx_students_mentor ON public.students(mentor_email);
CREATE INDEX IF NOT EXISTS idx_interventions_student ON public.interventions(student_id);
CREATE INDEX IF NOT EXISTS idx_interventions_owner ON public.interventions(owner_email);

-- 8. Row Level Security (RLS) Policies
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.students ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.interventions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.action_plan_tasks ENABLE ROW LEVEL SECURITY;

-- Administrators can read and modify all institutional tables
CREATE POLICY admin_all_students ON public.students
    FOR ALL USING (EXISTS (SELECT 1 FROM public.profiles WHERE profiles.id = auth.uid() AND profiles.role = 'admin'));

-- Staff can view students in their department or assigned mentees
CREATE POLICY staff_assigned_students ON public.students
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'staff'
            AND (profiles.email = students.mentor_email OR profiles.department = students.department)
        )
    );

-- Students can view only their own record
CREATE POLICY student_own_record ON public.students
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.profiles
            WHERE profiles.id = auth.uid()
            AND profiles.role = 'student'
            AND profiles.student_id = students.student_id
        )
    );
