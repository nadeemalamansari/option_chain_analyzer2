"""
PCR Test Script - Terminal
"""

import pandas as pd
import numpy as np

print("=" * 60)
print("PCR CALCULATION TEST")
print("=" * 60)

# File path
file_path = 'data/raw/option-chain-ED-ASIANPAINT-18-Aug-2026.csv'

# Read BSE file
df = pd.read_csv(file_path, skiprows=2, on_bad_lines='skip')
df = df.dropna(how='all')
df = df.dropna(axis=1, how='all')

print(f"\nShape: {df.shape}")
print(f"Total Columns: {len(df.columns)}")

# ✅ Column positions
strike_idx = 10
ce_oi_col = 0
pe_oi_col = len(df.columns) - 1  # Last column

print(f"\nSTRIKE column: {strike_idx} = '{df.columns[strike_idx]}'")
print(f"CE OI column: {ce_oi_col} = '{df.columns[ce_oi_col]}'")
print(f"PE OI column: {pe_oi_col} = '{df.columns[pe_oi_col]}'")

# Parse numbers
def parse_num(val):
    try:
        if pd.isna(val):
            return 0.0
        val_str = str(val).strip().replace(',', '')
        if not val_str or val_str in ['-', '--']:
            return 0.0
        return float(val_str)
    except:
        return 0.0

# Calculate totals
total_ce = 0
total_pe = 0

for idx, row in df.iterrows():
    ce_val = parse_num(row.iloc[ce_oi_col])
    pe_val = parse_num(row.iloc[pe_oi_col])
    total_ce += ce_val
    total_pe += pe_val

# ✅ PCR
pcr = total_pe / total_ce if total_ce > 0 else 0

print("\n" + "=" * 60)
print("RESULTS")
print("=" * 60)
print(f"Total CE OI: {total_ce:,.0f}")
print(f"Total PE OI: {total_pe:,.0f}")
print(f"PCR (PE/CE): {pcr:.2f}")

# Signal
print("\n" + "=" * 60)
print("SIGNAL")
print("=" * 60)

if pcr < 0.5:
    print("🚀 STRONGLY BULLISH")
elif pcr < 0.7:
    print("📈 BULLISH - Buy Call")
elif pcr <= 1.2:
    print("⚖️ NEUTRAL - Range Trade")
elif pcr <= 1.5:
    print("📉 BEARISH - Buy Put")
else:
    print("💥 STRONGLY BEARISH")

# Sample data
print("\n" + "=" * 60)
print("SAMPLE DATA (First 5 Rows)")
print("=" * 60)
print(f"{'Strike':<12} {'CE OI':<10} {'PE OI':<10} {'PCR':<8}")
print("-" * 45)

for i in range(min(5, len(df))):
    strike = df.iloc[i, strike_idx]
    ce = parse_num(df.iloc[i, ce_oi_col])
    pe = parse_num(df.iloc[i, pe_oi_col])
    strike_pcr = pe / ce if ce > 0 else 0
    print(f"{str(strike):<12} {ce:<10,.0f} {pe:<10,.0f} {strike_pcr:<8.2f}")

print("\n" + "=" * 60)
print("✅ TEST COMPLETE")
print("=" * 60)
