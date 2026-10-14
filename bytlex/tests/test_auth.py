"""
Pytest Test Suite: Authentication, Role Verification, and Server-Side Authorization
"""

import sqlite3
from types import SimpleNamespace

import pandas as pd
import pytest
import src.database as database
from src.database import (
    authenticate_user,
    add_intervention,
    get_all_students,
    get_action_tasks_for_student,
    get_interventions,
    get_student_by_id,
    init_database,
    sync_students_to_db,
    toggle_action_task,
    update_intervention_status,
    verify_student_access,
)


@pytest.fixture
def db_path(tmp_path):
    path = str(tmp_path / "campusiq-test.db")
    init_database(path)
    return path


def _sync_students(db_path):
    sync_students_to_db(
        pd.DataFrame(
            [
                {
                    "student_id": "ASSIGNED_001",
                    "name": "Assigned Student",
                    "department": "Computer Science & Engineering",
                    "semester": 5,
                    "mentor_email": "dr.sharma@campus.edu",
                },
                {
                    "student_id": "UNASSIGNED_002",
                    "name": "Other Mentor Student",
                    "department": "Computer Science & Engineering",
                    "semester": 5,
                    "mentor_email": "prof.rajesh@campus.edu",
                },
            ]
        ),
        db_path=db_path,
    )


def test_admin_successful_login(db_path):
    ok, user, err = authenticate_user("admin@campus.edu", "AdminPass2026!", "admin", db_path)
    assert ok is True
    assert user is not None
    assert user["role"] == "admin"
    assert "password_hash" not in user
    assert err is None


def test_staff_successful_login(db_path):
    ok, user, err = authenticate_user("dr.sharma@campus.edu", "StaffPass2026!", "staff", db_path)
    assert ok is True
    assert user is not None
    assert user["role"] == "staff"


def test_student_successful_login_by_id(db_path):
    ok, user, err = authenticate_user("STU2021004", "StudentPass2026!", "student", db_path)
    assert ok is True
    assert user is not None
    assert user["role"] == "student"
    assert user["student_id"] == "STU2021004"


def test_role_mismatch_rejected(db_path):
    # Admin attempting to sign in through student portal
    ok, user, err = authenticate_user("admin@campus.edu", "AdminPass2026!", "student", db_path)
    assert ok is False
    assert user is None
    assert "Access Denied" in err
    assert "ADMIN" in err


def test_passwords_of_any_length_are_still_verified(db_path):
    ok, user, err = authenticate_user("admin@campus.edu", "abcd", "admin", db_path)
    assert ok is False
    assert user is None
    assert err == "Invalid institutional credentials."


def test_legacy_plaintext_password_is_upgraded_on_database_initialization(db_path):
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            "UPDATE profiles SET password_hash = ? WHERE email = ?",
            ("LegacyPass2026!", "admin@campus.edu"),
        )

    init_database(db_path)

    with sqlite3.connect(db_path) as conn:
        stored_hash = conn.execute(
            "SELECT password_hash FROM profiles WHERE email = ?",
            ("admin@campus.edu",),
        ).fetchone()[0]
    assert stored_hash.startswith("pbkdf2_sha256$")
    assert stored_hash != "LegacyPass2026!"

    ok, user, err = authenticate_user("admin@campus.edu", "LegacyPass2026!", "admin", db_path)
    assert ok is True
    assert user is not None
    assert err is None


