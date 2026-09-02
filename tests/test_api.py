"""
Automated Integration and Unit Tests for OceanEmbed FastAPI Backend API.
Tests routes, schemas, coordinate boundary validation, and D26 linear interpolation math.
"""

from fastapi.testclient import TestClient
from api.main import app
from src.inference.mock_engine import calculate_d26, TARGET_DEPTHS_M

client = TestClient(app)


def test_health_check():
    """Verify /health endpoint returns HTTP 200 OK and expected keys."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["version"] == "1.0.0"
    assert "model_loaded" in data


def test_profile_valid_coordinates():
    """Verify /predict/profile returns 15 depths and temperatures for valid Ocean coordinate."""
    response = client.get("/predict/profile?latitude=15.0&longitude=65.0")
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 15.0
    assert data["longitude"] == 65.0
    assert len(data["depths_m"]) == 15
    assert len(data["temperatures_c"]) == 15
    assert data["is_land"] is False
    assert data["surface_temp_c"] is not None
    assert data["d26_depth_m"] is not None


def test_profile_post_valid_coordinates():
    """Verify POST /predict/profile with JSON body."""
    payload = {"latitude": 12.0, "longitude": 85.0}
    response = client.post("/predict/profile", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 12.0
    assert data["longitude"] == 85.0
    assert len(data["depths_m"]) == 15


def test_profile_out_of_bounds_latitude():
    """Verify latitude outside [5, 30] returns HTTP 400 Bad Request."""
    response = client.get("/predict/profile?latitude=35.0&longitude=65.0")
    assert response.status_code == 400
    assert "Latitude 35.0°N is out of bounds" in response.json()["detail"]


def test_profile_out_of_bounds_longitude():
    """Verify longitude outside [45, 105] returns HTTP 400 Bad Request."""
    response = client.get("/predict/profile?latitude=15.0&longitude=120.0")
    assert response.status_code == 400
    assert "Longitude 120.0°E is out of bounds" in response.json()["detail"]


def test_slice_valid_depth():
    """Verify /predict/slice returns 101x241 matrix for valid depth level."""
    response = client.get("/predict/slice?depth_m=50.0")
    assert response.status_code == 200
    data = response.json()
    assert data["depth_m"] == 50.0
    assert data["grid_shape"] == [101, 241]
    assert len(data["latitudes"]) == 101
    assert len(data["longitudes"]) == 241
    assert len(data["temperatures_2d"]) == 101
    assert len(data["temperatures_2d"][0]) == 241


def test_d26_endpoint():
    """Verify /predict/d26 endpoint returns valid thermocline depth."""
    response = client.get("/predict/d26?latitude=12.5&longitude=85.0")
    assert response.status_code == 200
    data = response.json()
    assert data["latitude"] == 12.5
    assert data["longitude"] == 85.0
    assert "d26_depth_m" in data
    assert data["is_valid_thermocline"] is True


def test_d26_math_interpolation():
    """
    Directly verify D26 linear interpolation mathematics against known benchmark values.
    Benchmark: If 50m is 27°C and 75m is 25°C, D26 must equal exactly 62.5m.
    """
    depths = [0.0, 5.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 300.0, 500.0, 700.0, 1000.0]
    temps =  [28.5, 28.5, 28.4, 28.2, 28.0, 27.0, 25.0,  20.0,  16.0,  14.0,  12.0,   9.0,   6.0,   5.0,    4.0]
    
    d26_depth, is_valid, explanation = calculate_d26(depths, temps)
    assert is_valid is True
    # z1=50, z2=75, t1=27, t2=25 -> 50 + (26-27)*(75-50)/(25-27) = 50 + (-1)(25)/(-2) = 62.5m
    assert d26_depth == 62.5


def test_d26_math_edge_case_cold_surface():
    """Verify surface temp < 26°C returns None for D26."""
    depths = [0.0, 5.0, 10.0, 20.0, 30.0, 50.0, 75.0, 100.0, 125.0, 150.0, 200.0, 300.0, 500.0, 700.0, 1000.0]
    temps =  [24.5, 24.0, 23.5, 22.0, 21.0, 20.0, 18.0,  16.0,  14.0,  12.0,  10.0,   8.0,   6.0,   5.0,    4.0]
    
    d26_depth, is_valid, explanation = calculate_d26(depths, temps)
    assert is_valid is False
    assert d26_depth is None
    assert "below 26.0°C" in explanation
