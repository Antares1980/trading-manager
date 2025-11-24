"""
Models package for SQLAlchemy database models.

All models use UTC for timestamps.
User-facing resources use UUID primary keys.
Time-series data uses bigserial primary keys for efficiency.
"""

from backend.models.user import User
from backend.models.asset import Asset, AssetType
from backend.models.watchlist import Watchlist
from backend.models.watchlist_item import WatchlistItem
from backend.models.candle import Candle, CandleInterval
from backend.models.indicator import Indicator, IndicatorType
from backend.models.signal import Signal, SignalType, SignalStrength

__all__ = [
    'User',
    'Asset',
    'AssetType',
    'Watchlist',
    'WatchlistItem',
    'Candle',
    'CandleInterval',
    'Indicator',
    'IndicatorType',
    'Signal',
    'SignalType',
    'SignalStrength',
]
