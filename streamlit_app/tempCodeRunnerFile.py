"""
Option Chain Analyzer PRO - Complete Fixed
✅ PCR < 0.7 = BEARISH (Call writers active)
✅ PCR > 1.2 = BULLISH (Put writers active)

============================================================
LAYER-BASED OPTIONS ANALYSIS SYSTEM
Layer 1: Fresh Positioning (40%)
Layer 2: Existing Structure (35%)
Layer 3: Confirmation (25%)
============================================================
"""

import streamlit as st
import sys
from pathlib import Path
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import traceback

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

try:
    from src.core.data_nse_parser import NSEOptionChainParser
    from src.core.data_bse_parser import BSEOptionChainParser
except ImportError:
    st.warning("⚠️ Parser modules not found. Some features may be limited.")

st.set_page_config(
    page_title="Option Chain Analyzer PRO",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ========== CSS ==========
st.markdown("""
    <style>
    .main-header {
        background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
        color: white;
        padding: 30px;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 25px;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 12px;
        text-align: center;
        box-shadow: 0 3px 10px rgba(0,0,0,0.1);
    }
    .stButton>button {
        background: linear-gradient(90deg, #667eea, #764ba2);
        color: white;
        font-weight: bold;
        padding: 12px 25px;
        border-radius: 10px;
        border: none;
        width: 100%;
    }
    .layer-card {
        background: white;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 5px solid #3498DB;
        margin-bottom: 10px;
    }
    </style>
""", unsafe_allow_html=True)

# ========== SESSION STATE ==========
def init_session():
    defaults = {
        'data': None,
        'spot_price': 0.0,
        'exchange': None,
        'total_ce': 0,
        'total_pe': 0,
        'pcr': 0.0,
        'total_oi': 0,
        'total_ce_vol': 0,
        'total_pe_vol': 0,
        'filename': None,
        'data_loaded': False,
        'processed_data': None,
        'analysis_results': None,
        'format_type': "N/A",
        'active_tab': "Basic Analysis"
    }
    for key, val in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = val

init_session()

# ========== UTILITY FUNCTIONS ==========
def safe_float(value, default=0.0):
    try:
        if value is None or pd.isna(value):
            return default
        if isinstance(value, str):
            value = value.replace(',', '').replace('-', '0').strip()
            if value == '' or value == '—':
                return default
        return float(value)
    except:
        return default

def get_signal(score):
    if score >= 70:
        return "STRONG BUY 🟢"
    elif score >= 55:
        return "BUY 🟡"
    elif score >= 45:
        return "NEUTRAL ⚪"
    elif score >= 30:
        return "SELL 🟠"
    else:
        return "STRONG SELL 🔴"

# ========== LAYER WEIGHTAGE ==========
LAYER_WEIGHTS = {
    'layer1': {'label': 'Fresh Positioning', 'weight': 40, 'emoji': '🆕'},
    'layer2': {'label': 'Existing Structure', 'weight': 35, 'emoji': '🏗️'},
    'layer3': {'label': 'Confirmation', 'weight': 25, 'emoji': '✅'},
}

# ========== PARSER ==========
def get_parser(exchange):
    try:
        if exchange == 'NSE':
            return NSEOptionChainParser()
        return BSEOptionChainParser()
    except:
        return None

# ========== LAYER ANALYSIS FUNCTIONS ==========

def analyze_layer1(df, spot):
    """Layer 1: Fresh Positioning - CE ΔOI vs PE ΔOI, Change-OI PCR, Call/Put Writing"""
    
    ce_chg = df['CE_CHG_OI'].sum()
    pe_chg = df['PE_CHG_OI'].sum()
    
    # 1. CE ΔOI vs PE ΔOI
    if ce_chg > 0 and pe_chg < 0:
        delta_signal = "BEARISH - CE Writing Active"
        delta_score = 1
    elif pe_chg > 0 and ce_chg < 0:
        delta_signal = "BULLISH - PE Writing Active"
        delta_score = 5
    elif ce_chg > 0 and pe_chg > 0:
        delta_signal = "Both Buildup - Volatile"
        delta_score = 3
    else:
        delta_signal = "Mixed/Unwinding"
        delta_score = 2
    
    # 2. Change-OI PCR
    change_pcr = pe_chg / ce_chg if ce_chg != 0 else 0
    if change_pcr > 1:
        pcr_signal = "BULLISH - PE ΔOI > CE ΔOI"
        pcr_score = 5
    elif change_pcr < -1:
        pcr_signal = "BEARISH - CE ΔOI > PE ΔOI"
        pcr_score = 1
    else:
        pcr_signal = "NEUTRAL"
        pcr_score = 3
    
    # 3. Call/Put Writing
    if ce_chg > 5000:
        writing_signal = "HEAVY CALL WRITING"
        writing_score = 1
    elif pe_chg > 5000:
        writing_signal = "HEAVY PUT WRITING"
        writing_score = 5
    else:
        writing_signal = "Normal Activity"
        writing_score = 3
    
    # Layer 1 Total
    layer1_score = (delta_score + pcr_score + writing_score) / 3 * 5
    
    return {
        'delta_signal': delta_signal,
        'delta_score': delta_score,
        'ce_chg': ce_chg,
        'pe_chg': pe_chg,
        'change_pcr': change_pcr,
        'pcr_signal': pcr_signal,
        'pcr_score': pcr_score,
        'writing_signal': writing_signal,
        'writing_score': writing_score,
        'layer_score': round(layer1_score, 1),
        'signal': delta_signal if delta_score <= 2 or delta_score >= 4 else pcr_signal,
    }

def analyze_layer2(df, spot):
    """Layer 2: Existing Structure - CE OI vs PE OI, S/R, ATM Concentration"""
    
    ce_oi = df['CE_OI'].sum()
    pe_oi = df['PE_OI'].sum()
    
    # 1. CE OI vs PE OI
    if ce_oi > pe_oi * 1.15:
        oi_signal = "BEARISH - CE OI Dominant"
        oi_score = 1
    elif pe_oi > ce_oi * 1.15:
        oi_signal = "BULLISH - PE OI Dominant"
        oi_score = 5
    else:
        oi_signal = "NEUTRAL - Balanced"
        oi_score = 3
    
    # 2. Strong Resistance vs Support
    support_df = df[df['STRIKE'] < spot]
    resistance_df = df[df['STRIKE'] > spot]
    
    nearest_support = support_df.loc[support_df['PE_OI'].idxmax(), 'STRIKE'] if not support_df.empty else spot - 500
    nearest_resistance = resistance_df.loc[resistance_df['CE_OI'].idxmax(), 'STRIKE'] if not resistance_df.empty else spot + 500
    
    support_oi = df[df['STRIKE'] == nearest_support]['PE_OI'].sum()
    resistance_oi = df[df['STRIKE'] == nearest_resistance]['CE_OI'].sum()
    
    if support_oi > resistance_oi * 1.15:
        sr_signal = "BULLISH - Support Stronger"
        sr_score = 5
    elif resistance_oi > support_oi * 1.15:
        sr_signal = "BEARISH - Resistance Stronger"
        sr_score = 1
    else:
        sr_signal = "NEUTRAL"
        sr_score = 3
    
    # 3. OI Concentration around ATM
    atm_strike = df.iloc[(df['STRIKE'] - spot).abs().argsort()[:1]]['STRIKE'].values[0]
    atm_range = df[df['STRIKE'].between(atm_strike - 300, atm_strike + 300)]
    atm_ce_oi = atm_range['CE_OI'].sum()
    atm_pe_oi = atm_range['PE_OI'].sum()
    
    if atm_pe_oi > atm_ce_oi * 1.1:
        atm_signal = "BULLISH - ATM PE Concentration"
        atm_score = 5
    elif atm_ce_oi > atm_pe_oi * 1.1:
        atm_signal = "BEARISH - ATM CE Concentration"
        atm_score = 1
    else:
        atm_signal = "NEUTRAL"
        atm_score = 3
    
    # Layer 2 Total
    layer2_score = (oi_score + sr_score + atm_score) / 3 * 5
    
    return {
        'ce_oi': ce_oi,
        'pe_oi': pe_oi,
        'oi_signal': oi_signal,
        'oi_score': oi_score,
        'nearest_support': nearest_support,
        'nearest_resistance': nearest_resistance,
        'support_oi': support_oi,
        'resistance_oi': resistance_oi,
        'sr_signal': sr_signal,
        'sr_score': sr_score,
        'atm_signal': atm_signal,
        'atm_score': atm_score,
        'layer_score': round(layer2_score, 1),
        'signal': oi_signal if oi_score <= 2 or oi_score >= 4 else sr_signal,
    }

def analyze_layer3(df, spot):
    """Layer 3: Confirmation - Price+OI, Volume, ATM ΔOI"""
    
    # 1. Price + OI
    ce_ltp_avg = df['CE_LTP'].mean()
    pe_ltp_avg = df['PE_LTP'].mean()
    ce_chg = df['CE_CHG_OI'].sum()
    
    if ce_chg > 0 and ce_ltp_avg > pe_ltp_avg:
        price_signal = "BULLISH - Long Buildup"
        price_score = 5
    elif ce_chg > 0:
        price_signal = "BEARISH - Short Buildup"
        price_score = 1
    else:
        price_signal = "NEUTRAL"
        price_score = 3
    
    # 2. Volume
    ce_vol = df['CE_VOLUME'].sum()
    pe_vol = df['PE_VOLUME'].sum()
    
    if pe_vol > ce_vol * 1.1:
        vol_signal = "BULLISH - PE Volume High"
        vol_score = 5
    elif ce_vol > pe_vol * 1.1:
        vol_signal = "BEARISH - CE Volume High"
        vol_score = 1
    else:
        vol_signal = "NEUTRAL"
        vol_score = 3
    
    # 3. ATM ΔOI
    atm_strike = df.iloc[(df['STRIKE'] - spot).abs().argsort()[:1]]['STRIKE'].values[0]
    atm_row = df[df['STRIKE'] == atm_strike]
    
    if not atm_row.empty:
        atm_ce_chg = safe_float(atm_row.iloc[0]['CE_CHG_OI'])
        atm_pe_chg = safe_float(atm_row.iloc[0]['PE_CHG_OI'])
        
        if atm_pe_chg > 0 and atm_ce_chg < 0:
            atm_delta_signal = "BULLISH - ATM PE Buildup"
            atm_delta_score = 5
        elif atm_ce_chg > 0 and atm_pe_chg < 0:
            atm_delta_signal = "BEARISH - ATM CE Buildup"
            atm_delta_score = 1
        else:
            atm_delta_signal = "NEUTRAL"
            atm_delta_score = 3
    else:
        atm_delta_signal = "N/A"
        atm_delta_score = 3
    
    # Layer 3 Total
    layer3_score = (price_score + vol_score + atm_delta_score) / 3 * 5
    
    return {
        'price_signal': price_signal,
        'price_score': price_score,
        'ce_vol': ce_vol,
        'pe_vol': pe_vol,
        'vol_signal': vol_signal,
        'vol_score': vol_score,
        'atm_delta_signal': atm_delta_signal,
        'atm_delta_score': atm_delta_score,
        'layer_score': round(layer3_score, 1),
        'signal': price_signal if price_score <= 2 or price_score >= 4 else vol_signal,
    }

def run_layer_analysis(df, spot):
    """Run all 3 layers and combine"""
    
    layer1 = analyze_layer1(df, spot)
    layer2 = analyze_layer2(df, spot)
    layer3 = analyze_layer3(df, spot)
    
    # Weighted final score (0-100)
    final_score = (
        layer1['layer_score'] / 5 * 40 +
        layer2['layer_score'] / 5 * 35 +
        layer3['layer_score'] / 5 * 25
    )
    
    signal = get_signal(final_score)
    
    return {
        'layer1': layer1,
        'layer2': layer2,
        'layer3': layer3,
        'final_score': round(final_score, 2),
        'signal': signal,
        'strategy': 'Bull Call Spread' if 'BUY' in signal else 'Bear Put Spread' if 'SELL' in signal else 'Iron Condor',
    }

# ========== HEADER ==========
st.markdown("""
<div class="main-header">
    <h1>📊 Option Chain Analyzer PRO</h1>
    <p style="font-size:1.1em;opacity:0.9;">Basic Analysis + Layer-Based Advanced Analysis</p>
</div>
""", unsafe_allow_html=True)

# ========== SIDEBAR ==========
with st.sidebar:
    st.markdown("### 📁 Upload Data")
    
    exchange = st.selectbox("Select Exchange", ["NSE", "BSE"])
    
    uploaded_file = st.file_uploader(
        f"Upload {exchange} Option Chain CSV",
        type=['csv']
    )
    
    if uploaded_file is not None:
        st.info(f"📄 {uploaded_file.name}")
        st.info(f"📏 {uploaded_file.size/1024:.1f} KB")
        
        if st.button("🔍 Analyze Data", use_container_width=True):
            with st.spinner("🔄 Analyzing..."):
                try:
                    parser = get_parser(exchange)
                    
                    if parser:
                        df = parser.parse_csv(uploaded_file)
                    else:
                        # Fallback: Try to parse directly
                        df = pd.read_csv(uploaded_file)
                        # Basic column mapping
                        if 'CE_OI' not in df.columns:
                            st.error("❌ Parser not available. Please ensure src/core/data_*.py exists.")
                            st.stop()
                    
                    if df is None or len(df) == 0:
                        st.error("❌ Could not parse CSV")
                    else:
                        # Basic calculations
                        total_ce = int(df['CE_OI'].sum())
                        total_pe = int(df['PE_OI'].sum())
                        total_oi = total_ce + total_pe
                        total_ce_vol = int(df['CE_VOLUME'].sum())
                        total_pe_vol = int(df['PE_VOLUME'].sum())
                        
                        pcr = total_pe / total_ce if total_ce > 0 else 0
                        
                        spot = parser.spot_price if parser and hasattr(parser, 'spot_price') else 0
                        if spot == 0:
                            spot = float(df['STRIKE'].iloc[len(df)//2])
                        
                        # Store in session
                        st.session_state.data = df
                        st.session_state.spot_price = spot
                        st.session_state.exchange = exchange
                        st.session_state.total_ce = total_ce
                        st.session_state.total_pe = total_pe
                        st.session_state.total_oi = total_oi
                        st.session_state.total_ce_vol = total_ce_vol
                        st.session_state.total_pe_vol = total_pe_vol
                        st.session_state.pcr = pcr
                        st.session_state.filename = uploaded_file.name
                        st.session_state.data_loaded = True
                        
                        # Process for layer analysis
                        st.session_state.processed_data = df
                        st.session_state.analysis_results = run_layer_analysis(df, spot)
                        
                        st.success(f"✅ Analysis Complete! {len(df)} strikes")
                        
                        # Summary
                        st.markdown(f"""
                        **📊 Summary:**
                        - CE OI: {total_ce:,}
                        - PE OI: {total_pe:,}
                        - PCR: {pcr:.2f}
                        """)
                        
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.code(traceback.format_exc())
    
    # Current data info
    if st.session_state.data_loaded:
        st.markdown("---")
        st.markdown("### 📊 Current Data")
        st.write(f"**Exchange:** {st.session_state.exchange}")
        st.write(f"**File:** {st.session_state.filename}")
        st.write(f"**Spot:** ₹{st.session_state.spot_price:,.2f}")
        st.write(f"**CE OI:** {st.session_state.total_ce:,}")
        st.write(f"**PE OI:** {st.session_state.total_pe:,}")
        st.write(f"**PCR:** {st.session_state.pcr:.2f}")
        
        # Reset
        if st.button("🔄 Reset Data", use_container_width=True):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            init_session()
            st.rerun()

# ========== MAIN CONTENT ==========
if st.session_state.data_loaded and st.session_state.data is not None:
    df = st.session_state.data
    spot = st.session_state.spot_price
    pcr = st.session_state.pcr
    exchange = st.session_state.exchange
    
    # ===== TABS =====
    tab1, tab2 = st.tabs(["📊 Basic Analysis", "🎯 Layer-Based Analysis"])
    
    # ===== TAB 1: Basic Analysis =====
    with tab1:
        st.markdown("### 📊 Quick Overview")
        
        # Key Metrics
        c1, c2, c3, c4, c5, c6 = st.columns(6)
        
        with c1:
            st.metric("PCR", f"{pcr:.2f}")
        with c2:
            st.metric("CE OI", f"{st.session_state.total_ce:,}")
        with c3:
            st.metric("PE OI", f"{st.session_state.total_pe:,}")
        with c4:
            st.metric("Total OI", f"{st.session_state.total_oi:,}")
        with c5:
            st.metric("CE Volume", f"{st.session_state.total_ce_vol:,}")
        with c6:
            st.metric("PE Volume", f"{st.session_state.total_pe_vol:,}")
        
        st.markdown("---")
        
        # PCR Signal Display
        if pcr < 0.5:
            st.error(f"""
            ### 🔴 STRONGLY BEARISH
            PCR {pcr:.2f} < 0.5 → CE OI >> PE OI → Call writers active
            **Recommendation: BUY PUT**
            """)
        elif pcr < 0.7:
            st.error(f"""
            ### 🔴 BEARISH
            PCR {pcr:.2f} < 0.7 → CE OI > PE OI → Call writers dominant
            **Recommendation: BUY PUT**
            """)
        elif pcr <= 1.2:
            st.warning(f"""
            ### 🟡 NEUTRAL
            PCR {pcr:.2f} → Balanced OI
            **Recommendation: RANGE TRADE**
            """)
        elif pcr <= 1.5:
            st.success(f"""
            ### 🟢 BULLISH
            PCR {pcr:.2f} > 1.2 → PE OI > CE OI → Put writers dominant
            **Recommendation: BUY CALL**
            """)
        else:
            st.success(f"""
            ### 🟢 STRONGLY BULLISH
            PCR {pcr:.2f} > 1.5 → PE OI >> CE OI → Put writers active
            **Recommendation: STRONG BUY CALL**
            """)
        
        st.markdown("---")
        
        # ATM
        if spot > 0:
            df['_dist'] = abs(df['STRIKE'] - spot)
            atm = float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
            df.drop('_dist', axis=1, inplace=True)
        else:
            atm = float(df['STRIKE'].iloc[len(df)//2])
        
        st.info(f"⚡ ATM Strike: ₹{atm:,.0f}")
        
        st.markdown("---")
        
        # Charts
        st.markdown("### 📈 Charts")
        
        try:
            fig = make_subplots(
                rows=2, cols=2,
                subplot_titles=('OI Distribution', 'CE vs PE OI', 'Volume', 'Strike PCR'),
                vertical_spacing=0.15,
                horizontal_spacing=0.1
            )
            
            fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_OI'], name='CE OI',
                           marker_color='#2ecc71', opacity=0.7), row=1, col=1)
            fig.add_trace(go.Bar(x=df['STRIKE'], y=-df['PE_OI'], name='PE OI',
                           marker_color='#e74c3c', opacity=0.7), row=1, col=1)
            fig.add_vline(x=spot, line_dash="dash", line_color="blue", row=1, col=1)
            
            fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['CE_OI'], name='CE',
                           line=dict(color='green', width=2)), row=1, col=2)
            fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['PE_OI'], name='PE',
                           line=dict(color='red', width=2)), row=1, col=2)
            
            fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_VOLUME'], name='CE Vol',
                           marker_color='#a8e6cf', opacity=0.7), row=2, col=1)
            fig.add_trace(go.Bar(x=df['STRIKE'], y=df['PE_VOLUME'], name='PE Vol',
                           marker_color='#ff8b94', opacity=0.7), row=2, col=1)
            
            if 'STRIKE_PCR' not in df.columns:
                df['STRIKE_PCR'] = np.where(df['CE_OI'] > 0, df['PE_OI'] / df['CE_OI'], 0)
            fig.add_trace(go.Scatter(x=df['STRIKE'], y=df['STRIKE_PCR'], name='PCR',
                           line=dict(color='#FF9800', width=2)), row=2, col=2)
            fig.add_hline(y=1, line_dash="dash", line_color="gray", row=2, col=2)
            
            fig.update_layout(height=700, showlegend=True, barmode='relative')
            st.plotly_chart(fig, width='stretch')
        except Exception as e:
            st.error(f"Chart error: {str(e)}")
        
        st.markdown("---")
        
        # Data Preview
        st.markdown("### 📋 Data Preview")
        display_cols = ['STRIKE', 'CE_OI', 'PE_OI', 'TOTAL_OI', 'STRIKE_PCR']
        available = [c for c in display_cols if c in df.columns]
        if available:
            preview = df[available].head(20).copy()
            for col in ['CE_OI', 'PE_OI', 'TOTAL_OI']:
                if col in preview.columns:
                    preview[col] = preview[col].apply(lambda x: f"{int(x):,}")
            st.dataframe(preview, width='stretch')
    
    # ===== TAB 2: Layer-Based Analysis =====
    with tab2:
        if st.session_state.analysis_results:
            results = st.session_state.analysis_results
            
            # Final Signal
            signal = results['signal']
            final_score = results['final_score']
            
            if 'BUY' in signal:
                bg = '#D5F5E3'
            elif 'SELL' in signal:
                bg = '#FADBD8'
            else:
                bg = '#FEF9E7'
            
            st.markdown(f"""
            <div style="background: {bg}; padding: 20px; border-radius: 15px; text-align: center;">
                <h1>{signal}</h1>
                <h3>Final Score: {final_score}/100</h3>
                <p>Suggested Strategy: <b>{results['strategy']}</b></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # 3 Layer Boxes
            col1, col2, col3 = st.columns(3)
            
            layers = [
                ('layer1', '🆕 Fresh Positioning', 40),
                ('layer2', '🏗️ Existing Structure', 35),
                ('layer3', '✅ Confirmation', 25),
            ]
            
            for col, (key, label, weight) in zip([col1, col2, col3], layers):
                data = results[key]
                score = data['layer_score']
                
                with col:
                    st.markdown(f"""
                    <div class="layer-card">
                        <h4>{label}</h4>
                        <p style="font-size: 12px; color: #666;">Weight: {weight}%</p>
                        <h2>{score}/5</h2>
                        <p><b>{data['signal']}</b></p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Layer Details
            st.subheader("📊 Layer Details")
            
            with st.expander("🆕 Layer 1: Fresh Positioning (40%)", expanded=True):
                l1 = results['layer1']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CE ΔOI", f"{l1['ce_chg']:+,.0f}")
                    st.metric("PE ΔOI", f"{l1['pe_chg']:+,.0f}")
                with col2:
                    st.metric("Change PCR", f"{l1['change_pcr']:.2f}")
                    st.metric("Signal", l1['delta_signal'])
                with col3:
                    st.metric("Writing", l1['writing_signal'])
                    st.metric("Layer Score", f"{l1['layer_score']}/5")
            
            with st.expander("🏗️ Layer 2: Existing Structure (35%)", expanded=True):
                l2 = results['layer2']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("CE OI", f"{l2['ce_oi']:,.0f}")
                    st.metric("PE OI", f"{l2['pe_oi']:,.0f}")
                with col2:
                    st.metric("Support", f"₹{l2['nearest_support']:,.0f}")
                    st.metric("Resistance", f"₹{l2['nearest_resistance']:,.0f}")
                with col3:
                    st.metric("S/R Signal", l2['sr_signal'])
                    st.metric("Layer Score", f"{l2['layer_score']}/5")
            
            with st.expander("✅ Layer 3: Confirmation (25%)", expanded=True):
                l3 = results['layer3']
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Price Signal", l3['price_signal'])
                with col2:
                    st.metric("Volume Signal", l3['vol_signal'])
                    st.metric("CE Vol", f"{l3['ce_vol']:,.0f}")
                with col3:
                    st.metric("ATM ΔOI", l3['atm_delta_signal'])
                    st.metric("Layer Score", f"{l3['layer_score']}/5")
            
            st.markdown("---")
            
            # OI Chart
            st.subheader("📈 OI Distribution")
            fig = go.Figure()
            fig.add_trace(go.Bar(x=df['STRIKE'], y=df['CE_OI'], name='CE OI', marker_color='#FF6B6B'))
            fig.add_trace(go.Bar(x=df['STRIKE'], y=df['PE_OI'], name='PE OI', marker_color='#4ECDC4'))
            fig.update_layout(height=400, barmode='overlay')
            st.plotly_chart(fig, use_container_width=True)

else:
    st.info("👈 Upload CSV file from sidebar to analyze")
    st.markdown("""
    ### How to use:
    1. Select Exchange (NSE/BSE)
    2. Upload CSV file
    3. Click Analyze Data
    4. View results in two tabs:
       - **Basic Analysis**: PCR, OI distribution, charts
       - **Layer-Based Analysis**: Advanced 3-layer scoring system
    """)

st.markdown("---")
st.markdown("""
<div style="text-align:center;color:#6c757d;font-size:0.85em;">
    ⚠️ Educational purposes only. Trading me risk hota hai.
</div>
""", unsafe_allow_html=True)