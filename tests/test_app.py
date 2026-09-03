import copy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


@pytest.fixture
def client():
    original_activities = copy.deepcopy(app_module.activities)
    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_activities))

    with TestClient(app_module.app) as test_client:
        yield test_client

    app_module.activities.clear()
    app_module.activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_all_activities(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert "Programming Class" in payload
    assert "Gym Class" in payload
    assert "participants" in payload["Chess Club"]


def test_signup_for_activity_success(client):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["message"] == f"Signed up {email} for {activity_name}"
    assert email in client.get("/activities").json()[activity_name]["participants"]


def test_signup_rejects_duplicate_email(client):
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    first_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    second_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )

    assert first_response.status_code == 400
    assert second_response.status_code == 400
    assert "already signed up" in second_response.json()["detail"].lower()


def test_signup_invalid_activity_returns_404(client):
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_removes_email_from_activity(client):
    activity_name = "Chess Club"
    email = "newstudent@mergington.edu"

    signup_response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email},
    )
    assert signup_response.status_code == 200

    delete_response = client.delete(
        f"/activities/{activity_name}/participants/{email}"
    )

    assert delete_response.status_code == 200
    assert delete_response.json()["message"] == f"Unregistered {email} from {activity_name}"

    activities = client.get("/activities").json()
    assert email not in activities[activity_name]["participants"]


def test_unregister_missing_participant_returns_404(client):
    response = client.delete(
        "/activities/Chess Club/participants/notregistered@mergington.edu"
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found in this activity"
