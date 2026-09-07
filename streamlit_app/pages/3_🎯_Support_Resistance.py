"""
🎯 Support/Resistance - Complete S/R Decision
Pure Streamlit Components
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Support/Resistance", page_icon="🎯", layout="wide")

# Check data
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded!")
    st.stop()

df = st.session_state.data.copy()
spot = st.session_state.get('spot_price', 0) or 0
exchange = st.session_state.get('exchange', 'N/A')

# ========== CALCULATIONS ==========
if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

# Highest PE OI (Support)
highest_pe_strike = float(df.loc[df['PE_OI'].idxmax(), 'STRIKE'])
highest_pe_oi = int(df['PE_OI'].max())

# Highest CE OI (Resistance)
highest_ce_strike = float(df.loc[df['CE_OI'].idxmax(), 'STRIKE'])
highest_ce_oi = int(df['CE_OI'].max())

# Highest PE ΔOI (Fresh Support)
highest_pe_change_strike = float(df.loc[df['PE_CHANGE_IN_OI'].idxmax(), 'STRIKE'])
highest_pe_change_val = int(df['PE_CHANGE_IN_OI'].max())

# Highest CE ΔOI (Fresh Resistance)
highest_ce_change_strike = float(df.loc[df['CE_CHANGE_IN_OI'].idxmax(), 'STRIKE'])
highest_ce_change_val = int(df['CE_CHANGE_IN_OI'].max())

# OI Concentration
total_pe = int(df['PE_OI'].sum())
total_ce = int(df['CE_OI'].sum())
near_atm = df[(df['STRIKE'] >= atm - 200) & (df['STRIKE'] <= atm + 200)]
pe_concentration = float(near_atm['PE_OI'].sum() / total_pe * 100) if total_pe > 0 else 0
ce_concentration = float(near_atm['CE_OI'].sum() / total_ce * 100) if total_ce > 0 else 0

# ATM Support/Resistance
atm_data = df[df['STRIKE'] == atm]
atm_pe_oi = int(atm_data.iloc[0]['PE_OI']) if len(atm_data) > 0 else 0
atm_ce_oi = int(atm_data.iloc[0]['CE_OI']) if len(atm_data) > 0 else 0

# ========== SUPPORT STRENGTH CALCULATION ==========
support_strength = 0
support_factors = []

# 1. Highest PE OI (30%)
if total_pe > 0:
    pe_oi_pct = highest_pe_oi / total_pe * 100
    oi_score = min(30, pe_oi_pct * 3)
else:
    oi_score = 0
support_strength += oi_score
support_factors.append(("Highest PE OI", oi_score, f"₹{highest_pe_strike:,.0f} ({highest_pe_oi:,})"))

# 2. PE ΔOI (25%)
max_pe_change = int(df['PE_CHANGE_IN_OI'].max()) if 'PE_CHANGE_IN_OI' in df.columns else 0
if max_pe_change > 0:
    change_score = min(25, max_pe_change / 1000)
else:
    change_score = 0
support_strength += change_score
support_factors.append(("PE ΔOI", change_score, f"₹{highest_pe_change_strike:,.0f} (+{highest_pe_change_val:,})"))

# 3. PE Concentration (20%)
if pe_concentration > 30:
    conc_score = min(20, pe_concentration / 5)
else:
    conc_score = pe_concentration / 10
support_strength += conc_score
support_factors.append(("PE Concentration", conc_score, f"{pe_concentration:.0f}%"))

# 4. ATM PE OI (15%)
if atm_pe_oi > 0:
    atm_score = min(15, atm_pe_oi / 1000)
else:
    atm_score = 0
support_strength += atm_score
support_factors.append(("ATM PE OI", atm_score, f"{atm_pe_oi:,}"))

# 5. Distance from Spot (10%)
support_distance = spot - highest_pe_strike
if support_distance < 500:
    dist_score = 10
elif support_distance < 1000:
    dist_score = 5
else:
    dist_score = 2
support_strength += dist_score
support_factors.append(("Distance", dist_score, f"{support_distance:.0f} pts"))

support_strength = min(100, round(support_strength))

# ========== RESISTANCE STRENGTH ==========
resistance_strength = 0
resistance_factors = []

# 1. Highest CE OI (30%)
if total_ce > 0:
    ce_oi_pct = highest_ce_oi / total_ce * 100
    oi_score = min(30, ce_oi_pct * 3)
else:
    oi_score = 0
resistance_strength += oi_score
resistance_factors.append(("Highest CE OI", oi_score, f"₹{highest_ce_strike:,.0f} ({highest_ce_oi:,})"))

# 2. CE ΔOI (25%)
max_ce_change = int(df['CE_CHANGE_IN_OI'].max()) if 'CE_CHANGE_IN_OI' in df.columns else 0
if max_ce_change > 0:
    change_score = min(25, max_ce_change / 1000)
else:
    change_score = 0
resistance_strength += change_score
resistance_factors.append(("CE ΔOI", change_score, f"₹{highest_ce_change_strike:,.0f} (+{highest_ce_change_val:,})"))

# 3. CE Concentration (20%)
if ce_concentration > 30:
    conc_score = min(20, ce_concentration / 5)
else:
    conc_score = ce_concentration / 10
resistance_strength += conc_score
resistance_factors.append(("CE Concentration", conc_score, f"{ce_concentration:.0f}%"))

# 4. ATM CE OI (15%)
if atm_ce_oi > 0:
    atm_score = min(15, atm_ce_oi / 1000)
else:
    atm_score = 0
resistance_strength += atm_score
resistance_factors.append(("ATM CE OI", atm_score, f"{atm_ce_oi:,}"))

# 5. Distance from Spot (10%)
resistance_distance = highest_ce_strike - spot
if resistance_distance < 500:
    dist_score = 10
elif resistance_distance < 1000:
    dist_score = 5
else:
    dist_score = 2
resistance_strength += dist_score
resistance_factors.append(("Distance", dist_score, f"{resistance_distance:.0f} pts"))

resistance_strength = min(100, round(resistance_strength))

# ========== S/R BIAS ==========
if support_strength > resistance_strength + 10:
    sr_bias = "BULLISH"
elif resistance_strength > support_strength + 10:
    sr_bias = "BEARISH"
else:
    sr_bias = "NEUTRAL"

# ========== HEADER ==========
st.title("🎯 Support & Resistance")
st.write(f"**{exchange}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.divider()

# ========== DECISION ==========
if sr_bias == "BULLISH":
    st.success(f"### 🟢 S/R BIAS: {sr_bias}")
elif sr_bias == "BEARISH":
    st.error(f"### 🔴 S/R BIAS: {sr_bias}")
else:
    st.warning(f"### 🟡 S/R BIAS: {sr_bias}")

st.divider()

# ========== STRONG LEVELS ==========
st.subheader("📊 Strong Levels")

col1, col2 = st.columns(2)

with col1:
    st.markdown(f"### 🟢 Strong Support")
    st.markdown(f"## ₹{highest_pe_strike:,.0f}")
    st.write(f"Strength: **{support_strength}/100**")
    st.progress(support_strength / 100)

with col2:
    st.markdown(f"### 🔴 Strong Resistance")
    st.markdown(f"## ₹{highest_ce_strike:,.0f}")
    st.write(f"Strength: **{resistance_strength}/100**")
    st.progress(resistance_strength / 100)

st.divider()

# ========== SUPPORT FACTORS ==========
st.subheader("🟢 Support Strength Breakdown")

for name, score, detail in support_factors:
    st.write(f"**{name}:** {score:.0f} pts - {detail}")

st.write(f"**Total Support Strength: {support_strength}/100**")

st.divider()

# ========== RESISTANCE FACTORS ==========
st.subheader("🔴 Resistance Strength Breakdown")

for name, score, detail in resistance_factors:
    st.write(f"**{name}:** {score:.0f} pts - {detail}")

st.write(f"**Total Resistance Strength: {resistance_strength}/100**")

st.divider()

# ========== KEY METRICS ==========
st.subheader("📊 Key Metrics")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Support", f"₹{highest_pe_strike:,.0f}")
col2.metric("Resistance", f"₹{highest_ce_strike:,.0f}")
col3.metric("Fresh Support", f"₹{highest_pe_change_strike:,.0f}")
col4.metric("Fresh Resistance", f"₹{highest_ce_change_strike:,.0f}")

st.divider()

# ========== CONCENTRATION ==========
st.subheader("📊 OI Concentration")

col1, col2 = st.columns(2)
col1.metric("PE Concentration", f"{pe_concentration:.1f}%")
col2.metric("CE Concentration", f"{ce_concentration:.1f}%")

st.divider()

# ========== CHART ==========
st.subheader("📈 S/R Chart")

try:
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_OI'], name='CE OI',
                   marker_color='rgba(231,76,60,0.6)'))
    fig.add_trace(go.Bar(x=df['STRIKE'], y=-df['PE_OI'], name='PE OI',
                   marker_color='rgba(39,174,96,0.6)'))
    
    fig.add_vline(x=spot, line_width=3, line_color="black", annotation_text=f"SPOT ₹{spot:,.0f}")
    fig.add_vline(x=highest_pe_strike, line_dash="dash", line_width=3, line_color="#27ae60",
                  annotation_text=f"SUPPORT ₹{highest_pe_strike:,.0f}")
    fig.add_vline(x=highest_ce_strike, line_dash="dash", line_width=3, line_color="#e74c3c",
                  annotation_text=f"RESISTANCE ₹{highest_ce_strike:,.0f}")
    
    fig.update_layout(height=500, barmode='relative', template='plotly_white')
    st.plotly_chart(fig, width='stretch')
except:
    pass

st.divider()
st.warning("⚠️ Educational purposes only.")