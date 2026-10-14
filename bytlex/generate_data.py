import pandas as pd
import numpy as np

np.random.seed(42)

num_students = 150

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
    "Dev", "Roshni", "Sameer", "Simran", "Abhishek", "Priti", "Karan", "Aishwarya"
]

last_names = [
    "Sharma", "Verma", "Patel", "Reddy", "Nair", "Iyer", "Rao", "Gupta",
    "Singh", "Mehta", "Chopra", "Joshi", "Bose", "Kulkarni", "Deshmukh", "Menon",
    "Chatterjee", "Bhat", "Pillai", "Saxena", "Mishra", "Pandey", "Kapoor", "Das"
]

student_ids = [f"STU{2021000 + i}" for i in range(1, num_students + 1)]
names = [f"{np.random.choice(first_names)} {np.random.choice(last_names)}" for _ in range(num_students)]
depts = np.random.choice(departments, size=num_students)
years = np.random.choice([1, 2, 3, 4], size=num_students, p=[0.20, 0.25, 0.30, 0.25])

# Archetypes generation to ensure realistic segmentation:
# 1. High all-rounder (~25%)
# 2. Book smart, low placement / coding (~20%)
# 3. Disengaged / Low attendance & LMS (~20%)
# 4. Struggling with backlogs (~15%)
# 5. Average / steady improvement (~20%)

archetypes = np.random.choice(["all_rounder", "academic_only", "disengaged", "backlog_struggle", "average"], 
                              size=num_students, p=[0.25, 0.20, 0.20, 0.15, 0.20])

cgpa_list = []
marks_list = []
backlogs_list = []
att_overall_list = []
att_math_list = []
att_core_list = []
att_lab_list = []
lms_login_list = []
lms_assign_list = []
events_list = []
clubs_list = []
hackathons_list = []
certs_list = []
aptitude_list = []
coding_list = []
mock_interview_list = []
placement_status_list = []
tech_skill_list = []
soft_skill_list = []
satisfaction_list = []
faculty_rating_list = []
faculty_notes_list = []

