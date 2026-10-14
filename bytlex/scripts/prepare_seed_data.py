import csv
import json
import os

students = []
with open("students.csv", mode="r", encoding="utf-8") as f:
    reader = csv.DictReader(f)
    for r in reader:
        # Convert numeric fields
        sem = int(r.get("year", 3)) * 2 - 1  # 3rd year -> 5th sem, 4th year -> 7th sem
        student = {
            "student_id": r["student_id"],
            "name": r["name"],
            "email": f"{r['name'].lower().replace(' ', '.')}@student.campus.edu",
            "department": r["department"],
            "semester": sem,
            "cgpa": float(r["cgpa"]),
            "marks_percentage": float(r["marks_percentage"]),
            "backlog_count": int(r.get("backlog_count", 0)),
            "attendance_overall": float(r["attendance_overall"]),
            "attendance_math": float(r.get("attendance_math", r["attendance_overall"])),
            "attendance_core": float(r.get("attendance_core", r["attendance_overall"])),
            "attendance_lab": float(r.get("attendance_lab", r["attendance_overall"])),
            "lms_login_frequency": int(r.get("lms_login_frequency", 10)),
            "lms_assignment_completion": float(r.get("lms_assignment_completion", 80.0)),
            "extracurricular_score": float(int(r.get("events_attended", 2)) * 10 + int(r.get("hackathons_participated", 0)) * 15),
            "technical_skills_score": float(r.get("technical_skill_score", 65.0)),
            "aptitude_score": float(r.get("aptitude_score", 60.0)),
            "coding_score": float(r.get("coding_score", 60.0)),
            "mock_interview_score": float(r.get("mock_interview_score", 60.0)),
            "student_feedback_score": float(r.get("student_satisfaction", 4.0)),
            "placement_status": r.get("placement_status", "Eligible"),
            "faculty_notes": r.get("faculty_notes", ""),
            "mentor_id": "staff_sharma_01" if "Computer" in r["department"] or "Information" in r["department"] or "Artificial" in r["department"] else "staff_kulkarni_02",
            "mentor_name": "Dr. Ananya Sharma" if "Computer" in r["department"] or "Information" in r["department"] or "Artificial" in r["department"] else "Prof. Rajesh Kulkarni",
            "mentor_email": "dr.sharma@campus.edu" if "Computer" in r["department"] or "Information" in r["department"] or "Artificial" in r["department"] else "prof.rajesh@campus.edu",
        }
        # Cap extracurricular to 100
        student["extracurricular_score"] = min(100.0, max(20.0, student["extracurricular_score"]))
        students.append(student)

# Add a few edge cases:
# 1. Missing attendance data
edge_1 = dict(students[0])
edge_1["student_id"] = "STU2021991"
edge_1["name"] = "Aarav Nambiar (Missing Attendance)"
edge_1["email"] = "aarav.nambiar@student.campus.edu"
edge_1["attendance_overall"] = None  # None
edge_1["faculty_notes"] = "Medical leave pending institutional attendance condonation."
students.append(edge_1)

# 2. Missing placement data
edge_2 = dict(students[1])
edge_2["student_id"] = "STU2021992"
edge_2["name"] = "Meera Sengupta (Freshman / No Placement)"
edge_2["email"] = "meera.sengupta@student.campus.edu"
edge_2["semester"] = 1
edge_2["aptitude_score"] = None
edge_2["coding_score"] = None
edge_2["mock_interview_score"] = None
edge_2["faculty_notes"] = "First-year student; placement modules not yet scheduled."
students.append(edge_2)

# 3. High CGPA with zero interview preparation
edge_3 = dict(students[2])
edge_3["student_id"] = "STU2021993"
edge_3["name"] = "Vikramaditya Roy (Exam Star, Interview Fear)"
edge_3["email"] = "vikramaditya.roy@student.campus.edu"
edge_3["cgpa"] = 9.45
edge_3["marks_percentage"] = 96.0
edge_3["coding_score"] = 38.0
edge_3["mock_interview_score"] = 32.0
edge_3["aptitude_score"] = 52.0
edge_3["faculty_notes"] = "Excels at textbook exams; severe anxiety during placement mock interviews."
students.append(edge_3)

# 4. Severe backlogs and low attendance
edge_4 = dict(students[3])
edge_4["student_id"] = "STU2021994"
edge_4["name"] = "Devansh Verma (Critical Risk)"
edge_4["email"] = "devansh.verma@student.campus.edu"
edge_4["cgpa"] = 4.82
edge_4["marks_percentage"] = 48.0
edge_4["backlog_count"] = 4
edge_4["attendance_overall"] = 49.5
edge_4["lms_assignment_completion"] = 35.0
edge_4["lms_login_frequency"] = 2
edge_4["faculty_notes"] = "Multiple backlogs across 3 semesters, urgent dean escalation needed."
students.append(edge_4)

