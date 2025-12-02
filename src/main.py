import asyncio
import sys
from datetime import datetime, timedelta
from typing import Dict, Optional
import signal

from src.data.price_fetcher import PriceFetcher
from src.data.news_fetcher import NewsFetcher
from src.data.historical_data_manager import HistoricalDataManager
from src.analysis.fundamental.news_analyzer import NewsAnalyzer
from src.signal.signal_generator import SignalGenerator
from src.visualization.chart_plotter import ChartPlotter
from src.visualization.signal_visualizer import SignalVisualizer
from src.discord.bot_client import DiscordBotClient
from src.config.settings import settings
from src.utils.logger import logger
from src.utils.helpers import format_price, format_pips

class GoldAnalysisBot:
    """
    Main orchestrator for ArapB Gold Analysis Bot
    Production-ready gold (XAU/USD) analysis system
    """
    
    def __init__(self):
        self.is_running = False
        self.price_fetcher = PriceFetcher()
        self.news_fetcher = NewsFetcher()
        self.historical_manager = HistoricalDataManager()
        self.news_analyzer = NewsAnalyzer()
        self.discord_client = DiscordBotClient()
        self.chart_plotter = ChartPlotter()
        self.signal_visualizer = SignalVisualizer()
        
        self.last_signal_time = None
        self.analysis_count = 0
        self.signals_generated = 0
        
        # Setup graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        logger.info("Shutdown signal received, stopping bot...")
        self.is_running = False
        
    async def initialize(self):
        """Initialize all components"""
        logger.info("=" * 70)
        logger.info("🚀 Initializing ArapB Gold Analysis Bot")
        logger.info("=" * 70)
        
        try:
            # Initialize Discord bot
            logger.info("Initializing Discord client...")
            await self.discord_client.initialize()
            
            # Send startup message
            await self.discord_client.send_system_message(
                "🤖 **ArapB Gold Analysis Bot Started**",
                f"```\nPair: {settings.TRADING_PAIR}\n"
                f"Base: {settings.CURRENCY_BASE}, Quote: {settings.CURRENCY_QUOTE}\n"
                f"Timeframes: {', '.join(settings.TIMEFRAMES.values())}\n"
                f"Analysis Interval: {settings.ANALYSIS_INTERVAL} seconds\n"
                f"Risk per Trade: {settings.RISK_PERCENTAGE}%\n"
                f"Max Daily Loss: {settings.MAX_DAILY_LOSS_PERCENT}%\n```"
            )
            
            # Test API connections
            logger.info("Testing API connections...")
            await self._test_connections()
            
            logger.info("✅ All components initialized successfully")
            logger.info("=" * 70)
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}", exc_info=True)
            raise
    
    async def _test_connections(self):
        """Test all API connections"""
        try:
            # Test price API
            logger.info("Testing gold price data API...")
            price_data = self.price_fetcher.get_live_price()
            if price_data:
                logger.info(f"✅ Price API working: {settings.TRADING_PAIR} @ ${price_data['mid']:.2f}")
            else:
                logger.warning("Price API returned no data")
            
            # Test news API
            logger.info("Testing gold news API...")
            test_news = self.news_fetcher.fetch_all_news()
            logger.info(f"✅ News API working: {len(test_news)} gold articles fetched")
            
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            raise
    
    async def run(self):
        """Main bot loop"""
        self.is_running = True
        logger.info("🔄 Starting main analysis loop...")
        
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while self.is_running:
            try:
                logger.info("\n" + "=" * 70)
                logger.info(f"📊 Starting Analysis Cycle #{self.analysis_count + 1}")
                logger.info(f"⏰ Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC")
                logger.info("=" * 70)
                
                # Run analysis cycle
                await self.analysis_cycle()
                
                # Reset error counter on success
                consecutive_errors = 0
                self.analysis_count += 1
                
                # Wait for next cycle
                logger.info(f"\n⏳ Waiting {settings.ANALYSIS_INTERVAL} seconds until next analysis...")
                await asyncio.sleep(settings.ANALYSIS_INTERVAL)
                
            except KeyboardInterrupt:
                logger.info("Keyboard interrupt received, shutting down...")
                break
                
            except Exception as e:
                consecutive_errors += 1
                logger.error(f"Error in main loop: {e}", exc_info=True)
                
                # Send error notification
                await self.discord_client.send_error_message(
                    f"⚠️ Analysis cycle error ({consecutive_errors}/{max_consecutive_errors})",
                    str(e)
                )
                
                if consecutive_errors >= max_consecutive_errors:
                    logger.critical(f"Too many consecutive errors ({consecutive_errors}), stopping bot")
                    await self.discord_client.send_system_message(
                        "🛑 **Bot Stopped**",
                        f"Too many consecutive errors. Manual intervention required."
                    )
                    break
                
                # Wait before retrying
                await asyncio.sleep(60)
        
        # Cleanup
        await self.shutdown()
    
    async def analysis_cycle(self):
        """Single analysis cycle"""
        try:
            # Step 1: Fetch current price data
            logger.info("📈 Fetching current gold price data...")
            current_price = self.price_fetcher.get_live_price()
            
            if not current_price:
                logger.error("Failed to fetch current gold price")
                return
            
            logger.info(f"Current Gold Price: ${current_price['mid']:.2f}")
            logger.info(f"Bid/Ask: ${current_price['bid']:.2f} / ${current_price['ask']:.2f}")
            
            # Step 2: Fetch historical data for all timeframes
            logger.info("📊 Fetching historical gold data for analysis...")
            data_dict = self._fetch_all_timeframes()
            
            if not data_dict or not any(df is not None for df in data_dict.values()):
                logger.error("Failed to fetch historical gold data")
                return
            
            # Log data status
            for tf, df in data_dict.items():
                if df is not None:
                    logger.info(f"  ✅ {tf}: {len(df)} candles")
                else:
                    logger.warning(f"  ❌ {tf}: No data")
            
            # Step 3: Fetch and analyze news
            logger.info("📰 Fetching latest gold news...")
            news_data = self.news_fetcher.fetch_all_news()
            analyzed_news = self.news_fetcher.analyze_sentiment(news_data)
            logger.info(f"Fetched {len(analyzed_news)} gold news articles")
            
            # Get news sentiment summary
            sentiment_data = self.news_fetcher.get_aggregated_sentiment(analyzed_news)
            logger.info(f"News Sentiment: {sentiment_data['overall']} (Score: {sentiment_data['score']:.2f})")
            
            # Step 4: Generate signal
            logger.info("🔍 Running comprehensive gold analysis...")
            signal_generator = SignalGenerator(data_dict, analyzed_news)
            signal = signal_generator.generate_signal()
            
            if signal:
                logger.info("✅ VALID GOLD SIGNAL GENERATED!")
                logger.info(f"Direction: {signal['direction']}")
                logger.info(f"Entry: ${signal['entry']:.2f}")
                logger.info(f"Stop Loss: ${signal['stop_loss']:.2f}")
                logger.info(f"Take Profit 1: ${signal['take_profit_1']:.2f}")
                logger.info(f"Confirmations: {signal['confirmation_count']}")
                logger.info(f"Confidence: {signal['confidence_score']:.2%}")
                logger.info(f"Signal Quality: {signal['signal_quality']}")
                
                # Check cooldown (default 2 hours between signals)
                if self._should_send_signal():
                    await self._process_and_send_signal(signal, data_dict)
                    self.signals_generated += 1
                    self.last_signal_time = datetime.utcnow()
                else:
                    logger.info(f"⏸️ Signal suppressed (cooldown period)")
            else:
                logger.info("ℹ️ No valid gold signal at this time")
                logger.info("Reasons: Insufficient confirmations or conflicting signals")
            
            # Step 5: Send periodic market update (every 6 analysis cycles)
            if self.analysis_count % 6 == 0:
                await self._send_gold_market_update(current_price, data_dict, sentiment_data)
            
        except Exception as e:
            logger.error(f"Error in analysis cycle: {e}", exc_info=True)
            raise
    
    def _fetch_all_timeframes(self) -> Dict:
        """Fetch gold data for all configured timeframes"""
        data_dict = {}
        
        # Get primary analysis timeframes
        timeframes_to_fetch = [
            settings.ENTRY_TIMEFRAME,
            settings.PRIMARY_TIMEFRAME,
            settings.HIGHER_TIMEFRAME,
            settings.LOWER_TIMEFRAME
        ]
        
        # Remove duplicates
        timeframes_to_fetch = list(dict.fromkeys(timeframes_to_fetch))
        
        for tf in timeframes_to_fetch:
            try:
                if tf in settings.TIMEFRAMES:
                    tf_str = settings.TIMEFRAMES[tf]
                    df = self.historical_manager.get_data_for_analysis(tf_str, bars=300)
                    if df is not None:
                        data_dict[tf_str] = df
                        logger.debug(f"Fetched {tf_str} data: {len(df)} bars")
                    else:
                        logger.warning(f"Could not fetch {tf_str} data")
                else:
                    logger.warning(f"Unknown timeframe: {tf}")
            except Exception as e:
                logger.error(f"Error fetching {tf}: {e}")
        
        return data_dict
    
    def _should_send_signal(self) -> bool:
        """Check if enough time has passed since last signal"""
        if self.last_signal_time is None:
            return True
        
        time_since_last = datetime.utcnow() - self.last_signal_time
        cooldown = timedelta(hours=2)  # 2 hour cooldown between signals for gold
        
        return time_since_last >= cooldown
    
    async def _process_and_send_signal(self, signal: Dict, data_dict: Dict):
        """Process signal and send to Discord"""
        try:
            # Get entry timeframe data
            entry_tf = signal.get('entry_timeframe', '15m')
            
            # Find matching dataframe
            chart_df = None
            for tf_key, df in data_dict.items():
                if tf_key == entry_tf or tf_key.endswith(entry_tf):
                    chart_df = df
                    break
            
            if chart_df is not None:
                # Generate chart visualization
                logger.info("📊 Generating gold chart visualization...")
                chart_path = self.signal_visualizer.create_signal_chart(
                    chart_df,
                    signal,
                    entry_tf
                )
            else:
                chart_path = None
                logger.warning("Could not generate chart: timeframe data not available")
            
            # Send signal to Discord
            logger.info("📤 Sending gold signal to Discord...")
            await self.discord_client.send_trading_signal(signal, chart_path)
            
            logger.info("✅ Gold signal sent successfully!")
            
        except Exception as e:
            logger.error(f"Error processing/sending gold signal: {e}", exc_info=True)
    
    async def _send_gold_market_update(self, current_price: Dict, data_dict: Dict, 
                                      sentiment_data: Dict):
        """Send periodic gold market update"""
        try:
            # Get primary timeframe data
            primary_tf = settings.PRIMARY_TIMEFRAME
            tf_str = settings.TIMEFRAMES[primary_tf]
            
            if tf_str not in data_dict or data_dict[tf_str] is None:
                return
            
            df = data_dict[tf_str]
            
            # Basic technical analysis
            from src.analysis.technical.babypips_indicators import BabyPipsIndicators
            from src.analysis.technical.ict_analysis import ICTAnalysis
            
            # BabyPips analysis
            babypips = BabyPipsIndicators(df)
            trend = babypips.analyze_trend()
            momentum = babypips.analyze_momentum()
            
            # ICT analysis
            ict = ICTAnalysis(df)
            kill_zone = ict.analyze_kill_zone()
            
            # Support/Resistance
            from src.analysis.technical.support_resistance import SupportResistanceAnalysis
            sr = SupportResistanceAnalysis(df)
            sr_levels = sr.find_all_levels()
            
            # Get nearest support/resistance
            nearest_levels = sr.get_nearest_levels(count=2)
            
            update_msg = (
                f"📊 **Gold Market Update - XAU/USD**\n"
                f"```\n"
                f"Current Price: ${current_price['mid']:.2f}\n"
                f"Trend: {trend['trend'].value}\n"
                f"Momentum: {momentum['overall'].value}\n"
                f"News Sentiment: {sentiment_data['overall']}\n"
                f"In Kill Zone: {'✅' if kill_zone['in_kill_zone'] else '❌'}\n"
                f"Nearest Support: ${nearest_levels.get('support', [{}])[0].get('price', 'N/A'):.2f}\n"
                f"Nearest Resistance: ${nearest_levels.get('resistance', [{}])[0].get('price', 'N/A'):.2f}\n"
                f"```\n"
                f"_Next analysis in {settings.ANALYSIS_INTERVAL} seconds_"
            )
            
            await self.discord_client.send_market_update(update_msg)
            
        except Exception as e:
            logger.error(f"Error sending gold market update: {e}")
    
    async def shutdown(self):
        """Graceful shutdown"""
        logger.info("\n" + "=" * 70)
        logger.info("🛑 Shutting down ArapB Gold Analysis Bot")
        logger.info("=" * 70)
        
        try:
            # Send shutdown message
            await self.discord_client.send_system_message(
                "🛑 **Gold Bot Shutting Down**",
                f"```\nAnalysis Cycles: {self.analysis_count}\n"
                f"Signals Generated: {self.signals_generated}\n"
                f"Uptime: Started at {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC\n"
                f"Pair: {settings.TRADING_PAIR} (Gold)\n```"
            )
            
            # Close Discord client
            await self.discord_client.close()
            
            logger.info("✅ Shutdown complete")
            
        except Exception as e:
            logger.error(f"Error during shutdown: {e}")

async def main():
    """Main entry point"""
    try:
        # Create bot instance
        bot = GoldAnalysisBot()
        
        # Initialize
        await bot.initialize()
        
        # Run
        await bot.run()
        
    except Exception as e:
        logger.critical(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    # Run the bot
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("\nGold Bot stopped by user")
    except Exception as e:
        logger.critical(f"Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