for i, arch in enumerate(archetypes):
    yr = years[i]
    if arch == "all_rounder":
        cgpa = round(np.random.uniform(8.2, 9.8), 2)
        marks = round(np.random.uniform(82, 98), 1)
        backlogs = 0
        att_overall = round(np.random.uniform(85, 98), 1)
        att_math = round(np.clip(att_overall + np.random.uniform(-4, 4), 60, 100), 1)
        att_core = round(np.clip(att_overall + np.random.uniform(-3, 3), 60, 100), 1)
        att_lab = round(np.clip(att_overall + np.random.uniform(-2, 4), 60, 100), 1)
        lms_login = int(np.random.uniform(14, 28))
        lms_assign = round(np.random.uniform(88, 100), 1)
        events = int(np.random.uniform(5, 12))
        clubs = int(np.random.uniform(2, 4))
        hackathons = int(np.random.uniform(2, 6))
        certs = int(np.random.uniform(3, 8))
        aptitude = round(np.random.uniform(78, 98), 1)
        coding = round(np.random.uniform(80, 98), 1)
        mock_interview = round(np.random.uniform(82, 96), 1)
        tech_skill = round(np.random.uniform(80, 95), 1)
        soft_skill = round(np.random.uniform(80, 95), 1)
        satisfaction = round(np.random.uniform(4.2, 5.0), 1)
        fac_rating = round(np.random.uniform(4.3, 5.0), 1)
        fac_note = "Outstanding academic performance and proactive leadership in campus events."
        placement_status = "Placed" if yr == 4 and np.random.rand() > 0.3 else ("Eligible" if yr >= 3 else "On Track")

    elif arch == "academic_only":
        cgpa = round(np.random.uniform(7.8, 9.2), 2)
        marks = round(np.random.uniform(78, 92), 1)
        backlogs = 0
        att_overall = round(np.random.uniform(80, 95), 1)
        att_math = round(np.clip(att_overall + np.random.uniform(-5, 5), 60, 100), 1)
        att_core = round(np.clip(att_overall + np.random.uniform(-4, 4), 60, 100), 1)
        att_lab = round(np.clip(att_overall + np.random.uniform(-3, 3), 60, 100), 1)
        lms_login = int(np.random.uniform(10, 20))
        lms_assign = round(np.random.uniform(85, 98), 1)
        events = int(np.random.uniform(1, 4))
        clubs = int(np.random.uniform(0, 1))
        hackathons = int(np.random.uniform(0, 1))
        certs = int(np.random.uniform(0, 2))
        aptitude = round(np.random.uniform(50, 68), 1)
        coding = round(np.random.uniform(32, 52), 1)
        mock_interview = round(np.random.uniform(38, 56), 1)
        tech_skill = round(np.random.uniform(55, 68), 1)
        soft_skill = round(np.random.uniform(45, 62), 1)
        satisfaction = round(np.random.uniform(3.4, 4.4), 1)
        fac_rating = round(np.random.uniform(3.8, 4.5), 1)
        fac_note = "Strong in exams and theory, but hesitant in technical coding interviews and group speaking."
        placement_status = "Needs Training" if yr >= 3 else "On Track"

    elif arch == "disengaged":
        cgpa = round(np.random.uniform(5.0, 6.8), 2)
        marks = round(np.random.uniform(48, 65), 1)
        backlogs = int(np.random.choice([0, 1, 2], p=[0.5, 0.35, 0.15]))
        att_overall = round(np.random.uniform(52, 72), 1)
        att_math = round(np.clip(att_overall + np.random.uniform(-8, 4), 40, 85), 1)
        att_core = round(np.clip(att_overall + np.random.uniform(-6, 4), 40, 85), 1)
        att_lab = round(np.clip(att_overall + np.random.uniform(-5, 5), 40, 90), 1)
        lms_login = int(np.random.uniform(1, 5))
        lms_assign = round(np.random.uniform(35, 62), 1)
        events = int(np.random.uniform(0, 2))
        clubs = 0
        hackathons = 0
        certs = 0
        aptitude = round(np.random.uniform(40, 62), 1)
        coding = round(np.random.uniform(35, 58), 1)
        mock_interview = round(np.random.uniform(40, 60), 1)
        tech_skill = round(np.random.uniform(42, 60), 1)
        soft_skill = round(np.random.uniform(40, 62), 1)
        satisfaction = round(np.random.uniform(2.1, 3.4), 1)
        fac_rating = round(np.random.uniform(2.2, 3.2), 1)
        fac_note = "Irregular attendance in morning lectures and missing LMS assignment deadlines."
        placement_status = "Needs Training" if yr >= 3 else "At Risk"

    elif arch == "backlog_struggle":
        cgpa = round(np.random.uniform(4.2, 6.2), 2)
        marks = round(np.random.uniform(42, 58), 1)
        backlogs = int(np.random.choice([1, 2, 3, 4], p=[0.4, 0.3, 0.2, 0.1]))
        att_overall = round(np.random.uniform(62, 78), 1)
        att_math = round(np.clip(att_overall + np.random.uniform(-10, 2), 35, 80), 1)
        att_core = round(np.clip(att_overall + np.random.uniform(-7, 3), 40, 80), 1)
        att_lab = round(np.clip(att_overall + np.random.uniform(-4, 6), 50, 85), 1)
        lms_login = int(np.random.uniform(3, 8))
        lms_assign = round(np.random.uniform(45, 70), 1)
        events = int(np.random.uniform(0, 3))
        clubs = int(np.random.choice([0, 1]))
        hackathons = 0
        certs = int(np.random.choice([0, 1]))
        aptitude = round(np.random.uniform(38, 58), 1)
        coding = round(np.random.uniform(30, 52), 1)
        mock_interview = round(np.random.uniform(35, 55), 1)
        tech_skill = round(np.random.uniform(40, 55), 1)
        soft_skill = round(np.random.uniform(45, 65), 1)
        satisfaction = round(np.random.uniform(2.5, 3.8), 1)
        fac_rating = round(np.random.uniform(2.4, 3.3), 1)
        fac_note = "Struggling with prerequisite technical subjects; needs remedial classes and clear study schedule."
        placement_status = "Ineligible (Backlogs)" if yr >= 3 else "Needs Academic Support"

    else:  # average
        cgpa = round(np.random.uniform(6.8, 8.0), 2)
        marks = round(np.random.uniform(68, 80), 1)
        backlogs = 0
        att_overall = round(np.random.uniform(75, 88), 1)
        att_math = round(np.clip(att_overall + np.random.uniform(-4, 4), 60, 95), 1)
        att_core = round(np.clip(att_overall + np.random.uniform(-4, 4), 60, 95), 1)
        att_lab = round(np.clip(att_overall + np.random.uniform(-3, 5), 65, 95), 1)
        lms_login = int(np.random.uniform(7, 16))
        lms_assign = round(np.random.uniform(72, 88), 1)
        events = int(np.random.uniform(2, 6))
        clubs = int(np.random.uniform(1, 2))
        hackathons = int(np.random.uniform(0, 2))
        certs = int(np.random.uniform(1, 3))
        aptitude = round(np.random.uniform(62, 78), 1)
        coding = round(np.random.uniform(58, 75), 1)
        mock_interview = round(np.random.uniform(60, 76), 1)
        tech_skill = round(np.random.uniform(62, 78), 1)
        soft_skill = round(np.random.uniform(65, 80), 1)
        satisfaction = round(np.random.uniform(3.5, 4.5), 1)
        fac_rating = round(np.random.uniform(3.5, 4.2), 1)
        fac_note = "Consistent performer with balanced engagement; receptive to feedback and mentoring."
        placement_status = "Eligible" if yr >= 3 else "On Track"

    cgpa_list.append(cgpa)
    marks_list.append(marks)
    backlogs_list.append(backlogs)
    att_overall_list.append(att_overall)
    att_math_list.append(att_math)
    att_core_list.append(att_core)
    att_lab_list.append(att_lab)
    lms_login_list.append(lms_login)
    lms_assign_list.append(lms_assign)
    events_list.append(events)
    clubs_list.append(clubs)
    hackathons_list.append(hackathons)
    certs_list.append(certs)
    aptitude_list.append(aptitude)
    coding_list.append(coding)
    mock_interview_list.append(mock_interview)
    placement_status_list.append(placement_status)
    tech_skill_list.append(tech_skill)
    soft_skill_list.append(soft_skill)
    satisfaction_list.append(satisfaction)
    faculty_rating_list.append(fac_rating)
    faculty_notes_list.append(fac_note)

df = pd.DataFrame({
    "student_id": student_ids,
    "name": names,
    "department": depts,
    "year": years,
    "cgpa": cgpa_list,
    "marks_percentage": marks_list,
    "backlog_count": backlogs_list,
    "attendance_overall": att_overall_list,
    "attendance_math": att_math_list,
    "attendance_core": att_core_list,
    "attendance_lab": att_lab_list,
    "lms_login_frequency": lms_login_list,
    "lms_assignment_completion": lms_assign_list,
    "events_attended": events_list,
    "club_memberships": clubs_list,
    "hackathons_participated": hackathons_list,
    "certifications_count": certs_list,
    "aptitude_score": aptitude_list,
    "coding_score": coding_list,
    "mock_interview_score": mock_interview_list,
    "placement_status": placement_status_list,
    "technical_skill_score": tech_skill_list,
    "soft_skill_score": soft_skill_list,
    "student_satisfaction": satisfaction_list,
    "faculty_feedback_rating": faculty_rating_list,
    "faculty_notes": faculty_notes_list
})

df.to_csv("students.csv", index=False)
print(f"Generated students.csv with {len(df)} records and {len(df.columns)} columns.")
