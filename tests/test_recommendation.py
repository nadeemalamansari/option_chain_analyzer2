"""
Tests for Recommendation Engine
"""

import unittest
import pandas as pd
import numpy as np
import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from src.core.recommendation import RecommendationEngine
from src.core.analyzer import OptionChainAnalyzer


class TestRecommendationEngine(unittest.TestCase):
    """Test cases for RecommendationEngine"""
    
    def setUp(self):
        """Set up test data"""
        # Create sample option chain data
        strikes = np.arange(19500, 20501, 50)
        
        self.spot_price = 20000
        
        data = {
            'STRIKE': strikes,
            'CE_OI': np.random.randint(1000, 10000, len(strikes)),
            'PE_OI': np.random.randint(1000, 10000, len(strikes)),
            'CE_CHANGE_IN_OI': np.random.randint(-500, 500, len(strikes)),
            'PE_CHANGE_IN_OI': np.random.randint(-500, 500, len(strikes)),
            'CE_VOLUME': np.random.randint(100, 5000, len(strikes)),
            'PE_VOLUME': np.random.randint(100, 5000, len(strikes)),
            'CE_LTP': np.random.uniform(1, 500, len(strikes)),
            'PE_LTP': np.random.uniform(1, 500, len(strikes)),
            'CE_IV': np.random.uniform(0.1, 0.4, len(strikes)),
            'PE_IV': np.random.uniform(0.1, 0.4, len(strikes))
        }
        
        self.data = pd.DataFrame(data)
        self.data['TOTAL_OI'] = self.data['CE_OI'] + self.data['PE_OI']
        self.data['STRIKE_PCR'] = self.data['PE_OI'] / self.data['CE_OI']
        
        # Create analyzer and get analysis results
        analyzer = OptionChainAnalyzer(self.data, self.spot_price)
        self.analysis_results = analyzer.get_complete_analysis()
        
        # Create recommendation engine
        self.rec_engine = RecommendationEngine(
            self.data,
            self.spot_price,
            self.analysis_results
        )
    
    def test_generate_recommendations(self):
        """Test generating recommendations"""
        recommendations = self.rec_engine.generate_recommendations()
        
        self.assertIsNotNone(recommendations)
        self.assertIsInstance(recommendations, list)
        
        if recommendations:
            for rec in recommendations:
                self.assertIn('type', rec)
                self.assertIn('strategy', rec)
                self.assertIn('strike', rec)
                self.assertIn('confidence', rec)
                self.assertIn('reason', rec)
                self.assertIn('risk_level', rec)
    
    def test_get_top_recommendations(self):
        """Test getting top recommendations"""
        top_recommendations = self.rec_engine.get_top_recommendations(3)
        
        self.assertIsNotNone(top_recommendations)
        self.assertLessEqual(len(top_recommendations), 3)
    
    def test_get_recommendations_by_type(self):
        """Test filtering recommendations by type"""
        buy_recommendations = self.rec_engine.get_recommendations_by_type('BUY')
        
        self.assertIsNotNone(buy_recommendations)
        
        for rec in buy_recommendations:
            self.assertEqual(rec['type'], 'BUY')
    
    def test_get_risk_summary(self):
        """Test getting risk summary"""
        risk_summary = self.rec_engine.get_risk_summary()
        
        self.assertIsNotNone(risk_summary)
        self.assertIn('LOW', risk_summary)
        self.assertIn('MEDIUM', risk_summary)
        self.assertIn('HIGH', risk_summary)


class TestOptionChainAnalyzer(unittest.TestCase):
    """Test cases for OptionChainAnalyzer"""
    
    def setUp(self):
        """Set up test data"""
        strikes = np.arange(19500, 20501, 50)
        self.spot_price = 20000
        
        data = {
            'STRIKE': strikes,
            'CE_OI': np.random.randint(1000, 10000, len(strikes)),
            'PE_OI': np.random.randint(1000, 10000, len(strikes)),
            'CE_VOLUME': np.random.randint(100, 5000, len(strikes)),
            'PE_VOLUME': np.random.randint(100, 5000, len(strikes))
        }
        
        self.data = pd.DataFrame(data)
        self.data['TOTAL_OI'] = self.data['CE_OI'] + self.data['PE_OI']
        
        self.analyzer = OptionChainAnalyzer(self.data, self.spot_price)
    
    def test_analyze_support_resistance(self):
        """Test support/resistance analysis"""
        result = self.analyzer.analyze_support_resistance()
        
        self.assertIsNotNone(result)
        self.assertIn('support', result)
        self.assertIn('resistance', result)
    
    def test_calculate_pcr(self):
        """Test PCR calculation"""
        result = self.analyzer.calculate_pcr()
        
        self.assertIsNotNone(result)
        self.assertIn('oi_pcr', result)
        self.assertIn('volume_pcr', result)
        
        # PCR should be positive
        self.assertGreaterEqual(result['oi_pcr'], 0)
    
    def test_find_max_pain(self):
        """Test max pain calculation"""
        max_pain = self.analyzer.find_max_pain()
        
        self.assertIsNotNone(max_pain)
        self.assertGreater(max_pain, 0)
    
    def test_get_complete_analysis(self):
        """Test complete analysis"""
        analysis = self.analyzer.get_complete_analysis()
        
        self.assertIsNotNone(analysis)
        self.assertIn('support_resistance', analysis)
        self.assertIn('pcr', analysis)
        self.assertIn('max_pain', analysis)
        self.assertIn('oi_concentration', analysis)
        self.assertIn('buildup', analysis)


if __name__ == '__main__':
    unittest.main()