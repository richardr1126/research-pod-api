import os
import sys
import pytest

# Add the parent directory to PYTHONPATH
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from server import server
from db import db

@pytest.fixture
def client():
    """Create a test client for the server."""
    # Set up the test database
    server.config['TESTING'] = True
    return server.test_client()

@pytest.fixture
def runner():
    """Create a test CLI runner for the server."""
    return server.test_cli_runner()
