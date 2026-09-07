"""
🚦 Recommendation - Final Decision Engine
Combines all module scores with weights
"""

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Recommendation", page_icon="🚦", layout="wide")

# Check data
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded!")
    st.stop()

df = st.session_state.data.copy()
spot = st.session_state.get('spot_price', 0) or 0
exchange = st.session_state.get('exchange', 'N/A')
filename = st.session_state.get('filename', '')

# ========== SYMBOL DETECTION ==========
def detect_symbol(spot_price, filename=""):
    fn = filename.upper()
    if "BANKNIFTY" in fn: return "BANKNIFTY", 30
    elif "FINNIFTY" in fn: return "FINNIFTY", 60
    elif "MIDCPNIFTY" in fn: return "MIDCPNIFTY", 120
    elif "NIFTY" in fn: return "NIFTY", 65
    elif "SENSEX" in fn: return "SENSEX", 20
    elif "BANKEX" in fn: return "BANKEX", 30
    
    if 50000 <= spot_price <= 60000: return "BANKNIFTY", 30
    elif 20000 <= spot_price <= 30000: return "NIFTY", 65
    elif 70000 <= spot_price <= 90000: return "SENSEX", 20
    else: return "UNKNOWN", 0

symbol, lot_size = detect_symbol(spot, filename)

# ========== MODULE SCORES CALCULATION ==========
total_ce = int(df['CE_OI'].sum())
total_pe = int(df['PE_OI'].sum())
ce_change = int(df['CE_CHANGE_IN_OI'].sum()) if 'CE_CHANGE_IN_OI' in df.columns else 0
pe_change = int(df['PE_CHANGE_IN_OI'].sum()) if 'PE_CHANGE_IN_OI' in df.columns else 0
ce_vol = int(df['CE_VOLUME'].sum())
pe_vol = int(df['PE_VOLUME'].sum())
pcr = total_pe / total_ce if total_ce > 0 else 0

if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

support_oi = int(df[df['STRIKE'] < spot]['PE_OI'].max())
resistance_oi = int(df[df['STRIKE'] > spot]['CE_OI'].max())

# ========== MODULE 1: OI ANALYSIS (20%) ==========
oi_bull = 0
oi_bear = 0

if total_pe > total_ce * 1.2:
    oi_bull = 20
elif total_ce > total_pe * 1.2:
    oi_bear = 20
else:
    oi_bull = 10
    oi_bear = 10

# ========== MODULE 2: OI CHANGE ANALYSIS (25%) ==========
change_bull = 0
change_bear = 0

if pe_change > 0 and ce_change < 0:
    change_bull = 25
elif ce_change > 0 and pe_change < 0:
    change_bear = 25
elif pe_change > 0:
    change_bull = 15
    change_bear = 5
elif ce_change > 0:
    change_bear = 15
    change_bull = 5
else:
    change_bull = 10
    change_bear = 10

# ========== MODULE 3: PCR ANALYSIS (20%) ==========
pcr_bull = 0
pcr_bear = 0

if pcr > 1.5:
    pcr_bull = 20
elif pcr > 1.2:
    pcr_bull = 15
    pcr_bear = 5
elif pcr < 0.5:
    pcr_bear = 20
elif pcr < 0.7:
    pcr_bear = 15
    pcr_bull = 5
else:
    pcr_bull = 10
    pcr_bear = 10

# ========== MODULE 4: SUPPORT/RESISTANCE (20%) ==========
sr_bull = 0
sr_bear = 0

if support_oi > resistance_oi * 1.2:
    sr_bull = 20
elif resistance_oi > support_oi * 1.2:
    sr_bear = 20
else:
    sr_bull = 10
    sr_bear = 10

# ========== MODULE 5: VOLUME CONFIRMATION (15%) ==========
vol_bull = 0
vol_bear = 0

if pe_vol > ce_vol * 1.3:
    vol_bull = 15
elif ce_vol > pe_vol * 1.3:
    vol_bear = 15
else:
    vol_bull = 7
    vol_bear = 7

# ========== TOTAL SCORES ==========
total_bull = oi_bull + change_bull + pcr_bull + sr_bull + vol_bull
total_bear = oi_bear + change_bear + pcr_bear + sr_bear + vol_bear

total_bull = min(100, total_bull)
total_bear = min(100, total_bear)

confidence = max(total_bull, total_bear)

