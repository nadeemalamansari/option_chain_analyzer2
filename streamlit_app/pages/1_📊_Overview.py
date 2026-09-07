"""
📊 Market Overview - Complete 9-Module Analysis
OI + Price+OI + PCR + S/R + OI Shift + Volume + IV + Max Pain + ATM
"""

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Overview", page_icon="📊", layout="wide")

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

# ========== ALL CALCULATIONS ==========
total_ce = int(df['CE_OI'].sum())
total_pe = int(df['PE_OI'].sum())
total_oi = total_ce + total_pe
ce_change = int(df['CE_CHANGE_IN_OI'].sum()) if 'CE_CHANGE_IN_OI' in df.columns else 0
pe_change = int(df['PE_CHANGE_IN_OI'].sum()) if 'PE_CHANGE_IN_OI' in df.columns else 0
ce_vol = int(df['CE_VOLUME'].sum())
pe_vol = int(df['PE_VOLUME'].sum())
total_vol = ce_vol + pe_vol
pcr = total_pe / total_ce if total_ce > 0 else 0
pcr_vol = pe_vol / ce_vol if ce_vol > 0 else 0
pcr_change = pe_change / ce_change if ce_change != 0 else 0

if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

atm_data = df[df['STRIKE'] == atm]
atm_ce_oi = int(atm_data.iloc[0]['CE_OI']) if len(atm_data) > 0 else 0
atm_pe_oi = int(atm_data.iloc[0]['PE_OI']) if len(atm_data) > 0 else 0
atm_ce_ltp = float(atm_data.iloc[0]['CE_LTP']) if len(atm_data) > 0 else 0
atm_pe_ltp = float(atm_data.iloc[0]['PE_LTP']) if len(atm_data) > 0 else 0
atm_ce_iv = float(atm_data.iloc[0]['CE_IV']) if len(atm_data) > 0 else 0
atm_pe_iv = float(atm_data.iloc[0]['PE_IV']) if len(atm_data) > 0 else 0
iv_skew = atm_pe_iv - atm_ce_iv
avg_iv = (atm_ce_iv + atm_pe_iv) / 2
expected_move = atm_ce_ltp + atm_pe_ltp

support = float(df[df['STRIKE'] < spot].nlargest(1, 'PE_OI')['STRIKE'].iloc[0]) if len(df[df['STRIKE'] < spot]) > 0 else spot - 200
resistance = float(df[df['STRIKE'] > spot].nlargest(1, 'CE_OI')['STRIKE'].iloc[0]) if len(df[df['STRIKE'] > spot]) > 0 else spot + 200
support_oi = int(df[df['STRIKE'] < spot]['PE_OI'].max())
resistance_oi = int(df[df['STRIKE'] > spot]['CE_OI'].max())

near_atm = df[(df['STRIKE'] >= atm - 200) & (df['STRIKE'] <= atm + 200)]
pe_concentration = float(near_atm['PE_OI'].sum() / total_pe * 100) if total_pe > 0 else 0
ce_concentration = float(near_atm['CE_OI'].sum() / total_ce * 100) if total_ce > 0 else 0
oi_imbalance = ((total_pe - total_ce) / total_oi * 100) if total_oi > 0 else 0
vol_imbalance = ((pe_vol - ce_vol) / total_vol * 100) if total_vol > 0 else 0

def calc_max_pain(df):
    strikes = df['STRIKE'].values
    pains = []
    for target in strikes:
        pain = 0
        for _, row in df.iterrows():
            if target > row['STRIKE']:
                pain += (target - row['STRIKE']) * row['CE_OI']
            if target < row['STRIKE']:
                pain += (row['STRIKE'] - target) * row['PE_OI']
        pains.append(pain)
    return float(strikes[np.argmin(pains)])

max_pain = calc_max_pain(df)
liquidity_score = min(100, int((total_vol / total_oi * 100) if total_oi > 0 else 0))

# ========== 9 MODULE SCORING ==========
all_factors = []
bull_score = 10
bear_score = 10

