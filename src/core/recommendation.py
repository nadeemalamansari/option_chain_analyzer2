"""
🚦 Complete Recommendation Engine - 100-Point Model
All 11 Factors with Proper Weighting
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
import logging
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RecommendationEngine:
    """Complete 100-Point Weighted Recommendation Engine"""
    
    def __init__(self, data: pd.DataFrame, analysis: Dict = None, spot_price: float = 0):
        self.df = data.copy()
        self.analysis = analysis if analysis else {}
        self.spot = spot_price if spot_price > 0 else float(data['STRIKE'].iloc[len(data)//2])
        self.bull_score = 0
        self.bear_score = 0
        self.factor_details = []
        self.final_output = {}
        
        # Run all calculations
        self._run_all()
    
    def _run_all(self):
        """Run all scoring factors"""
        self._score_oi_positioning()       # 20 points
        self._score_change_oi()             # 20 points
        self._score_ltp_oi_relationship()   # 15 points
        self._score_support_resistance()    # 15 points
        self._score_pcr()                   # 10 points
        self._score_volume()                # 8 points
        self._score_iv()                    # 7 points
        self._score_max_pain()              # 5 points
        self._apply_liquidity_filter()
        self._generate_final_signal()
    
    # ============ 1. OI POSITIONING (20 points) ============
    def _score_oi_positioning(self):
        ce_oi = float(self.df['CE_OI'].sum())
        pe_oi = float(self.df['PE_OI'].sum())
        total_oi = ce_oi + pe_oi
        
        # OI Imbalance
        oi_imbalance = (pe_oi - ce_oi) / total_oi if total_oi > 0 else 0
        
        # OI Concentration around ATM
        atm = self._get_atm_strike()
        atm_range = self.df[(self.df['STRIKE'] >= atm - 200) & (self.df['STRIKE'] <= atm + 200)]
        atm_conc = float(atm_range['TOTAL_OI'].sum() / total_oi) if total_oi > 0 else 0
        
        if oi_imbalance > 0.15:
            self.bull_score += 20
            self.factor_details.append({
                'factor': 'OI Positioning', 'signal': 'BULLISH', 'score': 20,
                'detail': f'PE OI {pe_oi:,.0f} >> CE OI {ce_oi:,.0f} - Put writers dominant'
            })
        elif oi_imbalance < -0.15:
            self.bear_score += 20
            self.factor_details.append({
                'factor': 'OI Positioning', 'signal': 'BEARISH', 'score': 20,
                'detail': f'CE OI {ce_oi:,.0f} >> PE OI {pe_oi:,.0f} - Call writers dominant'
            })
        elif oi_imbalance > 0.05:
            self.bull_score += 12
            self.factor_details.append({
                'factor': 'OI Positioning', 'signal': 'BULLISH', 'score': 12,
                'detail': 'PE OI slightly higher'
            })
        elif oi_imbalance < -0.05:
            self.bear_score += 12
            self.factor_details.append({
                'factor': 'OI Positioning', 'signal': 'BEARISH', 'score': 12,
                'detail': 'CE OI slightly higher'
            })
        else:
            self.bull_score += 6
            self.bear_score += 6
            self.factor_details.append({
                'factor': 'OI Positioning', 'signal': 'NEUTRAL', 'score': 0,
                'detail': 'OI balanced'
            })
    
    # ============ 2. CHANGE IN OI (20 points) ============
    def _score_change_oi(self):
        ce_change = float(self.df['CE_CHANGE_IN_OI'].sum())
        pe_change = float(self.df['PE_CHANGE_IN_OI'].sum())
        
        if pe_change > 0 and ce_change < 0:
            self.bull_score += 20
            self.factor_details.append({
                'factor': 'Change OI', 'signal': 'BULLISH', 'score': 20,
                'detail': f'PE Buildup +{pe_change:,.0f} + CE Unwinding {ce_change:,.0f}'
            })
        elif ce_change > 0 and pe_change < 0:
            self.bear_score += 20
            self.factor_details.append({
                'factor': 'Change OI', 'signal': 'BEARISH', 'score': 20,
                'detail': f'CE Buildup +{ce_change:,.0f} + PE Unwinding {pe_change:,.0f}'
            })
        elif pe_change > 0:
            self.bull_score += 12
            self.factor_details.append({
                'factor': 'Change OI', 'signal': 'BULLISH', 'score': 12,
                'detail': f'PE Buildup +{pe_change:,.0f}'
            })
        elif ce_change > 0:
            self.bear_score += 12
            self.factor_details.append({
                'factor': 'Change OI', 'signal': 'BEARISH', 'score': 12,
                'detail': f'CE Buildup +{ce_change:,.0f}'
            })
        else:
            self.factor_details.append({
                'factor': 'Change OI', 'signal': 'NEUTRAL', 'score': 0,
                'detail': 'No significant change'
            })
    
    # ============ 3. LTP + OI RELATIONSHIP (15 points) ============
    def _score_ltp_oi_relationship(self):
        atm = self._get_atm_strike()
        atm_data = self.df[self.df['STRIKE'] == atm]
        
        if len(atm_data) == 0:
            return
        
        ce_ltp = float(atm_data.iloc[0]['CE_LTP'])
        pe_ltp = float(atm_data.iloc[0]['PE_LTP'])
        ce_chg = float(atm_data.iloc[0].get('CE_CHANGE_IN_OI', 0))
        pe_chg = float(atm_data.iloc[0].get('PE_CHANGE_IN_OI', 0))
        
        # CE Pattern
        if ce_chg > 0 and ce_ltp > 0:
            ce_pattern = 'Long Buildup'
            ce_bull = True
            self.bull_score += 8
        elif ce_chg > 0 and ce_ltp <= 0:
            ce_pattern = 'Short Buildup'
            ce_bull = False
            self.bear_score += 8
        elif ce_chg < 0 and ce_ltp > 0:
            ce_pattern = 'Short Covering'
            ce_bull = True
            self.bull_score += 5
        elif ce_chg < 0 and ce_ltp <= 0:
            ce_pattern = 'Long Unwinding'
            ce_bull = False
            self.bear_score += 5
        else:
            ce_pattern = 'No Activity'
            ce_bull = None
        
        # PE Pattern
        if pe_chg > 0 and pe_ltp < 0:
            pe_pattern = 'Long Buildup'
            pe_bull = True
            self.bull_score += 7
        elif pe_chg > 0 and pe_ltp >= 0:
            pe_pattern = 'Short Buildup'
            pe_bull = False
            self.bear_score += 7
        elif pe_chg < 0 and pe_ltp < 0:
            pe_pattern = 'Short Covering'
            pe_bull = True
            self.bull_score += 4
        elif pe_chg < 0 and pe_ltp >= 0:
            pe_pattern = 'Long Unwinding'
            pe_bull = False
            self.bear_score += 4
        else:
            pe_pattern = 'No Activity'
            pe_bull = None
        
        self.factor_details.append({
            'factor': 'LTP+OI', 'signal': 'MIXED', 'score': 15,
            'detail': f'CE: {ce_pattern} | PE: {pe_pattern}'
        })
    
    # ============ 4. SUPPORT/RESISTANCE (15 points) ============
    def _score_support_resistance(self):
        supports = self.analysis.get('supports', [])
        resistances = self.analysis.get('resistances', [])
        
        if supports and resistances:
            s_strength = supports[0].get('strength', 0)
            r_strength = resistances[0].get('strength', 0)
            
            if s_strength > r_strength + 10:
                self.bull_score += 15
                self.factor_details.append({
                    'factor': 'S/R', 'signal': 'BULLISH', 'score': 15,
                    'detail': f'Support {s_strength} > Resistance {r_strength}'
                })
            elif r_strength > s_strength + 10:
                self.bear_score += 15
                self.factor_details.append({
                    'factor': 'S/R', 'signal': 'BEARISH', 'score': 15,
                    'detail': f'Resistance {r_strength} > Support {s_strength}'
                })
            else:
                self.bull_score += 7
                self.bear_score += 7
                self.factor_details.append({
                    'factor': 'S/R', 'signal': 'NEUTRAL', 'score': 0,
                    'detail': 'S/R balanced'
                })
    
    # ============ 5. PCR (10 points) ============
    def _score_pcr(self):
        pcr = self.analysis.get('pcr_oi', 1)
        
        if pcr > 1.5:
            self.bull_score += 10
            self.factor_details.append({
                'factor': 'PCR', 'signal': 'STRONG BULLISH', 'score': 10,
                'detail': f'PCR {pcr:.2f}'
            })
        elif pcr > 1.2:
            self.bull_score += 8
            self.factor_details.append({
                'factor': 'PCR', 'signal': 'BULLISH', 'score': 8,
                'detail': f'PCR {pcr:.2f}'
            })
        elif pcr < 0.5:
            self.bear_score += 10
            self.factor_details.append({
                'factor': 'PCR', 'signal': 'STRONG BEARISH', 'score': 10,
                'detail': f'PCR {pcr:.2f}'
            })
        elif pcr < 0.7:
            self.bear_score += 8
            self.factor_details.append({
                'factor': 'PCR', 'signal': 'BEARISH', 'score': 8,
                'detail': f'PCR {pcr:.2f}'
            })
        else:
            self.factor_details.append({
                'factor': 'PCR', 'signal': 'NEUTRAL', 'score': 0,
                'detail': f'PCR {pcr:.2f}'
            })
    
    # ============ 6. VOLUME (8 points) ============
    def _score_volume(self):
        ce_vol = float(self.df['CE_VOLUME'].sum())
        pe_vol = float(self.df['PE_VOLUME'].sum())
        
        if pe_vol > ce_vol * 1.3:
            self.bull_score += 8
            self.factor_details.append({
                'factor': 'Volume', 'signal': 'BULLISH', 'score': 8,
                'detail': f'PE Vol {pe_vol:,.0f} >> CE Vol'
            })
        elif ce_vol > pe_vol * 1.3:
            self.bear_score += 8
            self.factor_details.append({
                'factor': 'Volume', 'signal': 'BEARISH', 'score': 8,
                'detail': f'CE Vol {ce_vol:,.0f} >> PE Vol'
            })
        else:
            self.factor_details.append({
                'factor': 'Volume', 'signal': 'NEUTRAL', 'score': 0,
                'detail': 'Volume balanced'
            })
    
    # ============ 7. IV (7 points) ============
    def _score_iv(self):
        iv_skew = self.analysis.get('iv_skew', 0)
        
        if iv_skew > 3:
            self.bull_score += 7
            self.factor_details.append({
                'factor': 'IV Skew', 'signal': 'BULLISH', 'score': 7,
                'detail': f'PE IV > CE IV by {iv_skew:.1f}'
            })
        elif iv_skew < -3:
            self.bear_score += 7
            self.factor_details.append({
                'factor': 'IV Skew', 'signal': 'BEARISH', 'score': 7,
                'detail': f'CE IV > PE IV by {abs(iv_skew):.1f}'
            })
        else:
            self.factor_details.append({
                'factor': 'IV', 'signal': 'NEUTRAL', 'score': 0,
                'detail': 'IV balanced'
            })
    
    # ============ 8. MAX PAIN (5 points) ============
    def _score_max_pain(self):
        max_pain = self.analysis.get('max_pain_strike', self.spot)
        
        if max_pain > self.spot:
            self.bull_score += 5
            self.factor_details.append({
                'factor': 'Max Pain', 'signal': 'BULLISH', 'score': 5,
                'detail': f'₹{max_pain:,.0f} above spot'
            })
        elif max_pain < self.spot:
            self.bear_score += 5
            self.factor_details.append({
                'factor': 'Max Pain', 'signal': 'BEARISH', 'score': 5,
                'detail': f'₹{max_pain:,.0f} below spot'
            })
    
    # ============ LIQUIDITY FILTER ============
    def _apply_liquidity_filter(self):
        self.liquidity_pass = True
        self.liquidity_reasons = []
        
        liquidity = self.analysis.get('liquidity_score', 50)
        if liquidity < 20:
            self.liquidity_pass = False
            self.liquidity_reasons.append(f'Low liquidity ({liquidity}/100)')
        
        spread = self.analysis.get('bid_ask_spread_pct', 0)
        if spread > 5:
            self.liquidity_pass = False
            self.liquidity_reasons.append(f'Wide spread ({spread:.0f}%)')
    
    # ============ FINAL SIGNAL ============
    def _generate_final_signal(self):
        confidence = max(self.bull_score, self.bear_score)
        
        if self.bull_score >= 50 and self.bull_score > self.bear_score:
            direction = 'BULLISH'
            signal = 'BUY CE'
        elif self.bear_score >= 50 and self.bear_score > self.bull_score:
            direction = 'BEARISH'
            signal = 'BUY PE'
        else:
            direction = 'NEUTRAL'
            signal = 'NO TRADE'
        
        if not self.liquidity_pass and signal in ['BUY CE', 'BUY PE']:
            signal = 'WAIT FOR CONFIRMATION'
        
        self.final_output = {
            'signal': signal,
            'direction': direction,
            'confidence': confidence,
            'bull_score': self.bull_score,
            'bear_score': self.bear_score,
            'factor_details': self.factor_details,
            'liquidity_pass': self.liquidity_pass,
            'liquidity_reasons': self.liquidity_reasons,
            'timestamp': datetime.now()
        }
    
    # ============ HELPERS ============
    def _get_atm_strike(self) -> float:
        df = self.df.copy()
        df['_dist'] = abs(df['STRIKE'] - self.spot)
        return float(df.loc[df['_dist'].idxmin(), 'STRIKE'])
    
    def get_final_output(self) -> Dict:
        return self.final_output
    
    def get_signal(self) -> str:
        return self.final_output.get('signal', 'NO TRADE')
    
    def get_direction(self) -> str:
        return self.final_output.get('direction', 'NEUTRAL')
    
    def get_confidence(self) -> float:
        return self.final_output.get('confidence', 0)
    
    def get_bull_score(self) -> float:
        return self.bull_score
    
    def get_bear_score(self) -> float:
        return self.bear_score
    
    def get_factor_details(self) -> List:
        return self.factor_details
    
    def get_signal_display(self) -> Dict:
        direction = self.get_direction()
        signal = self.get_signal()
        
        if direction == 'BULLISH':
            emoji = '🟢'
            color = '#27ae60'
        elif direction == 'BEARISH':
            emoji = '🔴'
            color = '#e74c3c'
        else:
            emoji = '🟡'
            color = '#f39c12'
        
        return {'emoji': emoji, 'signal': signal, 'direction': direction, 'color': color}
    
    def print_report(self):
        """Print complete report"""
        print("=" * 60)
        print("TRADE RECOMMENDATION REPORT")
        print("=" * 60)
        print(f"Signal: {self.get_signal()}")
        print(f"Direction: {self.get_direction()}")
        print(f"Bull Score: {self.bull_score}/100")
        print(f"Bear Score: {self.bear_score}/100")
        print(f"Confidence: {self.get_confidence()}/100")
        print()
        print("FACTORS:")
        for f in self.factor_details:
            print(f"  {f['factor']}: {f['signal']} (+{f['score']}) - {f['detail']}")
        print("=" * 60)