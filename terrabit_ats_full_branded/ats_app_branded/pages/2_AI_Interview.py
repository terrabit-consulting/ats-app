import streamlit as st, json, re, io, tempfile, os
from lib import db
from lib.llm import LLMClient
from lib.pdf import build_softskills_pdf
from audio_recorder_streamlit import audio_recorder
import openai

st.title("🤖 AI Interview (Voice/Text)")
conn = st.session_state["db_conn"]
api_key = st.secrets["OPENAI_API_KEY"]
llm = LLMClient(api_key=api_key, model="gpt-4o", temperature=0)
ct = st.session_state.get("cost_tracker")
oai = openai.OpenAI(api_key=api_key)

jobs = db.list_jobs(conn)
if not jobs:
    st.info("Create a Job first."); st.stop()

job = st.selectbox("Select Job", jobs, format_func=lambda j: f"#{j['id']} {j['title']}")
apps = db.get_applications_for_job(conn, job["id"])
if not apps:
    st.info("No applications."); st.stop()

app_row = st.selectbox("Candidate", apps, format_func=lambda a: f"{a['candidate_name']} ({a['candidate_email']}) — Score {a['match_score']}%" )
stage = st.selectbox("Interview Stage", ["AI-Screen", "Tech-Round-1", "Tech-Round-2"])

with st.expander("Question Generator"):
    q_prompt = f"""You are an interviewer. Create 5 concise, role-relevant questions for this JD and candidate.
Return JSON list of strings. No preamble.

JD:
{job['jd_text']}

Candidate (LLM context):
{app_row['match_reason']}
"""
    if st.button("Generate Questions / Refresh"):
        try:
            qs_raw, usage_q = llm.chat_with_usage(q_prompt)
            if ct and usage_q: ct.add_chat_cost(usage_q.get("input_tokens",0), usage_q.get("output_tokens",0), feature="interview_qgen")
            questions = json.loads(qs_raw) if qs_raw.strip().startswith("[") else [q.strip("-• ") for q in qs_raw.splitlines() if q.strip()]
            st.session_state["questions"] = questions[:5]; st.success("Questions generated.")
        except Exception as e:
            st.error(f"Failed to parse: {e}")

questions = st.session_state.get("questions", [])
answers = []

if questions:
    st.write("**Answer by voice or text for each question**")
    for i,q in enumerate(questions,1):
        st.markdown(f"**Q{i}. {q}**")
        audio_bytes = audio_recorder(pause_threshold=1.0, sample_rate=41000, text="Record / Stop")
        text_answer = st.text_area(f"Or type your answer {i}", key=f"ans_text_{i}", height=80)
        transcript = ""
        if audio_bytes:
            with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
                tmp.write(audio_bytes); tmp_path = tmp.name
            with open(tmp_path, "rb") as f:
                try:
                    tr = oai.audio.transcriptions.create(model="whisper-1", file=f)
                    transcript = tr.text.strip()
                    if ct:
                        import wave, contextlib
                        with contextlib.closing(wave.open(tmp_path, "rb")) as w:
                            dur = w.getnframes()/float(w.getframerate() or 41000)
                        ct.add_whisper_cost_from_minutes(dur/60.0, feature="interview_stt")
                    st.success(f"Transcribed: {transcript[:120]}{'...' if len(transcript)>120 else ''}")
                except Exception as e:
                    st.error(f"Transcription failed: {e}")
            try: os.remove(tmp_path)
            except: pass

        final_ans = transcript if transcript else text_answer
        answers.append(final_ans)
        st.markdown("---")

    if st.button("🧠 Summarize & Score"):
        a_prompt = f"""Given the interview Q&A below, provide:
- A short competency summary
- Strengths
- Concerns
- A final suitability score [0-100]
Also return a compact JSON object with 1–5 scores for:
- Clarity of Explanation
- Depth of Knowledge
- Relevance of Examples
- Problem Solving Approach
- Communication Skills

Output format:
### Summary
...markdown summary...
Final Score: NN%

<JSON>
{{ "Clarity of Explanation": x, "Depth of Knowledge": x, "Relevance of Examples": x, "Problem Solving Approach": x, "Communication Skills": x }}
</JSON>

Q&A:
{list(zip(questions, answers))}
"""
        notes, usage_s = llm.chat_with_usage(a_prompt)
        if ct and usage_s: ct.add_chat_cost(usage_s.get("input_tokens",0), usage_s.get("output_tokens",0), feature="interview_summary")
        m = re.search(r"Final Score:\s*([0-9]{1,3})%", notes)
        score = int(m.group(1)) if m else 0
        rubric = {"Clarity of Explanation":0,"Depth of Knowledge":0,"Relevance of Examples":0,"Problem Solving Approach":0,"Communication Skills":0}
        jm = re.search(r"<JSON>\s*(\{[\s\S]*?\})\s*</JSON>", notes)
        if jm:
            try:
                rub = json.loads(jm.group(1))
                for k in rubric.keys():
                    if k in rub: rubric[k] = float(rub[k])
            except Exception: pass

        from lib.pdf import build_softskills_pdf
        import tempfile
        overall_5 = sum(rubric.values())/5.0 if sum(rubric.values())>0 else (score/20.0)
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); tmp_pdf.close()
        build_softskills_pdf(tmp_pdf.name, app_row['candidate_name'], job['title'], rubric, overall_5, notes.split("### Summary",1)[-1].strip(), logo_path="branding/logo.png")
        st.download_button("📥 Download Soft Skills PDF", data=open(tmp_pdf.name,"rb").read(), file_name=f"{app_row['candidate_name'].replace(' ','_')}_softskills.pdf", mime="application/pdf")
        st.markdown(notes, unsafe_allow_html=True)
