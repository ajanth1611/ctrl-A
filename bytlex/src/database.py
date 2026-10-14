"""
CampusIQ persistence and authorization layer.
Supabase uses the signed-in user's anon-key session; SQLite remains the local demo path.
"""

import os
import hashlib
import hmac
import json
import secrets
import sqlite3
import datetime
import base64
import logging
import uuid
from typing import Optional, List, Dict, Any, Tuple
import pandas as pd

# Load environment variables if available
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from supabase import create_client
    from supabase_auth.errors import AuthApiError
    from postgrest.exceptions import APIError
    from httpx import RequestError as HttpRequestError

    HAS_SUPABASE_LIB = True
except ImportError:
    create_client = None

    class AuthApiError(Exception):
        pass

    class APIError(Exception):
        pass

    class HttpRequestError(Exception):
        pass

    HAS_SUPABASE_LIB = False

logger = logging.getLogger(__name__)

DEFAULT_DB_PATH = os.getenv(
    "CAMPUSIQ_DB_PATH",
    os.path.join(os.path.dirname(os.path.dirname(__file__)), "campusiq.db"),
)
DEFAULT_SCHEMA_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "schema.sql")

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY", "")
_legacy_supabase_key = os.getenv("SUPABASE_KEY", "")


def _is_real_setting(value: str) -> bool:
    normalized = value.strip().lower()
    return bool(normalized) and not any(
        marker in normalized
        for marker in ("your-project", "your-anon", "placeholder")
    )


SUPABASE_SETUP_REQUESTED = True


def _is_service_role_key(key: str) -> bool:
    if key.strip().startswith("sb_secret_"):
        return True
    parts = key.strip().split(".")
    if len(parts) != 3:
        return False
    try:
        payload = parts[1] + "=" * (-len(parts[1]) % 4)
        claims = json.loads(base64.urlsafe_b64decode(payload))
    except (ValueError, json.JSONDecodeError):
        return False
    return isinstance(claims, dict) and claims.get("role") == "service_role"


def _validate_supabase_configuration() -> None:
    if not SUPABASE_SETUP_REQUESTED:
        return
    if not SUPABASE_URL.strip() or not _is_real_setting(SUPABASE_URL):
        raise RuntimeError("SUPABASE_URL must be set to your Supabase project URL.")
    configured_key = SUPABASE_ANON_KEY or _legacy_supabase_key
    if not _is_real_setting(configured_key):
        raise RuntimeError("Set SUPABASE_ANON_KEY to your project's public anon key.")
    if _is_service_role_key(configured_key):
        raise RuntimeError(
            "A Supabase service_role/secret key is not accepted. Use only the public anon key."
        )
    if not HAS_SUPABASE_LIB or create_client is None:
        raise RuntimeError(
            "Supabase settings are present but the Supabase Python client is not installed."
        )


def _new_supabase_client() -> Any:
    _validate_supabase_configuration()
    return create_client(SUPABASE_URL, SUPABASE_ANON_KEY or _legacy_supabase_key)


def _supabase_client_for_user(current_user: Optional[Dict[str, Any]]) -> Any:
    if not current_user or not current_user.get("access_token") or not current_user.get("refresh_token"):
        raise PermissionError("Sign in with your institutional account to access this data.")
    client = _new_supabase_client()
    response = client.auth.set_session(
        current_user["access_token"],
        current_user["refresh_token"],
    )
    session = getattr(response, "session", None) or client.auth.get_session()
    if session:
        current_user["access_token"] = session.access_token
        current_user["refresh_token"] = session.refresh_token
    return client


def sign_out_supabase_user(current_user: Dict[str, Any]) -> bool:
    """Revoke the signed-in Supabase session when the identity provider is reachable."""
    try:
        _supabase_client_for_user(current_user).auth.sign_out()
    except (AuthApiError, APIError, HttpRequestError) as exc:
        logger.error("Supabase sign-out request failed: %s", type(exc).__name__)
        return False
    return True


def is_using_supabase() -> bool:
    """Return whether a real Supabase project has been configured."""
    return SUPABASE_SETUP_REQUESTED


_PASSWORD_HASH_ITERATIONS = 310_000


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${_PASSWORD_HASH_ITERATIONS}${salt.hex()}${digest.hex()}"


def _verify_password(password: str, stored_value: str) -> Tuple[bool, bool]:
    """Return whether a password matches and whether the stored value is legacy plaintext."""
    if not stored_value.startswith("pbkdf2_sha256$"):
        return hmac.compare_digest(
            password.encode("utf-8"), stored_value.encode("utf-8")
        ), True

    try:
        algorithm, iterations, salt_hex, digest_hex = stored_value.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False, False
        digest = hashlib.pbkdf2_hmac(
            "sha256",
            password.encode("utf-8"),
            bytes.fromhex(salt_hex),
            int(iterations),
        )
        return hmac.compare_digest(digest.hex(), digest_hex), False
    except (ValueError, TypeError):
        return False, False


