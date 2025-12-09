import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI application"""
    return TestClient(app)


class TestActivities:
    """Test cases for activities endpoints"""

    def test_get_activities(self, client):
        """Test retrieving all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        activities = response.json()
        assert isinstance(activities, dict)
        assert len(activities) > 0
        
        # Verify structure of an activity
        chess_club = activities.get("Chess Club")
        assert chess_club is not None
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        assert isinstance(chess_club["participants"], list)

    def test_get_activities_contains_expected_activities(self, client):
        """Test that expected activities are present"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club",
            "Programming Class",
            "Gym Class",
            "Basketball Team",
            "Soccer Team",
            "Art Club",
            "Music Ensemble",
            "Science Club",
            "Debate Team"
        ]
        
        for activity in expected_activities:
            assert activity in activities


class TestSignup:
    """Test cases for signup endpoint"""

    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        # Use an email not in the initial participants list
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Signed up newstudent@mergington.edu for Chess Club"

    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/NonExistent%20Activity/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_signup_duplicate_student(self, client):
        """Test signup fails when student already registered"""
        # First signup
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent2@mergington.edu"
        )
        
        # Try to signup again with same email
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent2@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_activity_full(self, client):
        """Test signup fails when activity is at max capacity"""
        # Get the activity to check max participants
        response = client.get("/activities")
        activities = response.json()
        
        # Find an activity and fill it up
        for activity_name, activity_data in activities.items():
            if activity_data["max_participants"] <= 2:
                # Fill up the activity with test participants
                max_participants = activity_data["max_participants"]
                current_participants = len(activity_data["participants"])
                
                # Add participants until full
                for i in range(max_participants - current_participants):
                    client.post(
                        f"/activities/{activity_name.replace(' ', '%20')}/signup?email=filler{i}@mergington.edu"
                    )
                
                # Now try to add one more (should fail)
                response = client.post(
                    f"/activities/{activity_name.replace(' ', '%20')}/signup?email=overflow@mergington.edu"
                )
                assert response.status_code == 400
                assert "full" in response.json()["detail"]
                break

    def test_signup_updates_participant_count(self, client):
        """Test that signup updates the participant count"""
        # Get initial count
        response = client.get("/activities")
        initial_count = len(response.json()["Chess Club"]["participants"])
        
        # Sign up new participant
        client.post(
            "/activities/Chess%20Club/signup?email=counting@mergington.edu"
        )
        
        # Check updated count
        response = client.get("/activities")
        new_count = len(response.json()["Chess Club"]["participants"])
        
        assert new_count == initial_count + 1
        assert "counting@mergington.edu" in response.json()["Chess Club"]["participants"]


class TestUnregister:
    """Test cases for unregister endpoint"""

    def test_unregister_successful(self, client):
        """Test successful unregistration from an activity"""
        # First sign up
        client.post(
            "/activities/Programming%20Class/signup?email=tempstudent@mergington.edu"
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Programming%20Class/unregister?email=tempstudent@mergington.edu"
        )
        assert response.status_code == 200
        assert "Unregistered tempstudent@mergington.edu" in response.json()["message"]

    def test_unregister_activity_not_found(self, client):
        """Test unregister fails for non-existent activity"""
        response = client.delete(
            "/activities/NonExistent%20Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_unregister_student_not_registered(self, client):
        """Test unregister fails when student is not registered"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"]

    def test_unregister_removes_participant(self, client):
        """Test that unregister removes participant from list"""
        test_email = "removeme@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/Art%20Club/signup?email={test_email}"
        )
        
        # Verify signed up
        response = client.get("/activities")
        assert test_email in response.json()["Art Club"]["participants"]
        
        # Unregister
        client.delete(
            f"/activities/Art%20Club/unregister?email={test_email}"
        )
        
        # Verify removed
        response = client.get("/activities")
        assert test_email not in response.json()["Art Club"]["participants"]

    def test_unregister_updates_participant_count(self, client):
        """Test that unregister updates the participant count"""
        test_email = "countme@mergington.edu"
        
        # Sign up
        client.post(
            f"/activities/Gym%20Class/signup?email={test_email}"
        )
        
        # Get count after signup
        response = client.get("/activities")
        count_after_signup = len(response.json()["Gym Class"]["participants"])
        
        # Unregister
        client.delete(
            f"/activities/Gym%20Class/unregister?email={test_email}"
        )
        
        # Check count after unregister
        response = client.get("/activities")
        count_after_unregister = len(response.json()["Gym Class"]["participants"])
        
        assert count_after_unregister == count_after_signup - 1


class TestRoot:
    """Test cases for root endpoint"""

    def test_root_redirect(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
