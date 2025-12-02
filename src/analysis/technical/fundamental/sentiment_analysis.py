import re
from typing import List
from src.utils.logger import logger

class SentimentAnalysis:
    """Lightweight, production-friendly sentiment scoring without heavy external deps.

    It uses a combination of small lexicons and punctuation heuristics.
    Scores are in range [-1.0, 1.0].
    """

    def __init__(self):
        # Minimal lexicons tuned for financial news (kept small for performance)
        self.positive = set([
            'rise','rises','rose','up','gain','gains','gained','beats','strong','surge','surges','buy'
        ])
        self.negative = set([
            'fall','falls','fell','down','drop','drops','dropped','miss','weak','weaken','sell','plunge'
        ])
        self.intensifiers = set(['sharp','large','significant','massive','steep','quick'])
        self.negators = set(['not','no','never','less','without'])

    def _tokenize(self, text: str):
        text = text.lower()
        tokens = re.findall(r"\b[a-z']+\b", text)
        return tokens

    def score_text(self, text: str) -> float:
        try:
            tokens = self._tokenize(text)
            pos = sum(1 for t in tokens if t in self.positive)
            neg = sum(1 for t in tokens if t in self.negative)
            intens = sum(1 for t in tokens if t in self.intensifiers)
            negator = sum(1 for t in tokens if t in self.negators)
            if pos + neg == 0:
                return 0.0
            raw = (pos - neg) + 0.5 * intens
            # negators reduce polarity
            raw = raw * (1 - 0.25 * negator)
            # normalize between -1 and 1
            denom = max(abs(pos) + abs(neg) + 0.5*intens, 1)
            score = max(min(raw / denom, 1.0), -1.0)
            return score
        except Exception as e:
            logger.error(f"Sentiment scoring failed: {e}")
            return 0.0
