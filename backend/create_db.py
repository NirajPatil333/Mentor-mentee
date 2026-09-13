"""
Database table creation and verification script.
Uses SQLAlchemy's db.create_all() within the Flask application context.
"""

from app import app, db
from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError


def create_and_verify_tables():
    with app.app_context():
        print("Executing db.create_all() inside Flask application context...")
        try:
            db.create_all()
            print("db.create_all() executed successfully.")
        except OperationalError as e:
            if "1045" in str(e):
                print("\n[AUTHENTICATION ERROR] Access denied for MySQL user 'root'.")
                print("Please set your actual MySQL root password in 'backend/.env' (DB_PASSWORD=...).")
            elif "1049" in str(e):
                print("\n[DATABASE NOT FOUND] Database 'mentor_mentee_db' does not exist in MySQL.")
                print("Please create the database first: CREATE DATABASE mentor_mentee_db;")
            else:
                print(f"\n[DATABASE ERROR] {e}")
            return False

        print("\nVerifying database tables...")
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(f"Tables found in database: {table_names}")

        if "users" in table_names:
            print("\n[SUCCESS] 'users' table exists in MySQL database!")
            print("Columns in 'users' table:")
            for col in inspector.get_columns("users"):
                pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
                nullable = "NULL" if col.get("nullable") else "NOT NULL"
                print(f"  - {col['name']}: {col['type']} {nullable}{pk}")
            return True
        else:
            print("\n[FAILED] 'users' table was not found.")
            return False


if __name__ == "__main__":
    create_and_verify_tables()
