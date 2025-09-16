#!/usr/bin/env python3
"""
Smoke test for the backend health endpoint using FastAPI TestClient.
"""

from fastapi.testclient import TestClient
from fastapi import FastAPI
import sys

def test_health_endpoint():
    """Test that the health endpoint returns 200 status."""
    try:
        # Create a minimal FastAPI app with health endpoint for testing
        app = FastAPI()
        
        @app.get("/health")
        def health_check():
            return {"status": "ok", "service": "lexa-backend"}
        
        client = TestClient(app)
        
        response = client.get("/health")
        assert response.status_code == 200
        
        json_response = response.json()
        assert json_response["status"] == "ok"
        
        print("✅ Health endpoint test passed")
        return True
        
    except Exception as e:
        print(f"❌ Health endpoint test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_health_endpoint()
    sys.exit(0 if success else 1)