"""
📊 Technical Indicators Engine - Complete Mathematical Calculations
All standalone indicators from raw option chain data
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Indicators:
    """Complete Mathematical Indicator Engine"""
    
    def __init__(self, data: pd.DataFrame, spot_price: float = 0):
        self.df = data.copy()
        self.spot = spot_price if spot_price > 0 else float(data['STRIKE'].iloc[len(data)//2])
        self.indicators = {}
        
        # Prepare data
        self._prepare_data()
        
        # Calculate all indicators
        self.calculate_all()
    
    def _prepare_data(self):
        """Prepare data with required columns"""
        required = ['CE_OI', 'CE_CHANGE_IN_OI', 'CE_LTP', 'CE_VOLUME', 'CE_IV',
                   'PE_OI', 'PE_CHANGE_IN_OI', 'PE_LTP', 'PE_VOLUME', 'PE_IV']
        
        for col in required:
            if col not in self.df.columns:
                self.df[col] = 0.0
        
        # Derived columns
        self.df['TOTAL_OI'] = self.df['CE_OI'] + self.df['PE_OI']
        self.df['TOTAL_VOLUME'] = self.df['CE_VOLUME'] + self.df['PE_VOLUME']
        self.df['DISTANCE_FROM_SPOT'] = self.df['STRIKE'] - self.spot
    
    def calculate_all(self):
        """Calculate all indicators"""
        self.calculate_pcr_indicators()
        self.calculate_oi_indicators()
        self.calculate_change_oi_indicators()
        self.calculate_volume_indicators()
        self.calculate_iv_indicators()
        self.calculate_max_pain()
        self.calculate_expected_move()
        self.calculate_straddle_strangle()
        self.calculate_liquidity_indicators()
        self.calculate_greeks()
        self.calculate_advanced_indicators()
    
    # ==================== A. PCR INDICATORS ====================
    def calculate_pcr_indicators(self):
        """All PCR indicators"""
        total_ce_oi = float(self.df['CE_OI'].sum())
        total_pe_oi = float(self.df['PE_OI'].sum())
        
        # Total OI PCR
        pcr_oi = total_pe_oi / total_ce_oi if total_ce_oi > 0 else 0
        
        # Volume PCR
        total_ce_vol = float(self.df['CE_VOLUME'].sum())
        total_pe_vol = float(self.df['PE_VOLUME'].sum())
        pcr_vol = total_pe_vol / total_ce_vol if total_ce_vol > 0 else 0
        
        # Change OI PCR
        ce_change = float(self.df['CE_CHANGE_IN_OI'].sum())
        pe_change = float(self.df['PE_CHANGE_IN_OI'].sum())
        pcr_change = pe_change / ce_change if ce_change != 0 else 0
        
        # ATM PCR
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        atm_pcr = float(atm_data.iloc[0]['PE_OI'] / atm_data.iloc[0]['CE_OI']) if len(atm_data) > 0 and atm_data.iloc[0]['CE_OI'] > 0 else 0
        
        # Near-ATM PCR (±100 strikes)
        near_atm = self.df[(self.df['STRIKE'] >= atm - 100) & (self.df['STRIKE'] <= atm + 100)]
        near_atm_pcr = float(near_atm['PE_OI'].sum() / near_atm['CE_OI'].sum()) if near_atm['CE_OI'].sum() > 0 else 0
        
        # OTM PCR (CE OTM = strike > spot, PE OTM = strike < spot)
        otm_ce = self.df[self.df['STRIKE'] > self.spot]['CE_OI'].sum()
        otm_pe = self.df[self.df['STRIKE'] < self.spot]['PE_OI'].sum()
        otm_pcr = float(otm_pe / otm_ce) if otm_ce > 0 else 0
        
        # ITM PCR
        itm_ce = self.df[self.df['STRIKE'] < self.spot]['CE_OI'].sum()
        itm_pe = self.df[self.df['STRIKE'] > self.spot]['PE_OI'].sum()
        itm_pcr = float(itm_pe / itm_ce) if itm_ce > 0 else 0
        
        # Weighted PCR (volume weighted)
        weighted_ce = float((self.df['CE_OI'] * self.df['CE_VOLUME']).sum())
        weighted_pe = float((self.df['PE_OI'] * self.df['PE_VOLUME']).sum())
        weighted_pcr = weighted_pe / weighted_ce if weighted_ce > 0 else 0
        
        # Strike-wise PCR
        self.df['STRIKE_PCR'] = self.df['PE_OI'] / self.df['CE_OI'].replace(0, np.nan)
        self.df['STRIKE_PCR'] = self.df['STRIKE_PCR'].fillna(0)
        
        # PCR Momentum (PCR - PCR SMA)
        self.df['PCR_SMA'] = self.df['STRIKE_PCR'].rolling(window=5, min_periods=1).mean()
        self.df['PCR_MOMENTUM'] = self.df['STRIKE_PCR'] - self.df['PCR_SMA']
        pcr_momentum = float(self.df['PCR_MOMENTUM'].mean())
        
        self.indicators.update({
            'pcr_oi': round(pcr_oi, 3),
            'pcr_volume': round(pcr_vol, 3),
            'pcr_change_oi': round(pcr_change, 3),
            'atm_pcr': round(atm_pcr, 3),
            'near_atm_pcr': round(near_atm_pcr, 3),
            'otm_pcr': round(otm_pcr, 3),
            'itm_pcr': round(itm_pcr, 3),
            'weighted_pcr': round(weighted_pcr, 3),
            'pcr_momentum': round(pcr_momentum, 3)
        })
    
    # ==================== B. OI INDICATORS ====================
    def calculate_oi_indicators(self):
        """OI indicators"""
        total_ce_oi = float(self.df['CE_OI'].sum())
        total_pe_oi = float(self.df['PE_OI'].sum())
        total_oi = total_ce_oi + total_pe_oi
        
        # OI percentage
        ce_oi_pct = (total_ce_oi / total_oi * 100) if total_oi > 0 else 0
        pe_oi_pct = (total_pe_oi / total_oi * 100) if total_oi > 0 else 0
        
        # OI imbalance
        oi_imbalance = ((total_pe_oi - total_ce_oi) / total_oi) if total_oi > 0 else 0
        
        # Top OI strikes
        top_ce = self.df.nlargest(3, 'CE_OI')[['STRIKE', 'CE_OI']].to_dict('records')
        top_pe = self.df.nlargest(3, 'PE_OI')[['STRIKE', 'PE_OI']].to_dict('records')
        
        # OI concentration around ATM
        atm = self._get_atm_strike()
        atm_range = self.df[(self.df['STRIKE'] >= atm - 200) & (self.df['STRIKE'] <= atm + 200)]
        atm_oi_conc = float(atm_range['TOTAL_OI'].sum() / total_oi) if total_oi > 0 else 0
        
        # OI concentration around spot
        spot_range = self.df[(self.df['STRIKE'] >= self.spot - 200) & (self.df['STRIKE'] <= self.spot + 200)]
        spot_oi_conc = float(spot_range['TOTAL_OI'].sum() / total_oi) if total_oi > 0 else 0
        
        self.indicators.update({
            'total_ce_oi': total_ce_oi,
            'total_pe_oi': total_pe_oi,
            'total_oi': total_oi,
            'ce_oi_pct': round(ce_oi_pct, 2),
            'pe_oi_pct': round(pe_oi_pct, 2),
            'oi_imbalance': round(oi_imbalance, 3),
            'top_ce_oi_strikes': top_ce,
            'top_pe_oi_strikes': top_pe,
            'atm_oi_concentration': round(atm_oi_conc, 3),
            'spot_oi_concentration': round(spot_oi_conc, 3)
        })
    
    # ==================== C. CHANGE IN OI INDICATORS ====================
    def calculate_change_oi_indicators(self):
        """Change in OI indicators"""
        ce_change = float(self.df['CE_CHANGE_IN_OI'].sum())
        pe_change = float(self.df['PE_CHANGE_IN_OI'].sum())
        total_change = abs(ce_change) + abs(pe_change)
        
        # Change OI imbalance
        change_imbalance = ((pe_change - ce_change) / total_change) if total_change > 0 else 0
        
        # Writing intensity (positive change = writing)
        ce_writing = float(self.df[self.df['CE_CHANGE_IN_OI'] > 0]['CE_CHANGE_IN_OI'].sum())
        pe_writing = float(self.df[self.df['PE_CHANGE_IN_OI'] > 0]['PE_CHANGE_IN_OI'].sum())
        
        # Unwinding intensity (negative change = unwinding)
        ce_unwinding = abs(float(self.df[self.df['CE_CHANGE_IN_OI'] < 0]['CE_CHANGE_IN_OI'].sum()))
        pe_unwinding = abs(float(self.df[self.df['PE_CHANGE_IN_OI'] < 0]['PE_CHANGE_IN_OI'].sum()))
        
        # Fresh positioning score
        fresh_score = ((ce_writing + pe_writing) - (ce_unwinding + pe_unwinding)) / total_change if total_change > 0 else 0
        
        self.indicators.update({
            'ce_change_oi': ce_change,
            'pe_change_oi': pe_change,
            'change_oi_imbalance': round(change_imbalance, 3),
            'call_writing_intensity': ce_writing,
            'put_writing_intensity': pe_writing,
            'call_unwinding_intensity': ce_unwinding,
            'put_unwinding_intensity': pe_unwinding,
            'fresh_positioning_score': round(fresh_score, 3)
        })
    
    # ==================== D. VOLUME INDICATORS ====================
    def calculate_volume_indicators(self):
        """Volume indicators"""
        total_ce_vol = float(self.df['CE_VOLUME'].sum())
        total_pe_vol = float(self.df['PE_VOLUME'].sum())
        total_vol = total_ce_vol + total_pe_vol
        
        # Volume imbalance
        vol_imbalance = ((total_pe_vol - total_ce_vol) / total_vol) if total_vol > 0 else 0
        
        # Volume/OI ratio
        total_oi = float(self.df['TOTAL_OI'].sum())
        vol_oi_ratio = total_vol / total_oi if total_oi > 0 else 0
        
        # Volume concentration
        top_vol_strike = float(self.df.loc[self.df['TOTAL_VOLUME'].idxmax(), 'STRIKE'])
        top_vol_conc = float(self.df['TOTAL_VOLUME'].max() / total_vol) if total_vol > 0 else 0
        
        # Volume momentum (volume - SMA)
        self.df['VOL_SMA'] = self.df['TOTAL_VOLUME'].rolling(window=5, min_periods=1).mean()
        vol_momentum = float((self.df['TOTAL_VOLUME'] - self.df['VOL_SMA']).mean())
        
        self.indicators.update({
            'total_ce_volume': total_ce_vol,
            'total_pe_volume': total_pe_vol,
            'total_volume': total_vol,
            'volume_imbalance': round(vol_imbalance, 3),
            'volume_oi_ratio': round(vol_oi_ratio, 3),
            'top_volume_strike': top_vol_strike,
            'volume_concentration': round(top_vol_conc, 3),
            'volume_momentum': round(vol_momentum, 2)
        })
    
    # ==================== E. IV INDICATORS ====================
    def calculate_iv_indicators(self):
        """IV indicators"""
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        atm_ce_iv = float(atm_data.iloc[0]['CE_IV']) if len(atm_data) > 0 else 0
        atm_pe_iv = float(atm_data.iloc[0]['PE_IV']) if len(atm_data) > 0 else 0
        
        # Average IV
        avg_iv = float(self.df[['CE_IV', 'PE_IV']].mean().mean())
        
        # IV difference
        iv_diff = atm_pe_iv - atm_ce_iv
        
        # IV Skew = PE IV - CE IV
        iv_skew = iv_diff
        
        # Call IV skew (OTM CE IV - ATM CE IV)
        otm_ce = self.df[self.df['STRIKE'] > atm]['CE_IV'].mean()
        call_iv_skew = float(otm_ce - atm_ce_iv) if atm_ce_iv > 0 else 0
        
        # Put IV skew (OTM PE IV - ATM PE IV)
        otm_pe = self.df[self.df['STRIKE'] < atm]['PE_IV'].mean()
        put_iv_skew = float(otm_pe - atm_pe_iv) if atm_pe_iv > 0 else 0
        
        # OTM IV
        otm_iv = float((otm_ce + otm_pe) / 2)
        
        self.indicators.update({
            'atm_ce_iv': round(atm_ce_iv, 2),
            'atm_pe_iv': round(atm_pe_iv, 2),
            'average_iv': round(avg_iv, 2),
            'iv_difference': round(iv_diff, 2),
            'iv_skew': round(iv_skew, 2),
            'call_iv_skew': round(call_iv_skew, 2),
            'put_iv_skew': round(put_iv_skew, 2),
            'otm_iv': round(otm_iv, 2)
        })
    
    # ==================== F. MAX PAIN ====================
    def calculate_max_pain(self):
        """Max Pain calculation"""
        strikes = self.df['STRIKE'].values
        pain_data = []
        
        for target in strikes:
            ce_pain = 0
            pe_pain = 0
            for _, row in self.df.iterrows():
                if target > row['STRIKE']:
                    ce_pain += (target - row['STRIKE']) * row['CE_OI']
                if target < row['STRIKE']:
                    pe_pain += (row['STRIKE'] - target) * row['PE_OI']
            
            pain_data.append({
                'strike': float(target),
                'total_pain': ce_pain + pe_pain
            })
        
        pain_df = pd.DataFrame(pain_data)
        max_pain_strike = float(pain_df.loc[pain_df['total_pain'].idxmin(), 'strike'])
        
        # Distance from spot
        distance = max_pain_strike - self.spot
        distance_pct = (distance / self.spot * 100) if self.spot > 0 else 0
        
        self.indicators.update({
            'max_pain_strike': max_pain_strike,
            'max_pain_distance': round(distance, 2),
            'max_pain_distance_pct': round(distance_pct, 2),
            'pain_data': pain_data
        })
    
    # ==================== G. EXPECTED MOVE ====================
    def calculate_expected_move(self):
        """Expected move from ATM straddle"""
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        if len(atm_data) > 0:
            ce_ltp = float(atm_data.iloc[0]['CE_LTP'])
            pe_ltp = float(atm_data.iloc[0]['PE_LTP'])
            
            # Expected move = ATM CE + ATM PE
            expected_move = ce_ltp + pe_ltp
            
            # Upper and lower range
            upper_range = self.spot + expected_move
            lower_range = self.spot - expected_move
            
            expected_move_pct = (expected_move / self.spot * 100) if self.spot > 0 else 0
        else:
            expected_move = 0
            upper_range = self.spot
            lower_range = self.spot
            expected_move_pct = 0
        
        self.indicators.update({
            'expected_move': round(expected_move, 2),
            'upper_expected_range': round(upper_range, 2),
            'lower_expected_range': round(lower_range, 2),
            'expected_move_pct': round(expected_move_pct, 2)
        })
    
    # ==================== H. STRADDLE/STRANGLE ====================
    def calculate_straddle_strangle(self):
        """Straddle and Strangle calculations"""
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        if len(atm_data) > 0:
            atm_ce = float(atm_data.iloc[0]['CE_LTP'])
            atm_pe = float(atm_data.iloc[0]['PE_LTP'])
            atm_straddle = atm_ce + atm_pe
        else:
            atm_straddle = 0
        
        # OTM Strangle (ATM - 100 PE + ATM + 100 CE)
        pe_strike = atm - 100
        ce_strike = atm + 100
        
        pe_data = self.df[self.df['STRIKE'] == pe_strike]
        ce_data = self.df[self.df['STRIKE'] == ce_strike]
        
        strangle_premium = 0
        if len(pe_data) > 0 and len(ce_data) > 0:
            strangle_premium = float(pe_data.iloc[0]['PE_LTP']) + float(ce_data.iloc[0]['CE_LTP'])
        
        self.indicators.update({
            'atm_straddle_premium': round(atm_straddle, 2),
            'otm_strangle_premium': round(strangle_premium, 2)
        })
    
    # ==================== I. LIQUIDITY INDICATORS ====================
    def calculate_liquidity_indicators(self):
        """Liquidity indicators"""
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        if len(atm_data) > 0:
            # Bid-Ask spread approximation (using LTP as proxy)
            ce_ltp = float(atm_data.iloc[0]['CE_LTP'])
            pe_ltp = float(atm_data.iloc[0]['PE_LTP'])
            
            # Spread % (assuming 2% of LTP as spread)
            spread_pct = 2.0  # Placeholder - actual bid/ask data needed
            
            # Liquidity score based on volume
            total_vol = float(self.df['TOTAL_VOLUME'].sum())
            liquidity_score = min(100, round(total_vol / 100000 * 100))
        else:
            spread_pct = 0
            liquidity_score = 0
        
        self.indicators.update({
            'bid_ask_spread_pct': spread_pct,
            'liquidity_score': liquidity_score,
            'volume_oi_ratio': self.indicators.get('volume_oi_ratio', 0)
        })
    
    # ==================== J. OPTION GREEKS ====================
    def calculate_greeks(self):
        """Calculate option Greeks using Black-Scholes"""
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        if len(atm_data) == 0:
            self.indicators.update({
                'delta': 0, 'gamma': 0, 'theta': 0, 'vega': 0, 'rho': 0
            })
            return
        
        # Parameters
        S = self.spot  # Spot price
        K = atm  # Strike price
        r = 0.07  # Risk-free rate (7%)
        T = 7/365  # Time to expiry (7 days)
        sigma = float(atm_data.iloc[0]['CE_IV']) / 100 if atm_data.iloc[0]['CE_IV'] > 1 else float(atm_data.iloc[0]['CE_IV'])
        
        if sigma <= 0:
            sigma = 0.2  # Default 20% IV
        
        # Black-Scholes calculations
        try:
            from scipy.stats import norm
            
            d1 = (np.log(S/K) + (r + sigma**2/2) * T) / (sigma * np.sqrt(T))
            d2 = d1 - sigma * np.sqrt(T)
            
            delta = norm.cdf(d1)
            gamma = norm.pdf(d1) / (S * sigma * np.sqrt(T))
            theta = -(S * norm.pdf(d1) * sigma) / (2 * np.sqrt(T)) - r * K * np.exp(-r*T) * norm.cdf(d2)
            vega = S * norm.pdf(d1) * np.sqrt(T)
            rho = K * T * np.exp(-r*T) * norm.cdf(d2)
        except:
            # Fallback simple calculations
            delta = 0.5
            gamma = 0.01
            theta = -0.5
            vega = 0.1
            rho = 0.01
        
        self.indicators.update({
            'delta': round(delta, 4),
            'gamma': round(gamma, 4),
            'theta': round(theta, 4),
            'vega': round(vega, 4),
            'rho': round(rho, 4)
        })
    
    # ==================== K. ADVANCED INDICATORS ====================
    def calculate_advanced_indicators(self):
        """Advanced derived indicators"""
        # PCR moving average
        self.df['PCR_SMA_5'] = self.df['STRIKE_PCR'].rolling(window=5, min_periods=1).mean()
        
        # OI z-score (cross-sectional)
        oi_mean = self.df['TOTAL_OI'].mean()
        oi_std = self.df['TOTAL_OI'].std()
        if oi_std > 0:
            self.df['OI_ZSCORE'] = (self.df['TOTAL_OI'] - oi_mean) / oi_std
        else:
            self.df['OI_ZSCORE'] = 0
        
        # Volume z-score
        vol_mean = self.df['TOTAL_VOLUME'].mean()
        vol_std = self.df['TOTAL_VOLUME'].std()
        if vol_std > 0:
            self.df['VOL_ZSCORE'] = (self.df['TOTAL_VOLUME'] - vol_mean) / vol_std
        else:
            self.df['VOL_ZSCORE'] = 0
        
        # OI momentum
        self.df['OI_MOMENTUM'] = self.df['TOTAL_OI'].diff()
        
        # PCR momentum
        self.df['PCR_MOMENTUM'] = self.df['STRIKE_PCR'].diff()
        
        self.indicators.update({
            'oi_momentum': float(self.df['OI_MOMENTUM'].sum()),
            'pcr_momentum': float(self.df['PCR_MOMENTUM'].sum()),
            'oi_zscore_mean': float(self.df['OI_ZSCORE'].mean()),
            'vol_zscore_mean': float(self.df['VOL_ZSCORE'].mean())
        })
    
    # ==================== HELPERS ====================
    def _get_atm_strike(self) -> float:
        """Get ATM strike"""
        df = self.df.copy()
        df['_dist'] = abs(df['STRIKE'] - self.spot)
        return float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    
    def get_all(self) -> Dict:
        """Get all indicators"""
        return self.indicators
    
    def get(self, name: str, default=0):
        """Get specific indicator"""
        return self.indicators.get(name, default)
    
    def get_pcr_indicators(self) -> Dict:
        """Get all PCR indicators"""
        pcr_keys = ['pcr_oi', 'pcr_volume', 'pcr_change_oi', 'atm_pcr', 
                   'near_atm_pcr', 'otm_pcr', 'itm_pcr', 'weighted_pcr', 'pcr_momentum']
        return {k: self.indicators.get(k, 0) for k in pcr_keys}
    
    def get_oi_indicators(self) -> Dict:
        """Get all OI indicators"""
        oi_keys = ['total_ce_oi', 'total_pe_oi', 'total_oi', 'ce_oi_pct', 
                  'pe_oi_pct', 'oi_imbalance', 'atm_oi_concentration']
        return {k: self.indicators.get(k, 0) for k in oi_keys}
    
    def get_iv_indicators(self) -> Dict:
        """Get all IV indicators"""
        iv_keys = ['atm_ce_iv', 'atm_pe_iv', 'average_iv', 'iv_skew', 
                  'call_iv_skew', 'put_iv_skew', 'otm_iv']
        return {k: self.indicators.get(k, 0) for k in iv_keys}
    
    def get_support_resistance(self) -> Dict:
        """Get support and resistance levels"""
        support_data = self.df[self.df['STRIKE'] < self.spot].nlargest(2, 'PE_OI')
        resistance_data = self.df[self.df['STRIKE'] > self.spot].nlargest(2, 'CE_OI')
        
        return {
            'support1': float(support_data.iloc[0]['STRIKE']) if len(support_data) > 0 else self.spot - 100,
            'support2': float(support_data.iloc[1]['STRIKE']) if len(support_data) > 1 else self.spot - 200,
            'resistance1': float(resistance_data.iloc[0]['STRIKE']) if len(resistance_data) > 0 else self.spot + 100,
            'resistance2': float(resistance_data.iloc[1]['STRIKE']) if len(resistance_data) > 1 else self.spot + 200
        }