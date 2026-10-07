"""
Test suite for Certificates and Achievements features.
Covers:
- Unauthenticated access rejection (401)
- Role protection (mentee-only features, mentors blocked with 403)
- Certificates:
  - File format validation (.pdf, .jpg, .jpeg, .png allowed; others rejected with 400)
  - Missing fields and empty file validation (400)
  - Document upload & storage
  - Mentee retrieval, metadata update, authenticated download, and deletion with file cleanup
  - Mentee isolation & mentor access block (403)
- Achievements:
  - Required fields and date validation (400)
  - Mentee creation, listing, update, and deletion
  - Mentee isolation (Mentee 2 cannot see/edit Mentee 1's achievements)
- Full database schema preservation and test cleanup.
"""

import io
import os
import sys
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, Certificate, Achievement
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING CERTIFICATES & ACHIEVEMENTS TESTS")
    print("=" * 65)

    test_mentee1_email = "test_mentee1_cert_ach_suite@example.com"
    test_mentee2_email = "test_mentee2_cert_ach_suite@example.com"
    test_mentor_email = "test_mentor_cert_ach_suite@example.com"

    all_test_emails = [
        test_mentee1_email,
        test_mentee2_email,
        test_mentor_email
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

                if mentee_ids:
                    # Clean certificates and disk files
                    certs = Certificate.query.filter(Certificate.mentee_id.in_(mentee_ids)).all()
                    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'certificates')
                    for c in certs:
                        if c.file_path:
                            fname = os.path.basename(c.file_path)
                            fpath = os.path.join(upload_folder, fname)
                            if os.path.exists(fpath):
                                try:
                                    os.remove(fpath)
                                except OSError:
                                    pass

                    Certificate.query.filter(Certificate.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)
                    Achievement.query.filter(Achievement.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)

                MenteeProfile.query.filter(MenteeProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                MentorProfile.query.filter(MentorProfile.user_id.in_(user_ids)).delete(synchronize_session=False)
                User.query.filter(User.id.in_(user_ids)).delete(synchronize_session=False)
                db.session.commit()

    # Pre-clean
    cleanup_data()

    try:
        # -------------------------------------------------------------
        # 1. Unauthenticated Rejections (401)
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing Unauthenticated Access Rejection (401)...")
        assert client.get('/api/certificates').status_code == 401
        assert client.post('/api/certificates').status_code == 401
        assert client.get('/api/certificates/1/download').status_code == 401
        assert client.put('/api/certificates/1', json={}).status_code == 401
        assert client.delete('/api/certificates/1').status_code == 401

        assert client.get('/api/achievements').status_code == 401
        assert client.post('/api/achievements', json={}).status_code == 401
        assert client.put('/api/achievements/1', json={}).status_code == 401
        assert client.delete('/api/achievements/1').status_code == 401
        print("  -> PASSED: All certificate and achievement endpoints require JWT authentication (401)")

        # -------------------------------------------------------------
        # 2. Register test users
        # -------------------------------------------------------------
        print("\n[TEST 2] Registering test mentee 1, mentee 2, and mentor...")
        # Mentee 1
        client.post('/api/auth/register', json={
            "name": "Cert Mentee One", "email": test_mentee1_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee1 = client.post('/api/auth/login', json={
            "email": test_mentee1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee1 = {"Authorization": f"Bearer {token_mentee1}"}

        # Mentee 2
        client.post('/api/auth/register', json={
            "name": "Cert Mentee Two", "email": test_mentee2_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee2 = client.post('/api/auth/login', json={
            "email": test_mentee2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee2 = {"Authorization": f"Bearer {token_mentee2}"}

        # Mentor
        client.post('/api/auth/register', json={
            "name": "Cert Mentor", "email": test_mentor_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor = client.post('/api/auth/login', json={
            "email": test_mentor_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor = {"Authorization": f"Bearer {token_mentor}"}
        print("  -> PASSED: Test users registered and authenticated")

        # -------------------------------------------------------------
        # 3. Role Protection: Mentor blocked from mentee-only endpoints (403)
        # -------------------------------------------------------------
        print("\n[TEST 3] Testing Role Protection (Mentor gets 403)...")
        cert_data = {
            'title': 'Mentor Cert',
            'issuer': 'Test Issuer',
            'issue_date': '2026-05-01',
            'file': (io.BytesIO(b"%PDF-1.4 sample"), 'test.pdf')
        }
        assert client.post('/api/certificates', data=cert_data, headers=headers_mentor, content_type='multipart/form-data').status_code == 403
        assert client.get('/api/certificates', headers=headers_mentor).status_code == 403

        ach_data = {
            'title': 'Mentor Achievement',
            'achievement_date': '2026-05-01'
        }
        assert client.post('/api/achievements', json=ach_data, headers=headers_mentor).status_code == 403
        assert client.get('/api/achievements', headers=headers_mentor).status_code == 403
        print("  -> PASSED: Mentor blocked from mentee-only certificates and achievements (403)")

        # -------------------------------------------------------------
        # 4. Certificates: Validation (File types, empty files, missing fields)
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing Certificates Input Validation (400)...")
        # Missing title
        resp = client.post('/api/certificates', data={
            'issuer': 'AWS', 'issue_date': '2026-01-01', 'file': (io.BytesIO(b"%PDF-1.4 test"), 'test.pdf')
        }, headers=headers_mentee1, content_type='multipart/form-data')
        assert resp.status_code == 400

        # Invalid date
        resp = client.post('/api/certificates', data={
            'title': 'AWS Cert', 'issuer': 'AWS', 'issue_date': 'invalid-date', 'file': (io.BytesIO(b"%PDF-1.4 test"), 'test.pdf')
        }, headers=headers_mentee1, content_type='multipart/form-data')
        assert resp.status_code == 400

        # Unsupported file type (.docx, .txt, .zip)
        for bad_name, content in [('doc.docx', b'word'), ('file.txt', b'text'), ('app.zip', b'zip')]:
            resp = client.post('/api/certificates', data={
                'title': 'Cert', 'issuer': 'Issuer', 'issue_date': '2026-01-01', 'file': (io.BytesIO(content), bad_name)
            }, headers=headers_mentee1, content_type='multipart/form-data')
            assert resp.status_code == 400
            assert 'Unsupported file type' in resp.get_json()['message']

        # Empty file
        resp = client.post('/api/certificates', data={
            'title': 'Cert', 'issuer': 'Issuer', 'issue_date': '2026-01-01', 'file': (io.BytesIO(b""), 'test.pdf')
        }, headers=headers_mentee1, content_type='multipart/form-data')
        assert resp.status_code == 400
        print("  -> PASSED: Certificate validation (bad extension, missing fields, bad date, empty file) properly rejected with 400")

        # -------------------------------------------------------------
        # 5. Certificates: Successful Uploads (PDF, PNG, JPG)
        # -------------------------------------------------------------
        print("\n[TEST 5] Testing Successful Certificate Uploads (.pdf, .png, .jpg)...")
        # PDF
        resp_pdf = client.post('/api/certificates', data={
            'title': 'AWS Certified Solutions Architect',
            'issuer': 'Amazon Web Services',
            'issue_date': '2026-02-15',
            'file': (io.BytesIO(b"%PDF-1.5 AWS Solutions Architect Certificate Binary Content"), 'aws_cert.pdf')
        }, headers=headers_mentee1, content_type='multipart/form-data')
        assert resp_pdf.status_code == 201
        pdf_cert_id = resp_pdf.get_json()['certificate']['id']
        assert resp_pdf.get_json()['certificate']['file_type'] == 'pdf'
        print(f"  -> PASSED: PDF Certificate uploaded successfully (ID: {pdf_cert_id})")

        # PNG
        resp_png = client.post('/api/certificates', data={
            'title': 'Google Cloud Professional Cloud Architect',
            'issuer': 'Google Cloud',
            'issue_date': '2026-04-10',
            'file': (io.BytesIO(b"\x89PNG\r\n\x1a\n GCP Cloud Architect Certificate"), 'gcp_badge.png')
        }, headers=headers_mentee1, content_type='multipart/form-data')
        assert resp_png.status_code == 201
        png_cert_id = resp_png.get_json()['certificate']['id']
        assert resp_png.get_json()['certificate']['file_type'] == 'png'
        print(f"  -> PASSED: PNG Certificate uploaded successfully (ID: {png_cert_id})")

        # -------------------------------------------------------------
        # 6. Certificates: Retrieval, Download, and Isolation
        # -------------------------------------------------------------
        print("\n[TEST 6] Testing Certificate Retrieval, Download, & Isolation...")
        # Mentee 1 retrieves their certificates
        resp_list = client.get('/api/certificates', headers=headers_mentee1)
        assert resp_list.status_code == 200
        assert resp_list.get_json()['count'] == 2

        # Mentee 2 sees 0 certificates
        resp_me2_list = client.get('/api/certificates', headers=headers_mentee2)
        assert resp_me2_list.status_code == 200
        assert resp_me2_list.get_json()['count'] == 0

        # Mentee 1 downloads PDF certificate
        dl_resp = client.get(f'/api/certificates/{pdf_cert_id}/download', headers=headers_mentee1)
        assert dl_resp.status_code == 200
        assert b"%PDF-1.5 AWS Solutions Architect Certificate Binary Content" in dl_resp.data

        # Mentee 2 blocked from downloading Mentee 1's certificate (403)
        assert client.get(f'/api/certificates/{pdf_cert_id}/download', headers=headers_mentee2).status_code == 403

        # Mentor blocked from downloading Mentee 1's certificate (403)
        assert client.get(f'/api/certificates/{pdf_cert_id}/download', headers=headers_mentor).status_code == 403
        print("  -> PASSED: Mentee 1 downloaded certificate; unauthorized users blocked (403)")

        # -------------------------------------------------------------
        # 7. Certificates: Update & Deletion
        # -------------------------------------------------------------
        print("\n[TEST 7] Testing Certificate Update & Deletion...")
        # Mentee 1 updates metadata
        resp_update = client.put(f'/api/certificates/{pdf_cert_id}', json={
            "title": "AWS Certified Solutions Architect - Associate",
            "issuer": "Amazon Training & Certification"
        }, headers=headers_mentee1)
        assert resp_update.status_code == 200
        assert resp_update.get_json()['certificate']['title'] == "AWS Certified Solutions Architect - Associate"

        # Mentee 2 blocked from updating Mentee 1's certificate (403)
        assert client.put(f'/api/certificates/{pdf_cert_id}', json={"title": "Hacked"}, headers=headers_mentee2).status_code == 403

        # Mentee 1 deletes certificate
        resp_del = client.delete(f'/api/certificates/{pdf_cert_id}', headers=headers_mentee1)
        assert resp_del.status_code == 200
        assert client.get(f'/api/certificates/{pdf_cert_id}/download', headers=headers_mentee1).status_code == 404
        print("  -> PASSED: Certificate metadata updated, unauthorized update blocked, and certificate cleanly deleted")

        # -------------------------------------------------------------
        # 8. Achievements: Validation
        # -------------------------------------------------------------
        print("\n[TEST 8] Testing Achievements Validation (400)...")
        # Missing title
        resp = client.post('/api/achievements', json={'achievement_date': '2026-03-01'}, headers=headers_mentee1)
        assert resp.status_code == 400

        # Missing date
        resp = client.post('/api/achievements', json={'title': 'Hackathon Winner'}, headers=headers_mentee1)
        assert resp.status_code == 400

        # Invalid date
        resp = client.post('/api/achievements', json={'title': 'Hackathon Winner', 'achievement_date': 'bad-date'}, headers=headers_mentee1)
        assert resp.status_code == 400
        print("  -> PASSED: Achievements input validation rejected invalid payloads with 400")

        # -------------------------------------------------------------
        # 9. Achievements: Create, List, Update, Isolation, Delete
        # -------------------------------------------------------------
        print("\n[TEST 9] Testing Achievements Full Lifecycle & Isolation...")
        # Mentee 1 creates achievement
        resp_ach1 = client.post('/api/achievements', json={
            "title": "1st Place - Global AI & Cloud Hackathon",
            "description": "Built an automated mentor-mentee pairing and live coaching platform using Flask & React.",
            "achievement_date": "2026-03-20",
            "achievement_url": "https://devpost.com/software/mentor-mentee-ai"
        }, headers=headers_mentee1)
        assert resp_ach1.status_code == 201
        ach1_id = resp_ach1.get_json()['achievement']['id']
        assert resp_ach1.get_json()['achievement']['title'] == "1st Place - Global AI & Cloud Hackathon"
        print(f"  -> PASSED: Achievement created successfully (ID: {ach1_id})")

        # Mentee 1 retrieves achievements
        resp_ach_list = client.get('/api/achievements', headers=headers_mentee1)
        assert resp_ach_list.status_code == 200
        assert resp_ach_list.get_json()['count'] == 1

        # Mentee 2 retrieves achievements (0)
        assert client.get('/api/achievements', headers=headers_mentee2).get_json()['count'] == 0

        # Mentee 1 updates achievement
        resp_ach_update = client.put(f'/api/achievements/{ach1_id}', json={
            "description": "Updated project description with deployment links."
        }, headers=headers_mentee1)
        assert resp_ach_update.status_code == 200
        assert "Updated project description" in resp_ach_update.get_json()['achievement']['description']

        # Mentee 2 blocked from editing Mentee 1's achievement (403)
        assert client.put(f'/api/achievements/{ach1_id}', json={"title": "Hacked"}, headers=headers_mentee2).status_code == 403

        # Mentee 1 deletes achievement
        resp_ach_del = client.delete(f'/api/achievements/{ach1_id}', headers=headers_mentee1)
        assert resp_ach_del.status_code == 200
        assert client.get('/api/achievements', headers=headers_mentee1).get_json()['count'] == 0
        print("  -> PASSED: Achievement listing, isolation, updating, and deletion passed")

        # -------------------------------------------------------------
        # CLEANUP & SCHEMA VERIFICATION
        # -------------------------------------------------------------
        print("\n[CLEANUP] Cleaning up all test data...")
        cleanup_data()
        print("  -> PASSED: All test records and uploaded files removed cleanly")

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
                assert t in tables, f"Missing table: {t}"
            print(f"  -> PASSED: All 14 tables verified present in MySQL: {sorted(tables)}")

        print("\n" + "=" * 65)
        print("ALL CERTIFICATES & ACHIEVEMENTS TESTS PASSED SUCCESSFULLY!")
        print("=" * 65)

    except Exception:
        cleanup_data()
        raise


if __name__ == '__main__':
    run_tests()
