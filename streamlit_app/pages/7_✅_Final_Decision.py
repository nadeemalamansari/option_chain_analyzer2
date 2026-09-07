"""
🎯 Final Decision - Complete 20-Step Analysis
Full Option Chain Decision Engine
"""

import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="Final Decision", page_icon="🎯", layout="wide")

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

# ========== STEP 1: DATA VALIDATION ==========
data_quality = 100
validation_issues = []

if df['CE_OI'].isnull().sum() > 0:
    data_quality -= 10
    validation_issues.append("CE OI missing values")
if df['PE_OI'].isnull().sum() > 0:
    data_quality -= 10
    validation_issues.append("PE OI missing values")
if (df['CE_OI'] < 0).sum() > 0:
    data_quality -= 10
    validation_issues.append("Negative CE OI")
if (df['PE_OI'] < 0).sum() > 0:
    data_quality -= 10
    validation_issues.append("Negative PE OI")
if len(df[df['STRIKE'] == 0]) > 0:
    data_quality -= 10
    validation_issues.append("Zero strike prices")

data_quality = max(50, data_quality)
valid = data_quality > 70

# ========== STEP 2: ATM DETECTION ==========
if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

# ========== CALCULATIONS ==========
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

# ========== SCORING ==========
bull_score = 10
bear_score = 10
analysis_steps = []

# STEP 3-4: CE/PE OI Analysis (15 points)
if total_pe > total_ce * 1.2:
    bull_score += 15
    analysis_steps.append(("CE/PE OI Analysis", "BULLISH", 15, f"PE {total_pe:,} > CE {total_ce:,}"))
elif total_ce > total_pe * 1.2:
    bear_score += 15
    analysis_steps.append(("CE/PE OI Analysis", "BEARISH", 15, f"CE {total_ce:,} > PE {total_pe:,}"))
else:
    bull_score += 7
    bear_score += 7
    analysis_steps.append(("CE/PE OI Analysis", "NEUTRAL", 7, "Balanced"))

# STEP 5: Price + OI (15 points)
if atm_ce_ltp > 0 and ce_change > 0:
    bull_score += 8
elif ce_change > 0:
    bear_score += 8

if atm_pe_ltp < 0 and pe_change > 0:
    bull_score += 7
elif pe_change > 0:
    bear_score += 7

analysis_steps.append(("Price+OI", "MIXED", 15, f"CE ₹{atm_ce_ltp:.2f}, PE ₹{atm_pe_ltp:.2f}"))

# STEP 6: PCR (10 points)
if pcr > 1.3:
    bull_score += 10
    analysis_steps.append(("PCR", "BULLISH", 10, f"{pcr:.2f}"))
elif pcr < 0.7:
    bear_score += 10
    analysis_steps.append(("PCR", "BEARISH", 10, f"{pcr:.2f}"))
else:
    analysis_steps.append(("PCR", "NEUTRAL", 5, f"{pcr:.2f}"))

# STEP 7-8: Support/Resistance (15 points)
if support_oi > resistance_oi * 1.2:
    bull_score += 15
    analysis_steps.append(("Support/Resistance", "BULLISH", 15, f"S {support_oi:,} > R {resistance_oi:,}"))
elif resistance_oi > support_oi * 1.2:
    bear_score += 15
    analysis_steps.append(("Support/Resistance", "BEARISH", 15, f"R {resistance_oi:,} > S {support_oi:,}"))
else:
    bull_score += 7
    bear_score += 7
    analysis_steps.append(("Support/Resistance", "NEUTRAL", 7, "Balanced"))

# STEP 9-10: OI Shift/Migration (10 points)
if pe_change > 0 and ce_change < 0:
    bull_score += 10
    analysis_steps.append(("OI Shift/Migration", "BULLISH", 10, "PE buildup + CE unwinding"))
elif ce_change > 0 and pe_change < 0:
    bear_score += 10
    analysis_steps.append(("OI Shift/Migration", "BEARISH", 10, "CE buildup + PE unwinding"))
else:
    analysis_steps.append(("OI Shift/Migration", "NEUTRAL", 5, "No shift"))

# STEP 11: Volume (10 points)
if pe_vol > ce_vol * 1.2:
    bull_score += 10
    analysis_steps.append(("Volume", "BULLISH", 10, f"PE {pe_vol:,} > CE"))
elif ce_vol > pe_vol * 1.2:
    bear_score += 10
    analysis_steps.append(("Volume", "BEARISH", 10, f"CE {ce_vol:,} > PE"))
else:
    analysis_steps.append(("Volume", "NEUTRAL", 5, "Balanced"))

# STEP 12: IV (5 points)
if iv_skew > 2:
    bull_score += 5
    analysis_steps.append(("IV Skew", "BULLISH", 5, f"{iv_skew:.1f}"))
elif iv_skew < -2:
    bear_score += 5
    analysis_steps.append(("IV Skew", "BEARISH", 5, f"{iv_skew:.1f}"))

# STEP 13: ATM Structure (5 points)
if atm_pe_oi > atm_ce_oi * 1.2:
    bull_score += 5
    analysis_steps.append(("ATM Structure", "BULLISH", 5, f"PE {atm_pe_oi:,} > CE {atm_ce_oi:,}"))
elif atm_ce_oi > atm_pe_oi * 1.2:
    bear_score += 5
    analysis_steps.append(("ATM Structure", "BEARISH", 5, f"CE {atm_ce_oi:,} > PE {atm_pe_oi:,}"))

# STEP 14: Max Pain (5 points)
if max_pain > spot:
    bull_score += 3
    analysis_steps.append(("Max Pain", "BULLISH", 3, f"₹{max_pain:,.0f} above"))
