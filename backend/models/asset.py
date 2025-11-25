"""
Asset model for storing information about tradeable securities.
"""

from sqlalchemy import Column, String, DateTime, Text, Integer
from sqlalchemy.orm import relationship
from backend.db import Base
from datetime import datetime, timezone
import uuid


class Asset(Base):
    """
    Asset model for storing tradeable securities information.
    
    Uses string UUID as primary key for user-facing resources.
    Supports multiple asset types (stocks, ETFs, crypto, etc.).
    All timestamps are stored in UTC.
    """
    
    __tablename__ = 'assets'
    
    # Primary key
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # Asset identification
    symbol = Column(String(20), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    asset_type = Column(String(20), nullable=False, default='stock')
    
    # Asset details
    exchange = Column(String(50))
    currency = Column(String(10), default='USD')
    description = Column(Text)
    
    # Metadata stored as JSON string
    asset_metadata = Column(Text, default='{}')
    
    # Trading information
    is_active = Column(String(10), default='true')  # Can be traded
    market_cap = Column(String(50))
    sector = Column(String(100))
    industry = Column(String(100))
    
    # Timestamps (UTC)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    candles = relationship('Candle', back_populates='asset', cascade='all, delete-orphan')
    watchlist_items = relationship('WatchlistItem', back_populates='asset', cascade='all, delete-orphan')
    
    def to_dict(self, include_timestamps=True):
        """Convert asset to dictionary."""
        data = {
            'id': self.id,
            'symbol': self.symbol,
            'name': self.name,
            'asset_type': self.asset_type,
            'exchange': self.exchange,
            'currency': self.currency,
            'description': self.description,
            'is_active': self.is_active,
            'market_cap': self.market_cap,
            'sector': self.sector,
            'industry': self.industry,
            'metadata': self.asset_metadata,
        }
        
        if include_timestamps:
            data.update({
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            })
        
        return data
    
    def __repr__(self):
        return f'<Asset {self.symbol} ({self.asset_type})>'
