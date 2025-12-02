import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from datetime import datetime
from src.analysis.technical.babypips_indicators import BabyPipsIndicators
from src.analysis.technical.ict_analysis import ICTAnalysis
from src.analysis.technical.multi_timeframe import MultiTimeframeAnalysis
from src.analysis.technical.support_resistance import SupportResistanceAnalysis
from src.analysis.technical.fibonacci import FibonacciAnalysis
from src.analysis.fundamental.news_analyzer import NewsAnalyzer
from src.signal.confirmation_system import ConfirmationSystem
from src.signal.risk_calculator import RiskCalculator
from src.config.settings import settings
from src.config.constants import SignalType, TrendDirection
from src.utils.logger import logger

class SignalGenerator:
    """
    Advanced signal generation system implementing BabyPips + ICT strategies
    Requires 3+ confirmations before generating signals
    """
    
    def __init__(self, data_dict: Dict[str, pd.DataFrame], news_data: List[Dict] = None):
        """
        Args:
            data_dict: Dictionary mapping timeframe to DataFrame
            news_data: Recent news analysis
        """
        self.data_dict = data_dict
        self.news_data = news_data or []
        self.confirmation_system = ConfirmationSystem()
        self.risk_calculator = RiskCalculator()
        
    def generate_signal(self) -> Optional[Dict]:
        """
        Generate trading signal with full analysis
        
        Returns:
            Signal dictionary or None if no valid signal
        """
        logger.info("Starting signal generation process...")
        
        # Step 1: Multi-timeframe analysis
        mtf_analysis = MultiTimeframeAnalysis(self.data_dict)
        mtf_result = mtf_analysis.analyze_all_timeframes()
        
        # Step 2: Get trade recommendation
        trade_rec = mtf_analysis.get_trade_recommendation()
        
        if trade_rec['direction'] == SignalType.NEUTRAL:
            logger.info("No clear directional bias - skipping signal")
            return None
        
        # Step 3: Detailed analysis on entry timeframe
        entry_tf = mtf_result.get('entry_timeframe', '15m')
        
        if entry_tf not in self.data_dict or self.data_dict[entry_tf] is None:
            logger.warning(f"Entry timeframe {entry_tf} not available")
            return None
        
        df = self.data_dict[entry_tf]
        
        # BabyPips indicators
        babypips = BabyPipsIndicators(df)
        trend = babypips.analyze_trend()
        momentum = babypips.analyze_momentum()
        volatility = babypips.analyze_volatility()
        
        # ICT analysis
        ict = ICTAnalysis(df)
        ict_result = ict.full_ict_analysis()
        
        # Support/Resistance
        sr_analysis = SupportResistanceAnalysis(df)
        sr_levels = sr_analysis.find_all_levels()
        
        # Fibonacci
        fib_analysis = FibonacciAnalysis(df)
        fib_retracement = fib_analysis.calculate_retracement()
        fib_extension = fib_analysis.calculate_extension()
        
        # Step 4: Collect all confirmations
        confirmations = self._collect_confirmations(
            trade_rec, trend, momentum, ict_result, sr_levels, 
            fib_retracement, mtf_result
        )
        
        # Step 5: Validate confirmations (need at least 3)
        validation = self.confirmation_system.validate_confirmations(
            confirmations, 
            trade_rec['direction']
        )
        
        if not validation['is_valid']:
            logger.info(f"Insufficient confirmations: {validation['count']}/3 required")
            return None
        
        # Step 6: Check news sentiment
        news_check = self._check_news_alignment(trade_rec['direction'])
        
        if news_check['conflicting']:
            logger.warning("News sentiment conflicts with technical signal - skipping")
            return None
        
        # Step 7: Calculate entry, stop loss, and take profit
        current_price = df['close'].iloc[-1]
        
        entry_levels = self._calculate_entry_levels(
            current_price, trade_rec['direction'], ict_result, sr_levels
        )
        
        stop_loss = self._calculate_stop_loss(
            entry_levels['entry'], trade_rec['direction'], ict_result, sr_levels
        )
        
        take_profits = self._calculate_take_profits(
            entry_levels['entry'], trade_rec['direction'], fib_extension, sr_levels
        )
        
        # Step 8: Calculate position sizing
        risk_params = self.risk_calculator.calculate_position_size(
            entry_levels['entry'],
            stop_loss,
            settings.RISK_PERCENTAGE  # Fixed: was RISK_PER_TRADE
        )
        
        # Step 9: Assess market conditions
        market_conditions = self._assess_market_conditions(
            volatility, ict_result, sr_levels
        )
        
        # Step 10: Build signal
        signal = {
            'timestamp': datetime.utcnow().isoformat(),
            'pair': settings.TRADING_PAIR,  # Fixed: was SYMBOL
            'direction': trade_rec['direction'].value,
            'entry': entry_levels['entry'],
            'stop_loss': stop_loss,
            'take_profit_1': take_profits[0]['price'],
            'take_profit_2': take_profits[1]['price'] if len(take_profits) > 1 else None,
            'take_profit_3': take_profits[2]['price'] if len(take_profits) > 2 else None,
            
            # Position sizing
            'position_size': risk_params['position_size'],
            'risk_amount': risk_params['risk_amount'],
            'risk_reward_ratio': risk_params['risk_reward_ratio'],
            
            # Market analysis
            'timeframe_alignment': mtf_result['alignment']['status'],
            'primary_trend': mtf_result['primary_trend']['trend'].value,
            'trend_strength': trend['strength'],
            'momentum_score': momentum['bullish_count'] if trade_rec['direction'] == SignalType.BUY else momentum['bearish_count'],
            
            # Confirmations
            'confirmations': confirmations,
            'confirmation_count': validation['count'],
            'confidence_score': validation['confidence'],
            
            # ICT concepts
            'in_kill_zone': ict_result.get('kill_zone', {}).get('in_kill_zone', False),
            'kill_zone_name': ict_result.get('kill_zone', {}).get('zone_name'),
            'order_blocks_nearby': len(ict_result.get('order_blocks', [])),
            'fvg_present': len(ict_result.get('fair_value_gaps', [])) > 0,
            
            # Market conditions
            'volatility': market_conditions['volatility'],
            'liquidity': market_conditions['liquidity'],
            'market_structure': market_conditions['structure'],
            
            # News sentiment
            'news_sentiment': news_check['sentiment'],
            'news_impact': news_check['impact'],
            
            # Additional info
            'entry_reason': entry_levels['reason'],
            'stop_reason': self._get_stop_reason(stop_loss, entry_levels['entry'], ict_result),
            'nearest_support': sr_levels['support'][0]['price'] if sr_levels['support'] else None,
            'nearest_resistance': sr_levels['resistance'][0]['price'] if sr_levels['resistance'] else None,
            
            # Signal quality
            'signal_quality': self._calculate_signal_quality(validation, market_conditions, news_check),
            
            # Courtesy
            'generated_by': 'ArapB Gold Analysis Bot'  # Updated name
        }
        
        logger.info(f"✅ Signal generated: {signal['direction']} @ {signal['entry']}")
        logger.info(f"   Confirmations: {validation['count']}, Confidence: {validation['confidence']:.2%}")
        
        return signal
    
    def _collect_confirmations(self, trade_rec: Dict, trend: Dict, momentum: Dict,
                              ict_result: Dict, sr_levels: Dict, 
                              fib_retracement: Dict, mtf_result: Dict) -> List[str]:
        """Collect all trading confirmations"""
        confirmations = []
        direction = trade_rec['direction']
        
        # 1. Multi-timeframe alignment
        if mtf_result['alignment']['confidence'] >= 0.7:
            confirmations.append("MULTI_TIMEFRAME_ALIGNMENT")
        
        # 2. Trend confirmation
        if direction == SignalType.BUY and trend['trend'] == TrendDirection.BULLISH:
            confirmations.append("TREND_ALIGNED")
        elif direction == SignalType.SELL and trend['trend'] == TrendDirection.BEARISH:
            confirmations.append("TREND_ALIGNED")
        
        # 3. Momentum confirmation
        if (direction == SignalType.BUY and momentum['bullish_count'] >= 2) or \
           (direction == SignalType.SELL and momentum['bearish_count'] >= 2):
            confirmations.append("MOMENTUM_STRONG")
        
        # 4. ICT Order Block
        order_blocks = ict_result.get('order_blocks', [])
        for ob in order_blocks[:2]:  # Check top 2
            if direction == SignalType.BUY and ob.get('type', '').endswith('BULLISH_OB'):
                confirmations.append("ICT_BULLISH_ORDER_BLOCK")
                break
            elif direction == SignalType.SELL and ob.get('type', '').endswith('BEARISH_OB'):
                confirmations.append("ICT_BEARISH_ORDER_BLOCK")
                break
        
        # 5. Fair Value Gap
        fvgs = ict_result.get('fair_value_gaps', [])
        for fvg in fvgs[:2]:
            if direction == SignalType.BUY and 'BULLISH' in fvg.get('type', ''):
                confirmations.append("ICT_BULLISH_FVG")
                break
            elif direction == SignalType.SELL and 'BEARISH' in fvg.get('type', ''):
                confirmations.append("ICT_BEARISH_FVG")
                break
        
        # 6. Kill Zone timing
        kill_zone = ict_result.get('kill_zone', {})
        if kill_zone.get('in_kill_zone'):
            confirmations.append(f"ICT_KILL_ZONE_{kill_zone.get('zone_name', '').upper()}")
        
        # 7. Support/Resistance levels
        current_price = self.data_dict[mtf_result.get('entry_timeframe', '15m')]['close'].iloc[-1]
        
        if direction == SignalType.BUY:
            for support in sr_levels.get('support', [])[:3]:
                if abs(current_price - support['price']) / settings.PIP_VALUE <= 20:
                    if support.get('final_strength', 0) >= 0.6:
                        confirmations.append("STRONG_SUPPORT_LEVEL")
                        break
        else:
            for resistance in sr_levels.get('resistance', [])[:3]:
                if abs(current_price - resistance['price']) / settings.PIP_VALUE <= 20:
                    if resistance.get('final_strength', 0) >= 0.6:
                        confirmations.append("STRONG_RESISTANCE_LEVEL")
                        break
        
        # 8. Fibonacci levels
        fib_check = FibonacciAnalysis(self.data_dict[mtf_result.get('entry_timeframe', '15m')])
        golden_ratio = fib_check.is_at_golden_ratio(current_price)
        
        if golden_ratio['is_at_golden_ratio']:
            confirmations.append("FIBONACCI_GOLDEN_RATIO")
        
        # 9. Market Structure Break
        if ict_result.get('market_structure', {}).get('bos_levels'):
            confirmations.append("MARKET_STRUCTURE_BREAK")
        
        # 10. Liquidity sweep
        liquidity = ict_result.get('liquidity', {})
        if any(liq.get('swept', False) for liq in liquidity.get('buy_side', [])[:2] + liquidity.get('sell_side', [])[:2]):
            confirmations.append("LIQUIDITY_SWEEP")
        
        return confirmations
    
    def _check_news_alignment(self, direction: SignalType) -> Dict:
        """Check if news sentiment aligns with trade direction"""
        if not self.news_data:
            return {'conflicting': False, 'sentiment': 'NEUTRAL', 'impact': 'LOW'}
        
        # Analyze recent news
        bullish_count = 0
        bearish_count = 0
        high_impact_count = 0
        
        for news in self.news_data[:10]:  # Last 10 news items
            sentiment = news.get('sentiment', 'neutral')
            
            if sentiment == 'BULLISH':
                bullish_count += 1
            elif sentiment == 'BEARISH':
                bearish_count += 1
            
            # Check for high impact news based on keywords
            title = news.get('title', '').lower()
            if any(keyword in title for keyword in ['rate', 'fed', 'cpi', 'nfp', 'inflation', 'crisis']):
                high_impact_count += 1
        
        # Determine overall sentiment
        if bullish_count > bearish_count * 1.5:
            overall_sentiment = 'BULLISH'
        elif bearish_count > bullish_count * 1.5:
            overall_sentiment = 'BEARISH'
        else:
            overall_sentiment = 'NEUTRAL'
        
        # Check for conflict
        conflicting = False
        if direction == SignalType.BUY and overall_sentiment == 'BEARISH' and high_impact_count >= 2:
            conflicting = True
        elif direction == SignalType.SELL and overall_sentiment == 'BULLISH' and high_impact_count >= 2:
            conflicting = True
        
        return {
            'conflicting': conflicting,
            'sentiment': overall_sentiment,
            'impact': 'HIGH' if high_impact_count >= 2 else 'MEDIUM' if high_impact_count == 1 else 'LOW'
        }
    
    def _calculate_entry_levels(self, current_price: float, direction: SignalType,
                               ict_result: Dict, sr_levels: Dict) -> Dict:
        """Calculate optimal entry price"""
        entry_price = current_price
        reason = "Current market price"
        
        # Try to find better entry at order blocks or FVGs
        if direction == SignalType.BUY:
            # Look for bullish order blocks below current price
            for ob in ict_result.get('order_blocks', []):
                if 'BULLISH' in ob.get('type', '') and ob.get('low', float('inf')) < current_price:
                    distance_pips = (current_price - ob['low']) / settings.PIP_VALUE
                    if 10 <= distance_pips <= 50:  # Reasonable distance
                        entry_price = (ob['high'] + ob['low']) / 2
                        reason = "ICT Bullish Order Block"
                        break
            
            # Or FVG
            for fvg in ict_result.get('fair_value_gaps', []):
                if 'BULLISH' in fvg.get('type', '') and fvg.get('gap_low', float('inf')) < current_price:
                    distance_pips = (current_price - fvg['gap_low']) / settings.PIP_VALUE
                    if 10 <= distance_pips <= 50:
                        entry_price = fvg['gap_low'] + (fvg['gap_high'] - fvg['gap_low']) * 0.5
                        reason = "ICT Bullish Fair Value Gap"
                        break
        
        else:  # SELL
            # Look for bearish order blocks above current price
            for ob in ict_result.get('order_blocks', []):
                if 'BEARISH' in ob.get('type', '') and ob.get('high', 0) > current_price:
                    distance_pips = (ob['high'] - current_price) / settings.PIP_VALUE
                    if 10 <= distance_pips <= 50:
                        entry_price = (ob['high'] + ob['low']) / 2
                        reason = "ICT Bearish Order Block"
                        break
            
            # Or FVG
            for fvg in ict_result.get('fair_value_gaps', []):
                if 'BEARISH' in fvg.get('type', '') and fvg.get('gap_high', 0) > current_price:
                    distance_pips = (fvg['gap_high'] - current_price) / settings.PIP_VALUE
                    if 10 <= distance_pips <= 50:
                        entry_price = fvg['gap_low'] + (fvg['gap_high'] - fvg['gap_low']) * 0.5
                        reason = "ICT Bearish Fair Value Gap"
                        break
        
        return {
            'entry': round(entry_price, 5),
            'reason': reason
        }
    
    def _calculate_stop_loss(self, entry: float, direction: SignalType,
                            ict_result: Dict, sr_levels: Dict) -> float:
        """Calculate stop loss using ICT and structure"""
        
        if direction == SignalType.BUY:
            # Place stop below recent swing low or order block
            stop_candidates = []
            
            # Recent swing low
            for ob in ict_result.get('order_blocks', []):
                if 'BULLISH' in ob.get('type', ''):
                    stop_candidates.append(ob['low'] - (10 * settings.PIP_VALUE))
            
            # Support level
            for support in sr_levels.get('support', [])[:2]:
                if support['price'] < entry:
                    stop_candidates.append(support['price'] - (10 * settings.PIP_VALUE))
            
            # Use nearest valid stop
            valid_stops = [s for s in stop_candidates if (entry - s) / settings.PIP_VALUE >= 15]
            
            if valid_stops:
                stop_loss = max(valid_stops)  # Tightest stop
            else:
                stop_loss = entry - (30 * settings.PIP_VALUE)  # Default 30 pips
        
        else:  # SELL
            stop_candidates = []
            
            # Recent swing high
            for ob in ict_result.get('order_blocks', []):
                if 'BEARISH' in ob.get('type', ''):
                    stop_candidates.append(ob['high'] + (10 * settings.PIP_VALUE))
            
            # Resistance level
            for resistance in sr_levels.get('resistance', [])[:2]:
                if resistance['price'] > entry:
                    stop_candidates.append(resistance['price'] + (10 * settings.PIP_VALUE))
            
            valid_stops = [s for s in stop_candidates if (s - entry) / settings.PIP_VALUE >= 15]
            
            if valid_stops:
                stop_loss = min(valid_stops)
            else:
                stop_loss = entry + (30 * settings.PIP_VALUE)
        
        return round(stop_loss, 5)
    
    def _calculate_take_profits(self, entry: float, direction: SignalType,
                               fib_extension: Dict, sr_levels: Dict) -> List[Dict]:
        """Calculate multiple take profit levels"""
        take_profits = []
        
        if direction == SignalType.BUY:
            # TP1: 1.272 Fib extension
            if '1.272' in fib_extension['levels']:
                tp1 = fib_extension['levels']['1.272']['price']
                if tp1 > entry:
                    take_profits.append({
                        'price': round(tp1, 5),
                        'type': 'Fib 1.272',
                        'percentage': 50
                    })
            
            # TP2: 1.618 Fib extension (golden ratio)
            if '1.618' in fib_extension['levels']:
                tp2 = fib_extension['levels']['1.618']['price']
                if tp2 > entry:
                    take_profits.append({
                        'price': round(tp2, 5),
                        'type': 'Fib 1.618 (Golden)',
                        'percentage': 30
                    })
            
            # TP3: Next major resistance
            for resistance in sr_levels.get('resistance', [])[:3]:
                if resistance['price'] > entry:
                    take_profits.append({
                        'price': round(resistance['price'], 5),
                        'type': 'Major Resistance',
                        'percentage': 20
                    })
                    break
        
        else:  # SELL
            # TP1: 1.272 Fib extension
            if '1.272' in fib_extension['levels']:
                tp1 = fib_extension['levels']['1.272']['price']
                if tp1 < entry:
                    take_profits.append({
                        'price': round(tp1, 5),
                        'type': 'Fib 1.272',
                        'percentage': 50
                    })
            
            # TP2: 1.618 Fib extension
            if '1.618' in fib_extension['levels']:
                tp2 = fib_extension['levels']['1.618']['price']
                if tp2 < entry:
                    take_profits.append({
                        'price': round(tp2, 5),
                        'type': 'Fib 1.618 (Golden)',
                        'percentage': 30
                    })
            
            # TP3: Next major support
            for support in sr_levels.get('support', [])[:3]:
                if support['price'] < entry:
                    take_profits.append({
                        'price': round(support['price'], 5),
                        'type': 'Major Support',
                        'percentage': 20
                    })
                    break
        
        # Ensure at least 3 TPs
        while len(take_profits) < 3:
            if direction == SignalType.BUY:
                last_tp = take_profits[-1]['price'] if take_profits else entry
                new_tp = last_tp + (50 * settings.PIP_VALUE)
                take_profits.append({
                    'price': round(new_tp, 5),
                    'type': 'Extension',
                    'percentage': 10
                })
            else:
                last_tp = take_profits[-1]['price'] if take_profits else entry
                new_tp = last_tp - (50 * settings.PIP_VALUE)
                take_profits.append({
                    'price': round(new_tp, 5),
                    'type': 'Extension',
                    'percentage': 10
                })
        
        return take_profits[:3]
    
    def _assess_market_conditions(self, volatility: Dict, ict_result: Dict,
                                 sr_levels: Dict) -> Dict:
        """Assess current market conditions"""
        return {
            'volatility': volatility['level'],
            'liquidity': self._assess_liquidity(ict_result),
            'structure': self._assess_structure(ict_result, sr_levels)
        }
    
    def _assess_liquidity(self, ict_result: Dict) -> str:
        """Assess market liquidity"""
        liquidity_data = ict_result.get('liquidity', {})
        
        pool_count = len(liquidity_data.get('buy_side', [])) + len(liquidity_data.get('sell_side', []))
        
        if pool_count >= 3:
            return "HIGH"
        elif pool_count >= 1:
            return "MEDIUM"
        
        return "LOW"
    
    def _assess_structure(self, ict_result: Dict, sr_levels: Dict) -> str:
        """Assess market structure quality"""
        score = 0
        
        # Strong order blocks
        if len(ict_result.get('order_blocks', [])) >= 2:
            score += 1
        
        # Clear support/resistance
        if len(sr_levels.get('support', [])) >= 2 and len(sr_levels.get('resistance', [])) >= 2:
            score += 1
        
        # Market structure break
        if ict_result.get('market_structure', {}).get('bos_levels'):
            score += 1
        
        if score >= 2:
            return "STRONG"
        elif score == 1:
            return "MODERATE"
        else:
            return "WEAK"
    
    def _get_stop_reason(self, stop_loss: float, entry: float, ict_result: Dict) -> str:
        """Get reason for stop loss placement"""
        distance_pips = abs(stop_loss - entry) / settings.PIP_VALUE
        
        for ob in ict_result.get('order_blocks', []):
            if abs(stop_loss - ob.get('low', float('inf'))) / settings.PIP_VALUE <= 5:
                return "Below bullish order block"
            if abs(stop_loss - ob.get('high', 0)) / settings.PIP_VALUE <= 5:
                return "Above bearish order block"
        
        return f"Structure-based ({distance_pips:.1f} pips)"
    
    def _calculate_signal_quality(self, validation: Dict, market_conditions: Dict,
                                  news_check: Dict) -> str:
        """Calculate overall signal quality"""
        score = 0
        
        # Confirmation count
        if validation['count'] >= 5:
            score += 3
        elif validation['count'] >= 4:
            score += 2
        elif validation['count'] >= 3:
            score += 1
        
        # Confidence
        if validation['confidence'] >= 0.8:
            score += 2
        elif validation['confidence'] >= 0.6:
            score += 1
        
        # Market structure
        if market_conditions['structure'] == "STRONG":
            score += 2
        elif market_conditions['structure'] == "MODERATE":
            score += 1
        
        # News alignment
        if not news_check['conflicting']:
            score += 1
        
        # Liquidity
        if market_conditions['liquidity'] == "HIGH":
            score += 1
        
        if score >= 7:
            return "EXCELLENT"
        elif score >= 5:
            return "GOOD"
        elif score >= 3:
            return "FAIR"
        else:
            return "POOR"
