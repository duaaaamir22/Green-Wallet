# ─────────────────────────────────────────────────────────
# helpers.py
# Contributor : Ariba Khan
# Role        : Portfolio utilities — live price fetching,
#               ESG tier logic, bar chart renderer,
#               Gemini AI advisor, and demo portfolio data
# Last commit : "feat: add advisor prompt + demo portfolio seeding"
# ─────────────────────────────────────────────────────────

import streamlit as st
import yfinance as yf

from config import gemini, G, M, D, MUTED, TEXT

# ── LIVE PRICE ────────────────────────────────────────
def get_price(t):
    try:
        # yf.Ticker(t) looks up the stock symbol (e.g., "TSLA")
        # .fast_info.last_price grabs the most recent trade price
        # round(..., 2) makes sure we only see two decimal places (like $150.25)
        return round(yf.Ticker(t).fast_info.last_price, 2)
    except:
        # If the ticker is wrong or the internet is down, return 0.0 to avoid an error message
        return 0.0

# ── ESG TIER CLASSIFIER ───────────────────────────────
def tier(s):
    # If the score is 70 or higher, it's a top-tier "Sustainable" company (Green)
    if s >= 70: return "Sustainable", "pg", G
    # If it's between 40 and 69, it's "Moderate" (Yellow)
    if s >= 40: return "Moderate",    "py", M
    # Anything below 40 is flagged as "High Risk" (Red)
    return "High Risk", "pr", D

# ── PROGRESS BAR RENDERER ────────────────────────────
def bar(label, val, color):
    st.markdown(
        f"<div style='display:flex;justify-content:space-between;font-size:13px;color:{MUTED}'>"
        f"<span>{label}</span><span style='font-weight:700;color:{color}'>{int(val)}/100</span></div>"
        f"<div class='pb'><div class='pf' style='width:{val}%;background:{color}'></div></div>",
        unsafe_allow_html=True
    )

# ── AI ADVISOR (powered by Gemini) ───────────────────
def ask_advisor(question, pdata, sc):
    """Real AI advisor using Gemini — not if/else."""
    holdings_str = "\n".join([
        f"- {s['ticker']}: ESG {s['esg']}/100 (E:{s['env']}, S:{s['soc']}, G:{s['gov']}), {s['sector']}, ${s['value']:,.0f}"
        for s in pdata
    ])
    prompt = f"""You are an ESG portfolio advisor inside GreenWallet app. The user's portfolio Green Score is {sc}/100.

Their holdings:
{holdings_str}

Total portfolio value: ${sum(s['value'] for s in pdata):,.0f}

User asks: "{question}"

Give a clear, helpful, specific answer in 2-3 sentences. Reference their actual stocks and scores. No generic advice."""
    try:
        resp = gemini.generate_content(prompt)
        return resp.text.strip()
    except:
        return f"Portfolio score is {int(sc)}/100. Try asking about specific stocks or how to improve."

# ── DEMO PORTFOLIOS ───────────────────────────────────
DEMOS = {
    "Jugal Bhagat - Tech Growth Portfolio": (
        "Jugal Bhagat", "PF-1001",
        [("AAPL",10), ("MSFT",5), ("GOOGL",3), ("NVDA",4), ("AMZN",6)]
    ),
    "Radhika Chopra - Balanced Portfolio": (
        "Radhika Chopra", "PF-2002",
        [("TSLA",8), ("XOM",15), ("JPM",7), ("META",4), ("JNJ",5)]
    ),
}
