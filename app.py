# app.py
# Contributor : Duaa Aamir
# Role        : Main Streamlit application — login/register,
#               home screen, data-fetch animation, 6 dashboard tabs
# ─────────────────────────────────────────────────────────
import streamlit as st
import pandas as pd
import time
from config import G, M, D, BG, CARD, BORDER, TEXT, MUTED, APP_CSS, q
from esg_engine import get_esg
from helpers import get_price, tier, bar, ask_advisor, DEMOS

st.set_page_config(page_title="GreenWallet", page_icon="🌿", layout="centered", initial_sidebar_state="collapsed")
st.markdown(f"<style>{APP_CSS}</style>", unsafe_allow_html=True)

for k,v in dict(screen="login",user=None,uid=None,pdata=[],score=0,chat=[]).items():
    if k not in st.session_state: st.session_state[k]=v

# ═══════════════════════════════════════════════════════
# SCREEN 1: LOGIN / REGISTER
# ═══════════════════════════════════════════════════════
if st.session_state.screen == "login":
    st.markdown(f"<div style='text-align:center;padding:28px 0 20px;'><div style='font-size:28px;'>🌿</div><div style='font-size:26px;font-weight:700;color:{TEXT};'>Green<span style=\"color:{G}\">Wallet</span></div><div style='font-size:13px;color:{MUTED};margin-top:4px;'>ESG Portfolio Impact Scorer</div></div>",unsafe_allow_html=True)
    st.markdown(f"<div style='background:#0d1421;border:1px solid {BORDER};border-radius:14px;padding:16px 18px;margin-bottom:20px;font-size:13px;color:{MUTED};line-height:1.8;'>Track the <strong style='color:{TEXT};'>environmental and ethical impact</strong> of your investments. Login or create an account to get started.</div>",unsafe_allow_html=True)
    t1,t2 = st.tabs(["Login","Register"])
    with t1:
        login_user = st.text_input("Username",key="lu")
        if st.button("Login",key="lb"):
            user = q("SELECT * FROM users WHERE username=?",(login_user.strip(),),one=True)
            if user: st.session_state.update(user=user,uid=user[0],screen="home"); st.rerun()
            else: st.error("Account not found. Register first.")
    with t2:
        reg_user = st.text_input("Choose username",key="ru")
        reg_pno = st.text_input("Portfolio number (optional)",key="rp")
        if st.button("Create Account",key="rb"):
            if not reg_user.strip(): st.error("Enter a username.")
            elif q("SELECT * FROM users WHERE username=?",(reg_user.strip(),),one=True): st.error("Username taken.")
            else:
                uid = q("INSERT INTO users(username,portfolio_no) VALUES(?,?)",(reg_user.strip(),reg_pno.strip()))
                user = q("SELECT * FROM users WHERE username=?",(reg_user.strip(),),one=True)
                st.session_state.update(user=user,uid=user[0],screen="home"); st.rerun()
    st.caption("Demo accounts: **demo_investor** · **demo_trader** — pre-registered with portfolios")
    if not q("SELECT * FROM users WHERE username='demo_investor'",one=True):
        uid1 = q("INSERT INTO users(username,portfolio_no) VALUES('demo_investor','PF-1001')")
        for t,s in DEMOS["Tech Growth Portfolio"]: q("INSERT INTO holdings(user_id,ticker,shares) VALUES(?,?,?)",(uid1,t,s))
        uid2 = q("INSERT INTO users(username,portfolio_no) VALUES('demo_trader','PF-2002')")
        for t,s in DEMOS["Balanced Portfolio"]: q("INSERT INTO holdings(user_id,ticker,shares) VALUES(?,?,?)",(uid2,t,s))

