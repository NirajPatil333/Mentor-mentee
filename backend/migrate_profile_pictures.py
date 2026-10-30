"""
Idempotent and safe database migration script for profile picture support.
Adds 'profile_picture' column to the 'users' table if not already present.
"""

import sys
import os

# Ensure backend root is on sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db
from sqlalchemy import text


def migrate():
    with app.app_context():
        # Check existing columns in 'users' table
        inspector_cols = db.session.execute(text("DESCRIBE users")).fetchall()
        existing_column_names = {col[0] for col in inspector_cols}

        if 'profile_picture' not in existing_column_names:
            print("Adding 'profile_picture' column to 'users' table...")
            db.session.execute(text("ALTER TABLE users ADD COLUMN profile_picture VARCHAR(255) NULL"))
            db.session.commit()
            print("[SUCCESS] 'profile_picture' column added to 'users' table.")
        else:
            print("[INFO] 'profile_picture' column already exists in 'users' table.")

        print("Migration completed successfully.")


def rollback():
    """
    Rolls back the migration by dropping 'profile_picture' column from 'users'.
    """
    with app.app_context():
        inspector_cols = db.session.execute(text("DESCRIBE users")).fetchall()
        existing_column_names = {col[0] for col in inspector_cols}

        if 'profile_picture' in existing_column_names:
            print("Dropping 'profile_picture' column from 'users' table...")
            db.session.execute(text("ALTER TABLE users DROP COLUMN profile_picture"))
            db.session.commit()
            print("[SUCCESS] 'profile_picture' column dropped.")
        else:
            print("[INFO] 'profile_picture' column not present, skipping.")

        print("Rollback completed successfully.")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'rollback':
        rollback()
    else:
        migrate()
