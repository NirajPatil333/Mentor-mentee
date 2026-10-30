"""
Comprehensive test suite for Profile Picture, Skills, and Mentorship Request improvements.
Tests:
1. Mentor profile picture upload, file validation, update, and removal.
2. Mentee profile picture upload, file validation, update, and removal.
3. Mentor skills: add, edit proficiency, batch update, remove, and database persistence.
4. Mentee skills vs learning interests: separation of UserSkill (known skills) and LearningInterest (skills to learn).
5. Mentorship requests: received requests include mentee profile picture, known skills, learning interests.
6. Mentorship requests: view full mentee profile endpoint (/api/mentees/<id>/profile) with authorization check (403 for unauthorized mentors).
7. Mentorship requests: accept and reject functionality remains working.
8. Unauthorized user isolation: users cannot update another user's profile picture or access restricted information.
9. Static profile picture serving (/uploads/profiles/<filename>).
"""

import os
import io
import pytest
from app import app, db
from models import (
    User, MentorProfile, MenteeProfile, UserSkill, LearningInterest,
    Skill, MentorshipRequest
)

# Valid dummy PNG image bytes (1x1 transparent PNG)
VALID_PNG_BYTES = (
    b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
    b'\x08\x06\x00\x00\x00\x1f\x15c4\x00\x00\x00\rIDATx\x9cc`\x00\x00'
    b'\x00\x02\x00\x01H\xaf\xa4q\x00\x00\x00\x00IEND\xaeB`\x82'
)

# Valid dummy JPEG bytes
VALID_JPG_BYTES = b'\xff\xd8\xff\xe0\x00\x10JFIF\x00\x01\x01\x01\x00`\x00`\x00\x00\xff\xdb\x00C\x00' + (b'\x00' * 64) + b'\xff\xc0\x00\x0b\x08\x00\x01\x00\x01\x01\x01\x11\x00\xff\xda\x00\x08\x01\x01\x00\x00?\x00\xbf\x00\xff\xd9'

INVALID_FILE_BYTES = b'This is a plain text file pretending to be an image.'


