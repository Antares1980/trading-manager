"""
Indicator model for storing computed technical indicators.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric, Index, Text
from sqlalchemy.orm import relationship
from backend.db import Base
from datetime import datetime, timezone


class Indicator(Base):
    """
    Indicator model for storing computed technical indicator values.
    
    Stores indicator values with their parameters for reproducibility.
    All timestamps are stored in UTC.
    """
    
    __tablename__ = 'indicators'
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign key to asset
    asset_id = Column(String(36), ForeignKey('assets.id', ondelete='CASCADE'), 
                     nullable=False, index=True)
    
    # Time data (UTC)
    ts = Column(DateTime, nullable=False, index=True)  # Timestamp of the indicator value
    
    # Indicator identification
    indicator_type = Column(String(20), nullable=False)
    name = Column(String(100), nullable=False)  # e.g., "SMA_20", "RSI_14", "MACD_12_26_9"
    
    # Indicator value(s)
    value = Column(Numeric(precision=20, scale=8))  # Primary value
    value2 = Column(Numeric(precision=20, scale=8))  # Secondary value (e.g., MACD signal line)
    value3 = Column(Numeric(precision=20, scale=8))  # Tertiary value (e.g., MACD histogram)
    
    # Parameters used to compute the indicator (stored as JSON string)
    parameters = Column(Text, default='{}')  # e.g., {"period": 20, "type": "simple"}
    
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
            'asset_id': self.asset_id,
            'ts': self.ts.isoformat() if self.ts else None,
            'indicator_type': self.indicator_type,
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
