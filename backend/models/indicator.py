"""
Indicator model for storing computed technical indicators.
"""

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Numeric, Index, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.db import Base
from datetime import datetime, timezone
import enum


class IndicatorType(enum.Enum):
    """Enumeration of supported indicator types."""
    SMA = 'sma'
    EMA = 'ema'
    RSI = 'rsi'
    MACD = 'macd'
    BBANDS = 'bbands'
    ATR = 'atr'
    OBV = 'obv'
    STOCH = 'stoch'
    ADX = 'adx'
    CCI = 'cci'


class Indicator(Base):
    """
    Indicator model for storing computed technical indicator values.
    
    Uses bigserial as primary key for time-series efficiency.
    Stores indicator values with their parameters for reproducibility.
    All timestamps are stored in UTC.
    """
    
    __tablename__ = 'indicators'
    
    # Primary key - bigserial for time-series efficiency
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign key to asset
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), 
                     nullable=False, index=True)
    
    # Time data (UTC)
    ts = Column(DateTime, nullable=False, index=True)  # Timestamp of the indicator value
    
    # Indicator identification
    indicator_type = Column(SQLEnum(IndicatorType), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "SMA_20", "RSI_14", "MACD_12_26_9"
    
    # Indicator value(s)
    value = Column(Numeric(precision=20, scale=8))  # Primary value
    value2 = Column(Numeric(precision=20, scale=8))  # Secondary value (e.g., MACD signal line)
    value3 = Column(Numeric(precision=20, scale=8))  # Tertiary value (e.g., MACD histogram)
    
    # Parameters used to compute the indicator (stored as JSON)
    parameters = Column(JSONB, default=dict)  # e.g., {"period": 20, "type": "simple"}
    
    # Metadata
    timeframe = Column(String(10), default='1d')  # Timeframe used for computation
    
    # Timestamps (UTC)
    computed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_indicators_asset_type_ts', 'asset_id', 'indicator_type', 'ts'),
        Index('ix_indicators_asset_name_ts', 'asset_id', 'name', 'ts'),
    )
    
    def to_dict(self, include_timestamps=True):
        """Convert indicator to dictionary."""
        data = {
            'id': self.id,
            'asset_id': str(self.asset_id),
            'ts': self.ts.isoformat() if self.ts else None,
            'indicator_type': self.indicator_type.value if self.indicator_type else None,
            'name': self.name,
            'value': float(self.value) if self.value is not None else None,
            'value2': float(self.value2) if self.value2 is not None else None,
            'value3': float(self.value3) if self.value3 is not None else None,
            'parameters': self.parameters,
            'timeframe': self.timeframe,
        }
        
        if include_timestamps:
            data['computed_at'] = self.computed_at.isoformat() if self.computed_at else None
        
        return data
    
    def __repr__(self):
        return f'<Indicator {self.name} for {self.asset_id} @ {self.ts}>'
