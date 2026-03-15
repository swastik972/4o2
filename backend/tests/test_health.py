"""
Tests for the health-check endpoint.
"""


def test_health_check(client):
    """GET /api/health should return 200 with status='healthy'."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "version" in data
    assert "app_name" in data


def test_root_endpoint(client):
    """GET / should return 200 with a welcome message."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "docs" in data
