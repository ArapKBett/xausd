import pandas as pd
from typing import Optional
from src.utils.logger import logger

class MarketMakerModel:
    """Provides a probabilistic bias based on liquidity and structure.

    This is a compact production-friendly model: computes bias and confidence.
    """

    def __init__(self):
        pass

    def compute_bias(self, df: pd.DataFrame) -> dict:
        try:
            # simple rules: if last 20 candles show higher highs -> bullish
            window = min(20, len(df))
            highs = df['high'].iloc[-window:]
            lows = df['low'].iloc[-window:]
            hh = highs.max()
            ll = lows.min()
            last_close = df['close'].iloc[-1]
            bias = 'neutral'
            confidence = 0.0
            if last_close > highs.mean():
                bias = 'bullish'
                confidence = min(1.0, (last_close - lows.mean()) / (hh - ll + 1e-9))
            elif last_close < lows.mean():
                bias = 'bearish'
                confidence = min(1.0, (highs.mean() - last_close) / (hh - ll + 1e-9))
            return {'bias': bias, 'confidence': float(confidence)}
        except Exception as e:
            logger.error(f"MarketMakerModel compute_bias error: {e}")
            return {'bias': 'neutral', 'confidence': 0.0}
