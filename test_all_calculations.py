"""
Complete Test Script - Verify All Calculations
"""

import pandas as pd
import numpy as np
import sys
import os

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.core.data_bse_parser import BSEOptionChainParser
from src.core.data_nse_parser import NSEOptionChainParser
from src.core.analyzer import OptionChainAnalyzer

print("=" * 70)
print("COMPLETE CALCULATION VERIFICATION TEST")
print("=" * 70)

# ========== TEST 1: BSE ASIANPAINT ==========
print("\n" + "=" * 70)
print("TEST 1: BSE - ASIANPAINT")
print("=" * 70)

bse_file = '/Users/nadeemalamansari/Downloads/option-chain-ED-ASIANPAINT-18-Aug-2026.csv'
bse_parser = BSEOptionChainParser()
bse_df = bse_parser.parse_csv(bse_file)
bse_summary = bse_parser.get_summary()

bse_ce = bse_summary['total_ce_oi']
bse_pe = bse_summary['total_pe_oi']
bse_pcr = bse_summary['pcr']

print(f"\n📊 BSE Data:")
print(f"  Total Strikes: {len(bse_df)}")
print(f"  CE OI: {bse_ce:,.0f}")
print(f"  PE OI: {bse_pe:,.0f}")
print(f"  PCR: {bse_pcr:.2f}")

# Manual verification
manual_pcr = bse_pe / bse_ce if bse_ce > 0 else 0
print(f"\n🔍 Manual Verification:")
print(f"  Manual PCR: {manual_pcr:.2f}")
print(f"  Parser PCR: {bse_pcr:.2f}")
print(f"  Match: {'✅ YES' if abs(manual_pcr - bse_pcr) < 0.01 else '❌ NO'}")

# PCR Signal
if bse_pcr < 0.7:
    print(f"  Signal: 📈 BULLISH")
elif bse_pcr > 1.2:
    print(f"  Signal: 📉 BEARISH")
else:
    print(f"  Signal: ⚖️ NEUTRAL")

# ========== TEST 2: NSE SENSEX ==========
print("\n" + "=" * 70)
print("TEST 2: NSE - SENSEX")
print("=" * 70)

nse_file = '/Users/nadeemalamansari/Downloads/IO_OptionChain_SENSEX_18082026_194117.csv'
nse_parser = NSEOptionChainParser()
nse_df = nse_parser.parse_csv(nse_file)
nse_summary = nse_parser.get_summary()

nse_ce = nse_summary['total_ce_oi']
nse_pe = nse_summary['total_pe_oi']
nse_pcr = nse_summary['pcr']

print(f"\n📊 NSE Data:")
print(f"  Total Strikes: {len(nse_df)}")
print(f"  CE OI: {nse_ce:,.0f}")
print(f"  PE OI: {nse_pe:,.0f}")
print(f"  PCR: {nse_pcr:.2f}")

manual_pcr = nse_pe / nse_ce if nse_ce > 0 else 0
print(f"\n🔍 Manual Verification:")
print(f"  Manual PCR: {manual_pcr:.2f}")
print(f"  Parser PCR: {nse_pcr:.2f}")
print(f"  Match: {'✅ YES' if abs(manual_pcr - nse_pcr) < 0.01 else '❌ NO'}")

if nse_pcr < 0.7:
    print(f"  Signal: 📈 BULLISH")
elif nse_pcr > 1.2:
    print(f"  Signal: 📉 BEARISH")
else:
    print(f"  Signal: ⚖️ NEUTRAL")

# ========== TEST 3: ANALYZER ==========
print("\n" + "=" * 70)
print("TEST 3: ANALYZER (BSE)")
print("=" * 70)

analyzer = OptionChainAnalyzer(bse_df, bse_summary['spot_price'])
analysis = analyzer.get_complete_analysis()

print(f"\n📊 Analyzer Results:")
print(f"  PCR (OI): {analysis['pcr']['oi_pcr']:.2f}")
print(f"  PCR Sentiment: {analysis['pcr']['sentiment']}")
print(f"  Support Levels: {len(analysis['support_resistance']['support'])}")
print(f"  Resistance Levels: {len(analysis['support_resistance']['resistance'])}")
print(f"  Max Pain: {analysis['max_pain'].get('max_pain_strike', 0):,.0f}")

