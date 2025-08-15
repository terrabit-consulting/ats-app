import re
def build_match_prompt(jd_text, resume_text, candidate_name):
    return f"""You are a Recruiter Assistant. Compare the resume to the JD and output:\n\n**Name**: {candidate_name}\n**Score**: [0-100]%\n\n**Reason**:\n- Role Match: ...\n- Skill Match: ...\n- Major Gaps: ...\n\nAdd 'Warning:' only if Score < 70.\n\nJD:\n{jd_text}\n\nResume:\n{resume_text}\n"""
def parse_score(md):
    m = re.search(r"Score\*\*:?,?\s*([0-9]{1,3})%", md) or re.search(r"Score:\s*([0-9]{1,3})%", md)
    try: return max(0, min(100, int(m.group(1)))) if m else 0
    except: return 0
