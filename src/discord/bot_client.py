import discord
from discord.ext import commands
import aiohttp
from typing import Optional, Dict
from datetime import datetime
import os

from src.config.settings import settings
from src.utils.logger import logger
from src.utils.helpers import format_price, format_pips

class DiscordBotClient:
    """
    Discord bot client for sending trading signals and updates
    Professional-grade formatting and error handling
    """
    
    def __init__(self):
        # Setup intents
        intents = discord.Intents.default()
        intents.message_content = True
        
        self.bot = commands.Bot(command_prefix='!', intents=intents)
        self.channel = None
        self.webhook_url = None  # Fixed: Use environment variable
        self.is_initialized = False
        
        # Setup bot events
        @self.bot.event
        async def on_ready():
            logger.info(f'Discord bot logged in as {self.bot.user}')
            
            # Get channel
            if settings.DISCORD_CHANNEL_ID:
                self.channel = self.bot.get_channel(settings.DISCORD_CHANNEL_ID)
                if self.channel:
                    logger.info(f'Connected to channel: {self.channel.name}')
                else:
                    logger.error(f'Could not find channel with ID: {settings.DISCORD_CHANNEL_ID}')
    
    async def initialize(self):
        """Initialize Discord connection"""
        try:
            # Get webhook URL from settings or environment
            self.webhook_url = getattr(settings, 'DISCORD_WEBHOOK_URL', None)
            
            if self.webhook_url:
                # Use webhook mode (simpler, no bot token needed)
                logger.info("Using Discord webhook mode")
                self.is_initialized = True
                return True
            elif settings.DISCORD_BOT_TOKEN:
                # Use bot mode (requires bot token)
                logger.info("Using Discord bot mode")
                # Note: Bot should be started separately, not here
                # In production, the bot.start() should be handled in main.py
                self.is_initialized = True
                return True
            else:
                logger.error("No Discord credentials configured")
                return False
            
        except Exception as e:
            logger.error(f"Failed to initialize Discord: {e}")
            return False
    
    async def send_trading_signal(self, signal: Dict, chart_path: Optional[str] = None):
        """
        Send a trading signal to Discord channel
        
        Args:
            signal: Signal dictionary with all details
            chart_path: Path to chart image (optional)
        """
        try:
            # Create rich embed
            embed = discord.Embed(
                title=f"🎯 NEW TRADING SIGNAL - {signal.get('pair', settings.TRADING_PAIR)}",
                description=f"**{signal.get('direction', 'NEUTRAL')}** Setup Detected",
                color=discord.Color.green() if signal.get('direction') == 'BUY' else discord.Color.red(),
                timestamp=datetime.utcnow()
            )
            
            # Entry Details
            entry = signal.get('entry', 0)
            embed.add_field(
                name="📍 Entry Price",
                value=f"```{format_price(entry)}```",
                inline=True
            )
            
            # Stop Loss
            stop_loss = signal.get('stop_loss', 0)
            if entry and stop_loss:
                sl_pips = abs(entry - stop_loss) / settings.PIP_VALUE
                embed.add_field(
                    name="🛑 Stop Loss",
                    value=f"```{format_price(stop_loss)}\n({sl_pips:.1f} pips)```",
                    inline=True
                )
            else:
                embed.add_field(
                    name="🛑 Stop Loss",
                    value=f"```{format_price(stop_loss)}```",
                    inline=True
                )
            
            # Position Size
            position_size = signal.get('position_size', 0)
            risk_amount = signal.get('risk_amount', 0)
            embed.add_field(
                name="📊 Position Size",
                value=f"```{position_size} lots\n(${risk_amount:.2f} risk)```",
                inline=True
            )
            
            # Take Profits
            tp_text = f"**TP1:** {format_price(signal.get('take_profit_1', 0))}"
            if signal.get('take_profit_2'):
                tp_text += f"\n**TP2:** {format_price(signal['take_profit_2'])}"
            if signal.get('take_profit_3'):
                tp_text += f"\n**TP3:** {format_price(signal['take_profit_3'])}"
            
            embed.add_field(
                name="🎯 Take Profit Levels",
                value=tp_text,
                inline=False
            )
            
            # Risk-Reward
            rr_ratio = signal.get('risk_reward_ratio', 0)
            embed.add_field(
                name="💰 Risk/Reward",
                value=f"```{rr_ratio:.2f}:1```" if rr_ratio else "```Calculating...```",
                inline=True
            )
            
            # Signal Quality
            quality_emoji = {
                'EXCELLENT': '🌟',
                'GOOD': '✅',
                'FAIR': '👍',
                'POOR': '⚠️'
            }
            signal_quality = signal.get('signal_quality', 'UNKNOWN')
            embed.add_field(
                name=f"{quality_emoji.get(signal_quality, '📊')} Signal Quality",
                value=f"```{signal_quality}```",
                inline=True
            )
            
            # Confidence
            confidence = signal.get('confidence_score', 0)
            embed.add_field(
                name="🎲 Confidence",
                value=f"```{confidence:.0%}```" if confidence else "```N/A```",
                inline=True
            )
            
            # Analysis Details
            analysis_text = (
                f"**Timeframe Alignment:** {signal.get('timeframe_alignment', 'N/A')}\n"
                f"**Primary Trend:** {signal.get('primary_trend', 'N/A')}\n"
                f"**Trend Strength:** {signal.get('trend_strength', 0):.0f}%\n"
                f"**Momentum Score:** {signal.get('momentum_score', 0):.0f}/100\n"
            )
            
            if signal.get('in_kill_zone'):
                analysis_text += f"**Kill Zone:** {signal.get('kill_zone_name', 'N/A')} ⚡\n"
            
            embed.add_field(
                name="📈 Technical Analysis",
                value=analysis_text,
                inline=False
            )
            
            # Market Conditions
            conditions_text = (
                f"**Volatility:** {signal.get('volatility', 'N/A')}\n"
                f"**Liquidity:** {signal.get('liquidity', 'N/A')}\n"
                f"**Market Structure:** {signal.get('market_structure', 'N/A')}\n"
            )
            
            if signal.get('news_sentiment') != 'NEUTRAL':
                conditions_text += f"**News Sentiment:** {signal.get('news_sentiment', 'N/A')}"
            
            embed.add_field(
                name="🌍 Market Conditions",
                value=conditions_text,
                inline=True
            )
            
            # Confirmations
            confirmations = signal.get('confirmations', [])
            confirmations_text = "\n".join([
                f"✓ {conf.replace('_', ' ').title()}" 
                for conf in confirmations[:6]
            ])
            
            if len(confirmations) > 6:
                confirmations_text += f"\n...and {len(confirmations) - 6} more"
            
            embed.add_field(
                name=f"✅ Confirmations ({signal.get('confirmation_count', 0)})",
                value=confirmations_text if confirmations_text else "No confirmations",
                inline=True
            )
            
            # Entry & Stop Reasons
            reasons_text = (
                f"**Entry:** {signal.get('entry_reason', 'N/A')}\n"
                f"**Stop:** {signal.get('stop_reason', 'N/A')}"
            )
            
            embed.add_field(
                name="💡 Setup Details",
                value=reasons_text,
                inline=False
            )
            
            # Key Levels
            if signal.get('nearest_support') or signal.get('nearest_resistance'):
                levels_text = ""
                if signal.get('nearest_support'):
                    levels_text += f"**Support:** {format_price(signal['nearest_support'])}\n"
                if signal.get('nearest_resistance'):
                    levels_text += f"**Resistance:** {format_price(signal['nearest_resistance'])}"
                
                embed.add_field(
                    name="🔑 Key Levels",
                    value=levels_text,
                    inline=False
                )
            
            # Footer
            embed.set_footer(
                text=f"Courtesy of {signal.get('generated_by', 'ArapB Gold Analysis Bot')} | "
                     f"Analysis powered by BabyPips + ICT Strategies"
            )
            
            # Send via webhook or bot
            if self.webhook_url:
                await self._send_via_webhook(embed, chart_path)
            elif self.channel:
                await self._send_via_bot(embed, chart_path)
            else:
                logger.error("No Discord channel configured")
            
            logger.info("✅ Signal sent to Discord successfully")
            
        except Exception as e:
            logger.error(f"Failed to send signal to Discord: {e}", exc_info=True)
    
    async def _send_via_webhook(self, embed: discord.Embed, chart_path: Optional[str] = None):
        """Send message via webhook"""
        if not self.webhook_url:
            logger.error("Webhook URL not configured")
            return
        
        async with aiohttp.ClientSession() as session:
            try:
                webhook = discord.Webhook.from_url(
                    self.webhook_url,
                    session=session
                )
                
                if chart_path and os.path.exists(chart_path):
                    with open(chart_path, 'rb') as f:
                        file = discord.File(f, filename='chart.png')
                        embed.set_image(url='attachment://chart.png')
                        await webhook.send(embed=embed, file=file)
                else:
                    await webhook.send(embed=embed)
                    
            except Exception as e:
                logger.error(f"Failed to send via webhook: {e}")
    
    async def _send_via_bot(self, embed: discord.Embed, chart_path: Optional[str] = None):
        """Send message via bot"""
        if not self.channel:
            logger.error("Discord channel not available")
            return
        
        try:
            if chart_path and os.path.exists(chart_path):
                with open(chart_path, 'rb') as f:
                    file = discord.File(f, filename='chart.png')
                    embed.set_image(url='attachment://chart.png')
                    await self.channel.send(embed=embed, file=file)
            else:
                await self.channel.send(embed=embed)
                
        except Exception as e:
            logger.error(f"Failed to send via bot: {e}")
    
    async def send_system_message(self, title: str, message: str):
        """Send a system message"""
        try:
            embed = discord.Embed(
                title=title,
                description=message,
                color=discord.Color.blue(),
                timestamp=datetime.utcnow()
            )
            
            if self.webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                    await webhook.send(embed=embed)
            elif self.channel:
                await self.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to send system message: {e}")
    
    async def send_error_message(self, title: str, error: str):
        """Send an error notification"""
        try:
            embed = discord.Embed(
                title=title,
                description=f"```{error}```",
                color=discord.Color.dark_red(),
                timestamp=datetime.utcnow()
            )
            
            if self.webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                    await webhook.send(embed=embed)
            elif self.channel:
                await self.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to send error message: {e}")
    
    async def send_market_update(self, message: str):
        """Send a periodic market update"""
        try:
            embed = discord.Embed(
                description=message,
                color=discord.Color.light_gray(),
                timestamp=datetime.utcnow()
            )
            
            if self.webhook_url:
                async with aiohttp.ClientSession() as session:
                    webhook = discord.Webhook.from_url(self.webhook_url, session=session)
                    await webhook.send(embed=embed)
            elif self.channel:
                await self.channel.send(embed=embed)
            
        except Exception as e:
            logger.error(f"Failed to send market update: {e}")
    
    async def close(self):
        """Close Discord connection"""
        try:
            if self.bot and not self.bot.is_closed():
                await self.bot.close()
        except Exception as e:
            logger.error(f"Error closing Discord connection: {e}")
