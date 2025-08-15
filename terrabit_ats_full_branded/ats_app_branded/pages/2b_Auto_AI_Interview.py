import streamlit as st, json, re, os, tempfile
from lib import db
from lib.llm import LLMClient
from lib.pdf import build_softskills_pdf
from audio_recorder_streamlit import audio_recorder

st.title("🗣️ Auto AI Interview (Voice-led)")
conn = st.session_state["db_conn"]
api_key = st.secrets["OPENAI_API_KEY"]
llm = LLMClient(api_key=api_key, model="gpt-4o", temperature=0)
ct = st.session_state.get("cost_tracker")
# Audio helper that works for OpenAI v1.x and v0.x
try:
    from openai import OpenAI
    _SDK = "v1"
    oai_client = OpenAI(api_key=api_key)
except Exception:
    import openai as _oai
    _SDK = "v0"
    _oai.api_key = api_key
    oai_client = _oai

def whisper_transcribe(file_obj):
    if _SDK == "v1":
        return oai_client.audio.transcriptions.create(model="whisper-1", file=file_obj).text
    else:
        # v0.x
        return oai_client.Audio.transcriptions.create(model="whisper-1", file=file_obj)["text"]

def tts_bytes(text: str):
    if _SDK == "v1":
        speech = oai_client.audio.speech.create(model="gpt-4o-mini-tts", voice="alloy", input=text)
        return speech.read()
    else:
        # No official TTS in 0.x; skip
        return b""
jobs = db.list_jobs(conn)
if not jobs: st.info("Create a Job first."); st.stop()

job = st.selectbox("Select Job", jobs, format_func=lambda j: f"#{j['id']} {j['title']}")
apps = db.get_applications_for_job(conn, job["id"])
if not apps: st.info("No applications."); st.stop()

app_row = st.selectbox("Candidate", apps, format_func=lambda a: f"{a['candidate_name']} ({a['candidate_email']}) — Score {a['match_score']}%")
stage = st.selectbox("Interview Stage", ["AI-Screen","Tech-Round-1","Tech-Round-2"])

if "auto_questions" not in st.session_state: st.session_state["auto_questions"] = []
if "auto_answers" not in st.session_state: st.session_state["auto_answers"] = []
if "q_idx" not in st.session_state: st.session_state["q_idx"] = 0
if "auto_running" not in st.session_state: st.session_state["auto_running"] = False

with st.expander("Question Generator"):
    q_prompt = f"""You are an interviewer. Create 5 concise, role-relevant questions for this JD and candidate.
Return JSON list of strings. No preamble.

JD:
{job['jd_text']}

Candidate (LLM context):
{app_row['match_reason']}
"""
    if st.button("Generate / Refresh Questions"):
        try:
            qs_raw, usage_q = llm.chat_with_usage(q_prompt)
            if ct and usage_q: ct.add_chat_cost(usage_q.get("input_tokens",0), usage_q.get("output_tokens",0), feature="interview_qgen")
            questions = json.loads(qs_raw) if qs_raw.strip().startswith("[") else [q.strip("-• ") for q in qs_raw.splitlines() if q.strip()]
            st.session_state["auto_questions"] = questions[:5]
            st.session_state["auto_answers"] = [""]*len(st.session_state["auto_questions"])
            st.session_state["q_idx"] = 0
            st.success("Questions ready.")
        except Exception as e:
            st.error(f"Failed to parse: {e}")

questions = st.session_state["auto_questions"]
if not questions: st.warning("Generate questions to start."); st.stop()

colA,colB,colC = st.columns(3)
with colA:
    if st.button("▶️ Start / Resume"): st.session_state["auto_running"] = True
with colB:
    if st.button("⏸️ Pause"): st.session_state["auto_running"] = False
with colC:
    if st.button("🔁 Restart"):
        st.session_state["q_idx"]=0; st.session_state["auto_answers"]=[""]*len(questions); st.session_state["auto_running"]=False