# MODULE 1: OI STRUCTURE (20 points)
if total_pe > total_ce * 1.2:
    bull_score += 20
    all_factors.append(("1. OI Structure", "BULLISH", 20, f"PE {total_pe:,} > CE {total_ce:,}"))
elif total_ce > total_pe * 1.2:
    bear_score += 20
    all_factors.append(("1. OI Structure", "BEARISH", 20, f"CE {total_ce:,} > PE {total_pe:,}"))
else:
    bull_score += 10
    bear_score += 10
    all_factors.append(("1. OI Structure", "NEUTRAL", 10, "Balanced"))

# MODULE 2: PRICE + OI (20 points)
if atm_ce_ltp > 0 and ce_change > 0:
    bull_score += 8
elif ce_change > 0:
    bear_score += 8

if atm_pe_ltp < 0 and pe_change > 0:
    bull_score += 7
elif pe_change > 0:
    bear_score += 7

if pe_change > 0 and ce_change < 0:
    bull_score += 5
elif ce_change > 0 and pe_change < 0:
    bear_score += 5

all_factors.append(("2. Price+OI", "MIXED", 20, f"CE LTP ₹{atm_ce_ltp:.2f}, PE LTP ₹{atm_pe_ltp:.2f}"))

# MODULE 3: PCR (10 points)
if pcr > 1.3:
    bull_score += 10
    all_factors.append(("3. PCR", "STRONG BULLISH", 10, f"{pcr:.2f}"))
elif pcr > 1.1:
    bull_score += 8
    all_factors.append(("3. PCR", "BULLISH", 8, f"{pcr:.2f}"))
elif pcr < 0.7:
    bear_score += 10
    all_factors.append(("3. PCR", "STRONG BEARISH", 10, f"{pcr:.2f}"))
elif pcr < 0.9:
    bear_score += 8
    all_factors.append(("3. PCR", "BEARISH", 8, f"{pcr:.2f}"))
else:
    all_factors.append(("3. PCR", "NEUTRAL", 5, f"{pcr:.2f}"))

# MODULE 4: SUPPORT/RESISTANCE (15 points)
if support_oi > resistance_oi * 1.2:
    bull_score += 15
    all_factors.append(("4. Support/Resistance", "BULLISH", 15, f"S {support_oi:,} > R {resistance_oi:,}"))
elif resistance_oi > support_oi * 1.2:
    bear_score += 15
    all_factors.append(("4. Support/Resistance", "BEARISH", 15, f"R {resistance_oi:,} > S {support_oi:,}"))
else:
    bull_score += 7
    bear_score += 7
    all_factors.append(("4. Support/Resistance", "NEUTRAL", 7, "Balanced"))

# MODULE 5: OI SHIFT (10 points)
if pe_change > 0 and ce_change < 0:
    bull_score += 10
    all_factors.append(("5. OI Shift", "BULLISH", 10, "PE buildup + CE unwinding"))
elif ce_change > 0 and pe_change < 0:
    bear_score += 10
    all_factors.append(("5. OI Shift", "BEARISH", 10, "CE buildup + PE unwinding"))
else:
    all_factors.append(("5. OI Shift", "NEUTRAL", 5, "No clear shift"))

# MODULE 6: VOLUME (10 points)
if pe_vol > ce_vol * 1.2:
    bull_score += 10
    all_factors.append(("6. Volume", "BULLISH", 10, f"PE {pe_vol:,} > CE"))
elif ce_vol > pe_vol * 1.2:
    bear_score += 10
    all_factors.append(("6. Volume", "BEARISH", 10, f"CE {ce_vol:,} > PE"))
else:
    all_factors.append(("6. Volume", "NEUTRAL", 5, "Balanced"))

# MODULE 7: IV ANALYSIS (5 points)
if avg_iv > 40:
    all_factors.append(("7. IV", "HIGH", 3, f"{avg_iv:.1f}% - Expensive"))
elif avg_iv > 20:
    all_factors.append(("7. IV", "MODERATE", 5, f"{avg_iv:.1f}%"))
else:
    all_factors.append(("7. IV", "LOW", 3, f"{avg_iv:.1f}% - Cheap"))

