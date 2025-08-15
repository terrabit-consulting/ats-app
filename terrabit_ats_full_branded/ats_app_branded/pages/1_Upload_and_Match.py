import streamlit as st, io, pandas as pd
from lib.parsers import read_any
from lib.extractors import extract_email, extract_name_smart
from lib.llm import LLMClient
from lib.scorer import build_match_prompt, parse_score
from lib import db

st.title("📌 Upload & Match")
conn = st.session_state["db_conn"]
api_key = st.secrets["OPENAI_API_KEY"]
llm = LLMClient(api_key=api_key, model="gpt-4o", temperature=0)
ct = st.session_state.get("cost_tracker")

with st.expander("Create / Select Job"):
    jobs = db.list_jobs(conn)
    options = ["➕ Create new job"] + [f"#{j['id']} {j['title']}" for j in jobs]
    sel = st.selectbox("Job", options)
    if sel.startswith("➕"):
        c1,c2,c3 = st.columns(3)
        with c1: title = st.text_input("Job Title")
        with c2: dept  = st.text_input("Department")
        with c3: loc   = st.text_input("Location")
        jd_file = st.file_uploader("Upload JD (.txt/.pdf/.docx)", type=["txt","pdf","docx"])
        if st.button("Create Job") and title and jd_file:
            jd_text = read_any(jd_file)
            jid = db.add_job(conn, title, dept, loc, jd_text)
            st.success(f"Job #{jid} created."); st.rerun()
    else:
        job_id = int(sel.split()[0][1:])
        job = [j for j in jobs if j["id"]==job_id][0]
        st.caption(f"Selected JD: {job['title']} — {job['location']}")

st.markdown("---")
resumes = st.file_uploader("📑 Upload Resumes", type=["txt","pdf","docx"], accept_multiple_files=True)

if st.button("🚀 Run Matching") and resumes and not sel.startswith("➕"):
    for f in resumes:
        resume_text = read_any(f)
        name = extract_name_smart(resume_text, llm=llm)
        email = extract_email(resume_text)
        prompt = build_match_prompt(job["jd_text"], resume_text, name)
        md, usage = llm.chat_with_usage(prompt)
        if ct and usage: ct.add_chat_cost(usage.get("input_tokens",0), usage.get("output_tokens",0), model="gpt-4o", feature="resume_match")
        score = parse_score(md)
        cand_id = db.add_candidate(conn, name, email, None, None, resume_text, f.name)
        db.add_application(conn, job["id"], cand_id, score, md, status="Screened" if score>=50 else "New")
        st.markdown("----")
        st.subheader(f"📌 {name}  |  {email}  |  Score: **{score}%**")
        st.markdown(md, unsafe_allow_html=True)
        if score < 50: st.error("❌ Not suitable – Major mismatch")
        elif score < 70: st.warning("⚠️ Consider with caution – Missing core skills")
        else: st.success("✅ Strong match")

    apps = db.get_applications_for_job(conn, job["id"])
    df = pd.DataFrame([{"Candidate":a["candidate_name"],"Email":a["candidate_email"],"Score":a["match_score"],"Status":a["status"]} for a in apps])
    st.markdown("### 📊 Summary")
    st.dataframe(df, use_container_width=True)
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w: df.to_excel(w, index=False)
    st.download_button("📥 Download Summary (Excel)", data=buf.getvalue(), file_name="summary.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
