from typing import List, Dict
from src.config.constants import SignalType
from src.utils.logger import logger

class ConfirmationSystem:
    """
    3-confirmation system for signal validation
    Based on BabyPips and ICT methodology
    """
    
    # Confirmation weights (importance)
    CONFIRMATION_WEIGHTS = {
        'MULTI_TIMEFRAME_ALIGNMENT': 1.5,
        'TREND_ALIGNED': 1.3,
        'MOMENTUM_STRONG': 1.0,
        'ICT_BULLISH_ORDER_BLOCK': 1.4,
        'ICT_BEARISH_ORDER_BLOCK': 1.4,
        'ICT_BULLISH_FVG': 1.2,
        'ICT_BEARISH_FVG': 1.2,
        'ICT_KILL_ZONE_LONDON': 1.3,
        'ICT_KILL_ZONE_NEW_YORK': 1.3,
        'ICT_KILL_ZONE_ASIAN': 0.8,
        'STRONG_SUPPORT_LEVEL': 1.2,
        'STRONG_RESISTANCE_LEVEL': 1.2,
        'FIBONACCI_GOLDEN_RATIO': 1.1,
        'MARKET_STRUCTURE_BREAK': 1.3,
        'LIQUIDITY_SWEEP': 1.2,
        'VOLUME_CONFIRMATION': 1.0,
        'DIVERGENCE_DETECTED': 1.1,
        'CANDLESTICK_PATTERN': 0.9
    }
    
    def __init__(self):
        self.min_confirmations = 3
        self.min_weighted_score = 3.0
        
    def validate_confirmations(self, confirmations: List[str], 
                             direction: SignalType) -> Dict:
        """
        Validate if confirmations are sufficient for signal
        
        Args:
            confirmations: List of confirmation strings
            direction: Signal direction (BUY or SELL)
            
        Returns:
            Dictionary with validation results
        """
        if not confirmations:
            return {
                'is_valid': False,
                'count': 0,
                'confidence': 0.0,
                'reasons': ['No confirmations found']
            }
        
        # Calculate weighted score
        weighted_score = 0.0
        valid_confirmations = []
        
        for conf in confirmations:
            weight = self.CONFIRMATION_WEIGHTS.get(conf, 0.5)
            weighted_score += weight
            valid_confirmations.append({
                'name': conf,
                'weight': weight
            })
        
        # Count unique confirmation types
        unique_count = len(set(confirmations))
        
        # Calculate confidence (0-1 scale)
        confidence = min(weighted_score / 10.0, 1.0)
        
        # Validation checks
        is_valid = (
            unique_count >= self.min_confirmations and
            weighted_score >= self.min_weighted_score
        )
        
        # Additional quality checks
        quality_checks = self._perform_quality_checks(confirmations, direction)
        
        if not quality_checks['passed']:
            is_valid = False
        
        result = {
            'is_valid': is_valid,
            'count': unique_count,
            'weighted_score': weighted_score,
            'confidence': confidence,
            'confirmations': valid_confirmations,
            'quality_checks': quality_checks,
            'reasons': self._generate_reasons(is_valid, unique_count, weighted_score, quality_checks)
        }
        
        logger.info(f"Confirmation validation: {unique_count} confirmations, "
                   f"score: {weighted_score:.2f}, valid: {is_valid}")
        
        return result
    
    def _perform_quality_checks(self, confirmations: List[str], 
                               direction: SignalType) -> Dict:
        """Perform quality checks on confirmations"""
        checks = {
            'has_ict_concept': False,
            'has_trend': False,
            'has_structure': False,
            'directional_alignment': False,
            'passed': False
        }
        
        # Check for ICT concepts
        ict_keywords = ['ICT', 'ORDER_BLOCK', 'FVG', 'KILL_ZONE', 'LIQUIDITY']
        checks['has_ict_concept'] = any(
            any(keyword in conf for keyword in ict_keywords) 
            for conf in confirmations
        )
        
        # Check for trend confirmation
        checks['has_trend'] = any(
            'TREND' in conf or 'TIMEFRAME' in conf 
            for conf in confirmations
        )
        
        # Check for structure (support/resistance, fibonacci)
        structure_keywords = ['SUPPORT', 'RESISTANCE', 'FIBONACCI', 'STRUCTURE']
        checks['has_structure'] = any(
            any(keyword in conf for keyword in structure_keywords)
            for conf in confirmations
        )
        
        # Check directional alignment
        if direction == SignalType.BUY:
            bullish_confirms = [c for c in confirmations if 'BULLISH' in c or 'SUPPORT' in c]
            bearish_confirms = [c for c in confirmations if 'BEARISH' in c or 'RESISTANCE' in c]
            checks['directional_alignment'] = len(bullish_confirms) > len(bearish_confirms)
        else:
            bullish_confirms = [c for c in confirmations if 'BULLISH' in c or 'SUPPORT' in c]
            bearish_confirms = [c for c in confirmations if 'BEARISH' in c or 'RESISTANCE' in c]
            checks['directional_alignment'] = len(bearish_confirms) > len(bullish_confirms)
        
        # Overall pass if at least 2 key checks pass
        passed_count = sum([
            checks['has_ict_concept'],
            checks['has_trend'],
            checks['has_structure'],
            checks['directional_alignment']
        ])
        
        checks['passed'] = passed_count >= 2
        
        return checks
    
    def _generate_reasons(self, is_valid: bool, count: int, score: float,
                         quality_checks: Dict) -> List[str]:
        """Generate human-readable reasons"""
        reasons = []
        
        if is_valid:
            reasons.append(f"✅ {count} strong confirmations detected")
            reasons.append(f"✅ Weighted score: {score:.2f}/10")
            
            if quality_checks['has_ict_concept']:
                reasons.append("✅ ICT concepts confirmed")
            if quality_checks['has_trend']:
                reasons.append("✅ Trend alignment confirmed")
            if quality_checks['has_structure']:
                reasons.append("✅ Market structure confirmed")
        else:
            if count < self.min_confirmations:
                reasons.append(f"❌ Insufficient confirmations: {count}/{self.min_confirmations}")
            if score < self.min_weighted_score:
                reasons.append(f"❌ Low weighted score: {score:.2f}/{self.min_weighted_score}")
            if not quality_checks['passed']:
                reasons.append("❌ Quality checks failed")
            if not quality_checks['directional_alignment']:
                reasons.append("❌ Conflicting directional signals")
        
        return reasons
    
    def rank_confirmations(self, confirmations: List[str]) -> List[Dict]:
        """Rank confirmations by importance"""
        ranked = []
        
        for conf in confirmations:
            weight = self.CONFIRMATION_WEIGHTS.get(conf, 0.5)
            ranked.append({
                'confirmation': conf,
                'weight': weight,
                'importance': self._get_importance_level(weight)
            })
        
        ranked.sort(key=lambda x: x['weight'], reverse=True)
        return ranked
    
    def _get_importance_level(self, weight: float) -> str:
        """Convert weight to importance level"""
        if weight >= 1.3:
            return "CRITICAL"
        elif weight >= 1.0:
            return "HIGH"
        elif weight >= 0.8:
            return "MEDIUM"
        else:
            return "LOW"
    
    def get_missing_confirmations(self, confirmations: List[str], 
                                 direction: SignalType) -> List[str]:
        """Suggest what confirmations are missing"""
        all_possible = list(self.CONFIRMATION_WEIGHTS.keys())
        present = set(confirmations)
        
        missing = []
        for conf in all_possible:
            if conf not in present:
                # Check if it's relevant for this direction
                if direction == SignalType.BUY:
                    if 'BULLISH' in conf or 'SUPPORT' in conf or 'TREND' in conf:
                        missing.append(conf)
                else:
                    if 'BEARISH' in conf or 'RESISTANCE' in conf or 'TREND' in conf:
                        missing.append(conf)
        
        # Return top 5 most important missing
        missing_ranked = [
            {'conf': m, 'weight': self.CONFIRMATION_WEIGHTS[m]} 
            for m in missing
        ]
        missing_ranked.sort(key=lambda x: x['weight'], reverse=True)
        
        return [m['conf'] for m in missing_ranked[:5]]
