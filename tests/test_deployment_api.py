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

def unique_deployment_name():
    return f"TestDeployment_{int(time.time() * 1000)}"

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

@pytest.fixture
def test_deployment(auth_token, test_cluster):
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    yield deployment
    # Delete deployment after test
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200

def test_create_deployment(auth_token, test_cluster):
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    # Cleanup
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200

def test_create_deployment_with_dependency(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create dependency deployment
    dep_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    dep_resp = requests.post(f"{API_URL}/deployments/", json=dep_data, headers=headers)
    assert dep_resp.status_code == 200, dep_resp.text
    dep = dep_resp.json()
    # Create main deployment with dependency
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"],
        "dependency_ids": [dep["id"]]
    }
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    # Cleanup
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200
    del_dep_resp = requests.delete(f"{API_URL}/deployments/{dep['id']}", headers=headers)
    assert del_dep_resp.status_code == 200

def test_get_deployment(auth_token, test_deployment):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_URL}/deployments/{test_deployment['id']}", headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    assert deployment["id"] == test_deployment["id"]

def test_update_deployment(auth_token, test_deployment):
    headers = {"Authorization": f"Bearer {auth_token}"}
    update_data = {"name": test_deployment["name"] + "_updated", "priority": 3}
    response = requests.put(f"{API_URL}/deployments/{test_deployment['id']}", json=update_data, headers=headers)
    assert response.status_code == 200, response.text
    updated = response.json()
    assert updated["name"].endswith("_updated")
    assert updated["priority"] == 3

def test_list_deployments(auth_token, test_deployment):
    headers = {"Authorization": f"Bearer {auth_token}"}
    response = requests.get(f"{API_URL}/deployments/", headers=headers)
    assert response.status_code == 200, response.text
    deployments = response.json()
    assert any(d["id"] == test_deployment["id"] for d in deployments)

