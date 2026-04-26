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
 # ══════════════════════════════════════════════════════════
# TEST SECTION 2: ESG Data Engine (Radhika Chopra — esg_engine.py)
# ══════════════════════════════════════════════════════════
class TestESGData(unittest.TestCase):
    """Tests for ESG dataset integrity and scoring accuracy."""

    def setUp(self):
        from esg_engine import KNOWN_ESG, get_esg
        self.known = KNOWN_ESG
        self.get_esg = get_esg

    def test_dataset_has_30_stocks(self):
        self.assertEqual(len(self.known), 30)

    def test_all_env_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[0] <= 100, f"{ticker} env={data[0]}")

    def test_all_soc_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[1] <= 100, f"{ticker} soc={data[1]}")

    def test_all_gov_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[2] <= 100, f"{ticker} gov={data[2]}")

    def test_all_composite_scores_valid(self):
        for ticker, data in self.known.items():
            self.assertTrue(0 <= data[3] <= 100, f"{ticker} comp={data[3]}")

    def test_xom_low_environmental(self):
        self.assertLess(self.known["XOM"][0], 25)

    def test_cvx_low_environmental(self):
        self.assertLess(self.known["CVX"][0], 25)

    def test_msft_high_composite(self):
        self.assertGreater(self.known["MSFT"][3], 75)

    def test_aapl_high_composite(self):
        self.assertGreater(self.known["AAPL"][3], 70)

    def test_nee_high_environmental(self):
        self.assertGreater(self.known["NEE"][0], 85)

    def test_enph_high_environmental(self):
        self.assertGreater(self.known["ENPH"][0], 80)

    def test_every_stock_has_sector(self):
        for ticker, data in self.known.items():
            self.assertTrue(len(data[4]) > 0, f"{ticker} missing sector")

    def test_every_stock_has_explanation(self):
        for ticker, data in self.known.items():
            self.assertTrue(len(data[5]) > 0, f"{ticker} missing explanation")

    def test_get_esg_returns_known_data(self):
        e, s, g, comp, src, sector, expl = self.get_esg("AAPL")
        self.assertEqual(comp, 73)
        self.assertEqual(src, "MSCI/Sustainalytics")

    def test_get_esg_returns_7_values(self):
        result = self.get_esg("MSFT")
        self.assertEqual(len(result), 7)

    def test_unknown_ticker_doesnt_crash(self):
        result = self.get_esg("ZZZZZ")
        self.assertEqual(len(result), 7)

# ══════════════════════════════════════════════════════════
# HELPERS.PY TESTS — Ariba Khan
# ══════════════════════════════════════════════════════════

class TestHelpers:
    """Tests for tier classifier, score math, and demo data."""

    G, M, D = "#00b894", "#f59e0b", "#ef4444"

    def tier(self, s):
        if s >= 70: return "Sustainable", "pg", self.G
        if s >= 40: return "Moderate",    "py", self.M
        return "High Risk", "pr", self.D

    # ── Tier classifier ──────────────────────────────────
    def test_tier_sustainable_exact_boundary(self):
        label, css, color = self.tier(70)
        assert label == "Sustainable"
        assert color == self.G

    def test_tier_sustainable_high(self):
        label, _, _ = self.tier(95)
        assert label == "Sustainable"

    def test_tier_moderate_exact_lower(self):
        label, css, _ = self.tier(40)
        assert label == "Moderate"
        assert css   == "py"

    def test_tier_moderate_mid(self):
        label, _, _ = self.tier(55)
        assert label == "Moderate"

    def test_tier_high_risk_just_below(self):
        label, css, color = self.tier(39)
        assert label == "High Risk"
        assert css   == "pr"
        assert color == self.D

    def test_tier_zero_score(self):
        label, _, _ = self.tier(0)
        assert label == "High Risk"

    def test_tier_hundred_score(self):
        label, _, _ = self.tier(100)
        assert label == "Sustainable"

    # ── Green Score formula ──────────────────────────────
    def test_weighted_score_calculation(self):
        """Capital-weighted average ESG score."""
        pdata = [
            {"esg": 73, "value": 10000},  # AAPL
            {"esg": 81, "value": 5000},   # MSFT
            {"esg": 46, "value": 6000},   # AMZN
        ]
        total = sum(s["value"] for s in pdata)
        score = round(sum(s["value"] * s["esg"] for s in pdata) / total, 1)
        assert score == pytest.approx(67.2, abs=0.5)

    def test_zero_value_portfolio_no_crash(self):
        """If all shares are 0, should not divide by zero."""
        pdata = [{"esg": 73, "value": 0}, {"esg": 50, "value": 0}]
        total = sum(s["value"] for s in pdata)
        score = round(sum(s["value"] * s["esg"] for s in pdata) / total, 1) if total > 0 else 0
        assert score == 0

    def test_single_holding_score_equals_esg(self):
        pdata = [{"esg": 77, "value": 5000}]
        total = sum(s["value"] for s in pdata)
        score = round(sum(s["value"] * s["esg"] for s in pdata) / total, 1)
        assert score == 77.0

# ══════════════════════════════════════════════════════════
# APP.PY TESTS — Duaa Aamir
# ══════════════════════════════════════════════════════════

class TestDemoData:
    """Tests for demo portfolio integrity and PIN logic."""

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
    DEMO_PIN = "123456"

    def test_two_demo_portfolios_exist(self):
        assert len(self.DEMOS) == 2

    def test_jugal_portfolio_has_5_stocks(self):
        _, _, stocks = self.DEMOS["Jugal Bhagat - Tech Growth Portfolio"]
        assert len(stocks) == 5

    def test_radhika_portfolio_has_5_stocks(self):
        _, _, stocks = self.DEMOS["Radhika Chopra - Balanced Portfolio"]
        assert len(stocks) == 5

    def test_portfolio_numbers_are_unique(self):
        pnos = [v[1] for v in self.DEMOS.values()]
        assert len(pnos) == len(set(pnos)), "Portfolio numbers must be unique"

    def test_jugal_portfolio_tickers(self):
        _, _, stocks = self.DEMOS["Jugal Bhagat - Tech Growth Portfolio"]
        tickers = [t for t, _ in stocks]
        assert "AAPL" in tickers
        assert "MSFT" in tickers
        assert "NVDA" in tickers

    def test_radhika_portfolio_has_high_risk_stock(self):
        """XOM is in Radhika's portfolio — ESG 32, should be flagged."""
        KNOWN_ESG = {"XOM": (18,32,45,32,"Oil & Gas","Low environmental score")}
        _, _, stocks = self.DEMOS["Radhika Chopra - Balanced Portfolio"]
        tickers = [t for t, _ in stocks]
        assert "XOM" in tickers
        assert KNOWN_ESG["XOM"][3] < 40

    def test_all_shares_are_positive(self):
        for name, (_, _, stocks) in self.DEMOS.items():
            for ticker, shares in stocks:
                assert shares > 0, f"{ticker} in {name} has non-positive shares"

    def test_correct_pin_accepted(self):
        assert self.DEMO_PIN == "123456"

    def test_wrong_pin_rejected(self):
        assert "000000" != self.DEMO_PIN
        assert "111111" != self.DEMO_PIN

    def test_flagged_logic(self):
        """Stocks with ESG < 30 should be flagged."""
        pdata = [
            {"ticker": "AAPL", "esg": 73},
            {"ticker": "XOM",  "esg": 32},
            {"ticker": "FAKE", "esg": 15},  # flagged
        ]
        flagged = [s for s in pdata if s["esg"] < 30]
        assert len(flagged) == 1
        assert flagged[0]["ticker"] == "FAKE"

