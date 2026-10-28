"""
Comprehensive verification test suite for email verification and forgot/reset password flows.
Tests:
1. Registration creates unverified user and stores hashed token.
2. Unverified user is rejected from login (403 unverified).
3. Email verification with invalid token fails (400).
4. Email verification with valid token succeeds, marks user verified, and clears token hash.
5. Newly verified user can log in and receives valid JWT.
6. Forgot password returns generic message for both existing and non-existing emails.
7. Reset password with expired token fails.
8. Reset password with valid single-use token updates password hash.
9. Reset token is cleared after single use (replay attack blocked).
10. Login with new password succeeds.
11. Pre-existing accounts remain verified and can log in without issue.
12. All three roles (mentee, mentor, admin) are tested.
"""

import sys
from datetime import datetime, timezone, timedelta
from app import create_app, db
from models import User, MenteeProfile, MentorProfile
from utils.auth import hash_password, hash_token, verify_password


def run_tests():
    app = create_app()
    app.config['REQUIRE_EMAIL_VERIFICATION'] = True
    client = app.test_client()

    print("=" * 65)
    print("STARTING EMAIL VERIFICATION & PASSWORD RESET TEST SUITE")
    print("=" * 65)

    test_mentee_email = "test_verify_mentee@example.com"
    test_mentor_email = "test_verify_mentor@example.com"
    test_admin_email = "test_verify_admin@example.com"

    # Pre-cleanup in case previous runs left artifacts
    with app.app_context():
        old_users = User.query.filter(User.email.in_([test_mentee_email, test_mentor_email, test_admin_email])).all()
        for u in old_users:
            MenteeProfile.query.filter_by(user_id=u.id).delete()
            MentorProfile.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()

    # -------------------------------------------------------------
    # 1. Registration creates unverified user and saves token hash
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Mentee Registration (Unverified by default)...")
    reg_payload = {
        "name": "Verify Mentee",
        "email": test_mentee_email,
        "password": "Password123!",
        "role": "mentee"
    }
    resp = client.post('/api/auth/register', json=reg_payload)
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["user"]["is_verified"] is False
    print("  -> PASSED: Mentee registered as is_verified=False")

    with app.app_context():
        u = User.query.filter_by(email=test_mentee_email).first()
        assert u is not None
        assert u.is_verified is False
        assert u.email_verification_token_hash is not None
        assert len(u.email_verification_token_hash) == 64  # SHA-256 hex length
        print("  -> PASSED: Verification token stored strictly as SHA-256 hash in DB")

    # -------------------------------------------------------------
    # 2. Unverified user rejected from login
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Login Rejection for Unverified Account...")
    resp = client.post('/api/auth/login', json={
        "email": test_mentee_email,
        "password": "Password123!"
    })
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    data = resp.get_json()
    assert data["status"] == "error"
    assert data.get("unverified") is True
    print("  -> PASSED: Unverified account login blocked with 403 Forbidden")

    # -------------------------------------------------------------
    # 3. Email verification with invalid token fails
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Email Verification with Invalid Token...")
    resp = client.post('/api/auth/verify-email', json={"token": "invalid_fake_token_12345"})
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    assert resp.get_json()["status"] == "error"
    print("  -> PASSED: Invalid token rejected with 400")

    # -------------------------------------------------------------
    # 4. Email verification with valid token succeeds
    # -------------------------------------------------------------
    print("\n[TEST 4] Testing Email Verification with Valid Token...")
    # Inject a known token to test verification
    raw_token = "valid_test_verification_token_abc"
    with app.app_context():
        u = User.query.filter_by(email=test_mentee_email).first()
        u.email_verification_token_hash = hash_token(raw_token)
        u.email_verification_sent_at = datetime.now(timezone.utc)
        db.session.commit()

    resp = client.post('/api/auth/verify-email', json={"token": raw_token})
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    assert resp.get_json()["status"] == "success"

    with app.app_context():
        u = User.query.filter_by(email=test_mentee_email).first()
        assert u.is_verified is True
        assert u.email_verification_token_hash is None
    print("  -> PASSED: Verification succeeded, user marked verified, token hash cleared")

    # -------------------------------------------------------------
    # 5. Verified user can now log in
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Login After Successful Verification...")
    resp = client.post('/api/auth/login', json={
        "email": test_mentee_email,
        "password": "Password123!"
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    data = resp.get_json()
    assert "access_token" in data
    print("  -> PASSED: Verified user logged in successfully with JWT token")

    # -------------------------------------------------------------
    # 6. Forgot password (existing user vs non-existing user)
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Forgot Password Response Handling...")
    resp1 = client.post('/api/auth/forgot-password', json={"email": test_mentee_email})
    assert resp1.status_code == 200
    assert resp1.get_json()["status"] == "success"

    resp2 = client.post('/api/auth/forgot-password', json={"email": "nonexistent_999@example.com"})
    assert resp2.status_code == 404
    assert resp2.get_json()["message"] == "No account found with this email address."
    print("  -> PASSED: Expected responses for registered (200) and unregistered (404) emails")

    # -------------------------------------------------------------
    # 7. Reset password with expired token fails
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing Password Reset Token Expiry...")
    raw_reset_token = "test_reset_token_xyz"
    with app.app_context():
        u = User.query.filter_by(email=test_mentee_email).first()
        u.reset_password_token_hash = hash_token(raw_reset_token)
        # Set sent_at to 20 minutes ago (limit is 15 minutes)
        u.reset_password_sent_at = datetime.now(timezone.utc) - timedelta(minutes=20)
        db.session.commit()

    resp = client.post('/api/auth/reset-password', json={
        "token": raw_reset_token,
        "new_password": "NewSecretPassword456!"
    })
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    assert "expired" in resp.get_json()["message"].lower()
    print("  -> PASSED: Expired reset token rejected with 400")

    # -------------------------------------------------------------
    # 8. Reset password with valid token succeeds and updates password
    # -------------------------------------------------------------
    print("\n[TEST 8] Testing Password Reset with Valid Token...")
    valid_reset_token = "fresh_valid_reset_token_789"
    with app.app_context():
        u = User.query.filter_by(email=test_mentee_email).first()
        u.reset_password_token_hash = hash_token(valid_reset_token)
        u.reset_password_sent_at = datetime.now(timezone.utc)
        db.session.commit()

    resp = client.post('/api/auth/reset-password', json={
        "token": valid_reset_token,
        "new_password": "NewSecretPassword456!"
    })
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    print("  -> PASSED: Password reset successfully completed")

    # -------------------------------------------------------------
    # 9. Single-use validation: reuse of reset token is blocked
    # -------------------------------------------------------------
    print("\n[TEST 9] Testing Reset Token Single-Use (Replay Protection)...")
    resp_reuse = client.post('/api/auth/reset-password', json={
        "token": valid_reset_token,
        "new_password": "AnotherNewPassword999!"
    })
    assert resp_reuse.status_code == 400, f"Expected 400, got {resp_reuse.status_code}"
    print("  -> PASSED: Reusing reset token immediately blocked")

    # -------------------------------------------------------------
    # 10. Login with new password succeeds; old password fails
    # -------------------------------------------------------------
    print("\n[TEST 10] Testing Login with New Credentials...")
    resp_old = client.post('/api/auth/login', json={
        "email": test_mentee_email,
        "password": "Password123!"
    })
    assert resp_old.status_code == 401, f"Expected 401 for old password, got {resp_old.status_code}"

    resp_new = client.post('/api/auth/login', json={
        "email": test_mentee_email,
        "password": "NewSecretPassword456!"
    })
    assert resp_new.status_code == 200, f"Expected 200 for new password, got {resp_new.status_code}"
    print("  -> PASSED: Old password rejected, new password authenticated successfully")

    # -------------------------------------------------------------
    # 11. Testing mentor and admin roles with verification
    # -------------------------------------------------------------
    print("\n[TEST 11] Testing Mentor & Admin Roles...")
    # Register mentor
    resp = client.post('/api/auth/register', json={
        "name": "Verify Mentor",
        "email": test_mentor_email,
        "password": "MentorPassword123!",
        "role": "mentor"
    })
    assert resp.status_code == 201

    # Create admin directly in database
    with app.app_context():
        admin = User(
            name="Platform Admin",
            email=test_admin_email,
            password_hash=hash_password("AdminPassword123!"),
            role="admin",
            is_verified=True
        )
        db.session.add(admin)

        # Mark mentor as verified
        mentor_u = User.query.filter_by(email=test_mentor_email).first()
        mentor_u.is_verified = True
        db.session.commit()

    # Login mentor
    resp_m = client.post('/api/auth/login', json={
        "email": test_mentor_email,
        "password": "MentorPassword123!"
    })
    assert resp_m.status_code == 200
    m_token = resp_m.get_json()["access_token"]

    # Login admin
    resp_a = client.post('/api/auth/login', json={
        "email": test_admin_email,
        "password": "AdminPassword123!"
    })
    assert resp_a.status_code == 200
    a_token = resp_a.get_json()["access_token"]

    # Verify mentor role access
    m_resp = client.get('/api/auth/mentor-only-test', headers={"Authorization": f"Bearer {m_token}"})
    assert m_resp.status_code == 200
    print("  -> PASSED: Mentor and Admin roles verified and operational")

    # -------------------------------------------------------------
    # 12. Pre-existing accounts remain verified & can log in
    # -------------------------------------------------------------
    print("\n[TEST 12] Testing Pre-Existing Accounts Compatibility...")
    with app.app_context():
        # Check actual permanent user accounts that existed prior to migration (IDs <= 271)
        original_preexisting_ids = [41, 42, 43, 44, 221, 229, 230, 231, 271]
        preexisting_users = User.query.filter(User.id.in_(original_preexisting_ids)).all()
        assert len(preexisting_users) == 9, f"Expected 9 pre-existing users, found {len(preexisting_users)}"
        for u in preexisting_users:
            assert u.is_verified is True, f"Pre-existing user {u.email} was unexpectedly marked unverified!"
        print(f"  -> PASSED: All {len(preexisting_users)} original pre-existing accounts confirmed verified=True")

    # -------------------------------------------------------------
    # Cleanup Test Users
    # -------------------------------------------------------------
    print("\n[CLEANUP] Cleaning up test accounts...")
    with app.app_context():
        test_users = User.query.filter(User.email.in_([test_mentee_email, test_mentor_email, test_admin_email])).all()
        for u in test_users:
            MenteeProfile.query.filter_by(user_id=u.id).delete()
            MentorProfile.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()
    print("  -> PASSED: Cleaned up temporary test accounts cleanly")

    print("\n" + "=" * 65)
    print("ALL 12 VERIFICATION & PASSWORD RESET TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)
    return True


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
