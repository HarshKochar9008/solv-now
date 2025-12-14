import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from models import Page, Post, Employee

def test_root_endpoint(client: TestClient):
    """Test the root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "version" in data
    assert data["version"] == "1.0.0"

def test_health_check(client: TestClient):
    """Test the health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"

def test_search_pages_empty(client: TestClient):
    """Test searching pages when database is empty."""
    response = client.get("/api/pages")
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert "page" in data
    assert "page_size" in data
    assert "total_pages" in data
    assert data["total"] == 0
    assert len(data["items"]) == 0

def test_search_pages_with_filters(client: TestClient, db_session: Session):
    """Test searching pages with filters."""
    # Create a test page
    test_page = Page(
        page_id="test-company",
        name="Test Company",
        url="https://www.linkedin.com/company/test-company/",
        total_followers=50000,
        industry="Technology"
    )
    db_session.add(test_page)
    db_session.commit()
    
    # Test filter by min_followers
    response = client.get("/api/pages?min_followers=40000")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    
    # Test filter by max_followers
    response = client.get("/api/pages?max_followers=10000")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 0
    
    # Test name search
    response = client.get("/api/pages?name_search=Test")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    
    # Test industry filter
    response = client.get("/api/pages?industry=Technology")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1

def test_get_page_not_found(client: TestClient):
    """Test getting a page that doesn't exist."""
    # This will try to scrape, which may fail, but should return 500 or handle gracefully
    response = client.get("/api/pages/nonexistent-page")
    # The endpoint will try to scrape, so we expect either 404 or 500
    assert response.status_code in [404, 500]

def test_get_page_employees_not_found(client: TestClient):
    """Test getting employees for a non-existent page."""
    response = client.get("/api/pages/nonexistent-page/employees")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_page_posts_not_found(client: TestClient):
    """Test getting posts for a non-existent page."""
    response = client.get("/api/pages/nonexistent-page/posts")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()

def test_get_page_employees_with_data(client: TestClient, db_session: Session):
    """Test getting employees for a page with data."""
    # Create a test page
    test_page = Page(
        page_id="test-company",
        name="Test Company",
        url="https://www.linkedin.com/company/test-company/",
        total_followers=50000
    )
    db_session.add(test_page)
    db_session.flush()
    
    # Create test employees
    employee1 = Employee(
        page_id=test_page.id,
        name="John Doe",
        headline="Software Engineer",
        position="Software Engineer"
    )
    employee2 = Employee(
        page_id=test_page.id,
        name="Jane Smith",
        headline="Product Manager",
        position="Product Manager"
    )
    db_session.add(employee1)
    db_session.add(employee2)
    db_session.commit()
    
    response = client.get("/api/pages/test-company/employees")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 2
    assert len(data["items"]) == 2

def test_get_page_posts_with_data(client: TestClient, db_session: Session):
    """Test getting posts for a page with data."""
    # Create a test page
    test_page = Page(
        page_id="test-company",
        name="Test Company",
        url="https://www.linkedin.com/company/test-company/",
        total_followers=50000
    )
    db_session.add(test_page)
    db_session.flush()
    
    # Create test posts
    post1 = Post(
        page_id=test_page.id,
        linkedin_post_id="post-1",
        content="Test post 1",
        likes_count=10
    )
    post2 = Post(
        page_id=test_page.id,
        linkedin_post_id="post-2",
        content="Test post 2",
        likes_count=20
    )
    db_session.add(post1)
    db_session.add(post2)
    db_session.commit()
    
    response = client.get("/api/pages/test-company/posts?limit=10")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2

def test_pagination(client: TestClient, db_session: Session):
    """Test pagination functionality."""
    # Create multiple test pages
    for i in range(15):
        test_page = Page(
            page_id=f"test-company-{i}",
            name=f"Test Company {i}",
            url=f"https://www.linkedin.com/company/test-company-{i}/",
            total_followers=10000 + i * 1000
        )
        db_session.add(test_page)
    db_session.commit()
    
    # Test first page
    response = client.get("/api/pages?page=1&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 1
    assert data["page_size"] == 10
    assert data["total"] == 15
    assert data["total_pages"] == 2
    assert len(data["items"]) == 10
    
    # Test second page
    response = client.get("/api/pages?page=2&page_size=10")
    assert response.status_code == 200
    data = response.json()
    assert data["page"] == 2
    assert len(data["items"]) == 5

def test_page_size_validation(client: TestClient):
    """Test page size validation."""
    # Test max page size
    response = client.get("/api/pages?page_size=100")
    assert response.status_code == 200
    
    # Test exceeding max page size
    response = client.get("/api/pages?page_size=101")
    assert response.status_code == 422  # Validation error
    
    # Test invalid page size
    response = client.get("/api/pages?page_size=0")
    assert response.status_code == 422  # Validation error

def test_page_number_validation(client: TestClient):
    """Test page number validation."""
    # Test valid page number
    response = client.get("/api/pages?page=1")
    assert response.status_code == 200
    
    # Test invalid page number
    response = client.get("/api/pages?page=0")
    assert response.status_code == 422  # Validation error
    
    # Test negative page number
    response = client.get("/api/pages?page=-1")
    assert response.status_code == 422  # Validation error

