import re
from functools import lru_cache
@lru_cache
def _nlp():
    import spacy; return spacy.load("en_core_web_sm")

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}")
BLOCKLIST = {"developer","engineer","resume","cv","india","bangalore","python","java","azure","aws","servers"}

def extract_email(text):
    m = EMAIL_RE.search(text or ""); return m.group(0) if m else "Not found"

def extract_name_heuristics(text):
    for _, val in re.findall(r"(?i)(Candidate Name|Name)\s*[:\-–]\s*(.+)", text):
        name = val.strip().title()
        if 2 <= len(name.split()) <= 4 and len(name) <= 60: return name
    m = re.search(r"(?i)Resume of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", text)
    if m: return m.group(1).strip().title()
    return None

def extract_name_spacy(text):
    doc = _nlp()("\n".join(text.splitlines()[:50]))
    cands=[e.text.strip() for e in doc.ents if e.label_=="PERSON" and 2<=len(e.text.split())<=4]
    for c in cands:
        if not any(w in c.lower() for w in BLOCKLIST) and len(c) <= 60: return c.title()
    return None

def extract_name_smart(text, llm=None):
    n = extract_name_heuristics(text) or extract_name_spacy(text)
    if n: return n
    if llm is None: return "Name Not Found"
    prompt = f"""Extract ONLY the candidate full name (2–4 words). If unsure, return 'Name Not Found'.\n\nText:\n{ '\n'.join(text.splitlines()[:60]) }"""
    ans = (llm.chat(prompt) or "").strip()
    if ("@" in ans) or (len(ans.split())>5) or any(w in ans.lower() for w in BLOCKLIST) or ans.lower().startswith("name not found"):
        return "Name Not Found"
    return ans.title()
