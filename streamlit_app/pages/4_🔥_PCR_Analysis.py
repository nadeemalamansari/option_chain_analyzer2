"""
⚖️ PCR Analysis - Enhanced Complete Version
All PCR Variants + Zones + Interpretation
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="PCR Analysis", page_icon="⚖️", layout="wide")

# CSS
st.markdown("""
    <style>
    .stApp { background: #f5f7fa; }
    div[data-testid="stMetric"] {
        background: white;
        border-radius: 10px;
        padding: 10px;
        border: 1px solid #e8ecf1;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

# Check data
if 'data' not in st.session_state or st.session_state.data is None:
    st.warning("⚠️ No data loaded!")
    st.stop()

df = st.session_state.data.copy()
spot = st.session_state.get('spot_price', 0) or 0
exchange = st.session_state.get('exchange', 'N/A')

# ========== ALL PCR CALCULATIONS ==========
total_ce = int(df['CE_OI'].sum())
total_pe = int(df['PE_OI'].sum())
ce_vol = int(df['CE_VOLUME'].sum())
pe_vol = int(df['PE_VOLUME'].sum())
ce_change = int(df['CE_CHANGE_IN_OI'].sum()) if 'CE_CHANGE_IN_OI' in df.columns else 0
pe_change = int(df['PE_CHANGE_IN_OI'].sum()) if 'PE_CHANGE_IN_OI' in df.columns else 0

# PCR Variants
pcr_oi = total_pe / total_ce if total_ce > 0 else 0
pcr_vol = pe_vol / ce_vol if ce_vol > 0 else 0
pcr_change = pe_change / ce_change if ce_change != 0 else 0

if spot > 0:
    df['_dist'] = abs(df['STRIKE'] - spot)
    atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    df.drop('_dist', axis=1, inplace=True)
else:
    atm = float(df['STRIKE'].iloc[len(df)//2])

# ATM PCR
atm_data = df[df['STRIKE'] == atm]
atm_pcr = float(atm_data.iloc[0]['PE_OI'] / atm_data.iloc[0]['CE_OI']) if len(atm_data) > 0 and atm_data.iloc[0]['CE_OI'] > 0 else 0

# Near-ATM PCR (±100)
near_atm = df[(df['STRIKE'] >= atm - 100) & (df['STRIKE'] <= atm + 100)]
near_atm_pcr = float(near_atm['PE_OI'].sum() / near_atm['CE_OI'].sum()) if near_atm['CE_OI'].sum() > 0 else 0

# OTM PCR
otm_ce = df[df['STRIKE'] > spot]['CE_OI'].sum()
otm_pe = df[df['STRIKE'] < spot]['PE_OI'].sum()
otm_pcr = float(otm_pe / otm_ce) if otm_ce > 0 else 0

# ITM PCR
itm_ce = df[df['STRIKE'] < spot]['CE_OI'].sum()
itm_pe = df[df['STRIKE'] > spot]['PE_OI'].sum()
itm_pcr = float(itm_pe / itm_ce) if itm_ce > 0 else 0

# Weighted PCR
weighted_ce = float((df['CE_OI'] * df['CE_VOLUME']).sum())
weighted_pe = float((df['PE_OI'] * df['PE_VOLUME']).sum())
weighted_pcr = weighted_pe / weighted_ce if weighted_ce > 0 else 0

# Premium PCR
ce_premium = float(df['CE_LTP'].sum())
pe_premium = float(df['PE_LTP'].sum())
premium_pcr = pe_premium / ce_premium if ce_premium > 0 else 0

# ========== PCR SIGNAL FUNCTION ==========
def get_pcr_signal(pcr_val):
    if pcr_val > 1.5:
        return '🟢 STRONG BULLISH', '#27ae60'
    elif pcr_val > 1.2:
        return '🟢 BULLISH', '#2ecc71'
    elif pcr_val >= 0.7:
        return '🟡 NEUTRAL', '#f39c12'
    elif pcr_val >= 0.5:
        return '🔴 BEARISH', '#e67e22'
    else:
        return '🔴 STRONG BEARISH', '#e74c3c'

# ========== SCORING ==========
bull_score = 10
bear_score = 10

# OI PCR (30)
if pcr_oi > 1.5:
    bull_score += 30
elif pcr_oi > 1.2:
    bull_score += 25
elif pcr_oi < 0.5:
    bear_score += 30
elif pcr_oi < 0.7:
    bear_score += 25
else:
    bull_score += 15
    bear_score += 15

# Volume PCR (25)
if pcr_vol > 1.2:
    bull_score += 25
elif pcr_vol < 0.7:
    bear_score += 25
else:
    bull_score += 12
    bear_score += 12

# Change PCR (25)
if pcr_change > 1.2:
    bull_score += 25
elif pcr_change < 0.7:
    bear_score += 25
else:
    bull_score += 12
    bear_score += 12

# ATM PCR (20)
if atm_pcr > 1.2:
    bull_score += 20
elif atm_pcr < 0.7:
    bear_score += 20
else:
    bull_score += 10
    bear_score += 10

bull_score = min(100, bull_score)
bear_score = min(100, bear_score)
confidence = max(bull_score, bear_score)

# ========== HEADER ==========
st.title("⚖️ PCR Analysis")
st.write(f"**{exchange}** | Spot: **₹{spot:,.2f}** | ATM: **₹{atm:,.0f}**")
st.divider()

# ========== PCR DECISION ==========
if bull_score > bear_score + 10:
    decision = "BULLISH PCR"
    st.success(f"### 🟢 PCR DECISION: {decision}")
elif bear_score > bull_score + 10:
    decision = "BEARISH PCR"
    st.error(f"### 🔴 PCR DECISION: {decision}")
else:
    decision = "NEUTRAL PCR"
    st.warning(f"### 🟡 PCR DECISION: {decision}")

st.write(f"**Bull:** {bull_score}/100 | **Bear:** {bear_score}/100 | **Confidence:** {confidence}/100")
st.progress(confidence / 100)
st.divider()

# ========== ALL PCR VARIANTS ==========
st.subheader("📊 All PCR Variants")

c1, c2, c3, c4 = st.columns(4)

with c1:
    signal, color = get_pcr_signal(pcr_oi)
    st.metric("OI PCR", f"{pcr_oi:.3f}")
    st.write(f"<span style='color:{color};'>{signal}</span>", unsafe_allow_html=True)

with c2:
    signal, color = get_pcr_signal(pcr_vol)
    st.metric("Volume PCR", f"{pcr_vol:.3f}")
    st.write(f"<span style='color:{color};'>{signal}</span>", unsafe_allow_html=True)

with c3:
    signal, color = get_pcr_signal(pcr_change)
    st.metric("Change OI PCR", f"{pcr_change:.3f}")
    st.write(f"<span style='color:{color};'>{signal}</span>", unsafe_allow_html=True)

with c4:
    signal, color = get_pcr_signal(atm_pcr)
    st.metric("ATM PCR", f"{atm_pcr:.3f}")
    st.write(f"<span style='color:{color};'>{signal}</span>", unsafe_allow_html=True)

c5, c6, c7, c8 = st.columns(4)

with c5:
    signal, color = get_pcr_signal(near_atm_pcr)
    st.metric("Near-ATM PCR", f"{near_atm_pcr:.3f}")

with c6:
    signal, color = get_pcr_signal(otm_pcr)
    st.metric("OTM PCR", f"{otm_pcr:.3f}")

with c7:
    signal, color = get_pcr_signal(itm_pcr)
    st.metric("ITM PCR", f"{itm_pcr:.3f}")

with c8:
    signal, color = get_pcr_signal(weighted_pcr)
    st.metric("Weighted PCR", f"{weighted_pcr:.3f}")

st.divider()

# ========== PCR ZONES ==========
st.subheader("🎯 PCR Zones")

zones = [
    ('> 1.50', 'STRONG BULLISH', '#27ae60', pcr_oi > 1.5),
    ('1.20 - 1.50', 'BULLISH', '#2ecc71', 1.2 < pcr_oi <= 1.5),
    ('0.70 - 1.20', 'NEUTRAL', '#f39c12', 0.7 <= pcr_oi <= 1.2),
    ('0.50 - 0.70', 'BEARISH', '#e67e22', 0.5 <= pcr_oi < 0.7),
    ('< 0.50', 'STRONG BEARISH', '#e74c3c', pcr_oi < 0.5)
]

for range_val, signal, color, active in zones:
    marker = " ← CURRENT" if active else ""
    st.write(f"**PCR {range_val}** → {signal}{marker}")

st.divider()

# ========== OI DETAILS ==========
st.subheader("📊 OI Details")

c1, c2, c3 = st.columns(3)
c1.metric("Total CE OI", f"{total_ce:,}")
c2.metric("Total PE OI", f"{total_pe:,}")
c3.metric("Total OI", f"{total_ce+total_pe:,}")

st.divider()

# ========== CHARTS ==========
st.subheader("📈 PCR Charts")

try:
    if 'STRIKE_PCR' not in df.columns:
        df['STRIKE_PCR'] = np.where(df['CE_OI'] > 0, df['PE_OI'] / df['CE_OI'], 0)
    
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('Strike-wise PCR', 'CE vs PE OI', 'Volume Distribution', 'PCR Gauge'),
        vertical_spacing=0.15,
        horizontal_spacing=0.1
    )
    
    fig.update_layout(template='plotly_white', height=700)
    
    # Strike PCR
    fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['STRIKE_PCR'], name='PCR',
                   line=dict(color='#f39c12', width=2)), row=1, col=1)
    fig.add_hline(y=1, line_dash="dash", line_color="gray", row=1, col=1)
    fig.add_hline(y=0.7, line_dash="dot", line_color="#e74c3c", row=1, col=1)
    fig.add_hline(y=1.2, line_dash="dot", line_color="#27ae60", row=1, col=1)
    
    # CE vs PE OI
    fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['CE_OI'], name='CE OI',
                   line=dict(color='#27ae60', width=2)), row=1, col=2)
    fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['PE_OI'], name='PE OI',
                   line=dict(color='#e74c3c', width=2)), row=1, col=2)
    
    # Volume
    fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_VOLUME'], name='CE Vol',
                   marker_color='rgba(39,174,96,0.6)'), row=2, col=1)
    fig.add_trace(go.Bar(x=df['STRIKE'], y=df['PE_VOLUME'], name='PE Vol',
                   marker_color='rgba(231,76,60,0.6)'), row=2, col=1)
    
    # PCR Gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=pcr_oi,
        gauge={
            'axis': {'range': [0, 2]},
            'steps': [
                {'range': [0, 0.7], 'color': '#e74c3c'},
                {'range': [0.7, 1.2], 'color': '#f39c12'},
                {'range': [1.2, 2], 'color': '#27ae60'}
            ],
            'threshold': {'line': {'color': 'black', 'width': 3}, 'value': 1.0}
        }
    ), row=2, col=2)
    
    st.plotly_chart(fig, width='stretch')
