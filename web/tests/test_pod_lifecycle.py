import json
import time

GLOBAL_POD_ID = None

def test_01_create_pod(client):
    """Test pod creation and verify initial response"""
    response = client.post('/v1/api/pod/create', json={'query': 'pytest'})
    assert response.status_code == 202
    data = json.loads(response.data)
    global GLOBAL_POD_ID
    GLOBAL_POD_ID = data["pod_id"]

    # Verify the pod was created (pod_id fixture already created it)
    assert GLOBAL_POD_ID is not None
    
    # Check initial status
    status_response = client.get(f'/v1/api/pod/status/{GLOBAL_POD_ID}')
    assert status_response.status_code == 200
    status_data = json.loads(status_response.data)
    assert status_data["query"] == "pytest"
    assert status_data["pod_id"] == GLOBAL_POD_ID
    assert "status" in status_data
    assert "progress" in status_data

def test_02_check_pod_status(client):
    """Test pod status endpoint"""
    status_response = client.get(f'/v1/api/pod/status/{GLOBAL_POD_ID}')
    assert status_response.status_code == 200
    status_data = json.loads(status_response.data)
    assert status_data["pod_id"] == GLOBAL_POD_ID
    assert status_data["query"] == "pytest"
    assert "status" in status_data
    assert "progress" in status_data

def test_03_get_pod_details(client):
    """Test getting full pod details"""
    pod_response = client.get(f'/v1/api/pod/get/{GLOBAL_POD_ID}')
    assert pod_response.status_code == 200
    pod_data = json.loads(pod_response.data)
    assert pod_data["id"] == GLOBAL_POD_ID
    assert pod_data["query"] == "pytest"
    assert "status" in pod_data
    assert "created_at" in pod_data
    assert "updated_at" in pod_data

def test_04_wait_for_consumer_completion(client):
    """Test waiting for pod processing completion"""
    max_retries = 3 * 10 # Wait up to 3 minutes (localhost Kafka is slow)
    retry_count = 0
    
    while retry_count < max_retries:
        status_response = client.get(f'/v1/api/pod/status/{GLOBAL_POD_ID}')
        assert status_response.status_code == 200
        status_data = json.loads(status_response.data)
        
        if status_data["status"] in ["COMPLETED", "ERROR"]:
            break
            
        retry_count += 1
        time.sleep(6)  # Wait 6 seconds between checks
        
    assert retry_count < max_retries, "Pod processing did not complete in time"

def test_05_validate_pod(client):
    """Test the completed pod has all required fields and valid audio URL"""
    response = client.get(f'/v1/api/pod/get/{GLOBAL_POD_ID}')
    assert response.status_code == 200
    data = json.loads(response.data)
    
    # Validate all required fields
    assert data["id"] == GLOBAL_POD_ID
    assert data["query"] == "pytest"
    assert "summary" in data and data["summary"]  # Should have non-empty summary
    assert "transcript" in data and data["transcript"]  # Should have non-empty transcript
    assert "sources_arxiv" in data and isinstance(data["sources_arxiv"], list)
    #assert "sources_ddg" in data and isinstance(data["sources_ddg"], list)
    assert data["status"] == "COMPLETED"
    
    # Validate audio URL
    assert "audio_url" in data and data["audio_url"]
    audio_url = data["audio_url"]
    assert audio_url.startswith("https://")
    assert audio_url.endswith(".mp3")
    assert GLOBAL_POD_ID in audio_url