# ═══════════════════════════════════════════════════════
# SCREEN 2: HOME
# ═══════════════════════════════════════════════════════
elif st.session_state.screen == "home":
    user,uid = st.session_state.user, st.session_state.uid
    st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:12px 0 14px;border-bottom:1px solid {BORDER};margin-bottom:14px;'><div style='font-size:18px;font-weight:700;color:{TEXT};'>🌿 Green<span style=\"color:{G}\">Wallet</span></div><div style='font-size:12px;color:{MUTED};'>👤 {user[1]}</div></div>",unsafe_allow_html=True)
    holdings = q("SELECT * FROM holdings WHERE user_id=?",(uid,),fetch=True)
    if holdings:
        st.markdown(f"<div class='c ca'><div style='font-size:13px;color:{TEXT};'>You have <strong>{len(holdings)} stocks</strong> in your portfolio.</div></div>",unsafe_allow_html=True)
        if st.button("📊 Load My Portfolio"): st.session_state.screen="fetch"; st.rerun()
    else:
        st.markdown(f"<div class='c' style='text-align:center;'><div style='font-size:18px;font-weight:700;color:{TEXT};margin-bottom:8px;'>No Portfolio Connected</div><div style='font-size:13px;color:{MUTED};'>Connect a demo portfolio below or add stocks manually.</div></div>",unsafe_allow_html=True)
    st.markdown(f"<div class='sec'>Connect a Demo Portfolio</div>",unsafe_allow_html=True)
    demo_choice = st.selectbox("Choose portfolio",list(DEMOS.keys()),label_visibility="collapsed")
    if st.button("Connect Portfolio"):
        q("DELETE FROM holdings WHERE user_id=?",(uid,))
        for t,s in DEMOS[demo_choice]: q("INSERT INTO holdings(user_id,ticker,shares) VALUES(?,?,?)",(uid,t,s))
        st.session_state.screen="fetch"; st.rerun()
    st.markdown(f"<div class='sec'>Or Add Stocks Manually</div>",unsafe_allow_html=True)
    c1,c2 = st.columns([3,1])
    tick = c1.text_input("Ticker",placeholder="e.g. AAPL",label_visibility="collapsed")
    shares = c2.number_input("Shares",min_value=1.0,value=5.0,label_visibility="collapsed")
    if st.button("➕ Add Stock") and tick.strip():
        q("INSERT INTO holdings(user_id,ticker,shares) VALUES(?,?,?)",(uid,tick.upper().strip(),shares)); st.rerun()
    if holdings:
        st.markdown(f"<div class='sec'>Current Holdings</div>",unsafe_allow_html=True)
        for h in holdings: st.markdown(f"<div class='r'><span class='rl'>{h[2]}</span><span class='rv'>{h[3]} shares</span></div>",unsafe_allow_html=True)
    st.markdown("---")
    if st.button("🚪 Logout"):
        for k,v in dict(screen="login",user=None,uid=None,pdata=[],score=0,chat=[]).items(): st.session_state[k]=v
        st.rerun()

# ═══════════════════════════════════════════════════════
# SCREEN 3: FETCHING
# ═══════════════════════════════════════════════════════
elif st.session_state.screen == "fetch":
    user,uid = st.session_state.user, st.session_state.uid
    st.markdown(f"<div style='text-align:center;padding:28px 0 20px;'><div style='font-size:20px;font-weight:600;color:{TEXT};'>Analyzing {user[1]}'s portfolio</div><div style='font-size:13px;color:{MUTED};margin-top:6px;'>Fetching real ESG data + live prices</div></div>",unsafe_allow_html=True)
    holdings = q("SELECT * FROM holdings WHERE user_id=?",(uid,),fetch=True)
    prog = st.progress(0); status = st.empty(); pdata = []
    for i,h in enumerate(holdings):
        status.markdown(f"⏳ **{h[2]}** — fetching ESG scores..."); prog.progress((i+1)/len(holdings))
        price = get_price(h[2]); e,s,g,comp,src,sector,expl = get_esg(h[2])
        pdata.append(dict(ticker=h[2],shares=h[3],price=price,env=e,soc=s,gov=g,esg=comp,source=src,sector=sector,expl=expl,value=h[3]*price))
    status.markdown(f"✅ **{len(holdings)} stocks analyzed**")
    total = sum(s["value"] for s in pdata)
    score = round(sum(s["value"]*s["esg"] for s in pdata)/total,1) if total>0 else 0
    st.session_state.update(pdata=pdata,score=score,screen="app"); time.sleep(0.5); st.rerun()

