import matplotlib.pyplot as plt
import pandas as pd
from typing import Optional, List, Tuple
from src.utils.logger import logger

class ChartPlotter:
    """Creates OHLC charts with overlays like order blocks and FVGs.

    NOTE: When used interactively, do not set matplotlib styles here.
    """

    def __init__(self):
        pass

    def plot_ohlcv(self, df: pd.DataFrame, title: Optional[str] = None, overlays: Optional[dict] = None, save_path: Optional[str] = None):
        try:
            if df is None or df.empty:
                logger.warning('ChartPlotter: empty dataframe')
                return None
            fig, ax = plt.subplots(figsize=(12,6))
            ax.plot(df.index, df['close'])
            ax.set_title(title or 'OHLC close')
            if overlays:
                # order blocks
                obs = overlays.get('order_blocks') or []
                for ob in obs:
                    ax.axvspan(ob['start'], ob['end'], alpha=0.1)
                # fvg
                fvgs = overlays.get('fvgs') or []
                for f in fvgs:
                    ax.axhspan(f[2], f[3], alpha=0.08)
            if save_path:
                fig.savefig(save_path, bbox_inches='tight')
                plt.close(fig)
                return save_path
            else:
                plt.show()
                return None
        except Exception as e:
            logger.error(f"ChartPlotter plot_ohlcv error: {e}")
            return None