# Create src/data directory
os.makedirs("src/data", exist_ok=True)
os.makedirs("sample-data", exist_ok=True)

# Write src/data/seedStudents.ts
with open("src/data/seedStudents.ts", "w", encoding="utf-8") as f:
    f.write('import { Student } from "@/types";\n\n')
    f.write('export const SEED_STUDENTS: Student[] = ')
    f.write(json.dumps(students, indent=2))
    f.write(' as Student[];\n')

print(f"Generated src/data/seedStudents.ts with {len(students)} students.")

# Also generate separate CSVs in sample-data/ for CSV Import demonstration:
# 1. student_master.csv
with open("sample-data/student_master.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "name", "email", "department", "semester", "placement_status"])
    writer.writeheader()
    for s in students[:50]:
        writer.writerow({
            "student_id": s["student_id"],
            "name": s["name"],
            "email": s["email"],
            "department": s["department"],
            "semester": s["semester"],
            "placement_status": s.get("placement_status", "Eligible")
        })

# 2. academic_records.csv
with open("sample-data/academic_records.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "cgpa", "marks_percentage", "backlog_count"])
    writer.writeheader()
    for s in students[:50]:
        writer.writerow({
            "student_id": s["student_id"],
            "cgpa": s["cgpa"],
            "marks_percentage": s["marks_percentage"],
            "backlog_count": s["backlog_count"]
        })

# 3. attendance_records.csv
with open("sample-data/attendance_records.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "attendance_overall", "attendance_math", "attendance_core", "attendance_lab"])
    writer.writeheader()
    for s in students[:50]:
        writer.writerow({
            "student_id": s["student_id"],
            "attendance_overall": s["attendance_overall"] if s["attendance_overall"] is not None else "",
            "attendance_math": s.get("attendance_math", ""),
            "attendance_core": s.get("attendance_core", ""),
            "attendance_lab": s.get("attendance_lab", "")
        })

# 4. lms_records.csv
with open("sample-data/lms_records.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "lms_login_frequency", "lms_assignment_completion"])
    writer.writeheader()
    for s in students[:50]:
        writer.writerow({
            "student_id": s["student_id"],
            "lms_login_frequency": s["lms_login_frequency"],
            "lms_assignment_completion": s["lms_assignment_completion"]
        })

# 5. placement_assessments.csv
with open("sample-data/placement_assessments.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "aptitude_score", "coding_score", "mock_interview_score"])
    writer.writeheader()
    for s in students[:50]:
        writer.writerow({
            "student_id": s["student_id"],
            "aptitude_score": s["aptitude_score"] if s["aptitude_score"] is not None else "",
            "coding_score": s["coding_score"] if s["coding_score"] is not None else "",
            "mock_interview_score": s["mock_interview_score"] if s["mock_interview_score"] is not None else ""
        })

# 6. skills_assessments.csv
with open("sample-data/skills_assessments.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "technical_skills_score", "extracurricular_score"])
    writer.writeheader()
    for s in students[:50]:
        writer.writerow({
            "student_id": s["student_id"],
            "technical_skills_score": s["technical_skills_score"],
            "extracurricular_score": s["extracurricular_score"]
        })

# 7. import_with_errors.csv (to test validation error inspector)
with open("sample-data/import_with_errors.csv", "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["student_id", "name", "cgpa", "attendance_overall", "backlog_count"])
    writer.writeheader()
    writer.writerow({"student_id": "STU2021001", "name": "Karan Saxena", "cgpa": "9.13", "attendance_overall": "92.3", "backlog_count": "0"}) # Valid
    writer.writerow({"student_id": "", "name": "Nameless Missing ID", "cgpa": "7.5", "attendance_overall": "80.0", "backlog_count": "0"}) # Error: missing ID
    writer.writerow({"student_id": "STU2021005", "name": "Gaurav Chopra", "cgpa": "14.5", "attendance_overall": "88.1", "backlog_count": "0"}) # Error: CGPA > 10
    writer.writerow({"student_id": "STU2021007", "name": "Simran Gupta", "cgpa": "8.43", "attendance_overall": "150.0", "backlog_count": "0"}) # Error: Attendance > 100
    writer.writerow({"student_id": "STU2021008", "name": "Kavya Patel", "cgpa": "invalid_num", "attendance_overall": "79.5", "backlog_count": "0"}) # Error: Not a number
    writer.writerow({"student_id": "STU2021009", "name": "Riya Mishra", "cgpa": "8.32", "attendance_overall": "81.2", "backlog_count": "-3"}) # Error: negative backlogs

print("Sample CSV files generated in sample-data/ successfully.")
