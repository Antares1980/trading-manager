"""
Basic API tests for trading manager.
Run with: python -m pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


def test_app_creation(app):
    """Test that the Flask app can be created."""
    assert app is not None


def test_health_endpoint(client):
    """Test the health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'


def test_index_page(client):
    """Test that the index page loads."""
    response = client.get('/')
    assert response.status_code == 200


def test_login_endpoint(client):
    """Test the login endpoint."""
    # Test with valid credentials
    response = client.post('/api/auth/login', json={
        'username': 'demo',
        'password': 'demo123'
    })
    assert response.status_code == 200
    assert 'token' in response.json
    
    # Test with invalid credentials
    response = client.post('/api/auth/login', json={
        'username': 'invalid',
        'password': 'wrong'
    })
    assert response.status_code == 401


if __name__ == '__main__':
    import pytest
    pytest.main([__file__, '-v'])
