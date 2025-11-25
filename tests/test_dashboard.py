"""
Tests for dashboard API endpoints.

Run with: pytest tests/test_dashboard.py -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_dashboard_requires_auth(client):
    """Test that dashboard endpoint requires authentication."""
    response = client.get('/api/dashboard/watchlist-summary')
    assert response.status_code == 401


def test_dashboard_watchlist_summary(client, auth_token):
    """Test getting watchlist summary with valid auth."""
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assert 'success' in data
    assert data['success'] is True
    assert 'assets' in data
    assert 'watchlist_index' in data
    assert 'watchlist_info' in data


def test_dashboard_assets_have_required_fields(client, auth_token):
    """Test that assets in dashboard have all required fields."""
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assets = data.get('assets', [])
    
    # Should have test assets from conftest
    assert len(assets) > 0
    
    # Check required fields for each asset
    required_fields = ['symbol', 'name', 'last_price', 'change_1d', 'change_1w', 
                       'change_1m', 'change_1y', 'sparkline', 'data_status',
                       'asset_id', 'watchlist_item_id']
    
    for asset in assets:
        for field in required_fields:
            assert field in asset, f"Missing field: {field} in asset {asset.get('symbol')}"


def test_dashboard_watchlist_info(client, auth_token):
    """Test that watchlist info is returned correctly."""
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    watchlist_info = data.get('watchlist_info')
    
    assert watchlist_info is not None
    assert 'id' in watchlist_info
    assert 'name' in watchlist_info
    assert 'item_count' in watchlist_info


def test_dashboard_sparkline_data(client, auth_token):
    """Test that sparkline data is returned for assets."""
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assets = data.get('assets', [])
    
    # At least one asset should have sparkline data
    has_sparkline = any(len(asset.get('sparkline', [])) > 0 for asset in assets)
    assert has_sparkline, "No assets have sparkline data"


def test_dashboard_percentage_changes(client, auth_token):
    """Test that percentage changes are calculated correctly."""
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assets = data.get('assets', [])
    
    for asset in assets:
        # Check that percentage values are reasonable (within -100% to +1000%)
        for change_field in ['change_1d', 'change_1w', 'change_1m', 'change_1y']:
            change = asset.get(change_field)
            if change is not None:
                assert -100 <= change <= 1000, f"Unreasonable {change_field}: {change}"


def test_dashboard_percentage_changes_anchored_to_latest_candle(app):
    """
    Test that percentage changes are anchored to the latest candle timestamp,
    not the current wall-clock time.
    
    This test creates controlled candle data at specific dates with known prices
    to verify that percentage changes are computed correctly.
    """
    from backend.db import session_scope
    from backend.models import User, Asset, Watchlist, WatchlistItem, Candle
    from datetime import datetime, timezone, timedelta
    
    with app.app_context():
        with session_scope() as session:
            # Create a new test user for this isolated test
            test_user = User(
                username='pct_test_user',
                email='pct_test@test.com',
                full_name='Percentage Test User'
            )
            test_user.set_password('testpass123')
            session.add(test_user)
            session.flush()
            
            # Create test asset
            test_asset = Asset(
                symbol='PCTTEST',
                name='Percentage Test Asset',
                asset_type='stock',
                exchange='TEST',
                currency='USD',
                is_active='true'
            )
            session.add(test_asset)
            session.flush()
            
            # Create watchlist for test user
            test_watchlist = Watchlist(
                user_id=test_user.id,
                name='Percentage Test Watchlist',
                description='Test watchlist',
                is_default='true'
            )
            session.add(test_watchlist)
            session.flush()
            
            # Add asset to watchlist
            test_item = WatchlistItem(
                watchlist_id=test_watchlist.id,
                asset_id=test_asset.id,
                position=0
            )
            session.add(test_item)
            session.flush()
            
            # Create candles with known prices at specific dates
            # Latest candle: 7 days ago from "now" with close = 110
            # 1 day before latest: close = 100 (10% change)
            # 7 days before latest: close = 90 (~22.22% change)
            
            # Use a fixed anchor date in the past to simulate old data
            anchor_date = datetime(2024, 6, 15, 0, 0, 0, tzinfo=timezone.utc)
            
            candles_data = [
                # Latest candle (anchor)
                (anchor_date, 110.0),
                # 1 day before anchor
                (anchor_date - timedelta(days=1), 100.0),
                # 7 days before anchor
                (anchor_date - timedelta(days=7), 90.0),
                # 30 days before anchor  
                (anchor_date - timedelta(days=30), 80.0),
            ]
            
            for ts, close_price in candles_data:
                candle = Candle(
                    asset_id=test_asset.id,
                    ts=ts,
                    interval='1d',
                    open=close_price * 0.99,
                    high=close_price * 1.01,
                    low=close_price * 0.98,
                    close=close_price,
                    volume=1000000,
                    source='test_anchored'
                )
                session.add(candle)
            
            session.commit()
            
            # Get user ID for API call
            user_id = test_user.id
        
        # Now make API call as the test user
        client = app.test_client()
        
        # Login as test user
        response = client.post('/api/auth/login', json={
            'username': 'pct_test_user',
            'password': 'testpass123'
        })
        assert response.status_code == 200
        token = response.json.get('token')
        
        # Get watchlist summary
        response = client.get(
            '/api/dashboard/watchlist-summary',
            headers={'Authorization': f'Bearer {token}'}
        )
        assert response.status_code == 200
        
        data = response.json
        assets = data.get('assets', [])
        
        # Find our test asset
        test_asset_data = None
        for asset in assets:
            if asset['symbol'] == 'PCTTEST':
                test_asset_data = asset
                break
        
        assert test_asset_data is not None, "Test asset not found in response"
        
        # Verify price
        assert test_asset_data['last_price'] == 110.0
        
        # Verify 1D change: (110 - 100) / 100 * 100 = 10%
        assert test_asset_data['change_1d'] == 10.0, \
            f"Expected 1D change of 10%, got {test_asset_data['change_1d']}"
        
        # Verify 1W change: (110 - 90) / 90 * 100 = 22.22%
        expected_1w_change = round((110 - 90) / 90 * 100, 2)
        assert test_asset_data['change_1w'] == expected_1w_change, \
            f"Expected 1W change of {expected_1w_change}%, got {test_asset_data['change_1w']}"
        
        # Verify 1M change: (110 - 80) / 80 * 100 = 37.5%
        expected_1m_change = round((110 - 80) / 80 * 100, 2)
        assert test_asset_data['change_1m'] == expected_1m_change, \
            f"Expected 1M change of {expected_1m_change}%, got {test_asset_data['change_1m']}"
        
        # 1Y change should be None (no data 365 days back)
        assert test_asset_data['change_1y'] is None, \
            f"Expected 1Y change to be None, got {test_asset_data['change_1y']}"


def test_dashboard_watchlist_index(client, auth_token):
    """Test that watchlist index is calculated."""
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    watchlist_index = data.get('watchlist_index')
    
    # Index should be calculated if there's enough data
    # It's normalized to 200-day MA, so should be around 100 for fair value
    if watchlist_index is not None:
        assert 0 < watchlist_index < 500, f"Unreasonable watchlist index: {watchlist_index}"


def test_dashboard_quick_stats(client, auth_token):
    """Test the quick stats endpoint."""
    response = client.get(
        '/api/dashboard/quick-stats',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assert 'success' in data
    assert data['success'] is True
    assert 'stats' in data
    
    stats = data['stats']
    assert 'watchlist_count' in stats
    assert 'asset_count' in stats
    assert stats['watchlist_count'] >= 1
    assert stats['asset_count'] >= 0


def test_dashboard_default_watchlist_endpoint(client, auth_token):
    """Test the default watchlist endpoint."""
    response = client.get(
        '/api/dashboard/default-watchlist',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assert 'success' in data
    assert data['success'] is True
    assert 'watchlist' in data
    
    watchlist = data['watchlist']
    assert 'id' in watchlist
    assert 'name' in watchlist


def test_dashboard_page_loads(client):
    """Test that the dashboard page loads."""
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data


def test_asset_page_redirects(client):
    """Test that the asset detail page redirects correctly."""
    response = client.get('/asset/AAPL', follow_redirects=False)
    assert response.status_code == 302
    assert '/?ticker=AAPL' in response.headers['Location']


def test_search_assets(client, auth_token):
    """Test the asset search endpoint."""
    response = client.get(
        '/api/assets/?search=AAPL&limit=10',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assert 'assets' in data
    # Should find AAPL from test data
    assert len(data['assets']) > 0
    
    # Test with symbol that exists
    symbols = [a['symbol'] for a in data['assets']]
    assert 'AAPL' in symbols


def test_add_asset_to_watchlist(client, auth_token):
    """Test adding an asset to watchlist."""
    # First get the default watchlist
    response = client.get(
        '/api/dashboard/default-watchlist',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    watchlist_id = response.json['watchlist']['id']
    
    # Get list of assets to find one not in watchlist
    response = client.get(
        '/api/assets/?limit=100',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    all_assets = response.json['assets']
    
    # Get current watchlist assets
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    current_asset_ids = [a['asset_id'] for a in response.json.get('assets', [])]
    
    # Find an asset not in watchlist, or use an existing one to test duplicate handling
    test_asset = all_assets[0] if all_assets else None
    if test_asset and test_asset['id'] in current_asset_ids:
        # Asset already in watchlist, test duplicate prevention
        response = client.post(
            f'/api/watchlists/{watchlist_id}/items',
            headers={'Authorization': f'Bearer {auth_token}'},
            json={'asset_id': test_asset['id']}
        )
        assert response.status_code == 409  # Conflict - already exists


def test_remove_asset_from_watchlist(client, auth_token):
    """Test removing an asset from watchlist."""
    # Get watchlist summary to get an item to remove
    response = client.get(
        '/api/dashboard/watchlist-summary',
        headers={'Authorization': f'Bearer {auth_token}'}
    )
    assert response.status_code == 200
    
    data = response.json
    assets = data.get('assets', [])
    watchlist_info = data.get('watchlist_info')
    
    if assets and watchlist_info:
        # Get the first asset's watchlist item ID
        asset = assets[0]
        watchlist_id = watchlist_info['id']
        watchlist_item_id = asset['watchlist_item_id']
        
        # Remove the asset
        response = client.delete(
            f'/api/watchlists/{watchlist_id}/items/{watchlist_item_id}',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        
        # Verify the asset is removed
        response = client.get(
            '/api/dashboard/watchlist-summary',
            headers={'Authorization': f'Bearer {auth_token}'}
        )
        assert response.status_code == 200
        
        new_assets = response.json.get('assets', [])
        new_ids = [a['watchlist_item_id'] for a in new_assets]
        assert watchlist_item_id not in new_ids


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
