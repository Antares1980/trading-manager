"""
Tests for SQLAlchemy models.

Run with: pytest tests/test_models.py
"""

import pytest
from datetime import datetime, timezone
from backend.models import (
    User, Asset, AssetType, Watchlist, WatchlistItem,
    Candle, CandleInterval, Indicator, IndicatorType,
    Signal, SignalType, SignalStrength
)


def test_user_model():
    """Test User model creation and password management."""
    user = User(
        username='testuser',
        email='test@example.com',
        full_name='Test User'
    )
    
    # Test password setting and checking
    user.set_password('testpassword123')
    assert user.password_hash is not None
    assert user.check_password('testpassword123')
    assert not user.check_password('wrongpassword')
    
    # Test to_dict
    user_dict = user.to_dict(include_timestamps=False)
    assert user_dict['username'] == 'testuser'
    assert user_dict['email'] == 'test@example.com'
    assert 'password_hash' not in user_dict


def test_asset_model():
    """Test Asset model creation."""
    asset = Asset(
        symbol='AAPL',
        name='Apple Inc.',
        asset_type=AssetType.STOCK,
        exchange='NASDAQ',
        currency='USD',
        sector='Technology'
    )
    
    assert asset.symbol == 'AAPL'
    assert asset.asset_type == AssetType.STOCK
    
    # Test to_dict
    asset_dict = asset.to_dict(include_timestamps=False)
    assert asset_dict['symbol'] == 'AAPL'
    assert asset_dict['asset_type'] == 'stock'


def test_watchlist_model():
    """Test Watchlist model creation."""
    import uuid
    user_id = uuid.uuid4()
    
    watchlist = Watchlist(
        user_id=user_id,
        name='My Watchlist',
        description='Test watchlist',
        color='#3b82f6'
    )
    
    assert watchlist.name == 'My Watchlist'
    assert str(watchlist.user_id) == str(user_id)
    
    # Test to_dict
    wl_dict = watchlist.to_dict(include_timestamps=False)
    assert wl_dict['name'] == 'My Watchlist'


def test_candle_model():
    """Test Candle model creation."""
    import uuid
    asset_id = uuid.uuid4()
    
    candle = Candle(
        asset_id=asset_id,
        ts=datetime.now(timezone.utc),
        interval=CandleInterval.DAY_1,
        open=100.0,
        high=105.0,
        low=99.0,
        close=103.0,
        volume=1000000
    )
    
    assert candle.open == 100.0
    assert candle.interval == CandleInterval.DAY_1
    
    # Test to_dict
    candle_dict = candle.to_dict(include_timestamps=False)
    assert candle_dict['open'] == 100.0
    assert candle_dict['interval'] == '1d'


def test_indicator_model():
    """Test Indicator model creation."""
    import uuid
    asset_id = uuid.uuid4()
    
    indicator = Indicator(
        asset_id=asset_id,
        ts=datetime.now(timezone.utc),
        indicator_type=IndicatorType.RSI,
        name='RSI_14',
        value=45.5,
        parameters={'period': 14}
    )
    
    assert indicator.indicator_type == IndicatorType.RSI
    assert indicator.value == 45.5
    
    # Test to_dict
    ind_dict = indicator.to_dict(include_timestamps=False)
    assert ind_dict['indicator_type'] == 'rsi'
    assert ind_dict['name'] == 'RSI_14'


def test_signal_model():
    """Test Signal model creation."""
    import uuid
    asset_id = uuid.uuid4()
    
    signal = Signal(
        asset_id=asset_id,
        ts=datetime.now(timezone.utc),
        signal_type=SignalType.BUY,
        strength=SignalStrength.MODERATE,
        confidence=65.0,
        strategy='Test Strategy',
        rationale='Test rationale'
    )
    
    assert signal.signal_type == SignalType.BUY
    assert signal.strength == SignalStrength.MODERATE
    assert signal.confidence == 65.0
    
    # Test to_dict
    sig_dict = signal.to_dict(include_timestamps=False)
    assert sig_dict['signal_type'] == 'buy'
    assert sig_dict['strength'] == 'moderate'


def test_watchlist_item_model():
    """Test WatchlistItem model creation."""
    import uuid
    watchlist_id = uuid.uuid4()
    asset_id = uuid.uuid4()
    
    item = WatchlistItem(
        watchlist_id=watchlist_id,
        asset_id=asset_id,
        position=0,
        notes='Test notes'
    )
    
    assert str(item.watchlist_id) == str(watchlist_id)
    assert str(item.asset_id) == str(asset_id)
    assert item.notes == 'Test notes'
    
    # Test to_dict
    item_dict = item.to_dict(include_timestamps=False)
    assert item_dict['position'] == 0


if __name__ == '__main__':
    # Run tests manually
    test_user_model()
    print("✓ User model test passed")
    
    test_asset_model()
    print("✓ Asset model test passed")
    
    test_watchlist_model()
    print("✓ Watchlist model test passed")
    
    test_candle_model()
    print("✓ Candle model test passed")
    
    test_indicator_model()
    print("✓ Indicator model test passed")
    
    test_signal_model()
    print("✓ Signal model test passed")
    
    test_watchlist_item_model()
    print("✓ WatchlistItem model test passed")
    
    print("\nAll model tests passed!")
