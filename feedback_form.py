import os
import resend
import streamlit as st

STEP_NAMES = {
    1: "Business Profile",
    2: "Financial Data",
    3: "AI Analysis",
    4: "Loan Score",
    5: "Credit Pack",
}

STAR_MAP = {1: "★☆☆☆☆", 2: "★★☆☆☆", 3: "★★★☆☆", 4: "★★★★☆", 5: "★★★★★"}


def _send_email(step_name, overall, ease, usefulness, awareness, comments, business_name):
    api_key  = os.environ.get("RESEND_API_KEY", "").strip()
    to_email = os.environ.get("FEEDBACK_EMAIL", "").strip()

    if not api_key:
        return False, "RESEND_API_KEY is not set in environment variables."
    if not to_email:
        return False, "FEEDBACK_EMAIL is not set in environment variables."

    resend.api_key = api_key

    html = f"""
    <html><body style="font-family:Arial,sans-serif;color:#333;">
    <div style="max-width:520px;margin:auto;border:1px solid #ddd;border-radius:8px;overflow:hidden;">
      <div style="background:linear-gradient(135deg,#1a3c5e,#0d7b6e);color:white;padding:1rem 1.5rem;">
        <h2 style="margin:0;">New Feedback — {step_name}</h2>
        <p style="margin:0;opacity:0.85;font-size:0.9rem;">Loan Readiness Platform</p>
      </div>
      <div style="padding:1.5rem;">
        <table style="width:100%;border-collapse:collapse;">
          <tr><td style="padding:0.4rem;color:#666;width:45%;">Business</td>
              <td style="padding:0.4rem;"><b>{business_name or "Not provided"}</b></td></tr>
          <tr style="background:#f9f9f9;">
              <td style="padding:0.4rem;color:#666;">Overall Experience</td>
              <td style="padding:0.4rem;color:#f59e0b;">{STAR_MAP[overall]} ({overall}/5)</td></tr>
          <tr><td style="padding:0.4rem;color:#666;">Ease of Use</td>
              <td style="padding:0.4rem;color:#f59e0b;">{STAR_MAP[ease]} ({ease}/5)</td></tr>
          <tr style="background:#f9f9f9;">
              <td style="padding:0.4rem;color:#666;">Usefulness</td>
              <td style="padding:0.4rem;color:#f59e0b;">{STAR_MAP[usefulness]} ({usefulness}/5)</td></tr>
          <tr><td style="padding:0.4rem;color:#666;">Loan Readiness Awareness</td>
              <td style="padding:0.4rem;">{awareness}</td></tr>
        </table>
        <div style="margin-top:1rem;padding:0.8rem;background:#f0f4f8;border-radius:6px;">
          <p style="margin:0;color:#666;font-size:0.85rem;">Comments</p>
          <p style="margin:0.3rem 0 0;">{comments or "<em>None provided</em>"}</p>
        </div>
      </div>
    </div>
    </body></html>
    """

    try:
        resend.Emails.send({
            "from":    "LRP Feedback <onboarding@resend.dev>",
            "to":      [to_email],
            "subject": f"[LRP Feedback] {step_name} — {business_name or 'Anonymous'}",
            "html":    html,
        })
        return True, None
    except Exception as e:
        return False, str(e)


def render_feedback_button(step_number: int):
    submitted_key = f"fb_submitted_{step_number}"
    error_key     = f"fb_error_{step_number}"

    if st.session_state.get(submitted_key):
        st.success("✅ Thank you for your feedback!")
        return

    # Show error outside the expander so it stays visible after rerun
    if st.session_state.get(error_key):
        st.error(st.session_state[error_key])

    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("💬 Share feedback on this step"):
        st.caption("Takes 30 seconds — helps us improve the platform.")

        c1, c2, c3 = st.columns(3)
        with c1:
            overall = st.select_slider(
                "Overall experience", options=[1, 2, 3, 4, 5], value=4,
                format_func=lambda x: STAR_MAP[x], key=f"fb_overall_{step_number}")
        with c2:
            ease = st.select_slider(
                "Ease of use", options=[1, 2, 3, 4, 5], value=4,
                format_func=lambda x: STAR_MAP[x], key=f"fb_ease_{step_number}")
        with c3:
            usefulness = st.select_slider(
                "Usefulness", options=[1, 2, 3, 4, 5], value=4,
                format_func=lambda x: STAR_MAP[x], key=f"fb_useful_{step_number}")

        awareness = st.radio(
            "Before using this platform, did you know what 'loan readiness' meant?",
            ["Yes", "Somewhat", "No"],
            horizontal=True,
            key=f"fb_aware_{step_number}",
        )

        comments = st.text_area(
            "Any suggestions or comments? (optional)",
            placeholder="Tell us what worked well or what could be better…",
            key=f"fb_comments_{step_number}",
        )

        if st.button("Submit Feedback", key=f"fb_submit_{step_number}", type="primary"):
            biz       = st.session_state.get("business_data", {})
            step_name = STEP_NAMES.get(step_number, f"Step {step_number}")
            ok, err   = _send_email(step_name, overall, ease, usefulness,
                                    awareness, comments, biz.get("business_name"))
            if ok:
                st.session_state.pop(error_key, None)
                st.session_state[submitted_key] = True
            else:
                st.session_state[error_key] = f"Email failed: {err}"
            st.rerun()
