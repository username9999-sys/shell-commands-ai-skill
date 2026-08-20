#!/usr/bin/env python3
# test_api.py - Tests for API endpoints

import pytest
import tempfile
import json
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from api.app import app
from api.routes import load_commands_cache

client = TestClient(app)


@pytest.fixture(autouse=True)
def setup_cache():
    # Reset cache before each test
    import api.routes
    api.routes._commands_cache.clear()
    api.routes._categories_cache.clear()


def test_health():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert "version" in data


def test_list_commands():
    response = client.get("/api/v1/commands")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "limit" in data
    assert "offset" in data


def test_get_command_not_found():
    response = client.get("/api/v1/commands/nonexistent")
    assert response.status_code == 404


def test_categories():
    response = client.get("/api/v1/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_summary():
    response = client.get("/api/v1/summary")
    assert response.status_code == 200
    data = response.json()
    assert "total_commands" in data
    assert "categories" in data


def test_search():
    response = client.post("/api/v1/search", json={"query": "test"})
    assert response.status_code == 200
    data = response.json()
    assert "items" in data


def test_explain():
    response = client.post("/api/v1/explain", json={"command": "find"})
    # Will be 404 if command not in cache, that's OK
    assert response.status_code in [200, 404]


if __name__ == '__main__':
    pytest.main([__file__, "-v"])