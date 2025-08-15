CREATE TABLE IF NOT EXISTS jobs (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT, department TEXT, location TEXT, jd_text TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS candidates (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT, email TEXT, phone TEXT, location TEXT, raw_text TEXT, source_file TEXT, created_at TEXT
);
CREATE TABLE IF NOT EXISTS applications (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  job_id INTEGER, candidate_id INTEGER,
  match_score INTEGER, match_reason TEXT, status TEXT,
  created_at TEXT, updated_at TEXT
);
CREATE TABLE IF NOT EXISTS interviews (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  application_id INTEGER, stage TEXT,
  questions_json TEXT, answers_json TEXT,
  ai_notes TEXT, ai_score INTEGER,
  scheduled_at TEXT, completed_at TEXT
);