q_idx = st.session_state["q_idx"]
st.progress(q_idx/len(questions))

def tts(text:str)->bytes:
    try:
audio = tts_bytes(q)
        if ct: ct.add_tts_cost(len(text), feature="interview_tts")
        return audio
    except Exception as e:
        st.error(f"TTS failed: {e}"); return b""

if st.session_state["auto_running"] and q_idx < len(questions):
    q = questions[q_idx]

if st.session_state.get("auto_running", False) and q_idx < len(questions):
    q = questions[q_idx]
    st.markdown(f"### Q{q_idx+1}: {q}")

    # Speak the question (SDK v1 only; v0 just shows text)
    audio = tts_bytes(q)
    if audio:
        st.audio(audio, format="audio/mp3")
    else:
        st.info("Text-to-speech unavailable in this SDK mode. Please read the question above.")

    st.info("Record the candidate's answer, then stop to auto-continue.")
    bytes_wav = audio_recorder(text="Record / Stop", sample_rate=41000, pause_threshold=1.0)

    if bytes_wav:
        import tempfile, os, wave, contextlib
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp:
            tmp.write(bytes_wav)
            tmp_path = tmp.name
        # Transcribe with Whisper
        with open(tmp_path, "rb") as f:
            try:
                transcript = whisper_transcribe(f)
                if ct:
                    with contextlib.closing(wave.open(tmp_path, "rb")) as w:
                        dur = w.getnframes() / float(w.getframerate() or 41000)
                    ct.add_whisper_cost_from_minutes(dur/60.0, feature="interview_stt")
                st.session_state["auto_answers"][q_idx] = transcript
                st.success(f"Transcribed: {transcript[:120]}{'...' if len(transcript)>120 else ''}")
                st.session_state["q_idx"] = q_idx + 1
                st.rerun()
            except Exception as e:
                st.error(f"Transcription failed: {e}")
        try:
            os.remove(tmp_path)
        except Exception:
            pass
            except Exception as e:
                st.error(f"Transcription failed: {e}")
        try: os.remove(tmp_path)
        except: pass

st.markdown("---"); st.subheader("Captured Answers")
for i,(q,a) in enumerate(zip(questions, st.session_state["auto_answers"]),1):
    st.write(f"**Q{i}. {q}**"); st.write(a if a else "_(pending)_")

if all(a for a in st.session_state['auto_answers']):
    st.success("All answers captured.")
    if st.button("🧠 Summarize, Score & Save (PDF)"):
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
{list(zip(questions, st.session_state['auto_answers']))}
"""
        notes, usage_s = llm.chat_with_usage(a_prompt)
        if ct and usage_s: ct.add_chat_cost(usage_s.get("input_tokens",0), usage_s.get("output_tokens",0), feature="interview_summary")
        m = re.search(r"Final Score:\s*([0-9]{1,3})%", notes); score = int(m.group(1)) if m else 0
        rubric = {"Clarity of Explanation":0,"Depth of Knowledge":0,"Relevance of Examples":0,"Problem Solving Approach":0,"Communication Skills":0}
        jm = re.search(r"<JSON>\s*(\{[\s\S]*?\})\s*</JSON>", notes)
        if jm:
            try:
                rub = json.loads(jm.group(1))
                for k in rubric.keys():
                    if k in rub: rubric[k] = float(rub[k])
            except Exception: pass
        overall_5 = sum(rubric.values())/5.0 if sum(rubric.values())>0 else (score/20.0)
        import tempfile
        tmp_pdf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf"); tmp_pdf.close()
        build_softskills_pdf(tmp_pdf.name, app_row['candidate_name'], job['title'], rubric, overall_5, notes.split("### Summary",1)[-1].strip(), logo_path="branding/logo.png")
        st.download_button("📥 Download Soft Skills PDF", data=open(tmp_pdf.name,"rb").read(), file_name=f"{app_row['candidate_name'].replace(' ','_')}_softskills.pdf", mime="application/pdf")
        st.markdown(notes, unsafe_allow_html=True)