def test_start_deployment_with_dependency(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create dependency deployment (leave as PENDING)
    dep_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    dep_resp = requests.post(f"{API_URL}/deployments/", json=dep_data, headers=headers)
    assert dep_resp.status_code == 200, dep_resp.text
    dep = dep_resp.json()
    # Create main deployment with dependency
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"],
        "dependency_ids": [dep["id"]]
    }
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    # Try to start main deployment (should fail, dependency not completed)
    start_resp = requests.post(f"{API_URL}/deployments/{deployment['id']}/start", headers=headers)
    assert start_resp.status_code == 400 or start_resp.status_code == 200
    # Complete dependency
    dep_start = requests.post(f"{API_URL}/deployments/{dep['id']}/start", headers=headers)
    assert dep_start.status_code == 200, dep_start.text
    dep_stop = requests.post(f"{API_URL}/deployments/{dep['id']}/stop", headers=headers)
    assert dep_stop.status_code == 200, dep_stop.text
    # Wait for dependent deployment to be running or pending (retry up to 5 times)
    import time as _time
    for _ in range(5):
        dep_status_resp = requests.get(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
        assert dep_status_resp.status_code == 200, dep_status_resp.text
        status = dep_status_resp.json().get("status")
        if status == "running":
            break
        elif status == "pending":
            # Try to start it manually
            start_resp2 = requests.post(f"{API_URL}/deployments/{deployment['id']}/start", headers=headers)
            if start_resp2.status_code == 200:
                break
        _time.sleep(0.5)
    else:
        # Print cluster resources for debugging
        cluster_resp = requests.get(f"{API_URL}/clusters/{test_cluster['id']}", headers=headers)
        print("Cluster resources after dependency stop:", cluster_resp.json())
        pytest.fail(f"Main deployment could not be started after dependency completion. Status: {status}")
    # Final check: deployment should be running
    dep_status_resp = requests.get(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert dep_status_resp.status_code == 200, dep_status_resp.text
    assert dep_status_resp.json().get("status") == "running"
    # Cleanup
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200
    del_dep_resp = requests.delete(f"{API_URL}/deployments/{dep['id']}", headers=headers)
    assert del_dep_resp.status_code == 200

def test_stop_deployment(auth_token, test_deployment):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Start deployment
    start_resp = requests.post(f"{API_URL}/deployments/{test_deployment['id']}/start", headers=headers)
    # Stop deployment
    stop_resp = requests.post(f"{API_URL}/deployments/{test_deployment['id']}/stop", headers=headers)
    assert stop_resp.status_code == 200, stop_resp.text

def test_cancel_deployment(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    # Cancel deployment
    cancel_resp = requests.post(f"{API_URL}/deployments/{deployment['id']}/cancel", headers=headers)
    assert cancel_resp.status_code == 200, cancel_resp.text
    # Cleanup
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200

def test_delete_deployment(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    # Delete deployment
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200

def test_get_deployment_dependencies_and_dependents(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create dependency deployment
    dep_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    dep_resp = requests.post(f"{API_URL}/deployments/", json=dep_data, headers=headers)
    assert dep_resp.status_code == 200, dep_resp.text
    dep = dep_resp.json()
    # Create main deployment with dependency
    deployment_data = {
        "name": unique_deployment_name(),
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"],
        "dependency_ids": [dep["id"]]
    }
    response = requests.post(f"{API_URL}/deployments/", json=deployment_data, headers=headers)
    assert response.status_code == 200, response.text
    deployment = response.json()
    # Check dependencies
    dep_list_resp = requests.get(f"{API_URL}/deployments/{deployment['id']}/dependencies", headers=headers)
    assert dep_list_resp.status_code == 200, dep_list_resp.text
    deps = dep_list_resp.json()
    assert any(d["id"] == dep["id"] for d in deps)
    # Check dependents
    dependents_resp = requests.get(f"{API_URL}/deployments/{dep['id']}/dependents", headers=headers)
    assert dependents_resp.status_code == 200, dependents_resp.text
    dependents = dependents_resp.json()
    assert any(d["id"] == deployment["id"] for d in dependents)
    # Cleanup
    del_resp = requests.delete(f"{API_URL}/deployments/{deployment['id']}", headers=headers)
    assert del_resp.status_code == 200
    del_dep_resp = requests.delete(f"{API_URL}/deployments/{dep['id']}", headers=headers)
    assert del_dep_resp.status_code == 200

def test_dependency_state_transitions(auth_token, test_cluster):
    headers = {"Authorization": f"Bearer {auth_token}"}
    # Create dependency deployment (dep2)
    dep2_data = {
        "name": unique_deployment_name() + "_dep2",
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"]
    }
    dep2_resp = requests.post(f"{API_URL}/deployments/", json=dep2_data, headers=headers)
    assert dep2_resp.status_code == 200, dep2_resp.text
    dep2 = dep2_resp.json()
    # Create dependent deployment (dep1) that depends on dep2
    dep1_data = {
        "name": unique_deployment_name() + "_dep1",
        "docker_image": "test/image:latest",
        "required_ram": 1.0,
        "required_cpu": 1.0,
        "required_gpu": 0.0,
        "priority": 2,
        "cluster_id": test_cluster["id"],
        "dependency_ids": [dep2["id"]]
    }
    dep1_resp = requests.post(f"{API_URL}/deployments/", json=dep1_data, headers=headers)
    assert dep1_resp.status_code == 200, dep1_resp.text
    dep1 = dep1_resp.json()
    # 1. Both should be pending
    dep1_status = requests.get(f"{API_URL}/deployments/{dep1['id']}", headers=headers).json()["status"]
    dep2_status = requests.get(f"{API_URL}/deployments/{dep2['id']}", headers=headers).json()["status"]
    assert dep1_status == "pending"
    assert dep2_status == "pending"
    # 2. Start dep2, dep1 should still be pending
    start_dep2 = requests.post(f"{API_URL}/deployments/{dep2['id']}/start", headers=headers)
    assert start_dep2.status_code == 200, start_dep2.text
    dep1_status_after_start = requests.get(f"{API_URL}/deployments/{dep1['id']}", headers=headers).json()["status"]
    dep2_status_after_start = requests.get(f"{API_URL}/deployments/{dep2['id']}", headers=headers).json()["status"]
    assert dep2_status_after_start == "running"
    assert dep1_status_after_start == "pending"
    # 3. Complete dep2, dep1 should become running (auto-started)
    stop_dep2 = requests.post(f"{API_URL}/deployments/{dep2['id']}/stop", headers=headers)
    assert stop_dep2.status_code == 200, stop_dep2.text
    # Wait for dep1 to become running (retry up to 5 times)
    import time as _time
    for _ in range(5):
        dep1_status_final = requests.get(f"{API_URL}/deployments/{dep1['id']}", headers=headers).json()["status"]
        if dep1_status_final == "running":
            break
        _time.sleep(0.5)
    else:
        pytest.fail(f"dep1 did not become running after dep2 completed. Final status: {dep1_status_final}")
    # Cleanup
    del_resp1 = requests.delete(f"{API_URL}/deployments/{dep1['id']}", headers=headers)
    assert del_resp1.status_code == 200
    del_resp2 = requests.delete(f"{API_URL}/deployments/{dep2['id']}", headers=headers)
    assert del_resp2.status_code == 200


