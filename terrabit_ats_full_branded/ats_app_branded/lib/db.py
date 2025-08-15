import sqlite3, os, json, datetime

def connect(db_path="ats.db"):
    conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def now():
    return datetime.datetime.utcnow().isoformat(timespec="seconds")

def init(conn):
    cur = conn.cursor()
    schema_path = os.path.join(os.path.dirname(__file__), "schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        cur.executescript(f.read())
    conn.commit()

def add_job(conn, title, department, location, jd_text):
    cur = conn.cursor()
    cur.execute("INSERT INTO jobs(title,department,location,jd_text,created_at) VALUES(?,?,?,?,?)",
                (title,department,location,jd_text,now()))
    conn.commit()
    return cur.lastrowid

def list_jobs(conn):
    return conn.execute("SELECT * FROM jobs ORDER BY id DESC").fetchall()

def add_candidate(conn, name, email, phone, location, raw_text, source_file):
    cur = conn.cursor()
    cur.execute("""INSERT INTO candidates(name,email,phone,location,raw_text,source_file,created_at)
                 VALUES(?,?,?,?,?,?,?)""", (name,email,phone,location,raw_text,source_file,now()))
    conn.commit()
    return cur.lastrowid

def add_application(conn, job_id, candidate_id, match_score, match_reason, status="New"):
    cur = conn.cursor()
    cur.execute("""INSERT INTO applications(job_id,candidate_id,match_score,match_reason,status,created_at,updated_at)
                 VALUES(?,?,?,?,?,?,?)""", (job_id,candidate_id,match_score,match_reason,status,now(),now()))
    conn.commit()
    return cur.lastrowid

def update_application_status(conn, app_id, status):
    conn.execute("UPDATE applications SET status=?, updated_at=? WHERE id=?", (status, now(), app_id))
    conn.commit()

def get_applications_for_job(conn, job_id):
    q = """SELECT a.*, c.name AS candidate_name, c.email AS candidate_email
           FROM applications a JOIN candidates c ON c.id=a.candidate_id
           WHERE a.job_id=? ORDER BY a.match_score DESC"""
    return conn.execute(q, (job_id,)).fetchall()

def add_interview(conn, application_id, stage, questions, answers=None, ai_notes=None, ai_score=None, scheduled_at=None):
    cur = conn.cursor()
    cur.execute("""INSERT INTO interviews(application_id, stage, questions_json, answers_json, ai_notes, ai_score, scheduled_at, completed_at)
                 VALUES(?,?,?,?,?,?,?,?)""", (application_id, stage, json.dumps(questions),
                 json.dumps(answers) if answers else None, ai_notes, ai_score, scheduled_at, None))
    conn.commit()
    return cur.lastrowid

def complete_interview(conn, interview_id, answers, notes, score):
    conn.execute("""UPDATE interviews SET answers_json=?, ai_notes=?, ai_score=?, completed_at=? WHERE id=?""" ,
                 (answers, notes, score, now(), interview_id))
    conn.commit()
