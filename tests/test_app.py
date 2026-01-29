import pytest
from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Add src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Store original state
    original_activities = {
        "Basketball Team": {
            "description": "Join the school basketball team for training and competitions",
            "schedule": "Mondays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Soccer Club": {
            "description": "Practice soccer skills and play friendly matches",
            "schedule": "Wednesdays, 3:30 PM - 5:30 PM",
            "max_participants": 18,
            "participants": []
        },
        "Art Club": {
            "description": "Explore painting, drawing, and other visual arts",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": []
        },
        "Drama Society": {
            "description": "Participate in acting, stage production, and school plays",
            "schedule": "Fridays, 4:00 PM - 6:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Mathletes": {
            "description": "Compete in math competitions and solve challenging problems",
            "schedule": "Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 10,
            "participants": []
        },
        "Science Club": {
            "description": "Conduct experiments and explore scientific concepts",
            "schedule": "Wednesdays, 4:00 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        },
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": []
        }
    }
    
    # Clear and reset
    activities.clear()
    activities.update(original_activities)
    
    yield
    
    # Reset after test
    activities.clear()
    activities.update(original_activities)


class TestRoot:
    def test_root_redirects_to_static(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert len(data) == 9
        assert "Basketball Team" in data
        assert "Soccer Club" in data

    def test_get_activities_has_correct_structure(self, client, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        activity = data["Basketball Team"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    def test_signup_new_participant(self, client, reset_activities):
        """Test signing up a new participant to an activity"""
        email = "student@mergington.edu"
        activity = "Basketball Team"
        
        response = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities[activity]["participants"]

    def test_signup_nonexistent_activity(self, client, reset_activities):
        """Test signing up for a non-existent activity"""
        response = client.post(
            "/activities/NonExistent/signup?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_participant(self, client, reset_activities):
        """Test that a student cannot sign up twice for the same activity"""
        email = "student@mergington.edu"
        activity = "Basketball Team"
        
        # First signup
        response1 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        assert response1.status_code == 200
        
        # Second signup - should fail
        response2 = client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_multiple_participants(self, client, reset_activities):
        """Test adding multiple participants to the same activity"""
        activity = "Soccer Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all were added
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        assert len(participants) == 3
        for email in emails:
            assert email in participants


class TestUnregister:
    def test_unregister_existing_participant(self, client, reset_activities):
        """Test unregistering a participant from an activity"""
        email = "student@mergington.edu"
        activity = "Basketball Team"
        
        # First, sign up
        client.post(
            f"/activities/{activity}/signup?email={email}"
        )
        
        # Verify they're registered
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Now unregister
        response = client.delete(
            f"/activities/{activity}/unregister?email={email}"
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        
        # Verify they're removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]

    def test_unregister_nonexistent_activity(self, client, reset_activities):
        """Test unregistering from a non-existent activity"""
        response = client.delete(
            "/activities/NonExistent/unregister?email=test@mergington.edu"
        )
        
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_unregister_not_registered_participant(self, client, reset_activities):
        """Test unregistering someone not registered"""
        response = client.delete(
            "/activities/Basketball Team/unregister?email=notregistered@mergington.edu"
        )
        
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_multiple_participants(self, client, reset_activities):
        """Test unregistering multiple participants"""
        activity = "Soccer Club"
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        
        # Sign up all
        for email in emails:
            client.post(
                f"/activities/{activity}/signup?email={email}"
            )
        
        # Unregister the first two
        for email in emails[:2]:
            response = client.delete(
                f"/activities/{activity}/unregister?email={email}"
            )
            assert response.status_code == 200
        
        # Verify only one remains
        activities_response = client.get("/activities")
        participants = activities_response.json()[activity]["participants"]
        assert len(participants) == 1
        assert emails[2] in participants
