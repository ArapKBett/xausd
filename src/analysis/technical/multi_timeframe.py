import pandas as pd
from typing import Dict, List
from src.analysis.technical.babypips_indicators import BabyPipsIndicators
from src.analysis.technical.ict_analysis import ICTAnalysis
from src.config.settings import settings
from src.config.constants import TrendDirection, SignalType
from src.utils.logger import logger

class MultiTimeframeAnalysis:
    """
    Multi-timeframe analysis combining BabyPips and ICT concepts
    """
    
    def __init__(self, data_dict: Dict[str, pd.DataFrame]):
        """
        Args:
            data_dict: Dictionary mapping timeframe to DataFrame
        """
        self.data = data_dict
        self.timeframes = list(data_dict.keys())
        
    def analyze_all_timeframes(self) -> Dict:
        """
        Analyze all timeframes and provide comprehensive view
        
        Returns:
            Dictionary with multi-timeframe analysis
        """
        analysis = {
            'timeframes': {},
            'alignment': None,
            'primary_trend': None,
            'entry_timeframe': None,
            'confluence_zones': []
        }
        
        # Analyze each timeframe
        for tf in self.timeframes:
            if tf not in self.data or self.data[tf] is None:
                continue
            
            df = self.data[tf]
            
            # BabyPips analysis
            babypips = BabyPipsIndicators(df)
            trend_analysis = babypips.analyze_trend()
            momentum_analysis = babypips.analyze_momentum()
            volatility_analysis = babypips.analyze_volatility()
            
            # ICT analysis
            ict = ICTAnalysis(df)
            ict_analysis = ict.full_ict_analysis()
            
            analysis['timeframes'][tf] = {
                'trend': trend_analysis,
                'momentum': momentum_analysis,
                'volatility': volatility_analysis,
                'ict': ict_analysis,
                'current_price': df['close'].iloc[-1]
            }
        
        # Determine alignment
        analysis['alignment'] = self._check_timeframe_alignment(analysis['timeframes'])
        
        # Determine primary trend from higher timeframe
        analysis['primary_trend'] = self._get_primary_trend(analysis['timeframes'])
        
        # Find confluence zones
        analysis['confluence_zones'] = self._find_confluence_zones(analysis['timeframes'])
        
        # Determine best entry timeframe
        analysis['entry_timeframe'] = self._get_entry_timeframe(analysis['timeframes'])
        
        return analysis
    
    def _check_timeframe_alignment(self, timeframes_data: Dict) -> Dict:
        """
        Check if timeframes are aligned (all trending same direction)
        """
        trends = []
        
        for tf, data in timeframes_data.items():
            trend = data['trend']['trend']
            trends.append(trend)
        
        # Count trend directions
        bullish_count = sum(1 for t in trends if t == TrendDirection.BULLISH)
        bearish_count = sum(1 for t in trends if t == TrendDirection.BEARISH)
        ranging_count = sum(1 for t in trends if t == TrendDirection.RANGING)
        
        total = len(trends)
        
        if bullish_count >= total * 0.7:
            alignment = "BULLISH_ALIGNED"
            confidence = bullish_count / total
        elif bearish_count >= total * 0.7:
            alignment = "BEARISH_ALIGNED"
            confidence = bearish_count / total
        else:
            alignment = "NOT_ALIGNED"
            confidence = 0.5
        
        return {
            'status': alignment,
            'confidence': confidence,
            'bullish_count': bullish_count,
            'bearish_count': bearish_count,
            'ranging_count': ranging_count
        }
    
    def _get_primary_trend(self, timeframes_data: Dict) -> Dict:
        """Get primary trend from highest timeframe"""
        # Use H4 as primary if available, otherwise highest available
        priority_order = ["1d", "4h", "1h", "15m"]
        
        for tf in priority_order:
            if tf in timeframes_data:
                return {
                    'timeframe': tf,
                    'trend': timeframes_data[tf]['trend']['trend'],
                    'strength': timeframes_data[tf]['trend']['strength']
                }
        
        # Fallback to any available timeframe
        if timeframes_data:
            first_tf = list(timeframes_data.keys())[0]
            return {
                'timeframe': first_tf,
                'trend': timeframes_data[first_tf]['trend']['trend'],
                'strength': timeframes_data[first_tf]['trend']['strength']
            }
        
        return None
    
    def _find_confluence_zones(self, timeframes_data: Dict) -> List[Dict]:
        """
        Find zones where multiple timeframes show confluence
        (order blocks, FVGs, support/resistance)
        """
        confluence_zones = []
        
        # Collect all important levels from all timeframes
        all_levels = {
            'support': [],
            'resistance': [],
            'order_blocks': [],
            'fvgs': []
        }
        
        for tf, data in timeframes_data.items():
            ict_data = data.get('ict', {})
            
            # Order blocks
            for ob in ict_data.get('order_blocks', []):
                all_levels['order_blocks'].append({
                    'timeframe': tf,
                    'price': (ob['high'] + ob['low']) / 2,
                    'type': ob['type'],
                    'strength': ob.get('strength', 1)
                })
            
            # FVGs
            for fvg in ict_data.get('fair_value_gaps', []):
                all_levels['fvgs'].append({
                    'timeframe': tf,
                    'price': (fvg['gap_high'] + fvg['gap_low']) / 2,
                    'type': fvg['type']
                })
        
        # Find overlapping zones
        tolerance = 20 * settings.PIP_VALUE  # 20 pips tolerance
        
        all_prices = (
            [level['price'] for level in all_levels['order_blocks']] +
            [level['price'] for level in all_levels['fvgs']]
        )
        
        for i, price1 in enumerate(all_prices):
            confluence_count = 1
            types = []
            
            for j, price2 in enumerate(all_prices):
                if i != j and abs(price1 - price2) <= tolerance:
                    confluence_count += 1
            
            if confluence_count >= 2:  # At least 2 levels overlap
                confluence_zones.append({
                    'price': price1,
                    'confluence_count': confluence_count,
                    'strength': confluence_count / len(all_prices)
                })
        
        # Remove duplicates and sort by strength
        confluence_zones = list({z['price']: z for z in confluence_zones}.values())
        confluence_zones.sort(key=lambda x: x['strength'], reverse=True)
        
        return confluence_zones[:5]  # Return top 5
    
    def _get_entry_timeframe(self, timeframes_data: Dict) -> str:
        """Determine best timeframe for entry precision"""
        # Prefer lower timeframes for entry
        entry_priority = ["5m", "15m", "1h"]
        
        for tf in entry_priority:
            if tf in timeframes_data:
                return tf
        
        # Return lowest available
        if timeframes_data:
            return list(timeframes_data.keys())[0]
        
        return None
    
    def get_trade_recommendation(self) -> Dict:
        """
        Get trade recommendation based on multi-timeframe analysis
        
        Returns:
            Trade recommendation with direction and confidence
        """
        analysis = self.analyze_all_timeframes()
        
        recommendation = {
            'direction': SignalType.NEUTRAL,
            'confidence': 0.0,
            'reasons': [],
            'timeframe_alignment': analysis['alignment']['status'],
            'primary_trend': analysis['primary_trend']['trend'] if analysis['primary_trend'] else None
        }
        
        # Check alignment
        alignment = analysis['alignment']
        
        if alignment['status'] == "BULLISH_ALIGNED":
            recommendation['direction'] = SignalType.BUY
            recommendation['confidence'] += 0.3
            recommendation['reasons'].append("Bullish multi-timeframe alignment")
        
        elif alignment['status'] == "BEARISH_ALIGNED":
            recommendation['direction'] = SignalType.SELL
            recommendation['confidence'] += 0.3
            recommendation['reasons'].append("Bearish multi-timeframe alignment")
        
        # Check primary trend
        if analysis['primary_trend']:
            primary_trend = analysis['primary_trend']['trend']
            
            if primary_trend == TrendDirection.BULLISH:
                if recommendation['direction'] == SignalType.BUY:
                    recommendation['confidence'] += 0.2
                recommendation['reasons'].append("Primary trend is bullish")
            
            elif primary_trend == TrendDirection.BEARISH:
                if recommendation['direction'] == SignalType.SELL:
                    recommendation['confidence'] += 0.2
                recommendation['reasons'].append("Primary trend is bearish")
        
        # Check ICT concepts
        entry_tf = analysis.get('entry_timeframe')
        if entry_tf and entry_tf in analysis['timeframes']:
            ict_data = analysis['timeframes'][entry_tf]['ict']
            
            # Check kill zone
            if ict_data.get('kill_zone', {}).get('in_kill_zone'):
                recommendation['confidence'] += 0.15
                zone_name = ict_data['kill_zone']['zone_name']
                recommendation['reasons'].append(f"In {zone_name} kill zone")
            
            # Check optimal trade entry
            optimal_entry = ict_data.get('optimal_trade_entry')
            if optimal_entry and optimal_entry.get('entries'):
                entry = optimal_entry['entries'][0]
                if entry['direction'] == recommendation['direction']:
                    recommendation['confidence'] += 0.2
                    recommendation['reasons'].append(f"ICT {entry['type']} setup detected")
        
        # Cap confidence at 1.0
        recommendation['confidence'] = min(recommendation['confidence'], 1.0)
        
        return recommendation
