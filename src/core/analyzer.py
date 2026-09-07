"""
📊 Option Chain Analyzer - Interpretation Engine
Interprets indicator values into meaningful signals
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class Analyzer:
    """Interpretation Engine - Converts numbers to signals"""
    
    def __init__(self, data: pd.DataFrame, indicators: Dict, spot_price: float = 0):
        self.df = data.copy()
        self.indicators = indicators if indicators else {}
        self.spot = spot_price if spot_price > 0 else float(data['STRIKE'].iloc[len(data)//2])
        self.analysis = {}
        
        # Run all analyses
        self.analyze_all()
    
    def analyze_all(self):
        """Run all analyses"""
        self.analyze_market_trend()
        self.analyze_oi_interpretation()
        self.analyze_call_put_writing()
        self.analyze_support()
        self.analyze_resistance()
        self.analyze_pcr_interpretation()
        self.analyze_iv_interpretation()
        self.analyze_sentiment()
    
    # ==================== A. MARKET TREND ANALYSIS ====================
    def analyze_market_trend(self) -> Dict:
        """Determine market trend"""
        pcr = self.indicators.get('pcr_oi', 1)
        pcr_change = self.indicators.get('pcr_change_oi', 0)
        oi_imbalance = self.indicators.get('oi_imbalance', 0)
        volume_imbalance = self.indicators.get('volume_imbalance', 0)
        max_pain = self.indicators.get('max_pain_strike', self.spot)
        
        bull_score = 0
        bear_score = 0
        signals = []
        
        # PCR Signal
        if pcr > 1.2:
            bull_score += 20
            signals.append("PCR bullish (Put writers active)")
        elif pcr < 0.7:
            bear_score += 20
            signals.append("PCR bearish (Call writers active)")
        else:
            signals.append("PCR neutral")
        
        # PCR Change Signal
        if pcr_change > 1:
            bull_score += 15
            signals.append("PCR change bullish")
        elif pcr_change < 0.7:
            bear_score += 15
            signals.append("PCR change bearish")
        
        # OI Imbalance
        if oi_imbalance > 0.1:
            bull_score += 15
            signals.append("PE OI dominant (bullish)")
        elif oi_imbalance < -0.1:
            bear_score += 15
            signals.append("CE OI dominant (bearish)")
        
        # Volume Imbalance
        if volume_imbalance > 0.1:
            bull_score += 15
            signals.append("PE volume active (bullish)")
        elif volume_imbalance < -0.1:
            bear_score += 15
            signals.append("CE volume active (bearish)")
        
        # Max Pain
        if max_pain > self.spot:
            bull_score += 15
            signals.append(f"Max Pain ₹{max_pain:,.0f} above spot (bullish)")
        elif max_pain < self.spot:
            bear_score += 15
            signals.append(f"Max Pain ₹{max_pain:,.0f} below spot (bearish)")
        
        # Determine trend
        if bull_score >= 40:
            trend = 'BULLISH'
        elif bear_score >= 40:
            trend = 'BEARISH'
        else:
            trend = 'NEUTRAL'
        
        result = {
            'trend': trend,
            'bull_score': bull_score,
            'bear_score': bear_score,
            'signals': signals
        }
        
        self.analysis['trend'] = result
        return result
    
    # ==================== B. OI INTERPRETATION ====================
    def analyze_oi_interpretation(self) -> Dict:
        """Interpret OI patterns at important strikes"""
        interpretations = []
        
        # Analyze ATM strike
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        if len(atm_data) > 0:
            ce_oi_change = float(atm_data.iloc[0]['CE_CHANGE_IN_OI'])
            pe_oi_change = float(atm_data.iloc[0]['PE_CHANGE_IN_OI'])
            ce_price = float(atm_data.iloc[0]['CE_LTP'])
            pe_price = float(atm_data.iloc[0]['PE_LTP'])
            
            # CE Interpretation at ATM
            if ce_oi_change > 0 and ce_price > 0:
                interpretations.append({
                    'strike': atm,
                    'type': 'CE',
                    'pattern': 'LONG BUILDUP',
                    'signal': 'BULLISH',
                    'detail': f'CE OI +{ce_oi_change:,.0f}, Price ₹{ce_price:.2f}'
                })
            elif ce_oi_change > 0 and ce_price < 0:
                interpretations.append({
                    'strike': atm,
                    'type': 'CE',
                    'pattern': 'SHORT BUILDUP',
                    'signal': 'BEARISH',
                    'detail': f'CE OI +{ce_oi_change:,.0f}, Price ↓'
                })
            elif ce_oi_change < 0 and ce_price > 0:
                interpretations.append({
                    'strike': atm,
                    'type': 'CE',
                    'pattern': 'SHORT COVERING',
                    'signal': 'BULLISH',
                    'detail': f'CE OI {ce_oi_change:,.0f}, Price ↑'
                })
            elif ce_oi_change < 0 and ce_price < 0:
                interpretations.append({
                    'strike': atm,
                    'type': 'CE',
                    'pattern': 'LONG UNWINDING',
                    'signal': 'BEARISH',
                    'detail': f'CE OI {ce_oi_change:,.0f}, Price ↓'
                })
            
            # PE Interpretation at ATM
            if pe_oi_change > 0 and pe_price > 0:
                interpretations.append({
                    'strike': atm,
                    'type': 'PE',
                    'pattern': 'SHORT BUILDUP',
                    'signal': 'BEARISH',
                    'detail': f'PE OI +{pe_oi_change:,.0f}, Price ↑'
                })
            elif pe_oi_change > 0 and pe_price < 0:
                interpretations.append({
                    'strike': atm,
                    'type': 'PE',
                    'pattern': 'LONG BUILDUP',
                    'signal': 'BULLISH',
                    'detail': f'PE OI +{pe_oi_change:,.0f}, Price ↓'
                })
        
        self.analysis['oi_interpretation'] = interpretations
        return {'interpretations': interpretations}
    
    # ==================== C. CALL/PUT WRITING ANALYSIS ====================
    def analyze_call_put_writing(self) -> Dict:
        """Analyze call/put writing intensity"""
        ce_writing = self.indicators.get('call_writing_intensity', 0)
        pe_writing = self.indicators.get('put_writing_intensity', 0)
        ce_unwinding = self.indicators.get('call_unwinding_intensity', 0)
        pe_unwinding = self.indicators.get('put_unwinding_intensity', 0)
        
        # Intensity function
        def get_intensity(value, total):
            if total == 0:
                return 'NONE'
            ratio = value / total
            if ratio > 0.6:
                return 'VERY STRONG'
            elif ratio > 0.4:
                return 'STRONG'
            elif ratio > 0.2:
                return 'MODERATE'
            else:
                return 'WEAK'
        
        total_change = ce_writing + pe_writing + ce_unwinding + pe_unwinding
        
        result = {
            'call_writing': {
                'value': ce_writing,
                'intensity': get_intensity(ce_writing, total_change),
                'signal': 'BEARISH' if ce_writing > pe_writing else 'NEUTRAL'
            },
            'put_writing': {
                'value': pe_writing,
                'intensity': get_intensity(pe_writing, total_change),
                'signal': 'BULLISH' if pe_writing > ce_writing else 'NEUTRAL'
            },
            'call_unwinding': {
                'value': ce_unwinding,
                'intensity': get_intensity(ce_unwinding, total_change),
                'signal': 'BULLISH' if ce_unwinding > pe_unwinding else 'NEUTRAL'
            },
            'put_unwinding': {
                'value': pe_unwinding,
                'intensity': get_intensity(pe_unwinding, total_change),
                'signal': 'BEARISH' if pe_unwinding > ce_unwinding else 'NEUTRAL'
            }
        }
        
        self.analysis['writing_analysis'] = result
        return result
    
    # ==================== D. SUPPORT ANALYSIS ====================
    def analyze_support(self) -> Dict:
        """Calculate support levels with strength scores"""
        supports = []
        
        # Get PE OI based support candidates
        support_candidates = self.df[self.df['STRIKE'] < self.spot].nlargest(5, 'PE_OI')
        
        max_pe_oi = float(self.df['PE_OI'].max())
        max_pe_change = float(self.df['PE_CHANGE_IN_OI'].max())
        max_pe_vol = float(self.df['PE_VOLUME'].max())
        
        for _, row in support_candidates.iterrows():
            strike = float(row['STRIKE'])
            pe_oi = float(row['PE_OI'])
            pe_change = float(row.get('PE_CHANGE_IN_OI', 0))
            pe_vol = float(row['PE_VOLUME'])
            distance = self.spot - strike
            
            # Strength factors
            oi_strength = (pe_oi / max_pe_oi) * 35 if max_pe_oi > 0 else 0
            change_strength = (max(0, pe_change) / max_pe_change) * 25 if max_pe_change > 0 else 0
            volume_strength = (pe_vol / max_pe_vol) * 15 if max_pe_vol > 0 else 0
            writing_strength = 15 if pe_change > 0 else 0
            distance_strength = max(0, 10 - (distance / 100)) if distance < 1000 else 0
            
            total_strength = min(100, round(oi_strength + change_strength + volume_strength + writing_strength + distance_strength))
            
            supports.append({
                'strike': strike,
                'strength': total_strength,
                'pe_oi': pe_oi,
                'pe_change': pe_change,
                'pe_volume': pe_vol,
                'distance': round(distance, 0),
                'breakdown': {
                    'oi_strength': round(oi_strength, 1),
                    'change_strength': round(change_strength, 1),
                    'volume_strength': round(volume_strength, 1),
                    'writing_strength': writing_strength,
                    'distance_strength': round(distance_strength, 1)
                }
            })
        
        # Sort by strength
        supports = sorted(supports, key=lambda x: x['strength'], reverse=True)
        
        self.analysis['supports'] = supports
        return {'supports': supports, 'strongest': supports[0] if supports else None}
    
    # ==================== E. RESISTANCE ANALYSIS ====================
    def analyze_resistance(self) -> Dict:
        """Calculate resistance levels with strength scores"""
        resistances = []
        
        resistance_candidates = self.df[self.df['STRIKE'] > self.spot].nlargest(5, 'CE_OI')
        
        max_ce_oi = float(self.df['CE_OI'].max())
        max_ce_change = float(self.df['CE_CHANGE_IN_OI'].max())
        max_ce_vol = float(self.df['CE_VOLUME'].max())
        
        for _, row in resistance_candidates.iterrows():
            strike = float(row['STRIKE'])
            ce_oi = float(row['CE_OI'])
            ce_change = float(row.get('CE_CHANGE_IN_OI', 0))
            ce_vol = float(row['CE_VOLUME'])
            distance = strike - self.spot
            
            oi_strength = (ce_oi / max_ce_oi) * 35 if max_ce_oi > 0 else 0
            change_strength = (max(0, ce_change) / max_ce_change) * 25 if max_ce_change > 0 else 0
            volume_strength = (ce_vol / max_ce_vol) * 15 if max_ce_vol > 0 else 0
            writing_strength = 15 if ce_change > 0 else 0
            distance_strength = max(0, 10 - (distance / 100)) if distance < 1000 else 0
            
            total_strength = min(100, round(oi_strength + change_strength + volume_strength + writing_strength + distance_strength))
            
            resistances.append({
                'strike': strike,
                'strength': total_strength,
                'ce_oi': ce_oi,
                'ce_change': ce_change,
                'ce_volume': ce_vol,
                'distance': round(distance, 0),
                'breakdown': {
                    'oi_strength': round(oi_strength, 1),
                    'change_strength': round(change_strength, 1),
                    'volume_strength': round(volume_strength, 1),
                    'writing_strength': writing_strength,
                    'distance_strength': round(distance_strength, 1)
                }
            })
        
        resistances = sorted(resistances, key=lambda x: x['strength'], reverse=True)
        
        self.analysis['resistances'] = resistances
        return {'resistances': resistances, 'strongest': resistances[0] if resistances else None}
    
    # ==================== PCR INTERPRETATION ====================
    def analyze_pcr_interpretation(self) -> Dict:
        """Interpret PCR values"""
        pcr = self.indicators.get('pcr_oi', 1)
        pcr_change = self.indicators.get('pcr_change_oi', 0)
        pcr_vol = self.indicators.get('pcr_volume', 1)
        
        if pcr > 1.5:
            pcr_signal = 'STRONGLY BULLISH'
            pcr_detail = 'Put writers bahut active, strong support'
        elif pcr > 1.2:
            pcr_signal = 'BULLISH'
            pcr_detail = 'Put writers active, support building'
        elif pcr >= 0.7:
            pcr_signal = 'NEUTRAL'
            pcr_detail = 'Balanced market'
        elif pcr >= 0.5:
            pcr_signal = 'BEARISH'
            pcr_detail = 'Call writers active, resistance building'
        else:
            pcr_signal = 'STRONGLY BEARISH'
            pcr_detail = 'Call writers bahut active, strong resistance'
        
        result = {
            'pcr': pcr,
            'pcr_signal': pcr_signal,
            'pcr_detail': pcr_detail,
            'pcr_change': pcr_change,
            'pcr_volume': pcr_vol
        }
        
        self.analysis['pcr_interpretation'] = result
        return result
    
    # ==================== IV INTERPRETATION ====================
    def analyze_iv_interpretation(self) -> Dict:
        """Interpret IV values"""
        atm_iv = self.indicators.get('atm_ce_iv', 0)
        iv_skew = self.indicators.get('iv_skew', 0)
        
        if atm_iv > 30:
            iv_regime = 'HIGH VOLATILITY'
            iv_signal = 'Premium expensive, straddle avoid'
        elif atm_iv > 15:
            iv_regime = 'MODERATE VOLATILITY'
            iv_signal = 'Normal premium levels'
        else:
            iv_regime = 'LOW VOLATILITY'
            iv_signal = 'Premium cheap, straddle favorable'
        
        if iv_skew > 2:
            skew_signal = 'Put IV > Call IV → Downside fear'
        elif iv_skew < -2:
            skew_signal = 'Call IV > Put IV → Upside expectation'
        else:
            skew_signal = 'Balanced IV'
        
        result = {
            'atm_iv': atm_iv,
            'iv_regime': iv_regime,
            'iv_signal': iv_signal,
            'iv_skew': iv_skew,
            'skew_signal': skew_signal
        }
        
        self.analysis['iv_interpretation'] = result
        return result
    
    # ==================== SENTIMENT ====================
    def analyze_sentiment(self) -> Dict:
        """Final sentiment analysis"""
        trend = self.analysis.get('trend', {}).get('trend', 'NEUTRAL')
        pcr_signal = self.analysis.get('pcr_interpretation', {}).get('pcr_signal', 'NEUTRAL')
        
        bull_score = 0
        bear_score = 0
        factors = []
        
        # Trend
        if trend == 'BULLISH':
            bull_score += 25
            factors.append({'name': 'Trend', 'signal': 'BULLISH'})
        elif trend == 'BEARISH':
            bear_score += 25
            factors.append({'name': 'Trend', 'signal': 'BEARISH'})
        else:
            factors.append({'name': 'Trend', 'signal': 'NEUTRAL'})
        
        # PCR
        if 'BULLISH' in pcr_signal:
            bull_score += 25
            factors.append({'name': 'PCR', 'signal': 'BULLISH'})
        elif 'BEARISH' in pcr_signal:
            bear_score += 25
            factors.append({'name': 'PCR', 'signal': 'BEARISH'})
        else:
            factors.append({'name': 'PCR', 'signal': 'NEUTRAL'})
        
        # Writing analysis
        writing = self.analysis.get('writing_analysis', {})
        put_writing = writing.get('put_writing', {})
        call_writing = writing.get('call_writing', {})
        
        if put_writing.get('intensity', 'NONE') in ['STRONG', 'VERY STRONG']:
            bull_score += 25
            factors.append({'name': 'Put Writing', 'signal': 'BULLISH'})
        elif call_writing.get('intensity', 'NONE') in ['STRONG', 'VERY STRONG']:
            bear_score += 25
            factors.append({'name': 'Call Writing', 'signal': 'BEARISH'})
        
        # Support/Resistance
        supports = self.analysis.get('supports', [])
        resistances = self.analysis.get('resistances', [])
        
        if supports and resistances:
            if supports[0]['strength'] > resistances[0]['strength']:
                bull_score += 25
                factors.append({'name': 'S/R', 'signal': 'BULLISH'})
            else:
                bear_score += 25
                factors.append({'name': 'S/R', 'signal': 'BEARISH'})
        
        if bull_score > bear_score:
            sentiment = 'BULLISH'
        elif bear_score > bull_score:
            sentiment = 'BEARISH'
        else:
            sentiment = 'NEUTRAL'
        
        result = {
            'sentiment': sentiment,
            'bull_score': bull_score,
            'bear_score': bear_score,
            'confidence': max(bull_score, bear_score),
            'factors': factors
        }
        
        self.analysis['sentiment'] = result
        return result
    
    # ==================== HELPERS ====================
    def _get_atm_strike(self) -> float:
        """Get ATM strike"""
        df = self.df.copy()
        df['_dist'] = abs(df['STRIKE'] - self.spot)
        return float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    
    def get_all(self) -> Dict:
        """Get all analysis"""
        return self.analysis
    
    def get_trend(self) -> str:
        """Get market trend"""
        return self.analysis.get('trend', {}).get('trend', 'NEUTRAL')
    
    def get_sentiment(self) -> Dict:
        """Get sentiment"""
        return self.analysis.get('sentiment', {})
    
    def get_supports(self) -> List[Dict]:
        """Get support levels"""
        return self.analysis.get('supports', [])
    
    def get_resistances(self) -> List[Dict]:
        """Get resistance levels"""
        return self.analysis.get('resistances', [])
    
    def get_writing_analysis(self) -> Dict:
        """Get writing analysis"""
        return self.analysis.get('writing_analysis', {})
