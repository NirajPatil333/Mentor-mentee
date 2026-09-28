"""
Comprehensive test suite for Phase 4:
Profiles, Skills, Availability, Learning Interests, and Mentor Matching.
"""

import sys
from app import create_app, db
from models import (
    User, MenteeProfile, MentorProfile, Skill,
    UserSkill, LearningInterest, MentorAvailability
)
from sqlalchemy import inspect


def run_phase4_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING PHASE 4: PROFILES, SKILLS, AVAILABILITY & MATCHING TESTS")
    print("=" * 65)

    test_mentee_email = "test_phase4_mentee@example.com"
    test_mentor1_email = "test_phase4_mentor1@example.com"
    test_mentor2_email = "test_phase4_mentor2@example.com"

    # Pre-test cleanup
    with app.app_context():
        emails = [test_mentee_email, test_mentor1_email, test_mentor2_email]
        test_users = User.query.filter(User.email.in_(emails)).all()
        for u in test_users:
            mp = MenteeProfile.query.filter_by(user_id=u.id).first()
            if mp:
                LearningInterest.query.filter_by(mentee_id=mp.id).delete()
                db.session.delete(mp)
            mprof = MentorProfile.query.filter_by(user_id=u.id).first()
            if mprof:
                MentorAvailability.query.filter_by(mentor_id=mprof.id).delete()
                db.session.delete(mprof)
            UserSkill.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()

    # -------------------------------------------------------------
    # 14. Health check check
    # -------------------------------------------------------------
    print("\n[TEST 14] Checking GET /api/health...")
    resp = client.get('/api/health')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    print("  -> PASSED: /api/health returned 200 OK")

    # -------------------------------------------------------------
    # Setup: Register test mentee and 2 test mentors
    # -------------------------------------------------------------
    print("\n[SETUP] Registering test mentee and mentors...")
    resp = client.post('/api/auth/register', json={
        "name": "Phase4 Mentee",
        "email": test_mentee_email,
        "password": "Password123!",
        "role": "mentee"
    })
    assert resp.status_code == 201

    resp = client.post('/api/auth/register', json={
        "name": "Phase4 Mentor Alpha",
        "email": test_mentor1_email,
        "password": "Password123!",
        "role": "mentor"
    })
    assert resp.status_code == 201

    resp = client.post('/api/auth/register', json={
        "name": "Phase4 Mentor Beta",
        "email": test_mentor2_email,
        "password": "Password123!",
        "role": "mentor"
    })
    assert resp.status_code == 201

    # Login to obtain JWT tokens
    resp = client.post('/api/auth/login', json={"email": test_mentee_email, "password": "Password123!"})
    mentee_token = resp.get_json()["access_token"]
    mentee_headers = {"Authorization": f"Bearer {mentee_token}"}

    resp = client.post('/api/auth/login', json={"email": test_mentor1_email, "password": "Password123!"})
    mentor1_token = resp.get_json()["access_token"]
    mentor1_headers = {"Authorization": f"Bearer {mentor1_token}"}

    resp = client.post('/api/auth/login', json={"email": test_mentor2_email, "password": "Password123!"})
    mentor2_token = resp.get_json()["access_token"]
    mentor2_headers = {"Authorization": f"Bearer {mentor2_token}"}
    print("  -> Setup complete. JWT tokens acquired.")

    # -------------------------------------------------------------
    # 4. Skills can be retrieved
    # -------------------------------------------------------------
    print("\n[TEST 4] Retrieving skills catalog (GET /api/skills)...")
    resp = client.get('/api/skills')
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    skills_data = resp.get_json()
    assert skills_data.get("status") == "success"
    assert "skills" in skills_data
    assert len(skills_data["skills"]) >= 2
    skill1_id = skills_data["skills"][0]["id"]
    skill2_id = skills_data["skills"][1]["id"]
    print(f"  -> PASSED: Found {len(skills_data['skills'])} skills. Testing with Skill IDs: {skill1_id}, {skill2_id}")

    # -------------------------------------------------------------
    # 1. Authenticated mentee can create/update/get own profile
    # -------------------------------------------------------------
    print("\n[TEST 1] Testing Mentee Profile API (PUT & GET /api/mentees/profile)...")
    put_payload = {
        "bio": "Aspiring full-stack engineer and cloud enthusiast.",
        "education": "BS in Computer Science",
        "learning_goal": "Master backend architecture and scalable systems",
        "experience_level": "intermediate"
    }
    resp = client.put('/api/mentees/profile', json=put_payload, headers=mentee_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    put_data = resp.get_json()
    assert put_data["status"] == "success"
    assert put_data["profile"]["bio"] == put_payload["bio"]

    resp = client.get('/api/mentees/profile', headers=mentee_headers)
    assert resp.status_code == 200
    get_data = resp.get_json()
    assert get_data["profile"]["bio"] == put_payload["bio"]
    assert get_data["profile"]["experience_level"] == "intermediate"
    print("  -> PASSED: Mentee profile updated and retrieved successfully.")

    # -------------------------------------------------------------
    # 2. Authenticated mentor can create/update/get own profile
    # -------------------------------------------------------------
    print("\n[TEST 2] Testing Mentor Profile API (PUT & GET /api/mentors/profile)...")
    mentor_payload = {
        "bio": "Principal Software Engineer with 8 years in distributed systems.",
        "experience_years": 8,
        "education": "MS in Software Engineering",
        "current_position": "Staff Engineer at TechCorp",
        "availability_status": "available"
    }
    resp = client.put('/api/mentors/profile', json=mentor_payload, headers=mentor1_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    put_mentor_data = resp.get_json()
    assert put_mentor_data["status"] == "success"
    assert put_mentor_data["profile"]["experience_years"] == 8

    resp = client.get('/api/mentors/profile', headers=mentor1_headers)
    assert resp.status_code == 200
    get_mentor_data = resp.get_json()
    assert get_mentor_data["profile"]["current_position"] == "Staff Engineer at TechCorp"
    print("  -> PASSED: Mentor profile updated and retrieved successfully.")

    # -------------------------------------------------------------
    # 3. Wrong role is rejected
    # -------------------------------------------------------------
    print("\n[TEST 3] Testing Role Boundary Rejection...")
    # Mentor accessing mentee profile -> 403
    resp = client.get('/api/mentees/profile', headers=mentor1_headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    resp = client.put('/api/mentees/profile', json={"bio": "hacked"}, headers=mentor1_headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"

    # Mentee accessing mentor profile -> 403
    resp = client.get('/api/mentors/profile', headers=mentee_headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    resp = client.put('/api/mentors/profile', json={"bio": "hacked"}, headers=mentee_headers)
    assert resp.status_code == 403, f"Expected 403, got {resp.status_code}"
    print("  -> PASSED: Mentor blocked from Mentee routes (403), Mentee blocked from Mentor routes (403).")

    # -------------------------------------------------------------
    # 5. Mentor can set/get skills
    # -------------------------------------------------------------
    print("\n[TEST 5] Testing Mentor Skills (PUT & GET /api/mentors/skills)...")
    skills_payload = {
        "skills": [
            {"skill_id": skill1_id, "proficiency": "advanced"},
            {"skill_id": skill2_id, "proficiency": "intermediate"}
        ]
    }
    resp = client.put('/api/mentors/skills', json=skills_payload, headers=mentor1_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    resp = client.get('/api/mentors/skills', headers=mentor1_headers)
    assert resp.status_code == 200
    m_skills = resp.get_json()
    assert len(m_skills["skills"]) == 2
    assert m_skills["skills"][0]["proficiency"] in ["advanced", "intermediate"]
    print("  -> PASSED: Mentor skills configured and retrieved successfully.")

    # -------------------------------------------------------------
    # 6. Mentee can set/get learning interests
    # -------------------------------------------------------------
    print("\n[TEST 6] Testing Mentee Learning Interests (PUT & GET /api/mentees/interests)...")
    interests_payload = {
        "interests": [
            {"skill_id": skill1_id, "priority": 1},
            {"skill_id": skill2_id, "priority": 2}
        ]
    }
    resp = client.put('/api/mentees/interests', json=interests_payload, headers=mentee_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    resp = client.get('/api/mentees/interests', headers=mentee_headers)
    assert resp.status_code == 200
    m_interests = resp.get_json()
    assert len(m_interests["interests"]) == 2
    print("  -> PASSED: Mentee learning interests set and retrieved successfully.")

    # -------------------------------------------------------------
    # 7. Mentor can set/get availability
    # -------------------------------------------------------------
    print("\n[TEST 7] Testing Mentor Availability (PUT & GET /api/mentors/availability)...")
    avail_payload = {
        "availability": [
            {"day_of_week": "Monday", "start_time": "18:00", "end_time": "20:00"},
            {"day_of_week": "Wednesday", "start_time": "19:00", "end_time": "21:00"}
        ]
    }
    resp = client.put('/api/mentors/availability', json=avail_payload, headers=mentor1_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"

    resp = client.get('/api/mentors/availability', headers=mentor1_headers)
    assert resp.status_code == 200
    m_avail = resp.get_json()
    assert len(m_avail["availability"]) == 2
    print("  -> PASSED: Mentor availability slots saved and retrieved successfully.")

    # -------------------------------------------------------------
    # 8. Invalid skill IDs are rejected
    # -------------------------------------------------------------
    print("\n[TEST 8] Testing Invalid Skill ID Rejection...")
    invalid_skill_payload = {
        "skills": [
            {"skill_id": 9999999, "proficiency": "expert"}
        ]
    }
    resp = client.put('/api/mentors/skills', json=invalid_skill_payload, headers=mentor1_headers)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print("  -> PASSED: Invalid skill ID correctly rejected with 400 Bad Request.")

    # -------------------------------------------------------------
    # 9. Invalid time range is rejected (start_time >= end_time)
    # -------------------------------------------------------------
    print("\n[TEST 9] Testing Invalid Time Range Rejection...")
    invalid_time_payload = {
        "availability": [
            {"day_of_week": "Monday", "start_time": "20:00", "end_time": "18:00"}  # end before start
        ]
    }
    resp = client.put('/api/mentors/availability', json=invalid_time_payload, headers=mentor1_headers)
    assert resp.status_code == 400, f"Expected 400, got {resp.status_code}"
    print("  -> PASSED: Invalid time window (start >= end) correctly rejected with 400 Bad Request.")

    # Configure Mentor 2 with 0 overlapping skills & 1 year experience for ranking test
    client.put('/api/mentors/profile', json={
        "bio": "Junior mentor",
        "experience_years": 1,
        "current_position": "Associate Engineer"
    }, headers=mentor2_headers)

    # -------------------------------------------------------------
    # 10. Mentee can retrieve mentor recommendations
    # 11. Recommendations contain match score and breakdown
    # 12. Mentors are ordered by match score
    # -------------------------------------------------------------
    print("\n[TEST 10, 11, 12] Testing Mentor Recommendations & Scoring...")
    resp = client.get('/api/mentors/recommendations', headers=mentee_headers)
    assert resp.status_code == 200, f"Expected 200, got {resp.status_code}"
    rec_data = resp.get_json()
    assert rec_data.get("status") == "success"
    recs = rec_data.get("recommendations", [])
    assert len(recs) >= 2, f"Expected at least 2 mentors in recommendations, got {len(recs)}"

    print(f"  Found {len(recs)} recommended mentors.")
    for idx, r in enumerate(recs):
        print(f"    Rank {idx+1}: {r['mentor']['name']} (ID: {r['mentor']['id']}) - Score: {r['match_score']}%")
        print(f"      Breakdown: {r['breakdown']}")
        # Verify breakdown keys exist
        assert "skill_match" in r["breakdown"]
        assert "experience" in r["breakdown"]
        assert "rating" in r["breakdown"]
        assert "availability" in r["breakdown"]

    # Verify descending ordering
    scores = [r["match_score"] for r in recs]
    assert scores == sorted(scores, reverse=True), f"Recommendations not sorted descending by score: {scores}"

    # Verify mentor 1 has higher match score than mentor 2 because mentor 1 has 100% skill overlap + 8 yrs exp
    mentor1_rec = next(r for r in recs if r["mentor"]["name"] == "Phase4 Mentor Alpha")
    mentor2_rec = next(r for r in recs if r["mentor"]["name"] == "Phase4 Mentor Beta")
    assert mentor1_rec["match_score"] > mentor2_rec["match_score"]
    assert mentor1_rec["breakdown"]["skill_match"] == 100.0
    print("  -> PASSED: Recommendations calculated, breakdown verified, and sorted descending.")

    # -------------------------------------------------------------
    # 13. Unauthenticated requests are rejected
    # -------------------------------------------------------------
    print("\n[TEST 13] Testing Unauthenticated Rejection (401)...")
    assert client.get('/api/mentees/profile').status_code == 401
    assert client.put('/api/mentees/profile', json={}).status_code == 401
    assert client.get('/api/mentors/profile').status_code == 401
    assert client.put('/api/mentors/profile', json={}).status_code == 401
    assert client.get('/api/mentors/skills').status_code == 401
    assert client.get('/api/mentees/interests').status_code == 401
    assert client.get('/api/mentors/availability').status_code == 401
    assert client.get('/api/mentors/recommendations').status_code == 401
    print("  -> PASSED: All protected endpoints correctly return 401 without JWT token.")

    # -------------------------------------------------------------
    # Cleanup Temporary Test Data
    # -------------------------------------------------------------
    print("\n[CLEANUP] Cleaning up temporary test users and associated rows...")
    with app.app_context():
        emails = [test_mentee_email, test_mentor1_email, test_mentor2_email]
        test_users = User.query.filter(User.email.in_(emails)).all()
        for u in test_users:
            mp = MenteeProfile.query.filter_by(user_id=u.id).first()
            if mp:
                LearningInterest.query.filter_by(mentee_id=mp.id).delete()
                db.session.delete(mp)
            mprof = MentorProfile.query.filter_by(user_id=u.id).first()
            if mprof:
                MentorAvailability.query.filter_by(mentor_id=mprof.id).delete()
                db.session.delete(mprof)
            UserSkill.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()

        remaining = User.query.filter(User.email.in_(emails)).count()
        assert remaining == 0, f"Cleanup incomplete: {remaining} test users remain"
        print("  -> PASSED: All temporary test records removed cleanly (0 remaining).")

    # -------------------------------------------------------------
    # 15. Existing 14 database tables remain intact
    # -------------------------------------------------------------
    print("\n[TEST 15] Verifying all 14 database tables remain intact...")
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
        print(f"  -> PASSED: All {len(expected_tables)} tables present in MySQL: {sorted(list(expected_tables))}")

    print("\n" + "=" * 65)
    print("ALL 15 TESTS + CLEANUP + SCHEMA VERIFICATION PASSED SUCCESSFULLY!")
    print("=" * 65)
    return True


if __name__ == '__main__':
    success = run_phase4_tests()
    sys.exit(0 if success else 1)
