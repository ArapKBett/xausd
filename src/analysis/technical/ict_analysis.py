import pandas as pd
import numpy as np
from datetime import datetime, time
from typing import Dict, List, Tuple, Optional
from src.config.settings import settings
from src.config.constants import OrderBlockType, LiquidityType, SignalType
from src.utils.logger import logger
from src.utils.helpers import is_kill_zone, get_kill_zone_weight

class ICTAnalysis:
    """
    Inner Circle Trader (ICT) Concepts Implementation
    - Order Blocks
    - Fair Value Gaps (FVG)
    - Liquidity Sweeps
    - Break of Structure (BOS)
    - Change of Character (CHoCH)
    - Market Maker Model
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        self.order_blocks = []
        self.fair_value_gaps = []
        self.liquidity_pools = []
        
    def full_ict_analysis(self) -> Dict:
        """
        Perform complete ICT analysis
        
        Returns:
            Dictionary with all ICT concepts analyzed
        """
        return {
            'order_blocks': self.identify_order_blocks(),
            'fair_value_gaps': self.identify_fair_value_gaps(),
            'liquidity': self.identify_liquidity_pools(),
            'market_structure': self.analyze_market_structure(),
            'kill_zone': self.analyze_kill_zone(),
            'optimal_trade_entry': self.find_optimal_trade_entry(),
            'breaker_blocks': self.identify_breaker_blocks()
        }
    
    def identify_order_blocks(self) -> List[Dict]:
        """
        Identify bullish and bearish order blocks
        
        An order block is the last down candle before a strong bullish move
        or the last up candle before a strong bearish move
        """
        order_blocks = []
        lookback = settings.ORDER_BLOCK_LOOKBACK
        
        if len(self.df) < lookback:
            return order_blocks
        
        for i in range(lookback, len(self.df) - 1):
            current = self.df.iloc[i]
            next_candle = self.df.iloc[i + 1]
            
            # Calculate move strength
            move_size = abs(next_candle['close'] - next_candle['open'])
            avg_range = self.df['high'].iloc[i-20:i] - self.df['low'].iloc[i-20:i]
            avg_range = avg_range.mean()
            
            # Bullish Order Block: Last red candle before strong green candle
            if (current['close'] < current['open'] and  # Red candle
                next_candle['close'] > next_candle['open'] and  # Green candle
                move_size > avg_range * 1.5):  # Strong move
                
                order_blocks.append({
                    'type': OrderBlockType.BULLISH_OB,
                    'timestamp': self.df.index[i],
                    'high': current['high'],
                    'low': current['low'],
                    'open': current['open'],
                    'close': current['close'],
                    'strength': move_size / avg_range,
                    'tested': False
                })
            
            # Bearish Order Block: Last green candle before strong red candle
            elif (current['close'] > current['open'] and  # Green candle
                  next_candle['close'] < next_candle['open'] and  # Red candle
                  move_size > avg_range * 1.5):  # Strong move
                
                order_blocks.append({
                    'type': OrderBlockType.BEARISH_OB,
                    'timestamp': self.df.index[i],
                    'high': current['high'],
                    'low': current['low'],
                    'open': current['open'],
                    'close': current['close'],
                    'strength': move_size / avg_range,
                    'tested': False
                })
        
        # Keep only recent and untested order blocks
        self.order_blocks = order_blocks[-10:]
        
        return self.order_blocks
    
    def identify_fair_value_gaps(self) -> List[Dict]:
        """
        Identify Fair Value Gaps (FVG)
        
        A FVG occurs when there's a gap between candles that hasn't been filled
        """
        fvgs = []
        min_gap_pips = settings.FVG_MIN_SIZE_PIPS
        min_gap_price = min_gap_pips * settings.PIP_VALUE
        
        for i in range(2, len(self.df)):
            candle1 = self.df.iloc[i - 2]
            candle2 = self.df.iloc[i - 1]
            candle3 = self.df.iloc[i]
            
            # Bullish FVG: Gap between candle1 high and candle3 low
            if candle3['low'] > candle1['high']:
                gap_size = candle3['low'] - candle1['high']
                
                if gap_size >= min_gap_price:
                    fvgs.append({
                        'type': 'BULLISH_FVG',
                        'timestamp': self.df.index[i],
                        'gap_high': candle3['low'],
                        'gap_low': candle1['high'],
                        'gap_size': gap_size,
                        'filled': False
                    })
            
            # Bearish FVG: Gap between candle1 low and candle3 high
            elif candle3['high'] < candle1['low']:
                gap_size = candle1['low'] - candle3['high']
                
                if gap_size >= min_gap_price:
                    fvgs.append({
                        'type': 'BEARISH_FVG',
                        'timestamp': self.df.index[i],
                        'gap_high': candle1['low'],
                        'gap_low': candle3['high'],
                        'gap_size': gap_size,
                        'filled': False
                    })
        
        # Check if FVGs have been filled
        current_price = self.df['close'].iloc[-1]
        for fvg in fvgs:
            if fvg['gap_low'] <= current_price <= fvg['gap_high']:
                fvg['filled'] = True
        
        # Keep only unfilled FVGs
        self.fair_value_gaps = [fvg for fvg in fvgs if not fvg['filled']][-10:]
        
        return self.fair_value_gaps
    
    def identify_liquidity_pools(self) -> Dict:
        """
        Identify liquidity pools (equal highs/lows, stop loss clusters)
        """
        liquidity = {
            'buy_side': [],  # Above market (stops above highs)
            'sell_side': []  # Below market (stops below lows)
        }
        
        # Find swing points
        swing_period = 5
        
        for i in range(swing_period, len(self.df) - swing_period):
            window = self.df.iloc[i-swing_period:i+swing_period+1]
            current = self.df.iloc[i]
            
            # Swing High (buy-side liquidity)
            if current['high'] == window['high'].max():
                liquidity['buy_side'].append({
                    'price': current['high'],
                    'timestamp': self.df.index[i],
                    'type': LiquidityType.BUY_SIDE,
                    'swept': False
                })
            
            # Swing Low (sell-side liquidity)
            if current['low'] == window['low'].min():
                liquidity['sell_side'].append({
                    'price': current['low'],
                    'timestamp': self.df.index[i],
                    'type': LiquidityType.SELL_SIDE,
                    'swept': False
                })
        
        # Identify equal highs and lows
        liquidity['equal_highs'] = self._find_equal_levels(
            [liq['price'] for liq in liquidity['buy_side']]
        )
        liquidity['equal_lows'] = self._find_equal_levels(
            [liq['price'] for liq in liquidity['sell_side']]
        )
        
        # Check for liquidity sweeps
        current_price = self.df['close'].iloc[-1]
        recent_high = self.df['high'].tail(10).max()
        recent_low = self.df['low'].tail(10).min()
        
        # Check if buy-side liquidity was swept
        for liq in liquidity['buy_side'][-5:]:
            if recent_high > liq['price']:
                liq['swept'] = True
        
        # Check if sell-side liquidity was swept
        for liq in liquidity['sell_side'][-5:]:
            if recent_low < liq['price']:
                liq['swept'] = True
        
        self.liquidity_pools = liquidity
        return liquidity
    
    def _find_equal_levels(self, prices: List[float]) -> List[Dict]:
        """Find equal price levels (within tolerance)"""
        if not prices:
            return []
        
        equal_levels = []
        tolerance = settings.LIQUIDITY_SWEEP_PIPS * settings.PIP_VALUE
        
        prices_sorted = sorted(prices)
        
        i = 0
        while i < len(prices_sorted):
            current_level = prices_sorted[i]
            equal_count = 1
            
            # Count how many prices are equal (within tolerance)
            j = i + 1
            while j < len(prices_sorted) and abs(prices_sorted[j] - current_level) <= tolerance:
                equal_count += 1
                j += 1
            
            # If we have at least 2 equal levels, it's significant
            if equal_count >= 2:
                equal_levels.append({
                    'price': current_level,
                    'count': equal_count,
                    'strength': equal_count / len(prices)
                })
            
            i = j
        
        return equal_levels
    
    def analyze_market_structure(self) -> Dict:
        """
        Analyze market structure (BOS, CHoCH, Inducement)
        
        BOS (Break of Structure): Price breaks previous high/low in trend direction
        CHoCH (Change of Character): Price breaks counter-trend, signaling reversal
        """
        structure = {
            'current_structure': None,
            'bos_levels': [],
            'choch_levels': [],
            'inducement_detected': False
        }
        
        # Identify swing highs and lows
        swing_highs = []
        swing_lows = []
        
        for i in range(5, len(self.df) - 5):
            window = self.df.iloc[i-5:i+6]
            current = self.df.iloc[i]
            
            if current['high'] == window['high'].max():
                swing_highs.append({'price': current['high'], 'index': i})
            
            if current['low'] == window['low'].min():
                swing_lows.append({'price': current['low'], 'index': i})
        
        # Analyze structure
        if len(swing_highs) >= 2 and len(swing_lows) >= 2:
            # Check for higher highs and higher lows (uptrend)
            recent_highs = [sh['price'] for sh in swing_highs[-3:]]
            recent_lows = [sl['price'] for sl in swing_lows[-3:]]
            
            if len(recent_highs) >= 2:
                if recent_highs[-1] > recent_highs[-2]:
                    structure['bos_levels'].append({
                        'type': 'BULLISH_BOS',
                        'level': recent_highs[-2],
                        'broken_at': recent_highs[-1]
                    })
            
            if len(recent_lows) >= 2:
                if recent_lows[-1] > recent_lows[-2]:
                    structure['current_structure'] = 'BULLISH'
                elif recent_lows[-1] < recent_lows[-2]:
                    structure['choch_levels'].append({
                        'type': 'BEARISH_CHOCH',
                        'level': recent_lows[-2]
                    })
                    structure['current_structure'] = 'BEARISH'
        
        # Detect inducement (fake-out move before real move)
        if len(self.df) >= 20:
            recent_candles = self.df.tail(20)
            
            # Look for quick reversal after touching liquidity
            for i in range(len(recent_candles) - 5):
                candle = recent_candles.iloc[i]
                next_5 = recent_candles.iloc[i+1:i+6]
                
                # Inducement high (fake breakout up then reversal down)
                if candle['high'] > recent_candles['high'].iloc[:i].max():
                    if next_5['close'].iloc[-1] < candle['open']:
                        structure['inducement_detected'] = True
                
                # Inducement low (fake breakout down then reversal up)
                if candle['low'] < recent_candles['low'].iloc[:i].min():
                    if next_5['close'].iloc[-1] > candle['open']:
                        structure['inducement_detected'] = True
        
        return structure
    
    def analyze_kill_zone(self) -> Dict:
        """
        Analyze if current time is in ICT kill zone
        """
        now = datetime.now(settings.TIMEZONE)
        is_kz, zone_name = is_kill_zone(now)
        
        return {
            'in_kill_zone': is_kz,
            'zone_name': zone_name,
            'zone_weight': get_kill_zone_weight(now),
            'current_time': now.strftime('%H:%M UTC'),
            'all_zones': settings.ICT_KILL_ZONES
        }
    
    def find_optimal_trade_entry(self) -> Optional[Dict]:
        """
        Find optimal trade entry based on ICT concepts
        
        Looks for:
        1. Order block in higher timeframe
        2. FVG that needs to be filled
        3. Price at discount/premium
        4. In kill zone
        """
        if not self.order_blocks and not self.fair_value_gaps:
            return None
        
        current_price = self.df['close'].iloc[-1]
        recent_high = self.df['high'].tail(50).max()
        recent_low = self.df['low'].tail(50).min()
        
        # Calculate if price is at discount or premium
        range_size = recent_high - recent_low
        price_position = (current_price - recent_low) / range_size
        
        if price_position <= 0.5:
            zone = "DISCOUNT"  # Good for buying
        else:
            zone = "PREMIUM"  # Good for selling
        
        optimal_entry = {
            'zone': zone,
            'price_position': price_position,
            'entries': []
        }
        
        # Look for bullish setups in discount zone
        if zone == "DISCOUNT":
            for ob in self.order_blocks:
                if ob['type'] == OrderBlockType.BULLISH_OB and not ob['tested']:
                    if current_price <= ob['high'] and current_price >= ob['low']:
                        optimal_entry['entries'].append({
                            'type': 'ORDER_BLOCK',
                            'direction': SignalType.BUY,
                            'entry_zone_high': ob['high'],
                            'entry_zone_low': ob['low'],
                            'strength': ob['strength']
                        })
            
            for fvg in self.fair_value_gaps:
                if fvg['type'] == 'BULLISH_FVG' and not fvg['filled']:
                    if current_price <= fvg['gap_high']:
                        optimal_entry['entries'].append({
                            'type': 'FAIR_VALUE_GAP',
                            'direction': SignalType.BUY,
                            'entry_zone_high': fvg['gap_high'],
                            'entry_zone_low': fvg['gap_low'],
                            'gap_size': fvg['gap_size']
                        })
        
        # Look for bearish setups in premium zone
        elif zone == "PREMIUM":
            for ob in self.order_blocks:
                if ob['type'] == OrderBlockType.BEARISH_OB and not ob['tested']:
                    if current_price <= ob['high'] and current_price >= ob['low']:
                        optimal_entry['entries'].append({
                            'type': 'ORDER_BLOCK',
                            'direction': SignalType.SELL,
                            'entry_zone_high': ob['high'],
                            'entry_zone_low': ob['low'],
                            'strength': ob['strength']
                        })
            
            for fvg in self.fair_value_gaps:
                if fvg['type'] == 'BEARISH_FVG' and not fvg['filled']:
                    if current_price >= fvg['gap_low']:
                        optimal_entry['entries'].append({
                            'type': 'FAIR_VALUE_GAP',
                            'direction': SignalType.SELL,
                            'entry_zone_high': fvg['gap_high'],
                            'entry_zone_low': fvg['gap_low'],
                            'gap_size': fvg['gap_size']
                        })
        
        return optimal_entry if optimal_entry['entries'] else None
    
    def identify_breaker_blocks(self) -> List[Dict]:
        """
        Identify breaker blocks (failed order blocks that become opposite)
        
        A breaker block is an order block that was broken and now acts
        as the opposite (resistance becomes support, support becomes resistance)
        """
        breaker_blocks = []
        
        if not self.order_blocks:
            return breaker_blocks
        
        current_price = self.df['close'].iloc[-1]
        
        for ob in self.order_blocks:
            # Check if bullish OB was broken (price went below it)
            if ob['type'] == OrderBlockType.BULLISH_OB:
                if current_price < ob['low']:
                    # Check if it held on retest
                    recent_data = self.df.tail(10)
                    if any(recent_data['low'] <= ob['high'] and recent_data['close'] < ob['low']):
                        breaker_blocks.append({
                            'type': OrderBlockType.BREAKER_BEARISH,
                            'original_type': OrderBlockType.BULLISH_OB,
                            'high': ob['high'],
                            'low': ob['low'],
                            'timestamp': ob['timestamp'],
                            'confidence': 'HIGH' if ob['strength'] > 2 else 'MEDIUM'
                        })
            
            # Check if bearish OB was broken (price went above it)
            elif ob['type'] == OrderBlockType.BEARISH_OB:
                if current_price > ob['high']:
                    recent_data = self.df.tail(10)
                    if any(recent_data['high'] >= ob['low'] and recent_data['close'] > ob['high']):
                        breaker_blocks.append({
                            'type': OrderBlockType.BREAKER_BULLISH,
                            'original_type': OrderBlockType.BEARISH_OB,
                            'high': ob['high'],
                            'low': ob['low'],
                            'timestamp': ob['timestamp'],
                            'confidence': 'HIGH' if ob['strength'] > 2 else 'MEDIUM'
                        })
        
        return breaker_blocks
    
    def get_market_maker_model_bias(self) -> Dict:
        """
        Determine market maker model bias
        
        Market makers:
        1. Accumulate positions
        2. Manipulate price (stop hunt)
        3. Distribute (real move)
        """
        recent_data = self.df.tail(50)
        
        # Look for consolidation (accumulation)
        recent_range = recent_data['high'].max() - recent_data['low'].min()
        avg_range = (recent_data['high'] - recent_data['low']).mean()
        
        is_consolidating = recent_range < avg_range * 3
        
        # Look for manipulation (sudden spike then reversal)
        manipulation_detected = False
        for i in range(len(recent_data) - 5):
            candle = recent_data.iloc[i]
            next_candles = recent_data.iloc[i+1:i+4]
            
            # Bullish manipulation (spike up then down)
            if candle['high'] > recent_data['high'].iloc[:i].max():
                if all(next_candles['close'] < candle['open']):
                    manipulation_detected = True
            
            # Bearish manipulation (spike down then up)
            if candle['low'] < recent_data['low'].iloc[:i].min():
                if all(next_candles['close'] > candle['open']):
                    manipulation_detected = True
        
        # Determine phase
        if is_consolidating and not manipulation_detected:
            phase = "ACCUMULATION"
            bias = SignalType.NEUTRAL
        elif manipulation_detected:
            phase = "MANIPULATION"
            # Bias is opposite of manipulation direction
            if recent_data['close'].iloc[-1] > recent_data['close'].iloc[-5]:
                bias = SignalType.SELL  # After bullish manipulation, expect bearish move
            else:
                bias = SignalType.BUY  # After bearish manipulation, expect bullish move
        else:
            phase = "DISTRIBUTION"
            # Follow the trend
            if recent_data['close'].iloc[-1] > recent_data['close'].iloc[-20]:
                bias = SignalType.BUY
            else:
                bias = SignalType.SELL
        
        return {
            'phase': phase,
            'bias': bias,
            'consolidating': is_consolidating,
            'manipulation_detected': manipulation_detected,
            'confidence': 'HIGH' if manipulation_detected else 'MEDIUM'
        }
