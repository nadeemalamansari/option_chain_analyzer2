"""
BSE Option Chain Data Parser - Fixed for STRIKE PRICE format
✅ Col 0: Chg in OI (CE)
✅ Col 1: OI (CE)
✅ Col 10: STRIKE PRICE
✅ Col 19: OI (PE)
✅ Col 20: Chg in OI (PE)
✅ PCR = PE OI / CE OI
"""

import pandas as pd
import numpy as np
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class BSEOptionChainParser:
    """Parser for BSE option chain CSV files"""
    
    def __init__(self):
        self.exchange = 'BSE'
        self.data = None
        self.spot_price = 0.0
        
    def parse_csv(self, file_path) -> pd.DataFrame:
        """Parse BSE option chain CSV"""
        try:
            logger.info("🔄 Parsing BSE option chain...")
            
            # Read CSV - skip first row (CALLS/PUTS header)
            df = pd.read_csv(file_path, skiprows=1, on_bad_lines='skip')
            df = df.dropna(how='all')
            df = df.dropna(axis=1, how='all')
            
            logger.info(f"Shape: {df.shape}")
            logger.info(f"Total Columns: {len(df.columns)}")
            
            # ✅ FIXED POSITIONS for this format:
            # Col 0: Chg in OI (CE)
            # Col 1: OI (CE)           ← CE OI
            # Col 2: VOLUME (CE)
            # Col 3: IV (CE)
            # Col 4: LTP (CE)
            # Col 5: CHNG (CE)
            # Col 6: BID QTY (CE)
            # Col 7: BID PRICE (CE)
            # Col 8: ASK PRICE (CE)
            # Col 9: ASK QTY (CE)
            # Col 10: STRIKE PRICE
            # Col 11: BID QTY (PE)
            # Col 12: BID PRICE (PE)
            # Col 13: ASK PRICE (PE)
            # Col 14: ASK QTY (PE)
            # Col 15: CHNG (PE)
            # Col 16: LTP (PE)
            # Col 17: IV (PE)
            # Col 18: VOLUME (PE)
            # Col 19: OI (PE)          ← PE OI
            # Col 20: Chg in OI (PE)
            
            strike_idx = 10
            ce_change_oi_col = 0
            ce_oi_col = 1
            ce_volume_col = 2
            ce_iv_col = 3
            ce_ltp_col = 4
            
            pe_oi_col = 19
            pe_change_oi_col = 20
            pe_volume_col = 18
            pe_iv_col = 17
            pe_ltp_col = 16
            
            logger.info(f"CE OI (Col {ce_oi_col}): '{df.columns[ce_oi_col]}'")
            logger.info(f"PE OI (Col {pe_oi_col}): '{df.columns[pe_oi_col]}'")
            logger.info(f"STRIKE (Col {strike_idx}): '{df.columns[strike_idx]}'")
            
            result_data = []
            
            for idx, row in df.iterrows():
                try:
                    strike = self._parse_number(row.iloc[strike_idx])
                    if strike == 0:
                        continue
                    
                    record = {'STRIKE': strike}
                    
                    # CE DATA
                    record['CE_CHANGE_IN_OI'] = self._parse_number(row.iloc[ce_change_oi_col])
                    record['CE_OI'] = self._parse_number(row.iloc[ce_oi_col])
                    record['CE_VOLUME'] = self._parse_number(row.iloc[ce_volume_col])
                    record['CE_IV'] = self._parse_number(row.iloc[ce_iv_col])
                    record['CE_LTP'] = self._parse_number(row.iloc[ce_ltp_col])
                    
                    # PE DATA
                    record['PE_OI'] = self._parse_number(row.iloc[pe_oi_col])
                    record['PE_CHANGE_IN_OI'] = self._parse_number(row.iloc[pe_change_oi_col])
                    record['PE_VOLUME'] = self._parse_number(row.iloc[pe_volume_col])
                    record['PE_IV'] = self._parse_number(row.iloc[pe_iv_col])
                    record['PE_LTP'] = self._parse_number(row.iloc[pe_ltp_col])
                    
                    has_data = any(v != 0 for k, v in record.items() if k != 'STRIKE')
                    if has_data:
                        result_data.append(record)
                        
                except:
                    continue
            
            if not result_data:
                return pd.DataFrame()
            
            result_df = pd.DataFrame(result_data)
            
            required = ['CE_OI', 'CE_CHANGE_IN_OI', 'CE_LTP', 'CE_VOLUME', 'CE_IV',
                       'PE_OI', 'PE_CHANGE_IN_OI', 'PE_LTP', 'PE_VOLUME', 'PE_IV']
            
            for col in required:
                if col not in result_df.columns:
                    result_df[col] = 0.0
                result_df[col] = pd.to_numeric(result_df[col], errors='coerce').fillna(0)
            
            result_df = result_df[result_df['STRIKE'] > 0]
            result_df = result_df.sort_values('STRIKE').reset_index(drop=True)
            
            result_df['TOTAL_OI'] = result_df['CE_OI'] + result_df['PE_OI']
            result_df['TOTAL_VOLUME'] = result_df['CE_VOLUME'] + result_df['PE_VOLUME']
            result_df['STRIKE_PCR'] = result_df['PE_OI'] / result_df['CE_OI'].replace(0, np.nan)
            result_df['STRIKE_PCR'] = result_df['STRIKE_PCR'].fillna(0)
            
            self._extract_spot_price(result_df)
            self.data = result_df
            
            total_ce = float(result_df['CE_OI'].sum())
            total_pe = float(result_df['PE_OI'].sum())
            pcr = total_pe / total_ce if total_ce > 0 else 0
            
            logger.info(f"✅ CE OI: {total_ce:,.0f}")
            logger.info(f"✅ PE OI: {total_pe:,.0f}")
            logger.info(f"✅ PCR: {pcr:.2f}")
            
            return result_df
            
        except Exception as e:
            logger.error(f"Error: {str(e)}")
            import traceback
            logger.error(traceback.format_exc())
            return pd.DataFrame()
    
    def _parse_number(self, value) -> float:
        try:
            if value is None or pd.isna(value):
                return 0.0
            if isinstance(value, (int, float)):
                return float(value)
            value_str = str(value).strip().replace(',', '')
            if not value_str or value_str in ['-', '--', '']:
                return 0.0
            return float(value_str)
        except:
            return 0.0
    
    def _extract_spot_price(self, df: pd.DataFrame):
        try:
            if len(df) > 0:
                if 'CE_LTP' in df.columns and 'PE_LTP' in df.columns:
                    valid = df[(df['CE_LTP'] > 0) & (df['PE_LTP'] > 0)]
                    if len(valid) > 0:
                        valid = valid.copy()
                        valid['_diff'] = abs(valid['CE_LTP'] - valid['PE_LTP'])
                        self.spot_price = float(valid.loc[valid['_diff'].idxmin(), 'STRIKE'])
                    else:
                        self.spot_price = float(df['STRIKE'].iloc[len(df)//2])
                else:
                    self.spot_price = float(df['STRIKE'].iloc[len(df)//2])
        except:
            self.spot_price = 0.0
    
    def get_summary(self) -> dict:
        if self.data is None or len(self.data) == 0:
            return {}
        
        total_ce = float(self.data['CE_OI'].sum())
        total_pe = float(self.data['PE_OI'].sum())
        
        return {
            'exchange': 'BSE',
            'spot_price': self.spot_price,
            'total_ce_oi': total_ce,
            'total_pe_oi': total_pe,
            'total_oi': total_ce + total_pe,
            'pcr': round(total_pe / total_ce, 2) if total_ce > 0 else 0
        }