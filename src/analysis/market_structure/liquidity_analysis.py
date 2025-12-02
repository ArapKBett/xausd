import pandas as pd
from typing import List, Tuple, Optional
from src.utils.logger import logger

class LiquidityAnalysis:
    """Detect liquidity pools (swing highs/lows) in OHLC series."""

    def __init__(self):
        pass

    def find_liquidity_pools(self, df: pd.DataFrame, lookback: int = 200) -> List[Tuple[pd.Timestamp, float]]:
        try:
            pools = []
            highs = df['high']
            lows = df['low']
            # simple local max/min detection using rolling window
            window = max(3, int(min(21, lookback/10)))
            for i in range(window, len(df) - window):
                h = highs.iloc[i]
                l = lows.iloc[i]
                if h == highs.iloc[i-window:i+window+1].max():
                    pools.append((df.index[i], float(h)))
                if l == lows.iloc[i-window:i+window+1].min():
                    pools.append((df.index[i], float(l)))
            return pools
        except Exception as e:
            logger.error(f"LiquidityAnalysis find_liquidity_pools error: {e}")
            return []