# ========== FINAL DECISION ==========
if total_bull >= 55 and total_bull > total_bear:
    final_signal = "BULLISH"
    action = "BUY CALL"
    strike_type = "CE"
elif total_bear >= 55 and total_bear > total_bull:
    final_signal = "BEARISH"
    action = "BUY PUT"
    strike_type = "PE"
else:
    final_signal = "NEUTRAL"
    action = "WAIT"
    strike_type = None

# ========== HEADER ==========
st.title("🚦 Final Recommendation")
st.write(f"**{exchange}** | **{symbol}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.write(f"**Lot Size:** {lot_size}")
st.divider()

# ========== FINAL SIGNAL DISPLAY ==========
if final_signal == "BULLISH":
    st.success(f"### 🟢 FINAL SIGNAL: {final_signal}")
    st.success(f"### 📈 ACTION: {action}")
elif final_signal == "BEARISH":
    st.error(f"### 🔴 FINAL SIGNAL: {final_signal}")
    st.error(f"### 📉 ACTION: {action}")
else:
    st.warning(f"### ⚪ FINAL SIGNAL: {final_signal}")
    st.warning(f"### ⏳ ACTION: {action}")

st.write(f"**Overall Bullish Score:** {total_bull}/100")
st.write(f"**Overall Bearish Score:** {total_bear}/100")
st.write(f"**Confidence:** {confidence}%")
st.progress(confidence / 100)
st.divider()

# ========== MODULE SCORES BREAKDOWN ==========
st.subheader("📊 Module Scores (Weighted)")

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 🟢 Bullish Modules")
    st.write(f"OI Analysis: {oi_bull}/20")
    st.write(f"OI Change: {change_bull}/25")
    st.write(f"PCR: {pcr_bull}/20")
    st.write(f"S/R: {sr_bull}/20")
    st.write(f"Volume: {vol_bull}/15")
    st.write(f"**Total: {total_bull}/100**")

with col2:
    st.markdown("### 🔴 Bearish Modules")
    st.write(f"OI Analysis: {oi_bear}/20")
    st.write(f"OI Change: {change_bear}/25")
    st.write(f"PCR: {pcr_bear}/20")
    st.write(f"S/R: {sr_bear}/20")
    st.write(f"Volume: {vol_bear}/15")
    st.write(f"**Total: {total_bear}/100**")

st.divider()

# ========== TRADE DETAILS ==========
if strike_type:
    st.subheader("💡 Recommended Trade")
    
    # Find best strike with premium ₹700-₹1000 per lot
    min_prem = 700 / lot_size if lot_size > 0 else 0
    max_prem = 1000 / lot_size if lot_size > 0 else 0
    
    if strike_type == "CE":
        candidates = df[(df['CE_LTP'] >= min_prem) & (df['CE_LTP'] <= max_prem) & (df['CE_VOLUME'] > 20)].nlargest(1, 'CE_VOLUME')
        ltp_col = 'CE_LTP'
    else:
        candidates = df[(df['PE_LTP'] >= min_prem) & (df['PE_LTP'] <= max_prem) & (df['PE_VOLUME'] > 20)].nlargest(1, 'PE_VOLUME')
        ltp_col = 'PE_LTP'
    
    if len(candidates) > 0:
        row = candidates.iloc[0]
        strike = float(row['STRIKE'])
        entry = float(row[ltp_col])
        t1 = entry * 1.25
        t2 = entry * 1.5
        sl = entry * 0.75
        per_lot = entry * lot_size
        
        st.markdown(f"### Strike: {strike:,.0f} {strike_type}")
        
        col1, col2, col3 = st.columns(3)
        col1.metric("Entry", f"₹{entry:.2f}")
        col2.metric("Target 1", f"₹{t1:.2f}")
        col3.metric("Target 2", f"₹{t2:.2f}")
        
        col4, col5, col6 = st.columns(3)
        col4.metric("Stop Loss", f"₹{sl:.2f}")
        col5.metric("Per Lot", f"₹{per_lot:,.0f}")
        col6.metric("Lot Size", str(lot_size))
    else:
        st.warning("₹700-₹1000 per lot range mein koi trade nahi mila")

st.divider()

# ========== KEY METRICS ==========
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("PCR", f"{pcr:.2f}")
col2.metric("CE OI", f"{total_ce:,}")
col3.metric("PE OI", f"{total_pe:,}")
col4.metric("Total OI", f"{total_ce+total_pe:,}")

st.divider()
st.warning("⚠️ Educational purposes only. Trading me risk hota hai.")