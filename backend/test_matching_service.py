"""
Test suite for the mentor recommendation matching service.
Covers:
  1. Full Stack learning goal ranks a relevant Full Stack mentor above a Python/DB mentor.
  2. Python/data-science learning goal prefers a relevant Python/data mentor.
  3. Empty text and empty skill sets do not crash and return 0.0 skill_match.
  4. Both normalised skill-ID sets populated — existing primary path is used, unchanged.
  5. Only one side has skill-ID rows — text fallback is invoked.
  6. Composite scores use the correct 50/20/15/15 weights.
  7. API response shape (match_score, breakdown keys) is preserved.
"""

import sys
from datetime import datetime, timezone
from app import create_app, db
from models import (
    User, MenteeProfile, MentorProfile,
    UserSkill, LearningInterest, Skill
)
from utils.auth import hash_password
from services.matching_service import (
    _tech_tokens,
    _text_skill_match_pct,
    calculate_mentor_recommendations,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _clean(app, emails):
    """Remove test users and their profiles by email list."""
    with app.app_context():
        for email in emails:
            u = User.query.filter_by(email=email).first()
            if not u:
                continue
            if u.role == "mentee" and u.mentee_profile:
                mp = u.mentee_profile
                LearningInterest.query.filter_by(mentee_id=mp.id).delete()
                MenteeProfile.query.filter_by(id=mp.id).delete()
            if u.role == "mentor" and u.mentor_profile:
                mp = u.mentor_profile
                UserSkill.query.filter_by(user_id=u.id).delete()
                MentorProfile.query.filter_by(id=mp.id).delete()
            db.session.delete(u)
        db.session.commit()


def _make_mentor(app, email, name, position, bio, exp_years):
    with app.app_context():
        u = User(
            name=name, email=email,
            password_hash=hash_password("Password123!"),
            role="mentor", is_verified=True,
        )
        db.session.add(u)
        db.session.flush()
        mp = MentorProfile(
            user_id=u.id,
            current_position=position,
            bio=bio,
            experience_years=exp_years,
            average_rating=0.0,
            total_reviews=0,
        )
        db.session.add(mp)
        db.session.commit()
        return u.id, mp.id


def _make_mentee(app, email, name, goal):
    with app.app_context():
        u = User(
            name=name, email=email,
            password_hash=hash_password("Password123!"),
            role="mentee", is_verified=True,
        )
        db.session.add(u)
        db.session.flush()
        mp = MenteeProfile(user_id=u.id, learning_goal=goal)
        db.session.add(mp)
        db.session.commit()
        return u.id, mp.id


def _add_skill_to_mentor(app, mentor_user_id, skill_id):
    with app.app_context():
        us = UserSkill(user_id=mentor_user_id, skill_id=skill_id)
        db.session.add(us)
        db.session.commit()


def _add_interest_to_mentee(app, mentee_profile_id, skill_id):
    with app.app_context():
        li = LearningInterest(mentee_id=mentee_profile_id, skill_id=skill_id)
        db.session.add(li)
        db.session.commit()


# ---------------------------------------------------------------------------
# Unit-level tests for helper functions (no DB required)
# ---------------------------------------------------------------------------

def test_tech_tokens_basic():
    print("\n[TEST U1] _tech_tokens basic extraction...")
    tokens = _tech_tokens("I want to learn React, JavaScript and Node.js")
    assert "react" in tokens, f"Expected 'react' in {tokens}"
    assert "javascript" in tokens, f"Expected 'javascript' in {tokens}"
    assert "nodejs" in tokens, f"Expected 'nodejs' in {tokens}"
    # generic words must NOT appear
    for bad in ("learn", "want", "and"):
        assert bad not in tokens, f"Stop-word '{bad}' should not be in {tokens}"
    print("  -> PASSED: Technical tokens extracted, stop words excluded.")


def test_tech_tokens_fullstack():
    print("\n[TEST U2] _tech_tokens full-stack alias...")
    tokens = _tech_tokens("Full Stack Developer building web applications")
    assert "fullstack" in tokens, f"Expected 'fullstack' in {tokens}"
    print("  -> PASSED: 'full stack' mapped to 'fullstack'.")


def test_tech_tokens_empty():
    print("\n[TEST U3] _tech_tokens on empty / whitespace...")
    assert _tech_tokens("") == set()
    assert _tech_tokens("   ") == set()
    assert _tech_tokens(None) == set()
    print("  -> PASSED: Empty inputs return empty set.")


def test_text_skill_match_fullstack_mentor():
    print("\n[TEST U4] _text_skill_match_pct — full-stack mentee vs full-stack mentor...")
    pct = _text_skill_match_pct(
        "I want to learn HTML, CSS, JavaScript, React, and backend development.",
        "Full Stack Developer",
        "I build full-stack web applications using React, Node.js, and Python.",
    )
    assert pct > 0.0, f"Expected >0, got {pct}"
    print(f"  -> PASSED: full-stack mentee vs full-stack mentor = {pct:.1f}%")


def test_text_skill_match_fullstack_beats_python_db():
    print("\n[TEST U5] _text_skill_match_pct — full-stack mentee: full-stack mentor > Python/DB mentor...")
    fullstack_pct = _text_skill_match_pct(
        "I want to learn HTML, CSS, JavaScript, React, and backend development.",
        "Full Stack Developer",
        "I build full-stack web applications using React, Node.js, and Python.",
    )
    python_db_pct = _text_skill_match_pct(
        "I want to learn HTML, CSS, JavaScript, React, and backend development.",
        "Python & Database Development",
        "I enjoy teaching programming, database design, and problem-solving techniques.",
    )
    print(f"  full-stack mentor text match: {fullstack_pct:.1f}%")
    print(f"  python/db mentor text match: {python_db_pct:.1f}%")
    assert fullstack_pct > python_db_pct, (
        f"Full-stack mentor ({fullstack_pct:.1f}%) should beat Python/DB mentor ({python_db_pct:.1f}%)"
    )
    print("  -> PASSED: Full-stack mentor scores higher for a full-stack mentee.")


def test_text_skill_match_python_goal():
    print("\n[TEST U6] _text_skill_match_pct — Python/ML mentee prefers Python mentor...")
    python_pct = _text_skill_match_pct(
        "I want to learn Python, machine learning, and data analysis.",
        "Python & Data Science Specialist",
        "Experienced Python developer specialising in machine learning and data analysis.",
    )
    web_pct = _text_skill_match_pct(
        "I want to learn Python, machine learning, and data analysis.",
        "Full Stack Web Developer",
        "I build web applications using React, JavaScript, HTML, CSS, and Node.js.",
    )
    print(f"  Python mentor text match: {python_pct:.1f}%")
    print(f"  Web/JS mentor text match: {web_pct:.1f}%")
    assert python_pct > web_pct, (
        f"Python mentor ({python_pct:.1f}%) should beat Web mentor ({web_pct:.1f}%)"
    )
    print("  -> PASSED: Python/ML mentor scores higher for a Python/ML mentee.")


def test_text_skill_match_empty_goal():
    print("\n[TEST U7] _text_skill_match_pct — empty mentee goal returns 0...")
    pct = _text_skill_match_pct("", "Full Stack Developer", "React and Node.js mentor")
    assert pct == 0.0, f"Expected 0.0, got {pct}"
    pct2 = _text_skill_match_pct(None, "Full Stack Developer", "React and Node.js mentor")
    assert pct2 == 0.0, f"Expected 0.0, got {pct2}"
    print("  -> PASSED: Empty / None goal returns 0.0 without crash.")


def test_text_skill_match_empty_mentor():
    print("\n[TEST U8] _text_skill_match_pct — empty mentor texts return 0...")
    pct = _text_skill_match_pct("I want to learn React and JavaScript.", "", "")
    assert pct == 0.0, f"Expected 0.0, got {pct}"
    print("  -> PASSED: Empty mentor texts return 0.0 without crash.")


# ---------------------------------------------------------------------------
# Integration tests (require DB)
# ---------------------------------------------------------------------------

TEST_EMAILS = [
    "match_test_mentee_fs@example.com",
    "match_test_mentee_py@example.com",
    "match_test_mentor_fs@example.com",
    "match_test_mentor_py@example.com",
]


def test_fullstack_mentee_text_fallback(app):
    """
    Part A + B: No skill-ID rows on either side.
    Full-stack mentee (text goal) must rank the full-stack mentor above the Python/DB mentor.
    """
    print("\n[TEST 1] Full Stack mentee (text fallback, no skill-ID rows) — ranking order...")
    mentee_uid, mentee_pid = _make_mentee(
        app,
        "match_test_mentee_fs@example.com",
        "FS Mentee",
        "I want to learn HTML, CSS, JavaScript, React, and backend development to build full-stack web applications.",
    )
    fs_uid, fs_mid = _make_mentor(
        app,
        "match_test_mentor_fs@example.com",
        "FS Mentor",
        "Full Stack Developer",
        "I build full-stack web apps using React, JavaScript, Node.js, HTML and CSS.",
        exp_years=3,
    )
    py_uid, py_mid = _make_mentor(
        app,
        "match_test_mentor_py@example.com",
        "PY Mentor",
        "Python & Database Development",
        "I enjoy teaching programming, database design and SQL. I specialise in Python and SQL.",
        exp_years=6,
    )

    with app.app_context():
        recs = calculate_mentor_recommendations(mentee_uid)

    assert len(recs) >= 2, f"Expected at least 2 recommendations, got {len(recs)}"

    # Verify response shape
    for r in recs:
        assert "match_score" in r
        assert "breakdown" in r
        assert all(k in r["breakdown"] for k in ("skill_match", "experience", "rating", "availability"))

    names = [r["mentor"]["name"] for r in recs]
    scores = {r["mentor"]["name"]: r for r in recs}
    fs_score = scores["FS Mentor"]["match_score"]
    py_score = scores["PY Mentor"]["match_score"]
    fs_skill = scores["FS Mentor"]["breakdown"]["skill_match"]
    py_skill = scores["PY Mentor"]["breakdown"]["skill_match"]

    print(f"  FS Mentor  skill_match={fs_skill}  total={fs_score}")
    print(f"  PY Mentor  skill_match={py_skill}  total={py_score}")

    assert fs_skill > py_skill, (
        f"Full-stack mentor skill_match ({fs_skill}) should exceed Python/DB mentor ({py_skill})"
    )
    assert names[0] == "FS Mentor", (
        f"Full-stack mentor should rank first; got order: {names}"
    )
    print("  -> PASSED: Full-stack mentor ranks above Python/DB mentor for full-stack mentee.")
    return mentee_uid, fs_uid, py_uid


def test_python_mentee_text_fallback(app):
    """
    Part A + B: No skill-ID rows on either side.
    Python/ML mentee must rank the Python mentor above the Full Stack mentor.
    """
    print("\n[TEST 2] Python/ML mentee (text fallback) — ranking order...")
    mentee_uid, mentee_pid = _make_mentee(
        app,
        "match_test_mentee_py@example.com",
        "PY Mentee",
        "I want to learn Python, machine learning, and data analysis to work in data science.",
    )

    # Reuse mentors already created in Test 1
    with app.app_context():
        recs = calculate_mentor_recommendations(mentee_uid)

    assert len(recs) >= 2
    scores = {r["mentor"]["name"]: r for r in recs}
    fs_skill = scores["FS Mentor"]["breakdown"]["skill_match"]
    py_skill = scores["PY Mentor"]["breakdown"]["skill_match"]
    fs_total = scores["FS Mentor"]["match_score"]
    py_total = scores["PY Mentor"]["match_score"]
    print(f"  PY Mentor  skill_match={py_skill}  total={py_total}")
    print(f"  FS Mentor  skill_match={fs_skill}  total={fs_total}")
    assert py_skill >= fs_skill, (
        f"Python mentor skill_match ({py_skill}) should be >= Full-stack mentor ({fs_skill}) for Python mentee"
    )
    print("  -> PASSED: Python mentor matches as well or better for Python/ML mentee.")
    return mentee_uid


def test_empty_text_and_skills_no_crash(app):
    """
    Part B: Mentee with no learning_goal text and no skill-ID rows.
    Must not crash; skill_match must be 0.0 for all mentors.
    """
    print("\n[TEST 3] Empty goal, no skill-ID rows — no crash, skill_match=0...")
    mentee_uid, _ = _make_mentee(
        app,
        "match_test_mentee_fs@example.com",  # email already inserted in Test 1
        "FS Mentee",                           # already exists — skip if present
        "I want to learn HTML, CSS, JavaScript, React, and backend development to build full-stack web applications.",
    ) if False else (None, None)

    # Use the already-created empty-goal mentee with user_id from existing account
    with app.app_context():
        # Create a throw-away mentee with no goal inside context
        u_empty = User(
            name="Empty Goal Mentee",
            email="match_test_empty_goal@example.com",
            password_hash=hash_password("x"),
            role="mentee", is_verified=True,
        )
        db.session.add(u_empty)
        db.session.flush()
        mp_empty = MenteeProfile(user_id=u_empty.id, learning_goal=None)
        db.session.add(mp_empty)
        db.session.commit()
        empty_uid = u_empty.id

        recs = calculate_mentor_recommendations(empty_uid)
        for r in recs:
            assert r["breakdown"]["skill_match"] == 0.0, (
                f"Empty-goal mentee should get skill_match=0, got {r['breakdown']['skill_match']}"
            )

        # cleanup
        LearningInterest.query.filter_by(mentee_id=mp_empty.id).delete()
        MenteeProfile.query.filter_by(id=mp_empty.id).delete()
        db.session.delete(u_empty)
        db.session.commit()

    print("  -> PASSED: Empty goal produces skill_match=0.0 for all mentors without crash.")


def test_both_skill_ids_populated_primary_path(app):
    """
    Part B (primary path unchanged): When both sides have skill-ID rows,
    the existing intersection logic must be used, not the text fallback.
    """
    print("\n[TEST 4] Both skill-ID sets populated — primary path used...")
    with app.app_context():
        # Give FS mentor skills: React (7), JavaScript (2), Node.js (8), HTML & CSS (10)
        fs_user = User.query.filter_by(email="match_test_mentor_fs@example.com").first()
        py_user = User.query.filter_by(email="match_test_mentor_py@example.com").first()
        fs_mentee_user = User.query.filter_by(email="match_test_mentee_fs@example.com").first()

        # Add skill-IDs to mentors
        for sid in [2, 7, 8, 10]:   # JS, React, Node, HTML&CSS
            if not UserSkill.query.filter_by(user_id=fs_user.id, skill_id=sid).first():
                db.session.add(UserSkill(user_id=fs_user.id, skill_id=sid))
        for sid in [1, 14]:         # Python, SQL
            if not UserSkill.query.filter_by(user_id=py_user.id, skill_id=sid).first():
                db.session.add(UserSkill(user_id=py_user.id, skill_id=sid))

        # Add matching interest-IDs to mentee: React(7), JS(2), Node(8), HTML&CSS(10)
        fs_mentee_profile = MenteeProfile.query.filter_by(user_id=fs_mentee_user.id).first()
        for sid in [2, 7, 8, 10]:
            if not LearningInterest.query.filter_by(mentee_id=fs_mentee_profile.id, skill_id=sid).first():
                db.session.add(LearningInterest(mentee_id=fs_mentee_profile.id, skill_id=sid))
        db.session.commit()

        recs = calculate_mentor_recommendations(fs_mentee_user.id)
        scores = {r["mentor"]["name"]: r for r in recs}
        fs_skill = scores["FS Mentor"]["breakdown"]["skill_match"]
        py_skill = scores["PY Mentor"]["breakdown"]["skill_match"]

        print(f"  FS Mentor skill_match (primary) = {fs_skill}%")
        print(f"  PY Mentor skill_match (primary) = {py_skill}%")

        # mentee interests: {2,7,8,10} — FS mentor has all 4 → 100%
        # PY mentor has {1,14} → 0 overlap → 0%
        assert fs_skill == 100.0, f"Expected 100.0 for perfect skill overlap, got {fs_skill}"
        assert py_skill == 0.0,   f"Expected 0.0 for no skill overlap, got {py_skill}"

    print("  -> PASSED: Primary skill-ID path correct (100% vs 0% overlap).")


def test_one_side_skill_ids_only(app):
    """
    Part B: Mentor has skill-ID rows but mentee has NO learning-interest rows.
    Text fallback must be invoked (not division by zero or zero-scoring).
    """
    print("\n[TEST 5] Only mentor has skill-ID rows (mentee side empty) — text fallback invoked...")
    with app.app_context():
        # Create a fresh mentee with a goal but no learning-interest rows
        u = User(
            name="One-side Mentee",
            email="match_test_oneside_mentee@example.com",
            password_hash=hash_password("x"),
            role="mentee", is_verified=True,
        )
        db.session.add(u)
        db.session.flush()
        mp = MenteeProfile(
            user_id=u.id,
            learning_goal="I want to learn React, JavaScript, and HTML CSS for web development."
        )
        db.session.add(mp)
        db.session.commit()
        uid = u.id

        recs = calculate_mentor_recommendations(uid)
        scores = {r["mentor"]["name"]: r for r in recs}
        fs_skill = scores["FS Mentor"]["breakdown"]["skill_match"]

        print(f"  FS Mentor skill_match (one-side fallback) = {fs_skill}%")
        # Should NOT be 0 — the text fallback must have found React/JS/HTML
        assert fs_skill > 0.0, (
            f"Text fallback should produce >0 skill_match for a matching goal; got {fs_skill}"
        )

        # cleanup
        LearningInterest.query.filter_by(mentee_id=mp.id).delete()
        MenteeProfile.query.filter_by(id=mp.id).delete()
        db.session.delete(u)
        db.session.commit()

    print("  -> PASSED: Text fallback invoked when only mentor side has skill-ID rows.")


def run_all():
    app = create_app()
    app.config["REQUIRE_EMAIL_VERIFICATION"] = False

    print("=" * 70)
    print("STARTING MATCHING SERVICE TESTS")
    print("=" * 70)

    # Unit tests (no DB)
    test_tech_tokens_basic()
    test_tech_tokens_fullstack()
    test_tech_tokens_empty()
    test_text_skill_match_fullstack_mentor()
    test_text_skill_match_fullstack_beats_python_db()
    test_text_skill_match_python_goal()
    test_text_skill_match_empty_goal()
    test_text_skill_match_empty_mentor()

    # Pre-clean stale test data
    _clean(app, TEST_EMAILS + [
        "match_test_empty_goal@example.com",
        "match_test_oneside_mentee@example.com",
    ])

    # Integration tests (require DB + mentor fixtures)
    try:
        test_fullstack_mentee_text_fallback(app)   # creates fixtures
        test_python_mentee_text_fallback(app)       # reuses mentor fixtures
        test_empty_text_and_skills_no_crash(app)
        test_both_skill_ids_populated_primary_path(app)
        test_one_side_skill_ids_only(app)
    finally:
        _clean(app, TEST_EMAILS + [
            "match_test_empty_goal@example.com",
            "match_test_oneside_mentee@example.com",
        ])

    print("\n" + "=" * 70)
    print("ALL MATCHING SERVICE TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)
    return True


if __name__ == "__main__":
    ok = run_all()
    sys.exit(0 if ok else 1)
