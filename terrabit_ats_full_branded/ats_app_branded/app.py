import streamlit as st
from lib import db
from lib.cost_tracker import CostTracker

st.set_page_config(page_title="Terrabit ATS", layout="wide")
st.title("🧭 Terrabit ATS (Branded)")

if "db_conn" not in st.session_state:
    st.session_state["db_conn"] = db.connect("ats.db")
    try: db.init(st.session_state["db_conn"])
    except: pass

if "cost_tracker" not in st.session_state:
    st.session_state["cost_tracker"] = CostTracker(store_path="cost_log.json")

totals = st.session_state["cost_tracker"].get_monthly_totals()
with st.sidebar:
    st.markdown("### 💸 Monthly API Spend")
    st.metric("Total (MYR)", f"{totals['myr']:.2f}")
    for feat, v in totals["by_feature"].items():
        st.caption(f"{feat}: RM {v['myr']:.2f}")
    if st.button("Reset This Month's Spend"):
        st.session_state["cost_tracker"].reset_current_month(); st.rerun()

st.sidebar.info("Use the pages on the left to navigate.")
st.write("Upload & Match resumes, run AI interviews (voice-led available), manage pipeline, and export reports. PDFs use your brand styling.")
