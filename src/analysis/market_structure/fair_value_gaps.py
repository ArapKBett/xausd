import pandas as pd
from typing import List, Tuple
from src.utils.logger import logger

class FairValueGapDetector:
    """Detect fair value gaps (FVG) — simple implementation.

    Returns list of tuples: (start_idx, end_idx, low, high)
    """

    def __init__(self):
        pass

    def detect(self, df: pd.DataFrame) -> List[Tuple]:
        try:
            fvg = []
            o = df['open']
            c = df['close']
            for i in range(2, len(df)):
                # look for gaps between wick extremes
                previous_high = max(df['high'].iloc[i-2], df['high'].iloc[i-1])
                previous_low = min(df['low'].iloc[i-2], df['low'].iloc[i-1])
                current_low = df['low'].iloc[i]
                current_high = df['high'].iloc[i]
                if current_low > previous_high:
                    fvg.append((df.index[i-2], df.index[i], previous_high, current_low))
                if current_high < previous_low:
                    fvg.append((df.index[i-2], df.index[i], current_high, previous_low))
            return fvg
        except Exception as e:
            logger.error(f"FairValueGapDetector detect error: {e}")
            return []
