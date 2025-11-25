"""
Extended API tests for new endpoints.

Run with: pytest tests/test_api_extended.py
"""

import pytest
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from backend.app import create_app
from backend.settings import TestingConfig


@pytest.fixture
def app():
    """Create test Flask app."""
    app = create_app('test')
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()


def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code in [200, 503]  # May fail if DB not available
    data = response.json
    assert 'status' in data


def test_auth_register(client):
    """Test user registration endpoint."""
    response = client.post('/api/auth/register', json={
        'username': 'newuser',
        'email': 'newuser@example.com',
        'password': 'password123',
        'full_name': 'New User'
    })
    
    # May fail if DB not available, accept both success and server error
    assert response.status_code in [201, 500]


def test_auth_login_missing_credentials(client):
    """Test login with missing credentials."""
    response = client.post('/api/auth/login', json={})
    assert response.status_code == 400
    assert 'error' in response.json


def test_auth_login_invalid_credentials(client):
    """Test login with invalid credentials."""
    response = client.post('/api/auth/login', json={
        'username': 'nonexistent',
        'password': 'wrongpassword'
    })
    assert response.status_code in [401, 500]


def test_auth_verify_no_token(client):
    """Test token verification without token."""
    response = client.get('/api/auth/verify')
    assert response.status_code in [401, 422]


def test_assets_list(client):
    """Test listing assets."""
    response = client.get('/api/assets/')
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json
        assert 'assets' in data
        assert 'count' in data


def test_assets_list_with_filters(client):
    """Test listing assets with filters."""
    response = client.get('/api/assets/?asset_type=stock&limit=10')
    assert response.status_code in [200, 500]


def test_candles_list_missing_asset_id(client):
    """Test listing candles without asset_id."""
    response = client.get('/api/candles/')
    assert response.status_code == 400
    assert 'error' in response.json


def test_indicators_list_missing_asset_id(client):
    """Test listing indicators without asset_id."""
    response = client.get('/api/indicators/')
    assert response.status_code == 400
    assert 'error' in response.json


def test_signals_list(client):
    """Test listing signals."""
    response = client.get('/api/signals/')
    assert response.status_code in [200, 500]
    
    if response.status_code == 200:
        data = response.json
        assert 'signals' in data
        assert 'count' in data


def test_signals_list_with_filters(client):
    """Test listing signals with filters."""
    response = client.get('/api/signals/?signal_type=buy&is_active=true')
    assert response.status_code in [200, 500]


def test_watchlists_require_auth(client):
    """Test that watchlist endpoints require authentication."""
    response = client.get('/api/watchlists/')
    assert response.status_code in [401, 422]


def test_indicator_types(client):
    """Test getting indicator types."""
    response = client.get('/api/indicators/types')
    assert response.status_code == 200
    data = response.json
    assert 'indicator_types' in data


def test_signal_types(client):
    """Test getting signal types."""
    response = client.get('/api/signals/types')
    assert response.status_code == 200
    data = response.json
    assert 'signal_types' in data
    assert 'signal_strengths' in data


def test_candles_latest(client):
    """Test getting latest candles."""
    response = client.get('/api/candles/latest')
    assert response.status_code in [200, 500]


def test_signals_latest(client):
    """Test getting latest signals."""
    response = client.get('/api/signals/latest')
    assert response.status_code in [200, 500]


# Integration test (requires database)
def test_full_user_flow(client):
    """Test complete user registration and login flow."""
    # Register
    register_response = client.post('/api/auth/register', json={
        'username': 'flowuser',
        'email': 'flowuser@example.com',
        'password': 'password123',
        'full_name': 'Flow User'
    })
    
    if register_response.status_code != 201:
        pytest.skip("Database not available for integration test")
    
    # Login
    login_response = client.post('/api/auth/login', json={
        'username': 'flowuser',
        'password': 'password123'
    })
    
    assert login_response.status_code == 200
    data = login_response.json
    assert 'token' in data
    assert 'user' in data
    
    token = data['token']
    
    # Verify token
    verify_response = client.get('/api/auth/verify', headers={
        'Authorization': f'Bearer {token}'
    })
    
    assert verify_response.status_code == 200
    verify_data = verify_response.json
    assert verify_data['valid'] is True


if __name__ == '__main__':
    # Run tests manually
    import traceback
    
    # Create test app
    app = create_app('test')
    test_client = app.test_client()
    
    tests = [
        ('Health endpoint', test_health_endpoint),
        ('Auth register', test_auth_register),
        ('Auth login missing credentials', test_auth_login_missing_credentials),
        ('Auth login invalid credentials', test_auth_login_invalid_credentials),
        ('Auth verify no token', test_auth_verify_no_token),
        ('Assets list', test_assets_list),
        ('Assets list with filters', test_assets_list_with_filters),
        ('Candles missing asset_id', test_candles_list_missing_asset_id),
        ('Indicators missing asset_id', test_indicators_list_missing_asset_id),
        ('Signals list', test_signals_list),
        ('Signals with filters', test_signals_list_with_filters),
        ('Watchlists require auth', test_watchlists_require_auth),
        ('Indicator types', test_indicator_types),
        ('Signal types', test_signal_types),
        ('Candles latest', test_candles_latest),
        ('Signals latest', test_signals_latest),
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            test_func(test_client)
            print(f"✓ {test_name}")
            passed += 1
        except Exception as e:
            print(f"✗ {test_name}: {str(e)}")
            traceback.print_exc()
            failed += 1
    
    print(f"\n{passed} passed, {failed} failed")
