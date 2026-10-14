"""
CampusIQ: Synthetic Student Data Generator
Generates realistic, multi-dimensional student datasets with diverse performance archetypes.
"""

import os
import numpy as np
import pandas as pd

DEFAULT_DATA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "sample_students.csv")

DEMO_STUDENT_RECORDS = [
    {
        "student_id": "STU2021004",
        "name": "Karan Pillai",
        "email": "karan.pillai@student.campus.edu",
        "department": "Electronics & Communication",
        "semester": 5,
        "cgpa": 5.16,
        "marks_percentage": 54.0,
        "backlog_count": 2,
        "attendance_overall": 54.3,
        "lms_assignment_completion": 45.0,
        "lms_login_frequency": 4,
        "extracurricular_score": 30.0,
        "technical_skills_score": 45.0,
        "aptitude_score": 52.0,
        "coding_score": 38.0,
        "mock_interview_score": 36.0,
        "student_feedback_score": 3.2,
        "placement_status": "Eligible",
        "mentor_id": "staff_sharma_01",
        "mentor_name": "Dr. Ananya Sharma",
        "mentor_email": "dr.sharma@campus.edu",
    },
    {
        "student_id": "STU2021002",
        "name": "Pranav Deshmukh",
        "email": "pranav.deshmukh@student.campus.edu",
        "department": "Electronics & Communication",
        "semester": 7,
        "cgpa": 8.93,
        "marks_percentage": 91.2,
        "backlog_count": 0,
        "attendance_overall": 88.0,
        "lms_assignment_completion": 96.0,
        "lms_login_frequency": 18,
        "extracurricular_score": 55.0,
        "technical_skills_score": 52.0,
        "aptitude_score": 45.0,
        "coding_score": 35.0,
        "mock_interview_score": 40.0,
        "student_feedback_score": 4.0,
        "placement_status": "Eligible",
        "mentor_id": "staff_sharma_01",
        "mentor_name": "Dr. Ananya Sharma",
        "mentor_email": "dr.sharma@campus.edu",
    },
    {
        "student_id": "STU2021007",
        "name": "Simran Gupta",
        "email": "simran.gupta@student.campus.edu",
        "department": "Computer Science & Engineering",
        "semester": 8,
        "cgpa": 8.72,
        "marks_percentage": 89.0,
        "backlog_count": 0,
        "attendance_overall": 94.0,
        "lms_assignment_completion": 98.0,
        "lms_login_frequency": 20,
        "extracurricular_score": 88.0,
        "technical_skills_score": 92.0,
        "aptitude_score": 92.0,
        "coding_score": 94.0,
        "mock_interview_score": 91.0,
        "student_feedback_score": 4.8,
        "placement_status": "Placed",
        "mentor_id": "staff_sharma_01",
        "mentor_name": "Dr. Ananya Sharma",
        "mentor_email": "dr.sharma@campus.edu",
    },
]


def ensure_demo_student_records(df: pd.DataFrame) -> pd.DataFrame:
    """Add fictional profiles used by the documented demo accounts, without replacing rows."""
    if "student_id" not in df.columns:
        raise ValueError("Demo student records require a student_id column.")

    existing_ids = set(df["student_id"].astype(str).str.strip())
    missing_records = [
        record
        for record in DEMO_STUDENT_RECORDS
        if record["student_id"] not in existing_ids
    ]
    if not missing_records:
        return df.copy()
    return pd.concat([df, pd.DataFrame(missing_records)], ignore_index=True)


