import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from matplotlib.patches import Rectangle
import mplfinance as mpf
from typing import Dict, Optional
import os
from datetime import datetime

from src.config.settings import settings
from src.utils.logger import logger

class SignalVisualizer:
    """
    Create professional chart visualizations for trading signals
    """
    
    def __init__(self):
        self.output_dir = "charts"
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Set style
        plt.style.use('dark_background')
        
    def create_signal_chart(self, df: pd.DataFrame, signal: Dict, 
                          timeframe: str) -> str:
        """
        Create a chart with signal visualization
        
        Args:
            df: Price data DataFrame
            signal: Signal dictionary
            timeframe: Timeframe string
            
        Returns:
            Path to saved chart image
        """
        try:
            # Prepare data
            df = df.copy().tail(100)  # Last 100 candles
            
            # Ensure datetime index
            if not isinstance(df.index, pd.DatetimeIndex):
                if 'timestamp' in df.columns:
                    df.index = pd.to_datetime(df['timestamp'])
                elif 'time' in df.columns:
                    df.index = pd.to_datetime(df['time'])
                elif 'date' in df.columns:
                    df.index = pd.to_datetime(df['date'])
                else:
                    # Create dummy datetime index
                    df.index = pd.date_range(end=datetime.utcnow(), periods=len(df), freq='min')
            
            # Required columns for mplfinance
            required_cols = ['open', 'high', 'low', 'close']
            if not all(col in df.columns for col in required_cols):
                # Try lowercase
                df.columns = [col.lower() for col in df.columns]
            
            df_plot = df[required_cols].copy()
            
            # Create figure
            fig = mpf.figure(figsize=(16, 10), facecolor='#0a0e27')
            
            # Define custom style
            mc = mpf.make_marketcolors(
                up='#26a69a',
                down='#ef5350',
                edge='inherit',
                wick='inherit',
                volume='in',
                alpha=0.9
            )
            
            s = mpf.make_mpf_style(
                marketcolors=mc,
                gridstyle=':',
                gridcolor='#2a2e39',
                facecolor='#0a0e27',
                figcolor='#0a0e27',
                edgecolor='#2a2e39'
            )
            
            # Add subplots
            ax1 = fig.add_subplot(3, 1, (1, 2))  # Main chart
            ax2 = fig.add_subplot(3, 1, 3, sharex=ax1)  # Volume
            
            # Plot candlesticks
            mpf.plot(
                df_plot,
                type='candle',
                ax=ax1,
                volume=ax2 if 'volume' in df.columns and df['volume'].sum() > 0 else None,
                style=s,
                warn_too_much_data=len(df_plot) + 1
            )
            
            # Add signal markers
            self._add_signal_markers(ax1, df, signal)
            
            # Add price levels
            self._add_price_levels(ax1, signal)
            
            # Add indicators
            if 'volume' in df.columns and df['volume'].sum() > 0:
                self._format_volume_chart(ax2, df)
            
            # Format main chart
            pair = signal.get('pair', settings.TRADING_PAIR)
            direction = signal.get('direction', 'NEUTRAL')
            entry = signal.get('entry', 0)
            stop_loss = signal.get('stop_loss', 0)
            tp1 = signal.get('take_profit_1', 0)
            
            ax1.set_title(
                f"{pair} - {timeframe.upper()} | {direction} Signal\n"
                f"Entry: ${entry:.2f} | SL: ${stop_loss:.2f} | "
                f"TP1: ${tp1:.2f}",
                fontsize=14,
                fontweight='bold',
                color='white',
                pad=20
            )
            
            ax1.set_ylabel('Price ($)', fontsize=12, color='white')
            ax1.grid(True, alpha=0.2)
            ax1.legend(loc='upper left', fontsize=9, framealpha=0.7)
            
            # Add info box
            self._add_info_box(fig, signal)
            
            # Format x-axis
            ax1.xaxis.set_major_formatter(mdates.DateFormatter('%m/%d %H:%M'))
            ax1.xaxis.set_major_locator(mdates.HourLocator(interval=4))
            
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            
            # Save chart
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            filename = f"signal_{pair}_{direction}_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight', facecolor='#0a0e27')
            plt.close()
            
            logger.info(f"Chart saved: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating signal chart: {e}", exc_info=True)
            return None
    
    def _add_signal_markers(self, ax, df: pd.DataFrame, signal: Dict):
        """Add entry, SL, TP markers"""
        # Get current price index
        last_index = df.index[-1]
        entry = signal.get('entry', 0)
        
        if not entry:
            return
        
        direction = signal.get('direction', 'BUY')
        
        if direction == 'BUY':
            ax.scatter(last_index, entry, 
                      color='#26a69a', s=200, marker='^', 
                      label='Buy Entry', zorder=5, edgecolors='white', linewidths=2)
        elif direction == 'SELL':
            ax.scatter(last_index, entry, 
                      color='#ef5350', s=200, marker='v', 
                      label='Sell Entry', zorder=5, edgecolors='white', linewidths=2)
        else:
            ax.scatter(last_index, entry, 
                      color='yellow', s=200, marker='o', 
                      label='Entry', zorder=5, edgecolors='white', linewidths=2)
    
    def _add_price_levels(self, ax, signal: Dict):
        """Add horizontal lines for entry, SL, TP"""
        xlims = ax.get_xlim()
        ylims = ax.get_ylim()
        
        entry = signal.get('entry', 0)
        stop_loss = signal.get('stop_loss', 0)
        
        if entry:
            # Entry line
            ax.hlines(entry, xlims[0], xlims[1], 
                     colors='yellow', linestyles='--', linewidth=2, 
                     label=f"Entry: ${entry:.2f}", alpha=0.8)
        
        if stop_loss:
            # Stop loss line
            ax.hlines(stop_loss, xlims[0], xlims[1], 
                     colors='red', linestyles='--', linewidth=2, 
                     label=f"Stop Loss: ${stop_loss:.2f}", alpha=0.8)
        
        # Take profit lines
        colors = ['#00ff00', '#00cc00', '#009900']
        tps = [
            signal.get('take_profit_1'),
            signal.get('take_profit_2'),
            signal.get('take_profit_3')
        ]
        
        for i, tp in enumerate(tps):
            if tp:
                ax.hlines(tp, xlims[0], xlims[1], 
                         colors=colors[i], linestyles='--', linewidth=1.5, 
                         label=f"TP{i+1}: ${tp:.2f}", alpha=0.7)
        
        # Reset ylims to include all lines
        ax.set_ylim(min(ylims[0], *[tp for tp in tps if tp], entry or ylims[0], stop_loss or ylims[0]), 
                   max(ylims[1], *[tp for tp in tps if tp], entry or ylims[1], stop_loss or ylims[1]))
    
    def _format_volume_chart(self, ax, df: pd.DataFrame):
        """Format volume subplot"""
        ax.set_ylabel('Volume', fontsize=10, color='white')
        ax.grid(True, alpha=0.2)
        ax.tick_params(colors='white')
    
    def _add_info_box(self, fig, signal: Dict):
        """Add information box to chart"""
        # Get signal info with defaults
        signal_quality = signal.get('signal_quality', 'UNKNOWN')
        confidence = signal.get('confidence_score', 0)
        confirmations_count = signal.get('confirmation_count', 0)
        rr_ratio = signal.get('risk_reward_ratio', 0)
        position_size = signal.get('position_size', 0)
        risk_amount = signal.get('risk_amount', 0)
        
        info_text = (
            f"Signal Quality: {signal_quality}\n"
            f"Confidence: {confidence:.0%}\n"
            f"Confirmations: {confirmations_count}\n"
            f"R:R Ratio: {rr_ratio:.2f}:1\n"
            f"Position: {position_size} lots\n"
            f"Risk: ${risk_amount:.2f}"
        )
        
        # Add box
        fig.text(
            0.02, 0.02, info_text,
            fontsize=9,
            color='white',
            bbox=dict(boxstyle='round', facecolor='#1a1e3a', alpha=0.8, edgecolor='yellow'),
            verticalalignment='bottom',
            family='monospace'
        )
        
        # Add confirmations
        confirmations = signal.get('confirmations', [])
        if confirmations:
            confirmations_text = "Confirmations:\n" + "\n".join([
                f"• {conf.replace('_', ' ').title()}" 
                for conf in confirmations[:5]
            ])
            
            if len(confirmations) > 5:
                confirmations_text += f"\n• ...+{len(confirmations) - 5} more"
            
            fig.text(
                0.98, 0.02, confirmations_text,
                fontsize=8,
                color='#26a69a',
                bbox=dict(boxstyle='round', facecolor='#1a1e3a', alpha=0.8, edgecolor='#26a69a'),
                verticalalignment='bottom',
                horizontalalignment='right',
                family='monospace'
            )
    
    def create_multi_timeframe_chart(self, data_dict: Dict[str, pd.DataFrame], 
                                    signal: Dict) -> str:
        """
        Create a multi-timeframe chart view
        
        Args:
            data_dict: Dictionary of DataFrames for multiple timeframes
            signal: Signal dictionary
            
        Returns:
            Path to saved chart
        """
        try:
            # Filter out None dataframes
            valid_data = {tf: df for tf, df in data_dict.items() if df is not None and len(df) > 0}
            
            if not valid_data:
                logger.warning("No valid data for multi-timeframe chart")
                return None
            
            fig, axes = plt.subplots(len(valid_data), 1, figsize=(16, 5 * len(valid_data)))
            
            if len(valid_data) == 1:
                axes = [axes]
            
            for i, (tf, df) in enumerate(valid_data.items()):
                df = df.tail(100)
                ax = axes[i]
                
                # Plot candlesticks
                for idx in range(len(df)):
                    row = df.iloc[idx]
                    color = '#26a69a' if row['close'] >= row['open'] else '#ef5350'
                    
                    # Body
                    ax.plot([idx, idx], [row['low'], row['high']], color=color, linewidth=1)
                    ax.plot([idx, idx], [row['open'], row['close']], color=color, linewidth=3)
                
                ax.set_title(f"{tf.upper()} Timeframe", fontsize=12, fontweight='bold')
                ax.grid(True, alpha=0.3)
                ax.set_ylabel('Price ($)')
            
            plt.tight_layout()
            
            # Save
            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            pair = signal.get('pair', settings.TRADING_PAIR)
            filename = f"mtf_{pair}_{timestamp}.png"
            filepath = os.path.join(self.output_dir, filename)
            
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close()
            
            return filepath
            
        except Exception as e:
            logger.error(f"Error creating multi-timeframe chart: {e}", exc_info=True)
            return None
