from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, active_tokens, app


@pytest.fixture(autouse=True)
def reset_state():
    original_activities = deepcopy(activities)
    active_tokens.clear()
    yield
    activities.clear()
    activities.update(original_activities)
    active_tokens.clear()


client = TestClient(app)


def test_unauthenticated_user_cannot_signup():
    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "unauth@mergington.edu"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_student_role_cannot_modify_registrations():
    login = client.post(
        "/auth/login",
        json={"username": "student.viewer", "password": "changeme-student"},
    )
    token = login.json()["access_token"]

    response = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "student.blocked@mergington.edu"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 403
    assert response.json()["detail"] == "Insufficient permissions"


def test_teacher_role_can_signup_and_unregister():
    login = client.post(
        "/auth/login",
        json={"username": "teacher.alex", "password": "changeme-teacher"},
    )
    token = login.json()["access_token"]

    signup = client.post(
        "/activities/Chess%20Club/signup",
        params={"email": "student.allowed@mergington.edu"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert signup.status_code == 200

    unregister = client.delete(
        "/activities/Chess%20Club/unregister",
        params={"email": "student.allowed@mergington.edu"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert unregister.status_code == 200


def test_invalid_credentials_rejected():
    response = client.post(
        "/auth/login",
        json={"username": "teacher.alex", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Invalid username or password"
