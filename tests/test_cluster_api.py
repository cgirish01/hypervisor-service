import pytest
import requests
import time

API_URL = "http://localhost:8000"

def unique_username():
    return f"testuser_{int(time.time() * 1000)}"

def unique_email():
    return f"test_{int(time.time() * 1000)}@example.com"

def unique_org_name():
    return f"TestOrg_{int(time.time() * 1000)}"

def unique_cluster_name():
    return f"TestCluster_{int(time.time() * 1000)}"

@pytest.fixture
def test_user():
    return {
        "username": unique_username(),
        "email": unique_email(),
        "password": "testpassword123"
    }

@pytest.fixture
def register_user(test_user):
    response = requests.post(f"{API_URL}/register", json=test_user)
    assert response.status_code == 200, response.text
    user = response.json()
    yield test_user

@pytest.fixture
def auth_token(test_user, register_user):
    data = {"username": test_user["username"], "password": test_user["password"]}
    response = requests.post(f"{API_URL}/token", data=data)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    return token

@pytest.fixture
def test_org(auth_token):
    org_name = unique_org_name()
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{API_URL}/organizations/", json={"name": org_name}, headers=headers)
    assert response.status_code == 200, response.text
    org = response.json()
    yield org
    # Delete organization after test
    del_resp = requests.delete(f"{API_URL}/organizations/{org['id']}", headers=headers)
    assert del_resp.status_code == 200

@pytest.fixture
def test_cluster(auth_token, test_org):
    cluster_data = {
        "name": unique_cluster_name(),
        "total_ram": 8.0,
        "total_cpu": 4.0,
        "total_gpu": 1.0,
        "organization_id": test_org["id"]
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{API_URL}/clusters/", json=cluster_data, headers=headers)
    assert response.status_code == 200, response.text
    cluster = response.json()
    yield cluster
    # Delete cluster after test
    del_resp = requests.delete(f"{API_URL}/clusters/{cluster['id']}", headers=headers)
    assert del_resp.status_code == 200

def test_create_cluster(auth_token, test_org):
    cluster_data = {
        "name": unique_cluster_name(),
        "total_ram": 8.0,
        "total_cpu": 4.0,
        "total_gpu": 1.0,
        "organization_id": test_org["id"]
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{API_URL}/clusters/", json=cluster_data, headers=headers)
    assert response.status_code == 200, response.text
    cluster = response.json()
    # Cleanup
    del_resp = requests.delete(f"{API_URL}/clusters/{cluster['id']}", headers=headers)
    assert del_resp.status_code == 200

def test_get_cluster(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_URL}/clusters/{test_cluster['id']}", headers=headers)
    assert response.status_code == 200, response.text
    cluster = response.json()
    assert cluster["id"] == test_cluster["id"]

def test_update_cluster(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    update_data = {"name": test_cluster["name"] + "_updated"}
    response = requests.put(f"{API_URL}/clusters/{test_cluster['id']}", json=update_data, headers=headers)
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["name"].endswith("_updated")

def test_list_clusters(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_URL}/clusters/", headers=headers)
    assert response.status_code == 200, response.text
    clusters = response.json()
    assert any(c["id"] == test_cluster["id"] for c in clusters)

def test_delete_cluster(auth_token, test_org):
    # Create a cluster to delete
    cluster_data = {
        "name": unique_cluster_name(),
        "total_ram": 8.0,
        "total_cpu": 4.0,
        "total_gpu": 1.0,
        "organization_id": test_org["id"]
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{API_URL}/clusters/", json=cluster_data, headers=headers)
    assert response.status_code == 200, response.text
    cluster = response.json()
    # Now delete
    del_resp = requests.delete(f"{API_URL}/clusters/{cluster['id']}", headers=headers)
    assert del_resp.status_code == 200 