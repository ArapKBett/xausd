import requests
from bs4 import BeautifulSoup
import feedparser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from textblob import TextBlob
import re
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.cache_manager import cache

class NewsFetcher:
    """Fetch and process gold market news from multiple sources"""
    
    def __init__(self):
        self.newsapi_key = settings.NEWSAPI_KEY
        self.finnhub_key = settings.FINNHUB_API_KEY
        self.base_url_newsapi = "https://newsapi.org/v2/everything"
        self.base_url_finnhub = "https://finnhub.io/api/v1/news"
        
    def fetch_all_news(self) -> List[Dict]:
        """Fetch news from all available sources"""
        all_news = []
        
        # Fetch from NewsAPI
        if self.newsapi_key:
            newsapi_articles = self.fetch_from_newsapi()
            all_news.extend(newsapi_articles)
        
        # Fetch from Finnhub
        if self.finnhub_key:
            finnhub_articles = self.fetch_from_finnhub()
            all_news.extend(finnhub_articles)
        
        # Fetch from RSS feeds
        rss_articles = self.fetch_from_rss()
        all_news.extend(rss_articles)
        
        # Remove duplicates and sort by date
        all_news = self._deduplicate_news(all_news)
        all_news.sort(key=lambda x: x['published'], reverse=True)
        
        logger.info(f"Fetched {len(all_news)} unique news articles for gold")
        return all_news
    
    def fetch_from_newsapi(self) -> List[Dict]:
        """Fetch news from NewsAPI for gold"""
        cache_key = "news:newsapi:gold"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            from_date = (datetime.now() - timedelta(hours=settings.NEWS_LOOKBACK_HOURS)).isoformat()
            
            # Search for gold-related news
            params = {
                'q': '(gold OR XAU OR bullion OR precious metals) AND (USD OR dollar OR Federal Reserve)',
                'from': from_date,
                'sortBy': 'publishedAt',
                'language': 'en',
                'apiKey': self.newsapi_key
            }
            
            response = requests.get(self.base_url_newsapi, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            for article in data.get('articles', []):
                articles.append({
                    'title': article.get('title', ''),
                    'description': article.get('description', ''),
                    'content': article.get('content', ''),
                    'source': article.get('source', {}).get('name', 'NewsAPI'),
                    'url': article.get('url', ''),
                    'published': datetime.fromisoformat(article['publishedAt'].replace('Z', '+00:00')),
                    'sentiment': None  # Will be calculated later
                })
            
            cache.set(cache_key, articles, ttl=1800)  # Cache for 30 minutes
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching gold news from NewsAPI: {e}")
            return []
    
    def fetch_from_finnhub(self) -> List[Dict]:
        """Fetch gold market news from Finnhub"""
        cache_key = "news:finnhub:gold"
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        try:
            params = {
                'category': 'general',
                'token': self.finnhub_key
            }
            
            response = requests.get(self.base_url_finnhub, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            articles = []
            
            cutoff_time = datetime.now() - timedelta(hours=settings.NEWS_LOOKBACK_HOURS)
            
            for article in data:
                # Filter for gold-related news
                headline = article.get('headline', '').lower()
                if not any(keyword in headline for keyword in ['gold', 'xau', 'bullion', 'precious']):
                    continue
                
                pub_date = datetime.fromtimestamp(article.get('datetime', 0))
                
                if pub_date < cutoff_time:
                    continue
                
                articles.append({
                    'title': article.get('headline', ''),
                    'description': article.get('summary', ''),
                    'content': article.get('summary', ''),
                    'source': article.get('source', 'Finnhub'),
                    'url': article.get('url', ''),
                    'published': pub_date,
                    'sentiment': None
                })
            
            cache.set(cache_key, articles, ttl=1800)
            return articles
            
        except Exception as e:
            logger.error(f"Error fetching gold news from Finnhub: {e}")
            return []
    
    def fetch_from_rss(self) -> List[Dict]:
        """Fetch gold news from RSS feeds"""
        rss_feeds = [
            'https://www.kitco.com/rss/feeds/pressreleases.rss',  # Kitco gold news
            'https://www.bullionvault.com/gold-news/rss.xml',     # BullionVault
            'https://www.gold.org/rss',                           # World Gold Council
            'https://seekingalpha.com/feed/sector/precious-metals',  # Precious metals
            'https://www.investing.com/rss/news_303.rss',         # Commodities news
        ]
        
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=settings.NEWS_LOOKBACK_HOURS)
        
        for feed_url in rss_feeds:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries:
                    # Parse published date
                    if hasattr(entry, 'published_parsed'):
                        pub_date = datetime(*entry.published_parsed[:6])
                    else:
                        pub_date = datetime.now()
                    
                    if pub_date < cutoff_time:
                        continue
                    
                    articles.append({
                        'title': entry.get('title', ''),
                        'description': entry.get('summary', ''),
                        'content': entry.get('summary', ''),
                        'source': feed.feed.get('title', 'RSS'),
                        'url': entry.get('link', ''),
                        'published': pub_date,
                        'sentiment': None
                    })
                    
            except Exception as e:
                logger.warning(f"Error fetching gold RSS feed {feed_url}: {e}")
                continue
        
        return articles
    
    def analyze_sentiment(self, articles: List[Dict]) -> List[Dict]:
        """Analyze sentiment of news articles for gold"""
        for article in articles:
            try:
                text = f"{article['title']} {article['description']}"
                
                # Use TextBlob for sentiment
                blob = TextBlob(text)
                polarity = blob.sentiment.polarity
                
                # Adjust sentiment for gold-specific context
                # Words like "inflation", "uncertainty", "crisis" often bullish for gold
                bullish_keywords = ['inflation', 'uncertainty', 'crisis', 'safe haven', 'dovish', 'rate cut', 'weak dollar']
                bearish_keywords = ['strong dollar', 'rate hike', 'hawkish', 'deflation', 'risk-on', 'strengthening']
                
                # Adjust polarity based on gold-specific context
                text_lower = text.lower()
                for keyword in bullish_keywords:
                    if keyword in text_lower:
                        polarity += 0.05
                
                for keyword in bearish_keywords:
                    if keyword in text_lower:
                        polarity -= 0.05
                
                # Classify sentiment
                if polarity > 0.1:
                    sentiment = "BULLISH"
                elif polarity < -0.1:
                    sentiment = "BEARISH"
                else:
                    sentiment = "NEUTRAL"
                
                article['sentiment'] = sentiment
                article['sentiment_score'] = polarity
                
            except Exception as e:
                logger.warning(f"Error analyzing sentiment for gold news: {e}")
                article['sentiment'] = "NEUTRAL"
                article['sentiment_score'] = 0.0
        
        return articles
    
    def filter_relevant_news(self, articles: List[Dict]) -> List[Dict]:
        """Filter news relevant to XAU/USD (Gold)"""
        keywords = [
            'gold', 'xau', 'bullion', 'precious metal', 'commodity',
            'usd', 'dollar', 'federal reserve', 'fed', 'interest rate',
            'inflation', 'cpi', 'ppi', 'non-farm payrolls', 'nfp',
            'geopolitical', 'safe haven', 'central bank',
            'etf', 'spdr', 'gld', 'comex', 'london fix',
            'real yield', 'treasury', 'bond yield',
            'economic crisis', 'recession', 'uncertainty',
            'mining', 'production', 'supply', 'demand'
        ]
        
        relevant_articles = []
        
        for article in articles:
            text = f"{article['title']} {article['description']}".lower()
            
            relevance_score = sum(
                keyword.lower() in text for keyword in keywords
            )
            
            # Higher threshold for gold (3 keywords) since gold news is more specific
            if relevance_score >= 3:
                article['relevance_score'] = relevance_score / len(keywords)
                relevant_articles.append(article)
            elif 'gold' in text or 'xau' in text:
                # Direct mention of gold always relevant
                article['relevance_score'] = 0.5
                relevant_articles.append(article)
        
        return relevant_articles
    
    def _deduplicate_news(self, articles: List[Dict]) -> List[Dict]:
        """Remove duplicate articles"""
        seen_titles = set()
        unique_articles = []
        
        for article in articles:
            title_clean = re.sub(r'[^\w\s]', '', article['title'].lower())
            
            if title_clean not in seen_titles:
                seen_titles.add(title_clean)
                unique_articles.append(article)
        
        return unique_articles
    
    def get_aggregated_sentiment(self, articles: List[Dict]) -> Dict:
        """Get overall market sentiment from gold news"""
        if not articles:
            return {
                'overall': 'NEUTRAL',
                'score': 0.0,
                'bullish_count': 0,
                'bearish_count': 0,
                'neutral_count': 0
            }
        
        bullish = sum(1 for a in articles if a.get('sentiment') == 'BULLISH')
        bearish = sum(1 for a in articles if a.get('sentiment') == 'BEARISH')
        neutral = sum(1 for a in articles if a.get('sentiment') == 'NEUTRAL')
        
        avg_score = sum(a.get('sentiment_score', 0) for a in articles) / len(articles)
        
        # Slightly adjust thresholds for gold sentiment
        # Gold sentiment often more subtle than forex
        if avg_score > 0.05:
            overall = 'BULLISH'
        elif avg_score < -0.05:
            overall = 'BEARISH'
        else:
            overall = 'NEUTRAL'
        
        return {
            'overall': overall,
            'score': avg_score,
            'bullish_count': bullish,
            'bearish_count': bearish,
            'neutral_count': neutral,
            'total_articles': len(articles)
        }
