from typing import Dict, Any
from datetime import datetime

class EmbedFormatter:
    """Helper to build Discord-ready embed payloads (d.py or discord.py compatible)."""

    @staticmethod
    def build_signal_embed(signal: Dict[str, Any]) -> Dict[str, Any]:
        title = f"Signal: {signal.get('side', '').upper()} {signal.get('symbol','XAUUSD')}"
        description = signal.get('reason','Generated signal')
        embed = {
            'title': title,
            'description': description,
            'fields': [
                {'name': 'Entry', 'value': str(signal.get('entry', ''))},
                {'name': 'Stop', 'value': str(signal.get('stop', ''))},
                {'name': 'Size', 'value': str(signal.get('size', ''))},
                {'name': 'Confidence', 'value': str(signal.get('confidence', ''))}
            ],
            'timestamp': datetime.utcnow().isoformat()
        }
        return embed
