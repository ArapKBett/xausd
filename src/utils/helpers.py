import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Union, List, Tuple, Optional
import pytz
from src.config.settings import settings
from src.utils.logger import logger

def pips_to_price(pips: float, pair: str = "XAUUSD") -> float:
    """Convert pips to price movement for XAU/USD"""
    # For XAU/USD: 1 pip = $0.01
    return pips * settings.PIP_VALUE

def price_to_pips(price_diff: float, pair: str = "XAUUSD") -> float:
    """Convert price movement to pips for XAU/USD"""
    # For XAU/USD: price diff of $1.00 = 100 pips
    return price_diff / settings.PIP_VALUE

def calculate_position_size(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float,
    pair: str = "XAUUSD"
) -> float:
    """
    Calculate position size based on risk management for gold
    
    Args:
        account_balance: Trading account balance
        risk_percent: Risk percentage per trade
        stop_loss_pips: Stop loss in pips
        pair: XAUUSD for gold trading
    
    Returns:
        Position size in lots (1 lot = 100 oz of gold)
    """
    risk_amount = account_balance * (risk_percent / 100)
    pip_value = settings.PIP_VALUE  # $0.01 per pip
    
    # For gold: 1 standard lot = 100 ounces
    # For gold: Pip value per standard lot = 100 * $0.01 = $1.00 per pip
    pip_value_per_lot = 100 * pip_value  # $1.00 per pip for standard lot
    
    # Position size = (Risk Amount) / (Stop Loss in Pips * Pip Value per Lot)
    position_size = risk_amount / (stop_loss_pips * pip_value_per_lot)
    
    return round(position_size, 2)

def is_kill_zone(timestamp: datetime = None) -> Tuple[bool, Optional[str]]:
    """
    Check if current time is within an ICT kill zone
    
    Args:
        timestamp: Time to check (defaults to now)
    
    Returns:
        (is_in_kill_zone, zone_name)
    """
    if timestamp is None:
        timestamp = datetime.now(pytz.UTC)
    
    current_time = timestamp.strftime("%H:%M")
    
    for zone_name, zone_info in settings.ICT_KILL_ZONES.items():
        start = zone_info["start"]
        end = zone_info["end"]
        
        if start <= current_time <= end:
            return True, zone_name
    
    return False, None

def get_kill_zone_weight(timestamp: datetime = None) -> float:
    """Get the weight/importance of current kill zone"""
    is_kz, zone_name = is_kill_zone(timestamp)
    
    if is_kz and zone_name:
        return settings.ICT_KILL_ZONES[zone_name]["weight"]
    
    return 0.5  # Default weight for non-kill zone times

def round_to_pip(price: float, pair: str = "XAUUSD") -> float:
    """Round price to nearest pip for gold ($0.01)"""
    return round(price / settings.PIP_VALUE) * settings.PIP_VALUE

def calculate_atr_stop_loss(atr: float, multiplier: float = 2.0) -> float:
    """Calculate stop loss based on ATR for gold"""
    stop_pips = price_to_pips(atr * multiplier)
    return max(min(stop_pips, settings.MAX_STOP_LOSS_PIPS), settings.MIN_STOP_LOSS_PIPS)

def calculate_risk_reward(
    entry: float,
    stop_loss: float,
    take_profit: float
) -> float:
    """Calculate risk/reward ratio"""
    risk = abs(entry - stop_loss)
    reward = abs(take_profit - entry)
    
    if risk == 0:
        return 0
    
    return reward / risk

def validate_spread(bid: float, ask: float) -> bool:
    """Validate if spread is acceptable for gold"""
    spread_pips = price_to_pips(ask - bid)
    return spread_pips <= settings.MAX_SPREAD

def calculate_swing_highs_lows(
    df: pd.DataFrame,
    period: int = 5
) -> Tuple[pd.Series, pd.Series]:
    """
    Calculate swing highs and lows
    
    Args:
        df: DataFrame with OHLC data
        period: Lookback period
    
    Returns:
        (swing_highs, swing_lows)
    """
    swing_highs = df['high'].rolling(window=period*2+1, center=True).apply(
        lambda x: x[period] if x[period] == max(x) else np.nan
    )
    
    swing_lows = df['low'].rolling(window=period*2+1, center=True).apply(
        lambda x: x[period] if x[period] == min(x) else np.nan
    )
    
    return swing_highs, swing_lows

