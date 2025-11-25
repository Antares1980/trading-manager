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
                       'change_1m', 'change_1y', 'sparkline', 'data_status']
    
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


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