# ==============================================================================
# SQLITE CORE OPERATIONS
# ==============================================================================
def get_db_connection(db_path: str = DEFAULT_DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_columns_exist(conn: sqlite3.Connection, table_name: str, required_cols: Dict[str, str]) -> None:
    """Ensures that newly added columns exist in existing SQLite tables."""
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name});")
    existing_cols = {row["name"] for row in cursor.fetchall()}

    for col_name, col_type in required_cols.items():
        if col_name not in existing_cols:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {col_name} {col_type};")


def init_database(db_path: str = DEFAULT_DB_PATH) -> None:
    """Initialize local SQLite, or leave schema management to Supabase migrations."""
    if SUPABASE_SETUP_REQUESTED:
        _validate_supabase_configuration()
        return
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        
        # 1. Profiles (Auth & Role assignments)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS profiles (
            id TEXT PRIMARY KEY,
            email TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'staff', 'student')),
            department TEXT,
            student_id TEXT,
            designation TEXT,
            password_hash TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 2. Students Master Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS students (
            student_id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT,
            department TEXT NOT NULL,
            semester INTEGER NOT NULL,
            cgpa REAL NOT NULL,
            marks_percentage REAL NOT NULL,
            backlog_count INTEGER DEFAULT 0,
            attendance_overall REAL NOT NULL,
            attendance_math REAL,
            attendance_core REAL,
            attendance_lab REAL,
            lms_assignment_completion REAL NOT NULL,
            lms_login_frequency INTEGER DEFAULT 0,
            extracurricular_score REAL DEFAULT 50.0,
            technical_skills_score REAL DEFAULT 50.0,
            aptitude_score REAL DEFAULT 50.0,
            coding_score REAL DEFAULT 50.0,
            mock_interview_score REAL DEFAULT 50.0,
            student_feedback_score REAL DEFAULT 4.0,
            placement_status TEXT DEFAULT 'Eligible',
            success_score REAL,
            academic_risk TEXT,
            placement_risk TEXT,
            risk_level TEXT,
            segment TEXT,
            mentor_id TEXT,
            mentor_name TEXT,
            mentor_email TEXT,
            faculty_notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Ensure schema migrations on existing database
        student_cols = {
            "email": "TEXT",
            "attendance_math": "REAL",
            "attendance_core": "REAL",
            "attendance_lab": "REAL",
            "placement_status": "TEXT DEFAULT 'Eligible'",
            "academic_risk": "TEXT",
            "placement_risk": "TEXT",
            "mentor_id": "TEXT",
            "mentor_name": "TEXT",
            "mentor_email": "TEXT",
            "faculty_notes": "TEXT",
        }
        _ensure_columns_exist(conn, "students", student_cols)

        # 3. Interventions Table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS interventions (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            student_name TEXT NOT NULL,
            department TEXT NOT NULL,
            intervention_type TEXT NOT NULL,
            priority TEXT DEFAULT 'Medium' CHECK(priority IN ('Urgent', 'High', 'Medium', 'Low')),
            owner_name TEXT NOT NULL,
            owner_email TEXT,
            due_date TEXT NOT NULL,
            status TEXT DEFAULT 'Pending' CHECK(status IN ('Pending', 'In Progress', 'Completed', 'Escalated')),
            description TEXT,
            goal TEXT,
            outcome_measured TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (student_id) REFERENCES students(student_id) ON DELETE CASCADE
        );
        """)

        int_cols = {
            "owner_email": "TEXT",
            "priority": "TEXT DEFAULT 'Medium'",
            "goal": "TEXT",
            "outcome_measured": "TEXT",
        }
        _ensure_columns_exist(conn, "interventions", int_cols)

        # 4. Data Import Jobs History
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS data_import_jobs (
            id TEXT PRIMARY KEY,
            dataset_type TEXT NOT NULL,
            filename TEXT NOT NULL,
            total_rows INTEGER NOT NULL,
            valid_rows INTEGER NOT NULL,
            invalid_rows INTEGER NOT NULL,
            inserted_rows INTEGER NOT NULL,
            updated_rows INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # 5. Action Plan Tasks
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS action_plan_tasks (
            id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            title TEXT NOT NULL,
            description TEXT,
            category TEXT NOT NULL,
            priority TEXT NOT NULL,
            effort_hours REAL DEFAULT 2.0,
            due_date TEXT,
            completed INTEGER DEFAULT 0,
            reason TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Indexes for fast lookup
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_dept ON students(department);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_risk ON students(risk_level);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_students_mentor ON students(mentor_email);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_interventions_student ON interventions(student_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_profiles_email ON profiles(email);")

        conn.commit()

    # Seed default user profiles if empty (only for local SQLite)
    if not SUPABASE_SETUP_REQUESTED:
        seed_default_users(db_path)
        _upgrade_legacy_password_hashes(db_path)


def seed_default_users(db_path: str = DEFAULT_DB_PATH) -> None:
    """Pre-populates trusted demo users across all roles."""
    default_users = [
        ("user_admin_01", "admin@campus.edu", "Dr. Vikram Nair", "admin", "Academic Affairs & Planning", None, "Dean of Academic Operations", "AdminPass2026!"),
        ("staff_sharma_01", "dr.sharma@campus.edu", "Dr. Ananya Sharma", "staff", "Computer Science & Engineering", None, "Associate Professor & Placement Lead", "StaffPass2026!"),
        ("staff_kulkarni_02", "prof.rajesh@campus.edu", "Prof. Rajesh Kulkarni", "staff", "Mechanical Engineering", None, "Senior Faculty Mentor", "StaffPass2026!"),
        ("stu_karan_04", "karan.pillai@student.campus.edu", "Karan Pillai", "student", "Electronics & Communication", "STU2021004", "Undergraduate Student", "StudentPass2026!"),
        ("stu_pranav_02", "pranav.deshmukh@student.campus.edu", "Pranav Deshmukh", "student", "Electronics & Communication", "STU2021002", "Undergraduate Student", "StudentPass2026!"),
        ("stu_simran_07", "simran.gupta@student.campus.edu", "Simran Gupta", "student", "Computer Science & Engineering", "STU2021007", "Undergraduate Student", "StudentPass2026!"),
        ("stu_karan_saxena_05", "karan.saxena@student.campus.edu", "Karan Saxena", "student", "Computer Science & Engineering", "STU2021010", "Undergraduate Student", "karan@123")
    ]
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        for u in default_users:
            cursor.execute("SELECT 1 FROM profiles WHERE lower(email) = lower(?)", (u[1],))
            if cursor.fetchone():
                continue
            cursor.execute("""
            INSERT OR IGNORE INTO profiles (id, email, name, role, department, student_id, designation, password_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (*u[:7], _hash_password(u[7])))
        conn.commit()