except:
    pass

st.divider()

# ========== INTERPRETATION ==========
st.subheader("📖 PCR Interpretation")

if pcr_oi > 1.5:
    st.success("""
    **🟢 STRONG BULLISH (PCR > 1.5)**
    - PE OI bahut zyada hai CE OI se
    - Put writers dominant hain
    - Strong support building
    - Signal: BUY CALL favorable
    """)
elif pcr_oi > 1.2:
    st.success("""
    **🟢 BULLISH (PCR 1.2 - 1.5)**
    - PE OI zyada hai CE OI se
    - Put writers active
    - Support building
    - Signal: BUY CALL consider karo
    """)
elif pcr_oi >= 0.7:
    st.warning("""
    **🟡 NEUTRAL (PCR 0.7 - 1.2)**
    - OI balanced hai
    - No clear direction
    - Signal: Range trading better
    """)
elif pcr_oi >= 0.5:
    st.error("""
    **🔴 BEARISH (PCR 0.5 - 0.7)**
    - CE OI zyada hai PE OI se
    - Call writers active
    - Resistance building
    - Signal: BUY PUT consider karo
    """)
else:
    st.error("""
    **🔴 STRONG BEARISH (PCR < 0.5)**
    - CE OI bahut zyada hai
    - Call writers dominant
    - Strong resistance
    - Signal: BUY PUT favorable
    """)

st.divider()
st.warning("⚠️ Educational purposes only.")