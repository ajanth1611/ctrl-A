# 🔒 CampusIQ Security & Data Privacy Architecture

## 1. Authentication & Role Authorization

- **Multi-Role Gateway**: CampusIQ implements three differentiated user roles: `admin`, `staff`, and `student`.
- **Server-Side Role Verification**: The role selected at login is treated as an intent preference, **never as proof of permission**. The user's trusted role is retrieved from the database record and verified. If an administrator credentials are submitted to the student portal, access is rejected with a clear mismatch error.
- **Pre-Authentication Lock**: Dashboards and student records are never rendered before successful authentication.
- SQLite demo passwords are stored as salted PBKDF2-SHA256 hashes. Existing legacy plaintext credentials are upgraded during database initialization.
- One-click shortcuts are enabled by default for local SQLite demos to support the hackathon walkthrough. Set `CAMPUSIQ_ENABLE_DEMO_LOGIN=false` to disable them. They are hidden when Supabase is configured. Do not use shortcuts with real institutional records or shared access.

---

## 2. Authorization & Data Isolation

### Student Record Ownership
- Students are restricted to accessing their own profile and records (`verify_student_access(user, student_id)`).
- SQL and DataFrame queries filter automatically by `user.student_id`. A student cannot view or search other students' grades, attendance, or mentoring notes.

### Staff Assignment Restrictions
- Faculty mentors and advisors only access students whose `mentor_email` matches their authenticated account. Department membership alone does not grant access.
- Mentoring notes and intervention progress are protected from unauthorized cross-department view.

### Administrator Controls
- System administration actions (changing scoring weights, assigning mentors, running bulk CSV imports) are restricted to `admin` roles.

---

## 3. Supabase Status and Production Limitations

With Supabase configured, authentication uses Supabase Auth and application data requests use the signed-in user's public anon-key session. The application does not use a service-role key. Without real Supabase settings, the app uses local SQLite with fictional demo accounts. It does not fall back to SQLite after Supabase configuration or request failures.

The initial migration contained incomplete policies, including staff visibility across their whole department. The follow-up migration adds own-profile/admin policies, explicit mentor-assignment policies, and policies for interventions, tasks, and import auditing. Apply both migrations in filename order and review them before using a Supabase project. Live database policies and account setup have not been verified in this workspace because no Supabase project was supplied. Never put a `service_role` key in app configuration.

---

## 4. Input Sanitization & Error Handling

- CSV ingestion validates string types, numbers, and boundary ranges (e.g., CGPA $0.0 - 10.0$, Attendance $0.0 - 100.0\%$).
- Invalid rows are flagged, isolated, and downloadable as an audit CSV rather than corrupting database state.
