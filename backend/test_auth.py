"""
Test suite for Phase 3: Authentication.
Covers registration, login, JWT validation, role-based protection, error responses,
and temporary data cleanup.
"""

import sys
from app import create_app, db
from models import User, MenteeProfile, MentorProfile
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 60)
    print("STARTING AUTHENTICATION SYSTEM TESTS")
    print("=" * 60)

    test_mentee_email = "test_mentee_auth_suite@example.com"
    test_mentor_email = "test_mentor_auth_suite@example.com"

    # Pre-cleanup in case previous runs left artifacts
    with app.app_context():
        old_users = User.query.filter(User.email.in_([test_mentee_email, test_mentor_email])).all()
        for u in old_users:
            MenteeProfile.query.filter_by(user_id=u.id).delete()
            MentorProfile.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()

    all_passed = True

    # -------------------------------------------------------------
    # 0. Health Check
    # -------------------------------------------------------------
    print("\n[TEST 0] Testing GET /api/health...")
    resp = client.get('/api/health')
    assert resp.status_code == 200, f"Health check failed with status {resp.status_code}"
    data = resp.get_json()
    assert data.get("status") == "success", "Health check response invalid"
    print("  -> PASSED: /api/health returned 200 OK")

    # -------------------------------------------------------------
    # A. Successful mentee registration
    # -------------------------------------------------------------
    print("\n[TEST A] Testing Successful Mentee Registration...")
    reg_mentee_payload = {
        "name": "Jane Mentee",
        "email": test_mentee_email,
        "password": "SecurePassword123!",
        "role": "mentee"
    }
    resp = client.post('/api/auth/register', json=reg_mentee_payload)
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    assert data.get("status") == "success"
    assert "user" in data
    assert data["user"]["email"] == test_mentee_email
    assert data["user"]["role"] == "mentee"
    assert "password_hash" not in data["user"], "Security issue: password_hash exposed in response"
    print("  -> PASSED: Mentee registered successfully without exposing password_hash")

    # -------------------------------------------------------------
    # B. Successful mentor registration
    # -------------------------------------------------------------
    print("\n[TEST B] Testing Successful Mentor Registration...")
    reg_mentor_payload = {
        "name": "John Mentor",
        "email": test_mentor_email,
        "password": "MentorPassword456!",
        "role": "mentor"
    }
    resp = client.post('/api/auth/register', json=reg_mentor_payload)
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    assert data.get("status") == "success"
    assert "user" in data
    assert data["user"]["email"] == test_mentor_email
    assert data["user"]["role"] == "mentor"
    assert "password_hash" not in data["user"], "Security issue: password_hash exposed in response"
    print("  -> PASSED: Mentor registered successfully without exposing password_hash")

    # -------------------------------------------------------------
    # C. Duplicate email registration rejected
    # -------------------------------------------------------------
    print("\n[TEST C] Testing Duplicate Email Registration Rejection...")
    dup_payload = {
        "name": "Another Jane",
        "email": test_mentee_email.upper(),  # test case normalization as well
        "password": "AnotherPassword789!",
        "role": "mentee"
    }
    resp = client.post('/api/auth/register', json=dup_payload)
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 409, f"Expected 409 Conflict, got {resp.status_code}"
    assert data.get("status") == "error"
    print("  -> PASSED: Duplicate registration correctly rejected with 409 Conflict")

    # -------------------------------------------------------------
    # D. Invalid role rejected
    # -------------------------------------------------------------
    print("\n[TEST D] Testing Invalid Role Registration Rejection...")
    invalid_role_payload = {
        "name": "Invalid User",
        "email": "invalid_role_user@example.com",
        "password": "Password123!",
        "role": "superadmin"
    }
    resp = client.post('/api/auth/register', json=invalid_role_payload)
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 400, f"Expected 400 Bad Request, got {resp.status_code}"
    assert data.get("status") == "error"
    print("  -> PASSED: Invalid role correctly rejected with 400 Bad Request")

    # -------------------------------------------------------------
    # E. Successful login
    # -------------------------------------------------------------
    print("\n[TEST E] Testing Successful Login...")
    login_mentee_payload = {
        "email": test_mentee_email.upper(),  # test email case insensitivity
        "password": "SecurePassword123!"
    }
    resp = client.post('/api/auth/login', json=login_mentee_payload)
    mentee_login_data = resp.get_json()
    print(f"  Mentee Login Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert mentee_login_data.get("status") == "success"
    assert "access_token" in mentee_login_data
    assert "password_hash" not in mentee_login_data["user"]
    mentee_token = mentee_login_data["access_token"]

    login_mentor_payload = {
        "email": test_mentor_email,
        "password": "MentorPassword456!"
    }
    resp = client.post('/api/auth/login', json=login_mentor_payload)
    mentor_login_data = resp.get_json()
    print(f"  Mentor Login Status: {resp.status_code}")
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert mentor_login_data.get("status") == "success"
    assert "access_token" in mentor_login_data
    mentor_token = mentor_login_data["access_token"]
    print("  -> PASSED: Successful logins returned valid JWT access tokens")

    # -------------------------------------------------------------
    # F. Wrong password rejected
    # -------------------------------------------------------------
    print("\n[TEST F] Testing Wrong Password Login Rejection...")
    wrong_pass_payload = {
        "email": test_mentee_email,
        "password": "WrongPasswordHere!"
    }
    resp = client.post('/api/auth/login', json=wrong_pass_payload)
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
    assert data.get("status") == "error"
    print("  -> PASSED: Incorrect password rejected with 401 Unauthorized")

    # -------------------------------------------------------------
    # G. Protected test endpoint without token rejected
    # -------------------------------------------------------------
    print("\n[TEST G] Testing Protected Endpoint Without Token Rejection...")
    resp = client.get('/api/auth/me')
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 401, f"Expected 401 Unauthorized, got {resp.status_code}"
    assert data.get("status") == "error"
    print("  -> PASSED: Access without token correctly rejected with 401")

    # -------------------------------------------------------------
    # H. Protected test endpoint with valid token succeeds
    # -------------------------------------------------------------
    print("\n[TEST H] Testing Protected Endpoint With Valid Token...")
    headers = {"Authorization": f"Bearer {mentee_token}"}
    resp = client.get('/api/auth/me', headers=headers)
    data = resp.get_json()
    print(f"  Status: {resp.status_code}, Response: {data}")
    assert resp.status_code == 200, f"Expected 200 OK, got {resp.status_code}"
    assert data.get("status") == "success"
    assert data["user"]["email"] == test_mentee_email
    assert data["user"]["role"] == "mentee"
    print("  -> PASSED: Valid token authenticated successfully on /api/auth/me")

    # -------------------------------------------------------------
    # I. Mentor-only route rejects mentee and accepts mentor
    # -------------------------------------------------------------
    print("\n[TEST I] Testing Mentor-Only Route Protection...")
    # 1. Mentee attempts mentor route -> should fail (403)
    resp_mentee_blocked = client.get('/api/auth/mentor-only-test', headers={"Authorization": f"Bearer {mentee_token}"})
    print(f"  Mentee accessing mentor-only route - Status: {resp_mentee_blocked.status_code}, Response: {resp_mentee_blocked.get_json()}")
    assert resp_mentee_blocked.status_code == 403, f"Expected 403 Forbidden, got {resp_mentee_blocked.status_code}"

    # 2. Mentor attempts mentor route -> should succeed (200)
    resp_mentor_allowed = client.get('/api/auth/mentor-only-test', headers={"Authorization": f"Bearer {mentor_token}"})
    print(f"  Mentor accessing mentor-only route - Status: {resp_mentor_allowed.status_code}, Response: {resp_mentor_allowed.get_json()}")
    assert resp_mentor_allowed.status_code == 200, f"Expected 200 OK, got {resp_mentor_allowed.status_code}"
    print("  -> PASSED: Mentor-only route correctly rejects mentee (403) and allows mentor (200)")

    # -------------------------------------------------------------
    # J. Mentee-only route rejects mentor and accepts mentee
    # -------------------------------------------------------------
    print("\n[TEST J] Testing Mentee-Only Route Protection...")
    # 1. Mentor attempts mentee route -> should fail (403)
    resp_mentor_blocked = client.get('/api/auth/mentee-only-test', headers={"Authorization": f"Bearer {mentor_token}"})
    print(f"  Mentor accessing mentee-only route - Status: {resp_mentor_blocked.status_code}, Response: {resp_mentor_blocked.get_json()}")
    assert resp_mentor_blocked.status_code == 403, f"Expected 403 Forbidden, got {resp_mentor_blocked.status_code}"

    # 2. Mentee attempts mentee route -> should succeed (200)
    resp_mentee_allowed = client.get('/api/auth/mentee-only-test', headers={"Authorization": f"Bearer {mentee_token}"})
    print(f"  Mentee accessing mentee-only route - Status: {resp_mentee_allowed.status_code}, Response: {resp_mentee_allowed.get_json()}")
    assert resp_mentee_allowed.status_code == 200, f"Expected 200 OK, got {resp_mentee_allowed.status_code}"
    print("  -> PASSED: Mentee-only route correctly rejects mentor (403) and allows mentee (200)")

    # -------------------------------------------------------------
    # Cleanup Temporary Test Data
    # -------------------------------------------------------------
    print("\n[CLEANUP] Cleaning up temporary test data from database...")
    with app.app_context():
        test_users = User.query.filter(User.email.in_([test_mentee_email, test_mentor_email])).all()
        for u in test_users:
            MenteeProfile.query.filter_by(user_id=u.id).delete()
            MentorProfile.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()

        # Verify 0 rows remain for test emails
        remaining = User.query.filter(User.email.in_([test_mentee_email, test_mentor_email])).count()
        assert remaining == 0, f"Cleanup incomplete: {remaining} test users remain"
        print("  -> PASSED: Temporary test users and profiles cleanly deleted (0 remain)")

    # -------------------------------------------------------------
    # Table Schema Verification
    # -------------------------------------------------------------
    print("\n[VERIFICATION] Verifying all 14 database tables remain intact...")
    with app.app_context():
        inspector = inspect(db.engine)
        tables = set(inspector.get_table_names())
        expected_tables = {
            'users', 'mentor_profiles', 'mentee_profiles', 'skills',
            'user_skills', 'learning_interests', 'mentor_availability',
            'mentorship_requests', 'sessions', 'resources', 'progress',
            'feedback', 'certificates', 'achievements'
        }
        assert expected_tables.issubset(tables), f"Missing tables: {expected_tables - tables}"
        print(f"  -> PASSED: All {len(expected_tables)} expected tables verified present in MySQL: {sorted(list(expected_tables))}")

    print("\n" + "=" * 60)
    print("ALL 10 TESTS + CLEANUP + SCHEMA VERIFICATION PASSED SUCCESSFULLY!")
    print("=" * 60)
    return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
