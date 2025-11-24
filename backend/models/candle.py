"""
Candle model for storing OHLCV (candlestick) data.

This table is designed as a TimescaleDB hypertable for efficient time-series storage.
"""

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Numeric, Index, Enum as SQLEnum
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db import Base
from datetime import datetime, timezone
import enum


class CandleInterval(enum.Enum):
    """Enumeration of supported candle intervals."""
    MIN_1 = '1m'
    MIN_5 = '5m'
    MIN_15 = '15m'
    MIN_30 = '30m'
    HOUR_1 = '1h'
    HOUR_4 = '4h'
    DAY_1 = '1d'
    WEEK_1 = '1w'
    MONTH_1 = '1M'


class Candle(Base):
    """
    Candle model for OHLCV time-series data.
    
    Uses bigserial as primary key for time-series efficiency.
    Designed to be converted to a TimescaleDB hypertable partitioned by timestamp.
    All timestamps are stored in UTC.
    
    The table should be converted to a hypertable using:
        SELECT create_hypertable('candles', 'ts', chunk_time_interval => INTERVAL '7 days');
    """
    
    __tablename__ = 'candles'
    
    # Primary key - bigserial for time-series efficiency
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign key to asset
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), 
                     nullable=False, index=True)
    
    # Time data (UTC)
    ts = Column(DateTime, nullable=False, index=True)  # Timestamp - used for hypertable partitioning
    interval = Column(SQLEnum(CandleInterval), nullable=False, default=CandleInterval.DAY_1)
    
    # OHLCV data
    open = Column(Numeric(precision=20, scale=8), nullable=False)
    high = Column(Numeric(precision=20, scale=8), nullable=False)
    low = Column(Numeric(precision=20, scale=8), nullable=False)
    close = Column(Numeric(precision=20, scale=8), nullable=False)
    volume = Column(Numeric(precision=30, scale=8), nullable=False, default=0)
    
    # Additional trading metrics
    trades = Column(BigInteger)  # Number of trades
    vwap = Column(Numeric(precision=20, scale=8))  # Volume-weighted average price
    
    # Data source tracking
    source = Column(String(50), default='manual')  # e.g., 'yahoo', 'manual', 'api'
    
    # Timestamps (UTC)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    asset = relationship('Asset', back_populates='candles')
    
    # Indexes for efficient querying
    __table_args__ = (
        # Composite index for common query patterns
        Index('ix_candles_asset_ts_interval', 'asset_id', 'ts', 'interval'),
        Index('ix_candles_ts_asset', 'ts', 'asset_id'),  # For time-range queries
    )
    
    def to_dict(self, include_timestamps=True):
        """Convert candle to dictionary."""
        data = {
            'id': self.id,
            'asset_id': str(self.asset_id),
            'ts': self.ts.isoformat() if self.ts else None,
            'interval': self.interval.value if self.interval else None,
            'open': float(self.open) if self.open is not None else None,
            'high': float(self.high) if self.high is not None else None,
            'low': float(self.low) if self.low is not None else None,
            'close': float(self.close) if self.close is not None else None,
            'volume': float(self.volume) if self.volume is not None else None,
            'trades': self.trades,
            'vwap': float(self.vwap) if self.vwap is not None else None,
            'source': self.source,
        }
        
        if include_timestamps:
            data['created_at'] = self.created_at.isoformat() if self.created_at else None
        
        return data
    
    def __repr__(self):
        return f'<Candle {self.asset_id} @ {self.ts} [{self.interval.value if self.interval else "?"}]>'