# MODULE 8: IV SKEW (5 points)
if iv_skew > 2:
    bull_score += 5
    all_factors.append(("8. IV Skew", "BULLISH", 5, f"PE IV > CE IV by {iv_skew:.1f}"))
elif iv_skew < -2:
    bear_score += 5
    all_factors.append(("8. IV Skew", "BEARISH", 5, f"CE IV > PE IV by {abs(iv_skew):.1f}"))
else:
    all_factors.append(("8. IV Skew", "NEUTRAL", 3, "Balanced"))

# MODULE 9: MAX PAIN + ATM (5 points)
if max_pain > spot:
    bull_score += 3
    all_factors.append(("9. Max Pain", "BULLISH", 3, f"₹{max_pain:,.0f} above"))
elif max_pain < spot:
    bear_score += 3
    all_factors.append(("9. Max Pain", "BEARISH", 3, f"₹{max_pain:,.0f} below"))

if atm_pe_oi > atm_ce_oi * 1.2:
    bull_score += 2
    all_factors.append(("9. ATM Structure", "BULLISH", 2, f"PE {atm_pe_oi:,} > CE {atm_ce_oi:,}"))
elif atm_ce_oi > atm_pe_oi * 1.2:
    bear_score += 2
    all_factors.append(("9. ATM Structure", "BEARISH", 2, f"CE {atm_ce_oi:,} > PE {atm_pe_oi:,}"))

# Totals
bull_score = min(100, bull_score)
bear_score = min(100, bear_score)
confidence = max(bull_score, bear_score)

# ========== FINAL DECISION ==========
if bull_score >= 70 and bear_score <= 30:
    decision = "STRONG BULLISH"
    action = "BUY CALL"
elif bull_score >= 55:
    decision = "BULLISH"
    action = "BUY CALL"
elif bear_score >= 70 and bull_score <= 30:
    decision = "STRONG BEARISH"
    action = "BUY PUT"
elif bear_score >= 55:
    decision = "BEARISH"
    action = "BUY PUT"
else:
    decision = "NEUTRAL"
    action = "WAIT"

# ========== HEADER ==========
st.title("📊 Market Overview - 9 Module Analysis")
st.write(f"**{exchange}** | **{symbol}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.divider()

# ========== FINAL DECISION ==========
if "BULLISH" in decision:
    st.success(f"### 🟢 FINAL: {decision}")
    st.success(f"### Action: {action}")
elif "BEARISH" in decision:
    st.error(f"### 🔴 FINAL: {decision}")
    st.error(f"### Action: {action}")
else:
    st.warning(f"### ⚪ FINAL: {decision}")
    st.warning(f"### Action: {action}")

st.write(f"**Bull Score:** {bull_score}/100 | **Bear Score:** {bear_score}/100")
st.write(f"**Confidence:** {confidence}%")
st.progress(confidence / 100)
st.divider()

# ========== ALL 9 MODULES ==========
st.subheader("📊 9 Module Analysis")

for name, signal, score, detail in all_factors:
    if "BULLISH" in signal:
        icon = "🟢"
    elif "BEARISH" in signal:
        icon = "🔴"
    else:
        icon = "🟡"
    st.write(f"{icon} **{name}:** {signal} ({score}) - {detail}")

st.divider()

# ========== KEY METRICS ==========
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("PCR", f"{pcr:.2f}")
col2.metric("Max Pain", f"₹{max_pain:,.0f}")
col3.metric("Exp Move", f"±₹{expected_move:,.0f}")
col4.metric("IV Skew", f"{iv_skew:.1f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Support", f"₹{support:,.0f}")
col6.metric("Resistance", f"₹{resistance:,.0f}")
col7.metric("Liquidity", f"{liquidity_score}/100")
col8.metric("Avg IV", f"{avg_iv:.1f}%")

st.divider()

# ========== TRADE CONDITIONS ==========
st.subheader("📋 Trade Conditions")
st.write("✅ **Active:** BULLISH/BEARISH + Liquidity > 20")
st.write("🔄 **Change:** T2 hit, Market flip, SL hit")
st.write("📊 **Manage:** T1=50%, T2=25%, T3=25%")

st.divider()
st.warning("⚠️ Educational purposes only.")