def generate_synthetic_students(num_records: int = 220, save_path: str = DEFAULT_DATA_PATH) -> pd.DataFrame:
    """
    Generates >= 200 realistic synthetic student records across 5 academic departments
    and 8 semesters. Simulates 5 distinct archetypes to mirror real collegiate cohorts:
      1. High academics, low placement readiness
      2. Low academics, strong placement readiness
      3. Low academics and low placement readiness
      4. High academics and high placement readiness
      5. Developing or mixed performance
    """
    np.random.seed(42)

    departments = [
        "Computer Science & Engineering",
        "Information Technology",
        "Electronics & Communication",
        "Artificial Intelligence & Data Science",
        "Mechanical Engineering"
    ]

    first_names = [
        "Aarav", "Aditi", "Rohan", "Ananya", "Rahul", "Priya", "Vikram", "Sneha",
        "Karthik", "Pooja", "Arjun", "Divya", "Siddharth", "Neha", "Manish", "Meera",
        "Akash", "Ishita", "Varun", "Tanvi", "Nikhil", "Riya", "Gaurav", "Kavya",
        "Harsh", "Deepika", "Aditya", "Shreya", "Pranav", "Anushka", "Sanjay", "Swati",
        "Dev", "Roshni", "Sameer", "Simran", "Abhishek", "Priti", "Karan", "Aishwarya",
        "Aman", "Bhavya", "Chetan", "Dia", "Esha", "Farhan", "Geeta", "Harit",
        "Isha", "Jatin", "Komal", "Lalit", "Manoj", "Nandini", "Omkar", "Payal"
    ]

    last_names = [
        "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Gupta",
        "Singh", "Mehta", "Chopra", "Joshi", "Bose", "Kulkarni", "Deshmukh", "Menon",
        "Chatterjee", "Bhat", "Pillai", "Saxena", "Mishra", "Pandey", "Kapoor", "Das",
        "Mukherjee", "Agarwal", "Bansal", "Malhotra", "Tripathi", "Chauhan"
    ]

    student_ids = [f"CIQ{2022000 + i}" for i in range(1, num_records + 1)]
    names = [f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for _ in range(num_records)]
    depts = np.random.choice(departments, size=num_records)
    semesters = np.random.choice(list(range(1, 9)), size=num_records, p=[0.10, 0.10, 0.15, 0.15, 0.15, 0.15, 0.10, 0.10])

    # 5 intentional performance profiles matching the project requirements:
    # 1: High academics, low placement readiness (~20%)
    # 2: Low academics, strong placement readiness (~15%)
    # 3: Low academics and low placement readiness (~20%)
    # 4: High academics and placement readiness (~25%)
    # 5: Developing or mixed performance (~20%)
    archetype_keys = [
        "high_acad_low_place",
        "low_acad_high_place",
        "low_acad_low_place",
        "high_acad_high_place",
        "developing_mixed"
    ]
    archetype_choices = np.random.choice(archetype_keys, size=num_records, p=[0.20, 0.15, 0.20, 0.25, 0.20])

    cgpa_list = []
    marks_list = []
    backlogs_list = []
    att_list = []
    lms_assign_list = []
    lms_login_list = []
    extra_list = []
    tech_skill_list = []
    apt_list = []
    coding_list = []
    mock_list = []
    feedback_list = []

    for i, arch in enumerate(archetype_choices):
        sem = semesters[i]

        if arch == "high_acad_low_place":
            # Excellent exam theory, hesitant in coding/interview
            cgpa = round(np.random.uniform(8.0, 9.4), 2)
            marks = round(np.random.uniform(80.0, 95.0), 1)
            backlogs = 0
            att = round(np.random.uniform(82.0, 96.0), 1)
            lms_assign = round(np.random.uniform(85.0, 98.0), 1)
            lms_login = int(np.random.uniform(12, 22))
            extra = round(np.random.uniform(35.0, 60.0), 1)
            tech_skill = round(np.random.uniform(52.0, 68.0), 1)
            apt = round(np.random.uniform(48.0, 65.0), 1)
            coding = round(np.random.uniform(30.0, 50.0), 1)
            mock = round(np.random.uniform(35.0, 52.0), 1)
            feedback = round(np.random.uniform(3.5, 4.4), 1)

        elif arch == "low_acad_high_place":
            # Coding wizard/hackathon enthusiast with lower classroom attendance/CGPA
            cgpa = round(np.random.uniform(5.4, 6.4), 2)
            marks = round(np.random.uniform(52.0, 64.0), 1)
            backlogs = int(np.random.choice([0, 1], p=[0.7, 0.3]))
            att = round(np.random.uniform(62.0, 76.0), 1)
            lms_assign = round(np.random.uniform(60.0, 78.0), 1)
            lms_login = int(np.random.uniform(8, 16))
            extra = round(np.random.uniform(75.0, 95.0), 1)
            tech_skill = round(np.random.uniform(80.0, 95.0), 1)
            apt = round(np.random.uniform(72.0, 92.0), 1)
            coding = round(np.random.uniform(82.0, 98.0), 1)
            mock = round(np.random.uniform(75.0, 90.0), 1)
            feedback = round(np.random.uniform(3.6, 4.5), 1)

        elif arch == "low_acad_low_place":
            # Multi-risk student: attendance deficits, backlogs, low placement readiness
            cgpa = round(np.random.uniform(4.0, 5.8), 2)
            marks = round(np.random.uniform(40.0, 58.0), 1)
            backlogs = int(np.random.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1]))
            att = round(np.random.uniform(48.0, 68.0), 1)
            lms_assign = round(np.random.uniform(32.0, 62.0), 1)
            lms_login = int(np.random.uniform(1, 6))
            extra = round(np.random.uniform(20.0, 45.0), 1)
            tech_skill = round(np.random.uniform(35.0, 55.0), 1)
            apt = round(np.random.uniform(35.0, 52.0), 1)
            coding = round(np.random.uniform(25.0, 48.0), 1)
            mock = round(np.random.uniform(30.0, 50.0), 1)
            feedback = round(np.random.uniform(2.2, 3.4), 1)

        elif arch == "high_acad_high_place":
            # Star all-rounder
            cgpa = round(np.random.uniform(8.4, 9.9), 2)
            marks = round(np.random.uniform(84.0, 98.0), 1)
            backlogs = 0
            att = round(np.random.uniform(86.0, 99.0), 1)
            lms_assign = round(np.random.uniform(90.0, 100.0), 1)
            lms_login = int(np.random.uniform(16, 28))
            extra = round(np.random.uniform(75.0, 98.0), 1)
            tech_skill = round(np.random.uniform(82.0, 98.0), 1)
            apt = round(np.random.uniform(80.0, 98.0), 1)
            coding = round(np.random.uniform(82.0, 98.0), 1)
            mock = round(np.random.uniform(84.0, 98.0), 1)
            feedback = round(np.random.uniform(4.4, 5.0), 1)

        else:  # developing_mixed
            # Moderate steady progress
            cgpa = round(np.random.uniform(6.6, 7.8), 2)
            marks = round(np.random.uniform(66.0, 78.0), 1)
            backlogs = int(np.random.choice([0, 1], p=[0.85, 0.15]))
            att = round(np.random.uniform(74.0, 86.0), 1)
            lms_assign = round(np.random.uniform(70.0, 86.0), 1)
            lms_login = int(np.random.uniform(7, 16))
            extra = round(np.random.uniform(50.0, 72.0), 1)
            tech_skill = round(np.random.uniform(60.0, 75.0), 1)
            apt = round(np.random.uniform(58.0, 75.0), 1)
            coding = round(np.random.uniform(55.0, 72.0), 1)
            mock = round(np.random.uniform(58.0, 74.0), 1)
            feedback = round(np.random.uniform(3.4, 4.2), 1)

        cgpa_list.append(cgpa)
        marks_list.append(marks)
        backlogs_list.append(backlogs)
        att_list.append(att)
        lms_assign_list.append(lms_assign)
        lms_login_list.append(lms_login)
        extra_list.append(extra)
        tech_skill_list.append(tech_skill)
        apt_list.append(apt)
        coding_list.append(coding)
        mock_list.append(mock)
        feedback_list.append(feedback)

    df = pd.DataFrame({
        "student_id": student_ids,
        "name": names,
        "department": depts,
        "semester": semesters,
        "cgpa": cgpa_list,
        "marks_percentage": marks_list,
        "backlog_count": backlogs_list,
        "attendance_overall": att_list,
        "lms_assignment_completion": lms_assign_list,
        "lms_login_frequency": lms_login_list,
        "extracurricular_score": extra_list,
        "technical_skills_score": tech_skill_list,
        "aptitude_score": apt_list,
        "coding_score": coding_list,
        "mock_interview_score": mock_list,
        "student_feedback_score": feedback_list
    })

    # Ensure target directory exists
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    df.to_csv(save_path, index=False)
    return df


if __name__ == "__main__":
    df_gen = generate_synthetic_students(220)
    print(f"Generated {len(df_gen)} student records saved to {DEFAULT_DATA_PATH}")
