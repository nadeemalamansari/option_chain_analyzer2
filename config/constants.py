"""
Constants used across the application
"""

# Exchange types
EXCHANGE_TYPES = ['NSE', 'BSE']

# Option types
OPTION_TYPES = ['CE', 'PE']

# Timeframes
TIMEFRAMES = ['Intraday', 'Daily', 'Weekly', 'Monthly']

# Indicator thresholds
PCR_OVERSOLD_THRESHOLD = 0.5
PCR_OVERBOUGHT_THRESHOLD = 1.5
HIGH_OI_THRESHOLD = 0.7  # 70th percentile
LOW_OI_THRESHOLD = 0.3   # 30th percentile

# Recommendation thresholds
STRONG_SUPPORT_WEIGHT = 0.8
STRONG_RESISTANCE_WEIGHT = 0.8
MAX_RISK_REWARD_RATIO = 3.0
MIN_RISK_REWARD_RATIO = 1.5

# File paths
RAW_DATA_PATH = 'data/raw'
PROCESSED_DATA_PATH = 'data/processed'
OUTPUT_PATH = 'data/output'
REPORTS_PATH = 'reports'