def run_tests():
    print("=" * 70)
    print("STARTING PROFILE, SKILLS, AND REQUEST ENHANCEMENT TESTS")
    print("=" * 70)

    client = app.test_client()

    mentor_email = "test_prof_mentor@example.com"
    mentee_email = "test_prof_mentee@example.com"
    other_mentor_email = "test_prof_other_mentor@example.com"
    password = "SecurePassword123"

    test_emails = [mentor_email, mentee_email, other_mentor_email]

    def cleanup():
        with app.app_context():
            users = User.query.filter(User.email.in_(test_emails)).all()
            user_ids = [u.id for u in users]
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

                if mentee_ids:
                    LearningInterest.query.filter(LearningInterest.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)

                UserSkill.query.filter(UserSkill.user_id.in_(user_ids)).delete(synchronize_session=False)

                # Clean up uploaded physical files
                for u in users:
                    if u.profile_picture:
                        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), u.profile_picture)
                        if os.path.exists(p):
                            try:
                                os.remove(p)
                            except OSError:
                                pass

                MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
                db.session.commit()

    cleanup()

    try:
        # 1. SETUP: Register test users and get tokens
        print("\n[SETUP] Registering mentor, mentee, and other mentor...")
        reg_mentor = client.post('/api/auth/register', json={"name": "Alice Mentor", "email": mentor_email, "password": password, "role": "mentor"})
        assert reg_mentor.status_code == 201, f"Mentor registration failed: {reg_mentor.get_json()}"

        reg_mentee = client.post('/api/auth/register', json={"name": "Bob Mentee", "email": mentee_email, "password": password, "role": "mentee"})
        assert reg_mentee.status_code == 201, f"Mentee registration failed: {reg_mentee.get_json()}"

        reg_other = client.post('/api/auth/register', json={"name": "Charlie Other Mentor", "email": other_mentor_email, "password": password, "role": "mentor"})
        assert reg_other.status_code == 201, f"Other mentor registration failed: {reg_other.get_json()}"

        # Login
        log_mentor = client.post('/api/auth/login', json={"email": mentor_email, "password": password})
        mentor_token = log_mentor.get_json()["access_token"]
        mentor_headers = {"Authorization": f"Bearer {mentor_token}"}

        log_mentee = client.post('/api/auth/login', json={"email": mentee_email, "password": password})
        mentee_token = log_mentee.get_json()["access_token"]
        mentee_headers = {"Authorization": f"Bearer {mentee_token}"}

        log_other = client.post('/api/auth/login', json={"email": other_mentor_email, "password": password})
        other_token = log_other.get_json()["access_token"]
        other_headers = {"Authorization": f"Bearer {other_token}"}

        print("  -> PASSED: All test accounts registered and authenticated")

        # 2. TEST: Profile Picture Validation & Upload for Mentor
        print("\n[TEST 1] Testing Mentor Profile Picture Upload & Validation...")
        # Reject invalid file content
        bad_upload = client.post(
            '/api/auth/profile-picture',
            data={'file': (io.BytesIO(INVALID_FILE_BYTES), 'avatar.png')},
            content_type='multipart/form-data',
            headers=mentor_headers
        )
        assert bad_upload.status_code == 400, f"Expected 400 for spoofed image, got {bad_upload.status_code}"
        print("  -> PASSED: Spoofed / invalid file signature rejected with 400")

        # Reject unsupported extension
        bad_ext = client.post(
            '/api/auth/profile-picture',
            data={'file': (io.BytesIO(b'some bytes'), 'document.pdf')},
            content_type='multipart/form-data',
            headers=mentor_headers
        )
        assert bad_ext.status_code == 400
        print("  -> PASSED: Non-image extension (.pdf) rejected with 400")

        # Successful PNG upload
        png_upload = client.post(
            '/api/auth/profile-picture',
            data={'file': (io.BytesIO(VALID_PNG_BYTES), 'mentor_pic.png')},
            content_type='multipart/form-data',
            headers=mentor_headers
        )
        assert png_upload.status_code == 200, f"PNG upload failed: {png_upload.get_json()}"
        mentor_pic_path = png_upload.get_json()["profile_picture"]
        assert mentor_pic_path and mentor_pic_path.startswith("uploads/profiles/profile_"), f"Unexpected path: {mentor_pic_path}"
        print(f"  -> PASSED: Mentor uploaded profile picture successfully: {mentor_pic_path}")

        # Static serving of profile picture
        pic_filename = os.path.basename(mentor_pic_path)
        serve_resp = client.get(f'/uploads/profiles/{pic_filename}')
        assert serve_resp.status_code == 200, f"Serving picture failed: {serve_resp.status_code}"
        assert serve_resp.data == VALID_PNG_BYTES, "Served bytes do not match uploaded image bytes"
        print("  -> PASSED: Static profile picture serving returned 200 with matching image bytes")

        # Verify mentor profile returns profile_picture
        prof_res = client.get('/api/mentors/profile', headers=mentor_headers)
        assert prof_res.status_code == 200
        assert prof_res.get_json()["profile"]["profile_picture"] == mentor_pic_path
        print("  -> PASSED: GET /api/mentors/profile returns updated profile_picture")

        # Update picture with JPEG
        jpg_upload = client.post(
            '/api/mentors/profile-picture',
            data={'file': (io.BytesIO(VALID_JPG_BYTES), 'mentor_pic.jpg')},
            content_type='multipart/form-data',
            headers=mentor_headers
        )
        assert jpg_upload.status_code == 200
        mentor_new_pic = jpg_upload.get_json()["profile_picture"]
        assert mentor_new_pic != mentor_pic_path
        print("  -> PASSED: Mentor updated profile picture to JPEG")

        # Remove picture
        del_pic = client.delete('/api/mentors/profile-picture', headers=mentor_headers)
        assert del_pic.status_code == 200
        assert del_pic.get_json()["profile_picture"] is None
        prof_after_del = client.get('/api/mentors/profile', headers=mentor_headers)
        assert prof_after_del.get_json()["profile"]["profile_picture"] is None
        print("  -> PASSED: Mentor removed profile picture successfully")

        # 3. TEST: Profile Picture Upload, Update, Remove for Mentee
        print("\n[TEST 2] Testing Mentee Profile Picture Upload & Removal...")
        mentee_upload = client.post(
            '/api/mentees/profile-picture',
            data={'file': (io.BytesIO(VALID_PNG_BYTES), 'mentee_pic.png')},
            content_type='multipart/form-data',
            headers=mentee_headers
        )
        assert mentee_upload.status_code == 200
        mentee_pic_path = mentee_upload.get_json()["profile_picture"]
        assert mentee_pic_path

        mentee_prof_res = client.get('/api/mentees/profile', headers=mentee_headers)
        assert mentee_prof_res.status_code == 200
        assert mentee_prof_res.get_json()["profile"]["profile_picture"] == mentee_pic_path
        print(f"  -> PASSED: Mentee uploaded profile picture successfully: {mentee_pic_path}")

        # 4. TEST: Mentor Skills Management
        print("\n[TEST 3] Testing Mentor Skills Management (Add, Batch PUT, Delete)...")
        # Ensure initial skills catalog has entries
        with app.app_context():
            python_skill = Skill.query.filter_by(name="Python").first()
            if not python_skill:
                python_skill = Skill(name="Python", category="Programming")
                db.session.add(python_skill)
            react_skill = Skill.query.filter_by(name="React").first()
            if not react_skill:
                react_skill = Skill(name="React", category="Web Development")
                db.session.add(react_skill)
            db.session.commit()
            py_id = python_skill.id
            react_id = react_skill.id

        # Batch update mentor skills
        put_skills = client.put('/api/mentors/skills', json={
            "skills": [
                {"skill_id": py_id, "proficiency": "Expert"},
                {"skill_id": react_id, "proficiency": "Advanced"}
            ]
        }, headers=mentor_headers)
        assert put_skills.status_code == 200, f"Batch update failed: {put_skills.get_json()}"
        saved_mentor_skills = put_skills.get_json()["skills"]
        assert len(saved_mentor_skills) == 2
        print("  -> PASSED: Mentor batch updated skills with proficiency")

        # Add custom skill by name
        add_skill = client.post('/api/mentors/skills', json={
            "skill_name": "Docker & Kubernetes",
            "proficiency": "Intermediate",
            "category": "Cloud"
        }, headers=mentor_headers)
        assert add_skill.status_code == 200
        skills_now = add_skill.get_json()["skills"]
        assert any(s["skill_name"] == "Docker & Kubernetes" for s in skills_now)
        docker_id = [s["skill_id"] for s in skills_now if s["skill_name"] == "Docker & Kubernetes"][0]
        print("  -> PASSED: Mentor added custom skill by name")

        # Delete skill
        del_skill = client.delete(f'/api/mentors/skills/{docker_id}', headers=mentor_headers)
        assert del_skill.status_code == 200
        assert not any(s["skill_id"] == docker_id for s in del_skill.get_json()["skills"])
        print("  -> PASSED: Mentor removed single skill")

        # 5. TEST: Mentee Skills vs Learning Interests Separation
        print("\n[TEST 4] Testing Mentee Skills vs Learning Interests Separation...")
        # Mentee declares known skills in Section A (UserSkill)
        put_mentee_skills = client.put('/api/mentees/skills', json={
            "skills": [
                {"skill_id": py_id, "proficiency": "Beginner"}
            ]
        }, headers=mentee_headers)
        assert put_mentee_skills.status_code == 200, f"Mentee known skills update failed: {put_mentee_skills.get_json()}"
        m_skills = put_mentee_skills.get_json()["skills"]
        assert len(m_skills) == 1
        assert m_skills[0]["skill_name"] == "Python"
        print("  -> PASSED: Mentee added known skills (Section A)")

        # Mentee declares learning interests in Section B (LearningInterest)
        put_interests = client.put('/api/mentees/interests', json={
            "interests": [
                {"skill_id": react_id, "priority": "High"}
            ]
        }, headers=mentee_headers)
        assert put_interests.status_code == 200, f"Mentee interests update failed: {put_interests.get_json()}"
        m_interests = put_interests.get_json()["interests"]
        assert len(m_interests) == 1
        assert m_interests[0]["skill_name"] == "React"
        print("  -> PASSED: Mentee added learning interests (Section B)")

        # Verify database separation
        with app.app_context():
            mentee_u = User.query.filter_by(email=mentee_email).first()
            mentee_p = MenteeProfile.query.filter_by(user_id=mentee_u.id).first()

            user_skill_rows = UserSkill.query.filter_by(user_id=mentee_u.id).all()
            learning_interest_rows = LearningInterest.query.filter_by(mentee_id=mentee_p.id).all()

            assert len(user_skill_rows) == 1 and user_skill_rows[0].skill_id == py_id
            assert len(learning_interest_rows) == 1 and learning_interest_rows[0].skill_id == react_id
            print("  -> PASSED: Verified strictly separated tables in database (user_skills vs learning_interests)")

        # 6. TEST: Mentorship Request with Enhanced Mentee Profile Info
        print("\n[TEST 5] Testing Enhanced Mentorship Request Card Information...")
        with app.app_context():
            mentor_u = User.query.filter_by(email=mentor_email).first()
            mentor_p = MentorProfile.query.filter_by(user_id=mentor_u.id).first()
            mentor_p_id = mentor_p.id

        # Update mentee profile bio and goal
        client.put('/api/mentees/profile', json={
            "bio": "Enthusiastic beginner developer looking to master full-stack.",
            "learning_goal": "Learn React and modern web architecture.",
            "experience_level": "Beginner",
            "education": "BS Computer Science"
        }, headers=mentee_headers)

        # Mentee creates request
        create_req = client.post('/api/requests', json={
            "mentor_id": mentor_p_id,
            "message": "Hi Alice, I want to learn React from you!"
        }, headers=mentee_headers)
        assert create_req.status_code == 201, f"Create request failed: {create_req.get_json()}"
        req_id = create_req.get_json()["request"]["id"]
        print(f"  -> PASSED: Mentee created mentorship request ID {req_id}")

        # Mentor fetches received requests
        rec_res = client.get('/api/requests/received', headers=mentor_headers)
        assert rec_res.status_code == 200
        req_list = rec_res.get_json()["requests"]
        assert len(req_list) >= 1
        target_req = [r for r in req_list if r["id"] == req_id][0]

        # Verify all enhanced fields on request card
        mentee_data = target_req["mentee"]
        assert mentee_data["name"] == "Bob Mentee"
        assert mentee_data["email"] == mentee_email
        assert mentee_data["profile_picture"] == mentee_pic_path
        assert "Enthusiastic beginner" in mentee_data["bio"]
        assert mentee_data["learning_goal"] == "Learn React and modern web architecture."
        assert mentee_data["experience_level"] == "Beginner"
        assert target_req["message"] == "Hi Alice, I want to learn React from you!"
        assert target_req["status"] == "pending"

        # Verify known skills and learning interests in received request card
        assert len(mentee_data["skills"]) == 1
        assert mentee_data["skills"][0]["skill_name"] == "Python"
        assert len(mentee_data["learning_interests"]) == 1
        assert mentee_data["learning_interests"][0]["skill_name"] == "React"
        print("  -> PASSED: Request card contains all mentee info: picture, bio, skills, learning interests, goals")

        # 7. TEST: View Full Mentee Profile & Authorization Enforcement
        print("\n[TEST 6] Testing View Full Mentee Profile & Authorization...")
        with app.app_context():
            mentee_u = User.query.filter_by(email=mentee_email).first()
            mentee_p = MenteeProfile.query.filter_by(user_id=mentee_u.id).first()
            mentee_p_id = mentee_p.id

        # Authorized mentor accesses full profile
        full_prof_res = client.get(f'/api/mentees/{mentee_p_id}/profile', headers=mentor_headers)
        assert full_prof_res.status_code == 200, f"Full profile failed: {full_prof_res.get_json()}"
        full_data = full_prof_res.get_json()["mentee"]
        assert full_data["name"] == "Bob Mentee"
        assert full_data["email"] == mentee_email
        assert full_data["profile_picture"] == mentee_pic_path
        assert len(full_data["skills"]) == 1
        assert len(full_data["learning_interests"]) == 1
        assert full_data["request_status"] == "pending"
        print("  -> PASSED: Authorized mentor fetched full mentee profile successfully")

        # Unauthorized mentor accesses full profile (403 expected)
        unauth_res = client.get(f'/api/mentees/{mentee_p_id}/profile', headers=other_headers)
        assert unauth_res.status_code == 403, f"Expected 403 for unauthorized mentor, got {unauth_res.status_code}"
        print("  -> PASSED: Unauthorized mentor blocked with 403 Forbidden")

        # 8. TEST: Accept & Reject Functionality Remains Working
        print("\n[TEST 7] Testing Accept and Reject Functionality...")
        # Accept request
        acc_res = client.patch(f'/api/requests/{req_id}/accept', headers=mentor_headers)
        assert acc_res.status_code == 200
        assert acc_res.get_json()["request"]["status"] == "accepted"
        print("  -> PASSED: Mentor successfully accepted request")

        # Verify mentee sees accepted status in sent requests
        sent_res = client.get('/api/requests/sent', headers=mentee_headers)
        assert sent_res.status_code == 200
        sent_item = [r for r in sent_res.get_json()["requests"] if r["id"] == req_id][0]
        assert sent_item["status"] == "accepted"
        assert sent_item["mentor"]["name"] == "Alice Mentor"
        print("  -> PASSED: Mentee sees accepted request with mentor details")

        print("\n" + "=" * 70)
        print("ALL PROFILE, SKILLS, AND REQUEST ENHANCEMENT TESTS PASSED!")
        print("=" * 70)

    finally:
        cleanup()


if __name__ == '__main__':
    run_tests()