def _upgrade_legacy_password_hashes(db_path: str) -> None:
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        rows = cursor.execute(
            "SELECT id, password_hash FROM profiles"
        ).fetchall()
        for row in rows:
            stored_value = str(row["password_hash"] or "")
            if not stored_value.startswith("pbkdf2_sha256$"):
                cursor.execute(
                    "UPDATE profiles SET password_hash = ? WHERE id = ?",
                    (_hash_password(stored_value), row["id"]),
                )
        conn.commit()


# ==============================================================================
# AUTHENTICATION & ACCESS VERIFICATION
# ==============================================================================
def authenticate_user(email_or_id: str, password: str, intended_role: str, db_path: str = DEFAULT_DB_PATH) -> Tuple[bool, Optional[Dict[str, Any]], Optional[str]]:
    """
    Authenticates user and strictly verifies that their trusted database role
    matches the requested login role. The selected role is never accepted as proof of permission.
    """
    clean_query = email_or_id.strip().lower()
    if SUPABASE_SETUP_REQUESTED:
        init_database(db_path)
        client = _new_supabase_client()
        try:
            response = client.auth.sign_in_with_password(
                {"email": clean_query, "password": password}
            )
        except AuthApiError:
            return False, None, "Invalid institutional credentials."
        except HttpRequestError as exc:
            logger.error("Supabase authentication request failed: %s", type(exc).__name__)
            return False, None, "Authentication service is unavailable. Please try again."

        session = response.session
        auth_user = response.user
        if not session or not auth_user:
            return False, None, "Authentication did not return a valid user session."
        try:
            profile_response = (
                client.table("profiles")
                .select("*")
                .eq("id", str(auth_user.id))
                .limit(1)
                .execute()
            )
        except (APIError, HttpRequestError) as exc:
            logger.error("Supabase profile lookup failed: %s", type(exc).__name__)
            return False, None, "Unable to load your authorized profile. Contact an administrator."
        profiles = profile_response.data or []
        if not profiles:
            client.auth.sign_out()
            return (
                False,
                None,
                "Your account has no CampusIQ profile. Contact an administrator to request access.",
            )
        user_dict = dict(profiles[0])
        if str(user_dict.get("id")) != str(auth_user.id):
            client.auth.sign_out()
            return False, None, "The authenticated account does not match its authorized profile."
        if str(user_dict.get("email", "")).casefold() != str(auth_user.email or "").casefold():
            client.auth.sign_out()
            return False, None, "The authenticated account does not match its authorized profile."
        if user_dict.get("role") != intended_role:
            client.auth.sign_out()
            return (
                False,
                None,
                f"Access Denied: This account is officially registered as "
                f"'{str(user_dict.get('role', 'unknown')).upper()}', not "
                f"'{intended_role.upper()}'. Please sign in through the appropriate portal.",
            )
        user_dict["access_token"] = session.access_token
        user_dict["refresh_token"] = session.refresh_token
        return True, user_dict, None

    init_database(db_path)
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        SELECT * FROM profiles
        WHERE lower(email) = ? OR lower(student_id) = ?
        """, (clean_query, clean_query))
        row = cursor.fetchone()

        if not row:
            return False, None, "Invalid institutional credentials."

        user_dict = dict(row)
        expected_pass = str(user_dict.get("password_hash") or "")
        password_matches, is_legacy = _verify_password(password, expected_pass)
        if not password_matches:
            return False, None, "Invalid institutional credentials."

        if is_legacy:
            cursor.execute(
                "UPDATE profiles SET password_hash = ? WHERE id = ?",
                (_hash_password(password), user_dict["id"]),
            )
            conn.commit()

    # Strict server-side role check
    if user_dict["role"] != intended_role:
        return (
            False,
            None,
            f"Access Denied: This account is officially registered as '{user_dict['role'].upper()}', "
            f"not '{intended_role.upper()}'. Please sign in through the appropriate portal."
        )

    user_dict.pop("password_hash", None)
    return True, user_dict, None


def verify_student_access(
    current_user: Dict[str, Any],
    student_id: str,
    db_path: str = DEFAULT_DB_PATH,
) -> bool:
    """Enforces student ownership and staff assignment restrictions."""
    if not current_user:
        return False
    role = current_user.get("role")
    if role == "admin":
        return True
    if role == "student":
        own_student_id = current_user.get("student_id")
        return own_student_id is not None and str(own_student_id) == str(student_id)
    if role == "staff":
        if SUPABASE_SETUP_REQUESTED:
            client = _supabase_client_for_user(current_user)
            response = (
                client.table("students")
                .select("student_id")
                .eq("student_id", student_id)
                .limit(1)
                .execute()
            )
            return bool(response.data)
        assigned = get_student_by_id(student_id, db_path=db_path)
        if assigned:
            mentor_email = str(assigned.get("mentor_email") or "").casefold()
            staff_email = str(current_user.get("email") or "").casefold()
            return bool(staff_email) and mentor_email == staff_email
    return False


# ==============================================================================
# STUDENTS QUERIES & SYNCS
# ==============================================================================
def get_all_students(current_user: Optional[Dict[str, Any]] = None, db_path: str = DEFAULT_DB_PATH) -> pd.DataFrame:
    """
    Retrieves student records filtered server-side by authorization role.
    Students ONLY see their own record. Staff see their assigned mentees.
    """
    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        if not current_user or current_user.get("role") not in {"admin", "staff", "student"}:
            raise PermissionError("Sign in with an authorized account to view student records.")
        client = _supabase_client_for_user(current_user)
        response = (
            client.table("students")
            .select("*")
            .order("student_id")
            .execute()
        )
        return pd.DataFrame(response.data or [])

    with get_db_connection(db_path) as conn:
        if current_user is None:
            df = pd.read_sql_query("SELECT * FROM students ORDER BY student_id ASC", conn)
        elif current_user.get("role") == "student":
            s_id = current_user.get("student_id")
            df = pd.read_sql_query("SELECT * FROM students WHERE student_id = ?", conn, params=(s_id,))
        elif current_user.get("role") == "staff":
            staff_email = current_user.get("email")
            df = pd.read_sql_query(
                "SELECT * FROM students WHERE lower(mentor_email) = lower(?) ORDER BY student_id ASC",
                conn,
                params=(staff_email,),
            )
        elif current_user.get("role") != "admin":
            raise PermissionError("This account is not authorized to view student records.")
        else:
            df = pd.read_sql_query("SELECT * FROM students ORDER BY student_id ASC", conn)
    return df


def get_student_by_id(
    student_id: str,
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    if SUPABASE_SETUP_REQUESTED and not current_user:
        raise PermissionError("Sign in with an authorized account to view student records.")
    if current_user is not None and not verify_student_access(current_user, student_id, db_path):
        raise PermissionError("This account is not authorized to view this student record.")
    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        response = (
            client.table("students")
            .select("*")
            .eq("student_id", student_id)
            .limit(1)
            .execute()
        )
        return dict(response.data[0]) if response.data else None

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM students WHERE student_id = ?", (student_id,))
        row = cursor.fetchone()
        return dict(row) if row else None


def sync_students_to_db(
    df: pd.DataFrame,
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> int:
    """Upserts student records into database without duplicates."""
    if SUPABASE_SETUP_REQUESTED and (current_user is None or current_user.get("role") != "admin"):
        raise PermissionError("Only administrators can import or update student records.")
    init_database(db_path)
    # Supabase integration block disabled for local SQLite mode
    # if SUPABASE_SETUP_REQUESTED:
    #     if not current_user or current_user.get("role") != "admin":
    #         raise PermissionError("Only administrators can import or update student records.")
    existing_df = get_all_students(current_user=current_user, db_path=db_path)
    existing_records = {
        str(record["student_id"]): record
        for record in existing_df.to_dict(orient="records")
    }
    records = []
    defaults = {
            "email": None,
            "department": "Computer Science & Engineering",
            "semester": 5,
            "cgpa": 7.0,
            "marks_percentage": 70.0,
            "backlog_count": 0,
            "attendance_overall": 80.0,
            "lms_assignment_completion": 80.0,
            "lms_login_frequency": 10,
            "extracurricular_score": 50.0,
            "technical_skills_score": 60.0,
            "aptitude_score": 60.0,
            "coding_score": 60.0,
            "mock_interview_score": 60.0,
            "student_feedback_score": 4.0,
            "placement_status": "Eligible",
            "academic_risk": "Low Risk",
            "placement_risk": "Low Risk",
            "risk_level": "Low Risk",
            "segment": "Consistent Performer",
            "mentor_id": None,
            "mentor_name": None,
            "mentor_email": None,
            "faculty_notes": "",
        }
    for _, row in df.iterrows():
        student_id = str(row["student_id"])
        existing = existing_records.get(student_id, {})
        record = {}
        for field, default in defaults.items():
            fallback = existing.get(field, default)
            value = row.get(field, fallback)
            if pd.isna(value):
                value = fallback
            record[field] = value
        record["student_id"] = student_id
        # Safely extract 'name' if present; otherwise retain existing name or empty string
        if "name" in row:
            name_val = row["name"]
        else:
            name_val = existing.get("name", "")
        record["name"] = str(name_val)
        for field in (
            "semester",
            "backlog_count",
            "lms_login_frequency",
        ):
            record[field] = int(record[field])
        for field in (
            "cgpa",
            "marks_percentage",
            "attendance_overall",
            "lms_assignment_completion",
            "extracurricular_score",
            "technical_skills_score",
            "aptitude_score",
            "coding_score",
            "mock_interview_score",
            "student_feedback_score",
        ):
            record[field] = float(record[field])
        for field in (
            "attendance_math",
            "attendance_core",
            "attendance_lab",
            "success_score",
        ):
            fallback = existing.get(field)
            if field in {"attendance_math", "attendance_core", "attendance_lab"}:
                fallback = fallback if fallback is not None else record["attendance_overall"]
            value = row.get(field, fallback)
            record[field] = fallback if pd.isna(value) else float(value)
        record["updated_at"] = datetime.datetime.now(
            datetime.timezone.utc
        ).isoformat()
        records.append(record)
    # If Supabase integration is enabled, upsert via Supabase; otherwise SQLite will handle insertion later
    if records and SUPABASE_SETUP_REQUESTED:
        # Ensure we have a signed‑in user context for Supabase operations
        if not current_user:
            raise PermissionError("Sign in with your institutional account to access this data.")
        client = _supabase_client_for_user(current_user)
        client.table("students").upsert(
            records,
            on_conflict="student_id",
        ).execute()
        # In Supabase mode we are done
        return len(records)
    # In local SQLite mode we fall through to the SQLite insertion logic below
    # Supabase integration disabled for local SQLite mode

    records_synced = 0
    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        for _, row in df.iterrows():
            cursor.execute("""
            INSERT INTO students (
                student_id, name, email, department, semester, cgpa, marks_percentage,
                backlog_count, attendance_overall, attendance_math, attendance_core, attendance_lab,
                lms_assignment_completion, lms_login_frequency, extracurricular_score,
                technical_skills_score, aptitude_score, coding_score, mock_interview_score,
                student_feedback_score, placement_status, success_score, academic_risk,
                placement_risk, risk_level, segment, mentor_id, mentor_name, mentor_email,
                faculty_notes, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(student_id) DO UPDATE SET
                name=excluded.name,
                email=COALESCE(excluded.email, students.email),
                department=excluded.department,
                semester=excluded.semester,
                cgpa=excluded.cgpa,
                marks_percentage=excluded.marks_percentage,
                backlog_count=excluded.backlog_count,
                attendance_overall=excluded.attendance_overall,
                lms_assignment_completion=excluded.lms_assignment_completion,
                lms_login_frequency=excluded.lms_login_frequency,
                extracurricular_score=excluded.extracurricular_score,
                technical_skills_score=excluded.technical_skills_score,
                aptitude_score=excluded.aptitude_score,
                coding_score=excluded.coding_score,
                mock_interview_score=excluded.mock_interview_score,
                student_feedback_score=excluded.student_feedback_score,
                placement_status=excluded.placement_status,
                success_score=excluded.success_score,
                academic_risk=excluded.academic_risk,
                placement_risk=excluded.placement_risk,
                risk_level=excluded.risk_level,
                segment=excluded.segment,
                mentor_id=COALESCE(excluded.mentor_id, students.mentor_id),
                mentor_name=COALESCE(excluded.mentor_name, students.mentor_name),
                mentor_email=COALESCE(excluded.mentor_email, students.mentor_email),
                faculty_notes=COALESCE(excluded.faculty_notes, students.faculty_notes),
                updated_at=CURRENT_TIMESTAMP
            """, (
                str(row.get("student_id")),
                str(row.get("name")),
                str(row.get("email", f"{str(row.get('student_id')).lower()}@student.campus.edu")),
                str(row.get("department", "Computer Science & Engineering")),
                int(row.get("semester", 5)),
                float(row.get("cgpa", 7.0)),
                float(row.get("marks_percentage", 70.0)),
                int(row.get("backlog_count", 0)),
                float(row.get("attendance_overall", 80.0)),
                float(row.get("attendance_math", row.get("attendance_overall", 80.0))),
                float(row.get("attendance_core", row.get("attendance_overall", 80.0))),
                float(row.get("attendance_lab", row.get("attendance_overall", 80.0))),
                float(row.get("lms_assignment_completion", 80.0)),
                int(row.get("lms_login_frequency", 10)),
                float(row.get("extracurricular_score", 50.0)),
                float(row.get("technical_skills_score", 60.0)),
                float(row.get("aptitude_score", 60.0)),
                float(row.get("coding_score", 60.0)),
                float(row.get("mock_interview_score", 60.0)),
                float(row.get("student_feedback_score", 4.0)),
                str(row.get("placement_status", "Eligible")),
                float(row.get("success_score", 0.0)) if pd.notna(row.get("success_score")) else None,
                str(row.get("academic_risk", "Low Risk")),
                str(row.get("placement_risk", "Low Risk")),
                str(row.get("risk_level", "Low Risk")),
                str(row.get("segment", "Consistent Performer")),
                str(row.get("mentor_id", "staff_sharma_01")),
                str(row.get("mentor_name", "Dr. Ananya Sharma")),
                str(row.get("mentor_email", "dr.sharma@campus.edu")),
                str(row.get("faculty_notes", "")),
            ))
            records_synced += 1
        conn.commit()
    return records_synced


def assign_mentor_to_student(
    student_id: str,
    mentor_name: str,
    mentor_email: str,
    mentor_id: str = "staff_sharma_01",
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> bool:
    if not current_user or current_user.get("role") != "admin":
        raise PermissionError("Only administrators can assign student mentors.")
    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        response = (
            client.table("students")
            .update(
                {
                    "mentor_name": mentor_name,
                    "mentor_email": mentor_email,
                    "mentor_id": mentor_id,
                    "updated_at": datetime.datetime.now(
                        datetime.timezone.utc
                    ).isoformat(),
                }
            )
            .eq("student_id", student_id)
            .execute()
        )
        return bool(response.data)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        UPDATE students
        SET mentor_name = ?, mentor_email = ?, mentor_id = ?, updated_at = CURRENT_TIMESTAMP
        WHERE student_id = ?
        """, (mentor_name, mentor_email, mentor_id, student_id))
        conn.commit()
        return cursor.rowcount > 0


