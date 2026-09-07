"""
Application settings and configurations
"""

import os
from pathlib import Path

# Base directory
BASE_DIR = Path(__file__).parent.parent

# Data directories
RAW_DATA_DIR = BASE_DIR / 'data' / 'raw'
PROCESSED_DATA_DIR = BASE_DIR / 'data' / 'processed'
OUTPUT_DIR = BASE_DIR / 'data' / 'output'

# Reports directories
HTML_REPORTS_DIR = BASE_DIR / 'reports' / 'html_reports'
EXCEL_REPORTS_DIR = BASE_DIR / 'reports' / 'excel_reports'

# Create directories if they don't exist
for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, OUTPUT_DIR, 
                  HTML_REPORTS_DIR, EXCEL_REPORTS_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Streamlit settings
STREAMLIT_TITLE = "Option Chain Analyzer"
STREAMLIT_ICON = "📊"

# Visualization settings
CHART_HEIGHT = 500
CHART_WIDTH = 800
COLOR_PALETTE = {
    'CE': '#4CAF50',  # Green for Call
    'PE': '#F44336',  # Red for Put
    'OI': '#2196F3',  # Blue for OI
    'PCR': '#FF9800',  # Orange for PCR
    'Support': '#4CAF50',
    'Resistance': '#F44336',
    'Neutral': '#9E9E9E'
}

# Analysis settings
STRIKE_RANGE_PERCENT = 10  # Percentage range around spot price
MAX_STRIKES_DISPLAY = 20   # Maximum strikes to display
MIN_VOLUME_THRESHOLD = 100 # Minimum volume for consideration