def test_supabase_configuration_never_falls_back_to_sqlite(tmp_path, monkeypatch):
    monkeypatch.setattr(database, "SUPABASE_SETUP_REQUESTED", True)
    monkeypatch.setattr(database, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(database, "SUPABASE_ANON_KEY", "")
    monkeypatch.setattr(database, "_legacy_supabase_key", "")
    with pytest.raises(RuntimeError, match="SUPABASE_ANON_KEY"):
        database.init_database(str(tmp_path / "must-not-be-created.db"))
    assert not (tmp_path / "must-not-be-created.db").exists()


def test_supabase_login_uses_auth_profile_role_and_keeps_session_server_side(
    tmp_path, monkeypatch
):
    profile = {
        "id": "auth-user-1",
        "email": "student@campus.edu",
        "name": "Sample Student",
        "role": "student",
        "student_id": "STU1001",
    }

    class FakeQuery:
        def select(self, _columns):
            return self

        def eq(self, _field, _value):
            return self

        def limit(self, _count):
            return self

        def execute(self):
            return SimpleNamespace(data=[profile])

    class FakeAuth:
        signed_out = False

        def sign_in_with_password(self, credentials):
            assert credentials == {
                "email": "student@campus.edu",
                "password": "example-password",
            }
            return SimpleNamespace(
                session=SimpleNamespace(
                    access_token="access-token",
                    refresh_token="refresh-token",
                ),
                user=SimpleNamespace(id="auth-user-1", email="student@campus.edu"),
            )

        def sign_out(self):
            self.signed_out = True

    class FakeClient:
        def __init__(self):
            self.auth = FakeAuth()

        def table(self, _table_name):
            return FakeQuery()

    fake_client = FakeClient()
    monkeypatch.setattr(database, "SUPABASE_SETUP_REQUESTED", True)
    monkeypatch.setattr(database, "_validate_supabase_configuration", lambda: None)
    monkeypatch.setattr(database, "_new_supabase_client", lambda: fake_client)

    ok, user, error = authenticate_user(
        "STUDENT@CAMPUS.EDU",
        "example-password",
        "student",
        str(tmp_path / "unused.db"),
    )

    assert ok is True
    assert error is None
    assert user is not None
    assert user["role"] == "student"
    assert user["student_id"] == "STU1001"
    assert user["access_token"] == "access-token"
    assert user["refresh_token"] == "refresh-token"
    assert not (tmp_path / "unused.db").exists()

    ok, denied_user, error = authenticate_user(
        "student@campus.edu",
        "example-password",
        "admin",
        str(tmp_path / "unused.db"),
    )
    assert ok is False
    assert denied_user is None
    assert "Access Denied" in error
    assert fake_client.auth.signed_out is True


def test_service_role_keys_are_detected():
    assert database._is_service_role_key("sb_secret_do-not-use")
    assert database._is_service_role_key(
        "e30.eyJyb2xlIjoic2VydmljZV9yb2xlIn0.sig"
    )
    assert not database._is_service_role_key(
        "e30.eyJyb2xlIjoiYW5vbiJ9.sig"
    )


def test_supabase_configuration_rejects_service_role_key(monkeypatch):
    monkeypatch.setattr(database, "SUPABASE_SETUP_REQUESTED", True)
    monkeypatch.setattr(database, "SUPABASE_URL", "https://project.supabase.co")
    monkeypatch.setattr(database, "SUPABASE_ANON_KEY", "sb_secret_do-not-use")
    monkeypatch.setattr(database, "_legacy_supabase_key", "")
    with pytest.raises(RuntimeError, match="service_role/secret key"):
        database._validate_supabase_configuration()


def test_supabase_student_queries_require_an_authenticated_user(tmp_path, monkeypatch):
    class FakeQuery:
        def select(self, _columns):
            return self

        def order(self, _field):
            return self

        def execute(self):
            return SimpleNamespace(
                data=[
                    {
                        "student_id": "STU1001",
                        "name": "Sample Student",
                    }
                ]
            )

    class FakeClient:
        def table(self, table_name):
            assert table_name == "students"
            return FakeQuery()

    monkeypatch.setattr(database, "SUPABASE_SETUP_REQUESTED", True)
    monkeypatch.setattr(database, "_validate_supabase_configuration", lambda: None)
    monkeypatch.setattr(
        database,
        "_supabase_client_for_user",
        lambda _user: FakeClient(),
    )

    with pytest.raises(PermissionError):
        database.get_all_students(db_path=str(tmp_path / "unused.db"))
    students = database.get_all_students(
        current_user={
            "role": "admin",
            "access_token": "access-token",
            "refresh_token": "refresh-token",
        },
        db_path=str(tmp_path / "unused.db"),
    )
    assert students["student_id"].tolist() == ["STU1001"]
    assert not (tmp_path / "unused.db").exists()


def test_student_access_control(db_path):
    _sync_students(db_path)
    student_user = {
        "id": "stu_karan",
        "email": "karan.pillai@student.campus.edu",
        "role": "student",
        "student_id": "ASSIGNED_001",
    }

    # Student can access their own record
    assert verify_student_access(student_user, "ASSIGNED_001", db_path) is True

    # Student CANNOT access another student's record
    assert verify_student_access(student_user, "UNASSIGNED_002", db_path) is False


def test_admin_access_control(db_path):
    admin_user = {"id": "admin_1", "email": "admin@campus.edu", "role": "admin"}
    # Admin can access any record
    assert verify_student_access(admin_user, "ASSIGNED_001", db_path) is True
    assert verify_student_access(admin_user, "UNASSIGNED_002", db_path) is True


def test_staff_can_only_view_explicitly_assigned_students(db_path):
    _sync_students(db_path)
    staff_user = {
        "id": "staff_sharma_01",
        "email": "dr.sharma@campus.edu",
        "role": "staff",
        "department": "Computer Science & Engineering",
    }

    visible = get_all_students(staff_user, db_path)
    assert visible["student_id"].tolist() == ["ASSIGNED_001"]
    assert verify_student_access(staff_user, "ASSIGNED_001", db_path) is True
    assert verify_student_access(staff_user, "UNASSIGNED_002", db_path) is False

    with pytest.raises(PermissionError):
        get_student_by_id("UNASSIGNED_002", db_path, current_user=staff_user)
    with pytest.raises(PermissionError):
        get_all_students({}, db_path)


def test_staff_intervention_access_is_limited_to_assigned_students(db_path):
    _sync_students(db_path)
    staff_user = {
        "id": "staff_sharma_01",
        "email": "dr.sharma@campus.edu",
        "name": "Dr. Ananya Sharma",
        "role": "staff",
    }
    admin_user = {"id": "user_admin_01", "email": "admin@campus.edu", "role": "admin"}
    assigned_case = add_intervention(
        "ASSIGNED_001",
        "Ignored Client Name",
        "Ignored Department",
        "Academic Support",
        "Follow up",
        "Untrusted Owner",
        "2026-12-01",
        current_user=staff_user,
        db_path=db_path,
    )
    unassigned_case = add_intervention(
        "UNASSIGNED_002",
        "Other Student",
        "Computer Science & Engineering",
        "Academic Support",
        "Admin follow up",
        "Administrator",
        "2026-12-01",
        current_user=admin_user,
        db_path=db_path,
    )

    visible = get_interventions(current_user=staff_user, db_path=db_path)
    assert visible["id"].tolist() == [assigned_case]
    assert visible.iloc[0]["student_name"] == "Assigned Student"
    with pytest.raises(PermissionError):
        update_intervention_status(
            unassigned_case,
            "Completed",
            current_user=staff_user,
            db_path=db_path,
        )
    with pytest.raises(PermissionError):
        add_intervention(
            "UNASSIGNED_002",
            "Other Student",
            "Computer Science & Engineering",
            "Academic Support",
            "Unauthorized follow up",
            "Dr. Ananya Sharma",
            "2026-12-01",
            current_user=staff_user,
            db_path=db_path,
        )


def test_students_cannot_read_or_update_another_students_tasks(db_path):
    _sync_students(db_path)
    student_user = {
        "id": "student_1",
        "email": "student@example.edu",
        "role": "student",
        "student_id": "ASSIGNED_001",
    }
    with sqlite3.connect(db_path) as conn:
        conn.execute(
            """
            INSERT INTO action_plan_tasks
                (id, student_id, title, category, priority)
            VALUES (?, ?, ?, ?, ?)
            """,
            ("other-task", "UNASSIGNED_002", "Private task", "Academic", "High"),
        )

    with pytest.raises(PermissionError):
        get_action_tasks_for_student(
            "UNASSIGNED_002", db_path=db_path, current_user=student_user
        )
    with pytest.raises(PermissionError):
        toggle_action_task(
            "other-task", True, db_path=db_path, current_user=student_user
        )
