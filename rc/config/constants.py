"""
Constants and enums for the forex analysis bot
"""
from enum import Enum

class SignalType(Enum):
    """Signal types"""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"

class TimeFrame(Enum):
    """Timeframe enumeration"""
    M1 = "1m"
    M5 = "5m"
    M15 = "15m"
    H1 = "1h"
    H4 = "4h"
    D1 = "1d"
    W1 = "1wk"

class TrendDirection(Enum):
    """Trend direction"""
    BULLISH = "BULLISH"
    BEARISH = "BEARISH"
    RANGING = "RANGING"

class OrderBlockType(Enum):
    """ICT Order Block Types"""
    BULLISH_OB = "BULLISH_ORDER_BLOCK"
    BEARISH_OB = "BEARISH_ORDER_BLOCK"
    BREAKER_BULLISH = "BULLISH_BREAKER"
    BREAKER_BEARISH = "BEARISH_BREAKER"

class LiquidityType(Enum):
    """Liquidity pool types"""
    BUY_SIDE = "BUY_SIDE_LIQUIDITY"
    SELL_SIDE = "SELL_SIDE_LIQUIDITY"
    EQUAL_HIGHS = "EQUAL_HIGHS"
    EQUAL_LOWS = "EQUAL_LOWS"

class SessionType(Enum):
    """Trading sessions"""
    ASIAN = "ASIAN"
    LONDON = "LONDON"
    NEW_YORK = "NEW_YORK"
    # SYDNEY = "SYDNEY"  # Removed as not used in ICT_KILL_ZONES

class ConfirmationType(Enum):
    """Types of signal confirmations"""
    TECHNICAL = "TECHNICAL"
    FUNDAMENTAL = "FUNDAMENTAL"
    SENTIMENT = "SENTIMENT"
    ICT_STRUCTURE = "ICT_STRUCTURE"
    LIQUIDITY = "LIQUIDITY"
    PRICE_ACTION = "PRICE_ACTION"

class CandlestickPattern(Enum):
    """Candlestick patterns"""
    DOJI = "DOJI"
    HAMMER = "HAMMER"
    SHOOTING_STAR = "SHOOTING_STAR"
    ENGULFING_BULLISH = "ENGULFING_BULLISH"
    ENGULFING_BEARISH = "ENGULFING_BEARISH"
    MORNING_STAR = "MORNING_STAR"
    EVENING_STAR = "EVENING_STAR"
    THREE_WHITE_SOLDIERS = "THREE_WHITE_SOLDIERS"
    THREE_BLACK_CROWS = "THREE_BLACK_CROWS"

# Discord Embed Colors
COLORS = {
    "BUY": 0x00FF00,  # Green
    "SELL": 0xFF0000,  # Red
    "NEUTRAL": 0xFFFF00,  # Yellow
    "INFO": 0x3498DB,  # Blue
    "WARNING": 0xF39C12,  # Orange
    "ERROR": 0xE74C3C  # Dark Red
}

# Emoji mappings
EMOJIS = {
    "BUY": "📈",
    "SELL": "📉",
    "NEUTRAL": "➡️",
    "BULLISH": "🐂",
    "BEARISH": "🐻",
    "WARNING": "⚠️",
    "CHECK": "✅",
    "CROSS": "❌",
    "CHART": "📊",
    "NEWS": "📰",
    "CLOCK": "⏰",
    "MONEY": "💰",
    "TARGET": "🎯",
    "STOP": "🛑"
}

# Market Structure Patterns
MARKET_STRUCTURE = {
    "BREAK_OF_STRUCTURE": "BOS",
    "CHANGE_OF_CHARACTER": "CHoCH",
    "INDUCEMENT": "IND",
    "MITIGATION": "MIT"
}
