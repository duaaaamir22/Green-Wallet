# ─────────────────────────────────────────────────────────
# config.py
# Contributor : Jugal Bhagat
# Role        : API configuration, UI theming, database layer
# ─────────────────────────────────────────────────────────
import sqlite3
import streamlit as st
from google import genai

# ── API KEYS ─────────────────────────────────────────
GEMINI_KEY  = "AIzaSyCDlbjyqSawwc9yyaikQ9aIjXzDyGM0UGI"
ALPHA_KEY   = "7MHSFXGC9EV8NS8Y"
FINNHUB_KEY = "d7h2s9pr01qhiu0a2emgd7h2s9pr01qhiu0a2en0"

client = genai.Client(api_key=GEMINI_KEY)

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
# Role        : ESG data engine — hardcoded real-world ratings,
#               Gemini AI lookup, Finnhub fallback, caching layer
# ─────────────────────────────────────────────────────────
import json
import requests
from datetime import datetime, timedelta
from config import client, FINNHUB_KEY, q

# ── REAL-WORLD ESG SCORES (MSCI / Sustainalytics public data) ──
KNOWN_ESG = {
    "AAPL": (82,65,73,73,"Technology","Strong privacy practices and renewable energy commitments"),
    "MSFT": (85,78,80,81,"Technology","Industry leader in carbon negative pledge and AI ethics"),
    "GOOGL": (70,62,58,63,"Technology","Strong on renewable energy but governance concerns around data privacy"),
    "NVDA": (60,55,65,60,"Semiconductors","Growing focus on energy-efficient computing"),
    "AMZN": (45,42,50,46,"E-Commerce","High carbon footprint offset partially by renewable investments"),
    "META": (55,38,42,45,"Technology","Renewable data centers but social score impacted by content issues"),
    "NFLX": (58,52,60,57,"Entertainment","Moderate ESG with growing content diversity initiatives"),
    "CRM":  (78,75,72,75,"Cloud Software","Strong ESG performer with net-zero commitment"),
    "INTC": (74,68,66,69,"Semiconductors","Solid environmental track record"),
    "AMD":  (62,58,64,61,"Semiconductors","Improving energy efficiency but limited ESG disclosure"),
    "TSLA": (72,35,40,49,"Automotive","Strong environmental mission but governance concerns"),
    "XOM":  (18,32,45,32,"Oil & Gas","Low environmental score due to fossil fuel core business"),
    "CVX":  (22,35,48,35,"Oil & Gas","Heavy fossil fuel exposure with modest transition efforts"),
    "NEE":  (88,70,74,77,"Renewable Energy","Leading US utility in wind and solar capacity"),
    "ENPH": (84,62,68,71,"Clean Energy","Solar microinverter leader in clean energy transition"),
    "JPM":  (48,55,60,54,"Financial Services","Moderate ESG with fossil fuel financing scrutiny"),
    "GS":   (44,50,58,51,"Financial Services","Active in green bonds but controversial project financing"),
    "V":    (62,68,75,68,"Financial Services","Strong governance and data security"),
    "MA":   (64,66,74,68,"Financial Services","Strong governance and financial inclusion initiatives"),
    "JNJ":  (68,72,70,70,"Healthcare","Strong social responsibility but product safety litigation"),
    "PFE":  (65,74,62,67,"Pharmaceuticals","High social score from vaccine access programs"),
    "UNH":  (55,68,66,63,"Health Insurance","Growing health equity focus but pricing scrutiny"),
    "KO":   (58,65,68,64,"Beverages","Plastic waste challenges but strong water stewardship"),
    "PEP":  (60,63,66,63,"Beverages","Ongoing packaging sustainability investments"),
    "NKE":  (56,48,58,54,"Apparel","Supply chain labor concerns offset by climate commitments"),
    "SBUX": (64,60,55,60,"Food & Beverage","Ethical sourcing but labor relations issues"),
    "BA":   (40,45,35,40,"Aerospace","Safety governance failures and defense sector exposure"),
    "DIS":  (62,70,58,63,"Entertainment","Strong social metrics but governance faced pressure"),
    "WMT":  (52,55,60,56,"Retail","Renewable energy push but labor practices scrutiny"),
    "COST": (58,62,72,64,"Retail","Strong employee treatment but limited environmental disclosure"),
}

def fetch_esg_gemini(ticker):
    """Asks Google Gemini AI for real-world ESG scores from public data."""
    try:
        resp = client.models.generate_content(
            model="gemini-2.0-flash-001",
            contents=(
                f'ESG analyst: For "{ticker}" return ONLY JSON: '
                f'{{"environmental":<0-100>,"social":<0-100>,"governance":<0-100>,'
                f'"composite":<0-100>,"sector":"<n>","explanation":"<1 sentence>"}}'
                f' Use real MSCI/Sustainalytics data.'
            )
        )
        d = json.loads(resp.text.strip().replace("```json","").replace("```",""))
        return float(d["environmental"]),float(d["social"]),float(d["governance"]),float(d["composite"]),"Gemini AI",d.get("sector",""),d.get("explanation","")
    except:
        return None

def fetch_esg_finnhub(ticker):
    """Fallback: fetches ESG data from Finnhub free API."""
    try:
        r = requests.get(f"https://finnhub.io/api/v1/stock/esg?symbol={ticker}&token={FINNHUB_KEY}", timeout=8).json()
        if r.get("data") and len(r["data"]) > 0:
            d = r["data"][-1]
            e = float(d.get("environmentalScore", 0))
            s = float(d.get("socialScore", 0))
            g = float(d.get("governanceScore", 0))
            if e > 0:
                return e, s, g, float(d.get("totalESGScore", round((e+s+g)/3, 1))), "Finnhub", "", ""
    except:
        pass
    return None

def get_esg(ticker):
    """Main ESG fetch: known data → database cache → Gemini AI → Finnhub."""
    if ticker in KNOWN_ESG:
        e, s, g, comp, sector, expl = KNOWN_ESG[ticker]
        return e, s, g, comp, "MSCI/Sustainalytics", sector, expl
    try:
        row = q("SELECT * FROM esg_cache WHERE ticker=?", (ticker,), one=True)
        if row and len(row) >= 9 and row[8]:
            if datetime.now() - datetime.strptime(str(row[8])[:19], "%Y-%m-%d %H:%M:%S") < timedelta(days=7):
                return row[1], row[2], row[3], row[4], row[5], row[6] or "", row[7] or ""
    except:
        pass
    result = fetch_esg_gemini(ticker)
    if result:
        e, s, g, comp, src, sector, expl = result
        q("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)", (ticker, e, s, g, comp, src, sector, expl, datetime.now()))
        return e, s, g, comp, src, sector, expl
    result = fetch_esg_finnhub(ticker)
    if result:
        e, s, g, comp, src, _, _ = result
        q("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)", (ticker, e, s, g, comp, src, "", "", datetime.now()))
        return e, s, g, comp, src, "", ""
    return 0, 0, 0, 0, "Unavailable", "", "No ESG data available."
