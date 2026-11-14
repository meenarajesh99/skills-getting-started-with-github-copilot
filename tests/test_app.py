from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client():
    original_activities = deepcopy(activities)
    try:
        with TestClient(app) as test_client:
            yield test_client
    finally:
        activities.clear()
        activities.update(original_activities)


def test_root_redirects_to_activity_page(client):
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_data(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_adds_participant(client):
    email = "test-student@mergington.edu"

    response = client.post(
        "/activities/Basketball Club/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for Basketball Club"
    }
    assert email in client.get("/activities").json()["Basketball Club"]["participants"]


def test_signup_rejects_duplicate_participant(client):
    email = "test-student@mergington.edu"
    signup_url = "/activities/Basketball Club/signup"

    assert client.post(signup_url, params={"email": email}).status_code == 200
    response = client.post(signup_url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    participants = client.get("/activities").json()["Basketball Club"]["participants"]
    assert participants.count(email) == 1


def test_signup_rejects_unknown_activity(client):
    response = client.post(
        "/activities/Unknown Club/signup",
        params={"email": "test-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
