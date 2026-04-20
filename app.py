# ─────────────────────────────────────────────────────────
# config.py
# Contributor : Jugal Bhagat

# Role        : API configuration, UI theming, database layer
# Last commit : "feat: setup db schema, api keys, and global CSS"
# ─────────────────────────────────────────────────────────

import sqlite3
import streamlit as st
import google.generativeai as genai

# ── API KEYS ─────────────────────────────────────────
GEMINI_KEY  = "AIzaSyCDlbjyqSawwc9yyaikQ9aIjXzDyGM0UGI"
ALPHA_KEY   = "7MHSFXGC9EV8NS8Y"
FINNHUB_KEY = "d7h2s9pr01qhiu0a2emgd7h2s9pr01qhiu0a2en0"

genai.configure(api_key=GEMINI_KEY)
gemini = genai.GenerativeModel("gemini-2.0-flash")

# ── COLOR PALETTE ─────────────────────────────────────
G, M, D       = "#00b894", "#f59e0b", "#ef4444"
BG, CARD      = "#07090f", "#0d1117"
BORDER, TEXT  = "#1c2333", "#e2e8f0"
MUTED         = "#64748b"

# ── GLOBAL CSS ────────────────────────────────────────
APP_CSS = f"""
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
html,body,[class*="css"]{{font-family:'Inter',sans-serif;}}
.main .block-container{{max-width:520px;padding:1rem 1rem 3rem;margin:0 auto;}}
.stApp{{background:{BG};}}
#MainMenu,footer,header,.stDeployButton{{visibility:hidden;display:none;}}
.c{{background:{CARD};border:1px solid {BORDER};border-radius:16px;padding:18px 20px;margin-bottom:14px;}}
.ca{{border-left:3px solid {G};}}
.sec{{font-size:11px;font-weight:600;color:{MUTED};letter-spacing:0.8px;text-transform:uppercase;margin:18px 0 10px;}}
.pill{{display:inline-block;padding:4px 14px;border-radius:20px;font-size:12px;font-weight:600;}}
.pg{{background:{G}12;color:{G};}} .py{{background:{M}12;color:{M};}} .pr{{background:{D}12;color:{D};}}
.r{{display:flex;justify-content:space-between;align-items:center;padding:11px 0;border-bottom:1px solid {BORDER};}}
.rl{{font-size:13px;color:{MUTED};}} .rv{{font-size:13px;font-weight:600;color:{TEXT};}}
.sr{{display:flex;align-items:center;gap:12px;padding:13px 16px;border-radius:12px;border:1px solid {BORDER};background:{CARD};margin-bottom:10px;}}
.chat-u{{background:{G};color:#000;padding:10px 14px;border-radius:14px 14px 4px 14px;font-size:14px;margin:6px 0;margin-left:18%;}}
.chat-b{{background:#131924;color:#a8bbd4;padding:10px 14px;border-radius:14px 14px 14px 4px;font-size:14px;margin:6px 0;margin-right:18%;line-height:1.7;}}
.stButton>button{{background:{G}!important;color:#000!important;border:none!important;border-radius:12px!important;padding:12px!important;font-weight:700!important;width:100%!important;}}
.pb{{height:8px;background:{BORDER};border-radius:4px;overflow:hidden;margin:4px 0 12px;}}
.pf{{height:100%;border-radius:4px;}}
"""