# ==============================================================================
# INTERVENTIONS CRUD
# ==============================================================================
def add_intervention(
    student_id: str,
    student_name: str,
    department: str,
    intervention_type: str,
    description: str,
    owner_name: str,
    due_date: str,
    priority: str = "High",
    status: str = "Pending",
    goal: str = "",
    owner_email: str = "dr.sharma@campus.edu",
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> str:
    if not current_user or current_user.get("role") not in {"admin", "staff"}:
        raise PermissionError("Only authorized staff can create interventions.")
    student = get_student_by_id(
        student_id,
        db_path=db_path,
        current_user=current_user,
    )
    if not student or not verify_student_access(current_user, student_id, db_path):
        raise PermissionError("This account is not assigned to the selected student.")
    student_name = student["name"]
    department = student["department"]
    owner_name = str(current_user.get("name") or owner_name)
    owner_email = str(current_user.get("email") or owner_email)
    init_database(db_path)
    int_id = f"int_{uuid.uuid4().hex}"
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        client.table("interventions").insert(
            {
                "id": int_id,
                "student_id": student_id,
                "student_name": student_name,
                "department": department,
                "intervention_type": intervention_type,
                "priority": priority,
                "owner_name": owner_name,
                "owner_email": owner_email,
                "due_date": due_date,
                "status": status,
                "description": description,
                "goal": goal,
            }
        ).execute()
        return int_id

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO interventions (
            id, student_id, student_name, department, intervention_type, priority,
            owner_name, owner_email, due_date, status, description, goal
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            int_id, student_id, student_name, department, intervention_type, priority,
            owner_name, owner_email, due_date, status, description, goal
        ))
        conn.commit()
    return int_id


