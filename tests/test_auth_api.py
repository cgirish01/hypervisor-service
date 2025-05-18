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
    # No API to delete user, so just leave it (or implement if available)

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


def test_register_and_login(test_user):
    # Register
    response = requests.post(f"{API_URL}/register", json=test_user)
    assert response.status_code == 200, response.text
    # Login
    data = {"username": test_user["username"], "password": test_user["password"]}
    response = requests.post(f"{API_URL}/token", data=data)
    assert response.status_code == 200, response.text
    token = response.json()["access_token"]
    assert token


def test_join_organization(auth_token, test_org):
    # Create a new user to join the org
    join_user = {
        "username": unique_username(),
        "email": unique_email(),
        "password": "testpassword123"
    }
    reg_resp = requests.post(f"{API_URL}/register", json=join_user)
    assert reg_resp.status_code == 200, reg_resp.text
    # Login as new user
    data = {"username": join_user["username"], "password": join_user["password"]}
    login_resp = requests.post(f"{API_URL}/token", data=data)
    assert login_resp.status_code == 200, login_resp.text
    join_token = login_resp.json()["access_token"]
    # Join organization
    headers = {"Authorization": f"Bearer {join_token}"}
    join_resp = requests.post(f"{API_URL}/join-organization", json={"invite_code": test_org["invite_code"]}, headers=headers)
    assert join_resp.status_code == 200, join_resp.text
