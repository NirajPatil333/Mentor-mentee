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

        print("\n--- Verifying Database Tables ---")
        inspector = inspect(db.engine)
        table_names = inspector.get_table_names()
        print(f"Tables found in database: {table_names}")

        users_exist = "users" in table_names
        mentor_profiles_exist = "mentor_profiles" in table_names
        mentee_profiles_exist = "mentee_profiles" in table_names
        skills_exist = "skills" in table_names
        user_skills_exist = "user_skills" in table_names
        learning_interests_exist = "learning_interests" in table_names
        mentor_availability_exist = "mentor_availability" in table_names
        mentorship_requests_exist = "mentorship_requests" in table_names
        sessions_exist = "sessions" in table_names
        resources_exist = "resources" in table_names
        progress_exist = "progress" in table_names
        feedback_exist = "feedback" in table_names
        certificates_exist = "certificates" in table_names
        achievements_exist = "achievements" in table_names

        print(f"  - 'users' table exists: {users_exist}")
        print(f"  - 'mentor_profiles' table exists: {mentor_profiles_exist}")
        print(f"  - 'mentee_profiles' table exists: {mentee_profiles_exist}")
        print(f"  - 'skills' table exists: {skills_exist}")
        print(f"  - 'user_skills' table exists: {user_skills_exist}")
        print(f"  - 'learning_interests' table exists: {learning_interests_exist}")
        print(f"  - 'mentor_availability' table exists: {mentor_availability_exist}")
        print(f"  - 'mentorship_requests' table exists: {mentorship_requests_exist}")
        print(f"  - 'sessions' table exists: {sessions_exist}")
        print(f"  - 'resources' table exists: {resources_exist}")
        print(f"  - 'progress' table exists: {progress_exist}")
        print(f"  - 'feedback' table exists: {feedback_exist}")
        print(f"  - 'certificates' table exists: {certificates_exist}")
        print(f"  - 'achievements' table exists: {achievements_exist}")

        if not (users_exist and mentor_profiles_exist and mentee_profiles_exist and skills_exist and user_skills_exist and learning_interests_exist and mentor_availability_exist and mentorship_requests_exist and sessions_exist and resources_exist and progress_exist and feedback_exist and certificates_exist and achievements_exist):
            print("\n[FAILED] Expected tables were not found.")
            return False

        print("\n--- Inspecting 'mentor_profiles' Columns ---")
        for col in inspector.get_columns("mentor_profiles"):
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        print("\n--- Inspecting Foreign Keys in 'mentor_profiles' ---")
        fks = inspector.get_foreign_keys("mentor_profiles")
        fk_verified = False
        for fk in fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["user_id"] and referred_table == "users" and referred_columns == ["id"]:
                fk_verified = True

        if fk_verified:
            print("\n[SUCCESS] Confirmed: 'user_id' in 'mentor_profiles' has a foreign key to 'users.id'.")
        else:
            print("\n[WARNING] Foreign key constraint on 'user_id' -> 'users.id' was not detected.")
            return False

        print("\n--- Inspecting 'mentee_profiles' Columns ---")
        mentee_columns = inspector.get_columns("mentee_profiles")
        mentee_col_names = {col["name"]: col for col in mentee_columns}
        expected_columns = ["id", "user_id", "bio", "education", "learning_goal", "experience_level"]

        for col in mentee_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_columns = [c for c in expected_columns if c not in mentee_col_names]
        if missing_columns:
            print(f"\n[FAILED] Missing columns in 'mentee_profiles': {missing_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'mentee_profiles': {expected_columns}")

        user_id_col = mentee_col_names.get("user_id", {})
        user_id_not_null = not user_id_col.get("nullable", True)

        # Check unique constraint / index on user_id
        unique_constraints = inspector.get_unique_constraints("mentee_profiles")
        unique_indexes = [idx for idx in inspector.get_indexes("mentee_profiles") if idx.get("unique")]
        user_id_is_unique = any(
            uc.get("column_names") == ["user_id"] for uc in unique_constraints
        ) or any(
            idx.get("column_names") == ["user_id"] for idx in unique_indexes
        )

        print(f"  - 'user_id' NOT NULL: {user_id_not_null}")
        print(f"  - 'user_id' UNIQUE: {user_id_is_unique}")

        if not (user_id_not_null and user_id_is_unique):
            print("\n[FAILED] 'user_id' must be UNIQUE and NOT NULL.")
            return False

        print("\n--- Inspecting Foreign Keys in 'mentee_profiles' ---")
        mentee_fks = inspector.get_foreign_keys("mentee_profiles")
        mentee_fk_verified = False
        for fk in mentee_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["user_id"] and referred_table == "users" and referred_columns == ["id"]:
                mentee_fk_verified = True

        if mentee_fk_verified:
            print("\n[SUCCESS] Confirmed: 'user_id' in 'mentee_profiles' has a foreign key to 'users.id'.")
            print("\n[SUCCESS] All checks passed for 'mentee_profiles'!")
        else:
            print("\n[WARNING] Foreign key constraint on 'user_id' -> 'users.id' in 'mentee_profiles' was not detected.")
            return False

        print("\n--- Inspecting 'skills' Columns ---")
        skills_columns = inspector.get_columns("skills")
        skills_col_names = {col["name"]: col for col in skills_columns}
        expected_skill_columns = ["id", "name", "category"]

        for col in skills_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_skill_columns = [c for c in expected_skill_columns if c not in skills_col_names]
        if missing_skill_columns:
            print(f"\n[FAILED] Missing columns in 'skills': {missing_skill_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'skills': {expected_skill_columns}")

        name_col = skills_col_names.get("name", {})
        name_not_null = not name_col.get("nullable", True)

        # Check unique constraint / index on name
        skill_unique_constraints = inspector.get_unique_constraints("skills")
        skill_unique_indexes = [idx for idx in inspector.get_indexes("skills") if idx.get("unique")]
        name_is_unique = any(
            uc.get("column_names") == ["name"] for uc in skill_unique_constraints
        ) or any(
            idx.get("column_names") == ["name"] for idx in skill_unique_indexes
        )

        print(f"  - 'name' NOT NULL: {name_not_null}")
        print(f"  - 'name' UNIQUE: {name_is_unique}")

        if not (name_not_null and name_is_unique):
            print("\n[FAILED] 'name' must be UNIQUE and NOT NULL in 'skills'.")
            return False

        print("\n[SUCCESS] All checks passed for 'skills'!")

        print("\n--- Inspecting 'user_skills' Columns ---")
        user_skills_columns = inspector.get_columns("user_skills")
        user_skills_col_names = {col["name"]: col for col in user_skills_columns}
        expected_user_skill_columns = ["id", "user_id", "skill_id", "proficiency"]

        for col in user_skills_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_user_skill_columns = [c for c in expected_user_skill_columns if c not in user_skills_col_names]
        if missing_user_skill_columns:
            print(f"\n[FAILED] Missing columns in 'user_skills': {missing_user_skill_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'user_skills': {expected_user_skill_columns}")

        print("\n--- Inspecting Foreign Keys in 'user_skills' ---")
        us_fks = inspector.get_foreign_keys("user_skills")
        user_fk_verified = False
        skill_fk_verified = False
        for fk in us_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["user_id"] and referred_table == "users" and referred_columns == ["id"]:
                user_fk_verified = True
            if constrained == ["skill_id"] and referred_table == "skills" and referred_columns == ["id"]:
                skill_fk_verified = True

        if not user_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'user_id' -> 'users.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'user_id' in 'user_skills' has a foreign key to 'users.id'.")

        if not skill_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'skill_id' -> 'skills.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'skill_id' in 'user_skills' has a foreign key to 'skills.id'.")

        print("\n--- Inspecting Unique Constraints in 'user_skills' ---")
        us_unique_constraints = inspector.get_unique_constraints("user_skills")
        us_unique_indexes = [idx for idx in inspector.get_indexes("user_skills") if idx.get("unique")]
        composite_unique = any(
            set(uc.get("column_names", [])) == {"user_id", "skill_id"} for uc in us_unique_constraints
        ) or any(
            set(idx.get("column_names", [])) == {"user_id", "skill_id"} for idx in us_unique_indexes
        )

        print(f"  - Composite UNIQUE(user_id, skill_id): {composite_unique}")
        if not composite_unique:
            print("\n[FAILED] Composite UNIQUE constraint on (user_id, skill_id) was not detected.")
            return False

        print("\n[SUCCESS] All checks passed for 'user_skills'!")

        print("\n--- Inspecting 'learning_interests' Columns ---")
        li_columns = inspector.get_columns("learning_interests")
        li_col_names = {col["name"]: col for col in li_columns}
        expected_li_columns = ["id", "mentee_id", "skill_id", "priority"]

        for col in li_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_li_columns = [c for c in expected_li_columns if c not in li_col_names]
        if missing_li_columns:
            print(f"\n[FAILED] Missing columns in 'learning_interests': {missing_li_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'learning_interests': {expected_li_columns}")

        print("\n--- Inspecting Foreign Keys in 'learning_interests' ---")
        li_fks = inspector.get_foreign_keys("learning_interests")
        mentee_fk_verified = False
        skill_fk_verified = False
        for fk in li_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                mentee_fk_verified = True
            if constrained == ["skill_id"] and referred_table == "skills" and referred_columns == ["id"]:
                skill_fk_verified = True

        if not mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'learning_interests' has a foreign key to 'mentee_profiles.id'.")

        if not skill_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'skill_id' -> 'skills.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'skill_id' in 'learning_interests' has a foreign key to 'skills.id'.")

        print("\n--- Inspecting Unique Constraints in 'learning_interests' ---")
        li_unique_constraints = inspector.get_unique_constraints("learning_interests")
        li_unique_indexes = [idx for idx in inspector.get_indexes("learning_interests") if idx.get("unique")]
        li_composite_unique = any(
            set(uc.get("column_names", [])) == {"mentee_id", "skill_id"} for uc in li_unique_constraints
        ) or any(
            set(idx.get("column_names", [])) == {"mentee_id", "skill_id"} for idx in li_unique_indexes
        )

        print(f"  - Composite UNIQUE(mentee_id, skill_id): {li_composite_unique}")
        if not li_composite_unique:
            print("\n[FAILED] Composite UNIQUE constraint on (mentee_id, skill_id) was not detected.")
            return False

        print("\n[SUCCESS] All checks passed for 'learning_interests'!")

        print("\n--- Inspecting 'mentor_availability' Columns ---")
        ma_columns = inspector.get_columns("mentor_availability")
        ma_col_names = {col["name"]: col for col in ma_columns}
        expected_ma_columns = ["id", "mentor_id", "day_of_week", "start_time", "end_time"]

        for col in ma_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_ma_columns = [c for c in expected_ma_columns if c not in ma_col_names]
        if missing_ma_columns:
            print(f"\n[FAILED] Missing columns in 'mentor_availability': {missing_ma_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'mentor_availability': {expected_ma_columns}")

        # Verify start_time and end_time types
        start_time_col = ma_col_names.get("start_time", {})
        end_time_col = ma_col_names.get("end_time", {})
        start_time_is_time = "TIME" in str(start_time_col.get("type", "")).upper()
        end_time_is_time = "TIME" in str(end_time_col.get("type", "")).upper()

        print(f"  - 'start_time' is TIME type: {start_time_is_time} ({start_time_col.get('type')})")
        print(f"  - 'end_time' is TIME type: {end_time_is_time} ({end_time_col.get('type')})")

        if not (start_time_is_time and end_time_is_time):
            print("\n[FAILED] 'start_time' and 'end_time' must use a TIME-compatible type.")
            return False
        print("[SUCCESS] Confirmed: 'start_time' and 'end_time' use MySQL TIME-compatible type.")

        print("\n--- Inspecting Foreign Keys in 'mentor_availability' ---")
        ma_fks = inspector.get_foreign_keys("mentor_availability")
        mentor_fk_verified = False
        for fk in ma_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentor_id"] and referred_table == "mentor_profiles" and referred_columns == ["id"]:
                mentor_fk_verified = True

        if not mentor_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentor_id' -> 'mentor_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' in 'mentor_availability' has a foreign key to 'mentor_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'mentor_availability'!")

        print("\n--- Inspecting 'mentorship_requests' Columns ---")
        mr_columns = inspector.get_columns("mentorship_requests")
        mr_col_names = {col["name"]: col for col in mr_columns}
        expected_mr_columns = ["id", "mentee_id", "mentor_id", "message", "status", "requested_at", "responded_at"]

        for col in mr_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            default_val = f" DEFAULT {col.get('default')}" if col.get("default") is not None else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default_val}{pk}")

        missing_mr_columns = [c for c in expected_mr_columns if c not in mr_col_names]
        if missing_mr_columns:
            print(f"\n[FAILED] Missing columns in 'mentorship_requests': {missing_mr_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'mentorship_requests': {expected_mr_columns}")

        # Check status default value is 'pending'
        status_col = mr_col_names.get("status", {})
        status_default = status_col.get("default", "")
        from models import MentorshipRequest
        model_status_default = getattr(MentorshipRequest.status.default, 'arg', None)
        status_default_verified = "pending" in str(status_default).lower() or model_status_default == "pending"
        print(f"  - 'status' default is 'pending': {status_default_verified} (DB default: {status_default}, Model default: {model_status_default})")
        if not status_default_verified:
            print("\n[FAILED] 'status' must have a default value of 'pending'.")
            return False

        # Check requested_at is NOT NULL
        requested_at_col = mr_col_names.get("requested_at", {})
        requested_at_not_null = not requested_at_col.get("nullable", True)
        print(f"  - 'requested_at' NOT NULL: {requested_at_not_null}")
        if not requested_at_not_null:
            print("\n[FAILED] 'requested_at' must be NOT NULL.")
            return False

        print("\n--- Inspecting Foreign Keys in 'mentorship_requests' ---")
        mr_fks = inspector.get_foreign_keys("mentorship_requests")
        mentee_fk_verified = False
        mentor_fk_verified = False
        for fk in mr_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                mentee_fk_verified = True
            if constrained == ["mentor_id"] and referred_table == "mentor_profiles" and referred_columns == ["id"]:
                mentor_fk_verified = True

        if not mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'mentorship_requests' has a foreign key to 'mentee_profiles.id'.")

        if not mentor_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentor_id' -> 'mentor_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' in 'mentorship_requests' has a foreign key to 'mentor_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'mentorship_requests'!")

        print("\n--- Inspecting 'sessions' Columns ---")
        sess_columns = inspector.get_columns("sessions")
        sess_col_names = {col["name"]: col for col in sess_columns}
        expected_sess_columns = [
            "id", "request_id", "mentor_id", "mentee_id",
            "title", "description", "scheduled_date",
            "start_time", "end_time", "meeting_room", "status", "created_at"
        ]

        for col in sess_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            default_val = f" DEFAULT {col.get('default')}" if col.get("default") is not None else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default_val}{pk}")

        missing_sess_columns = [c for c in expected_sess_columns if c not in sess_col_names]
        if missing_sess_columns:
            print(f"\n[FAILED] Missing columns in 'sessions': {missing_sess_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'sessions': {expected_sess_columns}")

        # Check scheduled_date uses a MySQL DATE-compatible type
        scheduled_date_col = sess_col_names.get("scheduled_date", {})
        date_type_verified = "DATE" in str(scheduled_date_col.get("type", "")).upper()
        print(f"  - 'scheduled_date' is DATE type: {date_type_verified} ({scheduled_date_col.get('type')})")
        if not date_type_verified:
            print("\n[FAILED] 'scheduled_date' must use a DATE-compatible type.")
            return False
        print("[SUCCESS] Confirmed: 'scheduled_date' uses MySQL DATE-compatible type.")

        # Check start_time and end_time use MySQL TIME-compatible types
        start_time_col = sess_col_names.get("start_time", {})
        end_time_col = sess_col_names.get("end_time", {})
        start_time_is_time = "TIME" in str(start_time_col.get("type", "")).upper()
        end_time_is_time = "TIME" in str(end_time_col.get("type", "")).upper()
        print(f"  - 'start_time' is TIME type: {start_time_is_time} ({start_time_col.get('type')})")
        print(f"  - 'end_time' is TIME type: {end_time_is_time} ({end_time_col.get('type')})")
        if not (start_time_is_time and end_time_is_time):
            print("\n[FAILED] 'start_time' and 'end_time' must use a TIME-compatible type.")
            return False
        print("[SUCCESS] Confirmed: 'start_time' and 'end_time' use MySQL TIME-compatible types.")

        # Check status default is 'scheduled'
        status_col = sess_col_names.get("status", {})
        status_default = status_col.get("default", "")
        from models import Session
        model_status_default = getattr(Session.status.default, 'arg', None)
        status_default_verified = "scheduled" in str(status_default).lower() or model_status_default == "scheduled"
        print(f"  - 'status' default is 'scheduled': {status_default_verified} (DB default: {status_default}, Model default: {model_status_default})")
        if not status_default_verified:
            print("\n[FAILED] 'status' must have default value 'scheduled'.")
            return False

        print("\n--- Inspecting Foreign Keys in 'sessions' ---")
        sess_fks = inspector.get_foreign_keys("sessions")
        req_fk_verified = False
        mentor_fk_verified = False
        mentee_fk_verified = False
        for fk in sess_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["request_id"] and referred_table == "mentorship_requests" and referred_columns == ["id"]:
                req_fk_verified = True
            if constrained == ["mentor_id"] and referred_table == "mentor_profiles" and referred_columns == ["id"]:
                mentor_fk_verified = True
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                mentee_fk_verified = True

        if not req_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'request_id' -> 'mentorship_requests.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'request_id' in 'sessions' has a foreign key to 'mentorship_requests.id'.")

        if not mentor_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentor_id' -> 'mentor_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' in 'sessions' has a foreign key to 'mentor_profiles.id'.")

        if not mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'sessions' has a foreign key to 'mentee_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'sessions'!")

        print("\n--- Inspecting 'resources' Columns ---")
        res_columns = inspector.get_columns("resources")
        res_col_names = {col["name"]: col for col in res_columns}
        expected_res_columns = [
            "id", "mentor_id", "mentee_id", "title", "description",
            "resource_type", "resource_url", "file_path", "created_at"
        ]

        for col in res_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_res_columns = [c for c in expected_res_columns if c not in res_col_names]
        if missing_res_columns:
            print(f"\n[FAILED] Missing columns in 'resources': {missing_res_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'resources': {expected_res_columns}")

        # Check mentee_id is nullable
        mentee_id_col = res_col_names.get("mentee_id", {})
        mentee_id_is_nullable = mentee_id_col.get("nullable", False)
        print(f"  - 'mentee_id' is nullable: {mentee_id_is_nullable}")
        if not mentee_id_is_nullable:
            print("\n[FAILED] 'mentee_id' must be nullable.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' is nullable in 'resources'.")

        # Check created_at is NOT NULL
        created_at_col = res_col_names.get("created_at", {})
        created_at_not_null = not created_at_col.get("nullable", True)
        print(f"  - 'created_at' NOT NULL: {created_at_not_null}")
        if not created_at_not_null:
            print("\n[FAILED] 'created_at' must be NOT NULL.")
            return False
        print("[SUCCESS] Confirmed: 'created_at' is NOT NULL in 'resources'.")

        print("\n--- Inspecting Foreign Keys in 'resources' ---")
        res_fks = inspector.get_foreign_keys("resources")
        mentor_fk_verified = False
        mentee_fk_verified = False
        for fk in res_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentor_id"] and referred_table == "mentor_profiles" and referred_columns == ["id"]:
                mentor_fk_verified = True
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                mentee_fk_verified = True

        if not mentor_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentor_id' -> 'mentor_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' in 'resources' has a foreign key to 'mentor_profiles.id'.")

        if not mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'resources' has a foreign key to 'mentee_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'resources'!")

        print("\n--- Inspecting 'progress' Columns ---")
        prog_columns = inspector.get_columns("progress")
        prog_col_names = {col["name"]: col for col in prog_columns}
        expected_prog_columns = [
            "id", "mentee_id", "mentor_id", "skill_id", "goal",
            "description", "progress_percentage", "status", "updated_at"
        ]

        for col in prog_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            default_val = f" DEFAULT {col.get('default')}" if col.get("default") is not None else ""
            print(f"  - {col['name']}: {col['type']} {nullable}{default_val}{pk}")

        missing_prog_columns = [c for c in expected_prog_columns if c not in prog_col_names]
        if missing_prog_columns:
            print(f"\n[FAILED] Missing columns in 'progress': {missing_prog_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'progress': {expected_prog_columns}")

        # Check mentor_id is nullable
        mentor_id_col = prog_col_names.get("mentor_id", {})
        mentor_id_is_nullable = mentor_id_col.get("nullable", False)
        print(f"  - 'mentor_id' is nullable: {mentor_id_is_nullable}")
        if not mentor_id_is_nullable:
            print("\n[FAILED] 'mentor_id' must be nullable.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' is nullable in 'progress'.")

        # Check progress_percentage has default 0
        prog_pct_col = prog_col_names.get("progress_percentage", {})
        prog_pct_default = prog_pct_col.get("default", "")
        from models import Progress
        model_pct_default = getattr(Progress.progress_percentage.default, 'arg', None)
        prog_pct_default_verified = "0" in str(prog_pct_default) or model_pct_default == 0
        print(f"  - 'progress_percentage' default is 0: {prog_pct_default_verified} (DB default: {prog_pct_default}, Model default: {model_pct_default})")
        if not prog_pct_default_verified:
            print("\n[FAILED] 'progress_percentage' must have default 0.")
            return False

        # Check status has default 'not_started'
        status_col = prog_col_names.get("status", {})
        status_default = status_col.get("default", "")
        model_status_default = getattr(Progress.status.default, 'arg', None)
        status_default_verified = "not_started" in str(status_default).lower() or model_status_default == "not_started"
        print(f"  - 'status' default is 'not_started': {status_default_verified} (DB default: {status_default}, Model default: {model_status_default})")
        if not status_default_verified:
            print("\n[FAILED] 'status' must have default 'not_started'.")
            return False

        # Check updated_at is NOT NULL
        updated_at_col = prog_col_names.get("updated_at", {})
        updated_at_not_null = not updated_at_col.get("nullable", True)
        print(f"  - 'updated_at' NOT NULL: {updated_at_not_null}")
        if not updated_at_not_null:
            print("\n[FAILED] 'updated_at' must be NOT NULL.")
            return False
        print("[SUCCESS] Confirmed: 'updated_at' is NOT NULL in 'progress'.")

        # Check CHECK constraint on progress_percentage (0 to 100)
        try:
            check_constraints = inspector.get_check_constraints("progress")
        except Exception:
            check_constraints = []
        model_checks = [c for c in Progress.__table__.constraints if isinstance(c, db.CheckConstraint)]
        has_check = any("progress_percentage" in str(c.get("sqltext", "")).lower() for c in check_constraints) or len(model_checks) > 0
        print(f"  - 'progress_percentage' CHECK constraint (0-100): {has_check} (DB checks: {check_constraints}, Model checks: {[c.sqltext.text for c in model_checks]})")
        if not has_check:
            print("\n[FAILED] CHECK constraint on progress_percentage was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'progress_percentage' has a CHECK constraint for 0–100.")

        print("\n--- Inspecting Foreign Keys in 'progress' ---")
        prog_fks = inspector.get_foreign_keys("progress")
        mentee_fk_verified = False
        mentor_fk_verified = False
        skill_fk_verified = False
        for fk in prog_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                mentee_fk_verified = True
            if constrained == ["mentor_id"] and referred_table == "mentor_profiles" and referred_columns == ["id"]:
                mentor_fk_verified = True
            if constrained == ["skill_id"] and referred_table == "skills" and referred_columns == ["id"]:
                skill_fk_verified = True

        if not mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'progress' has a foreign key to 'mentee_profiles.id'.")

        if not mentor_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentor_id' -> 'mentor_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' in 'progress' has a foreign key to 'mentor_profiles.id'.")

        if not skill_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'skill_id' -> 'skills.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'skill_id' in 'progress' has a foreign key to 'skills.id'.")

        print("\n[SUCCESS] All checks passed for 'progress'!")

        print("\n--- Inspecting 'feedback' Columns ---")
        fb_columns = inspector.get_columns("feedback")
        fb_col_names = {col["name"]: col for col in fb_columns}
        expected_fb_columns = [
            "id", "session_id", "mentor_id", "mentee_id", "rating", "comment", "created_at"
        ]

        for col in fb_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_fb_columns = [c for c in expected_fb_columns if c not in fb_col_names]
        if missing_fb_columns:
            print(f"\n[FAILED] Missing columns in 'feedback': {missing_fb_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'feedback': {expected_fb_columns}")

        # Check rating CHECK constraint (1 to 5)
        try:
            fb_checks = inspector.get_check_constraints("feedback")
        except Exception:
            fb_checks = []
        from models import Feedback, Certificate
        fb_model_checks = [c for c in Feedback.__table__.constraints if isinstance(c, db.CheckConstraint)]
        has_fb_check = any("rating" in str(c.get("sqltext", "")).lower() for c in fb_checks) or len(fb_model_checks) > 0
        print(f"  - 'rating' CHECK constraint (1-5): {has_fb_check} (DB checks: {fb_checks}, Model checks: {[c.sqltext.text for c in fb_model_checks]})")
        if not has_fb_check:
            print("\n[FAILED] CHECK constraint on rating was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'rating' has a CHECK constraint for 1–5.")

        # Check composite UNIQUE(session_id, mentee_id)
        fb_unique_constraints = inspector.get_unique_constraints("feedback")
        fb_unique_indexes = [idx for idx in inspector.get_indexes("feedback") if idx.get("unique")]
        fb_composite_unique = any(
            set(uc.get("column_names", [])) == {"session_id", "mentee_id"} for uc in fb_unique_constraints
        ) or any(
            set(idx.get("column_names", [])) == {"session_id", "mentee_id"} for idx in fb_unique_indexes
        )
        print(f"  - Composite UNIQUE(session_id, mentee_id): {fb_composite_unique}")
        if not fb_composite_unique:
            print("\n[FAILED] Composite UNIQUE constraint on (session_id, mentee_id) was not detected.")
            return False
        print("[SUCCESS] Confirmed: UNIQUE(session_id, mentee_id) constraint exists.")

        print("\n--- Inspecting Foreign Keys in 'feedback' ---")
        fb_fks = inspector.get_foreign_keys("feedback")
        sess_fk_verified = False
        mentor_fk_verified = False
        mentee_fk_verified = False
        for fk in fb_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["session_id"] and referred_table == "sessions" and referred_columns == ["id"]:
                sess_fk_verified = True
            if constrained == ["mentor_id"] and referred_table == "mentor_profiles" and referred_columns == ["id"]:
                mentor_fk_verified = True
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                mentee_fk_verified = True

        if not sess_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'session_id' -> 'sessions.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'session_id' in 'feedback' has a foreign key to 'sessions.id'.")

        if not mentor_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentor_id' -> 'mentor_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentor_id' in 'feedback' has a foreign key to 'mentor_profiles.id'.")

        if not mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'feedback' has a foreign key to 'mentee_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'feedback'!")

        print("\n--- Inspecting 'certificates' Columns ---")
        cert_columns = inspector.get_columns("certificates")
        cert_col_names = {col["name"]: col for col in cert_columns}
        expected_cert_columns = [
            "id", "mentee_id", "title", "issuer", "issue_date", "file_path", "file_type", "created_at"
        ]

        for col in cert_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_cert_columns = [c for c in expected_cert_columns if c not in cert_col_names]
        if missing_cert_columns:
            print(f"\n[FAILED] Missing columns in 'certificates': {missing_cert_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'certificates': {expected_cert_columns}")

        # Check issue_date is DATE-compatible
        issue_date_col = cert_col_names.get("issue_date", {})
        issue_date_is_date = "DATE" in str(issue_date_col.get("type", "")).upper()
        print(f"  - 'issue_date' is DATE type: {issue_date_is_date} ({issue_date_col.get('type')})")
        if not issue_date_is_date:
            print("\n[FAILED] 'issue_date' must use a DATE-compatible type.")
            return False
        print("[SUCCESS] Confirmed: 'issue_date' uses MySQL DATE-compatible type.")

        # Check file_path and file_type are NOT NULL
        file_path_col = cert_col_names.get("file_path", {})
        file_type_col = cert_col_names.get("file_type", {})
        file_path_not_null = not file_path_col.get("nullable", True)
        file_type_not_null = not file_type_col.get("nullable", True)
        print(f"  - 'file_path' NOT NULL: {file_path_not_null}")
        print(f"  - 'file_type' NOT NULL: {file_type_not_null}")
        if not (file_path_not_null and file_type_not_null):
            print("\n[FAILED] Both 'file_path' and 'file_type' must be NOT NULL.")
            return False
        print("[SUCCESS] Confirmed: 'file_path' and 'file_type' are NOT NULL.")

        print("\n--- Inspecting Foreign Keys in 'certificates' ---")
        cert_fks = inspector.get_foreign_keys("certificates")
        cert_mentee_fk_verified = False
        for fk in cert_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                cert_mentee_fk_verified = True

        if not cert_mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'certificates' has a foreign key to 'mentee_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'certificates'!")

        print("\n--- Inspecting 'achievements' Columns ---")
        ach_columns = inspector.get_columns("achievements")
        ach_col_names = {col["name"]: col for col in ach_columns}
        expected_ach_columns = [
            "id", "mentee_id", "title", "description", "achievement_date", "achievement_url", "created_at"
        ]

        for col in ach_columns:
            pk = " (PRIMARY KEY)" if col.get("primary_key") else ""
            nullable = "NULL" if col.get("nullable") else "NOT NULL"
            print(f"  - {col['name']}: {col['type']} {nullable}{pk}")

        missing_ach_columns = [c for c in expected_ach_columns if c not in ach_col_names]
        if missing_ach_columns:
            print(f"\n[FAILED] Missing columns in 'achievements': {missing_ach_columns}")
            return False
        print(f"\n[SUCCESS] All expected columns exist in 'achievements': {expected_ach_columns}")

        # Check mentee_id, title, achievement_date, created_at are NOT NULL
        mentee_id_col = ach_col_names.get("mentee_id", {})
        title_col = ach_col_names.get("title", {})
        ach_date_col = ach_col_names.get("achievement_date", {})
        created_at_col = ach_col_names.get("created_at", {})

        mentee_id_not_null = not mentee_id_col.get("nullable", True)
        title_not_null = not title_col.get("nullable", True)
        ach_date_not_null = not ach_date_col.get("nullable", True)
        created_at_not_null = not created_at_col.get("nullable", True)

        print(f"  - 'mentee_id' NOT NULL: {mentee_id_not_null}")
        print(f"  - 'title' NOT NULL: {title_not_null}")
        print(f"  - 'achievement_date' NOT NULL: {ach_date_not_null}")
        print(f"  - 'created_at' NOT NULL: {created_at_not_null}")

        if not (mentee_id_not_null and title_not_null and ach_date_not_null and created_at_not_null):
            print("\n[FAILED] Required columns ('mentee_id', 'title', 'achievement_date', 'created_at') must be NOT NULL.")
            return False

        # Check description and achievement_url are nullable
        desc_col = ach_col_names.get("description", {})
        url_col = ach_col_names.get("achievement_url", {})
        desc_nullable = desc_col.get("nullable", False)
        url_nullable = url_col.get("nullable", False)

        print(f"  - 'description' nullable: {desc_nullable}")
        print(f"  - 'achievement_url' nullable: {url_nullable}")

        if not (desc_nullable and url_nullable):
            print("\n[FAILED] 'description' and 'achievement_url' must be nullable.")
            return False

        # Check achievement_date is DATE-compatible
        ach_date_is_date = "DATE" in str(ach_date_col.get("type", "")).upper()
        print(f"  - 'achievement_date' is DATE type: {ach_date_is_date} ({ach_date_col.get('type')})")
        if not ach_date_is_date:
            print("\n[FAILED] 'achievement_date' must use a DATE-compatible type.")
            return False

        print("\n--- Inspecting Foreign Keys in 'achievements' ---")
        ach_fks = inspector.get_foreign_keys("achievements")
        ach_mentee_fk_verified = False
        for fk in ach_fks:
            constrained = fk.get("constrained_columns")
            referred_table = fk.get("referred_table")
            referred_columns = fk.get("referred_columns")
            print(f"  - Constraint '{fk.get('name')}': {constrained} -> {referred_table}.{referred_columns}")
            if constrained == ["mentee_id"] and referred_table == "mentee_profiles" and referred_columns == ["id"]:
                ach_mentee_fk_verified = True

        if not ach_mentee_fk_verified:
            print("\n[FAILED] Foreign key constraint on 'mentee_id' -> 'mentee_profiles.id' was not detected.")
            return False
        print("[SUCCESS] Confirmed: 'mentee_id' in 'achievements' has a foreign key to 'mentee_profiles.id'.")

        print("\n[SUCCESS] All checks passed for 'achievements'!")
        return True


if __name__ == "__main__":
    create_and_verify_tables()
