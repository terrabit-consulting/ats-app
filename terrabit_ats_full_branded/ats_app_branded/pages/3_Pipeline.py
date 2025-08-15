import streamlit as st
from lib import db
st.title("📦 Pipeline")
conn = st.session_state["db_conn"]
jobs = db.list_jobs(conn)
if not jobs: st.info("Create a Job first."); st.stop()
job = st.selectbox("Select Job", jobs, format_func=lambda j: f"#{j['id']} {j['title']}")
apps = db.get_applications_for_job(conn, job["id"])
if not apps: st.info("No applications."); st.stop()
cols = st.columns(5); buckets = ["New","Screened","Interviewing","Offer","Rejected"]
data={b:[] for b in buckets}
for a in apps: data[a["status"] if a["status"] in buckets else "New"].append(a)
for col, b in zip(cols, buckets):
    with col:
        st.subheader(b)
        for a in data[b]:
            st.write(f"**{a['candidate_name']}** ({a['candidate_email']})")
            st.caption(f"Score: {a['match_score']}%  • AppID: {a['id']}")
            new_status = st.selectbox("Move to", buckets, index=buckets.index(b), key=f"mv_{a['id']}")
            if st.button("Update", key=f"upd_{a['id']}"):
                db.update_application_status(conn, a["id"], new_status); st.success("Updated"); st.rerun()
