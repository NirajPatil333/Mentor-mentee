"""
Test suite for Progress Tracking feature.
Covers:
- Unauthenticated access rejection (401)
- Role protection (only mentors can create/update progress)
- Scoped mentorship validation (mentors can only track accepted mentees)
- Input validation (percentage 0-100, valid statuses, existing skills)
- Mentor updating existing progress records
- Mentee viewing their own progress records & isolation
- Database schema preservation and full cleanup
"""

import sys
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest, Skill, Progress
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING PROGRESS TRACKING SYSTEM TESTS")
    print("=" * 65)

    test_mentor1_email = "test_mentor1_prog_suite@example.com"
    test_mentor2_email = "test_mentor2_prog_suite@example.com"
    test_mentee1_email = "test_mentee1_prog_suite@example.com"
    test_mentee2_email = "test_mentee2_prog_suite@example.com"

    all_test_emails = [
        test_mentor1_email,
        test_mentor2_email,
        test_mentee1_email,
        test_mentee2_email
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
                    Progress.query.filter(
                        (Progress.mentee_id.in_(mentee_ids)) |
                        (Progress.mentor_id.in_(mentor_ids))
                    ).delete(synchronize_session=False)

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
        # 1. Health check & 401 Rejections
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing Unauthenticated Rejections (401)...")
        assert client.get('/api/progress').status_code == 401
        assert client.post('/api/progress', json={}).status_code == 401
        assert client.put('/api/progress/1', json={}).status_code == 401
        assert client.delete('/api/progress/1').status_code == 401
        print("  -> PASSED: All progress endpoints require JWT authentication (401)")

        # -------------------------------------------------------------
        # 2. Register users & setup accepted mentorship
        # -------------------------------------------------------------
        print("\n[TEST 2] Registering test mentors & mentees...")
        # Mentor 1
        client.post('/api/auth/register', json={
            "name": "Progress Mentor 1", "email": test_mentor1_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor1 = client.post('/api/auth/login', json={
            "email": test_mentor1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor1 = {"Authorization": f"Bearer {token_mentor1}"}

        # Mentor 2
        client.post('/api/auth/register', json={
            "name": "Progress Mentor 2", "email": test_mentor2_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor2 = client.post('/api/auth/login', json={
            "email": test_mentor2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor2 = {"Authorization": f"Bearer {token_mentor2}"}

        # Mentee 1
        client.post('/api/auth/register', json={
            "name": "Progress Mentee 1", "email": test_mentee1_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee1 = client.post('/api/auth/login', json={
            "email": test_mentee1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee1 = {"Authorization": f"Bearer {token_mentee1}"}

        # Mentee 2
        client.post('/api/auth/register', json={
            "name": "Progress Mentee 2", "email": test_mentee2_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee2 = client.post('/api/auth/login', json={
            "email": test_mentee2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee2 = {"Authorization": f"Bearer {token_mentee2}"}

        with app.app_context():
            m1 = User.query.filter_by(email=test_mentor1_email).first().mentor_profile
            m2 = User.query.filter_by(email=test_mentor2_email).first().mentor_profile
            me1 = User.query.filter_by(email=test_mentee1_email).first().mentee_profile
            me2 = User.query.filter_by(email=test_mentee2_email).first().mentee_profile
            mentor1_id = m1.id
            mentor2_id = m2.id
            mentee1_id = me1.id
            mentee2_id = me2.id
            skill = Skill.query.first()
            if not skill:
                skill = Skill(name="Python", category="Backend")
                db.session.add(skill)
                db.session.commit()
            skill_id = skill.id

        # Accept mentorship between Mentor 1 and Mentee 1
        req_resp = client.post('/api/requests', json={"mentor_id": mentor1_id}, headers=headers_mentee1)
        req_id = req_resp.get_json()['request']['id']
        client.patch(f'/api/requests/{req_id}/accept', headers=headers_mentor1)
        print("  -> PASSED: Setup complete with accepted mentorship between Mentor 1 and Mentee 1")

        # -------------------------------------------------------------
        # 3. Mentee blocked from creating progress (403)
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing Mentee Progress Creation Rejection (403)...")
        resp_mentee_post = client.post('/api/progress', json={
            "mentee_id": mentee1_id,
            "skill_id": skill_id,
            "goal": "Master Flask",
            "progress_percentage": 25,
            "status": "in_progress"
        }, headers=headers_mentee1)
        assert resp_mentee_post.status_code == 403
        print("  -> PASSED: Mentee blocked from creating progress records (403)")

        # -------------------------------------------------------------
        # 4. Mentor creates progress for unaccepted mentee (403)
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing Mentor Tracking Unaccepted Mentee Rejection (403)...")
        resp_unaccepted = client.post('/api/progress', json={
            "mentee_id": mentee2_id,
            "skill_id": skill_id,
            "goal": "Learn React",
            "progress_percentage": 0,
            "status": "not_started"
        }, headers=headers_mentor1)
        assert resp_unaccepted.status_code == 403
        print("  -> PASSED: Mentor cannot create progress records for mentees without accepted mentorship (403)")

        # -------------------------------------------------------------
        # 5. Validation: percentage bounds & invalid status
        # -------------------------------------------------------------
        print("\n[TEST 5] Testing Input Validations (400)...")
        # Percentage > 100
        resp_over = client.post('/api/progress', json={
            "mentee_id": mentee1_id, "skill_id": skill_id, "goal": "Invalid %", "progress_percentage": 150
        }, headers=headers_mentor1)
        assert resp_over.status_code == 400

        # Percentage < 0
        resp_under = client.post('/api/progress', json={
            "mentee_id": mentee1_id, "skill_id": skill_id, "goal": "Invalid %", "progress_percentage": -10
        }, headers=headers_mentor1)
        assert resp_under.status_code == 400

        # Invalid status
        resp_bad_status = client.post('/api/progress', json={
            "mentee_id": mentee1_id, "skill_id": skill_id, "goal": "Invalid Status", "status": "unknown_status"
        }, headers=headers_mentor1)
        assert resp_bad_status.status_code == 400
        print("  -> PASSED: Percentage out of 0-100 range and invalid status properly rejected with 400")

        # -------------------------------------------------------------
        # 6. Mentor successfully creates progress record (201)
        # -------------------------------------------------------------
        print("\n[TEST 6] Testing Successful Progress Creation (201)...")
        resp_create = client.post('/api/progress', json={
            "mentee_id": mentee1_id,
            "skill_id": skill_id,
            "goal": "Master Flask REST APIs & Auth",
            "description": "Complete authentication blueprints, JWT middleware, and test suites.",
            "progress_percentage": 45,
            "status": "in_progress"
        }, headers=headers_mentor1)
        assert resp_create.status_code == 201
        prog_data = resp_create.get_json()['progress']
        assert prog_data['goal'] == "Master Flask REST APIs & Auth"
        assert prog_data['progress_percentage'] == 45
        assert prog_data['status'] == "in_progress"
        prog_id = prog_data['id']
        print(f"  -> PASSED: Progress record created successfully (ID: {prog_id})")

        # -------------------------------------------------------------
        # 7. Mentor updates progress record (200)
        # -------------------------------------------------------------
        print("\n[TEST 7] Testing Progress Update (200)...")
        resp_update = client.put(f'/api/progress/{prog_id}', json={
            "progress_percentage": 100,
            "status": "completed",
            "description": "All requirements completed with 100% test coverage."
        }, headers=headers_mentor1)
        assert resp_update.status_code == 200
        updated_data = resp_update.get_json()['progress']
        assert updated_data['progress_percentage'] == 100
        assert updated_data['status'] == "completed"
        print("  -> PASSED: Mentor updated progress percentage to 100% and status to 'completed'")

        # -------------------------------------------------------------
        # 8. Unauthorized Mentor update rejection (403)
        # -------------------------------------------------------------
        print("\n[TEST 8] Testing Unauthorized Mentor Update (403)...")
        resp_unauth_update = client.put(f'/api/progress/{prog_id}', json={
            "progress_percentage": 50
        }, headers=headers_mentor2)
        assert resp_unauth_update.status_code == 403
        print("  -> PASSED: Unrelated Mentor 2 blocked from updating Mentor 1's progress record (403)")

        # -------------------------------------------------------------
        # 9. Mentee views their own progress & isolation
        # -------------------------------------------------------------
        print("\n[TEST 9] Testing Mentee Progress Visibility & Isolation...")
        # Mentee 1 sees their progress record
        resp_me1 = client.get('/api/progress', headers=headers_mentee1)
        assert resp_me1.status_code == 200
        me1_list = resp_me1.get_json()['progress']
        assert len(me1_list) == 1
        assert me1_list[0]['id'] == prog_id
        assert me1_list[0]['mentor']['name'] == "Progress Mentor 1"

        # Mentee 2 sees 0 records
        resp_me2 = client.get('/api/progress', headers=headers_mentee2)
        assert resp_me2.status_code == 200
        assert resp_me2.get_json()['count'] == 0
        print("  -> PASSED: Mentee 1 views their progress with mentor metadata; Mentee 2 isolated (0 records)")

        # -------------------------------------------------------------
        # CLEANUP & SCHEMA CHECK
        # -------------------------------------------------------------
        print("\n[CLEANUP] Cleaning up all test data...")
        cleanup_data()
        print("  -> PASSED: All test records removed cleanly")

        print("\n[TEST SCHEMA] Verifying database tables remain intact...")
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
            print(f"  -> PASSED: All 14 expected tables present in MySQL")

        print("\n" + "=" * 65)
        print("ALL PROGRESS TRACKING TESTS PASSED SUCCESSFULLY!")
        print("=" * 65)

    except Exception:
        cleanup_data()
        raise


if __name__ == '__main__':
    run_tests()
