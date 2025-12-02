import pandas as pd
from datetime import datetime, timedelta
from typing import Optional, Dict, List
from src.data.yahoo_finance_client import YahooFinanceClient
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.cache_manager import cache

class HistoricalDataManager:
    """Manager for historical forex data"""
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
        
    def get_data_for_analysis(
        self,
        timeframe: str,
        bars: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Get historical data optimized for analysis
        
        Args:
            timeframe: Timeframe string
            bars: Number of bars needed
            
        Returns:
            DataFrame with complete OHLCV data
        """
        try:
            period = self._calculate_period(timeframe, bars)
            df = self.yahoo_client.get_historical_data(timeframe, period)
            
            if df is None or df.empty:
                return None
            
            # Ensure we have enough data
            if len(df) < bars * 0.8:  # Allow 20% tolerance
                logger.warning(f"Insufficient data: got {len(df)}, needed {bars}")
            
            # Clean data
            df = self._clean_data(df)
            
            return df.tail(bars)
            
        except Exception as e:
            logger.error(f"Error getting analysis data: {e}")
            return None
    
    def get_multi_timeframe_aligned_data(
        self,
        timeframes: List[str]
    ) -> Dict[str, pd.DataFrame]:
        """
        Get data for multiple timeframes, aligned by time
        
        Args:
            timeframes: List of timeframe strings
            
        Returns:
            Dictionary of aligned DataFrames
        """
        data = {}
        
        for tf in timeframes:
            df = self.get_data_for_analysis(tf)
            if df is not None:
                data[tf] = df
        
        return data
    
    def get_higher_timeframe_context(
        self,
        current_timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Get higher timeframe for context
        
        Args:
            current_timeframe: Current timeframe being analyzed
            
        Returns:
            DataFrame for higher timeframe
        """
        timeframe_order = ["1m", "5m", "15m", "1h", "4h", "1d", "1wk"]
        
        try:
            current_idx = timeframe_order.index(current_timeframe)
            if current_idx < len(timeframe_order) - 1:
                higher_tf = timeframe_order[current_idx + 1]
                return self.get_data_for_analysis(higher_tf)
        except ValueError:
            logger.warning(f"Unknown timeframe: {current_timeframe}")
        
        return None
    
    def get_lower_timeframe_precision(
        self,
        current_timeframe: str
    ) -> Optional[pd.DataFrame]:
        """
        Get lower timeframe for entry precision
        
        Args:
            current_timeframe: Current timeframe being analyzed
            
        Returns:
            DataFrame for lower timeframe
        """
        timeframe_order = ["1m", "5m", "15m", "1h", "4h", "1d", "1wk"]
        
        try:
            current_idx = timeframe_order.index(current_timeframe)
            if current_idx > 0:
                lower_tf = timeframe_order[current_idx - 1]
                return self.get_data_for_analysis(lower_tf)
        except ValueError:
            logger.warning(f"Unknown timeframe: {current_timeframe}")
        
        return None
    
    def _calculate_period(self, timeframe: str, bars: int) -> str:
        """Calculate required period to get enough bars"""
        # Map timeframe to approximate days needed
        days_map = {
            "1m": bars / (24 * 60),
            "5m": bars / (24 * 12),
            "15m": bars / (24 * 4),
            "1h": bars / 24,
            "4h": bars / 6,
            "1d": bars,
            "1wk": bars * 7
        }
        
        days_needed = days_map.get(timeframe, bars)
        
        # Convert to Yahoo Finance period
        if days_needed <= 5:
            return "5d"
        elif days_needed <= 30:
            return "1mo"
        elif days_needed <= 90:
            return "3mo"
        elif days_needed <= 180:
            return "6mo"
        elif days_needed <= 365:
            return "1y"
        elif days_needed <= 730:
            return "2y"
        else:
            return "5y"
    
    def _clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate data"""
        # Remove any NaN values
        df = df.dropna()
        
        # Remove duplicate timestamps
        df = df[~df.index.duplicated(keep='last')]
        
        # Sort by index
        df = df.sort_index()
        
        # Validate OHLC relationships
        df = df[
            (df['low'] <= df['high']) &
            (df['low'] <= df['open']) &
            (df['low'] <= df['close']) &
            (df['high'] >= df['open']) &
            (df['high'] >= df['close'])
        ]
        
        return df