elif max_pain < spot:
    bear_score += 3
    analysis_steps.append(("Max Pain", "BEARISH", 3, f"₹{max_pain:,.0f} below"))

bull_score = min(100, bull_score)
bear_score = min(100, bear_score)
confidence = max(bull_score, bear_score)

# STEP 17: Factor Agreement
bull_factors = sum(1 for _, sig, _, _ in analysis_steps if "BULLISH" in sig)
bear_factors = sum(1 for _, sig, _, _ in analysis_steps if "BEARISH" in sig)
total_factors = len(analysis_steps)
agreement = max(bull_factors, bear_factors) / total_factors * 100 if total_factors > 0 else 50

# STEP 18: Confidence Adjustment
final_confidence = min(100, (confidence * 0.7 + agreement * 0.3))
confidence_level = "HIGH" if final_confidence >= 70 else "MEDIUM" if final_confidence >= 50 else "LOW"

# STEP 19: Market Direction
if bull_score >= 70 and bear_score <= 30:
    direction = "STRONG BULLISH"
elif bull_score >= 55:
    direction = "BULLISH"
elif bear_score >= 70 and bull_score <= 30:
    direction = "STRONG BEARISH"
elif bear_score >= 55:
    direction = "BEARISH"
else:
    direction = "NEUTRAL"

# STEP 20: Trade Action
if "BULLISH" in direction:
    action = "BUY CALL"
    strike_type = "CE"
elif "BEARISH" in direction:
    action = "BUY PUT"
    strike_type = "PE"
else:
    action = "NO TRADE"
    strike_type = None

# ========== HEADER ==========
st.title("🎯 Final Decision - 20-Step Analysis")
st.write(f"**{exchange}** | **{symbol}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.divider()

# ========== STEP 1: DATA VALIDATION ==========
if valid:
    st.success(f"✅ **Data Quality:** {data_quality}% - Valid")
else:
    st.warning(f"⚠️ **Data Quality:** {data_quality}% - Issues found")
    for issue in validation_issues:
        st.write(f"• {issue}")

st.divider()

# ========== FINAL DECISION ==========
if "BULLISH" in direction:
    st.success(f"# 🟢 {direction}")
    st.success(f"## Action: {action}")
elif "BEARISH" in direction:
    st.error(f"# 🔴 {direction}")
    st.error(f"## Action: {action}")
else:
    st.warning(f"# ⚪ {direction}")
    st.warning(f"## Action: {action}")

st.write(f"**Bull Score:** {bull_score}/100 | **Bear Score:** {bear_score}/100")
st.write(f"**Factor Agreement:** {agreement:.0f}% ({max(bull_factors, bear_factors)}/{total_factors} factors)")
st.write(f"**Confidence:** {final_confidence:.0f}% ({confidence_level})")
st.progress(final_confidence / 100)
st.divider()

# ========== ALL ANALYSIS STEPS ==========
st.subheader("📊 All Analysis Steps")

for name, signal, score, detail in analysis_steps:
    if "BULLISH" in signal:
        icon = "🟢"
    elif "BEARISH" in signal:
        icon = "🔴"
    else:
        icon = "🟡"
    st.write(f"{icon} **{name}:** {signal} ({score}) - {detail}")

st.divider()

# ========== TRADE RECOMMENDATION ==========
if strike_type and lot_size > 0 and liquidity_score > 20:
    st.subheader("💡 Trade Recommendation")
    
    min_prem = 700 / lot_size
    max_prem = 1000 / lot_size
    
    if strike_type == "CE":
        candidates = df[(df['CE_LTP'] >= min_prem) & (df['CE_LTP'] <= max_prem) & (df['CE_VOLUME'] > 20)].nlargest(3, 'CE_VOLUME')
        ltp_col = 'CE_LTP'
    else:
        candidates = df[(df['PE_LTP'] >= min_prem) & (df['PE_LTP'] <= max_prem) & (df['PE_VOLUME'] > 20)].nlargest(3, 'PE_VOLUME')
        ltp_col = 'PE_LTP'
    
    if len(candidates) > 0:
        for i, (_, row) in enumerate(candidates.iterrows(), 1):
            strike = float(row['STRIKE'])
            entry = float(row[ltp_col])
            per_lot = entry * lot_size
            
            st.markdown("---")
            st.markdown(f"### Trade #{i}: BUY {strike:,.0f} {strike_type}")
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Entry", f"₹{entry:.2f}")
            col2.metric("Target 2", f"₹{entry*1.5:.2f}")
            col3.metric("Per Lot", f"₹{per_lot:,.0f}")
    else:
        st.warning("₹700-₹1000 range mein koi trade nahi")
elif liquidity_score <= 20:
    st.warning("⚠️ Liquidity low - trade avoid")

st.divider()

# ========== KEY METRICS ==========
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("PCR", f"{pcr:.2f}")
col2.metric("Max Pain", f"₹{max_pain:,.0f}")
col3.metric("Exp Move", f"±₹{expected_move:,.0f}")
col4.metric("Liquidity", f"{liquidity_score}/100")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Support", f"₹{support:,.0f}")
col6.metric("Resistance", f"₹{resistance:,.0f}")
col7.metric("IV Skew", f"{iv_skew:.1f}")
col8.metric("Avg IV", f"{avg_iv:.1f}%")

st.divider()

# ========== TRADE CONDITIONS ==========
st.subheader("📋 Trade Conditions")
st.write("✅ **Active:** Valid data + Direction + Liquidity > 20")
st.write("🔄 **Change:** T2 hit, Market flip, SL hit, New data")
st.write("📊 **Manage:** T1=50%, T2=25%, T3=25% | SL=Exit")
st.write(f"🎯 **Confidence Level:** {confidence_level}")

st.divider()
st.warning("⚠️ Educational purposes only.")