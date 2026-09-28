"""
Test suite for Phase 6: Sessions + Jitsi Meet integration.
Covers scheduling, retrieval, updates, cancellation, role-based authorization,
unrelated user isolation, Jitsi room and URL verification, cleanup, and schema integrity.
"""

import sys
from datetime import datetime, date, time
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest, Session
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING PHASE 6: SESSIONS & JITSI INTEGRATION TESTS")
    print("=" * 65)

    test_mentee1_email = "test_mentee1_session_suite@example.com"
    test_mentee2_email = "test_mentee2_session_suite@example.com"
    test_mentor1_email = "test_mentor1_session_suite@example.com"
    test_mentor2_email = "test_mentor2_session_suite@example.com"
    test_unrelated_email = "test_unrelated_session_suite@example.com"

    all_test_emails = [
        test_mentee1_email,
        test_mentee2_email,
        test_mentor1_email,
        test_mentor2_email,
        test_unrelated_email
    ]

    def cleanup_data():
        with app.app_context():
            users = User.query.filter(User.email.in_(all_test_emails)).all()
            user_ids = [u.id for u in users]
            if user_ids:
                mentee_profs = MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).all()
                mentor_profs = MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).all()
                mentee_ids = [m.id for m in mentee_profs]
                mentor_ids = [m.id for m in mentor_profs]

                if mentee_ids or mentor_ids:
                    # Delete sessions first due to foreign keys
                    Session.query.filter(
                        (Session.mentee_id.in_(mentee_ids)) |
                        (Session.mentor_id.in_(mentor_ids))
                    ).delete(synchronize_session=False)

                    # Delete mentorship requests
                    MentorshipRequest.query.filter(
                        (MentorshipRequest.mentee_id.in_(mentee_ids)) |
                        (MentorshipRequest.mentor_id.in_(mentor_ids))
                    ).delete(synchronize_session=False)

                MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
                db.session.commit()

    # Pre-clean
    cleanup_data()

    try:
        # -------------------------------------------------------------
        # A. Health Check
        # -------------------------------------------------------------
        print("\n[TEST A] Testing GET /api/health...")
        resp = client.get('/api/health')
        assert resp.status_code == 200, f"Health check failed with status {resp.status_code}"
        print("  -> PASSED: /api/health returned 200 OK")

        # -------------------------------------------------------------
        # B. Unauthenticated session access (401)
        # -------------------------------------------------------------
        print("\n[TEST B] Testing Unauthenticated Rejections (401)...")
        assert client.post('/api/sessions', json={}).status_code == 401
        assert client.get('/api/sessions').status_code == 401
        assert client.get('/api/sessions/1').status_code == 401
        assert client.put('/api/sessions/1', json={}).status_code == 401
        assert client.delete('/api/sessions/1').status_code == 401
        print("  -> PASSED: All session endpoints require JWT authentication (401)")

        # -------------------------------------------------------------
        # C. Register temporary users
        # -------------------------------------------------------------
        print("\n[TEST C] Registering temporary mentors, mentees, and unrelated user...")
        # Mentee 1
        client.post('/api/auth/register', json={
            "name": "Session Mentee One", "email": test_mentee1_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee1 = client.post('/api/auth/login', json={
            "email": test_mentee1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee1 = {"Authorization": f"Bearer {token_mentee1}"}

        # Mentee 2
        client.post('/api/auth/register', json={
            "name": "Session Mentee Two", "email": test_mentee2_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee2 = client.post('/api/auth/login', json={
            "email": test_mentee2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee2 = {"Authorization": f"Bearer {token_mentee2}"}

        # Mentor 1
        client.post('/api/auth/register', json={
            "name": "Session Mentor Alpha", "email": test_mentor1_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor1 = client.post('/api/auth/login', json={
            "email": test_mentor1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor1 = {"Authorization": f"Bearer {token_mentor1}"}

        # Mentor 2
        client.post('/api/auth/register', json={
            "name": "Session Mentor Beta", "email": test_mentor2_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor2 = client.post('/api/auth/login', json={
            "email": test_mentor2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor2 = {"Authorization": f"Bearer {token_mentor2}"}

        # Unrelated User (Mentee)
        client.post('/api/auth/register', json={
            "name": "Unrelated User", "email": test_unrelated_email, "password": "Password123!", "role": "mentee"
        })
        token_unrelated = client.post('/api/auth/login', json={
            "email": test_unrelated_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_unrelated = {"Authorization": f"Bearer {token_unrelated}"}

        with app.app_context():
            u_m1 = User.query.filter_by(email=test_mentor1_email).first()
            p_m1 = MentorProfile.query.filter_by(user_id=u_m1.id).first()
            mentor1_profile_id = p_m1.id

            u_m2 = User.query.filter_by(email=test_mentor2_email).first()
            p_m2 = MentorProfile.query.filter_by(user_id=u_m2.id).first()
            mentor2_profile_id = p_m2.id

        print("  -> PASSED: All 5 test users registered and authenticated")

        # -------------------------------------------------------------
        # D & E. Create mentorship request and accept as mentor
        # -------------------------------------------------------------
        print("\n[TEST D & E] Creating and accepting mentorship requests...")
        # Request 1: Mentee 1 -> Mentor 1 (Accepted)
        resp_req1 = client.post('/api/requests', json={
            "mentor_id": mentor1_profile_id,
            "message": "Let's learn Flask & Jitsi!"
        }, headers=headers_mentee1)
        assert resp_req1.status_code == 201
        req1_id = resp_req1.get_json()['request']['id']

        resp_acc1 = client.patch(f'/api/requests/{req1_id}/accept', headers=headers_mentor1)
        assert resp_acc1.status_code == 200
        assert resp_acc1.get_json()['request']['status'] == 'accepted'

        # Request 2: Mentee 2 -> Mentor 2 (Pending)
        resp_req2 = client.post('/api/requests', json={
            "mentor_id": mentor2_profile_id,
            "message": "Pending request test"
        }, headers=headers_mentee2)
        assert resp_req2.status_code == 201
        req2_pending_id = resp_req2.get_json()['request']['id']

        # Request 3: Mentee 1 -> Mentor 2 (Rejected)
        resp_req3 = client.post('/api/requests', json={
            "mentor_id": mentor2_profile_id,
            "message": "Rejected request test"
        }, headers=headers_mentee1)
        assert resp_req3.status_code == 201
        req3_rejected_id = resp_req3.get_json()['request']['id']
        client.patch(f'/api/requests/{req3_rejected_id}/reject', headers=headers_mentor2)

        print("  -> PASSED: Mentorship requests initialized (Accepted, Pending, Rejected)")

        # -------------------------------------------------------------
        # K. Invalid request_id -> 404
        # -------------------------------------------------------------
        print("\n[TEST K] Testing Invalid request_id (404)...")
        resp_k = client.post('/api/sessions', json={
            "request_id": 999999,
            "title": "Invalid Req",
            "scheduled_date": "2026-10-15",
            "start_time": "10:00",
            "end_time": "11:00"
        }, headers=headers_mentee1)
        assert resp_k.status_code == 404, f"Expected 404, got {resp_k.status_code}"
        print("  -> PASSED: Non-existent request_id returned 404 Not Found")

        # -------------------------------------------------------------
        # L. Session creation from pending or rejected request is rejected (400)
        # -------------------------------------------------------------
        print("\n[TEST L] Testing Session Creation from Pending/Rejected Request Rejection (400)...")
        # Attempt on pending request
        resp_l1 = client.post('/api/sessions', json={
            "request_id": req2_pending_id,
            "title": "Pending Session",
            "scheduled_date": "2026-10-15",
            "start_time": "10:00",
            "end_time": "11:00"
        }, headers=headers_mentee2)
        assert resp_l1.status_code == 400, f"Expected 400, got {resp_l1.status_code}"

        # Attempt on rejected request
        resp_l2 = client.post('/api/sessions', json={
            "request_id": req3_rejected_id,
            "title": "Rejected Session",
            "scheduled_date": "2026-10-15",
            "start_time": "10:00",
            "end_time": "11:00"
        }, headers=headers_mentee1)
        assert resp_l2.status_code == 400, f"Expected 400, got {resp_l2.status_code}"
        print("  -> PASSED: Sessions cannot be scheduled for pending or rejected requests (400)")

        # -------------------------------------------------------------
        # M. Unrelated user creating session for another pair's request (403)
        # -------------------------------------------------------------
        print("\n[TEST M] Testing Unrelated User Session Creation Rejection (403)...")
        resp_m = client.post('/api/sessions', json={
            "request_id": req1_id,
            "title": "Intruder Session",
            "scheduled_date": "2026-10-15",
            "start_time": "10:00",
            "end_time": "11:00"
        }, headers=headers_unrelated)
        assert resp_m.status_code == 403, f"Expected 403, got {resp_m.status_code}"
        print("  -> PASSED: Unrelated user blocked from creating session with 403 Forbidden")

        # -------------------------------------------------------------
        # N. Invalid time range (end_time <= start_time) -> 400
        # -------------------------------------------------------------
        print("\n[TEST N] Testing Invalid Time Range Rejection (400)...")
        resp_n = client.post('/api/sessions', json={
            "request_id": req1_id,
            "title": "Time Travel Session",
            "scheduled_date": "2026-10-15",
            "start_time": "15:00",
            "end_time": "14:00"
        }, headers=headers_mentee1)
        assert resp_n.status_code == 400, f"Expected 400, got {resp_n.status_code}"
        assert "end_time" in resp_n.get_json().get("message", "").lower()
        print("  -> PASSED: start_time >= end_time rejected with 400 Bad Request")

        # -------------------------------------------------------------
        # F, G, S. Create session as mentee & verify complete payload & Jitsi URL
        # -------------------------------------------------------------
        print("\n[TEST F, G, S] Creating Session as Mentee and Verifying Jitsi Integration...")
        session_payload = {
            "request_id": req1_id,
            "title": "Python Full-Stack Architecture",
            "description": "Deep dive into Flask blueprints, models, and real-time Jitsi integration.",
            "scheduled_date": "2026-10-20",
            "start_time": "14:00",
            "end_time": "15:30"
        }
        resp_f = client.post('/api/sessions', json=session_payload, headers=headers_mentee1)
        data_f = resp_f.get_json()
        print(f"  Status: {resp_f.status_code}, Response: {data_f}")
        assert resp_f.status_code == 201, f"Expected 201, got {resp_f.status_code}"
        assert data_f.get("status") == "success"

        sess = data_f.get("session", {})
        session1_id = sess.get("id")
        assert session1_id is not None
        assert sess.get("request_id") == req1_id
        assert sess.get("title") == "Python Full-Stack Architecture"
        assert sess.get("description") == "Deep dive into Flask blueprints, models, and real-time Jitsi integration."
        assert sess.get("scheduled_date") == "2026-10-20"
        assert "14:00" in sess.get("start_time")
        assert "15:30" in sess.get("end_time")
        assert sess.get("status") == "scheduled"
        assert "mentor" in sess and sess["mentor"]["name"] == "Session Mentor Alpha"
        assert "mentee" in sess and sess["mentee"]["name"] == "Session Mentee One"

        # Verify Jitsi room name and meeting URL
        meeting_room = sess.get("meeting_room")
        meeting_url = sess.get("meeting_url")
        assert meeting_room is not None and f"mentor_mentee_{req1_id}_" in meeting_room
        assert meeting_url == f"https://meet.jit.si/{meeting_room}"
        print(f"  -> PASSED: Session created (ID: {session1_id}) with Jitsi URL: {meeting_url}")

        # -------------------------------------------------------------
        # H & I. GET /api/sessions returns session to both mentor and mentee
        # -------------------------------------------------------------
        print("\n[TEST H & I] Verifying GET /api/sessions for Mentor and Mentee...")
        # Mentor 1 check
        resp_h = client.get('/api/sessions', headers=headers_mentor1)
        assert resp_h.status_code == 200
        mentor_sessions = resp_h.get_json().get("sessions", [])
        assert any(s["id"] == session1_id for s in mentor_sessions)
        print("  -> PASSED: Mentor saw the session in their session list")

        # Mentee 1 check
        resp_i = client.get('/api/sessions', headers=headers_mentee1)
        assert resp_i.status_code == 200
        mentee_sessions = resp_i.get_json().get("sessions", [])
        assert any(s["id"] == session1_id for s in mentee_sessions)
        print("  -> PASSED: Mentee saw the session in their session list")

        # -------------------------------------------------------------
        # J. Unrelated user cannot list or access the session
        # -------------------------------------------------------------
        print("\n[TEST J] Testing Unrelated User Isolation...")
        # Unrelated list
        resp_j1 = client.get('/api/sessions', headers=headers_unrelated)
        assert resp_j1.status_code == 200
        unrelated_sessions = resp_j1.get_json().get("sessions", [])
        assert not any(s["id"] == session1_id for s in unrelated_sessions)

        # Unrelated GET single session by ID
        resp_j2 = client.get(f'/api/sessions/{session1_id}', headers=headers_unrelated)
        assert resp_j2.status_code == 403, f"Expected 403, got {resp_j2.status_code}"
        print("  -> PASSED: Unrelated user completely isolated from session listing and direct access (403)")

        # -------------------------------------------------------------
        # O. Authorized Participant Updates Session (PUT /api/sessions/<id>)
        # -------------------------------------------------------------
        print("\n[TEST O] Testing Authorized Session Update...")
        update_payload = {
            "title": "Advanced Python & Architecture Discussion",
            "scheduled_date": "2026-10-22",
            "start_time": "16:00",
            "end_time": "17:30",
            "description": "Updated agenda items."
        }
        resp_o = client.put(f'/api/sessions/{session1_id}', json=update_payload, headers=headers_mentor1)
        assert resp_o.status_code == 200, f"Expected 200, got {resp_o.status_code}"
        data_o = resp_o.get_json()
        assert data_o.get("status") == "success"
        sess_updated = data_o.get("session", {})
        assert sess_updated.get("title") == "Advanced Python & Architecture Discussion"
        assert sess_updated.get("scheduled_date") == "2026-10-22"
        assert "16:00" in sess_updated.get("start_time")
        assert "17:30" in sess_updated.get("end_time")
        print("  -> PASSED: Mentor successfully updated session title, date, and time")

        # -------------------------------------------------------------
        # P. Unauthorized Participant Cannot Update Session (403)
        # -------------------------------------------------------------
        print("\n[TEST P] Testing Unauthorized Session Update (403)...")
        resp_p = client.put(f'/api/sessions/{session1_id}', json={"title": "Hacked Title"}, headers=headers_mentor2)
        assert resp_p.status_code == 403, f"Expected 403, got {resp_p.status_code}"
        print("  -> PASSED: Unauthorized user blocked from updating session (403)")

        # -------------------------------------------------------------
        # Q & R. Cancellation via DELETE /api/sessions/<id>
        # -------------------------------------------------------------
        print("\n[TEST Q & R] Testing Session Cancellation & Authorization...")
        # Unauthorized cancel attempt
        resp_r_unauth = client.delete(f'/api/sessions/{session1_id}', headers=headers_unrelated)
        assert resp_r_unauth.status_code == 403, f"Expected 403, got {resp_r_unauth.status_code}"

        # Authorized cancel by Mentee
        resp_r = client.delete(f'/api/sessions/{session1_id}', headers=headers_mentee1)
        assert resp_r.status_code == 200, f"Expected 200, got {resp_r.status_code}"
        data_r = resp_r.get_json()
        assert data_r.get("status") == "success"
        assert data_r.get("session", {}).get("status") == "cancelled"

        # Verify status is persisted as cancelled
        resp_check = client.get(f'/api/sessions/{session1_id}', headers=headers_mentor1)
        assert resp_check.status_code == 200
        assert resp_check.get_json().get("session", {}).get("status") == "cancelled"
        print("  -> PASSED: Session cancelled successfully and status persisted as 'cancelled'")

    except Exception as e:
        print(f"\n[ERROR DURING TESTS]: {e}")
        raise e

    finally:
        # -------------------------------------------------------------
        # CLEANUP: Remove all temporary test users, requests, and sessions
        # -------------------------------------------------------------
        print("\n[CLEANUP] Cleaning up all temporary test records...")
        cleanup_data()
        with app.app_context():
            rem = User.query.filter(User.email.in_(all_test_emails)).count()
            print(f"  -> PASSED: All temporary test records removed cleanly ({rem} remaining)")

    # -------------------------------------------------------------
    # T. Database Schema Integrity Check (all 14 tables)
    # -------------------------------------------------------------
    print("\n[TEST T] Verifying all 14 database tables remain intact...")
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
        print(f"  -> PASSED: All 14 expected tables present in MySQL: {sorted(list(existing_tables))}")

    print("=" * 65)
    print("ALL PHASE 6 SESSIONS & JITSI TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == '__main__':
    run_tests()
