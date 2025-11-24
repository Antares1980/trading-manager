"""
WatchlistItem model for the many-to-many relationship between watchlists and assets.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Text, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db import Base
from datetime import datetime, timezone
import uuid


class WatchlistItem(Base):
    """
    WatchlistItem model representing assets within a watchlist.
    
    Uses UUID as primary key for user-facing resources.
    Maintains the many-to-many relationship between watchlists and assets.
    Supports ordering and custom notes per asset.
    All timestamps are stored in UTC.
    """
    
    __tablename__ = 'watchlist_items'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign keys
    watchlist_id = Column(UUID(as_uuid=True), ForeignKey('watchlists.id', ondelete='CASCADE'), 
                         nullable=False, index=True)
    asset_id = Column(UUID(as_uuid=True), ForeignKey('assets.id', ondelete='CASCADE'), 
                     nullable=False, index=True)
    
    # Item metadata
    position = Column(Integer, default=0)  # Order in the watchlist
    notes = Column(Text)  # User notes about this asset
    
    # Alert settings (stored as simple flags/values for now)
    price_alert_high = Column(String(20))  # Alert if price goes above this
    price_alert_low = Column(String(20))   # Alert if price goes below this
    
    # Timestamps (UTC)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    watchlist = relationship('Watchlist', back_populates='items')
    asset = relationship('Asset', back_populates='watchlist_items')
    
    # Constraints
    __table_args__ = (
        UniqueConstraint('watchlist_id', 'asset_id', name='uq_watchlist_asset'),
    )
    
    def to_dict(self, include_asset=False, include_timestamps=True):
        """Convert watchlist item to dictionary."""
        data = {
            'id': str(self.id),
            'watchlist_id': str(self.watchlist_id),
            'asset_id': str(self.asset_id),
            'position': self.position,
            'notes': self.notes,
            'price_alert_high': self.price_alert_high,
            'price_alert_low': self.price_alert_low,
        }
        
        if include_timestamps:
            data.update({
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            })
        
        if include_asset and self.asset:
            data['asset'] = self.asset.to_dict(include_timestamps=False)
        
        return data
    
    def __repr__(self):
        return f'<WatchlistItem watchlist={self.watchlist_id} asset={self.asset_id}>'