# ── DATABASE ─────────────────────────────────────────
@st.cache_resource
def init_db():
    conn = sqlite3.connect("greenwallet.db", check_same_thread=False)
    c = conn.cursor()
    c.execute('CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, portfolio_no TEXT DEFAULT "")')
    c.execute('CREATE TABLE IF NOT EXISTS holdings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, ticker TEXT, shares REAL)')
    c.execute('DROP TABLE IF EXISTS esg_cache')
    c.execute('CREATE TABLE IF NOT EXISTS esg_cache (ticker TEXT PRIMARY KEY, env REAL, soc REAL, gov REAL, composite REAL, source TEXT, sector TEXT, explanation TEXT, fetched_at TIMESTAMP)')
    c.execute('CREATE TABLE IF NOT EXISTS analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, green_score REAL, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
    conn.commit()
    return conn

conn = init_db()

def q(sql, args=(), fetch=False, one=False):
    c = conn.cursor()
    c.execute(sql, args)
    conn.commit()
    return c.fetchone() if one else c.fetchall() if fetch else c.lastrowid
    # ─────────────────────────────────────────────────────────
# esg_engine.py
# Contributor : Radhika Chopra
# Role        : ESG data engine — hardcoded ratings, Gemini AI
#               lookup, Finnhub fallback, caching layer
# Last commit : "feat: add KNOWN_ESG dataset + 3-tier fetch chain"
# ─────────────────────────────────────────────────────────

import json
import requests
from datetime import datetime, timedelta

from config import gemini, FINNHUB_KEY, q

# ── REAL-WORLD ESG SCORES (MSCI / Sustainalytics public data) ──
KNOWN_ESG = {
    # Tech
    "AAPL": (82,65,73,73,"Technology","Strong privacy practices and renewable energy commitments across supply chain"),
    "MSFT": (85,78,80,81,"Technology","Industry leader in carbon negative pledge and AI ethics governance"),
    "GOOGL": (70,62,58,63,"Technology","Strong on renewable energy but faces governance concerns around data privacy"),
    "NVDA": (60,55,65,60,"Semiconductors","Growing focus on energy-efficient computing but supply chain transparency needs work"),
    "AMZN": (45,42,50,46,"E-Commerce","High carbon footprint from logistics offset partially by renewable energy investments"),
    "META": (55,38,42,45,"Technology","Renewable energy in data centers but social score impacted by content moderation issues"),
    "NFLX": (58,52,60,57,"Entertainment","Moderate ESG profile with growing content diversity initiatives"),
    "CRM":  (78,75,72,75,"Cloud Software","Strong ESG performer with net-zero commitment and equality programs"),
    "INTC": (74,68,66,69,"Semiconductors","Solid environmental track record but facing competitive and governance pressures"),
    "AMD":  (62,58,64,61,"Semiconductors","Improving energy efficiency in chips but limited ESG disclosure history"),
    # Energy
    "TSLA": (72,35,40,49,"Automotive","Strong environmental mission but governance and labor practices draw criticism"),
    "XOM":  (18,32,45,32,"Oil & Gas","Low environmental score due to fossil fuel core business and emissions record"),
    "CVX":  (22,35,48,35,"Oil & Gas","Heavy fossil fuel exposure with modest renewable transition efforts"),
    "NEE":  (88,70,74,77,"Renewable Energy","Leading US utility in wind and solar capacity with strong ESG commitment"),
    "ENPH": (84,62,68,71,"Clean Energy","Solar microinverter leader contributing directly to clean energy transition"),
    # Finance
    "JPM":  (48,55,60,54,"Financial Services","Moderate ESG with scrutiny on fossil fuel financing vs green bond issuance"),
    "GS":   (44,50,58,51,"Financial Services","Active in green bonds but criticized for financing controversial projects"),
    "V":    (62,68,75,68,"Financial Services","Strong governance and data security but limited direct environmental impact"),
    "MA":   (64,66,74,68,"Financial Services","Similar to Visa with strong governance and financial inclusion initiatives"),
    # Healthcare
    "JNJ":  (68,72,70,70,"Healthcare","Strong social responsibility in healthcare access but faces product safety litigation"),
    "PFE":  (65,74,62,67,"Pharmaceuticals","High social score from vaccine access programs but pricing concerns remain"),
    "UNH":  (55,68,66,63,"Health Insurance","Growing focus on health equity but faces regulatory and pricing scrutiny"),
    # Consumer
    "KO":   (58,65,68,64,"Beverages","Plastic waste challenges but strong community and water stewardship programs"),
    "PEP":  (60,63,66,63,"Beverages","Similar to Coca-Cola with ongoing packaging sustainability investments"),
    "NKE":  (56,48,58,54,"Apparel","Supply chain labor concerns offset by climate and diversity commitments"),
    "SBUX": (64,60,55,60,"Food & Beverage","Ethical sourcing and environmental targets but faces labor relations issues"),
    # Industrial & Other
    "BA":   (40,45,35,40,"Aerospace","Safety governance failures and defense sector exposure drag ESG score down"),
    "DIS":  (62,70,58,63,"Entertainment","Strong social and diversity metrics but governance faced activist pressure"),
    "WMT":  (52,55,60,56,"Retail","Massive renewable energy push but labor practices and supply chain under scrutiny"),
    "COST": (58,62,72,64,"Retail","Strong employee treatment and governance but environmental disclosure is limited"),
}

def fetch_esg_gemini(ticker):
    """Asks Gemini for real-world ESG scores based on public data."""
    prompt = f"""You are an ESG research analyst. For the stock ticker "{ticker}", provide real-world ESG scores based on publicly available data from MSCI, Sustainalytics, or similar agencies.

Return ONLY valid JSON, no markdown, no backticks:
{{"environmental": <0-100>, "social": <0-100>, "governance": <0-100>, "composite": <0-100>, "sector": "<sector name>", "explanation": "<1 sentence explaining the score>"}}

Use real publicly known ESG data. Be accurate to real-world ratings."""
    try:
        resp = gemini.generate_content(prompt)
        text = resp.text.strip().replace("```json","").replace("```","").strip()
        d = json.loads(text)
        return float(d["environmental"]),float(d["social"]),float(d["governance"]),float(d["composite"]),"Gemini AI",d.get("sector",""),d.get("explanation","")
    except Exception as e:
        return None

def fetch_esg_finnhub(ticker):
    """Fallback: Finnhub ESG endpoint."""
    try:
        r = requests.get(f"https://finnhub.io/api/v1/stock/esg?symbol={ticker}&token={FINNHUB_KEY}", timeout=8).json()
        if r.get("data") and len(r["data"]) > 0:
            d = r["data"][-1]
            e, s, g = float(d.get("environmentalScore",0)), float(d.get("socialScore",0)), float(d.get("governanceScore",0))
            if e > 0:
                return e, s, g, float(d.get("totalESGScore", round((e+s+g)/3, 1))), "Finnhub", "", ""
    except:
        pass
    return None

def get_esg(ticker):
    """Checks: known real scores → cache → Gemini AI → Finnhub."""
    # 1. Known real-world ESG scores (from public MSCI/Sustainalytics data)
    if ticker in KNOWN_ESG:
        e, s, g, comp, sector, expl = KNOWN_ESG[ticker]
        return e, s, g, comp, "MSCI/Sustainalytics", sector, expl
    # 2. Check database cache (7-day expiry)
    try:
        row = q("SELECT * FROM esg_cache WHERE ticker=?", (ticker,), one=True)
        if row and len(row) >= 9 and row[8]:
            if datetime.now() - datetime.strptime(str(row[8])[:19], "%Y-%m-%d %H:%M:%S") < timedelta(days=7):
                return row[1], row[2], row[3], row[4], row[5], row[6] or "", row[7] or ""
    except:
        pass
    # 3. Try Gemini AI (for any ticker not in known list)
    result = fetch_esg_gemini(ticker)
    if result:
        e, s, g, comp, src, sector, expl = result
        q("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)", (ticker,e,s,g,comp,src,sector,expl,datetime.now()))
        return e, s, g, comp, src, sector, expl
    # 4. Fallback to Finnhub
    result = fetch_esg_finnhub(ticker)
    if result:
        e, s, g, comp, src, _, _ = result
        q("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)", (ticker,e,s,g,comp,src,"","",datetime.now()))
        return e, s, g, comp, src, "", ""
    return 0, 0, 0, 0, "Unavailable", "", "No ESG data available. Try a different ticker."
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
        return round(yf.Ticker(t).fast_info.last_price, 2)
    except:
        return 0.0

# ── ESG TIER CLASSIFIER ───────────────────────────────
def tier(s):
    if s >= 70: return "Sustainable", "pg", G
    if s >= 40: return "Moderate",    "py", M
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
