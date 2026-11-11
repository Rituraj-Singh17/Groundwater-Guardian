from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_dashboard_route_is_registered():
    response = client.get("/openapi.json")

    assert response.status_code == 200
    assert "/api/dashboard/summary" in response.json()["paths"]


def test_station_routes_are_registered():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert "/api/stations" in paths
    assert "/api/stations/{station_id}" in paths
    assert "/api/stations/{station_id}/reliability" in paths

def test_alert_routes_are_registered():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert "/api/alerts" in paths
    assert "/api/alerts/{alert_id}" in paths


def test_maintenance_routes_are_registered():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert "/api/maintenance" in paths
    assert "/api/maintenance/{maintenance_id}" in paths


def test_maintenance_create_uses_post():
    response = client.get("/openapi.json")
    paths = response.json()["paths"]

    assert "post" in paths["/api/maintenance"]
    assert "patch" in paths["/api/maintenance/{maintenance_id}"]
