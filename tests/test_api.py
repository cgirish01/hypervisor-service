import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.models.base import Base, get_db
from src.main import app

# Set testing environment variable
os.environ["TESTING"] = "true"

# Create an in-memory SQLite database for testing
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all tables in the test database
Base.metadata.create_all(bind=engine)


# Override the get_db dependency to use the test database
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

# Create a test client
client = TestClient(app)


# Fixture for creating a test user
@pytest.fixture
def test_user():
    # Register a test user
    user_data = {
        "username": "testuser",
        "email": "test@example.com",
        "password": "password123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    return response.json()


# Fixture for getting an auth token
@pytest.fixture
def auth_token():
    # Login to get an access token
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    return response.json()["access_token"]


# Test root endpoint
def test_read_root():
    response = client.get("/")
    assert response.status_code == 200
    assert "name" in response.json()
    assert "version" in response.json()


# Test user registration
def test_register_user():
    user_data = {
        "username": "newuser",
        "email": "new@example.com",
        "password": "password123"
    }
    response = client.post("/register", json=user_data)
    assert response.status_code == 200
    assert response.json()["username"] == user_data["username"]
    assert response.json()["email"] == user_data["email"]


# Test login (token endpoint)
def test_login(test_user):
    login_data = {
        "username": "testuser",
        "password": "password123"
    }
    response = client.post("/token", data=login_data)
    assert response.status_code == 200
    assert "access_token" in response.json()
    assert "token_type" in response.json()


# Test create organization
def test_create_organization(auth_token):
    org_data = {
        "name": "Test Organization"
    }
    response = client.post(
        "/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == org_data["name"]
    assert "invite_code" in response.json()


# Test create cluster
def test_create_cluster(auth_token):
    # First create an organization to associate with the cluster
    org_data = {
        "name": "Cluster Org"
    }
    org_response = client.post(
        "/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]
    
    # Now create a cluster
    cluster_data = {
        "name": "Test Cluster",
        "total_ram": 16.0,
        "total_cpu": 4.0,
        "total_gpu": 2.0,
        "organization_id": org_id
    }
    response = client.post(
        "/clusters/",
        json=cluster_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == cluster_data["name"]
    assert response.json()["total_ram"] == cluster_data["total_ram"]
    assert response.json()["total_cpu"] == cluster_data["total_cpu"]
    assert response.json()["total_gpu"] == cluster_data["total_gpu"]
    assert response.json()["organization_id"] == cluster_data["organization_id"]


# Test create deployment
def test_create_deployment(auth_token):
    # First create an organization
    org_data = {
        "name": "Deployment Org"
    }
    org_response = client.post(
        "/organizations/",
        json=org_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert org_response.status_code == 200
    org_id = org_response.json()["id"]
    
    # Then create a cluster
    cluster_data = {
        "name": "Deployment Cluster",
        "total_ram": 16.0,
        "total_cpu": 4.0,
        "total_gpu": 2.0,
        "organization_id": org_id
    }
    cluster_response = client.post(
        "/clusters/",
        json=cluster_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert cluster_response.status_code == 200
    cluster_id = cluster_response.json()["id"]
    
    # Now create a deployment
    deployment_data = {
        "name": "Test Deployment",
        "docker_image": "test/image:latest",
        "required_ram": 2.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,  # MEDIUM
        "cluster_id": cluster_id
    }
    response = client.post(
        "/deployments/",
        json=deployment_data,
        headers={"Authorization": f"Bearer {auth_token}"}
    )
    assert response.status_code == 200
    assert response.json()["name"] == deployment_data["name"]
    assert response.json()["docker_image"] == deployment_data["docker_image"]
    assert response.json()["required_ram"] == deployment_data["required_ram"]
    assert response.json()["required_cpu"] == deployment_data["required_cpu"]
    assert response.json()["required_gpu"] == deployment_data["required_gpu"]
    assert response.json()["cluster_id"] == deployment_data["cluster_id"]
    assert response.json()["status"] == "pending" 