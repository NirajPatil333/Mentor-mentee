"""
Focused test suite for:
1. Multi-Participant Sessions with domain eligibility enforcement and Jitsi rooms.
2. Certificate inline preview endpoint (/api/certificates/<id>/preview) and authorization rules.
"""

import io
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, MentorshipRequest, Session, SessionParticipant, Certificate
from utils.auth import get_email_domain

def run_tests():
    app = create_app()
    client = app.test_client()

    print("=" * 65)
    print("STARTING FOCUSED TESTS: MULTI-MENTEE SESSIONS & CERTIFICATE PREVIEW")
    print("=" * 65)

    test_domain1_mentor = "mentor_alpha@techcorp.com"
    test_domain1_mentee1 = "alice@techcorp.com"
    test_domain1_mentee2 = "bob@techcorp.com"
    test_domain2_mentee3 = "carol@othercorp.com"

    all_emails = [
        test_domain1_mentor,
        test_domain1_mentee1,
        test_domain1_mentee2,
        test_domain2_mentee3,
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

                if mentee_ids or mentor_ids:
                    # Delete session participants
                    sessions = Session.query.filter(
                        (Session.mentee_id.in_(mentee_ids)) |
                        (Session.mentor_id.in_(mentor_ids))
                    ).all()
                    session_ids = [s.id for s in sessions]
                    if session_ids:
                        SessionParticipant.query.filter(SessionParticipant.session_id.in_(session_ids)).delete(synchronize_session=False)

                    # Delete certificates
                    Certificate.query.filter(Certificate.mentee_id.in_(mentee_ids)).delete(synchronize_session=False)

                    # Delete sessions
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

    cleanup()

    # 1. Register users
    def register(email, name, role):
        res = client.post('/api/auth/register', json={
            "name": name,
            "email": email,
            "password": "Password123!",
            "role": role
        })
        assert res.status_code == 201, f"Failed to register {email}: {res.get_json()}"
        login_res = client.post('/api/auth/login', json={
            "email": email,
            "password": "Password123!"
        })
        assert login_res.status_code == 200, f"Failed to login {email}: {login_res.get_json()}"
        return login_res.get_json()['access_token']

    mentor_token = register(test_domain1_mentor, "Mentor Alpha", "mentor")
    alice_token = register(test_domain1_mentee1, "Alice TechCorp", "mentee")
    bob_token = register(test_domain1_mentee2, "Bob TechCorp", "mentee")
    carol_token = register(test_domain2_mentee3, "Carol OtherCorp", "mentee")

    mentor_hdr = {"Authorization": f"Bearer {mentor_token}"}
    alice_hdr = {"Authorization": f"Bearer {alice_token}"}
    bob_hdr = {"Authorization": f"Bearer {bob_token}"}
    carol_hdr = {"Authorization": f"Bearer {carol_token}"}

    with app.app_context():
        mentor_prof = MentorProfile.query.filter_by(user_id=User.query.filter_by(email=test_domain1_mentor).first().id).first()
        alice_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=test_domain1_mentee1).first().id).first()
        bob_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=test_domain1_mentee2).first().id).first()
        carol_prof = MenteeProfile.query.filter_by(user_id=User.query.filter_by(email=test_domain2_mentee3).first().id).first()

    # 2. Send mentorship requests from all 3 mentees to mentor and accept them
    def send_and_accept(mentee_hdr, mentee_name):
        r = client.post('/api/requests', headers=mentee_hdr, json={
            "mentor_id": mentor_prof.id,
            "message": f"Hello from {mentee_name}"
        })
        assert r.status_code == 201
        req_id = r.get_json()['request']['id']
        acc = client.patch(f'/api/requests/{req_id}/accept', headers=mentor_hdr)
        assert acc.status_code == 200
        return req_id

    req_alice_id = send_and_accept(alice_hdr, "Alice")
    req_bob_id = send_and_accept(bob_hdr, "Bob")
    req_carol_id = send_and_accept(carol_hdr, "Carol")

    print("[TEST 1] Domain utility verification...")
    assert get_email_domain("test@techcorp.com") == "techcorp.com"
    assert get_email_domain("invalid-email") == ""
    print("  -> PASSED: Domain utility behaves correctly")

    print("[TEST 2] Multi-mentee session creation with domain validation...")
    # Attempt to create session with Carol (different domain: othercorp.com vs alice: techcorp.com) -> should reject 400
    res_mismatch = client.post('/api/sessions', headers=mentor_hdr, json={
        "request_id": req_alice_id,
        "title": "Domain Mismatch Test",
        "scheduled_date": "2026-10-25",
        "start_time": "10:00",
        "end_time": "11:00",
        "additional_mentee_ids": [carol_prof.id]
    })
    assert res_mismatch.status_code == 400
    assert "Domain mismatch" in res_mismatch.get_json()['message']
    print("  -> PASSED: Creation with different domain mentee rejected with 400 Bad Request")

    # Create session with Alice + Bob (both @techcorp.com) -> should succeed
    res_create = client.post('/api/sessions', headers=mentor_hdr, json={
        "request_id": req_alice_id,
        "title": "TechCorp Architecture Group Session",
        "description": "Multi-mentee sync",
        "scheduled_date": "2026-10-25",
        "start_time": "10:00",
        "end_time": "11:00",
        "additional_mentee_ids": [bob_prof.id]
    })
    assert res_create.status_code == 201
    created_sess = res_create.get_json()['session']
    session_id = created_sess['id']
    assert len(created_sess['participants']) == 2
    participant_emails = {p['email'] for p in created_sess['participants']}
    assert participant_emails == {test_domain1_mentee1, test_domain1_mentee2}
    assert created_sess['meeting_url'].startswith("https://meet.jit.si/")
    common_jitsi_url = created_sess['meeting_url']
    print("  -> PASSED: Multi-mentee session created with both mentees and common Jitsi link")

    print("[TEST 3] Jitsi room consistency & Session retrieval for co-participants...")
    # Check Alice sees the session and same Jitsi URL
    res_alice_sessions = client.get('/api/sessions', headers=alice_hdr)
    assert res_alice_sessions.status_code == 200
    alice_s = [s for s in res_alice_sessions.get_json()['sessions'] if s['id'] == session_id][0]
    assert alice_s['meeting_url'] == common_jitsi_url
    assert len(alice_s['participants']) == 2

    # Check Bob sees the session and same Jitsi URL
    res_bob_sessions = client.get('/api/sessions', headers=bob_hdr)
    assert res_bob_sessions.status_code == 200
    bob_s = [s for s in res_bob_sessions.get_json()['sessions'] if s['id'] == session_id][0]
    assert bob_s['meeting_url'] == common_jitsi_url
    assert len(bob_s['participants']) == 2

    # Check Carol does NOT see the session
    res_carol_sessions = client.get('/api/sessions', headers=carol_hdr)
    assert res_carol_sessions.status_code == 200
    carol_s_ids = [s['id'] for s in res_carol_sessions.get_json()['sessions']]
    assert session_id not in carol_s_ids

    # Check Carol cannot GET /api/sessions/<id> directly (403)
    res_carol_direct = client.get(f'/api/sessions/{session_id}', headers=carol_hdr)
    assert res_carol_direct.status_code == 403
    print("  -> PASSED: All participants share identical Jitsi URL; non-participants are forbidden (403)")

    print("[TEST 4] Adding participants to existing session (/api/sessions/<id>/participants)...")
    # Mentor gets available mentees for this session
    res_avail = client.get(f'/api/sessions/{session_id}/available-mentees', headers=mentor_hdr)
    assert res_avail.status_code == 200
    # Bob is already in the session, Carol is different domain, so available list should be empty
    assert len(res_avail.get_json()['mentees']) == 0

    # Try adding Carol to existing session -> rejected 400 due to domain mismatch
    res_add_carol = client.post(f'/api/sessions/{session_id}/participants', headers=mentor_hdr, json={
        "mentee_id": carol_prof.id
    })
    assert res_add_carol.status_code == 400
    assert "Domain mismatch" in res_add_carol.get_json()['message']

    # Try adding Alice again -> 409 already a participant
    res_add_alice = client.post(f'/api/sessions/{session_id}/participants', headers=mentor_hdr, json={
        "mentee_id": alice_prof.id
    })
    assert res_add_alice.status_code == 409
    print("  -> PASSED: Participant addition checks domain and duplicate participation correctly")

    print("[TEST 5] Certificate preview endpoint & authorization...")
    # Alice uploads a certificate (PDF)
    pdf_content = b"%PDF-1.4 test certificate pdf binary data for preview"
    res_upload = client.post(
        '/api/certificates',
        headers=alice_hdr,
        data={
            'title': 'Certified Cloud Architect',
            'issuer': 'Cloud Org',
            'issue_date': '2026-05-15',
            'file': (io.BytesIO(pdf_content), 'cloud_cert.pdf')
        },
        content_type='multipart/form-data'
    )
    assert res_upload.status_code == 201
    cert_id = res_upload.get_json()['certificate']['id']

    # Alice previews certificate -> 200 OK inline
    res_preview_owner = client.get(f'/api/certificates/{cert_id}/preview', headers=alice_hdr)
    assert res_preview_owner.status_code == 200
    assert res_preview_owner.headers.get('Content-Type') == 'application/pdf'
    # inline preview has no 'attachment' disposition or has inline
    content_disp = res_preview_owner.headers.get('Content-Disposition', '')
    assert 'attachment' not in content_disp
    assert res_preview_owner.data == pdf_content

    # Mentor (accepted mentorship with Alice) previews certificate -> 200 OK
    res_preview_mentor = client.get(f'/api/certificates/{cert_id}/preview', headers=mentor_hdr)
    assert res_preview_mentor.status_code == 200
    assert res_preview_mentor.data == pdf_content

    # Bob (unrelated mentee) previews Alice's certificate -> 403 Forbidden
    res_preview_unauth = client.get(f'/api/certificates/{cert_id}/preview', headers=bob_hdr)
    assert res_preview_unauth.status_code == 403

    # Carol (unrelated mentee) downloads Alice's certificate -> 403 Forbidden
    res_download_unauth = client.get(f'/api/certificates/{cert_id}/download', headers=carol_hdr)
    assert res_download_unauth.status_code == 403

    # Alice downloads certificate -> 200 OK attachment
    res_download_owner = client.get(f'/api/certificates/{cert_id}/download', headers=alice_hdr)
    assert res_download_owner.status_code == 200
    assert 'attachment' in res_download_owner.headers.get('Content-Disposition', '')
    print("  -> PASSED: Preview endpoint renders inline for owner and accepted mentor; rejects unauthorized users (403)")

    cleanup()
    print("=" * 65)
    print("ALL FOCUSED TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)

if __name__ == '__main__':
    run_tests()