# ═══════════════════════════════════════════════════════
# SCREEN 4: DASHBOARD (6 tabs)
# ═══════════════════════════════════════════════════════
elif st.session_state.screen == "app":
    user,uid,pdata,sc = st.session_state.user,st.session_state.uid,st.session_state.pdata,st.session_state.score
    lbl,css,col = tier(sc); flagged = [s for s in pdata if s["esg"]<30]; total = sum(s["value"] for s in pdata)
    st.markdown(f"<div style='display:flex;justify-content:space-between;align-items:center;padding:12px 0 14px;border-bottom:1px solid {BORDER};margin-bottom:14px;'><div style='font-size:18px;font-weight:700;color:{TEXT};'>🌿 Green<span style=\"color:{G}\">Wallet</span></div><div style='font-size:12px;color:{MUTED};'>{user[1]} · {user[2]}</div></div>",unsafe_allow_html=True)
    tabs = st.tabs(["Score","Holdings","ESG Deep Dive","Analytics","Simulator","AI Advisor"])

    with tabs[0]:
        st.markdown(f"<div class='c' style='text-align:center;'><div style='font-size:11px;color:{MUTED};text-transform:uppercase;letter-spacing:0.8px;'>Portfolio Green Score</div><div style='font-size:72px;font-weight:900;color:{col};line-height:1;'>{int(sc)}</div><div style='margin:8px 0;'><span class='pill {css}'>{lbl}</span></div><div style='font-size:12px;color:{MUTED};'>out of 100 · {len(pdata)} holdings · weighted by capital</div></div>",unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        c1.markdown(f"<div class='c' style='text-align:center;'><div style='font-size:11px;color:{MUTED};'>VALUE</div><div style='font-size:20px;font-weight:700;color:{TEXT};'>${total:,.0f}</div></div>",unsafe_allow_html=True)
        c2.markdown(f"<div class='c' style='text-align:center;'><div style='font-size:11px;color:{MUTED};'>HOLDINGS</div><div style='font-size:20px;font-weight:700;color:{TEXT};'>{len(pdata)}</div></div>",unsafe_allow_html=True)
        fc = D if flagged else G
        c3.markdown(f"<div class='c' style='text-align:center;'><div style='font-size:11px;color:{MUTED};'>FLAGGED</div><div style='font-size:20px;font-weight:700;color:{fc};'>{len(flagged)}</div></div>",unsafe_allow_html=True)
        st.markdown(f"<div class='sec'>API Status</div>",unsafe_allow_html=True)
        sources = set(s["source"] for s in pdata)
        for api,desc in [("MSCI/Sustainalytics","Verified real-world ESG ratings"),("Gemini AI","AI-powered ESG lookup"),("Finnhub","ESG endpoint (backup)"),("yfinance","Real-time stock prices")]:
            dot = "🟢" if api in sources or api=="yfinance" else "🟡"
            st.markdown(f"<div class='r'><span class='rl'>{dot} {api}</span><span style='font-size:11px;color:{MUTED};'>{desc}</span></div>",unsafe_allow_html=True)
        if st.button("💾 Save Score to History"): q("INSERT INTO analytics(user_id,green_score) VALUES(?,?)",(uid,int(sc))); st.success("Saved!")

    with tabs[1]:
        for s in sorted(pdata,key=lambda x:x["esg"],reverse=True):
            c = G if s["esg"]>=60 else M if s["esg"]>=30 else D; flag = "⚠️" if s["esg"]<30 else "✅" if s["esg"]>=60 else "⚡"; pct = s["value"]/total*100 if total>0 else 0
            st.markdown(f"<div class='sr' style='border-color:{c}22;'><div style='flex:1;'><div style='font-size:14px;font-weight:600;color:{TEXT};'>{s['ticker']} <span style='font-size:11px;color:{MUTED};font-weight:400;'>· {s['sector']}</span></div><div style='font-size:11px;color:{MUTED};'>{s['shares']} shares · ${s['price']:.2f} · {pct:.1f}% · via {s['source']}</div><div style='font-size:11px;color:{MUTED};font-style:italic;margin-top:2px;'>{s['expl']}</div></div><div style='text-align:right;'><div style='font-size:22px;font-weight:700;color:{c};'>{int(s['esg'])}</div><div style='font-size:10px;color:{MUTED};'>{flag}</div></div></div>",unsafe_allow_html=True)

    with tabs[2]:
        sel = st.selectbox("Select stock",[s["ticker"] for s in pdata],label_visibility="collapsed"); s = next(x for x in pdata if x["ticker"]==sel)
        c2 = G if s["esg"]>=60 else M if s["esg"]>=30 else D
        st.markdown(f"<div class='c' style='text-align:center;'><div style='font-size:22px;font-weight:700;color:{TEXT};'>{s['ticker']}</div><div style='font-size:12px;color:{MUTED};'>{s['sector']} · via {s['source']}</div><div style='font-size:52px;font-weight:900;color:{c2};margin:12px 0;'>{int(s['esg'])}</div><div style='font-size:13px;color:{MUTED};font-style:italic;'>{s['expl']}</div></div>",unsafe_allow_html=True)
        bar("🌍 Environmental",s["env"],G); bar("👥 Social",s["soc"],"#00cec9"); bar("🏛️ Governance",s["gov"],"#6366f1")

    with tabs[3]:
        data = q("SELECT green_score,recorded_at FROM analytics WHERE user_id=? ORDER BY recorded_at",(uid,),fetch=True)
        if data:
            df = pd.DataFrame(data,columns=["Green Score","Date"]); df["Date"]=pd.to_datetime(df["Date"]); st.line_chart(df.set_index("Date")["Green Score"],color=G)
        else: st.info("No history yet. Save scores from Score tab.")
        st.markdown(f"<div class='sec'>ESG Heatmap</div>",unsafe_allow_html=True)
        for s in sorted(pdata,key=lambda x:x["esg"],reverse=True):
            c = G if s["esg"]>=60 else M if s["esg"]>=30 else D
            st.markdown(f"<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px;'><span style='font-size:12px;color:{MUTED};width:50px;'>{s['ticker']}</span><div class='pb' style='flex:1;margin:0;'><div class='pf' style='width:{max(s['esg'],5)}%;background:{c};'></div></div><span style='font-size:12px;font-weight:700;color:{c};width:30px;text-align:right;'>{int(s['esg'])}</span></div>",unsafe_allow_html=True)

    with tabs[4]:
        st.markdown(f"<div class='c ca'><div style='font-size:11px;color:{G};'>What-If Simulator</div><div style='font-size:13px;color:{MUTED};margin-top:6px;'>Adjust shares and watch your Green Score change.</div></div>",unsafe_allow_html=True)
        sim = []
        for s in pdata:
            ns = st.slider(f"{s['ticker']} · ESG {int(s['esg'])}",0.0,float(s['shares']*3),float(s['shares']),1.0,key=f"s_{s['ticker']}"); sim.append(dict(esg=s["esg"],value=ns*s["price"]))
        st2 = sum(x["value"] for x in sim); sim_sc = sum(x["value"]*x["esg"] for x in sim)/st2 if st2>0 else 0; diff = sim_sc-sc; sl,scl,scol = tier(sim_sc); dc = G if diff>0 else D if diff<0 else MUTED
        st.markdown(f"<div class='c' style='text-align:center;'><div style='display:flex;justify-content:center;gap:40px;'><div><div style='font-size:12px;color:{MUTED};'>Current</div><div style='font-size:32px;font-weight:700;color:{col};'>{int(sc)}</div></div><div style='font-size:24px;color:{dc};font-weight:700;margin-top:16px;'>→</div><div><div style='font-size:12px;color:{MUTED};'>Simulated</div><div style='font-size:32px;font-weight:700;color:{scol};'>{int(sim_sc)}</div></div></div><div style='font-size:28px;font-weight:700;color:{dc};margin-top:8px;'>{'+'if diff>0 else''}{diff:.1f} pts</div><span class='pill {scl}'>{sl}</span></div>",unsafe_allow_html=True)

    with tabs[5]:
        st.markdown(f"<div class='c ca'><div style='font-size:11px;color:{G};'>AI ESG Advisor · Powered by Gemini</div><div style='font-size:13px;color:{MUTED};margin-top:6px;'>Score: <strong style='color:{TEXT};'>{int(sc)}/100</strong> · {lbl} · {len(pdata)} holdings</div></div>",unsafe_allow_html=True)
        if not st.session_state.chat:
            for i,question in enumerate(["How can I improve my score?","Which stock is my biggest risk?","Compare to benchmarks","Environmental breakdown"]):
                if st.button(question,key=f"q{i}"):
                    with st.spinner("Thinking..."): reply = ask_advisor(question,pdata,sc)
                    st.session_state.chat+=[{"r":"u","t":question},{"r":"b","t":reply}]; st.rerun()
        for m in st.session_state.chat: st.markdown(f"<div class='chat-{'u'if m['r']=='u'else'b'}'>{m['t']}</div>",unsafe_allow_html=True)
        inp = st.chat_input("Ask about your portfolio's ESG impact...")
        if inp:
            with st.spinner("Thinking..."): reply = ask_advisor(inp,pdata,sc)
            st.session_state.chat+=[{"r":"u","t":inp},{"r":"b","t":reply}]; st.rerun()

    st.markdown("---")
    c1,c2 = st.columns(2)
    with c1:
        if st.button("🔄 Back to Home"): st.session_state.update(screen="home",pdata=[],score=0,chat=[]); st.rerun()
    with c2:
        if st.button("🚪 Logout"):
            for k,v in dict(screen="login",user=None,uid=None,pdata=[],score=0,chat=[]).items(): st.session_state[k]=v
            st.rerun()
    st.markdown(f"<p style='text-align:center;font-size:11px;color:{BORDER};'>GreenWallet v2.0 · Gemini AI · Finnhub · yfinance</p>",unsafe_allow_html=True)
