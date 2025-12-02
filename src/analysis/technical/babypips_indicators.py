import pandas as pd
import numpy as np
from ta.trend import MACD, ADXIndicator, EMAIndicator, SMAIndicator
from ta.momentum import RSIIndicator, StochasticOscillator
from ta.volatility import BollingerBands, AverageTrueRange
from typing import Dict, Tuple, Optional
from src.config.settings import settings
from src.config.constants import TrendDirection, SignalType
from src.utils.logger import logger

class BabyPipsIndicators:
    """Technical indicators based on BabyPips methodology"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self._calculate_all_indicators()
    
    def _calculate_all_indicators(self):
        """Calculate all technical indicators"""
        try:
            # Moving Averages
            self._calculate_moving_averages()
            
            # Momentum Indicators
            self._calculate_rsi()
            self._calculate_macd()
            self._calculate_stochastic()
            
            # Volatility Indicators
            self._calculate_bollinger_bands()
            self._calculate_atr()
            
            # Trend Indicators
            self._calculate_adx()
            
        except Exception as e:
            logger.error(f"Error calculating indicators: {e}")
    
    def _calculate_moving_averages(self):
        """Calculate various moving averages"""
        # Simple Moving Averages
        for period in [7, 20, 50, 100, 200]:
            sma = SMAIndicator(self.df['close'], window=period)
            self.df[f'sma_{period}'] = sma.sma_indicator()
        
        # Exponential Moving Averages
        for period in [7, 20, 50, 100, 200]:
            ema = EMAIndicator(self.df['close'], window=period)
            self.df[f'ema_{period}'] = ema.ema_indicator()
    
    def _calculate_rsi(self):
        """Calculate RSI"""
        rsi = RSIIndicator(self.df['close'], window=settings.RSI_PERIOD)
        self.df['rsi'] = rsi.rsi()
    
    def _calculate_macd(self):
        """Calculate MACD"""
        macd = MACD(
            self.df['close'],
            window_fast=settings.MACD_FAST,
            window_slow=settings.MACD_SLOW,
            window_sign=settings.MACD_SIGNAL
        )
        self.df['macd'] = macd.macd()
        self.df['macd_signal'] = macd.macd_signal()
        self.df['macd_diff'] = macd.macd_diff()
    
    def _calculate_stochastic(self):
        """Calculate Stochastic Oscillator"""
        stoch = StochasticOscillator(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            window=settings.STOCHASTIC_K,
            smooth_window=settings.STOCHASTIC_D
        )
        self.df['stoch_k'] = stoch.stoch()
        self.df['stoch_d'] = stoch.stoch_signal()
    
    def _calculate_bollinger_bands(self):
        """Calculate Bollinger Bands"""
        bb = BollingerBands(
            self.df['close'],
            window=settings.BOLLINGER_PERIOD,
            window_dev=settings.BOLLINGER_STD
        )
        self.df['bb_upper'] = bb.bollinger_hband()
        self.df['bb_middle'] = bb.bollinger_mavg()
        self.df['bb_lower'] = bb.bollinger_lband()
        self.df['bb_width'] = bb.bollinger_wband()
        self.df['bb_pband'] = bb.bollinger_pband()
    
    def _calculate_atr(self):
        """Calculate Average True Range"""
        atr = AverageTrueRange(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            window=settings.ATR_PERIOD
        )
        self.df['atr'] = atr.average_true_range()
    
    def _calculate_adx(self):
        """Calculate ADX"""
        adx = ADXIndicator(
            self.df['high'],
            self.df['low'],
            self.df['close'],
            window=settings.ADX_PERIOD
        )
        self.df['adx'] = adx.adx()
        self.df['adx_pos'] = adx.adx_pos()
        self.df['adx_neg'] = adx.adx_neg()
    
    def analyze_trend(self) -> Dict:
        """
        Analyze trend using multiple indicators
        
        Returns:
            Dictionary with trend analysis
        """
        latest = self.df.iloc[-1]
        
        # Moving Average Analysis
        ma_signals = self._analyze_moving_averages(latest)
        
        # ADX Analysis
        adx_analysis = self._analyze_adx(latest)
        
        # Price Position
        price_position = self._analyze_price_position(latest)
        
        # Overall trend determination
        bullish_score = (
            ma_signals['bullish_count'] +
            (1 if adx_analysis['trend'] == TrendDirection.BULLISH else 0) +
            (1 if price_position == 'above_mas' else 0)
        )
        
        bearish_score = (
            ma_signals['bearish_count'] +
            (1 if adx_analysis['trend'] == TrendDirection.BEARISH else 0) +
            (1 if price_position == 'below_mas' else 0)
        )
        
        if bullish_score > bearish_score + 2:
            trend = TrendDirection.BULLISH
        elif bearish_score > bullish_score + 2:
            trend = TrendDirection.BEARISH
        else:
            trend = TrendDirection.RANGING
        
        return {
            'trend': trend,
            'strength': adx_analysis['strength'],
            'ma_alignment': ma_signals,
            'adx_value': adx_analysis['value'],
            'price_position': price_position,
            'bullish_score': bullish_score,
            'bearish_score': bearish_score
        }
    
    def _analyze_moving_averages(self, latest: pd.Series) -> Dict:
        """Analyze moving average alignment"""
        ma_periods = [7, 20, 50, 200]
        
        bullish_count = 0
        bearish_count = 0
        
        # Check if EMAs are in order
        for i in range(len(ma_periods) - 1):
            current_ma = latest.get(f'ema_{ma_periods[i]}', 0)
            next_ma = latest.get(f'ema_{ma_periods[i+1]}', 0)
            
            if current_ma > next_ma:
                bullish_count += 1
            elif current_ma < next_ma:
                bearish_count += 1
        
        # Check price position relative to key MAs
        if latest['close'] > latest.get('ema_20', 0):
            bullish_count += 1
        else:
            bearish_count += 1
        
        return {
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'alignment': 'bullish' if bullish_count > bearish_count else 'bearish'
        }
    
    def _analyze_adx(self, latest: pd.Series) -> Dict:
        """Analyze ADX for trend strength"""
        adx_value = latest.get('adx', 0)
        adx_pos = latest.get('adx_pos', 0)
        adx_neg = latest.get('adx_neg', 0)
        
        # Determine trend strength
        if adx_value > 50:
            strength = "VERY_STRONG"
        elif adx_value > 25:
            strength = "STRONG"
        elif adx_value > 20:
            strength = "MODERATE"
        else:
            strength = "WEAK"
        
        # Determine trend direction
        if adx_pos > adx_neg:
            trend = TrendDirection.BULLISH
        elif adx_neg > adx_pos:
            trend = TrendDirection.BEARISH
        else:
            trend = TrendDirection.RANGING
        
        return {
            'value': adx_value,
            'strength': strength,
            'trend': trend
        }
    
    def _analyze_price_position(self, latest: pd.Series) -> str:
        """Analyze price position relative to moving averages"""
        price = latest['close']
        ema_20 = latest.get('ema_20', price)
        ema_50 = latest.get('ema_50', price)
        
        if price > ema_20 and price > ema_50:
            return 'above_mas'
        elif price < ema_20 and price < ema_50:
            return 'below_mas'
        else:
            return 'between_mas'
    
    def analyze_momentum(self) -> Dict:
        """
        Analyze momentum indicators
        
        Returns:
            Dictionary with momentum analysis
        """
        latest = self.df.iloc[-1]
        
        # RSI Analysis
        rsi_signal = self._analyze_rsi(latest)
        
        # MACD Analysis
        macd_signal = self._analyze_macd(latest)
        
        # Stochastic Analysis
        stoch_signal = self._analyze_stochastic(latest)
        
        # Overall momentum
        bullish_signals = sum([
            rsi_signal == SignalType.BUY,
            macd_signal == SignalType.BUY,
            stoch_signal == SignalType.BUY
        ])
        
        bearish_signals = sum([
            rsi_signal == SignalType.SELL,
            macd_signal == SignalType.SELL,
            stoch_signal == SignalType.SELL
        ])
        
        if bullish_signals >= 2:
            overall = SignalType.BUY
        elif bearish_signals >= 2:
            overall = SignalType.SELL
        else:
            overall = SignalType.NEUTRAL
        
        return {
            'overall': overall,
            'rsi': {
                'value': latest.get('rsi', 50),
                'signal': rsi_signal
            },
            'macd': {
                'value': latest.get('macd', 0),
                'signal': macd_signal
            },
            'stochastic': {
                'k': latest.get('stoch_k', 50),
                'd': latest.get('stoch_d', 50),
                'signal': stoch_signal
            },
            'bullish_count': bullish_signals,
            'bearish_count': bearish_signals
        }
    
    def _analyze_rsi(self, latest: pd.Series) -> SignalType:
        """Analyze RSI"""
        rsi = latest.get('rsi', 50)
        
        if rsi < settings.RSI_OVERSOLD:
            return SignalType.BUY
        elif rsi > settings.RSI_OVERBOUGHT:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL
    
    def _analyze_macd(self, latest: pd.Series) -> SignalType:
        """Analyze MACD"""
        macd = latest.get('macd', 0)
        macd_signal = latest.get('macd_signal', 0)
        macd_diff = latest.get('macd_diff', 0)
        
        # Check for crossover
        prev = self.df.iloc[-2]
        prev_diff = prev.get('macd_diff', 0)
        
        # Bullish crossover
        if macd_diff > 0 and prev_diff <= 0:
            return SignalType.BUY
        # Bearish crossover
        elif macd_diff < 0 and prev_diff >= 0:
            return SignalType.SELL
        # No crossover, check position
        elif macd > macd_signal and macd_diff > 0:
            return SignalType.BUY
        elif macd < macd_signal and macd_diff < 0:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL
    
    def _analyze_stochastic(self, latest: pd.Series) -> SignalType:
        """Analyze Stochastic"""
        k = latest.get('stoch_k', 50)
        d = latest.get('stoch_d', 50)
        
        # Oversold and bullish crossover
        if k < 20 and k > d:
            return SignalType.BUY
        # Overbought and bearish crossover
        elif k > 80 and k < d:
            return SignalType.SELL
        else:
            return SignalType.NEUTRAL
    
    def analyze_volatility(self) -> Dict:
        """
        Analyze volatility
        
        Returns:
            Dictionary with volatility analysis
        """
        latest = self.df.iloc[-1]
        
        # ATR Analysis
        atr = latest.get('atr', 0)
        atr_sma = self.df['atr'].tail(20).mean()
        
        if atr > atr_sma * 1.5:
            volatility = "HIGH"
        elif atr > atr_sma:
            volatility = "MODERATE"
        else:
            volatility = "LOW"
        
        # Bollinger Band Analysis
        bb_width = latest.get('bb_width', 0)
        bb_position = latest.get('bb_pband', 0.5)
        
        # Price position in BB
        if bb_position > 0.8:
            bb_signal = "OVERBOUGHT"
        elif bb_position < 0.2:
            bb_signal = "OVERSOLD"
        else:
            bb_signal = "NEUTRAL"
        
        return {
            'level': volatility,
            'atr': atr,
            'atr_sma': atr_sma,
            'bb_width': bb_width,
            'bb_position': bb_position,
            'bb_signal': bb_signal
        }
    
    def get_support_resistance_from_pivot(self) -> Dict:
        """Calculate pivot points for support/resistance"""
        latest = self.df.iloc[-1]
        prev = self.df.iloc[-2]
        
        # Standard Pivot Points
        pivot = (prev['high'] + prev['low'] + prev['close']) / 3
        
        r1 = 2 * pivot - prev['low']
        r2 = pivot + (prev['high'] - prev['low'])
        r3 = r1 + (prev['high'] - prev['low'])
        
        s1 = 2 * pivot - prev['high']
        s2 = pivot - (prev['high'] - prev['low'])
        s3 = s1 - (prev['high'] - prev['low'])
        
        return {
            'pivot': pivot,
            'resistance': {
                'r1': r1,
                'r2': r2,
                'r3': r3
            },
            'support': {
                's1': s1,
                's2': s2,
                's3': s3
            }
        }
    
    def check_divergence(self) -> Dict:
        """Check for divergences between price and indicators"""
        divergences = {
            'rsi': self._check_rsi_divergence(),
            'macd': self._check_macd_divergence()
        }
        
        return divergences
    
    def _check_rsi_divergence(self) -> Optional[str]:
        """Check RSI divergence"""
        if len(self.df) < 50:
            return None
        
        recent = self.df.tail(50)
        
        # Find swing highs in price
        price_highs = recent['high'].rolling(5, center=True).max()
        rsi_highs = recent['rsi'].rolling(5, center=True).max()
        
        # Check bearish divergence (price higher high, RSI lower high)
        if price_highs.iloc[-5] < price_highs.iloc[-1]:
            if rsi_highs.iloc[-5] > rsi_highs.iloc[-1]:
                return "BEARISH_DIVERGENCE"
        
        # Find swing lows
        price_lows = recent['low'].rolling(5, center=True).min()
        rsi_lows = recent['rsi'].rolling(5, center=True).min()
        
        # Check bullish divergence (price lower low, RSI higher low)
        if price_lows.iloc[-5] > price_lows.iloc[-1]:
            if rsi_lows.iloc[-5] < rsi_lows.iloc[-1]:
                return "BULLISH_DIVERGENCE"
        
        return None
    
    def _check_macd_divergence(self) -> Optional[str]:
        """Check MACD divergence"""
        if len(self.df) < 50:
            return None
        
        recent = self.df.tail(50)
        
        # Similar logic to RSI
        price_highs = recent['high'].rolling(5, center=True).max()
        macd_highs = recent['macd'].rolling(5, center=True).max()
        
        if price_highs.iloc[-5] < price_highs.iloc[-1]:
            if macd_highs.iloc[-5] > macd_highs.iloc[-1]:
                return "BEARISH_DIVERGENCE"
        
        price_lows = recent['low'].rolling(5, center=True).min()
        macd_lows = recent['macd'].rolling(5, center=True).min()
        
        if price_lows.iloc[-5] > price_lows.iloc[-1]:
            if macd_lows.iloc[-5] < macd_lows.iloc[-1]:
                return "BULLISH_DIVERGENCE"
        
        return None
