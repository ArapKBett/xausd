import pandas as pd
from typing import Optional
from src.utils.logger import logger

class COTAnalysis:
    """COT (Commitments of Traders) lightweight analyzer.

    Expects a DataFrame with columns: date, commercial_long, commercial_short, noncommercial_long, noncommercial_short
    """

    def __init__(self):
        pass

    def compute_net_positions(self, df: pd.DataFrame) -> Optional[pd.Series]:
        try:
            if df is None or df.empty:
                return None
            net_noncommercial = df['noncommercial_long'] - df['noncommercial_short']
            return net_noncommercial
        except Exception as e:
            logger.error(f"COTAnalysis compute_net_positions failed: {e}")
            return None

    def signal_from_cot(self, df: pd.DataFrame) -> Optional[str]:
        try:
            net = self.compute_net_positions(df)
            if net is None:
                return None
            # trend of net positions (simple slope)
            slope = net.iloc[-1] - net.iloc[-4] if len(net) >= 4 else net.diff().mean()
            if slope > 0:
                return 'bullish'
            elif slope < 0:
                return 'bearish'
            return 'neutral'
        except Exception as e:
            logger.error(f"COTAnalysis signal_from_cot failed: {e}")
            return None
