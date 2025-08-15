import streamlit as st, pandas as pd
from lib import db
st.title("📈 Reports")
conn = st.session_state["db_conn"]
jobs = db.list_jobs(conn)
if not jobs: st.info("Create a Job first."); st.stop()
job = st.selectbox("Job", jobs, format_func=lambda j: f"#{j['id']} {j['title']}")
apps = db.get_applications_for_job(conn, job["id"])
if not apps: st.info("No data."); st.stop()
df = pd.DataFrame([{"ApplicationID":a["id"],"Candidate":a["candidate_name"],"Email":a["candidate_email"],"Score":a["match_score"],"Status":a["status"],"Created":a["created_at"]} for a in apps])
c1,c2,c3 = st.columns(3)
with c1: st.metric("Total Candidates", len(df))
with c2: st.metric("Avg Score", round(df["Score"].mean(),1))
with c3: st.metric("Strong Matches (≥70%)", int((df["Score"]>=70).sum()))
st.dataframe(df, use_container_width=True)
st.download_button("📥 Export CSV", data=df.to_csv(index=False), file_name="report.csv", mime="text/csv")
