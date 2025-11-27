"""
Tests for the Mergington High School API
"""

import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add the src directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original activities
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Soccer Team": {
            "description": "Join the school soccer team and compete in matches",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
            "max_participants": 22,
            "participants": []
        },
        "Basketball Club": {
            "description": "Practice basketball skills and play friendly games",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Drama Club": {
            "description": "Act, direct, and produce school plays and performances",
            "schedule": "Mondays, 4:00 PM - 5:30 PM",
            "max_participants": 18,
            "participants": []
        },
        "Art Workshop": {
            "description": "Explore painting, drawing, and sculpture techniques",
            "schedule": "Fridays, 2:00 PM - 4:00 PM",
            "max_participants": 16,
            "participants": []
        },
        "Mathletes": {
            "description": "Compete in math competitions and solve challenging problems",
            "schedule": "Thursdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": []
        },
        "Science Club": {
            "description": "Conduct experiments and participate in science fairs",
            "schedule": "Wednesdays, 4:00 PM - 5:30 PM",
            "max_participants": 14,
            "participants": []
        }
    }
    
    # Import activities from app and reset
    from app import activities
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


def test_root_redirect():
    """Test that root path redirects to /static/index.html"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities(reset_activities):
    """Test getting all activities"""
    response = client.get("/activities")
    assert response.status_code == 200
    
    data = response.json()
    assert isinstance(data, dict)
    assert "Chess Club" in data
    assert "Programming Class" in data
    assert data["Chess Club"]["description"] == "Learn strategies and compete in chess tournaments"
    assert len(data["Chess Club"]["participants"]) == 2


def test_signup_success(reset_activities):
    """Test successful signup for an activity"""
    response = client.post("/activities/Soccer%20Team/signup?email=newstudent@mergington.edu")
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "newstudent@mergington.edu" in data["message"]
    
    # Verify participant was added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "newstudent@mergington.edu" in activities_data["Soccer Team"]["participants"]


def test_signup_already_registered(reset_activities):
    """Test signup fails when student is already registered"""
    response = client.post("/activities/Chess%20Club/signup?email=michael@mergington.edu")
    assert response.status_code == 400
    
    data = response.json()
    assert "already signed up" in data["detail"]


def test_signup_activity_full(reset_activities):
    """Test signup fails when activity is full"""
    # First, get an activity with limited spots
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    
    # Create a full activity by adding participants
    from app import activities
    activities["Mathletes"]["participants"] = [
        f"student{i}@mergington.edu" for i in range(10)  # max_participants is 10
    ]
    
    response = client.post("/activities/Mathletes/signup?email=newstudent@mergington.edu")
    assert response.status_code == 400
    
    data = response.json()
    assert "full" in data["detail"]


def test_signup_nonexistent_activity(reset_activities):
    """Test signup fails for non-existent activity"""
    response = client.post("/activities/Nonexistent%20Activity/signup?email=test@mergington.edu")
    assert response.status_code == 404
    
    data = response.json()
    assert "not found" in data["detail"]


def test_unregister_success(reset_activities):
    """Test successful unregister from an activity"""
    response = client.post("/activities/Chess%20Club/unregister?email=michael@mergington.edu")
    assert response.status_code == 200
    
    data = response.json()
    assert "michael@mergington.edu" in data["message"]
    
    # Verify participant was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    assert len(activities_data["Chess Club"]["participants"]) == 1


def test_unregister_not_registered(reset_activities):
    """Test unregister fails when student is not registered"""
    response = client.post("/activities/Soccer%20Team/unregister?email=notregistered@mergington.edu")
    assert response.status_code == 400
    
    data = response.json()
    assert "not registered" in data["detail"]


def test_unregister_nonexistent_activity(reset_activities):
    """Test unregister fails for non-existent activity"""
    response = client.post("/activities/Nonexistent%20Activity/unregister?email=test@mergington.edu")
    assert response.status_code == 404
    
    data = response.json()
    assert "not found" in data["detail"]


def test_multiple_signups_and_unregisters(reset_activities):
    """Test multiple signup and unregister operations"""
    # Sign up multiple students
    for i in range(3):
        email = f"student{i}@mergington.edu"
        response = client.post(f"/activities/Basketball%20Club/signup?email={email}")
        assert response.status_code == 200
    
    # Verify all were added
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert len(activities_data["Basketball Club"]["participants"]) == 3
    
    # Unregister one
    response = client.post("/activities/Basketball%20Club/unregister?email=student0@mergington.edu")
    assert response.status_code == 200
    
    # Verify it was removed
    activities_response = client.get("/activities")
    activities_data = activities_response.json()
    assert len(activities_data["Basketball Club"]["participants"]) == 2
    assert "student0@mergington.edu" not in activities_data["Basketball Club"]["participants"]
