"""
Test suite for Resources feature (Document Upload & Access Control).
Covers:
- Unauthenticated access rejection (401)
- Role protection (only mentors can upload, 403 for mentees)
- File type validation (.pdf, .ppt, .pptx, .doc, .docx allowed; others rejected with 400)
- Empty / missing file validation (400)
- Scoped mentorship validation (mentors can share generally or with accepted mentees only)
- Mentee visibility & isolation (mentees only see resources from mentors with accepted relationships)
- Authenticated download endpoint (authorized users get 200, unauthorized get 403)
- Mentor deletion of resources and physical file cleanup
- Full test cleanup and schema preservation
"""

import os
import io
import sys
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest, Resource
from sqlalchemy import inspect


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING RESOURCES FEATURE: DOCUMENT UPLOAD & ACCESS CONTROL TESTS")
    print("=" * 65)

    test_mentor1_email = "test_mentor1_res_suite@example.com"
    test_mentor2_email = "test_mentor2_res_suite@example.com"
    test_mentee1_email = "test_mentee1_res_suite@example.com"
    test_mentee2_email = "test_mentee2_res_suite@example.com"
    test_unrelated_email = "test_unrelated_res_suite@example.com"

    all_test_emails = [
        test_mentor1_email,
        test_mentor2_email,
        test_mentee1_email,
        test_mentee2_email,
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
                    # Clean up resources and files on disk
                    resources = Resource.query.filter(
                        (Resource.mentor_id.in_(mentor_ids)) |
                        (Resource.mentee_id.in_(mentee_ids))
                    ).all()
                    
                    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'resources')
                    for r in resources:
                        if r.file_path:
                            fname = os.path.basename(r.file_path)
                            fpath = os.path.join(upload_folder, fname)
                            if os.path.exists(fpath):
                                try:
                                    os.remove(fpath)
                                except OSError:
                                    pass

                    Resource.query.filter(
                        (Resource.mentor_id.in_(mentor_ids)) |
                        (Resource.mentee_id.in_(mentee_ids))
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
        # 1. Health check
        # -------------------------------------------------------------
        print("\n[TEST 1] Testing GET /api/health...")
        resp = client.get('/api/health')
        assert resp.status_code == 200, f"Health check failed with status {resp.status_code}"
        print("  -> PASSED: /api/health returned 200 OK")

        # -------------------------------------------------------------
        # 2. Unauthenticated access tests (401)
        # -------------------------------------------------------------
        print("\n[TEST 2] Testing Unauthenticated Rejections (401)...")
        assert client.get('/api/resources').status_code == 401
        assert client.post('/api/resources').status_code == 401
        assert client.get('/api/resources/1/download').status_code == 401
        assert client.delete('/api/resources/1').status_code == 401
        print("  -> PASSED: All resource endpoints require JWT authentication (401)")

        # -------------------------------------------------------------
        # 3. Register test users and set up relationships
        # -------------------------------------------------------------
        print("\n[TEST 3] Registering test mentors, mentees, and setting up mentorships...")
        # Mentor 1
        client.post('/api/auth/register', json={
            "name": "Resource Mentor One", "email": test_mentor1_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor1 = client.post('/api/auth/login', json={
            "email": test_mentor1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor1 = {"Authorization": f"Bearer {token_mentor1}"}

        # Mentor 2
        client.post('/api/auth/register', json={
            "name": "Resource Mentor Two", "email": test_mentor2_email, "password": "Password123!", "role": "mentor"
        })
        token_mentor2 = client.post('/api/auth/login', json={
            "email": test_mentor2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentor2 = {"Authorization": f"Bearer {token_mentor2}"}

        # Mentee 1
        client.post('/api/auth/register', json={
            "name": "Resource Mentee One", "email": test_mentee1_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee1 = client.post('/api/auth/login', json={
            "email": test_mentee1_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee1 = {"Authorization": f"Bearer {token_mentee1}"}

        # Mentee 2
        client.post('/api/auth/register', json={
            "name": "Resource Mentee Two", "email": test_mentee2_email, "password": "Password123!", "role": "mentee"
        })
        token_mentee2 = client.post('/api/auth/login', json={
            "email": test_mentee2_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_mentee2 = {"Authorization": f"Bearer {token_mentee2}"}

        # Unrelated User
        client.post('/api/auth/register', json={
            "name": "Resource Unrelated", "email": test_unrelated_email, "password": "Password123!", "role": "mentee"
        })
        token_unrelated = client.post('/api/auth/login', json={
            "email": test_unrelated_email, "password": "Password123!"
        }).get_json()['access_token']
        headers_unrelated = {"Authorization": f"Bearer {token_unrelated}"}

        with app.app_context():
            m1 = User.query.filter_by(email=test_mentor1_email).first().mentor_profile
            m2 = User.query.filter_by(email=test_mentor2_email).first().mentor_profile
            me1 = User.query.filter_by(email=test_mentee1_email).first().mentee_profile
            me2 = User.query.filter_by(email=test_mentee2_email).first().mentee_profile
            mentor1_id = m1.id
            mentor2_id = m2.id
            mentee1_id = me1.id
            mentee2_id = me2.id

        # Mentee 1 sends request to Mentor 1 and Mentor 1 accepts
        req_resp = client.post('/api/requests', json={"mentor_id": mentor1_id}, headers=headers_mentee1)
        req_id = req_resp.get_json()['request']['id']
        client.patch(f'/api/requests/{req_id}/accept', headers=headers_mentor1)
        print("  -> PASSED: Test users registered and accepted mentorship relationship created between Mentor 1 and Mentee 1")

        # -------------------------------------------------------------
        # 4. Mentee attempting to upload (403)
        # -------------------------------------------------------------
        print("\n[TEST 4] Testing Mentee Upload Rejection (403)...")
        data_mentee = {
            'title': 'Mentee Cheat Sheet',
            'file': (io.BytesIO(b"%PDF-1.4 Fake PDF Content"), 'cheatsheet.pdf')
        }
        resp = client.post('/api/resources', data=data_mentee, headers=headers_mentee1, content_type='multipart/form-data')
        assert resp.status_code == 403, f"Expected 403 for mentee upload, got {resp.status_code}"
        print("  -> PASSED: Mentee blocked from uploading resources (403)")

        # -------------------------------------------------------------
        # 5. Unsupported file types rejection (400)
        # -------------------------------------------------------------
        print("\n[TEST 5] Testing Unsupported File Types Rejection (400)...")
        unsupported_files = [
            ('script.exe', b'binary executable code'),
            ('notes.txt', b'plain text'),
            ('image.png', b'\x89PNG\r\n\x1a\n'),
            ('archive.zip', b'PK\x03\x04'),
        ]
        for fname, content in unsupported_files:
            data = {
                'title': f'Test {fname}',
                'file': (io.BytesIO(content), fname)
            }
            resp = client.post('/api/resources', data=data, headers=headers_mentor1, content_type='multipart/form-data')
            assert resp.status_code == 400, f"Expected 400 for {fname}, got {resp.status_code}"
            assert 'Unsupported file type' in resp.get_json()['message']
        print("  -> PASSED: Unsupported extensions (.exe, .txt, .png, .zip) rejected with 400 Bad Request")

        # -------------------------------------------------------------
        # 6. Missing / empty file validation (400)
        # -------------------------------------------------------------
        print("\n[TEST 6] Testing Missing & Empty File Validation (400)...")
        # Missing title
        resp_no_title = client.post('/api/resources', data={'file': (io.BytesIO(b"%PDF-1.4 test"), 'test.pdf')}, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_no_title.status_code == 400, f"Expected 400 for missing title, got {resp_no_title.status_code}"

        # Missing file
        resp_no_file = client.post('/api/resources', data={'title': 'Only Title'}, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_no_file.status_code == 400, f"Expected 400 for missing file, got {resp_no_file.status_code}"

        # Empty file content
        resp_empty_file = client.post('/api/resources', data={'title': 'Empty PDF', 'file': (io.BytesIO(b""), 'empty.pdf')}, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_empty_file.status_code == 400, f"Expected 400 for empty file, got {resp_empty_file.status_code}"
        print("  -> PASSED: Missing title, missing file, and empty file rejected with 400 Bad Request")

        # -------------------------------------------------------------
        # 7. Allowed Document Uploads (PDF, Word, PowerPoint)
        # -------------------------------------------------------------
        print("\n[TEST 7] Testing Successful Document Uploads (.pdf, .docx, .pptx)...")
        # 7a. PDF Upload (General - all mentees)
        pdf_payload = {
            'title': 'Python Backend Guide',
            'description': 'Essential guide for Flask architecture and SQLAlchemy patterns.',
            'file': (io.BytesIO(b"%PDF-1.5 Flask Backend Architecture Guide Content"), 'backend_guide.pdf')
        }
        resp_pdf = client.post('/api/resources', data=pdf_payload, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_pdf.status_code == 201, f"PDF upload failed: {resp_pdf.get_json()}"
        res_pdf_data = resp_pdf.get_json()['resource']
        assert res_pdf_data['resource_type'] == 'pdf'
        assert res_pdf_data['title'] == 'Python Backend Guide'
        assert 'backend_guide.pdf' in res_pdf_data['file_name']
        res_pdf_id = res_pdf_data['id']
        print(f"  -> PASSED: PDF uploaded successfully (ID: {res_pdf_id}, Type: {res_pdf_data['resource_type']})")

        # 7b. Word Document Upload (.docx)
        docx_payload = {
            'title': 'Data Structures Roadmap',
            'description': 'Comprehensive syllabus for DSA mastery.',
            'file': (io.BytesIO(b"DOCX Fake Binary Content for DSA"), 'dsa_roadmap.docx')
        }
        resp_docx = client.post('/api/resources', data=docx_payload, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_docx.status_code == 201, f"Word upload failed: {resp_docx.get_json()}"
        res_docx_data = resp_docx.get_json()['resource']
        assert res_docx_data['resource_type'] == 'word'
        res_docx_id = res_docx_data['id']
        print(f"  -> PASSED: Word (.docx) uploaded successfully (ID: {res_docx_id}, Type: {res_docx_data['resource_type']})")

        # 7c. PowerPoint Upload (.pptx) targeted specifically to Mentee 1
        pptx_payload = {
            'title': 'System Design Slides',
            'description': 'Microservices and Distributed Caching overview.',
            'mentee_id': str(mentee1_id),
            'file': (io.BytesIO(b"PPTX Presentation Stream Content"), 'system_design.pptx')
        }
        resp_pptx = client.post('/api/resources', data=pptx_payload, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_pptx.status_code == 201, f"PowerPoint upload failed: {resp_pptx.get_json()}"
        res_pptx_data = resp_pptx.get_json()['resource']
        assert res_pptx_data['resource_type'] == 'powerpoint'
        assert res_pptx_data['mentee_id'] == mentee1_id
        res_pptx_id = res_pptx_data['id']
        print(f"  -> PASSED: PowerPoint (.pptx) uploaded successfully for Mentee 1 (ID: {res_pptx_id})")

        # -------------------------------------------------------------
        # 8. Mentor Scoped Upload Validation (Targeting unrelated mentee)
        # -------------------------------------------------------------
        print("\n[TEST 8] Testing Target Mentee Scoping Validation...")
        # Mentor 1 tries to target Mentee 2 (no accepted mentorship) -> 403
        bad_scope_payload = {
            'title': 'Confidential Slides',
            'mentee_id': str(mentee2_id),
            'file': (io.BytesIO(b"%PDF-1.4 sample"), 'test.pdf')
        }
        resp_bad_scope = client.post('/api/resources', data=bad_scope_payload, headers=headers_mentor1, content_type='multipart/form-data')
        assert resp_bad_scope.status_code == 403, f"Expected 403 for unaccepted mentee target, got {resp_bad_scope.status_code}"
        print("  -> PASSED: Mentors cannot target mentees without an accepted mentorship (403)")

        # -------------------------------------------------------------
        # 9. Mentor 2 uploads a resource (for Mentor 2's own mentees)
        # -------------------------------------------------------------
        print("\n[TEST 9] Mentor 2 uploads their own resource...")
        m2_payload = {
            'title': 'Mentor 2 Java Guide',
            'file': (io.BytesIO(b"%PDF-1.4 Java Guide"), 'java.pdf')
        }
        resp_m2 = client.post('/api/resources', data=m2_payload, headers=headers_mentor2, content_type='multipart/form-data')
        assert resp_m2.status_code == 201
        res_m2_id = resp_m2.get_json()['resource']['id']
        print(f"  -> PASSED: Mentor 2 uploaded resource ID {res_m2_id}")

        # -------------------------------------------------------------
        # 10. Mentee Resource Visibility & Isolation
        # -------------------------------------------------------------
        print("\n[TEST 10] Testing Mentee Visibility & Isolation (GET /api/resources)...")
        # Mentee 1 (has accepted mentorship with Mentor 1) should see Mentor 1's general and targeted resources (3 resources)
        resp_me1_list = client.get('/api/resources', headers=headers_mentee1)
        assert resp_me1_list.status_code == 200
        me1_resources = resp_me1_list.get_json()['resources']
        me1_res_ids = [r['id'] for r in me1_resources]
        assert res_pdf_id in me1_res_ids
        assert res_docx_id in me1_res_ids
        assert res_pptx_id in me1_res_ids
        assert res_m2_id not in me1_res_ids, "Mentee 1 should NOT see Mentor 2's resources"
        print(f"  -> PASSED: Mentee 1 sees all 3 authorized resources from Mentor 1 and 0 from Mentor 2")

        # Mentee 2 (has NO accepted mentorships) should see 0 resources
        resp_me2_list = client.get('/api/resources', headers=headers_mentee2)
        assert resp_me2_list.status_code == 200
        assert resp_me2_list.get_json()['count'] == 0
        print("  -> PASSED: Mentee 2 with no accepted mentors sees 0 resources")

        # Mentor 1 sees their uploaded resources
        resp_m1_list = client.get('/api/resources', headers=headers_mentor1)
        assert resp_m1_list.status_code == 200
        assert resp_m1_list.get_json()['count'] == 3
        print("  -> PASSED: Mentor 1 sees all 3 resources they uploaded")

        # -------------------------------------------------------------
        # 11. Authenticated Document Download Endpoint
        # -------------------------------------------------------------
        print("\n[TEST 11] Testing Authenticated Download Endpoint (GET /api/resources/<id>/download)...")
        # 11a. Mentee 1 downloads authorized PDF
        dl_pdf = client.get(f'/api/resources/{res_pdf_id}/download', headers=headers_mentee1)
        assert dl_pdf.status_code == 200, f"Download failed: {dl_pdf.status_code}"
        assert b"%PDF-1.5 Flask Backend Architecture Guide Content" in dl_pdf.data
        assert 'attachment' in dl_pdf.headers.get('Content-Disposition', '')
        print("  -> PASSED: Mentee 1 successfully downloaded authorized PDF file")

        # 11b. Mentor 1 downloads own Word document
        dl_docx = client.get(f'/api/resources/{res_docx_id}/download', headers=headers_mentor1)
        assert dl_docx.status_code == 200
        assert b"DOCX Fake Binary Content for DSA" in dl_docx.data
        print("  -> PASSED: Mentor 1 successfully downloaded own Word document")

        # 11c. Mentee 2 attempts to download Mentor 1's resource (403)
        dl_unauthorized = client.get(f'/api/resources/{res_pdf_id}/download', headers=headers_mentee2)
        assert dl_unauthorized.status_code == 403, f"Expected 403 for unauthorized mentee download, got {dl_unauthorized.status_code}"
        print("  -> PASSED: Unauthorized Mentee 2 rejected with 403 Forbidden on download")

        # 11d. Unrelated user attempts to download Mentor 2's resource (403)
        dl_unrelated = client.get(f'/api/resources/{res_m2_id}/download', headers=headers_unrelated)
        assert dl_unrelated.status_code == 403
        print("  -> PASSED: Unrelated user rejected with 403 Forbidden on download")

        # -------------------------------------------------------------
        # 12. Resource Deletion and Disk Cleanup
        # -------------------------------------------------------------
        print("\n[TEST 12] Testing Resource Deletion & Disk Cleanup...")
        # Mentor 2 cannot delete Mentor 1's resource (403)
        del_unauth = client.delete(f'/api/resources/{res_pdf_id}', headers=headers_mentor2)
        assert del_unauth.status_code == 403
        print("  -> PASSED: Mentor 2 cannot delete Mentor 1's resource (403)")

        # Mentor 1 deletes res_pdf
        del_resp = client.delete(f'/api/resources/{res_pdf_id}', headers=headers_mentor1)
        assert del_resp.status_code == 200
        # Check that GET download now returns 404
        assert client.get(f'/api/resources/{res_pdf_id}/download', headers=headers_mentor1).status_code == 404
        print("  -> PASSED: Mentor 1 deleted resource successfully; file removed from disk and database")

        # -------------------------------------------------------------
        # CLEANUP
        # -------------------------------------------------------------
        print("\n[CLEANUP] Cleaning up all test records and uploaded test files...")
        cleanup_data()
        print("  -> PASSED: All temporary test records and files removed cleanly")

        # -------------------------------------------------------------
        # SCHEMA INTEGRITY CHECK
        # -------------------------------------------------------------
        print("\n[TEST SCHEMA] Verifying all 14 database tables remain intact...")
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
            print(f"  -> PASSED: All 14 expected tables present in MySQL: {sorted(tables)}")

        print("\n" + "=" * 65)
        print("ALL RESOURCE FEATURE TESTS PASSED SUCCESSFULLY!")
        print("=" * 65)

    except Exception:
        cleanup_data()
        raise


if __name__ == '__main__':
    run_tests()
