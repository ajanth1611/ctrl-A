# 📐 Student Success Scoring & Risk Assessment Methodology

## 1. Overview and Design Principles

The CampusIQ Student Success Engine provides an **explainable, deterministic, multi-source scoring and early warning system** for college faculty, academic advisors, and placement coordinators.

### Core Tenets:
1. **Zero Black-Box Bias**: Every score can be traced back to exact weighted points, positive drivers, and negative drags.
2. **Distinct Risk Axes**: Academic risk (course backlogs, exam grades, attendance) is evaluated independently from Placement risk (coding assessments, aptitude tests, interview confidence).
3. **Data Completeness & Fairness**: CSV ingestion validates required fields and reports row errors. Optional or absent fields are filled with documented defaults before scoring; the current scorer does not dynamically renormalize weights or label profiles "Insufficient Data." Treat scores for records with imputed values as provisional and review the import report before using them for interventions.

---

## 2. Dimension Weights and Normalized Sub-Scores

All 6 student dimensions are normalized onto a uniform 0–100 scale ($I_i \in [0, 100]$):

| Dimension | Default Weight ($W_i$) | Component Formula & Normalization Logic |
| :--- | :---: | :--- |
| **Academic Performance** | **30%** (0.30) | $\text{clip}(0.70 \times (\text{CGPA} \times 10) + 0.30 \times \text{Marks} - (\text{Backlogs} \times 12), 0, 100)$ |
| **Attendance Record** | **20%** (0.20) | Classroom attendance percentage (statutory warning cutoff at 75%) |
| **LMS Engagement** | **15%** (0.15) | $0.40 \times \left(\min(20, \text{Logins})/20 \times 100\right) + 0.60 \times \text{Assignment Completion Rate}$ |
| **Placement Readiness** | **20%** (0.20) | $0.35 \times \text{Aptitude} + 0.40 \times \text{Coding Score} + 0.25 \times \text{Mock Interview Score}$ |
| **Technical Skills & Extra** | **10%** (0.10) | $0.60 \times \text{Technical Practical Assessment} + 0.40 \times \text{Extracurricular Engagement}$ |
| **Student Feedback** | **5%** (0.05) | $(\text{Student Satisfaction Rating} / 5.0) \times 100$ |
| **Total** | **100%** (1.00) | $\sum_{i=1}^{6} (W_i \times I_i)$ |

---

## 3. Risk Identification Rules

### A. Academic Risk Tier
* **High Risk**: Active Backlogs $\ge 2$, OR CGPA $< 5.5$, OR Academic Score $< 50.0$.
* **Medium Risk**: Active Backlogs $= 1$, OR CGPA $< 6.5$, OR Academic Score $< 65.0$.
* **Low Risk**: CGPA $\ge 6.5$, Zero backlogs, Academic Score $\ge 65.0$.

### B. Placement Risk Tier
* **High Risk**: Coding Score $< 45.0$, OR Aptitude Score $< 50.0$, OR Mock Interview Score $< 45.0$, OR Placement Index $< 50.0$.
* **Medium Risk**: Placement Index $< 65.0$, OR Aptitude Score $< 60.0$, OR Coding Score $< 50.0$ (provided no high-risk condition applies).
* **Low Risk**: Meets or exceeds campus recruitment cutoffs.

### C. Independent Critical Rules
1. **Attendance Cutoff (< 75%)**: Triggers statutory attendance warning and mandatory faculty counseling.
2. **Academic-Placement Asymmetry**: High CGPA ($\ge 8.0$) but low placement readiness ($< 55.0$). Flags students who excel at written exams but suffer from interview anxiety or practical coding deficits.
3. **Hands-on Talent Alert**: Low theoretical CGPA ($< 6.5$) but high coding scores ($\ge 80.0$). Flags practical coders who need academic tutoring to clear eligibility hurdles.

---

## 4. Cohort Segmentation Rules

| Segment | Criteria | Target Institutional Action |
| :--- | :--- | :--- |
| **Placed Champion** | Official status is 'Placed' | Peer mentoring & alumni talk |
| **Academic High Flier** | Score $\ge 82$ and CGPA $\ge 8.5$ | Research fellowships, honors tracks |
| **Placement Star** | Coding $\ge 80$ and Placement Low Risk | Tier-1 recruitment drives |
| **Theory-Oriented Scholar** | CGPA $\ge 8.0$ but Placement High Risk | Mock interview coaching, soft skills |
| **Practical Coder / Hands-on** | Coding $\ge 75$ but CGPA $< 6.5$ | Remedial theory tutoring |
| **Urgent Intervention Needed**| Backlogs $\ge 2$ or Attendance $< 70\%$ | Dean escalation, parent-teacher meet |
