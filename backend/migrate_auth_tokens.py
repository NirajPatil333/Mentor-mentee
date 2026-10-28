"""
Idempotent and safe database migration script for user email verification and password reset.

Requirements:
- Checks if 'is_verified' was newly added during this migration execution.
- If and ONLY IF 'is_verified' was newly added, marks pre-existing accounts as verified.
- If 'is_verified' already exists, leaves all verification statuses untouched.
- Re-running the migration must never mark unverified accounts as verified.
"""

from app import app, db
from sqlalchemy import text


def migrate():
    with app.app_context():
        # Check existing columns in 'users' table
        inspector_cols = db.session.execute(text("DESCRIBE users")).fetchall()
        existing_column_names = {col[0] for col in inspector_cols}

        is_verified_newly_added = False

        if 'is_verified' not in existing_column_names:
            print("Adding 'is_verified' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN is_verified BOOLEAN NOT NULL DEFAULT FALSE"))
            is_verified_newly_added = True
        else:
            print("'is_verified' column already exists.")

        if 'email_verification_token_hash' not in existing_column_names:
            print("Adding 'email_verification_token_hash' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN email_verification_token_hash VARCHAR(64) NULL"))
        else:
            print("'email_verification_token_hash' column already exists.")

        if 'email_verification_sent_at' not in existing_column_names:
            print("Adding 'email_verification_sent_at' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN email_verification_sent_at DATETIME NULL"))
        else:
            print("'email_verification_sent_at' column already exists.")

        if 'reset_password_token_hash' not in existing_column_names:
            print("Adding 'reset_password_token_hash' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN reset_password_token_hash VARCHAR(64) NULL"))
        else:
            print("'reset_password_token_hash' column already exists.")

        if 'reset_password_sent_at' not in existing_column_names:
            print("Adding 'reset_password_sent_at' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN reset_password_sent_at DATETIME NULL"))
        else:
            print("'reset_password_sent_at' column already exists.")

        db.session.commit()

        # Mark existing accounts as verified ONLY IF 'is_verified' was newly added in this run
        if is_verified_newly_added:
            print("Marking pre-existing accounts as verified...")
            updated = db.session.execute(text("UPDATE users SET is_verified = TRUE WHERE is_verified = FALSE"))
            db.session.commit()
            print(f"Pre-existing accounts marked verified: {updated.rowcount}")
        else:
            print("Skipping bulk verification update: 'is_verified' already existed prior to this run.")

        print("Migration completed successfully.")


def rollback():
    """
    Rolls back the migration by dropping newly added columns if they exist.
    Note: Restoring the full SQL backup will overwrite changes made after the backup.
    """
    with app.app_context():
        inspector_cols = db.session.execute(text("DESCRIBE users")).fetchall()
        existing_column_names = {col[0] for col in inspector_cols}

        columns_to_drop = [
            'reset_password_sent_at',
            'reset_password_token_hash',
            'email_verification_sent_at',
            'email_verification_token_hash',
            'is_verified'
        ]

        for col in columns_to_drop:
            if col in existing_column_names:
                print(f"Dropping column '{col}'...")
                db.session.execute(text(f"ALTER TABLE users DROP COLUMN {col}"))
            else:
                print(f"Column '{col}' not present, skipping.")

        db.session.commit()
        print("Rollback completed successfully.")


if __name__ == '__main__':
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
