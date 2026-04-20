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
