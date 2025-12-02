import pandas as pd
import numpy as np
from typing import List, Dict, Tuple
from scipy.signal import argrelextrema
from src.config.settings import settings
from src.utils.logger import logger

class SupportResistanceAnalysis:
    """
    Advanced support and resistance detection using multiple methods
    Implements BabyPips concepts with institutional precision
    """
    
    def __init__(self, df: pd.DataFrame):
        self.df = df.copy()
        
    def find_all_levels(self) -> Dict:
        """
        Find all support and resistance levels using multiple methods
        
        Returns:
            Dictionary with support/resistance levels
        """
        levels = {
            'support': [],
            'resistance': [],
            'pivot_points': {},
            'psychological_levels': [],
            'dynamic_levels': {}
        }
        
        # 1. Pivot point levels
        levels['pivot_points'] = self._calculate_pivot_points()
        
        # 2. Swing highs and lows
        swing_levels = self._find_swing_levels()
        levels['support'].extend(swing_levels['support'])
        levels['resistance'].extend(swing_levels['resistance'])
        
        # 3. Historical test levels (touched multiple times)
        historical_levels = self._find_historical_levels()
        levels['support'].extend(historical_levels['support'])
        levels['resistance'].extend(historical_levels['resistance'])
        
        # 4. Psychological levels (round numbers)
        levels['psychological_levels'] = self._find_psychological_levels()
        
        # 5. Dynamic levels (moving averages)
        levels['dynamic_levels'] = self._calculate_dynamic_levels()
        
        # 6. Volume profile levels
        volume_levels = self._find_volume_profile_levels()
        levels['support'].extend(volume_levels['support'])
        levels['resistance'].extend(volume_levels['resistance'])
        
        # Consolidate and remove duplicates
        levels['support'] = self._consolidate_levels(levels['support'])
        levels['resistance'] = self._consolidate_levels(levels['resistance'])
        
        # Rank by strength
        levels['support'] = self._rank_levels(levels['support'], 'support')
        levels['resistance'] = self._rank_levels(levels['resistance'], 'resistance')
        
        return levels
    
    def _calculate_pivot_points(self) -> Dict:
        """Calculate standard pivot points"""
        high = self.df['high'].iloc[-1]
        low = self.df['low'].iloc[-1]
        close = self.df['close'].iloc[-2]  # Previous close
        
        pivot = (high + low + close) / 3
        
        # Standard levels
        r1 = 2 * pivot - low
        r2 = pivot + (high - low)
        r3 = high + 2 * (pivot - low)
        
        s1 = 2 * pivot - high
        s2 = pivot - (high - low)
        s3 = low - 2 * (high - pivot)
        
        # Camarilla levels
        cam_range = high - low
        
        h4 = close + (cam_range * 1.1) / 2
        h3 = close + (cam_range * 1.1) / 4
        h2 = close + (cam_range * 1.1) / 6
        h1 = close + (cam_range * 1.1) / 12
        
        l1 = close - (cam_range * 1.1) / 12
        l2 = close - (cam_range * 1.1) / 6
        l3 = close - (cam_range * 1.1) / 4
        l4 = close - (cam_range * 1.1) / 2
        
        return {
            'standard': {
                'pivot': pivot,
                'r1': r1, 'r2': r2, 'r3': r3,
                's1': s1, 's2': s2, 's3': s3
            },
            'camarilla': {
                'h1': h1, 'h2': h2, 'h3': h3, 'h4': h4,
                'l1': l1, 'l2': l2, 'l3': l3, 'l4': l4
            }
        }
    
    def _find_swing_levels(self, order: int = 5) -> Dict:
        """Find swing highs and lows"""
        highs = self.df['high'].values
        lows = self.df['low'].values
        
        # Find local maxima and minima
        high_indices = argrelextrema(highs, np.greater, order=order)[0]
        low_indices = argrelextrema(lows, np.less, order=order)[0]
        
        resistance_levels = []
        support_levels = []
        
        # Get swing highs (resistance)
        for idx in high_indices:
            if idx < len(highs) - 20:  # Not too recent
                resistance_levels.append({
                    'price': highs[idx],
                    'index': idx,
                    'touches': 1,
                    'strength': 1.0,
                    'type': 'swing_high'
                })
        
        # Get swing lows (support)
        for idx in low_indices:
            if idx < len(lows) - 20:
                support_levels.append({
                    'price': lows[idx],
                    'index': idx,
                    'touches': 1,
                    'strength': 1.0,
                    'type': 'swing_low'
                })
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    def _find_historical_levels(self, tolerance_pips: int = 10) -> Dict:
        """Find levels that have been tested multiple times"""
        highs = self.df['high'].values
        lows = self.df['low'].values
        
        tolerance = tolerance_pips * settings.PIP_VALUE
        
        support_clusters = []
        resistance_clusters = []
        
        # Cluster lows for support
        for i, low in enumerate(lows[:-50]):  # Exclude recent data
            touches = 1
            for j, other_low in enumerate(lows):
                if i != j and abs(low - other_low) <= tolerance:
                    touches += 1
            
            if touches >= 2:  # At least 2 touches
                support_clusters.append({
                    'price': low,
                    'touches': touches,
                    'strength': touches / len(lows),
                    'type': 'tested_support'
                })
        
        # Cluster highs for resistance
        for i, high in enumerate(highs[:-50]):
            touches = 1
            for j, other_high in enumerate(highs):
                if i != j and abs(high - other_high) <= tolerance:
                    touches += 1
            
            if touches >= 2:
                resistance_clusters.append({
                    'price': high,
                    'touches': touches,
                    'strength': touches / len(highs),
                    'type': 'tested_resistance'
                })
        
        return {
            'support': support_clusters,
            'resistance': resistance_clusters
        }
    
    def _find_psychological_levels(self) -> List[Dict]:
        """Find round number levels near current price"""
        current_price = self.df['close'].iloc[-1]
        
        # Determine the step based on price magnitude
        if current_price >= 10:
            steps = [0.1, 0.5, 1.0]
        else:
            steps = [0.001, 0.005, 0.01]
        
        psychological_levels = []
        
        for step in steps:
            # Find nearest round numbers
            lower = (int(current_price / step) - 2) * step
            upper = (int(current_price / step) + 3) * step
            
            level = lower
            while level <= upper:
                if abs(level - current_price) > step * 0.1:  # Not too close to current
                    psychological_levels.append({
                        'price': level,
                        'type': 'psychological',
                        'step': step,
                        'strength': 0.5
                    })
                level += step
        
        return psychological_levels
    
    def _calculate_dynamic_levels(self) -> Dict:
        """Calculate dynamic support/resistance (moving averages)"""
        dynamic_levels = {}
        
        # Calculate various MAs
        periods = [20, 50, 100, 200]
        
        for period in periods:
            if len(self.df) >= period:
                ma = self.df['close'].rolling(window=period).mean().iloc[-1]
                dynamic_levels[f'MA{period}'] = {
                    'price': ma,
                    'period': period,
                    'type': 'moving_average'
                }
        
        # EMA levels
        ema_periods = [9, 21, 55]
        for period in ema_periods:
            if len(self.df) >= period:
                ema = self.df['close'].ewm(span=period, adjust=False).mean().iloc[-1]
                dynamic_levels[f'EMA{period}'] = {
                    'price': ema,
                    'period': period,
                    'type': 'exponential_ma'
                }
        
        return dynamic_levels
    
    def _find_volume_profile_levels(self) -> Dict:
        """Find high volume nodes (VPOC - Volume Point of Control)"""
        if 'volume' not in self.df.columns:
            return {'support': [], 'resistance': []}
        
        # Create price bins
        price_min = self.df['low'].min()
        price_max = self.df['high'].max()
        
        bins = 50
        price_range = np.linspace(price_min, price_max, bins)
        
        volume_profile = np.zeros(bins - 1)
        
        # Accumulate volume in each price bin
        for i in range(len(self.df)):
            price = self.df['close'].iloc[i]
            volume = self.df['volume'].iloc[i]
            
            # Find which bin this price belongs to
            bin_idx = np.searchsorted(price_range, price) - 1
            if 0 <= bin_idx < len(volume_profile):
                volume_profile[bin_idx] += volume
        
        # Find high volume nodes (HVN)
        hvn_threshold = np.percentile(volume_profile, 70)
        
        support_levels = []
        resistance_levels = []
        current_price = self.df['close'].iloc[-1]
        
        for i, volume in enumerate(volume_profile):
            if volume >= hvn_threshold:
                price = (price_range[i] + price_range[i + 1]) / 2
                
                level = {
                    'price': price,
                    'volume': volume,
                    'strength': volume / volume_profile.max(),
                    'type': 'volume_node'
                }
                
                if price < current_price:
                    support_levels.append(level)
                else:
                    resistance_levels.append(level)
        
        return {
            'support': support_levels,
            'resistance': resistance_levels
        }
    
    def _consolidate_levels(self, levels: List[Dict], tolerance_pips: int = 10) -> List[Dict]:
        """Consolidate nearby levels"""
        if not levels:
            return []
        
        tolerance = tolerance_pips * settings.PIP_VALUE
        consolidated = []
        used = set()
        
        for i, level1 in enumerate(levels):
            if i in used:
                continue
            
            cluster = [level1]
            used.add(i)
            
            for j, level2 in enumerate(levels):
                if j not in used and abs(level1['price'] - level2['price']) <= tolerance:
                    cluster.append(level2)
                    used.add(j)
            
            # Average the cluster
            avg_price = np.mean([l['price'] for l in cluster])
            total_touches = sum([l.get('touches', 1) for l in cluster])
            avg_strength = np.mean([l.get('strength', 1.0) for l in cluster])
            
            consolidated.append({
                'price': avg_price,
                'touches': total_touches,
                'strength': avg_strength,
                'cluster_size': len(cluster),
                'types': list(set([l.get('type', 'unknown') for l in cluster]))
            })
        
        return consolidated
    
    def _rank_levels(self, levels: List[Dict], level_type: str) -> List[Dict]:
        """Rank levels by strength and relevance"""
        current_price = self.df['close'].iloc[-1]
        
        for level in levels:
            score = 0.0
            
            # Factor 1: Number of touches
            touches = level.get('touches', 1)
            score += min(touches * 0.2, 1.0)
            
            # Factor 2: Cluster size
            cluster_size = level.get('cluster_size', 1)
            score += min(cluster_size * 0.15, 0.75)
            
            # Factor 3: Distance from current price (closer = more relevant)
            distance = abs(level['price'] - current_price)
            distance_pips = distance / settings.PIP_VALUE
            
            if distance_pips <= 50:
                score += 0.5
            elif distance_pips <= 100:
                score += 0.3
            elif distance_pips <= 200:
                score += 0.1
            
            # Factor 4: Type of level
            types = level.get('types', [])
            if 'tested_support' in types or 'tested_resistance' in types:
                score += 0.3
            if 'volume_node' in types:
                score += 0.2
            if 'swing_high' in types or 'swing_low' in types:
                score += 0.15
            
            level['final_strength'] = min(score, 1.0)
        
        # Sort by strength
        levels.sort(key=lambda x: x['final_strength'], reverse=True)
        
        return levels
    
    def get_nearest_levels(self, direction: str = 'both', count: int = 3) -> Dict:
        """
        Get nearest support/resistance levels
        
        Args:
            direction: 'support', 'resistance', or 'both'
            count: Number of levels to return
        
        Returns:
            Dictionary with nearest levels
        """
        all_levels = self.find_all_levels()
        current_price = self.df['close'].iloc[-1]
        
        result = {}
        
        if direction in ['support', 'both']:
            supports = [l for l in all_levels['support'] if l['price'] < current_price]
            supports.sort(key=lambda x: abs(x['price'] - current_price))
            result['support'] = supports[:count]
        
        if direction in ['resistance', 'both']:
            resistances = [l for l in all_levels['resistance'] if l['price'] > current_price]
            resistances.sort(key=lambda x: abs(x['price'] - current_price))
            result['resistance'] = resistances[:count]
        
        return result
    
    def is_at_level(self, price: float = None, tolerance_pips: int = 5) -> Dict:
        """Check if price is at a support or resistance level"""
        if price is None:
            price = self.df['close'].iloc[-1]
        
        tolerance = tolerance_pips * settings.PIP_VALUE
        all_levels = self.find_all_levels()
        
        at_support = False
        at_resistance = False
        level_info = None
        
        # Check support
        for level in all_levels['support']:
            if abs(price - level['price']) <= tolerance:
                at_support = True
                level_info = level
                break
        
        # Check resistance
        for level in all_levels['resistance']:
            if abs(price - level['price']) <= tolerance:
                at_resistance = True
                level_info = level
                break
        
        return {
            'at_support': at_support,
            'at_resistance': at_resistance,
            'level_info': level_info,
            'action': self._suggest_action(at_support, at_resistance, level_info)
        }
    
    def _suggest_action(self, at_support: bool, at_resistance: bool, level_info: Dict) -> str:
        """Suggest trading action based on level"""
        if at_support and level_info:
            strength = level_info.get('final_strength', 0)
            if strength >= 0.7:
                return "STRONG_BUY_ZONE"
            else:
                return "BUY_ZONE"
        
        if at_resistance and level_info:
            strength = level_info.get('final_strength', 0)
            if strength >= 0.7:
                return "STRONG_SELL_ZONE"
            else:
                return "SELL_ZONE"
        
        return "NO_LEVEL"