# Verify PCR from analyzer
analyzer_pcr = analysis['pcr']['oi_pcr']
print(f"\n🔍 PCR Verification:")
print(f"  Parser PCR: {bse_pcr:.2f}")
print(f"  Analyzer PCR: {analyzer_pcr:.2f}")
print(f"  Match: {'✅ YES' if abs(bse_pcr - analyzer_pcr) < 0.01 else '❌ NO'}")

# ========== TEST 4: DATA INTEGRITY ==========
print("\n" + "=" * 70)
print("TEST 4: DATA INTEGRITY")
print("=" * 70)

print(f"\n🔍 BSE DataFrame Check:")
print(f"  Columns: {list(bse_df.columns)}")
print(f"  Null values: {bse_df.isnull().sum().sum()}")
print(f"  Negative CE OI: {(bse_df['CE_OI'] < 0).sum()}")
print(f"  Negative PE OI: {(bse_df['PE_OI'] < 0).sum()}")
print(f"  Zero Strikes: {(bse_df['STRIKE'] == 0).sum()}")

print(f"\n🔍 NSE DataFrame Check:")
print(f"  Columns: {list(nse_df.columns)}")
print(f"  Null values: {nse_df.isnull().sum().sum()}")
print(f"  Negative CE OI: {(nse_df['CE_OI'] < 0).sum()}")
print(f"  Negative PE OI: {(nse_df['PE_OI'] < 0).sum()}")
print(f"  Zero Strikes: {(nse_df['STRIKE'] == 0).sum()}")

# ========== TEST 5: SUPPORT/RESISTANCE ==========
print("\n" + "=" * 70)
print("TEST 5: SUPPORT/RESISTANCE")
print("=" * 70)

sr = analysis['support_resistance']

print(f"\n🟢 Support Levels:")
for s in sr['support'][:3]:
    print(f"  Strike: ₹{s['strike']:,.0f} | OI: {s['oi']:,.0f} | Strength: {s['strength']:.1%}")

print(f"\n🔴 Resistance Levels:")
for r in sr['resistance'][:3]:
    print(f"  Strike: ₹{r['strike']:,.0f} | OI: {r['oi']:,.0f} | Strength: {r['strength']:.1%}")

# ========== SUMMARY ==========
print("\n" + "=" * 70)
print("TEST SUMMARY")
print("=" * 70)

tests_passed = 0
total_tests = 5

# Test 1
if abs(manual_pcr - bse_pcr) < 0.01:
    tests_passed += 1
    print("✅ Test 1 (BSE PCR): PASSED")
else:
    print("❌ Test 1 (BSE PCR): FAILED")

# Test 2
if abs(manual_pcr - nse_pcr) < 0.01:
    tests_passed += 1
    print("✅ Test 2 (NSE PCR): PASSED")
else:
    print("❌ Test 2 (NSE PCR): FAILED")

# Test 3
if abs(bse_pcr - analyzer_pcr) < 0.01:
    tests_passed += 1
    print("✅ Test 3 (Analyzer PCR): PASSED")
else:
    print("❌ Test 3 (Analyzer PCR): FAILED")

# Test 4
if bse_df.isnull().sum().sum() == 0 and nse_df.isnull().sum().sum() == 0:
    tests_passed += 1
    print("✅ Test 4 (Data Integrity): PASSED")
else:
    print("❌ Test 4 (Data Integrity): FAILED")

# Test 5
if len(sr['support']) > 0 and len(sr['resistance']) > 0:
    tests_passed += 1
    print("✅ Test 5 (Support/Resistance): PASSED")
else:
    print("❌ Test 5 (Support/Resistance): FAILED")

print(f"\n{tests_passed}/{total_tests} Tests Passed")

if tests_passed == total_tests:
    print("\n🎉 ALL TESTS PASSED! Calculations are correct!")
else:
    print(f"\n⚠️ {total_tests - tests_passed} test(s) failed. Check calculations.")

print("\n" + "=" * 70)