def get_interventions(
    current_user: Optional[Dict[str, Any]] = None,
    student_id: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
) -> pd.DataFrame:
    if current_user is not None:
        role = current_user.get("role")
        if role not in {"admin", "staff", "student"}:
            raise PermissionError("This account is not authorized to view interventions.")
        if student_id and role != "admin" and not verify_student_access(current_user, student_id, db_path):
            raise PermissionError("This account is not authorized to view this student's interventions.")

    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        if not current_user or current_user.get("role") not in {"admin", "staff", "student"}:
            raise PermissionError("Sign in with an authorized account to view interventions.")
        if student_id and current_user.get("role") != "admin" and not verify_student_access(
            current_user, student_id, db_path
        ):
            raise PermissionError("This account is not authorized to view this student's interventions.")
        client = _supabase_client_for_user(current_user)
        query = client.table("interventions").select("*")
        if student_id:
            query = query.eq("student_id", student_id)
        response = query.order("created_at", desc=True).execute()
        return pd.DataFrame(response.data or [])

    with get_db_connection(db_path) as conn:
        if current_user and current_user.get("role") == "student":
            own_student_id = str(current_user.get("student_id") or "")
            if student_id and str(student_id) != own_student_id:
                raise PermissionError("Students can only view their own interventions.")
            df = pd.read_sql_query("SELECT * FROM interventions WHERE student_id = ? ORDER BY created_at DESC", conn, params=(own_student_id,))
        elif current_user and current_user.get("role") == "staff":
            staff_email = current_user.get("email")
            if student_id:
                df = pd.read_sql_query(
                    "SELECT * FROM interventions WHERE student_id = ? AND student_id IN "
                    "(SELECT student_id FROM students WHERE lower(mentor_email) = lower(?)) "
                    "ORDER BY created_at DESC",
                    conn,
                    params=(student_id, staff_email),
                )
            else:
                df = pd.read_sql_query(
                    "SELECT * FROM interventions WHERE student_id IN "
                    "(SELECT student_id FROM students WHERE lower(mentor_email) = lower(?)) "
                    "ORDER BY created_at DESC",
                    conn,
                    params=(staff_email,),
                )
        elif student_id:
            df = pd.read_sql_query("SELECT * FROM interventions WHERE student_id = ? ORDER BY created_at DESC", conn, params=(student_id,))
        else:
            df = pd.read_sql_query("SELECT * FROM interventions ORDER BY created_at DESC", conn)
    return df


