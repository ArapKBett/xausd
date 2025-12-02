import requests
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from src.utils.logger import logger

class EconomicCalendar:
    """Fetch economic calendar events (lightweight, configurable source).

    The implementation uses an abstract fetcher; for production you can point
    to an internal calendar service or a provider like econoday or tradingeconomics.
    """

    def __init__(self, provider_url: Optional[str] = None, api_key: Optional[str] = None):
        self.provider_url = provider_url
        self.api_key = api_key

    def fetch_events(self, start: datetime, end: datetime) -> List[Dict]:
        try:
            if not self.provider_url:
                # No provider configured — return empty list
                return []
            params = {
                'from': start.isoformat(),
                'to': end.isoformat(),
                'api_key': self.api_key
            }
            r = requests.get(self.provider_url, params=params, timeout=10)
            r.raise_for_status()
            data = r.json()
            return data.get('events', [])
        except Exception as e:
            logger.error(f"EconomicCalendar fetch_events error: {e}")
            return []
