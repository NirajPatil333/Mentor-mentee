import datetime
import os
from app import app, db
from sqlalchemy import text

def backup():
    with app.app_context():
        ts = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(os.path.dirname(__file__), f"backup_mentor_mentee_db_{ts}.sql")
        tables = [t[0] for t in db.session.execute(text("SHOW TABLES")).fetchall()]
        print(f"Backing up {len(tables)} tables to {backup_file}...")
        with open(backup_file, "w", encoding="utf-8") as f:
            f.write("SET FOREIGN_KEY_CHECKS=0;\n\n")
            for t in tables:
                ct = db.session.execute(text(f"SHOW CREATE TABLE `{t}`")).fetchone()[1]
                f.write(f"DROP TABLE IF EXISTS `{t}`;\n{ct};\n\n")
                rows = db.session.execute(text(f"SELECT * FROM `{t}`")).mappings().all()
                for r in rows:
                    cols = ", ".join([f"`{k}`" for k in r.keys()])
                    vals = []
                    for v in r.values():
                        if v is None:
                            vals.append("NULL")
                        elif isinstance(v, (int, float)):
                            vals.append(str(v))
                        else:
                            s = str(v).replace("\\", "\\\\").replace("'", "\\'")
                            vals.append(f"'{s}'")
                    f.write(f"INSERT INTO `{t}` ({cols}) VALUES ({', '.join(vals)});\n")
                f.write("\n")
            f.write("SET FOREIGN_KEY_CHECKS=1;\n")
        print(f"Database backup successfully saved: {backup_file}")
        return backup_file

if __name__ == "__main__":
    backup()
