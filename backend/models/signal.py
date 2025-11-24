"""
Signal model for storing trading signals generated from technical analysis.
"""

from sqlalchemy import Column, BigInteger, String, DateTime, ForeignKey, Numeric, Index, Enum as SQLEnum, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from backend.db import Base
from datetime import datetime, timezone
import enum


class SignalType(enum.Enum):
    """Enumeration of signal types."""
    BUY = 'buy'
    SELL = 'sell'
    HOLD = 'hold'
    STRONG_BUY = 'strong_buy'
    STRONG_SELL = 'strong_sell'


class SignalStrength(enum.Enum):
    """Enumeration of signal strength levels."""
    WEAK = 'weak'
    MODERATE = 'moderate'
    STRONG = 'strong'


class Signal(Base):
    """
    Signal model for storing trading signals.
    
    Uses bigserial as primary key for time-series efficiency.
    Stores signals with their rationale and confidence for transparency.
    All timestamps are stored in UTC.
    """
    
    __tablename__ = 'signals'
    
    # Primary key - bigserial for time-series efficiency
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign key to asset
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), 
                     nullable=False, index=True)
    
    # Time data (UTC)
    ts = Column(DateTime, nullable=False, index=True)  # Timestamp of the signal
    
    # Signal details
    signal_type = Column(SQLEnum(SignalType), nullable=False)
    strength = Column(SQLEnum(SignalStrength), default=SignalStrength.MODERATE)
    confidence = Column(Numeric(precision=5, scale=2))  # 0-100 confidence score
    
    # Price context
    price = Column(Numeric(precision=20, scale=8))  # Price at signal generation
    target_price = Column(Numeric(precision=20, scale=8))  # Suggested target price
    stop_loss = Column(Numeric(precision=20, scale=8))  # Suggested stop loss
    
    # Signal rationale
    strategy = Column(String(100))  # Strategy name that generated the signal
    rationale = Column(Text)  # Human-readable explanation
    indicators_used = Column(JSONB, default=list)  # List of indicators used
    
    # Metadata
    timeframe = Column(String(10), default='1d')  # Timeframe analyzed
    is_active = Column(String(10), default='true')  # Whether signal is still active
    
    # Timestamps (UTC)
    generated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    expires_at = Column(DateTime)  # Optional expiration time
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('ix_signals_asset_ts', 'asset_id', 'ts'),
        Index('ix_signals_asset_type_ts', 'asset_id', 'signal_type', 'ts'),
        Index('ix_signals_active', 'is_active', 'ts'),
    )
    
    def to_dict(self, include_timestamps=True):
        """Convert signal to dictionary."""
        data = {
            'id': self.id,
            'asset_id': str(self.asset_id),
            'ts': self.ts.isoformat() if self.ts else None,
            'signal_type': self.signal_type.value if self.signal_type else None,
            'strength': self.strength.value if self.strength else None,
            'confidence': float(self.confidence) if self.confidence is not None else None,
            'price': float(self.price) if self.price is not None else None,
            'target_price': float(self.target_price) if self.target_price is not None else None,
            'stop_loss': float(self.stop_loss) if self.stop_loss is not None else None,
            'strategy': self.strategy,
            'rationale': self.rationale,
            'indicators_used': self.indicators_used,
            'timeframe': self.timeframe,
            'is_active': self.is_active,
        }
        
        if include_timestamps:
            data.update({
                'generated_at': self.generated_at.isoformat() if self.generated_at else None,
                'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            })
        
        return data
    
    def __repr__(self):
        return f'<Signal {self.signal_type.value if self.signal_type else "?"} for {self.asset_id} @ {self.ts}>'
