import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
import time
import requests
from retry import retry
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.cache_manager import cache

class YahooFinanceClient:
    """Client for fetching gold data from Yahoo Finance with fallbacks"""
    
    def __init__(self):
        self.symbol = settings.TRADING_PAIR  # GC=F for gold futures
        self.alternative_symbols = [
            "GC=F",            # COMEX Gold Futures
            "XAUUSD=X",        # Gold/USD spot
            "XAU-USD",         # Alternative format
            "GCZ25.CMX",       # December 2025 futures
            "GC1!",           # Generic front month
            "GLD",            # Gold ETF (proxy)
            "IAU",            # iShares Gold Trust
            "XAUUSD",         # Common forex pair format
        ]
        
        # Create session with proper headers
        self.session = self._create_session()
        
        # Try to initialize with primary symbol
        self.ticker = None
        self.active_symbol = None
        
        # Initialize ticker with first working symbol
        self._initialize_ticker()
        
        logger.info(f"Yahoo Finance client initialized for Gold ({self.active_symbol})")
    
    def _create_session(self):
        """Create a session with proper headers to mimic browser"""
        session = requests.Session()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        return session
    
    def _initialize_ticker(self):
        """Find a working symbol and initialize ticker"""
        for symbol in self.alternative_symbols:
            try:
                logger.info(f"Testing symbol: {symbol}")
                ticker = yf.Ticker(symbol, session=self.session)
                
                # Test with a small data fetch
                test_data = ticker.history(period="1d", interval="1m", timeout=5)
                
                if not test_data.empty:
                    self.ticker = ticker
                    self.active_symbol = symbol
                    logger.info(f"✓ Symbol {symbol} is working")
                    return True
                    
            except Exception as e:
                logger.debug(f"Symbol {symbol} failed: {str(e)[:50]}")
                continue
        
        # If no symbol works, fallback to default
        logger.warning("No alternative symbols worked, using default with fallback")
        self.ticker = yf.Ticker(self.symbol, session=self.session)
        self.active_symbol = self.symbol
        return False
    
    def _fetch_with_retry(self, func, *args, **kwargs):
        """Generic retry mechanism for Yahoo Finance calls"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff
                    logger.warning(f"Attempt {attempt + 1} failed: {str(e)[:100]}. Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                    
                    # Try reinitializing ticker on failure
                    if attempt == 1:  # On second failure, try different symbol
                        self._initialize_ticker()
                else:
                    raise
    
    def get_current_price(self) -> Optional[Dict[str, float]]:
        """
        Get current bid/ask prices for gold with robust error handling
        
        Returns:
            Dictionary with bid, ask, and mid prices or None
        """
        cache_key = f"current_price:{self.active_symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            # Try with current ticker first
            data = self._fetch_with_retry(
                lambda: self.ticker.history(period="1d", interval="1m")
            )
            
            if data is None or data.empty:
                logger.warning("Empty data returned, trying alternative symbol...")
                # Try to switch to alternative symbol
                if self._initialize_ticker():
                    data = self.ticker.history(period="1d", interval="1m")
            
            if data.empty:
                logger.error("No current price data available for any gold symbol")
                return None
            
            latest = data.iloc[-1]
            
            # For gold, typical spread is around 0.10-0.50 (10-50 pips)
            current_price = latest['Close']
            spread_estimate = 0.20  # Conservative 20 pip estimate
            
            price_data = {
                'bid': current_price - (spread_estimate / 2),
                'ask': current_price + (spread_estimate / 2),
                'mid': current_price,
                'timestamp': datetime.now(),
                'high': latest['High'],
                'low': latest['Low'],
                'open': latest['Open'],
                'volume': latest['Volume'],
                'symbol': self.active_symbol
            }
            
            # Validate price is reasonable (gold is usually $1800-$2500)
            if not (1000 < current_price < 5000):
                logger.error(f"Unreasonable gold price: ${current_price}")
                return None
            
            # Cache for 10 seconds
            cache.set(cache_key, price_data, ttl=10)
            
            logger.info(f"Gold price fetched: ${current_price:.2f} ({self.active_symbol})")
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
        Get historical OHLCV data for gold with fallback
        
        Args:
            timeframe: Data interval (1m, 5m, 15m, 1h, 4h, 1d, 1wk)
            period: Data period (1d, 5d, 1mo, 3mo, 6mo, 1y, 2y, 5y, 10y, ytd, max)
        
        Returns:
            DataFrame with OHLCV data or None
        """
        cache_key = f"historical:{self.active_symbol}:{timeframe}:{period}"
        cached_data = cache.get(cache_key)
        
        if cached_data is not None:
            return cached_data
        
        try:
            # Fetch data with retry logic
            data = self._fetch_with_retry(
                lambda: self.ticker.history(period=period, interval=timeframe)
            )
            
            if data.empty:
                logger.warning(f"No historical data for {timeframe}/{period}")
                
                # Try fallback with longer period
                if timeframe == "1m":
                    fallback_data = self.ticker.history(period="5d", interval="5m")
                    if not fallback_data.empty:
                        data = fallback_data
                        logger.info("Using 5m data as fallback for 1m")
                
                if data.empty:
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
        Get data for multiple timeframes with fallback
        
        Args:
            timeframes: List of timeframes to fetch
        
        Returns:
            Dictionary mapping timeframe to DataFrame
        """
        if timeframes is None:
            timeframes = [
                "15m",  # M15
                "1h",   # H1
                "4h",   # H4
                "1d"    # D1
            ]
        
        data = {}
        
        for tf in timeframes:
            try:
                period = self._get_period_for_timeframe(tf)
                df = self.get_historical_data(timeframe=tf, period=period)
                
                if df is not None and not df.empty:
                    data[tf] = df
                else:
                    logger.warning(f"No data for timeframe {tf}")
                    
                    # Try alternative timeframes for missing data
                    if tf == "1m":
                        alt_df = self.get_historical_data(timeframe="5m", period="1d")
                        if alt_df is not None:
                            data[tf] = alt_df
                            logger.info(f"Using 5m data as proxy for {tf}")
                            
            except Exception as e:
                logger.error(f"Failed to fetch {tf} data: {e}")
                continue
        
        return data
    
    # Keep the helper methods the same as before:
    def get_info(self) -> Optional[Dict]:
        """Get ticker info for gold"""
        cache_key = f"info:{self.active_symbol}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return cached_data
        
        try:
            info = self.ticker.info
            cache.set(cache_key, info, ttl=3600)
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
        if df is None or df.empty:
            return False
        required_cols = ['open', 'high', 'low', 'close', 'volume']
        return all(col in df.columns for col in required_cols)
