"""
📈 OI Analysis - OI Positioning Complete
Pure Streamlit Components
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="OI Analysis", page_icon="📈", layout="wide")

# Check data
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded!")
    st.info("👉 Go to main page → Upload CSV → Analyze Data")
    st.stop()

df = st.session_state.data.copy()
spot = st.session_state.get('spot_price', 0) or 0
exchange = st.session_state.get('exchange', 'N/A')

# ========== CALCULATIONS ==========
total_ce = int(df['CE_OI'].sum())
total_pe = int(df['PE_OI'].sum())
total_oi = total_ce + total_pe
pcr = total_pe / total_ce if total_ce > 0 else 0

ce_change = int(df['CE_CHANGE_IN_OI'].sum()) if 'CE_CHANGE_IN_OI' in df.columns else 0
pe_change = int(df['PE_CHANGE_IN_OI'].sum()) if 'PE_CHANGE_IN_OI' in df.columns else 0

if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

# Highest OI strikes
highest_ce_strike = float(df.loc[df['CE_OI'].idxmax(), 'STRIKE'])
highest_pe_strike = float(df.loc[df['PE_OI'].idxmax(), 'STRIKE'])
highest_ce_oi = int(df['CE_OI'].max())
highest_pe_oi = int(df['PE_OI'].max())

# ATM OI
atm_data = df[df['STRIKE'] == atm]
atm_ce_oi = int(atm_data.iloc[0]['CE_OI']) if len(atm_data) > 0 else 0
atm_pe_oi = int(atm_data.iloc[0]['PE_OI']) if len(atm_data) > 0 else 0

# OI Concentration
near_atm = df[(df['STRIKE'] >= atm - 200) & (df['STRIKE'] <= atm + 200)]
ce_concentration = float(near_atm['CE_OI'].sum() / total_ce * 100) if total_ce > 0 else 0
pe_concentration = float(near_atm['PE_OI'].sum() / total_pe * 100) if total_pe > 0 else 0

# OI Imbalance
oi_imbalance = ((total_pe - total_ce) / total_oi * 100) if total_oi > 0 else 0

# ========== OI BIAS SCORING ==========
oi_bias_score = 0
factors = []

# 1. Total OI Comparison (30 points)
if total_pe > total_ce * 1.3:
    oi_bias_score += 30
    factors.append(("Total OI", "BULLISH", 30, f"PE {total_pe:,} >> CE {total_ce:,}"))
elif total_pe > total_ce * 1.1:
    oi_bias_score += 20
    factors.append(("Total OI", "BULLISH", 20, f"PE {total_pe:,} > CE {total_ce:,}"))
elif total_ce > total_pe * 1.3:
    oi_bias_score -= 30
    factors.append(("Total OI", "BEARISH", -30, f"CE {total_ce:,} >> PE {total_pe:,}"))
elif total_ce > total_pe * 1.1:
    oi_bias_score -= 20
    factors.append(("Total OI", "BEARISH", -20, f"CE {total_ce:,} > PE {total_pe:,}"))
else:
    factors.append(("Total OI", "NEUTRAL", 0, "Balanced"))

# 2. OI PCR (25 points)
if pcr > 1.5:
    oi_bias_score += 25
    factors.append(("OI PCR", "STRONG BULLISH", 25, f"{pcr:.2f}"))
elif pcr > 1.2:
    oi_bias_score += 20
    factors.append(("OI PCR", "BULLISH", 20, f"{pcr:.2f}"))
elif pcr < 0.5:
    oi_bias_score -= 25
    factors.append(("OI PCR", "STRONG BEARISH", -25, f"{pcr:.2f}"))
elif pcr < 0.7:
    oi_bias_score -= 20
    factors.append(("OI PCR", "BEARISH", -20, f"{pcr:.2f}"))
else:
    factors.append(("OI PCR", "NEUTRAL", 0, f"{pcr:.2f}"))

# 3. Highest OI Strike Position (20 points)
if highest_pe_strike < spot and highest_ce_strike > spot:
    oi_bias_score += 20
    factors.append(("OI Strike Position", "BULLISH", 20, f"PE S: {highest_pe_strike:,.0f}, CE R: {highest_ce_strike:,.0f}"))
elif highest_ce_strike < spot:
    oi_bias_score -= 20
    factors.append(("OI Strike Position", "BEARISH", -20, f"CE below spot: {highest_ce_strike:,.0f}"))
else:
    factors.append(("OI Strike Position", "NEUTRAL", 0, "Mixed"))

# 4. ATM OI (15 points)
if atm_pe_oi > atm_ce_oi * 1.2:
    oi_bias_score += 15
    factors.append(("ATM OI", "BULLISH", 15, f"PE {atm_pe_oi:,} > CE {atm_ce_oi:,}"))
elif atm_ce_oi > atm_pe_oi * 1.2:
    oi_bias_score -= 15
    factors.append(("ATM OI", "BEARISH", -15, f"CE {atm_ce_oi:,} > PE {atm_pe_oi:,}"))
else:
    factors.append(("ATM OI", "NEUTRAL", 0, "Balanced"))

# 5. OI Concentration (10 points)
if pe_concentration > ce_concentration:
    oi_bias_score += 10
    factors.append(("OI Concentration", "BULLISH", 10, f"PE {pe_concentration:.0f}% > CE {ce_concentration:.0f}%"))
else:
    oi_bias_score -= 10
    factors.append(("OI Concentration", "BEARISH", -10, f"CE {ce_concentration:.0f}% > PE {pe_concentration:.0f}%"))

# Normalize score to -100 to +100
oi_bias_score = max(-100, min(100, oi_bias_score))

# ========== FINAL OI BIAS ==========
if oi_bias_score > 20:
    oi_bias = "BULLISH"
elif oi_bias_score < -20:
    oi_bias = "BEARISH"
else:
    oi_bias = "NEUTRAL"

# ========== HEADER ==========
st.title("📈 OI Analysis - OI Positioning")
st.write(f"**{exchange}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.divider()

# ========== OI BIAS DECISION ==========
if oi_bias == "BULLISH":
    st.success(f"### 🟢 OI BIAS: {oi_bias}")
elif oi_bias == "BEARISH":
    st.error(f"### 🔴 OI BIAS: {oi_bias}")
else:
    st.warning(f"### 🟡 OI BIAS: {oi_bias}")

st.write(f"**OI Bias Score:** {oi_bias_score:+d}/100")
st.progress(abs(oi_bias_score) / 100)
st.divider()

# ========== FACTORS ==========
st.subheader("🔍 OI Positioning Factors")

for name, signal, score, detail in factors:
    if signal == "BULLISH" or signal == "STRONG BULLISH":
        icon = "🟢"
    elif signal == "BEARISH" or signal == "STRONG BEARISH":
        icon = "🔴"
    else:
        icon = "🟡"
    
    score_display = f"+{score}" if score > 0 else str(score)
    st.write(f"{icon} **{name}:** {signal} ({score_display}) - {detail}")

st.divider()

# ========== OI METRICS ==========
st.subheader("📊 OI Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total CE OI", f"{total_ce:,}")
col2.metric("Total PE OI", f"{total_pe:,}")
col3.metric("Total OI", f"{total_oi:,}")
col4.metric("OI PCR", f"{pcr:.2f}")

col5, col6, col7, col8 = st.columns(4)
col5.metric("Highest CE OI", f"₹{highest_ce_strike:,.0f}")
col6.metric("Highest PE OI", f"₹{highest_pe_strike:,.0f}")
col7.metric("ATM CE OI", f"{atm_ce_oi:,}")
col8.metric("ATM PE OI", f"{atm_pe_oi:,}")

st.divider()

# ========== CONCENTRATION ==========
st.subheader("📊 OI Concentration")

col1, col2, col3 = st.columns(3)
col1.metric("CE Concentration", f"{ce_concentration:.1f}%")
col2.metric("PE Concentration", f"{pe_concentration:.1f}%")
col3.metric("OI Imbalance", f"{oi_imbalance:+.1f}%")

st.divider()

# ========== OI CHANGE ==========
st.subheader("📈 OI Change")

col1, col2 = st.columns(2)
col1.metric("CE Change", f"{ce_change:,.0f}")
col2.metric("PE Change", f"{pe_change:,.0f}")

st.divider()

# ========== CHART ==========
st.subheader("📊 OI Distribution")

try:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_OI'], name='CE OI', marker_color='#27ae60'))
    fig.add_trace(go.Bar(x=df['STRIKE'], y=-df['PE_OI'], name='PE OI', marker_color='#e74c3c'))
    fig.add_vline(x=spot, line_dash="dash", line_color="black", annotation_text="SPOT")
    fig.add_vline(x=highest_ce_strike, line_dash="dot", line_color="#e74c3c", annotation_text="CE MAX")
    fig.add_vline(x=highest_pe_strike, line_dash="dot", line_color="#27ae60", annotation_text="PE MAX")
    fig.update_layout(height=400, barmode='relative', template='plotly_white')
    st.plotly_chart(fig, width='stretch')
except:
    pass

st.divider()
st.warning("⚠️ Educational purposes only.")