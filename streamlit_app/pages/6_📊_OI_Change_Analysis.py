"""
📊 OI Change Analysis - Fresh Positioning
Pure Streamlit Components
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="OI Change Analysis", page_icon="📊", layout="wide")

# Check data
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded!")
    st.info("👉 Go to main page → Upload CSV → Analyze Data")
    st.stop()

df = st.session_state.data.copy()
spot = st.session_state.get('spot_price', 0) or 0
exchange = st.session_state.get('exchange', 'N/A')

# ========== CALCULATIONS ==========
ce_change = int(df['CE_CHANGE_IN_OI'].sum()) if 'CE_CHANGE_IN_OI' in df.columns else 0
pe_change = int(df['PE_CHANGE_IN_OI'].sum()) if 'PE_CHANGE_IN_OI' in df.columns else 0
total_change = abs(ce_change) + abs(pe_change)
pcr_change = pe_change / ce_change if ce_change != 0 else 0

if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

# Highest ΔOI strikes
highest_ce_change_strike = float(df.loc[df['CE_CHANGE_IN_OI'].idxmax(), 'STRIKE'])
highest_pe_change_strike = float(df.loc[df['PE_CHANGE_IN_OI'].idxmax(), 'STRIKE'])
highest_ce_change_val = int(df['CE_CHANGE_IN_OI'].max())
highest_pe_change_val = int(df['PE_CHANGE_IN_OI'].max())

# Writing/Unwinding
ce_writing = int(df[df['CE_CHANGE_IN_OI'] > 0]['CE_CHANGE_IN_OI'].sum())
ce_unwinding = abs(int(df[df['CE_CHANGE_IN_OI'] < 0]['CE_CHANGE_IN_OI'].sum()))
pe_writing = int(df[df['PE_CHANGE_IN_OI'] > 0]['PE_CHANGE_IN_OI'].sum())
pe_unwinding = abs(int(df[df['PE_CHANGE_IN_OI'] < 0]['PE_CHANGE_IN_OI'].sum()))

# ATM ΔOI
atm_data = df[df['STRIKE'] == atm]
atm_ce_change = int(atm_data.iloc[0].get('CE_CHANGE_IN_OI', 0)) if len(atm_data) > 0 else 0
atm_pe_change = int(atm_data.iloc[0].get('PE_CHANGE_IN_OI', 0)) if len(atm_data) > 0 else 0

# ========== SCORING ==========
oi_change_score = 0
factors = []

# 1. Total Change OI (30 points)
if pe_change > 0 and ce_change < 0:
    oi_change_score += 30
    factors.append(("Total ΔOI", "BULLISH", 30, f"PE +{pe_change:,}, CE {ce_change:,}"))
elif pe_change > 0 and ce_change > 0:
    if pe_change > ce_change:
        oi_change_score += 15
        factors.append(("Total ΔOI", "BULLISH", 15, f"PE +{pe_change:,} > CE +{ce_change:,}"))
    else:
        oi_change_score -= 15
        factors.append(("Total ΔOI", "BEARISH", -15, f"CE +{ce_change:,} > PE +{pe_change:,}"))
elif ce_change > 0 and pe_change < 0:
    oi_change_score -= 30
    factors.append(("Total ΔOI", "BEARISH", -30, f"CE +{ce_change:,}, PE {pe_change:,}"))
else:
    factors.append(("Total ΔOI", "NEUTRAL", 0, "No significant change"))

# 2. Change-OI PCR (25 points)
if pcr_change > 1.5:
    oi_change_score += 25
    factors.append(("Change-OI PCR", "STRONG BULLISH", 25, f"{pcr_change:.2f}"))
elif pcr_change > 1.2:
    oi_change_score += 20
    factors.append(("Change-OI PCR", "BULLISH", 20, f"{pcr_change:.2f}"))
elif pcr_change < 0.5:
    oi_change_score -= 25
    factors.append(("Change-OI PCR", "STRONG BEARISH", -25, f"{pcr_change:.2f}"))
elif pcr_change < 0.7:
    oi_change_score -= 20
    factors.append(("Change-OI PCR", "BEARISH", -20, f"{pcr_change:.2f}"))
else:
    factors.append(("Change-OI PCR", "NEUTRAL", 0, f"{pcr_change:.2f}"))

# 3. Writing Indication (20 points)
if pe_writing > ce_writing * 1.3:
    oi_change_score += 20
    factors.append(("Writing", "BULLISH", 20, f"Put writing {pe_writing:,} > Call writing {ce_writing:,}"))
elif ce_writing > pe_writing * 1.3:
    oi_change_score -= 20
    factors.append(("Writing", "BEARISH", -20, f"Call writing {ce_writing:,} > Put writing {pe_writing:,}"))
else:
    factors.append(("Writing", "NEUTRAL", 0, "Balanced"))

# 4. Unwinding Indication (15 points)
if ce_unwinding > pe_unwinding * 1.3:
    oi_change_score += 15
    factors.append(("Unwinding", "BULLISH", 15, f"Call unwinding {ce_unwinding:,} > Put unwinding {pe_unwinding:,}"))
elif pe_unwinding > ce_unwinding * 1.3:
    oi_change_score -= 15
    factors.append(("Unwinding", "BEARISH", -15, f"Put unwinding {pe_unwinding:,} > Call unwinding {ce_unwinding:,}"))
else:
    factors.append(("Unwinding", "NEUTRAL", 0, "Balanced"))

# 5. ATM ΔOI (10 points)
if atm_pe_change > 0 and atm_ce_change < 0:
    oi_change_score += 10
    factors.append(("ATM ΔOI", "BULLISH", 10, f"PE +{atm_pe_change:,}, CE {atm_ce_change:,}"))
elif atm_ce_change > 0 and atm_pe_change < 0:
    oi_change_score -= 10
    factors.append(("ATM ΔOI", "BEARISH", -10, f"CE +{atm_ce_change:,}, PE {atm_pe_change:,}"))
else:
    factors.append(("ATM ΔOI", "NEUTRAL", 0, "Mixed"))

# Normalize
oi_change_score = max(-100, min(100, oi_change_score))

# ========== FINAL DECISION ==========
if oi_change_score > 20:
    oi_change_bias = "BULLISH"
elif oi_change_score < -20:
    oi_change_bias = "BEARISH"
else:
    oi_change_bias = "NEUTRAL"

# ========== HEADER ==========
st.title("📊 OI Change Analysis - Fresh Positioning")
st.write(f"**{exchange}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.divider()

# ========== DECISION ==========
if oi_change_bias == "BULLISH":
    st.success(f"### 🟢 OI CHANGE BIAS: {oi_change_bias}")
elif oi_change_bias == "BEARISH":
    st.error(f"### 🔴 OI CHANGE BIAS: {oi_change_bias}")
else:
    st.warning(f"### 🟡 OI CHANGE BIAS: {oi_change_bias}")

st.write(f"**OI Change Score:** {oi_change_score:+d}/100")
st.progress(abs(oi_change_score) / 100)
st.divider()

# ========== FACTORS ==========
st.subheader("🔍 Fresh Positioning Factors")

for name, signal, score, detail in factors:
    if "BULLISH" in signal:
        icon = "🟢"
    elif "BEARISH" in signal:
        icon = "🔴"
    else:
        icon = "🟡"
    
    score_display = f"+{score}" if score > 0 else str(score)
    st.write(f"{icon} **{name}:** {signal} ({score_display}) - {detail}")

st.divider()

# ========== CHANGE METRICS ==========
st.subheader("📊 Change in OI Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Total CE ΔOI", f"{ce_change:+,.0f}")
col2.metric("Total PE ΔOI", f"{pe_change:+,.0f}")
col3.metric("Change-OI PCR", f"{pcr_change:.2f}")
col4.metric("Total Change", f"{total_change:,}")

st.divider()

# ========== WRITING/UNWINDING ==========
st.subheader("📝 Writing vs Unwinding")

col1, col2, col3, col4 = st.columns(4)
col1.metric("🔴 Call Writing", f"{ce_writing:,}")
col2.metric("🟢 Put Writing", f"{pe_writing:,}")
col3.metric("🔴 Call Unwinding", f"{ce_unwinding:,}")
col4.metric("🟢 Put Unwinding", f"{pe_unwinding:,}")

st.divider()

# ========== HIGHEST ΔOI ==========
st.subheader("🏆 Highest ΔOI Strikes")

col1, col2 = st.columns(2)
col1.metric("CE Max ΔOI Strike", f"₹{highest_ce_change_strike:,.0f}")
col2.metric("PE Max ΔOI Strike", f"₹{highest_pe_change_strike:,.0f}")

st.divider()

# ========== CHARTS ==========
st.subheader("📊 Change OI Charts")

try:
    fig = make_subplots(
        rows=2, cols=1,
        subplot_titles=('Change in OI Distribution', 'CE vs PE Change'),
        vertical_spacing=0.2
    )
    
    fig.update_layout(template='plotly_white', height=600)
    
    fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_CHANGE_IN_OI'], name='CE ΔOI',
                   marker_color='#e74c3c'), row=1, col=1)
    fig.add_trace(go.Bar(x=df['STRIKE'], y=df['PE_CHANGE_IN_OI'], name='PE ΔOI',
                   marker_color='#27ae60'), row=1, col=1)
    fig.add_vline(x=spot, line_dash="dash", line_color="black", row=1, col=1)
    
    fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['CE_CHANGE_IN_OI'].cumsum(), name='Cum CE',
                   line=dict(color='#e74c3c', width=2)), row=2, col=1)
    fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['PE_CHANGE_IN_OI'].cumsum(), name='Cum PE',
                   line=dict(color='#27ae60', width=2)), row=2, col=1)
    
    st.plotly_chart(fig, width='stretch')
except:
    pass

st.divider()
st.warning("⚠️ Educational purposes only.")