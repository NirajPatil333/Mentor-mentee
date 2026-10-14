"""
Test suite for Mentor viewing Mentees' Certificates and Achievements.
Verifies:
1. Authentication requirements (401 when unauthenticated)
2. Role requirements (403 when mentee tries to access mentor-only mentee record endpoints)
3. Relationship authorization (403 when mentor has no accepted mentorship with mentee)
4. Non-existent mentee handling (404)
5. Accepted mentor can view mentee's certificates and achievements (200)
6. Both route paths:
   - /api/certificates/mentee/<id> and /api/mentees/<id>/certificates
   - /api/achievements/mentee/<id> and /api/mentees/<id>/achievements
7. Mentor can preview and download certificate of accepted mentee (200)
8. Unrelated mentor cannot preview or download certificate of mentee (403)
9. Mentor cannot create, update, or delete mentee certificates or achievements (403)
10. Mentee can still manage their own certificates and achievements normally
"""

import io
import os
import sys
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest, Certificate, Achievement


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 70)
    print("STARTING TESTS: MENTOR VIEW MENTEES' CERTIFICATES & ACHIEVEMENTS")
    print("=" * 70)

    mentor1_email = "mentor_alpha_view_test@example.com"
    mentor2_email = "mentor_beta_view_test@example.com"
    mentee1_email = "mentee_accepted_view_test@example.com"
    mentee2_email = "mentee_unrelated_view_test@example.com"

    all_emails = [mentor1_email, mentor2_email, mentee1_email, mentee2_email]

    def cleanup():
        with app.app_context():
            users = User.query.filter(User.email.in_(all_emails)).all()
            user_ids = [u.id for u in users]
            if user_ids:
                mentee_profs = MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).all()
                mentor_profs = MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).all()
                mentee_ids = [m.id for m in mentee_profs]
                mentor_ids = [m.id for m in mentor_profs]

                if mentee_ids:
                    # Clean uploaded certificate files
                    certs = Certificate.query.filter(Certificate.mentee_id.in_(mentee_ids)).all()
                    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'certificates')
                    for c in certs:
                        if c.file_path:
                            fn = os.path.basename(c.file_path)
                            fpath = os.path.join(upload_folder, fn)
                            if os.path.exists(fpath):
                                try:
                                    os.remove(fpath)
                                except OSError:
                                    pass

                    Certificate.query.filter(Certificate.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)
                    Achievement.query.filter(Achievement.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)

                if mentee_ids or mentor_ids:
                    MentorshipRequest.query.filter(
                        (MentorshipRequest.mentee_id.in_(mentee_ids)) |
                        (MentorshipRequest.mentor_id.in_(mentor_ids))
                    ).delete(synchronize_session=False)

                MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
                db.session.commit()

    cleanup()

    try:
        # 1. Unauthenticated requests
        print("\n[TEST 1] Testing unauthenticated access (401)...")
        assert client.get('/api/certificates/mentee/1').status_code == 401
        assert client.get('/api/achievements/mentee/1').status_code == 401
        assert client.get('/api/mentees/1/certificates').status_code == 401
        assert client.get('/api/mentees/1/achievements').status_code == 401
        print("  -> PASSED: Unauthenticated requests returned 401")

        # 2. Register users
        print("\n[TEST 2] Registering test users...")
        def register(email, name, role):
            res = client.post('/api/auth/register', json={
                "name": name,
                "email": email,
                "password": "Password123!",
                "role": role
            })
            assert res.status_code == 201
            login_res = client.post('/api/auth/login', json={
                "email": email,
                "password": "Password123!"
            })
            assert login_res.status_code == 200
            return login_res.get_json()['access_token']

        mentor1_tok = register(mentor1_email, "Mentor Alpha", "mentor")
        mentor2_tok = register(mentor2_email, "Mentor Beta", "mentor")
        mentee1_tok = register(mentee1_email, "Mentee Accepted", "mentee")
        mentee2_tok = register(mentee2_email, "Mentee Unrelated", "mentee")

        m1_hdr = {"Authorization": f"Bearer {mentor1_tok}"}
        m2_hdr = {"Authorization": f"Bearer {mentor2_tok}"}
        me1_hdr = {"Authorization": f"Bearer {mentee1_tok}"}
        me2_hdr = {"Authorization": f"Bearer {mentee2_tok}"}

        with app.app_context():
            mentor1_prof = MentorProfile.query.filter_by(user_id=User.query.filter_by(email=mentor1_email).first().id).first()
            mentor2_prof = MentorProfile.query.filter_by(user_id=User.query.filter_by(email=mentor2_email).first().id).first()
            mentee1_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=mentee1_email).first().id).first()
            mentee2_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=mentee2_email).first().id).first()

        print("  -> PASSED: Registered 2 mentors and 2 mentees")

        # 3. Mentee user role blocked from mentor endpoints (403)
        print("\n[TEST 3] Testing role enforcement (Mentee gets 403 on mentor endpoints)...")
        assert client.get(f'/api/certificates/mentee/{mentee1_prof.id}', headers=me1_hdr).status_code == 403
        assert client.get(f'/api/achievements/mentee/{mentee1_prof.id}', headers=me1_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/certificates', headers=me1_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/achievements', headers=me1_hdr).status_code == 403
        print("  -> PASSED: Mentees blocked with 403 from mentor-specific mentee endpoints")

        # 4. Mentee 1 creates certificates and achievements
        print("\n[TEST 4] Mentee 1 creates certificates and achievements...")
        cert_res = client.post('/api/certificates', headers=me1_hdr, data={
            'title': 'Certified Kubernetes Administrator',
            'issuer': 'Linux Foundation',
            'issue_date': '2026-03-20',
            'file': (io.BytesIO(b"%PDF-1.4 CKA Cert Data Content"), 'cka_cert.pdf')
        }, content_type='multipart/form-data')
        assert cert_res.status_code == 201
        cert_id = cert_res.get_json()['certificate']['id']

        ach_res = client.post('/api/achievements', headers=me1_hdr, json={
            'title': 'Hackathon Winner - Cloud Division',
            'description': 'Built an automated microservices deployment pipeline.',
            'achievement_date': '2026-04-15',
            'achievement_url': 'https://devpost.com/software/my-hackathon-entry'
        })
        assert ach_res.status_code == 201
        ach_id = ach_res.get_json()['achievement']['id']
        print("  -> PASSED: Mentee 1 uploaded certificate and created achievement")

        # 5. Non-existent mentee ID returns 404
        print("\n[TEST 5] Testing non-existent mentee profile (404)...")
        assert client.get('/api/certificates/mentee/999999', headers=m1_hdr).status_code == 404
        assert client.get('/api/achievements/mentee/999999', headers=m1_hdr).status_code == 404
        assert client.get('/api/mentees/999999/certificates', headers=m1_hdr).status_code == 404
        assert client.get('/api/mentees/999999/achievements', headers=m1_hdr).status_code == 404
        print("  -> PASSED: Non-existent mentee returned 404")

        # 6. Unrelated Mentor 1 requests Mentee 1 data before mentorship is accepted (403)
        print("\n[TEST 6] Testing unauthorized mentor access before accepted mentorship (403)...")
        assert client.get(f'/api/certificates/mentee/{mentee1_prof.id}', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/achievements/mentee/{mentee1_prof.id}', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/certificates', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/achievements', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/certificates/{cert_id}/preview', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/certificates/{cert_id}/download', headers=m1_hdr).status_code == 403
        print("  -> PASSED: Unrelated mentor access returned 403")

        # 7. Establish accepted mentorship between Mentor 1 and Mentee 1
        print("\n[TEST 7] Establishing accepted mentorship between Mentor 1 and Mentee 1...")
        req_res = client.post('/api/requests', headers=me1_hdr, json={
            "mentor_id": mentor1_prof.id,
            "message": "Mentorship request for test"
        })
        assert req_res.status_code == 201
        request_id = req_res.get_json()['request']['id']

        accept_res = client.patch(f'/api/requests/{request_id}/accept', headers=m1_hdr)
        assert accept_res.status_code == 200
        print("  -> PASSED: Mentorship request accepted")

        # 8. Accepted Mentor 1 can now access Mentee 1's certificates and achievements
        print("\n[TEST 8] Mentor 1 accessing accepted Mentee 1's records (200)...")
        # Route 1: /api/certificates/mentee/<id>
        res_c1 = client.get(f'/api/certificates/mentee/{mentee1_prof.id}', headers=m1_hdr)
        assert res_c1.status_code == 200
        data_c1 = res_c1.get_json()
        assert data_c1['status'] == 'success'
        assert data_c1['count'] == 1
        assert data_c1['certificates'][0]['title'] == 'Certified Kubernetes Administrator'
        assert data_c1['certificates'][0]['issuer'] == 'Linux Foundation'
        assert data_c1['certificates'][0]['issue_date'] == '2026-03-20'
        assert data_c1['certificates'][0]['file_type'] == 'pdf'

        # Route 1 alias: /api/mentees/<id>/certificates
        res_c2 = client.get(f'/api/mentees/{mentee1_prof.id}/certificates', headers=m1_hdr)
        assert res_c2.status_code == 200
        assert res_c2.get_json()['count'] == 1

        # Route 2: /api/achievements/mentee/<id>
        res_a1 = client.get(f'/api/achievements/mentee/{mentee1_prof.id}', headers=m1_hdr)
        assert res_a1.status_code == 200
        data_a1 = res_a1.get_json()
        assert data_a1['status'] == 'success'
        assert data_a1['count'] == 1
        assert data_a1['achievements'][0]['title'] == 'Hackathon Winner - Cloud Division'
        assert 'microservices' in data_a1['achievements'][0]['description']
        assert data_a1['achievements'][0]['achievement_date'] == '2026-04-15'
        assert data_a1['achievements'][0]['achievement_url'] == 'https://devpost.com/software/my-hackathon-entry'

        # Route 2 alias: /api/mentees/<id>/achievements
        res_a2 = client.get(f'/api/mentees/{mentee1_prof.id}/achievements', headers=m1_hdr)
        assert res_a2.status_code == 200
        assert res_a2.get_json()['count'] == 1
        print("  -> PASSED: Mentor 1 successfully retrieved Mentee 1's certificates and achievements")

        # 9. Mentor 1 preview and download
        print("\n[TEST 9] Mentor 1 preview and download certificate of accepted mentee...")
        prev_res = client.get(f'/api/certificates/{cert_id}/preview', headers=m1_hdr)
        assert prev_res.status_code == 200
        assert b"%PDF-1.4 CKA Cert Data Content" in prev_res.data
        assert 'application/pdf' in prev_res.headers.get('Content-Type', '')

        dl_res = client.get(f'/api/certificates/{cert_id}/download', headers=m1_hdr)
        assert dl_res.status_code == 200
        assert b"%PDF-1.4 CKA Cert Data Content" in dl_res.data
        assert 'attachment' in dl_res.headers.get('Content-Disposition', '')
        print("  -> PASSED: Preview and download working for accepted mentor")

        # 10. Mentor 2 (unrelated mentor) remains blocked with 403
        print("\n[TEST 10] Mentor 2 (unrelated mentor) blocked from Mentee 1 records (403)...")
        assert client.get(f'/api/certificates/mentee/{mentee1_prof.id}', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/achievements/mentee/{mentee1_prof.id}', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/certificates', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/achievements', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/certificates/{cert_id}/preview', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/certificates/{cert_id}/download', headers=m2_hdr).status_code == 403
        print("  -> PASSED: Unrelated Mentor 2 strictly blocked with 403")

        # 11. Mentor cannot create, update, or delete mentee records
        print("\n[TEST 11] Mentors cannot create, update, or delete records (403)...")
        # Try upload certificate as mentor
        assert client.post('/api/certificates', headers=m1_hdr, data={
            'title': 'Mentor Fake Cert',
            'issuer': 'Test',
            'issue_date': '2026-01-01',
            'file': (io.BytesIO(b"%PDF test"), 'test.pdf')
        }, content_type='multipart/form-data').status_code == 403

        # Try update cert as mentor
        assert client.put(f'/api/certificates/{cert_id}', headers=m1_hdr, json={'title': 'Hacked'}).status_code == 403

        # Try delete cert as mentor
        assert client.delete(f'/api/certificates/{cert_id}', headers=m1_hdr).status_code == 403

        # Try create achievement as mentor
        assert client.post('/api/achievements', headers=m1_hdr, json={
            'title': 'Mentor Fake Ach',
            'achievement_date': '2026-01-01'
        }).status_code == 403

        # Try update achievement as mentor
        assert client.put(f'/api/achievements/{ach_id}', headers=m1_hdr, json={'title': 'Hacked'}).status_code == 403

        # Try delete achievement as mentor
        assert client.delete(f'/api/achievements/{ach_id}', headers=m1_hdr).status_code == 403
        print("  -> PASSED: Mentor cannot create, update, or delete mentee records")

        # 12. Empty state when mentee has no records
        print("\n[TEST 12] Empty state when mentee has no records...")
        # Mentee 2 has no records yet. Establish accepted mentorship between Mentor 1 and Mentee 2
        req2 = client.post('/api/requests', headers=me2_hdr, json={
            "mentor_id": mentor1_prof.id,
            "message": "Mentorship request from mentee 2"
        })
        assert req2.status_code == 201
        req2_id = req2.get_json()['request']['id']
        assert client.patch(f'/api/requests/{req2_id}/accept', headers=m1_hdr).status_code == 200

        empty_c = client.get(f'/api/certificates/mentee/{mentee2_prof.id}', headers=m1_hdr)
        assert empty_c.status_code == 200
        assert empty_c.get_json()['count'] == 0
        assert empty_c.get_json()['certificates'] == []

        empty_a = client.get(f'/api/achievements/mentee/{mentee2_prof.id}', headers=m1_hdr)
        assert empty_a.status_code == 200
        assert empty_a.get_json()['count'] == 0
        assert empty_a.get_json()['achievements'] == []
        print("  -> PASSED: Empty states handled gracefully with count 0 and empty lists")

        print("\n" + "=" * 70)
        print("ALL MENTOR VIEW MENTEE RECORDS TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        cleanup()


if __name__ == '__main__':
    run_tests()
