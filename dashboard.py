from dotenv import load_dotenv
load_dotenv()  # reads .env file when running locally

import streamlit as st
import pandas as pd
from db import init_db, get_all_feedback, get_step_stats

st.set_page_config(page_title="Feedback Dashboard — LRP", page_icon="📊", layout="wide")

st.markdown("""
<div style="background:linear-gradient(135deg,#1a3c5e 0%,#0d7b6e 100%);
            color:white;padding:1.2rem 2rem;border-radius:10px;margin-bottom:1.5rem;">
  <h2 style="margin:0;">📊 Feedback Dashboard</h2>
  <p style="margin:0;opacity:0.85;font-size:0.9rem;">Loan Readiness Platform — Local Analytics</p>
</div>
""", unsafe_allow_html=True)

init_db()
df    = get_all_feedback()
stats = get_step_stats()

if df.empty:
    st.info("No feedback in the local database yet. Run the main app locally and submit some feedback to see it here.")
    st.stop()

# ── Top-line metrics ──────────────────────────────────────────────────────────
st.markdown("### Overview")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Total Responses",    len(df))
c2.metric("Avg Overall Rating", f"{df['overall_rating'].mean():.2f} / 5")
c3.metric("Avg Ease of Use",    f"{df['ease_rating'].mean():.2f} / 5")
c4.metric("Avg Usefulness",     f"{df['usefulness_rating'].mean():.2f} / 5")

st.divider()

# ── Ratings by step ───────────────────────────────────────────────────────────
if not stats.empty:
    st.markdown("### Ratings by Step")
    chart_df = stats.set_index("step_name")[
        ["avg_overall", "avg_ease", "avg_usefulness"]
    ].rename(columns={
        "avg_overall":    "Overall",
        "avg_ease":       "Ease of Use",
        "avg_usefulness": "Usefulness",
    })
    st.bar_chart(chart_df, height=320)

    display_stats = stats[
        ["step_name", "responses", "avg_overall", "avg_ease", "avg_usefulness"]
    ].rename(columns={
        "step_name":      "Step",
        "responses":      "Responses",
        "avg_overall":    "Avg Overall",
        "avg_ease":       "Avg Ease",
        "avg_usefulness": "Avg Usefulness",
    })
    st.dataframe(display_stats, use_container_width=True, hide_index=True)

st.divider()

# ── Loan readiness awareness ──────────────────────────────────────────────────
st.markdown("### Loan Readiness Awareness")
awareness = df["loan_awareness"].value_counts().reset_index()
awareness.columns = ["Answer", "Count"]
c1, c2 = st.columns([1, 2])
with c1:
    st.dataframe(awareness, use_container_width=True, hide_index=True)
with c2:
    st.bar_chart(awareness.set_index("Answer"), height=220)

st.divider()

# ── Overall rating distribution ───────────────────────────────────────────────
st.markdown("### Overall Rating Distribution")
dist = df["overall_rating"].value_counts().sort_index().reset_index()
dist.columns = ["Stars", "Count"]
dist["Stars"] = dist["Stars"].apply(lambda x: f"{'★'*x}{'☆'*(5-x)} ({x})")
st.bar_chart(dist.set_index("Stars"), height=250)

st.divider()

# ── Recent comments ───────────────────────────────────────────────────────────
st.markdown("### Written Comments")
comments_df = df[df["comments"].str.strip() != ""][
    ["created_at", "step_name", "overall_rating", "business_name", "district", "comments"]
].head(50).rename(columns={
    "created_at":     "Date",
    "step_name":      "Step",
    "overall_rating": "Rating",
    "business_name":  "Business",
    "district":       "District",
    "comments":       "Comment",
})
if comments_df.empty:
    st.info("No written comments yet.")
else:
    st.dataframe(comments_df, use_container_width=True, hide_index=True)

st.divider()

# ── Export ────────────────────────────────────────────────────────────────────
st.markdown("### Export")
csv = df.to_csv(index=False).encode("utf-8")
st.download_button(
    label="⬇️ Download all feedback as CSV",
    data=csv,
    file_name="lrp_feedback.csv",
    mime="text/csv",
)
