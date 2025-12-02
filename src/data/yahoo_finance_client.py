import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
from retry import retry
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.cache_manager import cache

class YahooFinanceClient:
    """Client for fetching gold data from Yahoo Finance"""
    
    def __init__(self):
        self.symbol = settings.TRADING_PAIR  # GC=F for gold futures
        self.ticker = yf.Ticker(self.symbol)
        logger.info(f"Yahoo Finance client initialized for Gold ({self.symbol})")
    
    @retry(tries=3, delay=2, backoff=2)
    def get_current_price(self) -> Optional[Dict[str, float]]:
        """
        Get current bid/ask prices for gold
        
        Returns:
            Dictionary with bid, ask, and mid prices
        """
        cache_key = f"current_price:{self.symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Get real-time data
            data = self.ticker.history(period="1d", interval="1m")
            
            if data.empty:
                logger.error("No current price data available for gold")
                return None
            
            latest = data.iloc[-1]
            
            # Yahoo Finance doesn't provide bid/ask, so we estimate
            current_price = latest['Close']
            
            # For gold, typical spread is around 0.10-0.50 (10-50 pips)
            # Using 0.20 ($0.20) as a conservative estimate
            spread_estimate = 0.20  # 20 pips spread estimate for gold
            
            price_data = {
                'bid': current_price - (spread_estimate / 2),
                'ask': current_price + (spread_estimate / 2),
                'mid': current_price,
                'timestamp': datetime.now(),
                'high': latest['High'],
                'low': latest['Low'],
                'open': latest['Open'],
                'volume': latest['Volume']
            }
            
            # Cache for 10 seconds
            cache.set(cache_key, price_data, ttl=10)
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error fetching current gold price: {e}")
            return None
    
    @retry(tries=3, delay=2, backoff=2)
    def get_historical_data(
        self,
        timeframe: str = "1h",
        period: str = "1mo"
    ) -> Optional[pd.DataFrame]:
        """
        Get historical OHLCV data for gold
        
        Args:
            timeframe: Data interval (1m, 5m, 15m, 1h, 4h, 1d, 1wk)
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            DataFrame with OHLCV data
        """
        cache_key = f"historical:{self.symbol}:{timeframe}:{period}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            # Fetch data
            data = self.ticker.history(period=period, interval=timeframe)
            
            if data.empty:
                logger.warning(f"No historical data for gold {timeframe}/{period}")
                return None
            
            # Standardize column names
            data.columns = [col.lower() for col in data.columns]
            
            # Add technical columns
            data['typical_price'] = (data['high'] + data['low'] + data['close']) / 3
            data['hl_avg'] = (data['high'] + data['low']) / 2
            
            # Cache based on timeframe
            cache_ttl = self._get_cache_ttl(timeframe)
            cache.set(cache_key, data, ttl=cache_ttl)
            
            logger.info(f"Fetched {len(data)} gold bars for {timeframe}")
            return data
            
        except Exception as e:
            logger.error(f"Error fetching historical gold data: {e}")
            return None
    
    def get_multi_timeframe_data(
        self,
        timeframes: List[str] = None
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple timeframes
        
        Args:
            timeframes: List of timeframes to fetch
        
        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        if timeframes is None:
            timeframes = [
                settings.TIMEFRAMES["M15"],
                settings.TIMEFRAMES["H1"],
                settings.TIMEFRAMES["H4"],
                settings.TIMEFRAMES["D1"]
            ]
        
        data = {}
        
        for tf in timeframes:
            period = self._get_period_for_timeframe(tf)
            df = self.get_historical_data(timeframe=tf, period=period)
            
            if df is not None:
                data[tf] = df
            else:
                logger.warning(f"Failed to fetch gold data for {tf}")
        
        return data
    
    def get_info(self) -> Optional[Dict]:
        """Get ticker info for gold"""
        cache_key = f"info:{self.symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            info = self.ticker.info
            cache.set(cache_key, info, ttl=3600)  # Cache for 1 hour
            return info
        except Exception as e:
            logger.error(f"Error fetching gold ticker info: {e}")
            return None
    
    def _get_period_for_timeframe(self, timeframe: str) -> str:
        """Get appropriate period for a timeframe"""
        period_map = {
            "1m": "1d",
            "5m": "5d",
            "15m": "1mo",
            "1h": "3mo",
            "4h": "6mo",
            "1d": "2y",
            "1wk": "5y"
        }
        return period_map.get(timeframe, "1mo")
    
    def _get_cache_ttl(self, timeframe: str) -> int:
        """Get cache TTL based on timeframe"""
        ttl_map = {
            "1m": 60,
            "5m": 300,
            "15m": 900,
            "1h": 1800,
            "4h": 7200,
            "1d": 14400,
            "1wk": 86400
        }
        return ttl_map.get(timeframe, 300)
    
    def validate_data(self, df: pd.DataFrame) -> bool:
        """Validate DataFrame has required columns"""
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_cols)