def detect_equal_highs_lows(
    df: pd.DataFrame,
    tolerance_pips: float = 200.0  # Increased for gold ($2.00)
) -> Tuple[List[float], List[float]]:
    """
    Detect equal highs and lows (liquidity pools) for gold
    
    Args:
        df: DataFrame with OHLC data
        tolerance_pips: Tolerance in pips for "equal" determination
        
    Returns:
        (equal_highs, equal_lows)
    """
    swing_highs, swing_lows = calculate_swing_highs_lows(df)
    
    equal_highs = []
    equal_lows = []
    
    tolerance = pips_to_price(tolerance_pips)
    
    # Find equal highs
    highs = swing_highs.dropna().values
    for i in range(len(highs) - 1):
        for j in range(i + 1, len(highs)):
            if abs(highs[i] - highs[j]) <= tolerance:
                equal_highs.append(highs[i])
                break
    
    # Find equal lows
    lows = swing_lows.dropna().values
    for i in range(len(lows) - 1):
        for j in range(i + 1, len(lows)):
            if abs(lows[i] - lows[j]) <= tolerance:
                equal_lows.append(lows[i])
                break
    
    return equal_highs, equal_lows

def format_price(price: float, decimals: int = 2) -> str:
    """Format gold price for display (2 decimal places standard)"""
    return f"{price:.{decimals}f}"

def format_pips(pips: float) -> str:
    """Format pips for display"""
    return f"{pips:.1f}"

def get_trading_session(timestamp: datetime = None) -> str:
    """Get current trading session"""
    if timestamp is None:
        timestamp = datetime.now(pytz.UTC)
    
    hour = timestamp.hour
    
    if 0 <= hour < 8:
        return "ASIAN"
    elif 8 <= hour < 16:
        return "LONDON"
    elif 16 <= hour < 24:
        return "NEW_YORK"
    
    return "ASIAN"

def calculate_fibonacci_levels(
    high: float,
    low: float,
    is_uptrend: bool = True
) -> dict:
    """
    Calculate Fibonacci retracement levels
    
    Args:
        high: Swing high
        low: Swing low
        is_uptrend: Direction of trend
    
    Returns:
        Dictionary of Fibonacci levels
    """
    diff = high - low
    
    levels = {}
    for ratio in settings.FIBONACCI_LEVELS:
        if is_uptrend:
            levels[f"{ratio*100:.1f}%"] = high - (diff * ratio)
        else:
            levels[f"{ratio*100:.1f}%"] = low + (diff * ratio)
    
    return levels

def is_market_open() -> bool:
    """Check if gold market is open"""
    now = datetime.now(pytz.UTC)
    
    # Gold market trading hours (approximate - 24/5 but with reduced liquidity)
    # Sunday 6:00 PM EST to Friday 5:00 PM EST
    # Convert to UTC: Sunday 22:00 UTC to Friday 21:00 UTC
    
    if now.weekday() == 5:  # Saturday
        return False
    elif now.weekday() == 6:  # Sunday
        return now.hour >= 22  # Opens Sunday 22:00 UTC
    
    # Friday after 21:00 UTC is closed
    if now.weekday() == 4 and now.hour >= 21:
        return False
    
    return True

def calculate_volume_weighted_price(df: pd.DataFrame) -> float:
    """Calculate volume weighted average price"""
    if 'volume' not in df.columns or df['volume'].sum() == 0:
        return df['close'].mean()
    
    return (df['close'] * df['volume']).sum() / df['volume'].sum()

def detect_divergence(
    price_series: pd.Series,
    indicator_series: pd.Series,
    lookback: int = 14
) -> Tuple[bool, str]:
    """
    Detect bullish or bearish divergence
    
    Returns:
        (has_divergence, divergence_type)
    """
    if len(price_series) < lookback or len(indicator_series) < lookback:
        return False, "NONE"
    
    recent_price = price_series.tail(lookback)
    recent_indicator = indicator_series.tail(lookback)
    
    price_trend = recent_price.iloc[-1] > recent_price.iloc[0]
    indicator_trend = recent_indicator.iloc[-1] > recent_indicator.iloc[0]
    
    if price_trend and not indicator_trend:
        return True, "BEARISH"
    elif not price_trend and indicator_trend:
        return True, "BULLISH"
    
    return False, "NONE"

def calculate_lot_size_from_risk(
    account_balance: float,
    risk_percent: float,
    stop_loss_pips: float
) -> dict:
    """
    Calculate lot sizes for different account types for gold
    
    Returns:
        Dictionary with standard, mini, and micro lot sizes
    """
    risk_amount = account_balance * (risk_percent / 100)
    
    # Standard lot (100 ounces) - Pip value = $1.00 per pip
    standard_lots = risk_amount / (stop_loss_pips * 1.00)
    
    # Mini lot (10 ounces) - Pip value = $0.10 per pip
    mini_lots = risk_amount / (stop_loss_pips * 0.10)
    
    # Micro lot (1 ounce) - Pip value = $0.01 per pip
    micro_lots = risk_amount / (stop_loss_pips * 0.01)
    
    return {
        "standard": round(standard_lots, 2),
        "mini": round(mini_lots, 2),
        "micro": round(micro_lots, 2)
    }
