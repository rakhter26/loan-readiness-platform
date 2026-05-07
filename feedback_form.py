import os
import smtplib
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

STEP_NAMES = {
    1: "Business Profile",
    2: "Financial Data",
    3: "AI Analysis",
    4: "Loan Score",
    5: "Credit Pack",
}

STAR_MAP = {1: "★☆☆☆☆", 2: "★★☆☆☆", 3: "★★★☆☆", 4: "★★★★☆", 5: "★★★★★"}


def _send_email(step_name, overall, ease, usefulness, awareness, comments, business_name):
    gmail_user = os.environ.get("GMAIL_USER", "").strip()
    gmail_pass = os.environ.get("GMAIL_APP_PASSWORD", "").replace(" ", "")
    to_email   = os.environ.get("FEEDBACK_EMAIL", gmail_user).strip()

    if not gmail_user:
        return False, "GMAIL_USER is not set in environment variables."
    if not gmail_pass:
        return False, "GMAIL_APP_PASSWORD is not set in environment variables."

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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"[LRP Feedback] {step_name} — {business_name or 'Anonymous'}"
    msg["From"]    = gmail_user
    msg["To"]      = to_email
    msg.attach(MIMEText(html, "html"))

    # Try port 465 (SSL) first, fall back to 587 (STARTTLS)
    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(gmail_user, gmail_pass)
            smtp.sendmail(gmail_user, to_email, msg.as_string())
        return True, None
    except Exception as e1:
        try:
            with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                smtp.ehlo()
                smtp.starttls()
                smtp.login(gmail_user, gmail_pass)
                smtp.sendmail(gmail_user, to_email, msg.as_string())
            return True, None
        except Exception as e2:
            return False, f"465: {e1} | 587: {e2}"


def render_feedback_button(step_number: int):
    submitted_key = f"fb_submitted_{step_number}"
    error_key     = f"fb_error_{step_number}"

    if st.session_state.get(submitted_key):
        st.success("✅ Thank you for your feedback!")
        return

    # Show error OUTSIDE the expander so it stays visible after rerun
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
