import pandas as pd
from typing import Dict, Any
from src.utils.logger import logger

class TradeValidator:
    """Validates trade signals against risk rules and account status."""

    def __init__(self, account_balance: float = 10000.0, max_risk_pct: float = 1.0):
        self.account_balance = float(account_balance)
        self.max_risk_pct = float(max_risk_pct)  # percent per trade

    def validate(self, signal: Dict[str, Any], market_data: pd.DataFrame) -> Dict[str, Any]:
        """Return validated trade dict with 'allowed' boolean and details.

        Expected signal keys: side ('buy'/'sell'), entry, stop, size(optional)
        """
        try:
            side = signal.get('side')
            entry = float(signal.get('entry'))
            stop = float(signal.get('stop'))
            if side not in ('buy', 'sell'):
                return {'allowed': False, 'reason': 'invalid_side'}
            # compute risk per unit
            risk_per_unit = abs(entry - stop)
            if risk_per_unit <= 0:
                return {'allowed': False, 'reason': 'invalid_risk'}
            max_risk = self.account_balance * (self.max_risk_pct / 100.0)
            # default size in units
            size = signal.get('size')
            if size is None:
                size = max_risk / risk_per_unit
            else:
                size = float(size)
            position_risk = size * risk_per_unit
            allowed = position_risk <= max_risk
            return {
                'allowed': bool(allowed),
                'position_size': float(size),
                'position_risk': float(position_risk),
                'max_risk': float(max_risk),
                'reason': None if allowed else 'risk_too_high'
            }
        except Exception as e:
            logger.error(f"TradeValidator validate error: {e}")
            return {'allowed': False, 'reason': 'exception'}
