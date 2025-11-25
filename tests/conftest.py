"""
Pytest configuration and fixtures for trading manager tests.
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from backend.db import create_all_tables, session_scope
from backend.models import User, Asset, Watchlist, WatchlistItem, Candle
from datetime import datetime, timezone, timedelta


@pytest.fixture(scope='function')
def app():
    """Create application for testing."""
    application = create_app('testing')
    
    with application.app_context():
        create_all_tables()
        _seed_test_data()
    
    yield application


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


@pytest.fixture
def auth_token(client):
    """Get authentication token for test user."""
    response = client.post('/api/auth/login', json={
        'username': 'demo',
        'password': 'demo123'
    })
    return response.json.get('token')


def _seed_test_data():
    """Seed test database with demo data."""
    with session_scope() as session:
        # Create demo user
        demo_user = User(
            username='demo',
            email='demo@trading-manager.com',
            full_name='Demo User'
        )
        demo_user.set_password('demo123')
        session.add(demo_user)
        session.flush()
        
        # Create test assets
        assets_data = [
            ('AAPL', 'Apple Inc.', 'stock', 'NASDAQ', 'Technology', 'Consumer Electronics'),
            ('GOOGL', 'Alphabet Inc.', 'stock', 'NASDAQ', 'Technology', 'Internet Services'),
            ('MSFT', 'Microsoft Corporation', 'stock', 'NASDAQ', 'Technology', 'Software'),
        ]
        
        assets = []
        for symbol, name, asset_type, exchange, sector, industry in assets_data:
            asset = Asset(
                symbol=symbol,
                name=name,
                asset_type=asset_type,
                exchange=exchange,
                sector=sector,
                industry=industry,
                currency='USD',
                is_active='true'
            )
            session.add(asset)
            assets.append(asset)
        
        session.flush()
        
        # Create default watchlist
        watchlist = Watchlist(
            user_id=demo_user.id,
            name='Default Watchlist',
            description='Default test watchlist',
            is_default='true'
        )
        session.add(watchlist)
        session.flush()
        
        # Add assets to watchlist
        for i, asset in enumerate(assets):
            item = WatchlistItem(
                watchlist_id=watchlist.id,
                asset_id=asset.id,
                position=i
            )
            session.add(item)
        
        # Generate candle data for each asset
        end_date = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
        start_date = end_date - timedelta(days=365)
        
        for asset in assets:
            current_date = start_date
            base_price = 150.0
            
            while current_date <= end_date:
                # Skip weekends
                if current_date.weekday() >= 5:
                    current_date += timedelta(days=1)
                    continue
                
                candle = Candle(
                    asset_id=asset.id,
                    ts=current_date,
                    interval='1d',
                    open=base_price,
                    high=base_price * 1.02,
                    low=base_price * 0.98,
                    close=base_price * 1.01,
                    volume=1000000,
                    source='test_data'
                )
                session.add(candle)
                base_price *= 1.001  # Slight upward trend
                current_date += timedelta(days=1)
        
        session.commit()
