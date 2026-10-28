"""
Comprehensive test suite specifically for Forgot Password & Reset Password functionality.
Covers:
  - Unknown email ("No account found with this email address." 404)
  - Registered email and successful email dispatch (200 + token hash stored with 15-min expiry)
  - SMTP delivery failure (502 and appropriate retryable error message)
  - Expired token (400)
  - Invalid token (400)
  - Single-use token (cannot be replayed)
  - Successful password reset and rejection of the old password
"""

import sys
from datetime import datetime, timezone, timedelta
from unittest.mock import patch
from app import create_app, db
from models import User, MenteeProfile, MentorProfile
from utils.auth import hash_password, hash_token, verify_password


def run_tests():
    app = create_app()
    app.config['REQUIRE_EMAIL_VERIFICATION'] = True
    client = app.test_client()

    print("=" * 70)
    print("STARTING FORGOT PASSWORD & PASSWORD RESET VERIFICATION SUITE")
    print("=" * 70)

    test_email = "forgot_pwd_test_user@example.com"
    unknown_email = "non_existent_account_12345@example.com"
    initial_password = "OldInitialPassword123!"
    new_password = "NewSecurePassword456!"

    # Pre-cleanup
    with app.app_context():
        old_user = User.query.filter_by(email=test_email).first()
        if old_user:
            MenteeProfile.query.filter_by(user_id=old_user.id).delete()
            MentorProfile.query.filter_by(user_id=old_user.id).delete()
            db.session.delete(old_user)
            db.session.commit()

        # Create active, verified user for password reset testing
        test_user = User(
            name="Forgot Pwd User",
            email=test_email,
            password_hash=hash_password(initial_password),
            role="mentee",
            is_verified=True
        )
        db.session.add(test_user)
        db.session.commit()
        test_user_id = test_user.id

    try:
        # -----------------------------------------------------------------
        # 1. Unknown Email Check
        # -----------------------------------------------------------------
        print("\n[TEST 1] Testing unknown email request...")
        resp = client.post('/api/auth/forgot-password', json={"email": unknown_email})
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}: {resp.get_data(as_text=True)}"
        data = resp.get_json()
        assert data.get("status") == "error"
        assert data.get("message") == "No account found with this email address.", (
            f"Unexpected message: {data.get('message')}"
        )
        print("  -> PASSED: Returns 404 with 'No account found with this email address.'")

        # -----------------------------------------------------------------
        # 2. SMTP Delivery Failure Check
        # -----------------------------------------------------------------
        print("\n[TEST 2] Testing SMTP delivery failure handling...")
        with patch('routes.auth.send_password_reset_email', return_value=False):
            resp = client.post('/api/auth/forgot-password', json={"email": test_email})
            assert resp.status_code == 502, f"Expected 502, got {resp.status_code}: {resp.get_data(as_text=True)}"
            data = resp.get_json()
            assert data.get("status") == "error"
            assert "failed to send" in data.get("message", "").lower()
            print(f"  -> Returned error message: '{data.get('message')}'")

        # Verify that after failed delivery, token hash is cleared to allow clean retry
        with app.app_context():
            u = db.session.get(User, test_user_id)
            assert u.reset_password_token_hash is None
        print("  -> PASSED: Delivery failure returned 502 error and invalidated failed token state")

        # -----------------------------------------------------------------
        # 3. Registered Email & Successful Dispatch Check
        # -----------------------------------------------------------------
        print("\n[TEST 3] Testing registered email and successful email dispatch...")
        captured_token = None

        def mock_send(to_email, recipient_name, raw_token):
            nonlocal captured_token
            captured_token = raw_token
            return True

        with patch('routes.auth.send_password_reset_email', side_effect=mock_send):
            resp = client.post('/api/auth/forgot-password', json={"email": test_email})
            assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.get_data(as_text=True)}"
            data = resp.get_json()
            assert data.get("status") == "success"
            assert captured_token is not None, "Raw token was not passed to email dispatcher"

        # Verify database token hash, expiration, and that raw token is NEVER stored
        with app.app_context():
            u = db.session.get(User, test_user_id)
            assert u.reset_password_token_hash is not None
            assert u.reset_password_token_hash == hash_token(captured_token)
            assert u.reset_password_token_hash != captured_token
            assert len(u.reset_password_token_hash) == 64
            assert u.reset_password_sent_at is not None
        print("  -> PASSED: Email dispatched, SHA-256 hash stored in DB, raw token never stored")

        # -----------------------------------------------------------------
        # 4. Invalid Token Check
        # -----------------------------------------------------------------
        print("\n[TEST 4] Testing invalid token rejection...")
        resp = client.post('/api/auth/reset-password', json={
            "token": "completely_invalid_random_token_999",
            "new_password": new_password
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.get_data(as_text=True)}"
        assert "invalid" in resp.get_json().get("message", "").lower()
        print("  -> PASSED: Invalid token rejected with 400")

        # -----------------------------------------------------------------
        # 5. Expired Token Check (>15 minutes)
        # -----------------------------------------------------------------
        print("\n[TEST 5] Testing expired token rejection (15-minute expiry)...")
        expired_token = "expired_raw_token_xyz_123"
        with app.app_context():
            u = db.session.get(User, test_user_id)
            u.reset_password_token_hash = hash_token(expired_token)
            # Set to 16 minutes ago (limit is 15 minutes)
            u.reset_password_sent_at = datetime.now(timezone.utc) - timedelta(minutes=16)
            db.session.commit()

        resp = client.post('/api/auth/reset-password', json={
            "token": expired_token,
            "new_password": new_password
        })
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}: {resp.get_data(as_text=True)}"
        assert "expired" in resp.get_json().get("message", "").lower()
        print("  -> PASSED: Expired token rejected with 400 and invalidated")

        # -----------------------------------------------------------------
        # 6. Successful Password Reset & Token Invalidation
        # -----------------------------------------------------------------
        print("\n[TEST 6] Testing valid token reset...")
        valid_token = "valid_fresh_reset_token_456"
        with app.app_context():
            u = db.session.get(User, test_user_id)
            u.reset_password_token_hash = hash_token(valid_token)
            u.reset_password_sent_at = datetime.now(timezone.utc)
            db.session.commit()

        resp = client.post('/api/auth/reset-password', json={
            "token": valid_token,
            "new_password": new_password
        })
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.get_data(as_text=True)}"
        print("  -> PASSED: Reset password returned 200 OK")

        # -----------------------------------------------------------------
        # 7. Single-Use Verification (Replay Protection)
        # -----------------------------------------------------------------
        print("\n[TEST 7] Testing single-use token replay rejection...")
        with app.app_context():
            u = db.session.get(User, test_user_id)
            assert u.reset_password_token_hash is None, "Token hash was not cleared after use"

        resp = client.post('/api/auth/reset-password', json={
            "token": valid_token,
            "new_password": "YetAnotherPassword789!"
        })
        assert resp.status_code == 400, f"Expected 400 on reuse, got {resp.status_code}: {resp.get_data(as_text=True)}"
        print("  -> PASSED: Reusing already consumed token is blocked with 400")

        # -----------------------------------------------------------------
        # 8. Authentication Check: Old Password Rejected, New Accepted
        # -----------------------------------------------------------------
        print("\n[TEST 8] Testing login with old vs new password...")
        # Old password must fail
        resp_old = client.post('/api/auth/login', json={
            "email": test_email,
            "password": initial_password
        })
        assert resp_old.status_code == 401, f"Expected 401 for old password, got {resp_old.status_code}"
        print("  -> PASSED: Old password rejected with 401 Unauthorized")

        # New password must succeed
        resp_new = client.post('/api/auth/login', json={
            "email": test_email,
            "password": new_password
        })
        assert resp_new.status_code == 200, f"Expected 200 for new password, got {resp_new.status_code}"
        new_data = resp_new.get_json()
        assert "access_token" in new_data
        print("  -> PASSED: New password successfully authenticates and issues JWT")

    finally:
        # Cleanup
        print("\n[CLEANUP] Removing test user...")
        with app.app_context():
            u = db.session.get(User, test_user_id)
            if u:
                MenteeProfile.query.filter_by(user_id=u.id).delete()
                MentorProfile.query.filter_by(user_id=u.id).delete()
                db.session.delete(u)
                db.session.commit()
        print("  -> PASSED: Cleanup finished")

    print("\n" + "=" * 70)
    print("ALL FORGOT PASSWORD & RESET TESTS COMPLETED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == '__main__':
    ok = run_tests()
    sys.exit(0 if ok else 1)
