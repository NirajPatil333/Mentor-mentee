"""
conftest.py — shared pytest fixtures for the backend test suite.

Provides the `app` fixture used by integration tests that need a live
application context (e.g. test_matching_service.py).

Design decisions
----------------
* Reuses the existing `create_app()` factory from app.py verbatim — no
  parallel app construction.
* Targets the same MySQL database configured via .env.  The matching-service
  integration tests insert rows with distinctive "@example.com" email
  addresses and clean up after themselves; this fixture adds an extra safety
  net by wiping those sentinel emails before the session starts and once more
  after it ends.
* TESTING = True and REQUIRE_EMAIL_VERIFICATION = False are injected so that
  email-dispatch code is suppressed and tests are not blocked by verification.
* Scope is "session" so the app is created once and shared across all tests
  in the run — matches the original run_all() pattern.
"""

import pytest
from app import create_app, db
from models import User, MenteeProfile, MentorProfile, UserSkill, LearningInterest

# ---------------------------------------------------------------------------
# Sentinel emails inserted exclusively by the matching-service test suite.
# These are wiped before the session starts and after it ends to ensure no
# stale data from a previous aborted run can interfere, and that no test
# data is left behind in the production database.
# ---------------------------------------------------------------------------
_MATCHING_TEST_EMAILS = [
    "match_test_mentee_fs@example.com",
    "match_test_mentee_py@example.com",
    "match_test_mentor_fs@example.com",
    "match_test_mentor_py@example.com",
    "match_test_empty_goal@example.com",
    "match_test_oneside_mentee@example.com",
]


def _purge_test_users(app_instance):
    """Delete all rows associated with the matching-service sentinel emails."""
    with app_instance.app_context():
        users = User.query.filter(User.email.in_(_MATCHING_TEST_EMAILS)).all()
        for u in users:
            # Delete child rows first to avoid NOT NULL FK constraint violations
            # when SQLAlchemy tries to null-out the FK on the parent user row.
            if u.role == "mentee":
                mentee_profile = MenteeProfile.query.filter_by(user_id=u.id).first()
                if mentee_profile:
                    LearningInterest.query.filter_by(mentee_id=mentee_profile.id).delete()
                    MenteeProfile.query.filter_by(id=mentee_profile.id).delete()
            if u.role == "mentor":
                UserSkill.query.filter_by(user_id=u.id).delete()
                MentorProfile.query.filter_by(user_id=u.id).delete()
            db.session.delete(u)
        db.session.commit()


@pytest.fixture(scope="session")
def app():
    """
    Session-scoped Flask application fixture.

    Yields a fully initialised Flask app instance configured for testing.
    Pre-cleans any stale matching-service test data before the session and
    performs a final cleanup sweep after the last test in the session exits.
    """
    flask_app = create_app()

    # Override settings that are safe/required for automated testing
    flask_app.config["TESTING"] = True
    flask_app.config["REQUIRE_EMAIL_VERIFICATION"] = False

    # Pre-session cleanup: remove any sentinel rows left by a previous aborted run
    _purge_test_users(flask_app)

    yield flask_app

    # Post-session cleanup: ensure no test data remains in the database
    _purge_test_users(flask_app)
