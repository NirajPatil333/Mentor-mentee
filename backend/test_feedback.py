"""
Test suite for Feedback and Rating system.
Covers authentication, role restrictions, session ownership, duplicate feedback prevention,
rating validation (1-5), mentor average rating and review count recalculation,
mentor rating visibility, mentee feedback listing, and isolation.
"""

import sys
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest, Session, Feedback
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING FEEDBACK & RATING FEATURE TESTS")
    print("=" * 65)

    test_mentee1_email = "test_feedback_mentee1@example.com"
    test_mentee2_email = "test_feedback_mentee2@example.com"
    test_mentor1_email = "test_feedback_mentor1@example.com"
    test_password = "Password123!"

    # 0. Pre-test cleanup
    with app.app_context():
        users = User.query.filter(User.email.in_([
            test_mentee1_email, test_mentee2_email, test_mentor1_email
        ])).all()
        for u in users:
            m_prof = MentorProfile.query.filter_by(user_id=u.id).first()
            if m_prof:
                Feedback.query.filter_by(mentor_id=m_prof.id).delete()
                Session.query.filter_by(mentor_id=m_prof.id).delete()
                MentorshipRequest.query.filter_by(mentor_id=m_prof.id).delete()
                db.session.delete(m_prof)

            e_prof = MenteeProfile.query.filter_by(user_id=u.id).first()
            if e_prof:
                Feedback.query.filter_by(mentee_id=e_prof.id).delete()
                Session.query.filter_by(mentee_id=e_prof.id).delete()
                MentorshipRequest.query.filter_by(mentee_id=e_prof.id).delete()
                db.session.delete(e_prof)

            db.session.delete(u)
        db.session.commit()

    # 1. Unauthenticated request -> 401
    print("\n[TEST 1] Testing Unauthenticated Rejections (401)...")
    resp_post = client.post('/api/feedback', json={"session_id": 1, "rating": 5})
    assert resp_post.status_code == 401, f"Expected 401, got {resp_post.status_code}"

    resp_mentee = client.get('/api/feedback/mentee')
    assert resp_mentee.status_code == 401, f"Expected 401, got {resp_mentee.status_code}"

    resp_mentor = client.get('/api/feedback/mentor')
    assert resp_mentor.status_code == 401, f"Expected 401, got {resp_mentor.status_code}"
    print("  -> PASSED: All feedback endpoints require JWT authentication (401)")

    # 2. Register test users & set up session
    print("\n[TEST 2] Registering test mentee 1, mentee 2, and mentor...")
    resp = client.post('/api/auth/register', json={
        "name": "Feedback Mentee One", "email": test_mentee1_email, "password": test_password, "role": "mentee"
    })
    assert resp.status_code == 201
    resp = client.post('/api/auth/register', json={
        "name": "Feedback Mentee Two", "email": test_mentee2_email, "password": test_password, "role": "mentee"
    })
    assert resp.status_code == 201
    resp = client.post('/api/auth/register', json={
        "name": "Feedback Mentor Alpha", "email": test_mentor1_email, "password": test_password, "role": "mentor"
    })
    assert resp.status_code == 201

    t_m1 = client.post('/api/auth/login', json={"email": test_mentee1_email, "password": test_password}).get_json()["access_token"]
    t_m2 = client.post('/api/auth/login', json={"email": test_mentee2_email, "password": test_password}).get_json()["access_token"]
    t_mentor = client.post('/api/auth/login', json={"email": test_mentor1_email, "password": test_password}).get_json()["access_token"]

    h_m1 = {"Authorization": f"Bearer {t_m1}"}
    h_m2 = {"Authorization": f"Bearer {t_m2}"}
    h_mentor = {"Authorization": f"Bearer {t_mentor}"}

    with app.app_context():
        user_m1 = User.query.filter_by(email=test_mentee1_email).first()
        user_m2 = User.query.filter_by(email=test_mentee2_email).first()
        user_mentor = User.query.filter_by(email=test_mentor1_email).first()

        prof_m1 = MenteeProfile.query.filter_by(user_id=user_m1.id).first()
        prof_m2 = MenteeProfile.query.filter_by(user_id=user_m2.id).first()
        prof_mentor = MentorProfile.query.filter_by(user_id=user_mentor.id).first()

        req1 = MentorshipRequest(mentee_id=prof_m1.id, mentor_id=prof_mentor.id, status='accepted')
        db.session.add(req1)
        req2 = MentorshipRequest(mentee_id=prof_m2.id, mentor_id=prof_mentor.id, status='accepted')
        db.session.add(req2)
        db.session.flush()

        sess1 = Session(
            request_id=req1.id, mentor_id=prof_mentor.id, mentee_id=prof_m1.id,
            title="Session 1: Python Basics", scheduled_date="2026-10-20",
            start_time="10:00:00", end_time="11:00:00", status="completed"
        )
        sess2 = Session(
            request_id=req1.id, mentor_id=prof_mentor.id, mentee_id=prof_m1.id,
            title="Session 2: Flask Routing", scheduled_date="2026-10-21",
            start_time="10:00:00", end_time="11:00:00", status="completed"
        )
        sess3 = Session(
            request_id=req2.id, mentor_id=prof_mentor.id, mentee_id=prof_m2.id,
            title="Session 3: Database Models", scheduled_date="2026-10-22",
            start_time="10:00:00", end_time="11:00:00", status="completed"
        )
        db.session.add_all([sess1, sess2, sess3])
        db.session.commit()

        sess1_id = sess1.id
        sess2_id = sess2.id
        sess3_id = sess3.id
        mentor_prof_id = prof_mentor.id

    print("  -> PASSED: Test users, profiles, and 3 sessions initialized successfully")

    # 3. Role restrictions: Mentor submitting feedback -> 403
    print("\n[TEST 3] Testing Role Protection (Mentor submitting feedback -> 403)...")
    resp = client.post('/api/feedback', headers=h_mentor, json={
        "session_id": sess1_id, "rating": 5, "comment": "Great session"
    })
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"

    resp_m = client.get('/api/feedback/mentor', headers=h_m1)
    assert resp_m.status_code == 403, f"Expected 403, got {resp_m.status_code}"

    resp_m2 = client.get('/api/feedback/mentee', headers=h_mentor)
    assert resp_m2.status_code == 403, f"Expected 403, got {resp_m2.status_code}"
    print("  -> PASSED: Mentor submitting feedback and role boundaries correctly return 403 Forbidden")

    # 4. Session ownership restriction: Mentee 1 attempting to rate Mentee 2's session -> 403
    print("\n[TEST 4] Testing Session Ownership Protection (Mentee 1 rating Mentee 2's session -> 403)...")
    resp = client.post('/api/feedback', headers=h_m1, json={
        "session_id": sess3_id, "rating": 5, "comment": "Trying to rate session 3"
    })
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    print("  -> PASSED: Unassociated mentee blocked from rating another mentee's session with 403")

    # 5. Rating Validation (<1 or >5 or non-integer) -> 400
    print("\n[TEST 5] Testing Rating Validation (<1, >5, non-integer -> 400)...")
    for bad_rating in [0, 6, -1, 10, "five", 4.5, True]:
        resp = client.post('/api/feedback', headers=h_m1, json={
            "session_id": sess1_id, "rating": bad_rating, "comment": "Invalid rating test"
        })
        assert resp.status_code == 400, f"Expected 400 for rating={bad_rating}, got {resp.status_code}"
    print("  -> PASSED: Invalid ratings (<1, >5, float/bool/str) correctly rejected with 400 Bad Request")

    # 6. Valid Feedback Submission 1 -> 201
    print("\n[TEST 6] Testing Valid Feedback Submission (Mentee 1 rates Session 1 with 5 stars)...")
    resp = client.post('/api/feedback', headers=h_m1, json={
        "session_id": sess1_id, "rating": 5, "comment": "Outstanding session! Highly recommended."
    })
    assert resp.status_code == 201, f"Expected 201, got {resp.status_code}: {resp.get_json()}"
    data = resp.get_json()
    assert data["status"] == "success"
    assert data["feedback"]["rating"] == 5
    print("  -> PASSED: Mentee 1 submitted 5-star feedback for Session 1")

    # Verify Mentor average rating updated to 5.0 and total_reviews = 1
    with app.app_context():
        mp = db.session.get(MentorProfile, mentor_prof_id)
        assert mp.total_reviews == 1, f"Expected total_reviews 1, got {mp.total_reviews}"
        assert mp.average_rating == 5.0, f"Expected average_rating 5.0, got {mp.average_rating}"
    print("  -> PASSED: Mentor profile metrics updated: rating=5.0, total_reviews=1")

    # 7. Duplicate Feedback Prevention -> 400
    print("\n[TEST 7] Testing Duplicate Feedback Prevention (Mentee 1 rating Session 1 again -> 400)...")
    resp_dup = client.post('/api/feedback', headers=h_m1, json={
        "session_id": sess1_id, "rating": 4, "comment": "Duplicate attempt"
    })
    assert resp_dup.status_code == 400, f"Expected 400 for duplicate, got {resp_dup.status_code}"
    print("  -> PASSED: Duplicate feedback submission correctly rejected with 400 Bad Request")

    # 8. Valid Submissions 2 & 3 & Recalculate Average Rating
    print("\n[TEST 8] Testing Multiple Feedbacks & Average Rating Calculation (5, 4, 3 -> avg 4.0, total 3)...")
    resp2 = client.post('/api/feedback', headers=h_m1, json={
        "session_id": sess2_id, "rating": 4, "comment": "Solid session on Flask."
    })
    assert resp2.status_code == 201

    resp3 = client.post('/api/feedback', headers=h_m2, json={
        "session_id": sess3_id, "rating": 3, "comment": "Good overview."
    })
    assert resp3.status_code == 201

    with app.app_context():
        mp = db.session.get(MentorProfile, mentor_prof_id)
        assert mp.total_reviews == 3, f"Expected total_reviews 3, got {mp.total_reviews}"
        assert mp.average_rating == 4.0, f"Expected average_rating 4.0, got {mp.average_rating}"
    print("  -> PASSED: Recalculated mentor metrics: average_rating=4.0, total_reviews=3 (ratings: 5, 4, 3)")

    # 9. Mentor Ratings Listing (GET /api/feedback/mentor)
    print("\n[TEST 9] Testing Mentor Received Ratings List (GET /api/feedback/mentor)...")
    resp_mentor_list = client.get('/api/feedback/mentor', headers=h_mentor)
    assert resp_mentor_list.status_code == 200
    m_data = resp_mentor_list.get_json()
    assert m_data["status"] == "success"
    assert m_data["average_rating"] == 4.0
    assert m_data["total_reviews"] == 3
    assert len(m_data["feedbacks"]) == 3

    first_fb = m_data["feedbacks"][0]
    assert "mentee_name" in first_fb
    assert "rating" in first_fb
    assert "comment" in first_fb
    assert "session_title" in first_fb
    assert "session_date" in first_fb
    assert "created_at" in first_fb
    print("  -> PASSED: Mentor successfully retrieved received ratings with mentee and session details")

    # 10. Mentee Feedback Listing & Isolation (GET /api/feedback/mentee)
    print("\n[TEST 10] Testing Mentee Submitted Feedback Listing & Isolation (GET /api/feedback/mentee)...")
    resp_mentee1 = client.get('/api/feedback/mentee', headers=h_m1)
    assert resp_mentee1.status_code == 200
    m1_feedbacks = resp_mentee1.get_json()["feedbacks"]
    assert len(m1_feedbacks) == 2, f"Mentee 1 expected 2 feedbacks, got {len(m1_feedbacks)}"

    resp_mentee2 = client.get('/api/feedback/mentee', headers=h_m2)
    assert resp_mentee2.status_code == 200
    m2_feedbacks = resp_mentee2.get_json()["feedbacks"]
    assert len(m2_feedbacks) == 1, f"Mentee 2 expected 1 feedback, got {len(m2_feedbacks)}"
    print("  -> PASSED: Mentee 1 sees 2 feedbacks, Mentee 2 sees 1 feedback (strict isolation confirmed)")

    # 11. Database Cleanup
    print("\n[CLEANUP] Cleaning up temporary test records...")
    with app.app_context():
        users = User.query.filter(User.email.in_([
            test_mentee1_email, test_mentee2_email, test_mentor1_email
        ])).all()
        for u in users:
            m_prof = MentorProfile.query.filter_by(user_id=u.id).first()
            if m_prof:
                Feedback.query.filter_by(mentor_id=m_prof.id).delete()
                Session.query.filter_by(mentor_id=m_prof.id).delete()
                MentorshipRequest.query.filter_by(mentor_id=m_prof.id).delete()
                db.session.delete(m_prof)

            e_prof = MenteeProfile.query.filter_by(user_id=u.id).first()
            if e_prof:
                Feedback.query.filter_by(mentee_id=e_prof.id).delete()
                Session.query.filter_by(mentee_id=e_prof.id).delete()
                MentorshipRequest.query.filter_by(mentee_id=e_prof.id).delete()
                db.session.delete(e_prof)

            db.session.delete(u)
        db.session.commit()
    print("  -> PASSED: Temporary test records removed cleanly")

    # 12. Verify Schema Integrity
    print("\n[TEST SCHEMA] Verifying database schema integrity...")
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        expected_tables = [
            'achievements', 'certificates', 'feedback', 'learning_interests',
            'mentee_profiles', 'mentor_availability', 'mentor_profiles',
            'mentorship_requests', 'progress', 'resources', 'sessions',
            'skills', 'user_skills', 'users'
        ]
        for t in expected_tables:
            assert t in tables, f"Missing expected table: {t}"
        assert len(tables) >= 14, f"Expected at least 14 tables, found {len(tables)}"
    print(f"  -> PASSED: All {len(expected_tables)} expected tables present in database: {sorted(tables)}")

    print("\n" + "=" * 65)
    print("ALL FEEDBACK & RATING FEATURE TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == '__main__':
    run_tests()
