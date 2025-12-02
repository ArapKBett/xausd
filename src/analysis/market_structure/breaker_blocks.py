import pandas as pd
from typing import List
from src.utils.logger import logger

class BreakerBlocksDetector:
    """Detect breaker blocks — simple heuristic based on failed structure breaks."""

    def __init__(self):
        pass

    def detect(self, df: pd.DataFrame) -> List[dict]:
        try:
            results = []
            highs = df['high']
            lows = df['low']
            for i in range(3, len(df)-1):
                # failed breakout: previous swing high broken then reclaimed
                if highs.iloc[i-1] < highs.iloc[i] and highs.iloc[i+1] < highs.iloc[i]:
                    # potential breaker sell
                    results.append({'index': df.index[i], 'type': 'sell_breaker', 'price': float(highs.iloc[i])})
                if lows.iloc[i-1] > lows.iloc[i] and lows.iloc[i+1] > lows.iloc[i]:
                    results.append({'index': df.index[i], 'type': 'buy_breaker', 'price': float(lows.iloc[i])})
            return results
        except Exception as e:
            logger.error(f"BreakerBlocksDetector detect error: {e}")
            return []
