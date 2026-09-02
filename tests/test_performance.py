"""
Automated Performance SLA Benchmarking Tests for OceanEmbed Backend API.
Verifies API response latency is strictly under 2.0 seconds.
"""

import time
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


def test_performance_profile_latency():
    """Verify /predict/profile latency is under 2.0 seconds."""
    start_time = time.time()
    response = client.get("/predict/profile?latitude=15.0&longitude=65.0")
    elapsed = time.time() - start_time

    assert response.status_code == 200
    assert elapsed < 2.0, f"Profile endpoint latency ({elapsed:.3f}s) exceeded SLA (2.0s)."


def test_performance_slice_latency():
    """Verify /predict/slice latency is under 2.0 seconds."""
    start_time = time.time()
    response = client.get("/predict/slice?depth_m=50.0")
    elapsed = time.time() - start_time

    assert response.status_code == 200
    assert elapsed < 2.0, f"Slice endpoint latency ({elapsed:.3f}s) exceeded SLA (2.0s)."


def test_performance_d26_latency():
    """Verify /predict/d26 latency is under 2.0 seconds."""
    start_time = time.time()
    response = client.get("/predict/d26?latitude=12.5&longitude=85.0")
    elapsed = time.time() - start_time

    assert response.status_code == 200
    assert elapsed < 2.0, f"D26 endpoint latency ({elapsed:.3f}s) exceeded SLA (2.0s)."
