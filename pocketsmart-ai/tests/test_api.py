"""
Basic API tests for PocketSmart AI
Run with: pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Test health check endpoint"""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"


def test_index_page():
    """Test index page loads"""
    response = client.get("/")
    assert response.status_code == 200


def test_login_page():
    """Test login page loads"""
    response = client.get("/login")
    assert response.status_code == 200


def test_register_page():
    """Test register page loads"""
    response = client.get("/register")
    assert response.status_code == 200


def test_dashboard_redirects_without_auth():
    """Test dashboard redirects to login when not authenticated"""
    response = client.get("/dashboard", follow_redirects=False)
    assert response.status_code == 302
    assert "/login" in response.headers["location"]


def test_register_user():
    """Test user registration"""
    response = client.post("/register", json={
        "username": "testuser",
        "email": "test@example.com",
        "full_name": "Test User",
        "password": "testpass123"
    })
    # Either success or already exists
    assert response.status_code in [200, 400]


def test_login_with_demo_credentials():
    """Test login with demo credentials"""
    response = client.post("/token", data={
        "username": "demo",
        "password": "demo123"
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data