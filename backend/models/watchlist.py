"""
Watchlist model for organizing user's asset collections.
"""

from sqlalchemy import Column, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from backend.db import Base
from datetime import datetime, timezone
import uuid


class Watchlist(Base):
    """
    Watchlist model for user's curated asset lists.
    
    Uses UUID as primary key for user-facing resources.
    Each watchlist belongs to a user and contains multiple assets.
    All timestamps are stored in UTC.
    """
    
    __tablename__ = 'watchlists'
    
    # Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # Foreign key to user
    user_id = Column(UUID(as_uuid=True), ForeignKey('users.id', ondelete='CASCADE'), 
                    nullable=False, index=True)
    
    # Watchlist info
    name = Column(String(100), nullable=False)
    description = Column(Text)
    
    # Display settings
    color = Column(String(20))  # Hex color code for UI
    icon = Column(String(50))   # Icon identifier for UI
    is_default = Column(String(10), default='false')  # Default watchlist for user
    
    # Timestamps (UTC)
    created_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(timezone.utc), 
                       onupdate=lambda: datetime.now(timezone.utc), nullable=False)
    
    # Relationships
    user = relationship('User', back_populates='watchlists')
    items = relationship('WatchlistItem', back_populates='watchlist', 
                        cascade='all, delete-orphan', order_by='WatchlistItem.position')
    
    def to_dict(self, include_items=False, include_timestamps=True):
        """Convert watchlist to dictionary."""
        data = {
            'id': str(self.id),
            'user_id': str(self.user_id),
            'name': self.name,
            'description': self.description,
            'color': self.color,
            'icon': self.icon,
            'is_default': self.is_default,
        }
        
        if include_timestamps:
            data.update({
                'created_at': self.created_at.isoformat() if self.created_at else None,
                'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            })
        
        if include_items:
            data['items'] = [item.to_dict() for item in self.items]
            data['item_count'] = len(self.items)
        
        return data
    
    def __repr__(self):
        return f'<Watchlist {self.name} (user={self.user_id})>'
