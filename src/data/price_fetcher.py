import pandas as pd
from datetime import datetime
from typing import Optional, Dict
from src.data.yahoo_finance_client import YahooFinanceClient
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.helpers import validate_spread

class PriceFetcher:
    """Main price fetching orchestrator"""
    
    def __init__(self):
        self.yahoo_client = YahooFinanceClient()
        logger.info("PriceFetcher initialized")
    
    def get_live_price(self) -> Optional[Dict[str, float]]:
        """
        Get current live price with validation
        
        Returns:
            Price data dictionary or None
        """
        try:
            price_data = self.yahoo_client.get_current_price()
            
            if not price_data:
                logger.error("Failed to fetch live price")
                return None
            
            # Validate spread
            if not validate_spread(price_data['bid'], price_data['ask']):
                logger.warning(
                    f"Spread too wide: {price_data['ask'] - price_data['bid']:.5f}"
                )
            
            return price_data
            
        except Exception as e:
            logger.error(f"Error in get_live_price: {e}")
            return None
    
    def get_timeframe_data(
        self,
        timeframe: str,
        bars: int = 500
    ) -> Optional[pd.DataFrame]:
        """
        Get data for specific timeframe
        
        Args:
            timeframe: Timeframe string (e.g., "1h", "4h")
            bars: Number of bars to fetch
        
        Returns:
            DataFrame with OHLCV data
        """
        try:
            period = self.yahoo_client._get_period_for_timeframe(timeframe)
            df = self.yahoo_client.get_historical_data(timeframe, period)
            
            if df is None or df.empty:
                logger.error(f"No data for timeframe {timeframe}")
                return None
            
            # Limit to requested bars
            if len(df) > bars:
                df = df.tail(bars)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching {timeframe} data: {e}")
            return None
    
    def get_all_timeframes(self) -> Dict[str, pd.DataFrame]:
        """Get data for all configured timeframes"""
        return self.yahoo_client.get_multi_timeframe_data()
    
    def get_specific_timeframes(
        self,
        timeframes: list
    ) -> Dict[str, pd.DataFrame]:
        """Get data for specific timeframes"""
        return self.yahoo_client.get_multi_timeframe_data(timeframes)
