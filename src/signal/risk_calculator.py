import math
from typing import Dict
from src.config.settings import settings
from src.utils.logger import logger

class RiskCalculator:
    """
    Professional risk management and position sizing calculator
    Updated for gold (XAU/USD) trading
    """
    
    def __init__(self):
        # Set default account balance if not in settings
        self.account_balance = getattr(settings, 'ACCOUNT_BALANCE', 10000.0)
        self.risk_per_trade = settings.RISK_PERCENTAGE
        
    def calculate_position_size(self, entry: float, stop_loss: float,
                               risk_percentage: float = None) -> Dict:
        """
        Calculate optimal position size for gold (XAU/USD)
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            risk_percentage: Risk per trade (default from settings)
            
        Returns:
            Dictionary with position sizing details
        """
        if risk_percentage is None:
            risk_percentage = self.risk_per_trade
        
        # Calculate risk amount in account currency
        risk_amount = self.account_balance * (risk_percentage / 100)
        
        # Calculate stop loss distance in pips (for gold: 1 pip = $0.01)
        stop_distance = abs(entry - stop_loss)
        stop_distance_pips = stop_distance / settings.PIP_VALUE
        
        # For XAU/USD (Gold):
        # - 1 standard lot = 100 ounces
        # - Pip value per standard lot = 100 * $0.01 = $1.00 per pip
        # - Mini lot = 10 ounces, Pip value = $0.10 per pip
        # - Micro lot = 1 ounce, Pip value = $0.01 per pip
        
        pip_value_per_standard_lot = 1.0  # $1.00 per pip for standard lot (100 oz)
        
        # Calculate lots (standard lots = 100 oz each)
        # Position Size = (Risk Amount) / (Stop Loss in Pips × Pip Value per Standard Lot)
        lots = risk_amount / (stop_distance_pips * pip_value_per_standard_lot)
        
        # Round to 2 decimal places (0.01 lot increments = 1 ounce)
        lots = round(lots, 2)
        
        # Minimum position size (0.01 lots = 1 ounce)
        if lots < 0.01:
            lots = 0.01
            logger.warning(f"Position size too small, using minimum: 0.01 lots (1 ounce)")
        
        # Maximum position size for safety
        # Gold is volatile, so be more conservative
        max_lots = self.account_balance / 5000  # Max 1 lot per $5000 account balance
        if lots > max_lots:
            lots = max_lots
            logger.warning(f"Position size capped at {max_lots:.2f} lots (safety)")
        
        # Calculate actual risk with this position size
        actual_risk = lots * stop_distance_pips * pip_value_per_standard_lot
        actual_risk_percentage = (actual_risk / self.account_balance) * 100
        
        # Calculate equivalent in ounces and mini/micro lots
        ounces = lots * 100
        mini_lots = ounces / 10  # 1 mini lot = 10 ounces
        micro_lots = ounces  # 1 micro lot = 1 ounce
        
        result = {
            'position_size': lots,  # Standard lots
            'position_size_ounces': round(ounces, 2),
            'position_size_mini': round(mini_lots, 2),
            'position_size_micro': round(micro_lots, 2),
            'risk_amount': round(actual_risk, 2),
            'risk_percentage': round(actual_risk_percentage, 2),
            'stop_distance_pips': round(stop_distance_pips, 1),
            'stop_distance_dollars': round(stop_distance_pips * pip_value_per_standard_lot * lots, 2),
            'pip_value': round(lots * pip_value_per_standard_lot, 2),
            'pip_value_mini': round(mini_lots * 0.10, 2),  # $0.10 per pip for mini lot
            'account_balance': self.account_balance,
            'risk_reward_ratio': None  # Will be calculated with TP
        }
        
        logger.info(f"Gold position size: {lots:.2f} lots ({ounces:.1f} oz), "
                   f"Risk: ${actual_risk:.2f} ({actual_risk_percentage:.2f}%)")
        
        return result
    
    def calculate_risk_reward(self, entry: float, stop_loss: float,
                             take_profit: float) -> Dict:
        """
        Calculate risk-reward ratio for gold
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Dictionary with R:R details
        """
        risk_distance = abs(entry - stop_loss)
        reward_distance = abs(take_profit - entry)
        
        risk_pips = risk_distance / settings.PIP_VALUE
        reward_pips = reward_distance / settings.PIP_VALUE
        
        # Convert to dollars (approximate)
        risk_dollars = risk_pips * 1.0  # $1 per pip for 1 standard lot
        reward_dollars = reward_pips * 1.0
        
        # Calculate ratio
        if risk_pips > 0:
            ratio = reward_pips / risk_pips
        else:
            ratio = 0
        
        # Assess quality (adjust thresholds for gold - higher volatility)
        if ratio >= 2.5:
            quality = "EXCELLENT"
        elif ratio >= 2.0:
            quality = "GOOD"
        elif ratio >= 1.5:
            quality = "ACCEPTABLE"
        else:
            quality = "POOR"
        
        return {
            'ratio': round(ratio, 2),
            'risk_pips': round(risk_pips, 1),
            'reward_pips': round(reward_pips, 1),
            'risk_dollars': round(risk_dollars, 2),
            'reward_dollars': round(reward_dollars, 2),
            'quality': quality,
            'is_acceptable': ratio >= 1.5
        }
    
    def calculate_multiple_targets(self, entry: float, stop_loss: float,
                                  targets: list) -> Dict:
        """
        Calculate risk-reward for multiple take profit levels
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            targets: List of TP dictionaries with 'price' and 'percentage'
            
        Returns:
            Dictionary with multi-TP analysis
        """
        risk_distance = abs(entry - stop_loss)
        risk_pips = risk_distance / settings.PIP_VALUE
        risk_dollars = risk_pips * 1.0  # For 1 standard lot
        
        tp_analysis = []
        weighted_rr = 0.0
        
        for i, target in enumerate(targets, 1):
            tp_price = target['price']
            tp_percentage = target.get('percentage', 100 / len(targets))
            
            reward_distance = abs(tp_price - entry)
            reward_pips = reward_distance / settings.PIP_VALUE
            reward_dollars = reward_pips * 1.0  # For 1 standard lot
            
            if risk_pips > 0:
                rr_ratio = reward_pips / risk_pips
            else:
                rr_ratio = 0
            
            # Weighted contribution to overall R:R
            weighted_rr += rr_ratio * (tp_percentage / 100)
            
            tp_analysis.append({
                'target_number': i,
                'price': tp_price,
                'percentage': tp_percentage,
                'reward_pips': round(reward_pips, 1),
                'reward_dollars': round(reward_dollars, 2),
                'rr_ratio': round(rr_ratio, 2)
            })
        
        return {
            'risk_pips': round(risk_pips, 1),
            'risk_dollars': round(risk_dollars, 2),
            'targets': tp_analysis,
            'weighted_rr': round(weighted_rr, 2),
            'total_targets': len(targets)
        }
    
    def calculate_expected_value(self, win_rate: float, avg_win_pips: float,
                                avg_loss_pips: float) -> Dict:
        """
        Calculate expected value of trading system for gold
        
        Args:
            win_rate: Win rate percentage (0-100)
            avg_win_pips: Average win in pips
            avg_loss_pips: Average loss in pips
            
        Returns:
            Expected value analysis
        """
        win_rate_decimal = win_rate / 100
        loss_rate = 1 - win_rate_decimal
        
        # Convert pips to dollars (for 1 standard lot)
        avg_win_dollars = avg_win_pips * 1.0
        avg_loss_dollars = avg_loss_pips * 1.0
        
        expected_value_pips = (win_rate_decimal * avg_win_pips) + (loss_rate * (-avg_loss_pips))
        expected_value_dollars = (win_rate_decimal * avg_win_dollars) + (loss_rate * (-avg_loss_dollars))
        
        # Calculate expectancy per trade
        expectancy = expected_value_pips / avg_loss_pips if avg_loss_pips > 0 else 0
        
        # Assess system quality (adjusted for gold)
        if expectancy >= 0.4:
            quality = "EXCELLENT"
        elif expectancy >= 0.15:
            quality = "GOOD"
        elif expectancy > 0:
            quality = "ACCEPTABLE"
        else:
            quality = "UNPROFITABLE"
        
        return {
            'expected_value_pips': round(expected_value_pips, 2),
            'expected_value_dollars': round(expected_value_dollars, 2),
            'expectancy': round(expectancy, 3),
            'quality': quality,
            'is_profitable': expected_value_pips > 0
        }
    
    def calculate_drawdown_info(self, consecutive_losses: int = None) -> Dict:
        """
        Calculate potential drawdown scenarios
        
        Args:
            consecutive_losses: Number of consecutive losses to simulate
            
        Returns:
            Drawdown analysis
        """
        if consecutive_losses is None:
            consecutive_losses = 3  # Gold is more volatile, be more conservative
            
        risk_per_trade_amount = self.account_balance * (self.risk_per_trade / 100)
        
        # Simple drawdown (doesn't compound)
        simple_drawdown = consecutive_losses * risk_per_trade_amount
        simple_drawdown_pct = (simple_drawdown / self.account_balance) * 100
        
        # Compound drawdown (account decreases with each loss)
        remaining_balance = self.account_balance
        compound_drawdown = 0
        
        for _ in range(consecutive_losses):
            loss = remaining_balance * (self.risk_per_trade / 100)
            compound_drawdown += loss
            remaining_balance -= loss
        
        compound_drawdown_pct = (compound_drawdown / self.account_balance) * 100
        
        # Recovery needed
        if remaining_balance > 0:
            recovery_needed_pct = (compound_drawdown / remaining_balance) * 100
        else:
            recovery_needed_pct = float('inf')
        
        return {
            'consecutive_losses': consecutive_losses,
            'simple_drawdown': round(simple_drawdown, 2),
            'simple_drawdown_pct': round(simple_drawdown_pct, 2),
            'compound_drawdown': round(compound_drawdown, 2),
            'compound_drawdown_pct': round(compound_drawdown_pct, 2),
            'remaining_balance': round(remaining_balance, 2),
            'recovery_needed_pct': round(recovery_needed_pct, 2),
            'risk_level': self._assess_drawdown_risk(compound_drawdown_pct)
        }
    
    def _assess_drawdown_risk(self, drawdown_pct: float) -> str:
        """Assess drawdown risk level (more conservative for gold)"""
        if drawdown_pct >= 30:
            return "CRITICAL"
        elif drawdown_pct >= 20:
            return "HIGH"
        elif drawdown_pct >= 15:
            return "MODERATE"
        elif drawdown_pct >= 10:
            return "LOW"
        else:
            return "MINIMAL"
    
    def calculate_kelly_criterion(self, win_rate: float, win_loss_ratio: float) -> Dict:
        """
        Calculate optimal position size using Kelly Criterion
        
        Args:
            win_rate: Historical win rate (0-100)
            win_loss_ratio: Average win / average loss ratio
            
        Returns:
            Kelly criterion analysis
        """
        win_rate_decimal = win_rate / 100
        
        # Kelly formula: K = W - [(1 - W) / R]
        # Where W = win rate, R = win/loss ratio
        
        if win_loss_ratio > 0:
            kelly_percentage = win_rate_decimal - ((1 - win_rate_decimal) / win_loss_ratio)
        else:
            kelly_percentage = 0
        
        # Convert to percentage
        kelly_percentage *= 100
        
        # Cap at reasonable limits (more conservative for gold)
        kelly_percentage = max(0, min(kelly_percentage, 20))  # Max 20% for gold
        
        # Fractional Kelly (more conservative for volatile markets)
        half_kelly = kelly_percentage / 2
        quarter_kelly = kelly_percentage / 4
        
        recommendation = self._get_kelly_recommendation(kelly_percentage)
        
        return {
            'full_kelly': round(kelly_percentage, 2),
            'half_kelly': round(half_kelly, 2),
            'quarter_kelly': round(quarter_kelly, 2),
            'recommended': round(quarter_kelly, 2),  # Quarter Kelly for gold (more conservative)
            'recommendation': recommendation
        }
    
    def _get_kelly_recommendation(self, kelly_pct: float) -> str:
        """Get Kelly criterion recommendation for gold"""
        if kelly_pct <= 0:
            return "System not profitable - Do not trade gold"
        elif kelly_pct <= 2:
            return "Very conservative sizing - Use full Kelly for gold"
        elif kelly_pct <= 5:
            return "Moderate edge - Use quarter Kelly for gold safety"
        elif kelly_pct <= 10:
            return "Good edge - Use quarter Kelly for gold volatility"
        else:
            return "Strong edge but use quarter Kelly due to gold volatility"
    
    def validate_trade_parameters(self, entry: float, stop_loss: float,
                                 take_profit: float) -> Dict:
        """
        Validate if gold trade parameters meet risk management rules
        
        Args:
            entry: Entry price
            stop_loss: Stop loss price
            take_profit: Take profit price
            
        Returns:
            Validation results
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': []
        }
        
        # Calculate distances in pips
        sl_distance = abs(entry - stop_loss) / settings.PIP_VALUE
        tp_distance = abs(take_profit - entry) / settings.PIP_VALUE
        
        # Convert to dollars (approximate for 1 standard lot)
        sl_dollars = sl_distance * 1.0
        tp_dollars = tp_distance * 1.0
        
        # Rule 1: Minimum stop loss distance for gold (150 pips = $1.50)
        if sl_distance < 150:
            validation['errors'].append(f"Stop loss too tight: {sl_distance:.1f} pips (${sl_dollars:.2f}) - minimum 150 pips ($1.50) for gold")
            validation['is_valid'] = False
        
        # Rule 2: Maximum stop loss distance for gold (500 pips = $5.00)
        if sl_distance > 500:
            validation['warnings'].append(f"Stop loss very wide: {sl_distance:.1f} pips (${sl_dollars:.2f}) - consider reducing for gold")
        
        # Rule 3: Minimum R:R ratio for gold (1:2)
        rr_ratio = tp_distance / sl_distance if sl_distance > 0 else 0
        if rr_ratio < 2.0:
            validation['warnings'].append(f"Risk-reward ratio below 1:2 ({rr_ratio:.2f}) - gold trades need higher R:R")
        
        # Rule 4: Entry between SL and TP
        if entry <= min(stop_loss, take_profit) or entry >= max(stop_loss, take_profit):
            validation['errors'].append("Entry price must be between stop loss and take profit")
            validation['is_valid'] = False
        
        # Rule 5: SL and TP on correct sides
        direction = "BUY" if take_profit > entry else "SELL"
        
        if direction == "BUY" and stop_loss >= entry:
            validation['errors'].append("For BUY: Stop loss must be below entry")
            validation['is_valid'] = False
        
        if direction == "SELL" and stop_loss <= entry:
            validation['errors'].append("For SELL: Stop loss must be above entry")
            validation['is_valid'] = False
        
        # Rule 6: Check if SL/TP are psychologically significant levels (round numbers)
        def is_psychological(price):
            # For gold, psychological levels are typically round dollars or $5 increments
            return round(price * 100) % 100 == 0  # Whole dollar
        
        if not is_psychological(stop_loss) or not is_psychological(take_profit):
            validation['warnings'].append("Consider adjusting SL/TP to whole dollar amounts for gold")
        
        return validation
    
    def calculate_max_position_sizes(self) -> Dict:
        """Calculate maximum allowed position sizes for gold"""
        # Get max risk from settings or use default
        max_risk_percentage = getattr(settings, 'MAX_DAILY_LOSS_PERCENT', 5.0)
        max_risk_amount = self.account_balance * (max_risk_percentage / 100)
        
        # Different scenarios for gold
        # Using $1.00 per pip per standard lot for XAU/USD
        scenarios = {
            '150_pip_stop': max_risk_amount / (150 * 1.0),  # $1.50 risk per lot
            '300_pip_stop': max_risk_amount / (300 * 1.0),  # $3.00 risk per lot
            '500_pip_stop': max_risk_amount / (500 * 1.0),  # $5.00 risk per lot
        }
        
        return {
            'account_balance': self.account_balance,
            'max_risk_percentage': max_risk_percentage,
            'max_risk_amount': round(max_risk_amount, 2),
            'max_lots_by_stop': {k: round(v, 2) for k, v in scenarios.items()},
            'max_ounces_by_stop': {k: round(v * 100, 1) for k, v in scenarios.items()}
        }
