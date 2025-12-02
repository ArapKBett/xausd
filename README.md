# 🤖 ArapB Gold Analysis Bot

**Production-Ready Gold (XAU/USD) Analysis Bot** 
Implementing BabyPips Principles + ICT (Inner Circle Trader) Strategies

## 🌟 Features

### Core Capabilities
- ✅ **Multi-Timeframe Analysis** - Analyzes 15m, 1h, 4h, 1d timeframes simultaneously
- ✅ **3-Confirmation System** - Requires minimum 3 confirmations before signal generation
- ✅ **ICT Concepts** - Order blocks, Fair Value Gaps, Kill Zones, Liquidity Analysis
- ✅ **BabyPips Indicators** - Trend analysis, Momentum, Support/Resistance, Fibonacci
- ✅ **Real-Time Gold News Analysis** - Fetches and analyzes gold-specific news sentiment
- ✅ **Advanced Risk Management** - Gold-specific position sizing, R:R calculations
- ✅ **Discord Integration** - Automated signal posting with rich embeds and charts
- ✅ **Professional Visualizations** - Auto-generated gold charts with all levels marked

### Technical Analysis
- Trend Analysis (SMA, EMA, ADX)
- Momentum Indicators (RSI, MACD, Stochastic)
- Volatility Analysis (ATR, Bollinger Bands)
- Support & Resistance Detection (Multiple methods)
- Fibonacci Retracement & Extensions
- Candlestick Pattern Recognition
- Volume Profile Analysis
- Order Block Detection
- Fair Value Gap Identification
- Market Structure Break Detection
- Liquidity Sweep Analysis

### Gold-Specific Risk Management
- **Gold-specific position sizing** (1 standard lot = 100 ounces)
- **Dollar-based risk calculations** for gold
- **Conservative sizing** for gold volatility
- **Psychological level detection** (whole dollar amounts)
- **Minimum 150 pip stops** for gold ($1.50)
- **Minimum 1:2 risk-reward ratio** for gold trades

## 📋 Prerequisites

- Python 3.9 or higher
- Discord Account (for signal notifications)
- Yahoo Finance access for gold data (free)
- News API for gold market news

## 🚀 Installation

### 1. Clone the Repository

`git clone https://github.com/ArapKBett/xausd
cd xausd`

python -m venv venv

# On Windows
venv\Scripts\activate

# On Linux/Mac
source venv/bin/activate

pip install -r requirements.txt

# Discord Configuration (Required)
DISCORD_BOT_TOKEN=your_discord_bot_token_here
DISCORD_CHANNEL_ID=your_channel_id_here
DISCORD_GUILD_ID=your_server_id_here

# Optional: Use webhook instead of bot token
# DISCORD_WEBHOOK_URL=your_webhook_url_here

# Trading Configuration
TRADING_PAIR=GC=F                     # Gold futures on Yahoo Finance
CURRENCY_BASE=XAU                     # Gold
CURRENCY_QUOTE=USD                    # US Dollar
ANALYSIS_INTERVAL=300                 # 5 minutes between analyses
MIN_CONFIRMATIONS=3                   # Minimum confirmations required

# Risk Management (Gold-specific)
RISK_PERCENTAGE=2.0                   # 2% risk per gold trade
MAX_DAILY_TRADES=5                    # Maximum trades per day
MAX_DAILY_LOSS_PERCENT=5.0            # Maximum daily loss %
MIN_RISK_REWARD_RATIO=2.0             # Minimum 1:2 for gold
DEFAULT_STOP_LOSS_PIPS=300            # 300 pips = $3.00 for gold

# API Keys (Optional - for advanced features)
ALPHA_VANTAGE_API_KEY=your_key_here   # Alternative price data
FINNHUB_API_KEY=your_key_here         # Gold news
NEWSAPI_KEY=your_key_here             # General news
OANDA_API_KEY=your_key_here           # Professional price data
OANDA_ACCOUNT_ID=your_account_id      # OANDA account

# Technical Settings
LOG_LEVEL=INFO
REDIS_HOST=localhost                  # For caching
REDIS_PORT=6379



python -m src.main

nohup python -m src.main > bot.log 2>&1 &



