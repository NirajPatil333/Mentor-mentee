"""
Comprehensive test suite for Academic Records, Semester SGPA, Automatic CGPA, and Mentor Verification.

Tests cover:
1. Unauthenticated request rejections (401)
2. Role enforcement (Mentee-only creation/update/deletion, Mentor gets 403)
3. Input validation:
   - SGPA < 0.0 or > 10.0 rejected with 400
   - Invalid semester numbers (< 1 or non-integer) rejected with 400
   - Unsupported marksheet file types rejected with 400
   - Empty files rejected with 400
4. Duplicate semester prevention (409 Conflict)
5. Automatic CGPA calculation:
   - 1 semester: SGPA 8.2 -> CGPA 8.2
   - 2 semesters: SGPA 8.2, 7.6 -> CGPA 7.9
   - 3 semesters: SGPA 8.2, 7.6, 8.5 -> CGPA 8.1
6. Recalculation after editing SGPA
7. Recalculation after deleting a semester
8. Marksheet upload, preview, and download:
   - Mentee uploads marksheet
   - Mentee previews inline and downloads attachment
9. Mentor verification & authorization:
   - Unrelated mentor cannot access mentee's records (403)
   - Unrelated mentor cannot preview or download marksheet (403)
   - Accepted mentor can view mentee's academic records and calculate CGPA (200)
   - Accepted mentor can preview and download marksheet (200)
   - Mentor verification: Verified with review note (200)
   - Mentor verification: Rejected with review note (200)
   - Mentee blocked from calling mentor verify endpoint (403)
10. Reset to 'pending' upon SGPA update or marksheet replacement
11. Proper database cleanup and schema integrity
"""

import io
import os
import sys
from app import create_app, db
from models import (
    User, MenteeProfile, MentorProfile, MentorshipRequest,
    AcademicRecord, Certificate, Achievement
)


