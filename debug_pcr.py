# debug_pcr.py - Fixed with file selection
import pandas as pd
import numpy as np
import os
import glob

# Find all CSV files
csv_files = glob.glob("**/*.csv", recursive=True)

print("=" * 60)
print("AVAILABLE CSV FILES:")
print("=" * 60)

if csv_files:
    for i, file in enumerate(csv_files, 1):
        print(f"{i}. {file}")
    
    # Use first CSV file
    file_path = csv_files[0]
    print(f"\n✅ Using: {file_path}")
else:
    print("❌ No CSV files found!")
    print("Please upload your CSV file to this directory")
    exit()

print("\n" + "=" * 60)
print("READING FILE:")
print("=" * 60)

# Try different skiprows
for skip in [0, 1, 2]:
    try:
        df = pd.read_csv(file_path, skiprows=skip, on_bad_lines='skip')
        df = df.dropna(how='all')
        df = df.dropna(axis=1, how='all')
        
        print(f"\nskiprows={skip}: Shape={df.shape}")
        print(f"Columns: {list(df.columns)[:5]}...")
        
        # Check if STRIKE column exists
        has_strike = any('STRIKE' in str(col).upper() for col in df.columns)
        print(f"Has STRIKE: {has_strike}")
        
        if has_strike:
            print(f"✅ Using skiprows={skip}")
            break
    except Exception as e:
        print(f"skiprows={skip}: Error - {str(e)[:50]}")

# Now parse with correct skiprows
print("\n" + "=" * 60)
print("DETAILED COLUMN ANALYSIS:")
print("=" * 60)

for i, col in enumerate(df.columns):
    print(f"Col {i}: '{col}'")

# Find STRIKE
strike_idx = None
for i, col in enumerate(df.columns):
    if 'STRIKE' in str(col).upper():
        strike_idx = i
        break

if strike_idx is None:
    strike_idx = len(df.columns) // 2
    print(f"\n⚠️ STRIKE not found by name, using middle: {strike_idx}")

print(f"\n✅ STRIKE at index: {strike_idx}")

# Show first data row
print("\n" + "=" * 60)
print("FIRST DATA ROW:")
print("=" * 60)

for i in range(min(len(df.columns), 22)):
    val = df.iloc[0, i] if len(df) > 0 else "N/A"
    marker = " ← STRIKE" if i == strike_idx else ""
    print(f"Col {i}: {val}{marker}")

# Calculate PCR
print("\n" + "=" * 60)
print("PCR CALCULATION:")
print("=" * 60)

# CE OI = Col 1 (usually)
# PE OI = Last col (usually)

ce_oi_col = 1
pe_oi_col = len(df.columns) - 1

try:
    total_ce = pd.to_numeric(df.iloc[:, ce_oi_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).sum()
    total_pe = pd.to_numeric(df.iloc[:, pe_oi_col].astype(str).str.replace(',', ''), errors='coerce').fillna(0).sum()
    
    print(f"CE OI (Col {ce_oi_col}): {total_ce:,.0f}")
    print(f"PE OI (Col {pe_oi_col}): {total_pe:,.0f}")
    print(f"PCR (PE/CE): {total_pe/total_ce:.2f}" if total_ce > 0 else "PCR: N/A")
    
    # Show sample values
    print("\nSample values (first 5 rows):")
    for i in range(min(5, len(df))):
        ce_val = df.iloc[i, ce_oi_col]
        pe_val = df.iloc[i, pe_oi_col]
        strike = df.iloc[i, strike_idx]
        print(f"Strike={strike}: CE OI={ce_val}, PE OI={pe_val}")
        
except Exception as e:
    print(f"Error: {str(e)}")