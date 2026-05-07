import streamlit as st
import time
import pandas as pd
from datetime import datetime

st.set_page_config(
    page_title="Loan Readiness Platform",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
    .block-container { padding-top: 1.5rem; }
    div[data-testid="stMetric"] { background:#f8fafc; border-radius:8px; padding:0.5rem 1rem; }
    div[data-testid="stDataFrame"] { border-radius:8px; overflow:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Session state defaults ────────────────────────────────────────────────────
for k, v in [
    ("step", 1),
    ("business_data", {}),
    ("financial_data", {}),
    ("generated_financials", {}),
    ("score_data", {}),
    ("processing_done", False),
    ("submitted", False),
]:
    if k not in st.session_state:
        st.session_state[k] = v


# ── Helper: scoring ───────────────────────────────────────────────────────────
def calculate_score(biz, fin):
    components = {}

    years = fin.get("years_operation", 0)
    components["Business Stability"] = (
        25 if years >= 5 else 20 if years >= 3 else 15 if years >= 2 else 10 if years >= 1 else 5
    )

    avg_sales = sum(fin["monthly_sales"]) / 3
    avg_exp = sum(fin["monthly_expenses"]) / 3
    margin = (avg_sales - avg_exp) / avg_sales if avg_sales else 0
    components["Revenue & Cash Flow"] = (
        25 if margin >= 0.30 else 20 if margin >= 0.20 else 15 if margin >= 0.10 else 10 if margin >= 0 else 5
    )

    s = fin["monthly_sales"]
    components["Revenue Trend"] = (
        20 if s[2] > s[1] > s[0]
        else 15 if s[2] >= s[0]
        else 10 if s[2] >= s[0] * 0.9
        else 5
    )

    ratio = fin.get("loan_amount", 0) / avg_sales if avg_sales else 999
    components["Loan Sizing"] = (
        15 if ratio <= 6 else 12 if ratio <= 12 else 8 if ratio <= 18 else 5 if ratio <= 24 else 2
    )

    profile = 5
    if fin.get("employees", 0) > 1:
        profile += 3
    if fin.get("has_assets"):
        profile += 4
    if not fin.get("has_existing_loans"):
        profile += 3
    components["Business Profile"] = profile

    return sum(components.values()), components


# ── Helper: financials ────────────────────────────────────────────────────────
def generate_financials(fin):
    sales = fin["monthly_sales"]
    expenses = fin["monthly_expenses"]
    avg_s = sum(sales) / 3
    avg_e = sum(expenses) / 3
    avg_p = avg_s - avg_e
    margin = (avg_p / avg_s * 100) if avg_s else 0

    # Annualised growth estimate
    raw_growth = ((sales[2] / sales[0]) ** 0.5 - 1) if sales[0] else 0
    growth = min(max(raw_growth, -0.05), 0.10)

    return dict(
        monthly_sales=sales,
        monthly_expenses=expenses,
        avg_sales=avg_s,
        avg_expenses=avg_e,
        avg_profit=avg_p,
        profit_margin=margin,
        growth_rate=growth * 100,
    )


# ── Page header ───────────────────────────────────────────────────────────────
st.markdown("""
<div style="background:linear-gradient(135deg,#1a3c5e 0%,#0d7b6e 100%);
            color:white;padding:1.4rem 2rem;border-radius:10px;margin-bottom:1rem;">
  <div style="display:flex;align-items:center;justify-content:space-between;flex-wrap:wrap;gap:0.5rem;">
    <div>
      <h2 style="margin:0;font-size:1.6rem;">🏦 Loan Readiness Platform</h2>
      <p style="margin:0;opacity:0.85;font-size:0.9rem;">AI-Enabled MSME Credit Readiness — Bangladesh</p>
    </div>
    <div style="text-align:right;">
      <p style="margin:0;font-style:italic;font-size:1rem;color:#7dd3c8;">"From Informal to Bankable"</p>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Step progress bar ─────────────────────────────────────────────────────────
STEP_LABELS = [
    ("📋", "Business\nProfile"),
    ("💰", "Financial\nData"),
    ("🤖", "AI\nAnalysis"),
    ("📊", "Loan\nScore"),
    ("📄", "Credit\nPack"),
]
cur = st.session_state.step
cols = st.columns(5)
for i, (col, (icon, label)) in enumerate(zip(cols, STEP_LABELS), 1):
    with col:
        if i < cur:
            bg, fg, txt = "#0d7b6e", "white", f"✓ {label.split(chr(10))[1]}"
        elif i == cur:
            bg, fg, txt = "#1a3c5e", "white", f"{icon} {label.split(chr(10))[1]}"
        else:
            bg, fg, txt = "#e8edf2", "#666", f"{icon} {label.split(chr(10))[1]}"
        st.markdown(
            f'<div style="background:{bg};color:{fg};padding:0.55rem;border-radius:8px;'
            f'text-align:center;font-size:0.75rem;font-weight:{"bold" if i==cur else "normal"};">'
            f'{txt}</div>',
            unsafe_allow_html=True,
        )

st.markdown("<br>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# STEP 1 — Business Profile
# ══════════════════════════════════════════════════════════════════════════════
if st.session_state.step == 1:
    st.subheader("Step 1: Tell us about your business")
    st.caption("All information is kept strictly confidential. Estimates are fine.")

    c1, c2 = st.columns(2)
    with c1:
        business_name = st.text_input("Business Name *", placeholder="e.g., Rahman General Store")
        owner_name    = st.text_input("Owner's Name *",   placeholder="e.g., Mohammad Rahman")
        phone         = st.text_input("Mobile Number *",  placeholder="e.g., 01712345678")
        district = st.selectbox("District *", [
            "— Select —", "Dhaka", "Chittagong", "Sylhet", "Rajshahi",
            "Khulna", "Barisal", "Mymensingh", "Rangpur", "Comilla", "Narayanganj", "Other"
        ])
    with c2:
        business_type = st.selectbox("Business Type *", [
            "— Select —", "Retail / Trading", "Food & Beverage", "Garments / Textile",
            "Agriculture / Farming", "Manufacturing", "Service Business",
            "Transport", "Healthcare", "Education", "Other"
        ])
        years = st.number_input("Years in Operation *", min_value=0.0, max_value=50.0,
                                value=2.0, step=0.5)
        employees     = st.number_input("Number of Employees (incl. yourself)", min_value=1, max_value=500, value=3)
        women_led     = st.checkbox("This is a women-led business")

    st.markdown("")
    if st.button("Next: Financial Data →", type="primary", use_container_width=True):
        if not all([business_name.strip(), owner_name.strip(), phone.strip(),
                    district != "— Select —", business_type != "— Select —"]):
            st.error("Please fill in all required fields marked with *")
        else:
            st.session_state.business_data = dict(
                business_name=business_name.strip(),
                owner_name=owner_name.strip(),
                phone=phone.strip(),
                district=district,
                business_type=business_type,
                years_operation=years,
                employees=employees,
                is_women_led=women_led,
                submission_date=datetime.now().strftime("%d %B %Y"),
            )
            st.session_state.step = 2
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 2 — Financial Data
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 2:
    biz = st.session_state.business_data
    st.subheader(f"Step 2: Financial Information — {biz['business_name']}")
    st.caption("Enter your best estimates. Our platform will help structure them properly.")

    st.markdown("#### Monthly Sales (Revenue in BDT)")
    c1, c2, c3 = st.columns(3)
    with c1: s1 = st.number_input("3 Months Ago", min_value=0, value=80_000, step=5_000, key="s1")
    with c2: s2 = st.number_input("2 Months Ago", min_value=0, value=85_000, step=5_000, key="s2")
    with c3: s3 = st.number_input("Last Month",   min_value=0, value=90_000, step=5_000, key="s3")

    st.markdown("#### Monthly Expenses (BDT) — rent, stock, staff, utilities, etc.")
    c1, c2, c3 = st.columns(3)
    with c1: e1 = st.number_input("3 Months Ago", min_value=0, value=60_000, step=5_000, key="e1")
    with c2: e2 = st.number_input("2 Months Ago", min_value=0, value=63_000, step=5_000, key="e2")
    with c3: e3 = st.number_input("Last Month",   min_value=0, value=65_000, step=5_000, key="e3")

    st.markdown("---")
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("#### Business Assets")
        has_assets = st.checkbox("I have business assets (equipment, inventory, property)")
        asset_desc = ""
        if has_assets:
            asset_desc = st.text_area("Describe your assets",
                                      placeholder="e.g., 2 sewing machines, shop stock worth 50,000 BDT")
    with c2:
        st.markdown("#### Existing Loans / MFI Payments")
        has_loans = st.checkbox("I currently have existing loans or MFI repayments")
        loan_repay = 0
        if has_loans:
            loan_repay = st.number_input("Monthly repayment amount (BDT)", min_value=0, value=5_000, step=500)

    st.markdown("---")
    st.markdown("#### Loan Request")
    c1, c2 = st.columns(2)
    with c1:
        loan_amount = st.number_input("How much do you need to borrow? (BDT) *",
                                      min_value=10_000, max_value=10_000_000, value=500_000, step=50_000)
    with c2:
        loan_purpose = st.selectbox("Purpose of Loan *", [
            "Working Capital / Stock Purchase", "Equipment / Machinery",
            "Business Expansion", "Seasonal Stock", "Renovation / Shop Improvement", "Other"
        ])

    cb, cn = st.columns([1, 3])
    with cb:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 1
            st.rerun()
    with cn:
        if st.button("Generate My Financial Report →", type="primary", use_container_width=True):
            st.session_state.financial_data = dict(
                monthly_sales=[s1, s2, s3],
                monthly_expenses=[e1, e2, e3],
                years_operation=biz["years_operation"],
                employees=biz["employees"],
                has_assets=has_assets,
                asset_description=asset_desc,
                has_existing_loans=has_loans,
                existing_loan_amount=loan_repay,
                loan_amount=loan_amount,
                loan_purpose=loan_purpose,
            )
            st.session_state.processing_done = False
            st.session_state.step = 3
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 3 — AI Analysis
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 3:
    biz = st.session_state.business_data
    fin = st.session_state.financial_data

    st.subheader("Step 3: AI Analysis")

    if not st.session_state.processing_done:
        st.markdown("**Our AI is analysing your business data. Please wait...**")
        bar = st.progress(0)
        msg = st.empty()
        for text, pct in [
            ("Scanning business profile…", 20),
            ("Analysing 3-month revenue data…", 40),
            ("Generating financial statements…", 60),
            ("Computing loan readiness score…", 80),
            ("Preparing your credit pack…", 100),
        ]:
            msg.info(f"🤖 {text}")
            bar.progress(pct)
            time.sleep(0.75)

        st.session_state.generated_financials = generate_financials(fin)
        total, components = calculate_score(biz, fin)
        st.session_state.score_data = dict(total=total, components=components)
        st.session_state.processing_done = True
        msg.success("✅ Analysis complete!")
        time.sleep(0.4)
        st.rerun()

    else:
        gf = st.session_state.generated_financials
        st.success("✅ AI Analysis complete! Here is your financial summary.")

        c1, c2, c3 = st.columns(3)
        c1.metric("Avg Monthly Revenue", f"BDT {gf['avg_sales']:,.0f}")
        c2.metric("Avg Monthly Profit",  f"BDT {gf['avg_profit']:,.0f}")
        c3.metric("Profit Margin",       f"{gf['profit_margin']:.1f}%")

        st.markdown("#### Revenue vs Expenses — Last 3 Months")
        chart_df = pd.DataFrame({
            "Revenue (BDT)":  gf["monthly_sales"],
            "Expenses (BDT)": gf["monthly_expenses"],
        }, index=["3 Months Ago", "2 Months Ago", "Last Month"])
        st.bar_chart(chart_df)

        st.markdown("#### AI-Generated Profit & Loss Statement")
        pl = pd.DataFrame({
            "Period":          ["3 Months Ago", "2 Months Ago", "Last Month"],
            "Revenue (BDT)":   [f"{v:,.0f}" for v in gf["monthly_sales"]],
            "Expenses (BDT)":  [f"{v:,.0f}" for v in gf["monthly_expenses"]],
            "Net Profit (BDT)":[f"{s-e:,.0f}" for s, e in zip(gf["monthly_sales"], gf["monthly_expenses"])],
        })
        st.dataframe(pl, use_container_width=True, hide_index=True)

        trend = "📈 growing" if gf["growth_rate"] > 1 else ("📉 declining" if gf["growth_rate"] < -1 else "➡️ stable")
        st.info(f"Revenue trend: {trend} ({gf['growth_rate']:+.1f}% per month)")

        cb, cn = st.columns([1, 3])
        with cb:
            if st.button("← Back", use_container_width=True):
                st.session_state.step = 2
                st.session_state.processing_done = False
                st.rerun()
        with cn:
            if st.button("View My Loan Readiness Score →", type="primary", use_container_width=True):
                st.session_state.step = 4
                st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 4 — Loan Readiness Score
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 4:
    biz        = st.session_state.business_data
    score_data = st.session_state.score_data
    total      = score_data["total"]
    components = score_data["components"]

    MAX_SCORES = {
        "Business Stability":  25,
        "Revenue & Cash Flow": 25,
        "Revenue Trend":       20,
        "Loan Sizing":         15,
        "Business Profile":    15,
    }

    if total >= 80:
        rating, color = "Excellent", "#0d7b6e"
        headline = "Your business is highly bank-ready. You are likely to qualify for most MSME loans."
        advice   = "Proceed to generate your credit pack and submit to partner banks."
    elif total >= 65:
        rating, color = "Good", "#2563eb"
        headline = "Your business shows strong potential. Minor improvements could raise your approval chances."
        advice   = "Review the recommendations below before submitting."
    elif total >= 50:
        rating, color = "Fair", "#d97706"
        headline = "Your business has a foundation but needs some strengthening before applying."
        advice   = "Work on the improvement areas and re-score in 30 days."
    else:
        rating, color = "Needs Work", "#dc2626"
        headline = "Your business needs more preparation before applying for a formal bank loan."
        advice   = "Our advisors will help you build a stronger profile over 60–90 days."

    st.subheader("Step 4: Your Loan Readiness Score")

    # Big score display
    st.markdown(f"""
    <div style="text-align:center;padding:2rem;background:white;border-radius:12px;
                border:3px solid {color};margin-bottom:1.5rem;box-shadow:0 2px 10px rgba(0,0,0,0.08);">
        <div style="font-size:5rem;font-weight:900;color:{color};line-height:1;">{total}</div>
        <div style="font-size:1.6rem;font-weight:bold;color:{color};">out of 100 — {rating}</div>
        <p style="margin-top:1rem;color:#444;max-width:500px;margin-left:auto;margin-right:auto;">{headline}</p>
        <p style="color:{color};font-weight:600;">{advice}</p>
    </div>
    """, unsafe_allow_html=True)

    # Score breakdown
    st.markdown("#### Score Breakdown")
    for cat, score in components.items():
        mx  = MAX_SCORES[cat]
        pct = score / mx
        icon = "✅" if pct >= 0.70 else ("⚠️" if pct >= 0.50 else "❌")
        ca, cb_col, cc = st.columns([4, 1, 1])
        with ca:
            st.write(f"**{cat}**")
            st.progress(pct)
        with cb_col:
            st.metric("", f"{score}/{mx}")
        with cc:
            st.markdown(f"<div style='font-size:1.5rem;padding-top:1.2rem;'>{icon}</div>",
                        unsafe_allow_html=True)

    # Recommendations
    recs = []
    if components.get("Business Stability", 0) < 15:
        recs.append("📅 Continue operating and reapply in 6–12 months as your business matures.")
    if components.get("Revenue & Cash Flow", 0) < 15:
        recs.append("💰 Work on reducing expenses or increasing sales to improve profit margins.")
    if components.get("Revenue Trend", 0) < 12:
        recs.append("📈 Focus on growing monthly revenue consistently before applying.")
    if components.get("Loan Sizing", 0) < 10:
        recs.append("📉 Consider requesting a smaller loan amount relative to your monthly revenue.")
    if components.get("Business Profile", 0) < 10:
        recs.append("📋 Document your business assets and ensure your registration is current.")
    if not recs:
        recs.append("🌟 Your business profile is strong. Keep maintaining accurate financial records.")

    st.markdown("#### Recommendations")
    for r in recs:
        st.info(r)

    cb, cn = st.columns([1, 3])
    with cb:
        if st.button("← Back", use_container_width=True):
            st.session_state.step = 3
            st.rerun()
    with cn:
        if st.button("Generate My Credit Pack →", type="primary", use_container_width=True):
            st.session_state.step = 5
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
# STEP 5 — Credit Pack
# ══════════════════════════════════════════════════════════════════════════════
elif st.session_state.step == 5:
    biz        = st.session_state.business_data
    fin        = st.session_state.financial_data
    gf         = st.session_state.generated_financials
    score_data = st.session_state.score_data
    total      = score_data["total"]

    if total >= 80:
        status_color, status_label = "#0d7b6e", "APPROVED FOR SUBMISSION"
    elif total >= 65:
        status_color, status_label = "#2563eb", "RECOMMENDED FOR SUBMISSION"
    elif total >= 50:
        status_color, status_label = "#d97706", "CONDITIONAL — REVIEW REQUIRED"
    else:
        status_color, status_label = "#dc2626", "PENDING IMPROVEMENT PLAN"

    app_id = f"LRP-{abs(hash(biz['business_name'])) % 100_000:05d}"
    women_row = (
        '<tr><td style="padding:0.45rem;color:#0d7b6e;">Women-Led Business</td>'
        '<td style="padding:0.45rem;color:#0d7b6e;font-weight:bold;">✓ Yes</td></tr>'
        if biz.get("is_women_led") else ""
    )

    month_rows = "".join(
        f'<tr style="background:{("#f9f9f9" if i % 2 == 0 else "white")}">'
        f'<td style="padding:0.45rem;text-align:center;">{m}</td>'
        f'<td style="padding:0.45rem;text-align:right;">{s:,.0f}</td>'
        f'<td style="padding:0.45rem;text-align:right;">{e:,.0f}</td>'
        f'<td style="padding:0.45rem;text-align:right;color:{"#0d7b6e" if s > e else "#dc2626"};">{s - e:,.0f}</td>'
        f'</tr>'
        for i, (m, s, e) in enumerate(
            zip(["3 Months Ago", "2 Months Ago", "Last Month"],
                gf["monthly_sales"], gf["monthly_expenses"])
        )
    )

    trend_desc = "consistent growth" if gf["growth_rate"] > 2 else "stability"
    proportion_desc = "well-proportioned" if fin["loan_amount"] <= gf["avg_sales"] * 8 else "ambitious"

    st.subheader("Step 5: Your Credit Pack")
    st.caption("This standardised document will be reviewed by a credit officer and sent to partner banks.")

    if not st.session_state.submitted:
        st.markdown(f"""
        <div style="border:2px solid #1a3c5e;border-radius:12px;padding:2rem;background:white;
                    box-shadow:0 2px 12px rgba(0,0,0,0.1);">

          <!-- Header -->
          <div style="background:linear-gradient(135deg,#1a3c5e,#0d7b6e);color:white;
                      padding:1.5rem 2rem;margin:-2rem -2rem 1.5rem;border-radius:10px 10px 0 0;text-align:center;">
            <h2 style="margin:0;font-size:1.4rem;">LOAN READINESS PLATFORM</h2>
            <p style="margin:0.3rem 0 0;opacity:0.9;font-size:0.9rem;">MSME Credit Application Pack — Bangladesh</p>
            <div style="background:{status_color};display:inline-block;padding:0.3rem 1.5rem;
                        border-radius:20px;margin-top:0.8rem;font-weight:bold;font-size:0.8rem;">
              {status_label}
            </div>
          </div>

          <!-- Meta row -->
          <div style="display:flex;justify-content:space-between;color:#666;font-size:0.82rem;margin-bottom:1.5rem;flex-wrap:wrap;gap:0.5rem;">
            <span>Application ID: <strong>{app_id}</strong></span>
            <span>Date: {biz["submission_date"]}</span>
            <span>Loan Readiness Score: <strong style="color:#1a3c5e;">{total}/100</strong></span>
          </div>

          <!-- Business Info -->
          <h3 style="color:#1a3c5e;border-bottom:2px solid #0d7b6e;padding-bottom:0.3rem;margin-top:0;">Business Information</h3>
          <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem;">
            <tr><td style="padding:0.45rem;color:#666;width:42%;">Business Name</td>
                <td style="padding:0.45rem;font-weight:bold;">{biz["business_name"]}</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:0.45rem;color:#666;">Owner Name</td>
                <td style="padding:0.45rem;">{biz["owner_name"]}</td></tr>
            <tr><td style="padding:0.45rem;color:#666;">Business Type</td>
                <td style="padding:0.45rem;">{biz["business_type"]}</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:0.45rem;color:#666;">Location</td>
                <td style="padding:0.45rem;">{biz["district"]}, Bangladesh</td></tr>
            <tr><td style="padding:0.45rem;color:#666;">Years in Operation</td>
                <td style="padding:0.45rem;">{biz["years_operation"]} years</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:0.45rem;color:#666;">Employees</td>
                <td style="padding:0.45rem;">{biz["employees"]}</td></tr>
            {women_row}
          </table>

          <!-- Financial Summary -->
          <h3 style="color:#1a3c5e;border-bottom:2px solid #0d7b6e;padding-bottom:0.3rem;">Financial Summary</h3>
          <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem;">
            <tr style="background:#1a3c5e;color:white;">
              <th style="padding:0.5rem;">Period</th>
              <th style="padding:0.5rem;text-align:right;">Revenue (BDT)</th>
              <th style="padding:0.5rem;text-align:right;">Expenses (BDT)</th>
              <th style="padding:0.5rem;text-align:right;">Net Profit (BDT)</th>
            </tr>
            {month_rows}
            <tr style="background:#e8f4f2;font-weight:bold;">
              <td style="padding:0.5rem;">Monthly Average</td>
              <td style="padding:0.5rem;text-align:right;">{gf["avg_sales"]:,.0f}</td>
              <td style="padding:0.5rem;text-align:right;">{gf["avg_expenses"]:,.0f}</td>
              <td style="padding:0.5rem;text-align:right;color:#0d7b6e;">{gf["avg_profit"]:,.0f}</td>
            </tr>
          </table>

          <!-- Loan Request -->
          <h3 style="color:#1a3c5e;border-bottom:2px solid #0d7b6e;padding-bottom:0.3rem;">Loan Request</h3>
          <table style="width:100%;border-collapse:collapse;margin-bottom:1.5rem;">
            <tr><td style="padding:0.45rem;color:#666;width:42%;">Amount Requested</td>
                <td style="padding:0.45rem;font-weight:bold;font-size:1.05rem;color:#1a3c5e;">BDT {fin["loan_amount"]:,.0f}</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:0.45rem;color:#666;">Purpose</td>
                <td style="padding:0.45rem;">{fin["loan_purpose"]}</td></tr>
            <tr><td style="padding:0.45rem;color:#666;">Est. Monthly Repayment Capacity</td>
                <td style="padding:0.45rem;">BDT {gf["avg_profit"] * 0.6:,.0f}</td></tr>
            <tr style="background:#f9f9f9;"><td style="padding:0.45rem;color:#666;">Loan-to-Annual-Revenue Ratio</td>
                <td style="padding:0.45rem;">{fin["loan_amount"] / (gf["avg_sales"] * 12):.2f}x</td></tr>
          </table>

          <!-- AI Assessment -->
          <h3 style="color:#1a3c5e;border-bottom:2px solid #0d7b6e;padding-bottom:0.3rem;">AI-Generated Business Assessment</h3>
          <p style="color:#444;line-height:1.7;margin-bottom:1.5rem;">
            {biz["business_name"]} is a {biz["business_type"].lower()} business based in {biz["district"]}
            that has been operating for {biz["years_operation"]} years, employing {biz["employees"]} staff.
            The business demonstrates {"positive" if gf["avg_profit"] > 0 else "challenging"} cash flow with an
            average monthly profit of BDT {gf["avg_profit"]:,.0f} ({gf["profit_margin"]:.1f}% margin).
            Revenue shows {trend_desc} with a {abs(gf["growth_rate"]):.1f}%
            {"upward" if gf["growth_rate"] >= 0 else "downward"} monthly trend.
            The requested loan of BDT {fin["loan_amount"]:,.0f} for {fin["loan_purpose"].lower()} is
            {proportion_desc} relative to the business's revenue base.
          </p>

          <!-- Footer -->
          <div style="padding-top:1rem;border-top:1px solid #ddd;text-align:center;color:#999;font-size:0.75rem;">
            Generated by Loan Readiness Platform · AI-Enabled MSME Credit Readiness · Bangladesh<br>
            This pack is AI-generated and pending human validation by a certified credit officer.
          </div>

        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        cb, cs, cr = st.columns([1, 2, 1])
        with cb:
            if st.button("← Back to Score", use_container_width=True):
                st.session_state.step = 4
                st.rerun()
        with cs:
            if st.button("✅ Submit to Credit Officer for Review", type="primary", use_container_width=True):
                st.session_state.submitted = True
                st.rerun()
        with cr:
            if st.button("🔄 New Application", use_container_width=True):
                for k in ["step","business_data","financial_data","generated_financials",
                          "score_data","processing_done","submitted"]:
                    st.session_state.pop(k, None)
                st.rerun()

    else:
        st.balloons()
        st.success(f"""
### 🎉 Application Submitted Successfully!

**Application ID:** {app_id}

**What happens next:**
1. A credit officer will review your pack within **2–3 business days**
2. They may contact you at **{biz["phone"]}** for any clarifications
3. Your pack will be forwarded to partner banks (BRAC Bank & others)
4. You will receive an update on your application status via SMS

---
Thank you, **{biz["owner_name"]}**. We are committed to helping your business access the finance it deserves. 🌱
        """)

        if st.button("🔄 Start a New Application", type="primary"):
            for k in ["step","business_data","financial_data","generated_financials",
                      "score_data","processing_done","submitted"]:
                st.session_state.pop(k, None)
            st.rerun()