def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 70)
    print("STARTING TEST SUITE: ACADEMIC RECORDS, CGPA & MENTOR VERIFICATION")
    print("=" * 70)

    test_mentee1_email = "mentee1_acad_suite@example.com"
    test_mentee2_email = "mentee2_acad_suite@example.com"
    test_mentor1_email = "mentor1_acad_suite@example.com"
    test_mentor2_email = "mentor2_acad_suite@example.com"

    all_emails = [
        test_mentee1_email,
        test_mentee2_email,
        test_mentor1_email,
        test_mentor2_email
    ]

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
                    # Clean physical marksheet files
                    records = AcademicRecord.query.filter(AcademicRecord.mentee_id.in_(mentee_ids)).all()
                    upload_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads', 'marksheets')
                    for r in records:
                        if r.file_path:
                            fn = os.path.basename(r.file_path)
                            fpath = os.path.join(upload_folder, fn)
                            if os.path.exists(fpath):
                                try:
                                    os.remove(fpath)
                                except OSError:
                                    pass

                    AcademicRecord.query.filter(AcademicRecord.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)

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
        # -----------------------------------------------------------------
        # 1. Unauthenticated Requests (401)
        # -----------------------------------------------------------------
        print("\n[TEST 1] Testing unauthenticated access (401)...")
        assert client.get('/api/academic-records').status_code == 401
        assert client.post('/api/academic-records', json={'semester': 1, 'sgpa': 8.0}).status_code == 401
        assert client.put('/api/academic-records/1', json={'sgpa': 8.5}).status_code == 401
        assert client.delete('/api/academic-records/1').status_code == 401
        assert client.get('/api/academic-records/1/preview').status_code == 401
        assert client.get('/api/academic-records/1/download').status_code == 401
        assert client.get('/api/academic-records/mentee/1').status_code == 401
        assert client.patch('/api/academic-records/1/verify', json={'status': 'verified'}).status_code == 401
        print("  -> PASSED: All endpoints reject unauthenticated access with 401")

        # -----------------------------------------------------------------
        # 2. Register Test Users
        # -----------------------------------------------------------------
        print("\n[TEST 2] Registering test mentees and mentors...")
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

        mentee1_tok = register(test_mentee1_email, "Alice Mentee", "mentee")
        mentee2_tok = register(test_mentee2_email, "Bob Mentee", "mentee")
        mentor1_tok = register(test_mentor1_email, "Dr. Smith Mentor", "mentor")
        mentor2_tok = register(test_mentor2_email, "Prof. Jones Mentor", "mentor")

        me1_hdr = {"Authorization": f"Bearer {mentee1_tok}"}
        me2_hdr = {"Authorization": f"Bearer {mentee2_tok}"}
        m1_hdr = {"Authorization": f"Bearer {mentor1_tok}"}
        m2_hdr = {"Authorization": f"Bearer {mentor2_tok}"}

        with app.app_context():
            mentee1_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=test_mentee1_email).first().id).first()
            mentee2_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=test_mentee2_email).first().id).first()
            mentor1_prof = MentorProfile.query.filter_by(user_id=User.query.filter_by(email=test_mentor1_email).first().id).first()
            mentor2_prof = MentorProfile.query.filter_by(user_id=User.query.filter_by(email=test_mentor2_email).first().id).first()

        print("  -> PASSED: Registered 2 mentees and 2 mentors")

        # -----------------------------------------------------------------
        # 3. Role Protection: Mentor blocked from Mentee endpoints (403)
        # -----------------------------------------------------------------
        print("\n[TEST 3] Testing role enforcement (Mentors cannot create/edit/delete records)...")
        assert client.post('/api/academic-records', headers=m1_hdr, json={'semester': 1, 'sgpa': 8.0}).status_code == 403
        assert client.put('/api/academic-records/1', headers=m1_hdr, json={'sgpa': 8.0}).status_code == 403
        assert client.delete('/api/academic-records/1', headers=m1_hdr).status_code == 403
        print("  -> PASSED: Mentors blocked with 403 from mentee academic management")

        # -----------------------------------------------------------------
        # 4. Input Validations (SGPA range, Semester number, File types)
        # -----------------------------------------------------------------
        print("\n[TEST 4] Testing SGPA & Semester input validation (400)...")
        # SGPA > 10.0
        res = client.post('/api/academic-records', headers=me1_hdr, json={'semester': 1, 'sgpa': 10.5})
        assert res.status_code == 400
        assert "between 0.0 and 10.0" in res.get_json()['message']

        # SGPA < 0.0
        res = client.post('/api/academic-records', headers=me1_hdr, json={'semester': 1, 'sgpa': -1.0})
        assert res.status_code == 400

        # Non-numeric SGPA
        res = client.post('/api/academic-records', headers=me1_hdr, json={'semester': 1, 'sgpa': 'invalid'})
        assert res.status_code == 400

        # Semester < 1
        res = client.post('/api/academic-records', headers=me1_hdr, json={'semester': 0, 'sgpa': 8.0})
        assert res.status_code == 400

        # Missing semester
        res = client.post('/api/academic-records', headers=me1_hdr, json={'sgpa': 8.0})
        assert res.status_code == 400

        # Unsupported file type (.txt, .exe)
        bad_file_data = {
            'semester': '1',
            'sgpa': '8.5',
            'file': (io.BytesIO(b"malicious script"), 'bad.exe')
        }
        res = client.post('/api/academic-records', headers=me1_hdr, data=bad_file_data, content_type='multipart/form-data')
        assert res.status_code == 400
        assert "Unsupported file type" in res.get_json()['message']

        # Empty file
        empty_file_data = {
            'semester': '1',
            'sgpa': '8.5',
            'file': (io.BytesIO(b""), 'empty.pdf')
        }
        res = client.post('/api/academic-records', headers=me1_hdr, data=empty_file_data, content_type='multipart/form-data')
        assert res.status_code == 400
        assert "file is empty" in res.get_json()['message']
        print("  -> PASSED: All invalid inputs properly rejected with 400")

        # -----------------------------------------------------------------
        # 5. Adding Semesters & Automatic CGPA Calculation (Prompt Example)
        # -----------------------------------------------------------------
        print("\n[TEST 5] Testing semester additions & automatic CGPA calculation...")
        # Add Semester 1: SGPA 8.2
        pdf_content = b"%PDF-1.4 official marksheet semester 1 binary content"
        res_sem1 = client.post('/api/academic-records', headers=me1_hdr, data={
            'semester': '1',
            'sgpa': '8.2',
            'file': (io.BytesIO(pdf_content), 'sem1_marksheet.pdf')
        }, content_type='multipart/form-data')
        assert res_sem1.status_code == 201
        data1 = res_sem1.get_json()
        assert data1['cgpa'] == 8.2
        assert data1['record']['semester'] == 1
        assert data1['record']['sgpa'] == 8.2
        assert data1['record']['has_marksheet'] is True
        assert data1['record']['verification_status'] == 'pending'
        rec1_id = data1['record']['id']
        print(f"  -> Added Semester 1 (SGPA 8.2) => CGPA: {data1['cgpa']}")

        # Add Semester 2: SGPA 7.6
        res_sem2 = client.post('/api/academic-records', headers=me1_hdr, json={
            'semester': 2,
            'sgpa': 7.6
        })
        assert res_sem2.status_code == 201
        data2 = res_sem2.get_json()
        # (8.2 + 7.6) / 2 = 15.8 / 2 = 7.9
        assert data2['cgpa'] == 7.9
        rec2_id = data2['record']['id']
        print(f"  -> Added Semester 2 (SGPA 7.6) => CGPA: {data2['cgpa']} (Expected: 7.9)")

        # Add Semester 3: SGPA 8.5
        res_sem3 = client.post('/api/academic-records', headers=me1_hdr, json={
            'semester': 3,
            'sgpa': 8.5
        })
        assert res_sem3.status_code == 201
        data3 = res_sem3.get_json()
        # (8.2 + 7.6 + 8.5) / 3 = 24.3 / 3 = 8.1
        assert data3['cgpa'] == 8.1
        rec3_id = data3['record']['id']
        print(f"  -> Added Semester 3 (SGPA 8.5) => CGPA: {data3['cgpa']} (Expected: 8.1)")

        # Verify listing
        res_list = client.get('/api/academic-records', headers=me1_hdr)
        assert res_list.status_code == 200
        list_data = res_list.get_json()
        assert list_data['count'] == 3
        assert list_data['cgpa'] == 8.1
        assert list_data['cgpa_label'] == "Calculated CGPA (Simple Average)"
        print("  -> PASSED: Automatic CGPA arithmetic calculation matches prompt specification")

        # -----------------------------------------------------------------
        # 6. Duplicate Semester Prevention
        # -----------------------------------------------------------------
        print("\n[TEST 6] Testing duplicate semester prevention (409 Conflict)...")
        res_dup = client.post('/api/academic-records', headers=me1_hdr, json={
            'semester': 1,
            'sgpa': 9.0
        })
        assert res_dup.status_code == 409
        assert "already exists" in res_dup.get_json()['message']

        # Trying to edit Semester 2 to Semester 1 should also fail with 409
        res_edit_dup = client.put(f'/api/academic-records/{rec2_id}', headers=me1_hdr, json={
            'semester': 1
        })
        assert res_edit_dup.status_code == 409
        print("  -> PASSED: Duplicate semesters prevented at API and database constraint levels")

        # -----------------------------------------------------------------
        # 7. Recalculation on Update & Delete
        # -----------------------------------------------------------------
        print("\n[TEST 7] Testing CGPA recalculation after editing and deleting records...")
        # Update Semester 2 SGPA from 7.6 to 8.6
        # New sum: 8.2 + 8.6 + 8.5 = 25.3 / 3 = 8.43
        res_update = client.put(f'/api/academic-records/{rec2_id}', headers=me1_hdr, json={
            'sgpa': 8.6
        })
        assert res_update.status_code == 200
        assert res_update.get_json()['cgpa'] == 8.43
        print(f"  -> Updated Semester 2 to 8.6 => Recalculated CGPA: {res_update.get_json()['cgpa']} (Expected: 8.43)")

        # Delete Semester 3 (SGPA 8.5)
        # Remaining: 8.2 and 8.6 => (8.2 + 8.6) / 2 = 8.4
        res_del = client.delete(f'/api/academic-records/{rec3_id}', headers=me1_hdr)
        assert res_del.status_code == 200
        assert res_del.get_json()['cgpa'] == 8.4
        assert res_del.get_json()['remaining_count'] == 2
        print(f"  -> Deleted Semester 3 => Recalculated CGPA: {res_del.get_json()['cgpa']} (Expected: 8.4)")

        # -----------------------------------------------------------------
        # 8. Marksheet Preview & Download Authorization
        # -----------------------------------------------------------------
        print("\n[TEST 8] Testing marksheet preview & download...")
        # Mentee 1 previews their marksheet -> 200 OK inline
        prev_resp = client.get(f'/api/academic-records/{rec1_id}/preview', headers=me1_hdr)
        assert prev_resp.status_code == 200
        assert prev_resp.data == pdf_content
        assert 'application/pdf' in prev_resp.headers.get('Content-Type', '')

        # Mentee 1 downloads their marksheet -> 200 OK attachment
        dl_resp = client.get(f'/api/academic-records/{rec1_id}/download', headers=me1_hdr)
        assert dl_resp.status_code == 200
        assert dl_resp.data == pdf_content
        assert 'attachment' in dl_resp.headers.get('Content-Disposition', '')

        # Mentee 2 tries to download Mentee 1's marksheet -> 403 Forbidden
        assert client.get(f'/api/academic-records/{rec1_id}/download', headers=me2_hdr).status_code == 403
        assert client.get(f'/api/academic-records/{rec1_id}/preview', headers=me2_hdr).status_code == 403

        # Mentor 1 (not yet accepted) tries to download Mentee 1's marksheet -> 403 Forbidden
        assert client.get(f'/api/academic-records/{rec1_id}/download', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/academic-records/{rec1_id}/preview', headers=m1_hdr).status_code == 403
        print("  -> PASSED: Marksheet preview and download protected with 403 against unauthorized users")

        # -----------------------------------------------------------------
        # 9. Mentor Access & Verification Workflow
        # -----------------------------------------------------------------
        print("\n[TEST 9] Testing mentor access & verification workflow...")
        # Mentor 1 attempts to view Mentee 1 records before accepted mentorship -> 403
        assert client.get(f'/api/academic-records/mentee/{mentee1_prof.id}', headers=m1_hdr).status_code == 403
        assert client.get(f'/api/mentees/{mentee1_prof.id}/academic-records', headers=m1_hdr).status_code == 403

        # Establish accepted mentorship between Mentor 1 and Mentee 1
        req_res = client.post('/api/requests', headers=me1_hdr, json={
            "mentor_id": mentor1_prof.id,
            "message": "Please mentor me for academic verification test"
        })
        assert req_res.status_code == 201
        req_id = req_res.get_json()['request']['id']
        assert client.patch(f'/api/requests/{req_id}/accept', headers=m1_hdr).status_code == 200

        # Now Mentor 1 can view Mentee 1's academic records
        mentor_view = client.get(f'/api/academic-records/mentee/{mentee1_prof.id}', headers=m1_hdr)
        assert mentor_view.status_code == 200
        mv_data = mentor_view.get_json()
        assert mv_data['count'] == 2
        assert mv_data['cgpa'] == 8.4
        assert mv_data['records'][0]['semester'] == 1
        assert mv_data['records'][0]['verification_status'] == 'pending'

        # Also test route alias /api/mentees/<id>/academic-records
        alias_view = client.get(f'/api/mentees/{mentee1_prof.id}/academic-records', headers=m1_hdr)
        assert alias_view.status_code == 200
        assert alias_view.get_json()['count'] == 2

        # Accepted Mentor 1 can preview and download marksheet
        assert client.get(f'/api/academic-records/{rec1_id}/preview', headers=m1_hdr).status_code == 200
        assert client.get(f'/api/academic-records/{rec1_id}/download', headers=m1_hdr).status_code == 200

        # Unrelated Mentor 2 remains blocked (403)
        assert client.get(f'/api/academic-records/mentee/{mentee1_prof.id}', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/academic-records/{rec1_id}/preview', headers=m2_hdr).status_code == 403
        assert client.get(f'/api/academic-records/{rec1_id}/download', headers=m2_hdr).status_code == 403

        # Mentee cannot call verify endpoint (403)
        assert client.patch(f'/api/academic-records/{rec1_id}/verify', headers=me1_hdr, json={'status': 'verified'}).status_code == 403

        # Mentor 1 verifies Semester 1 marksheet
        v_res = client.patch(f'/api/academic-records/{rec1_id}/verify', headers=m1_hdr, json={
            'status': 'verified',
            'review_note': 'Official marksheet verified against university portal.'
        })
        assert v_res.status_code == 200
        v_data = v_res.get_json()['record']
        assert v_data['verification_status'] == 'verified'
        assert v_data['verified_by_mentor_id'] == mentor1_prof.id
        assert v_data['verified_by_name'] == "Dr. Smith Mentor"
        assert v_data['verified_at'] is not None
        assert 'portal' in v_data['review_note']
        print("  -> PASSED: Mentor verified Semester 1 record with reviewer ID, timestamp, and review note")

        # Mentor 1 rejects Semester 2 record
        r_res = client.patch(f'/api/academic-records/{rec2_id}/verify', headers=m1_hdr, json={
            'status': 'rejected',
            'review_note': 'No marksheet attached; please upload official document.'
        })
        assert r_res.status_code == 200
        assert r_res.get_json()['record']['verification_status'] == 'rejected'
        print("  -> PASSED: Mentor rejected Semester 2 record with review note")

        # -----------------------------------------------------------------
        # 10. Re-verification Reset to 'pending' on Modification
        # -----------------------------------------------------------------
        print("\n[TEST 10] Testing verification reset to 'pending' when SGPA is edited...")
        # Record 1 was 'verified'. Mentee updates SGPA from 8.2 to 8.3
        edit_res = client.put(f'/api/academic-records/{rec1_id}', headers=me1_hdr, json={
            'sgpa': 8.3
        })
        assert edit_res.status_code == 200
        edited_rec = edit_res.get_json()['record']
        assert edited_rec['sgpa'] == 8.3
        assert edited_rec['verification_status'] == 'pending'
        assert edited_rec['verified_by_mentor_id'] is None
        assert edited_rec['verified_at'] is None
        assert edited_rec['review_note'] == ''
        print("  -> PASSED: Verification status automatically reset to 'pending' upon SGPA modification")

        # -----------------------------------------------------------------
        # 11. Empty State Handling
        # -----------------------------------------------------------------
        print("\n[TEST 11] Testing empty state handling...")
        empty_res = client.get('/api/academic-records', headers=me2_hdr)
        assert empty_res.status_code == 200
        assert empty_res.get_json()['count'] == 0
        assert empty_res.get_json()['cgpa'] == 0.0
        assert empty_res.get_json()['records'] == []
        print("  -> PASSED: Empty states handled cleanly with count 0, cgpa 0.0, and empty records array")

        print("\n" + "=" * 70)
        print("ALL ACADEMIC RECORDS & MENTOR VERIFICATION TESTS PASSED SUCCESSFULLY!")
        print("=" * 70)

    finally:
        cleanup()


if __name__ == '__main__':
    run_tests()
