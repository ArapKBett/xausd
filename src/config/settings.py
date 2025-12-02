import os
from pathlib import Path
from dotenv import load_dotenv
from typing import Dict, List, Tuple
import pytz

# Load environment variables
load_dotenv()

class Settings:
    """Central configuration management"""
    
    # Base paths
    BASE_DIR = Path(__file__).resolve().parent.parent.parent
    DATA_DIR = BASE_DIR / "data"
    LOGS_DIR = BASE_DIR / "logs"
    CHARTS_DIR = BASE_DIR / "charts"
    
    # Create directories
    for dir_path in [DATA_DIR, LOGS_DIR, CHARTS_DIR]:
        dir_path.mkdir(exist_ok=True)
    
    # Discord Configuration
    DISCORD_BOT_TOKEN = os.getenv("DISCORD_BOT_TOKEN")
    DISCORD_CHANNEL_ID = int(os.getenv("DISCORD_CHANNEL_ID", 0))
    DISCORD_GUILD_ID = int(os.getenv("DISCORD_GUILD_ID", 0))
    
    # API Keys
    ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
    FINNHUB_API_KEY = os.getenv("FINNHUB_API_KEY")
    NEWSAPI_KEY = os.getenv("NEWSAPI_KEY")
    OANDA_API_KEY = os.getenv("OANDA_API_KEY")
    OANDA_ACCOUNT_ID = os.getenv("OANDA_ACCOUNT_ID")
    
    # Database
    REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
    REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
    REDIS_DB = int(os.getenv("REDIS_DB", 0))
    REDIS_PASSWORD = os.getenv("REDIS_PASSWORD")
    
    # Trading Configuration - Updated for XAU/USD
    TRADING_PAIR = os.getenv("TRADING_PAIR", "GC=F")  # Gold futures symbol for Yahoo Finance
    CURRENCY_BASE = os.getenv("CURRENCY_BASE", "XAU")  # Gold
    CURRENCY_QUOTE = os.getenv("CURRENCY_QUOTE", "USD")
    ANALYSIS_INTERVAL = int(os.getenv("ANALYSIS_INTERVAL", 300))
    MIN_CONFIRMATIONS = int(os.getenv("MIN_CONFIRMATIONS", 3))
    RISK_PERCENTAGE = float(os.getenv("RISK_PERCENTAGE", 2.0))
    MAX_SPREAD = float(os.getenv("MAX_SPREAD", 2.5))
    
    # Timeframes (Yahoo Finance format)
    TIMEFRAMES = {
        "M1": "1m",
        "M5": "5m",
        "M15": "15m",
        "H1": "1h",
        "H4": "4h",
        "D1": "1d",
        "W1": "1wk"
    }
    
    # Timeframe periods for historical data
    TIMEFRAME_PERIODS = {
        "M1": "1d",
        "M5": "5d",
        "M15": "5d",
        "H1": "1mo",
        "H4": "3mo",
        "D1": "1y",
        "W1": "2y"
    }
    
    # Primary analysis timeframes
    PRIMARY_TIMEFRAME = "H1"
    HIGHER_TIMEFRAME = "H4"
    LOWER_TIMEFRAME = "M15"
    ENTRY_TIMEFRAME = "M5"
    
    # Timezone
    TIMEZONE = pytz.UTC
    
    # ICT Kill Zones (UTC times)
    ICT_KILL_ZONES = {
        "ASIAN": {
            "start": "00:00",
            "end": "03:00",
            "weight": 0.7,
            "description": "Asian Session Liquidity"
        },
        "LONDON": {
            "start": "07:00",
            "end": "10:00",
            "weight": 0.9,
            "description": "London Session Liquidity"
        },
        "NEW_YORK": {
            "start": "13:30",
            "end": "16:00",
            "weight": 1.0,
            "description": "New York Kill Zone"
        },
        "LONDON_CLOSE": {
            "start": "15:00",
            "end": "17:00",
            "weight": 0.85,
            "description": "London Close"
        }
    }
    
    # Risk Management
    MAX_DAILY_TRADES = int(os.getenv("MAX_DAILY_TRADES", 5))
    MAX_DAILY_LOSS_PERCENT = float(os.getenv("MAX_DAILY_LOSS_PERCENT", 5.0))
    MIN_RISK_REWARD_RATIO = float(os.getenv("MIN_RISK_REWARD_RATIO", 2.0))
    DEFAULT_STOP_LOSS_PIPS = int(os.getenv("DEFAULT_STOP_LOSS_PIPS", 300))  # Increased for gold volatility
    MIN_STOP_LOSS_PIPS = int(os.getenv("MIN_STOP_LOSS_PIPS", 150))  # ~$15 move
    MAX_STOP_LOSS_PIPS = int(os.getenv("MAX_STOP_LOSS_PIPS", 1000))  # ~$100 move
    POSITION_SIZE_METHOD = os.getenv("POSITION_SIZE_METHOD", "risk_based")
    
    # Technical Analysis Parameters
    RSI_PERIOD = int(os.getenv("RSI_PERIOD", 14))
    RSI_OVERBOUGHT = int(os.getenv("RSI_OVERBOUGHT", 70))
    RSI_OVERSOLD = int(os.getenv("RSI_OVERSOLD", 30))
    
    MACD_FAST = int(os.getenv("MACD_FAST", 12))
    MACD_SLOW = int(os.getenv("MACD_SLOW", 26))
    MACD_SIGNAL = int(os.getenv("MACD_SIGNAL", 9))
    
    BOLLINGER_PERIOD = int(os.getenv("BOLLINGER_PERIOD", 20))
    BOLLINGER_STD = int(os.getenv("BOLLINGER_STD", 2))
    
    ATR_PERIOD = int(os.getenv("ATR_PERIOD", 14))
    ADX_PERIOD = int(os.getenv("ADX_PERIOD", 14))
    
    STOCHASTIC_K = int(os.getenv("STOCHASTIC_K", 14))
    STOCHASTIC_D = int(os.getenv("STOCHASTIC_D", 3))
    
    # Fibonacci Levels
    FIBONACCI_LEVELS = [0, 0.236, 0.382, 0.5, 0.618, 0.786, 1.0, 1.272, 1.414, 1.618, 2.0, 2.618]
    
    # ICT Concepts
    ORDER_BLOCK_LOOKBACK = int(os.getenv("ORDER_BLOCK_LOOKBACK", 50))
    FVG_MIN_SIZE_PIPS = float(os.getenv("FVG_MIN_SIZE_PIPS", 50))  # Increased for gold
    LIQUIDITY_SWEEP_PIPS = float(os.getenv("LIQUIDITY_SWEEP_PIPS", 100))  # Increased for gold
    BREAKER_BLOCK_CONFIRMATION = int(os.getenv("BREAKER_BLOCK_CONFIRMATION", 3))
    
    # Market Structure - Updated for XAU/USD
    SWING_HIGH_LOW_PERIOD = 5
    SUPPORT_RESISTANCE_TOLERANCE = 2.0  # $2.00 for XAU/USD
    
    # Sentiment Analysis
    NEWS_LOOKBACK_HOURS = int(os.getenv("NEWS_LOOKBACK_HOURS", 24))
    MIN_NEWS_RELEVANCE_SCORE = float(os.getenv("MIN_NEWS_RELEVANCE_SCORE", 0.6))
    SENTIMENT_WEIGHT = float(os.getenv("SENTIMENT_WEIGHT", 0.3))
    
    # News Sources
    NEWS_SOURCES = [
        "reuters",
        "bloomberg",
        "financial-times",
        "wall-street-journal",
        "cnbc",
        "marketwatch",
        "forexlive",
        "investing.com"
    ]
    
    # Economic Indicators for XAU/USD
    ECONOMIC_INDICATORS = {
        "USD": [
            "Non-Farm Payrolls", "FOMC Rate Decision", "CPI",
            "GDP", "Unemployment Rate", "Retail Sales",
            "ISM Manufacturing PMI", "Consumer Confidence",
            "PPI", "Federal Reserve Speeches"
        ],
        "GLOBAL": [
            "Geopolitical Events", "Global Risk Sentiment",
            "US Dollar Index (DXY)", "Real Yields",
            "Central Bank Gold Reserves", "Inflation Expectations"
        ]
    }
    
    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = BASE_DIR / os.getenv("LOG_FILE", "logs/forex_bot.log")
    LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 10485760))
    LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 5))
    
    # Chart Settings
    CHART_WIDTH = int(os.getenv("CHART_WIDTH", 1920))
    CHART_HEIGHT = int(os.getenv("CHART_HEIGHT", 1080))
    CHART_DPI = int(os.getenv("CHART_DPI", 100))
    CHART_STYLE = os.getenv("CHART_STYLE", "dark_background")
    
    # Performance
    MAX_WORKERS = int(os.getenv("MAX_WORKERS", 4))
    CACHE_TTL = int(os.getenv("CACHE_TTL", 300))
    REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", 30))
    MAX_RETRIES = int(os.getenv("MAX_RETRIES", 3))
    
    # Pip Value for XAU/USD
    PIP_VALUE = 0.01
    PIPETTE_VALUE = 0.001
    
    @classmethod
    def validate(cls):
        """Validate critical settings"""
        required_settings = [
            ("DISCORD_BOT_TOKEN", cls.DISCORD_BOT_TOKEN),
            ("DISCORD_CHANNEL_ID", cls.DISCORD_CHANNEL_ID),
        ]
        
        missing = [name for name, value in required_settings if not value]
        
        if missing:
            raise ValueError(f"Missing required settings: {', '.join(missing)}")
        
        return True

settings = Settings()
