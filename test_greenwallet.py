# ─────────────────────────────────────────────────────────
# test_greenwallet.py
# Unit tests for GreenWallet ESG Portfolio Impact Scorer
# Run: python -m pytest test_greenwallet.py -v
# ─────────────────────────────────────────────────────────
import unittest
import sqlite3
from datetime import datetime

# ══════════════════════════════════════════════════════════
# TEST SECTION 1: Database Layer (Jugal Bhagat — config.py)
# ══════════════════════════════════════════════════════════
class TestDatabase(unittest.TestCase):
    """Tests for database schema creation and CRUD operations."""

    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        c = self.conn.cursor()
        c.execute('CREATE TABLE users (id INTEGER PRIMARY KEY AUTOINCREMENT, username TEXT UNIQUE, portfolio_no TEXT DEFAULT "")')
        c.execute('CREATE TABLE holdings (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, ticker TEXT, shares REAL)')
        c.execute('CREATE TABLE esg_cache (ticker TEXT PRIMARY KEY, env REAL, soc REAL, gov REAL, composite REAL, source TEXT, sector TEXT, explanation TEXT, fetched_at TIMESTAMP)')
        c.execute('CREATE TABLE analytics (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INT, green_score REAL, recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)')
        self.conn.commit()

    def test_create_user(self):
        self.conn.execute("INSERT INTO users(username,portfolio_no) VALUES(?,?)", ("testuser","PF-001"))
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM users WHERE username='testuser'").fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[1], "testuser")
        self.assertEqual(row[2], "PF-001")

    def test_duplicate_user_rejected(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute("INSERT INTO users(username) VALUES('testuser')")

    def test_add_holding(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM holdings WHERE user_id=1").fetchone()
        self.assertEqual(row[2], "AAPL")
        self.assertEqual(row[3], 10.0)

    def test_multiple_holdings_per_user(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'MSFT',5)")
        self.conn.commit()
        rows = self.conn.execute("SELECT * FROM holdings WHERE user_id=1").fetchall()
        self.assertEqual(len(rows), 2)

    def test_delete_holding(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.commit()
        self.conn.execute("DELETE FROM holdings WHERE ticker='AAPL' AND user_id=1")
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM holdings WHERE user_id=1").fetchone()
        self.assertIsNone(row)

    def test_update_shares(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO holdings(user_id,ticker,shares) VALUES(1,'AAPL',10)")
        self.conn.commit()
        self.conn.execute("UPDATE holdings SET shares=25 WHERE ticker='AAPL' AND user_id=1")
        self.conn.commit()
        row = self.conn.execute("SELECT shares FROM holdings WHERE ticker='AAPL'").fetchone()
        self.assertEqual(row[0], 25.0)

    def test_save_green_score(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,72)")
        self.conn.commit()
        row = self.conn.execute("SELECT green_score FROM analytics WHERE user_id=1").fetchone()
        self.assertEqual(row[0], 72.0)

    def test_multiple_analytics_entries(self):
        self.conn.execute("INSERT INTO users(username) VALUES('testuser')")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,50)")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,55)")
        self.conn.execute("INSERT INTO analytics(user_id,green_score) VALUES(1,60)")
        self.conn.commit()
        rows = self.conn.execute("SELECT * FROM analytics WHERE user_id=1").fetchall()
        self.assertEqual(len(rows), 3)

    def test_esg_cache_write_and_read(self):
        self.conn.execute("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)",
            ("AAPL",82,65,73,73,"MSCI","Technology","Strong ESG",datetime.now()))
        self.conn.commit()
        row = self.conn.execute("SELECT * FROM esg_cache WHERE ticker='AAPL'").fetchone()
        self.assertEqual(row[0], "AAPL")
        self.assertEqual(row[1], 82)
        self.assertEqual(row[4], 73)

    def test_esg_cache_overwrite(self):
        self.conn.execute("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)",
            ("AAPL",82,65,73,73,"MSCI","Technology","Old",datetime.now()))
        self.conn.execute("REPLACE INTO esg_cache VALUES(?,?,?,?,?,?,?,?,?)",
            ("AAPL",85,70,75,77,"Gemini","Technology","Updated",datetime.now()))
        self.conn.commit()
        row = self.conn.execute("SELECT composite,explanation FROM esg_cache WHERE ticker='AAPL'").fetchone()
        self.assertEqual(row[0], 77)
        self.assertEqual(row[1], "Updated")

    def tearDown(self):
        self.conn.close()