def update_intervention_status(
    int_id: str,
    status: str,
    outcome_measured: Optional[str] = None,
    notes: Optional[str] = None,
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> bool:
    if not current_user or current_user.get("role") not in {"admin", "staff"}:
        raise PermissionError("Only authorized staff can update interventions.")
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        lookup = (
            client.table("interventions")
            .select("id,student_id")
            .eq("id", int_id)
            .limit(1)
            .execute()
        )
        if not lookup.data:
            return False
        student_id = str(lookup.data[0]["student_id"])
        if current_user.get("role") != "admin" and not verify_student_access(
            current_user, student_id, db_path
        ):
            raise PermissionError("This account is not assigned to the intervention's student.")
        update_values = {"status": status}
        if outcome_measured is not None:
            update_values["outcome_measured"] = outcome_measured
        if notes is not None:
            update_values["notes"] = notes
        result = (
            client.table("interventions")
            .update(update_values)
            .eq("id", int_id)
            .execute()
        )
        return bool(result.data)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM interventions WHERE id = ?", (int_id,))
        intervention = cursor.fetchone()
        if not intervention:
            return False
        if current_user.get("role") != "admin" and not verify_student_access(
            current_user, intervention["student_id"], db_path
        ):
            raise PermissionError("This account is not assigned to the intervention's student.")
        cursor.execute("""
        UPDATE interventions
        SET status = ?,
            outcome_measured = COALESCE(?, outcome_measured),
            notes = COALESCE(?, notes),
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """, (status, outcome_measured, notes, int_id))
        conn.commit()
        return cursor.rowcount > 0


# ==============================================================================
# ACTION PLAN TASKS (FOR STUDENTS)
# ==============================================================================
def get_action_tasks_for_student(
    student_id: str,
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> List[Dict[str, Any]]:
    if not current_user or not verify_student_access(current_user, student_id, db_path):
        raise PermissionError("This account is not authorized to view this student's action plan.")
    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        result = (
            client.table("action_plan_tasks")
            .select("*")
            .eq("student_id", student_id)
            .order("created_at", desc=True)
            .execute()
        )
        rows = result.data or []
        if not rows:
            student = get_student_by_id(
                student_id,
                db_path=db_path,
                current_user=current_user,
            )
            if student:
                tasks = []
                if float(student.get("attendance_overall", 100)) < 75.0:
                    tasks.append({
                        "id": f"tsk_att_{student_id}",
                        "student_id": student_id,
                        "title": "Submit Attendance Medical Condonation Form",
                        "description": "Meet HOD and submit official leave documentation to review attendance requirements.",
                        "category": "Attendance",
                        "priority": "High",
                        "effort_hours": 2.0,
                        "due_date": "In 3 days",
                        "completed": False,
                        "reason": "Attendance below 75% cutoff",
                    })
                if int(student.get("backlog_count", 0)) > 0:
                    tasks.append({
                        "id": f"tsk_bck_{student_id}",
                        "student_id": student_id,
                        "title": f"Register for Backlog Remedial Tutoring ({student.get('backlog_count')} active)",
                        "description": "Attend remedial classes and work through previous exam papers.",
                        "category": "Academic",
                        "priority": "High",
                        "effort_hours": 10.0,
                        "due_date": "In 7 days",
                        "completed": False,
                        "reason": "Active backlogs affect academic progress",
                    })
                if float(student.get("coding_score", 50)) < 65.0:
                    tasks.append({
                        "id": f"tsk_cod_{student_id}",
                        "student_id": student_id,
                        "title": "Solve 15 coding practice problems",
                        "description": "Practice core data structures and algorithms and track completed problems.",
                        "category": "Placement",
                        "priority": "High",
                        "effort_hours": 8.0,
                        "due_date": "In 10 days",
                        "completed": False,
                        "reason": "Coding assessment benchmark",
                    })
                tasks.append({
                    "id": f"tsk_res_{student_id}",
                    "student_id": student_id,
                    "title": "Optimize Technical Resume with ATS Keywords",
                    "description": "Update project descriptions with measurable outcomes.",
                    "category": "Placement",
                    "priority": "Medium",
                    "effort_hours": 3.0,
                    "due_date": "In 2 weeks",
                    "completed": False,
                    "reason": "Placement drive readiness",
                })
                client.table("action_plan_tasks").upsert(
                    tasks,
                    on_conflict="id",
                    ignore_duplicates=True,
                ).execute()
                result = (
                    client.table("action_plan_tasks")
                    .select("*")
                    .eq("student_id", student_id)
                    .order("created_at", desc=True)
                    .execute()
                )
                rows = result.data or []
        return [dict(row) for row in rows]

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM action_plan_tasks WHERE student_id = ? ORDER BY created_at DESC", (student_id,))
        rows = cursor.fetchall()

    if not rows:
        # Generate personalized tasks based on student metrics
        student = get_student_by_id(student_id, db_path)
        if student:
            tasks = []
            if float(student.get("attendance_overall", 100)) < 75.0:
                tasks.append((f"tsk_att_{student_id}", student_id, "Submit Attendance Medical Condonation Form", "Meet HOD and submit official leaves documentation to avoid semester exam debarment.", "Attendance", "High", 2.0, "In 3 days", 0, "Attendance below 75% cutoff"))
            if int(student.get("backlog_count", 0)) > 0:
                tasks.append((f"tsk_bck_{student_id}", student_id, f"Register for Backlog Remedial Tutoring ({student.get('backlog_count')} active)", "Attend weekend remedial classes and solve previous 3 years papers.", "Academic", "High", 10.0, "In 7 days", 0, "Active backlogs drag down academic index"))
            if float(student.get("coding_score", 50)) < 65.0:
                tasks.append((f"tsk_cod_{student_id}", student_id, "Solve 15 LeetCode / HackerRank DSA Problems", "Practice Two Pointers, Sliding Window, and Hash Maps.", "Placement", "High", 8.0, "In 10 days", 0, "Coding assessment benchmark"))
            tasks.append((f"tsk_res_{student_id}", student_id, "Optimize Technical Resume with ATS Keywords", "Update project descriptions with quantified business impact.", "Placement", "Medium", 3.0, "In 2 weeks", 1, "Placement drive readiness"))

            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                for t in tasks:
                    cursor.execute("""
                    INSERT OR IGNORE INTO action_plan_tasks (id, student_id, title, description, category, priority, effort_hours, due_date, completed, reason)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, t)
                conn.commit()

            with get_db_connection(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM action_plan_tasks WHERE student_id = ?", (student_id,))
                rows = cursor.fetchall()

    return [dict(r) for r in rows]


def toggle_action_task(
    task_id: str,
    completed: bool,
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> bool:
    if not current_user or current_user.get("role") not in {"admin", "student"}:
        raise PermissionError("This account is not authorized to update action plan tasks.")
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        task_response = (
            client.table("action_plan_tasks")
            .select("student_id")
            .eq("id", task_id)
            .limit(1)
            .execute()
        )
        if not task_response.data:
            return False
        if not verify_student_access(current_user, task_response.data[0]["student_id"], db_path):
            raise PermissionError("This account is not authorized to update this student's action plan.")
        result = (
            client.table("action_plan_tasks")
            .update({"completed": completed})
            .eq("id", task_id)
            .execute()
        )
        return bool(result.data)

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT student_id FROM action_plan_tasks WHERE id = ?", (task_id,))
        task = cursor.fetchone()
        if not task:
            return False
        if not verify_student_access(current_user, task["student_id"], db_path):
            raise PermissionError("This account is not authorized to update this student's action plan.")
        cursor.execute("UPDATE action_plan_tasks SET completed = ? WHERE id = ?", (1 if completed else 0, task_id))
        conn.commit()
        return cursor.rowcount > 0


# ==============================================================================
# AUDIT LOGGING FOR CSV IMPORTS
# ==============================================================================
def log_import_job(
    dataset_type: str,
    filename: str,
    total_rows: int,
    valid_rows: int,
    invalid_rows: int,
    inserted_rows: int,
    updated_rows: int,
    status: str,
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> str:
    if not current_user or current_user.get("role") != "admin":
        raise PermissionError("Only administrators can create data import audit entries.")
    job_id = f"imp_{uuid.uuid4().hex}"
    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        client.table("data_import_jobs").insert(
            {
                "id": job_id,
                "dataset_type": dataset_type,
                "filename": filename,
                "total_rows": total_rows,
                "valid_rows": valid_rows,
                "invalid_rows": invalid_rows,
                "inserted_rows": inserted_rows,
                "updated_rows": updated_rows,
                "status": status,
            }
        ).execute()
        return job_id

    with get_db_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("""
        INSERT INTO data_import_jobs (
            id, dataset_type, filename, total_rows, valid_rows, invalid_rows, inserted_rows, updated_rows, status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (job_id, dataset_type, filename, total_rows, valid_rows, invalid_rows, inserted_rows, updated_rows, status))
        conn.commit()
    return job_id


def get_import_history(
    db_path: str = DEFAULT_DB_PATH,
    current_user: Optional[Dict[str, Any]] = None,
) -> pd.DataFrame:
    if not current_user or current_user.get("role") != "admin":
        raise PermissionError("Only administrators can view data import history.")
    init_database(db_path)
    if SUPABASE_SETUP_REQUESTED:
        client = _supabase_client_for_user(current_user)
        response = (
            client.table("data_import_jobs")
            .select("*")
            .order("created_at", desc=True)
            .limit(20)
            .execute()
        )
        return pd.DataFrame(response.data or [])
    with get_db_connection(db_path) as conn:
        df = pd.read_sql_query("SELECT * FROM data_import_jobs ORDER BY created_at DESC LIMIT 20", conn)
    return df
