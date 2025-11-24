"""
Basic API tests for trading manager.
Run with: python -m pytest tests/
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app


def test_app_creation():
    """Test that the Flask app can be created."""
    app = create_app()
    assert app is not None


def test_health_endpoint():
    """Test the health check endpoint."""
    app = create_app()
    client = app.test_client()
    
    response = client.get('/health')
    assert response.status_code == 200
    assert response.json['status'] == 'healthy'


def test_index_page():
    """Test that the index page loads."""
    app = create_app()
    client = app.test_client()
    
    response = client.get('/')
    assert response.status_code == 200


def test_login_endpoint():
    """Test the login endpoint."""
    app = create_app()
    client = app.test_client()
    
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
    # Run tests manually
    test_app_creation()
    print("✓ App creation test passed")
    
    test_health_endpoint()
    print("✓ Health endpoint test passed")
    
    test_index_page()
    print("✓ Index page test passed")
    
    test_login_endpoint()
    print("✓ Login endpoint test passed")
    
    print("\nAll tests passed!")
