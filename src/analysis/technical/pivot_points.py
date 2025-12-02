import pandas as pd
from typing import Dict
from src.utils.logger import logger

class PivotPoints:
    """Calculate classical pivot points (S/R levels) for OHLC data."""

    def __init__(self):
        pass

    def classical(self, df: pd.DataFrame) -> Dict[str, float]:
        try:
            last = df.iloc[-2] if len(df) >= 2 else df.iloc[-1]
            high = float(last['high'])
            low = float(last['low'])
            close = float(last['close'])
            pivot = (high + low + close) / 3.0
            r1 = 2*pivot - low
            s1 = 2*pivot - high
            r2 = pivot + (high - low)
            s2 = pivot - (high - low)
            return {'pivot': pivot, 'r1': r1, 's1': s1, 'r2': r2, 's2': s2}
        except Exception as e:
            logger.error(f"PivotPoints classical error: {e}")
            return {}
