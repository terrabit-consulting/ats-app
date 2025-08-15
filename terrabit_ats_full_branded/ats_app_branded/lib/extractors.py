import re
from functools import lru_cache

EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[A-Za-z]{2,}")
BLOCKLIST = {"developer","engineer","resume","cv","india","bangalore","python","java","azure","aws","servers"}

@lru_cache
def _maybe_nlp():
    try:
        import spacy
        return spacy.load("en_core_web_sm")
    except Exception:
        return None

def extract_email(text: str) -> str:
    m = EMAIL_RE.search(text or "")
    return m.group(0) if m else "Not found"

def extract_name_heuristics(text: str) -> str | None:
    for _, val in re.findall(r"(?i)(Candidate Name|Name)\s*[:\-–]\s*(.+)", text or ""):
        name = val.strip().title()
        if 2 <= len(name.split()) <= 4 and len(name) <= 60:
            return name
    m = re.search(r"(?i)Resume of\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})", text or "")
    if m:
        return m.group(1).strip().title()
    return None

def extract_name_spacy(text: str) -> str | None:
    nlp = _maybe_nlp()
    if not nlp:
        return None
    doc = nlp("\n".join((text or "").splitlines()[:50]))
    for ent in doc.ents:
        if ent.label_ == "PERSON":
            cand = ent.text.strip()
            if 2 <= len(cand.split()) <= 4 and len(cand) <= 60 and not any(w in cand.lower() for w in BLOCKLIST):
                return cand.title()
    return None

def extract_name_smart(text: str, llm=None) -> str:
    name = extract_name_heuristics(text) or extract_name_spacy(text)
    if name:
        return name
    if llm is None:
        return "Name Not Found"
    prompt = f"""Extract ONLY the candidate's full name (2–4 words).
If unsure, return exactly: Name Not Found

Text:
{ "\n".join((text or "").splitlines()[:60]) }"""
    ans = (llm.chat(prompt) or "").strip()
    if ("@" in ans) or (len(ans.split()) > 5) or any(w in ans.lower() for w in BLOCKLIST) or ans.lower().startswith("name not found"):
        return "Name Not Found"
    return ans.title()
