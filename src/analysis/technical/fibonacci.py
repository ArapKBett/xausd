import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from src.config.settings import settings
from src.config.constants import TrendDirection
from src.utils.logger import logger

class FibonacciAnalysis:
    """
    Advanced Fibonacci analysis for forex trading
    Includes retracement, extension, and projection levels
    """
    
    # Standard Fibonacci ratios
    RETRACEMENT_LEVELS = [0.236, 0.382, 0.5, 0.618, 0.786]
    EXTENSION_LEVELS = [1.272, 1.414, 1.618, 2.0, 2.618]
    PROJECTION_LEVELS = [0.618, 1.0, 1.272, 1.618]
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
    def calculate_retracement(self, swing_high: float = None, swing_low: float = None) -> Dict:
        """
        Calculate Fibonacci retracement levels
        
        Args:
            swing_high: High point of the move
            swing_low: Low point of the move
            
        Returns:
            Dictionary with retracement levels
        """
        if swing_high is None or swing_low is None:
            # Auto-detect swing points
            swing_high, swing_low = self._find_recent_swing()
        
        # Determine direction
        if swing_high > swing_low:
            direction = 'uptrend'
            diff = swing_high - swing_low
        else:
            direction = 'downtrend'
            diff = swing_low - swing_high
            swing_high, swing_low = swing_low, swing_high
        
        levels = {
            'swing_high': swing_high,
            'swing_low': swing_low,
            'direction': direction,
            'range': diff,
            'levels': {}
        }
        
        # Calculate retracement levels
        for ratio in self.RETRACEMENT_LEVELS:
            if direction == 'uptrend':
                price = swing_high - (diff * ratio)
            else:
                price = swing_low + (diff * ratio)
            
            levels['levels'][f'{ratio:.3f}'] = {
                'price': price,
                'ratio': ratio,
                'type': 'retracement'
            }
        
        # Add 0% and 100% levels
        levels['levels']['0.000'] = {
            'price': swing_high if direction == 'uptrend' else swing_low,
            'ratio': 0.0,
            'type': 'retracement'
        }
        levels['levels']['1.000'] = {
            'price': swing_low if direction == 'uptrend' else swing_high,
            'ratio': 1.0,
            'type': 'retracement'
        }
        
        return levels
    
    def calculate_extension(self, swing_high: float = None, swing_low: float = None) -> Dict:
        """
        Calculate Fibonacci extension levels (for profit targets)
        
        Args:
            swing_high: High point of the move
            swing_low: Low point of the move
            
        Returns:
            Dictionary with extension levels
        """
        if swing_high is None or swing_low is None:
            swing_high, swing_low = self._find_recent_swing()
        
        # Determine direction
        if swing_high > swing_low:
            direction = 'uptrend'
            diff = swing_high - swing_low
        else:
            direction = 'downtrend'
            diff = swing_low - swing_high
            swing_high, swing_low = swing_low, swing_high
        
        levels = {
            'swing_high': swing_high,
            'swing_low': swing_low,
            'direction': direction,
            'range': diff,
            'levels': {}
        }
        
        # Calculate extension levels
        for ratio in self.EXTENSION_LEVELS:
            if direction == 'uptrend':
                price = swing_high + (diff * (ratio - 1))
            else:
                price = swing_low - (diff * (ratio - 1))
            
            levels['levels'][f'{ratio:.3f}'] = {
                'price': price,
                'ratio': ratio,
                'type': 'extension'
            }
        
        return levels
    
    def calculate_projection(self, point_a: float = None, point_b: float = None, 
                           point_c: float = None) -> Dict:
        """
        Calculate Fibonacci projection (ABC projection)
        Used for projecting the third wave in a trend
        
        Args:
            point_a: First pivot
            point_b: Second pivot (retracement)
            point_c: Third pivot (current position)
            
        Returns:
            Dictionary with projection levels
        """
        if None in [point_a, point_b, point_c]:
            # Auto-detect ABC pattern
            point_a, point_b, point_c = self._find_abc_pattern()
        
        # Calculate AB distance
        ab_distance = abs(point_b - point_a)
        
        # Determine direction
        if point_b > point_a:
            direction = 'uptrend'
        else:
            direction = 'downtrend'
        
        levels = {
            'point_a': point_a,
            'point_b': point_b,
            'point_c': point_c,
            'direction': direction,
            'ab_distance': ab_distance,
            'levels': {}
        }
        
        # Calculate projection levels from point C
        for ratio in self.PROJECTION_LEVELS:
            if direction == 'uptrend':
                price = point_c + (ab_distance * ratio)
            else:
                price = point_c - (ab_distance * ratio)
            
            levels['levels'][f'{ratio:.3f}'] = {
                'price': price,
                'ratio': ratio,
                'type': 'projection'
            }
        
        return levels
    
    def _find_recent_swing(self) -> Tuple[float, float]:
        """Find most recent significant swing high and low"""
        lookback = min(100, len(self.df))
        recent_data = self.df.tail(lookback)
        
        swing_high = recent_data['high'].max()
        swing_low = recent_data['low'].min()
        
        return swing_high, swing_low
    
    def _find_abc_pattern(self) -> Tuple[float, float, float]:
        """Auto-detect ABC pattern in recent price action"""
        lookback = min(150, len(self.df))
        recent_data = self.df.tail(lookback)
        
        highs = recent_data['high'].values
        lows = recent_data['low'].values
        
        # Find three significant pivots
        from scipy.signal import argrelextrema
        
        high_indices = argrelextrema(highs, np.greater, order=5)[0]
        low_indices = argrelextrema(lows, np.less, order=5)[0]
        
        # Combine and sort by time
        all_pivots = []
        for idx in high_indices:
            all_pivots.append({'index': idx, 'price': highs[idx], 'type': 'high'})
        for idx in low_indices:
            all_pivots.append({'index': idx, 'price': lows[idx], 'type': 'low'})
        
        all_pivots.sort(key=lambda x: x['index'])
        
        # Get last 3 pivots
        if len(all_pivots) >= 3:
            point_a = all_pivots[-3]['price']
            point_b = all_pivots[-2]['price']
            point_c = all_pivots[-1]['price']
        else:
            # Fallback
            point_a = highs[0] if highs[0] > lows[0] else lows[0]
            point_b = lows[len(lows)//2] if point_a == highs[0] else highs[len(highs)//2]
            point_c = recent_data['close'].iloc[-1]
        
        return point_a, point_b, point_c
    
    def find_fibonacci_confluences(self, retracement: Dict, extension: Dict) -> List[Dict]:
        """
        Find price levels where multiple Fibonacci levels converge
        
        Args:
            retracement: Retracement levels dictionary
            extension: Extension levels dictionary
            
        Returns:
            List of confluence zones
        """
        tolerance = 10 * settings.PIP_VALUE  # 10 pips tolerance
        confluences = []
        
        # Get all levels
        all_levels = []
        
        for level_name, level_data in retracement['levels'].items():
            all_levels.append({
                'price': level_data['price'],
                'type': 'retracement',
                'ratio': level_data['ratio']
            })
        
        for level_name, level_data in extension['levels'].items():
            all_levels.append({
                'price': level_data['price'],
                'type': 'extension',
                'ratio': level_data['ratio']
            })
        
        # Find confluences
        for i, level1 in enumerate(all_levels):
            confluence_group = [level1]
            
            for j, level2 in enumerate(all_levels):
                if i != j and abs(level1['price'] - level2['price']) <= tolerance:
                    confluence_group.append(level2)
            
            if len(confluence_group) >= 2:
                avg_price = np.mean([l['price'] for l in confluence_group])
                
                confluences.append({
                    'price': avg_price,
                    'count': len(confluence_group),
                    'levels': confluence_group,
                    'strength': len(confluence_group) / len(all_levels)
                })
        
        # Remove duplicates
        unique_confluences = []
        used_prices = set()
        
        for conf in confluences:
            price_key = round(conf['price'] / tolerance) * tolerance
            if price_key not in used_prices:
                unique_confluences.append(conf)
                used_prices.add(price_key)
        
        # Sort by strength
        unique_confluences.sort(key=lambda x: x['strength'], reverse=True)
        
        return unique_confluences
    
    def get_nearest_fib_level(self, price: float = None) -> Dict:
        """
        Get nearest Fibonacci level to current or specified price
        
        Args:
            price: Price to check (default: current price)
            
        Returns:
            Dictionary with nearest level info
        """
        if price is None:
            price = self.df['close'].iloc[-1]
        
        retracement = self.calculate_retracement()
        
        nearest_level = None
        min_distance = float('inf')
        
        for level_name, level_data in retracement['levels'].items():
            distance = abs(price - level_data['price'])
            
            if distance < min_distance:
                min_distance = distance
                nearest_level = {
                    'name': level_name,
                    'price': level_data['price'],
                    'ratio': level_data['ratio'],
                    'distance_pips': distance / settings.PIP_VALUE,
                    'type': level_data['type']
                }
        
        return nearest_level
    
    def is_at_golden_ratio(self, price: float = None, tolerance_pips: int = 5) -> Dict:
        """
        Check if price is at 0.618 or 1.618 golden ratio levels
        
        Args:
            price: Price to check
            tolerance_pips: Tolerance in pips
            
        Returns:
            Dictionary with golden ratio info
        """
        if price is None:
            price = self.df['close'].iloc[-1]
        
        tolerance = tolerance_pips * settings.PIP_VALUE
        
        retracement = self.calculate_retracement()
        extension = self.calculate_extension()
        
        at_golden_retracement = False
        at_golden_extension = False
        
        # Check 0.618 retracement
        if '0.618' in retracement['levels']:
            ret_618 = retracement['levels']['0.618']['price']
            if abs(price - ret_618) <= tolerance:
                at_golden_retracement = True
        
        # Check 1.618 extension
        if '1.618' in extension['levels']:
            ext_1618 = extension['levels']['1.618']['price']
            if abs(price - ext_1618) <= tolerance:
                at_golden_extension = True
        
        return {
            'at_golden_retracement': at_golden_retracement,
            'at_golden_extension': at_golden_extension,
            'is_at_golden_ratio': at_golden_retracement or at_golden_extension,
            'significance': 'HIGH' if (at_golden_retracement or at_golden_extension) else 'NONE'
        }
    
    def get_potential_targets(self, entry_price: float, direction: str) -> List[Dict]:
        """
        Get potential profit targets using Fibonacci extensions
        
        Args:
            entry_price: Entry price of trade
            direction: 'buy' or 'sell'
            
        Returns:
            List of target levels
        """
        extension = self.calculate_extension()
        targets = []
        
        for level_name, level_data in extension['levels'].items():
            level_price = level_data['price']
            
            # Only include levels in the direction of trade
            if direction.lower() == 'buy' and level_price > entry_price:
                distance_pips = (level_price - entry_price) / settings.PIP_VALUE
                targets.append({
                    'level': level_name,
                    'price': level_price,
                    'ratio': level_data['ratio'],
                    'distance_pips': distance_pips,
                    'risk_reward': distance_pips / 10  # Assuming 10 pip stop
                })
            
            elif direction.lower() == 'sell' and level_price < entry_price:
                distance_pips = (entry_price - level_price) / settings.PIP_VALUE
                targets.append({
                    'level': level_name,
                    'price': level_price,
                    'ratio': level_data['ratio'],
                    'distance_pips': distance_pips,
                    'risk_reward': distance_pips / 10
                })
        
        # Sort by distance
        targets.sort(key=lambda x: x['distance_pips'])
        
        return targets[:3]  # Return top 3 targets
    
    def analyze_fib_confluence_with_structure(self, support_resistance: Dict) -> List[Dict]:
        """
        Find areas where Fibonacci levels align with support/resistance
        
        Args:
            support_resistance: Support/resistance levels from SupportResistanceAnalysis
            
        Returns:
            List of high-probability zones
        """
        retracement = self.calculate_retracement()
        extension = self.calculate_extension()
        
        tolerance = 15 * settings.PIP_VALUE
        confluence_zones = []
        
        # Get all fib levels
        fib_levels = []
        for level_name, level_data in retracement['levels'].items():
            fib_levels.append(level_data['price'])
        for level_name, level_data in extension['levels'].items():
            fib_levels.append(level_data['price'])
        
        # Check against support levels
        for support in support_resistance.get('support', []):
            support_price = support['price']
            
            for fib_price in fib_levels:
                if abs(support_price - fib_price) <= tolerance:
                    confluence_zones.append({
                        'price': (support_price + fib_price) / 2,
                        'type': 'support_fib_confluence',
                        'support_strength': support.get('final_strength', 0.5),
                        'significance': 'HIGH',
                        'action': 'BUY_ZONE'
                    })
        
        # Check against resistance levels
        for resistance in support_resistance.get('resistance', []):
            resistance_price = resistance['price']
            
            for fib_price in fib_levels:
                if abs(resistance_price - fib_price) <= tolerance:
                    confluence_zones.append({
                        'price': (resistance_price + fib_price) / 2,
                        'type': 'resistance_fib_confluence',
                        'resistance_strength': resistance.get('final_strength', 0.5),
                        'significance': 'HIGH',
                        'action': 'SELL_ZONE'
                    })
        
        return confluence_zones
