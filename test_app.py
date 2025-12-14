"""
Simple test script to verify the application works correctly.
This can be run without pytest to avoid dependency conflicts.
"""
import sys
import os
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

# Add current directory to path
sys.path.insert(0, os.path.dirname(__file__))

from database import Base, get_db
from main import app

# Use in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override database dependency
app.dependency_overrides[get_db] = override_get_db

# Create test client
client = TestClient(app)

def test_root_endpoint():
    """Test the root endpoint."""
    print("Testing root endpoint...")
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    print(f"[OK] Root endpoint works: {data}")

def test_health_check():
    """Test the health check endpoint."""
    print("Testing health check endpoint...")
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    print(f"[OK] Health check works: {data}")

def test_search_pages_empty():
    """Test searching pages when database is empty."""
    print("Testing search pages (empty database)...")
    response = client.get("/api/pages")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] == 0
    print(f"[OK] Search pages works: {data}")

def test_config():
    """Test configuration loading."""
    print("Testing configuration...")
    from config import settings
    assert settings is not None
    assert hasattr(settings, 'database_url')
    assert hasattr(settings, 'host')
    assert hasattr(settings, 'port')
    print(f"[OK] Configuration loaded: host={settings.host}, port={settings.port}")

def run_all_tests():
    """Run all tests."""
    print("=" * 50)
    print("Running Application Tests")
    print("=" * 50)
    
    # Create database tables
    Base.metadata.create_all(bind=engine)
    
    try:
        test_config()
        test_root_endpoint()
        test_health_check()
        test_search_pages_empty()
        
        print("=" * 50)
        print("[OK] All tests passed!")
        print("=" * 50)
        return True
    except Exception as e:
        print("=" * 50)
        print(f"[FAIL] Test failed: {e}")
        print("=" * 50)
        import traceback
        traceback.print_exc()
        return False
    finally:
        Base.metadata.drop_all(bind=engine)
        app.dependency_overrides.clear()

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

