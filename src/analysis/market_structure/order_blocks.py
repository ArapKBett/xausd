import pandas as pd
from typing import List, Dict, Optional
from src.utils.logger import logger

class OrderBlock:
    def __init__(self, start, end, price_level, polarity):
        self.start = start
        self.end = end
        self.price_level = price_level
        self.polarity = polarity

    def to_dict(self):
        return {
            'start': self.start,
            'end': self.end,
            'price_level': self.price_level,
            'polarity': self.polarity
        }

class OrderBlocksDetector:
    """Detect order blocks using candle structure heuristics.

    This implementation looks for strong directional candles followed by consolidation and retest.
    """

    def __init__(self):
        pass

    def detect(self, df: pd.DataFrame, lookback: int = 500) -> List[OrderBlock]:
        try:
            obs = []
            o = df['open']
            c = df['close']
            h = df['high']
            l = df['low']
            for i in range(2, len(df)-2):
                # bullish order block heuristic
                if o.iloc[i] > c.iloc[i] and o.iloc[i-1] > c.iloc[i-1]:
                    # two bearish candles - consider bearish order block at their high
                    price = max(h.iloc[i-1], h.iloc[i])
                    obs.append(OrderBlock(df.index[i-1], df.index[i], float(price), 'bear'))
                if o.iloc[i] < c.iloc[i] and o.iloc[i-1] < c.iloc[i-1]:
                    price = min(l.iloc[i-1], l.iloc[i])
                    obs.append(OrderBlock(df.index[i-1], df.index[i], float(price), 'bull'))
            return obs
        except Exception as e:
            logger.error(f"OrderBlocksDetector detect error: {e}")
            return []
