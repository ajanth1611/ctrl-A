# 📚 CampusIQ Data Dictionary

## 1. Supported Ingestion Datasets

### A. Student Master Data (`student_master.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | e.g. `STU2021001` | Unique institutional student identifier |
| `name` | String | Yes | Full Name | Student's registered full name |
| `email` | String | No | Valid email | Institutional student email |
| `department` | String | Yes | e.g. `Computer Science & Engineering` | Academic department |
| `semester` | Integer | Yes | 1 to 8 | Current academic semester |
| `placement_status`| String | No | `Placed`, `Eligible`, `Needs Training` | Recruitment eligibility status |

### B. Academic Records (`academic_records.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | Unique ID | Primary key reference |
| `cgpa` | Float | Yes | 0.00 to 10.00 | Cumulative Grade Point Average |
| `marks_percentage`| Float | Yes | 0.0 to 100.0 | Overall aggregate marks percentage |
| `backlog_count` | Integer | No | $\ge 0$ | Total number of uncleared backlogs |

### C. Classroom Attendance (`attendance_records.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | Unique ID | Primary key reference |
| `attendance_overall`| Float | Yes | 0.0 to 100.0% | Overall semester attendance |
| `attendance_math` | Float | No | 0.0 to 100.0% | Attendance in Mathematics courses |
| `attendance_core` | Float | No | 0.0 to 100.0% | Attendance in Core departmental courses |
| `attendance_lab` | Float | No | 0.0 to 100.0% | Attendance in practical laboratory sessions|

### D. LMS Engagement Records (`lms_records.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | Unique ID | Primary key reference |
| `lms_login_frequency`| Integer| Yes| $\ge 0$ (benchmark: 20/wk) | Logins per week on learning portal |
| `lms_assignment_completion`| Float| Yes | 0.0 to 100.0% | Proportion of completed online assignments |

### E. Placement Assessments (`placement_assessments.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | Unique ID | Primary key reference |
| `aptitude_score` | Float | Yes | 0.0 to 100.0 | Quantitative & logical reasoning score |
| `coding_score` | Float | Yes | 0.0 to 100.0 | Technical programming test score |
| `mock_interview_score`| Float | Yes | 0.0 to 100.0 | Practical mock interview rating |

### F. Technical Skills & Extracurriculars (`skills_assessments.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | Unique ID | Primary key reference |
| `technical_skills_score`| Float | Yes | 0.0 to 100.0 | Assessed technical practical competencies |
| `extracurricular_score`| Float | No | 0.0 to 100.0 | Hackathon, clubs, and sports involvement |

### G. Student Feedback & Mentoring (`student_feedback.csv`)
| Column Name | Type | Required | Valid Range / Format | Description |
| :--- | :---: | :---: | :--- | :--- |
| `student_id` | String | Yes | Unique ID | Primary key reference |
| `student_feedback_score`| Float | Yes | 1.0 to 5.0 | Student institutional satisfaction rating |
| `faculty_notes` | String | No | Text description | Qualitative mentoring observations |
