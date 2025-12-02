import logging
from typing import List, Dict, Optional
from src.data.news_fetcher import NewsFetcher
from src.analysis.fundamental.sentiment_analysis import SentimentAnalysis
from src.utils.logger import logger

class NewsAnalyzer:
    """Fetches news for XAUUSD and produces scored events suitable for trading signals."""

    def __init__(self, sources: Optional[List[str]] = None):
        self.fetcher = NewsFetcher()
        self.sentiment = SentimentAnalysis()
        self.sources = sources

    def analyze_recent(self, lookback_minutes: int = 60) -> List[Dict]:
        """Fetch recent news and return scored items.

        Returns:
            list of dicts with keys: title, summary, time, sentiment_score, importance
        """
        try:
            articles = self.fetcher.fetch_recent(symbol='XAUUSD', minutes=lookback_minutes, sources=self.sources)
            results = []
            for a in articles:
                txt = (a.get('title') or '') + ' ' + (a.get('summary') or '')
                sscore = self.sentiment.score_text(txt)
                importance = a.get('importance') or self._estimate_importance(a)
                results.append({
                    'title': a.get('title'),
                    'summary': a.get('summary'),
                    'time': a.get('time'),
                    'sentiment_score': sscore,
                    'importance': importance,
                    'meta': a
                })
            # sort by importance then absolute sentiment magnitude
            results.sort(key=lambda x: (x['importance'], abs(x['sentiment_score'])), reverse=True)
            return results
        except Exception as e:
            logger.error(f"NewsAnalyzer analyze_recent error: {e}")
            return []

    def _estimate_importance(self, article: Dict) -> float:
        # Basic heuristic: presence of keywords + source credibility
        title = (article.get('title') or '').lower()
        summary = (article.get('summary') or '').lower()
        score = 0.0
        keywords = ['inflation','rate','fed','cpi','employment','jobs','gdp','crude','oil','usd','dollar','gold','xau']
        for kw in keywords:
            if kw in title or kw in summary:
                score += 1.0
        source = (article.get('source') or '').lower()
        if 'reuters' in source or 'bloomberg' in source or 'wsj' in source:
            score += 1.5
        return score
