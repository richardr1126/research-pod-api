import json

def test_health_endpoint(client):
    """Test the health check endpoint"""
    response = client.get('/health')
    assert response.status_code == 200
    data = json.loads(response.data)
    assert "status" in data
    assert "redis" in data
    assert "kafka_producer" in data
    assert "database" in data
    assert "timestamp" in data

def test_create_pod_without_query(client):
    """Test error handling for missing query"""
    response = client.post('/v1/api/pod/create', json={})
    assert response.status_code == 400
    data = json.loads(response.data)
    assert data["error"] == "Missing query in request body"

def test_get_nonexistent_pod(client):
    """Test error handling for nonexistent pod"""
    response = client.get('/v1/api/pod/get/nonexistent-id')
    assert response.status_code == 404

def test_get_pod_status_nonexistent(client):
    """Test error handling for nonexistent pod status"""
    response = client.get('/v1/api/pod/status/nonexistent-id')
    assert response.status_code == 404
    data = json.loads(response.data)
    assert data["error"] == "Pod not found"