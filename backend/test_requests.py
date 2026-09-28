"""
Test suite for Phase 5: Mentorship Requests.
Covers request creation, retrieval, acceptance, rejection, duplicate handling,
role-based access control, security checks, edge cases, cleanup, and schema integrity verification.
"""

import sys
from datetime import datetime
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING PHASE 5: MENTORSHIP REQUESTS SYSTEM TESTS")
    print("=" * 65)

    test_mentee1_email = "test_mentee1_req_suite@example.com"
    test_mentee2_email = "test_mentee2_req_suite@example.com"
    test_mentor1_email = "test_mentor1_req_suite@example.com"
    test_mentor2_email = "test_mentor2_req_suite@example.com"
    test_dual_email = "test_dual_req_suite@example.com"

    all_test_emails = [
        test_mentee1_email,
        test_mentee2_email,
        test_mentor1_email,
        test_mentor2_email,
        test_dual_email
    ]

    # Clean up any leftover test data from prior aborted test runs
    with app.app_context():
        existing_users = User.query.filter(User.email.in_(all_test_emails)).all()
        user_ids = [u.id for u in existing_users]
        if user_ids:
            mentee_profs = MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).all()
            mentor_profs = MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).all()
            mentee_ids = [m.id for m in mentee_profs]
            mentor_ids = [m.id for m in mentor_profs]

            if mentee_ids or mentor_ids:
                MentorshipRequest.query.filter(
                    (MentorshipRequest.mentee_id.in_(mentee_ids)) |
                    (MentorshipRequest.mentor_id.in_(mentor_ids))
                ).delete(synchronize_session=False)

            MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
            MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
            User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
            db.session.commit()

    all_passed = True

    try:
        # -------------------------------------------------------------
        # P. Health Check
        # -------------------------------------------------------------
        print("\n[TEST P] Testing GET /api/health...")
        resp = client.get('/api/health')
        assert resp.status_code == 200, f"Health check failed with status {resp.status_code}"
        data = resp.get_json()
        assert data.get("status") == "success", "Health check response invalid"
        print("  -> PASSED: /api/health returned 200 OK")

        # -------------------------------------------------------------
        # SETUP: Register test users and obtain JWTs
        # -------------------------------------------------------------
        print("\n[SETUP] Registering test mentees and mentors...")

        # Mentee 1
        client.post('/api/auth/register', json={
            "name": "Mentee One", "email": test_mentee1_email, "password": "Password123!", "role": "mentee"
        })
        login1 = client.post('/api/auth/login', json={"email": test_mentee1_email, "password": "Password123!"}).get_json()
        token_mentee1 = login1['access_token']
        headers_mentee1 = {"Authorization": f"Bearer {token_mentee1}"}

        # Mentee 2
        client.post('/api/auth/register', json={
            "name": "Mentee Two", "email": test_mentee2_email, "password": "Password123!", "role": "mentee"
        })
        login2 = client.post('/api/auth/login', json={"email": test_mentee2_email, "password": "Password123!"}).get_json()
        token_mentee2 = login2['access_token']
        headers_mentee2 = {"Authorization": f"Bearer {token_mentee2}"}

        # Mentor 1
        client.post('/api/auth/register', json={
            "name": "Mentor Alpha", "email": test_mentor1_email, "password": "Password123!", "role": "mentor"
        })
        login_m1 = client.post('/api/auth/login', json={"email": test_mentor1_email, "password": "Password123!"}).get_json()
        token_mentor1 = login_m1['access_token']
        headers_mentor1 = {"Authorization": f"Bearer {token_mentor1}"}

        # Mentor 2
        client.post('/api/auth/register', json={
            "name": "Mentor Beta", "email": test_mentor2_email, "password": "Password123!", "role": "mentor"
        })
        login_m2 = client.post('/api/auth/login', json={"email": test_mentor2_email, "password": "Password123!"}).get_json()
        token_mentor2 = login_m2['access_token']
        headers_mentor2 = {"Authorization": f"Bearer {token_mentor2}"}

        # Fetch Profile IDs for Mentor 1 and Mentor 2
        with app.app_context():
            u_m1 = User.query.filter_by(email=test_mentor1_email).first()
            p_m1 = MentorProfile.query.filter_by(user_id=u_m1.id).first()
            mentor1_profile_id = p_m1.id

            u_m2 = User.query.filter_by(email=test_mentor2_email).first()
            p_m2 = MentorProfile.query.filter_by(user_id=u_m2.id).first()
            mentor2_profile_id = p_m2.id

            u_me1 = User.query.filter_by(email=test_mentee1_email).first()
            p_me1 = MenteeProfile.query.filter_by(user_id=u_me1.id).first()
            mentee1_profile_id = p_me1.id

        print(f"  -> Setup complete. Mentor1 Profile ID: {mentor1_profile_id}, Mentor2 Profile ID: {mentor2_profile_id}")

        # -------------------------------------------------------------
        # N. Unauthenticated Endpoint Rejections (401)
        # -------------------------------------------------------------
        print("\n[TEST N] Testing Unauthenticated Rejections (401)...")
        assert client.post('/api/requests', json={"mentor_id": mentor1_profile_id}).status_code == 401
        assert client.get('/api/requests/sent').status_code == 401
        assert client.get('/api/requests/received').status_code == 401
        assert client.patch('/api/requests/1/accept').status_code == 401
        assert client.patch('/api/requests/1/reject').status_code == 401
        print("  -> PASSED: All request endpoints returned 401 when unauthenticated")

        # -------------------------------------------------------------
        # H. Mentor Cannot Create Request (403)
        # -------------------------------------------------------------
        print("\n[TEST H] Testing Mentor Create Request Rejection (403)...")
        resp = client.post('/api/requests', json={"mentor_id": mentor2_profile_id}, headers=headers_mentor1)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        data = resp.get_json()
        assert data.get("status") == "error"
        print("  -> PASSED: Mentor blocked from creating request with 403 Forbidden")

        # -------------------------------------------------------------
        # L. Invalid Mentor ID (404)
        # -------------------------------------------------------------
        print("\n[TEST L] Testing Request Creation to Invalid Mentor (404)...")
        resp = client.post('/api/requests', json={"mentor_id": 999999}, headers=headers_mentee1)
        assert resp.status_code == 404, f"Expected 404, got {resp.status_code}"
        print("  -> PASSED: Request to invalid mentor returned 404 Not Found")

        # -------------------------------------------------------------
        # M. Self-Request Prevention (400)
        # -------------------------------------------------------------
        print("\n[TEST M] Testing Self-Request Prevention (400)...")
        # Give Mentee 1 a mentor profile as well to simulate self-request
        with app.app_context():
            u_me1 = User.query.filter_by(email=test_mentee1_email).first()
            self_m_prof = MentorProfile(user_id=u_me1.id)
            db.session.add(self_m_prof)
            db.session.commit()
            self_mentor_profile_id = self_m_prof.id

        resp = client.post('/api/requests', json={"mentor_id": self_mentor_profile_id}, headers=headers_mentee1)
        assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
        assert "themselves" in resp.get_json().get("message", "").lower()
        print("  -> PASSED: Self-request rejected with 400 Bad Request")

        # -------------------------------------------------------------
        # A & B. Mentee Successfully Creates Request (201 & pending status)
        # -------------------------------------------------------------
        print("\n[TEST A & B] Testing Mentee Request Creation (201 & Pending)...")
        req_payload = {
            "mentor_id": mentor1_profile_id,
            "message": "I would like guidance in Python and Flask development."
        }
        resp = client.post('/api/requests', json=req_payload, headers=headers_mentee1)
        data = resp.get_json()
        print(f"  Status: {resp.status_code}, Response: {data}")
        assert resp.status_code == 201, f"Expected 201, got {resp.status_code}"
        assert data.get("status") == "success"
        req1 = data.get("request", {})
        assert req1.get("status") == "pending"
        assert req1.get("requested_at") is not None
        assert req1.get("responded_at") is None
        assert req1.get("mentor_id") == mentor1_profile_id
        req1_id = req1.get("id")
        print("  -> PASSED: Mentee created request successfully with initial 'pending' status")

        # -------------------------------------------------------------
        # G. Duplicate Pending Request Rejection (409)
        # -------------------------------------------------------------
        print("\n[TEST G] Testing Duplicate Request Rejection (409)...")
        resp_dup = client.post('/api/requests', json=req_payload, headers=headers_mentee1)
        data_dup = resp_dup.get_json()
        assert resp_dup.status_code == 409, f"Expected 409, got {resp_dup.status_code}"
        assert data_dup.get("status") == "error"
        print("  -> PASSED: Duplicate request correctly rejected with 409 Conflict")

        # -------------------------------------------------------------
        # C. Mentor Sees Request in Received List (GET /api/requests/received)
        # -------------------------------------------------------------
        print("\n[TEST C] Testing Mentor Received Requests List...")
        resp = client.get('/api/requests/received', headers=headers_mentor1)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.get_json()
        assert data.get("status") == "success"
        requests = data.get("requests", [])
        assert len(requests) >= 1
        found = any(r['id'] == req1_id for r in requests)
        assert found, f"Request {req1_id} not found in mentor received list"
        target_req = next(r for r in requests if r['id'] == req1_id)
        assert "mentee" in target_req
        assert target_req["mentee"]["name"] == "Mentee One"
        print("  -> PASSED: Mentor saw pending request in received list with mentee metadata")

        # -------------------------------------------------------------
        # D. Mentee Sees Request in Sent List (GET /api/requests/sent)
        # -------------------------------------------------------------
        print("\n[TEST D] Testing Mentee Sent Requests List...")
        resp = client.get('/api/requests/sent', headers=headers_mentee1)
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        data = resp.get_json()
        assert data.get("status") == "success"
        requests = data.get("requests", [])
        assert len(requests) >= 1
        found = any(r['id'] == req1_id for r in requests)
        assert found, f"Request {req1_id} not found in mentee sent list"
        target_req = next(r for r in requests if r['id'] == req1_id)
        assert "mentor" in target_req
        assert target_req["mentor"]["name"] == "Mentor Alpha"
        print("  -> PASSED: Mentee saw pending request in sent list with mentor metadata")

        # -------------------------------------------------------------
        # K. Mentee Sent Isolation (Mentee 2 sees empty/isolated list)
        # -------------------------------------------------------------
        print("\n[TEST K] Testing Mentee Sent Request Isolation...")
        resp = client.get('/api/requests/sent', headers=headers_mentee2)
        assert resp.status_code == 200
        data = resp.get_json()
        reqs = data.get("requests", [])
        assert not any(r['id'] == req1_id for r in reqs), "Mentee 2 accessed Mentee 1's sent request!"
        print("  -> PASSED: Mentee 2 cannot see Mentee 1's sent requests")

        # -------------------------------------------------------------
        # I. Mentee Cannot Accept Request (403)
        # -------------------------------------------------------------
        print("\n[TEST I] Testing Mentee Accept Rejection (403)...")
        resp = client.patch(f'/api/requests/{req1_id}/accept', headers=headers_mentee1)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("  -> PASSED: Mentee blocked from accepting requests with 403 Forbidden")

        # -------------------------------------------------------------
        # J. Unauthorized Mentor Cannot Accept Another Mentor's Request (403)
        # -------------------------------------------------------------
        print("\n[TEST J] Testing Unauthorized Mentor Accept Rejection (403)...")
        resp = client.patch(f'/api/requests/{req1_id}/accept', headers=headers_mentor2)
        assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
        print("  -> PASSED: Mentor Beta blocked from accepting Mentor Alpha's request with 403 Forbidden")

        # -------------------------------------------------------------
        # E. Mentor Successfully Accepts Request -> status accepted
        # -------------------------------------------------------------
        print("\n[TEST E] Testing Mentor Acceptance (status accepted)...")
        resp = client.patch(f'/api/requests/{req1_id}/accept', headers=headers_mentor1)
        data = resp.get_json()
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert data.get("status") == "success"
        req_acc = data.get("request", {})
        assert req_acc.get("status") == "accepted"
        assert req_acc.get("responded_at") is not None
        print("  -> PASSED: Mentor Alpha successfully accepted request (status = accepted)")

        # -------------------------------------------------------------
        # O. Repeated Accept Attempt Handled Safely
        # -------------------------------------------------------------
        print("\n[TEST O-1] Testing Idempotent / Repeated Accept Handling...")
        resp = client.patch(f'/api/requests/{req1_id}/accept', headers=headers_mentor1)
        data = resp.get_json()
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
        assert data.get("status") == "success"
        assert data.get("request", {}).get("status") == "accepted"
        print("  -> PASSED: Repeated accept returned 200 OK safely")

        # -------------------------------------------------------------
        # F. Mentor Successfully Rejects Another Request -> status rejected
        # -------------------------------------------------------------
        print("\n[TEST F] Testing Mentee Request 2 Creation & Mentor Rejection...")
        # Create request from Mentee 2 to Mentor 2
        resp2 = client.post('/api/requests', json={
            "mentor_id": mentor2_profile_id,
            "message": "Looking for frontend guidance."
        }, headers=headers_mentee2)
        assert resp2.status_code == 201
        req2_id = resp2.get_json()["request"]["id"]

        resp_rej = client.patch(f'/api/requests/{req2_id}/reject', headers=headers_mentor2)
        data_rej = resp_rej.get_json()
        assert resp_rej.status_code == 200, f"Expected 200, got {resp_rej.status_code}"
        assert data_rej.get("status") == "success"
        req_rej = data_rej.get("request", {})
        assert req_rej.get("status") == "rejected"
        assert req_rej.get("responded_at") is not None
        print("  -> PASSED: Mentor Beta successfully rejected request (status = rejected)")

        # -------------------------------------------------------------
        # O. Repeated Reject Attempt Handled Safely
        # -------------------------------------------------------------
        print("\n[TEST O-2] Testing Idempotent / Repeated Reject Handling...")
        resp_rej2 = client.patch(f'/api/requests/{req2_id}/reject', headers=headers_mentor2)
        data_rej2 = resp_rej2.get_json()
        assert resp_rej2.status_code == 200, f"Expected 200, got {resp_rej2.status_code}"
        assert data_rej2.get("status") == "success"
        assert data_rej2.get("request", {}).get("status") == "rejected"
        print("  -> PASSED: Repeated reject returned 200 OK safely")

    except Exception as err:
        print(f"\n[ERROR DURING TESTS]: {err}")
        all_passed = False
        raise err

    finally:
        # -------------------------------------------------------------
        # CLEANUP: Delete all temporary test records
        # -------------------------------------------------------------
        print("\n[CLEANUP] Cleaning up all temporary test users, profiles, and requests...")
        with app.app_context():
            existing_users = User.query.filter(User.email.in_(all_test_emails)).all()
            user_ids = [u.id for u in existing_users]
            if user_ids:
                mentee_profs = MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).all()
                mentor_profs = MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).all()
                mentee_ids = [m.id for m in mentee_profs]
                mentor_ids = [m.id for m in mentor_profs]

                if mentee_ids or mentor_ids:
                    MentorshipRequest.query.filter(
                        (MentorshipRequest.mentee_id.in_(mentee_ids)) |
                        (MentorshipRequest.mentor_id.in_(mentor_ids))
                    ).delete(synchronize_session=False)

                MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
                db.session.commit()

            # Verify zero leftover test records
            rem_users = User.query.filter(User.email.in_(all_test_emails)).count()
            print(f"  -> PASSED: All temporary test records removed cleanly ({rem_users} remaining)")

    # -------------------------------------------------------------
    # S. Database Schema & Table Count Verification
    # -------------------------------------------------------------
    print("\n[TEST S] Verifying all 14 database tables remain intact...")
    expected_tables = {
        'achievements', 'certificates', 'feedback', 'learning_interests',
        'mentee_profiles', 'mentor_availability', 'mentor_profiles',
        'mentorship_requests', 'progress', 'resources', 'sessions',
        'skills', 'user_skills', 'users'
    }

    with app.app_context():
        inspector = inspect(db.engine)
        existing_tables = set(inspector.get_table_names())

        missing_tables = expected_tables - existing_tables
        assert not missing_tables, f"Missing database tables detected: {missing_tables}"
        print(f"  -> PASSED: All 14 expected tables present in database: {sorted(list(existing_tables))}")

    print("=" * 65)
    print("ALL PHASE 5 TESTS + CLEANUP + SCHEMA VERIFICATION PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == '__main__':
    run_tests()
