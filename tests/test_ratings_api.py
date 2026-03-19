import pytest
import uuid
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


# Helpers and Fixtures
def register_and_login(client, role):
    """Helper: register a fresh user and return (token, user_id)"""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    password = "testpass123"

    reg_data = {
        "full_name": f"Test {role.capitalize()}",
        "contact": "0700000000",
        "email": unique_email,
        "password": password,
        "role": role
    }
    if role == 'TRANSPORTER':
        reg_data.update({
            "vehicle_type": "Truck",
            "vehicle_capacity": 5000,
            "license_number": f"LIC{uuid.uuid4().hex[:6].upper()}",
            "organization_name": "Test Transport Co"
        })
    elif role == 'FARMER':
        reg_data["farm_location"] = "Test Farm"

    register_resp = client.post('/api/auth/register', json=reg_data)

    assert register_resp.status_code == 201

    login_resp = client.post('/api/auth/login', json={
        "email": unique_email,
        "password": password,
        "role": role
    })

    assert login_resp.status_code == 200
    data = login_resp.get_json()
    return data['token'], data['user']['user_id']

#farmer fixture
@pytest.fixture
def farmer(client):
    """Registers and logs in a farmer, returns (token, user_id)"""
    return register_and_login(client, 'FARMER')

#transporter fixture
@pytest.fixture
def transporter(client):
    """Registers and logs in a transporter, returns (token, user_id)"""
    return register_and_login(client, 'TRANSPORTER')

#Create a pending request
@pytest.fixture
def pending_request_id(client, farmer):
    """Creates a farmer transport request and returns its request_id."""
    farmer_token, _ = farmer

    response = client.post(
        '/api/requests',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "pickup_location": "Musanze",
            "destination_location": "Market B",
            "pickup_date": "2026-04-05",
            "animal_type": "Cattle",
            "animal_quantity": 15
        }
    )

    assert response.status_code == 201
    data = response.get_json()
    request_id = data['request_id']
    return request_id

#active booking fixture
@pytest.fixture
def active_booking(client, transporter, pending_request_id):
    """Creates a booking that exists but is not yet delivered."""
    transporter_token, _ = transporter

    response = client.post(
        '/api/bookings',
        headers={"Authorization": f"Bearer {transporter_token}"},
        json={"request_id": pending_request_id}
    )

    assert response.status_code == 201
    data = response.get_json()
    return data['booking_id']

#completed_booking fixture
@pytest.fixture
def completed_booking(client, transporter, pending_request_id):
    """Creates a completed booking and returns its booking_id."""
    transporter_token, _ = transporter
    create_response = client.post(
        '/api/bookings',
        headers={"Authorization": f"Bearer {transporter_token}"},
        json={"request_id": pending_request_id}
    )

    assert create_response.status_code == 201
    create_data = create_response.get_json()
    booking_id = create_data['booking_id']

    update_response = client.put(
        f'/api/bookings/{booking_id}',
        headers={"Authorization": f"Bearer {transporter_token}"},
        json={"status": "DELIVERED"}
    )

    assert update_response.status_code == 200
    return booking_id

@pytest.fixture
def created_rating(client, farmer, transporter, completed_booking):
    """Creates a rating and returns its rating_id."""
    farmer_token, farmer_id = farmer
    _, transporter_id = transporter
    booking_id = completed_booking

    response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "booking_id": booking_id,
            "score": 5,
            "comment": "Great service"
        }
    )

    assert response.status_code == 201
    data = response.get_json()

    return data["rating_id"], farmer_id, transporter_id


# POST ENDPOINT TESTS
#Test 1: Creating a rating successfully
def test_create_rating_success(client, farmer, completed_booking):
    """Test that a farmer can successfully rate a completed booking."""

    farmer_token, _ = farmer
    booking_id = completed_booking

    response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "booking_id": booking_id,
            "score": 5,
            "comment": "Great service"
        }
    )

    data = response.get_json()

    assert response.status_code == 201
    assert "rating_id" in data
    assert data["message"] == "Rating created"

#Test 2: Create rating with missing booking_id
def test_create_rating_missing_booking_id(client, farmer):
    """Test that rating creation fails if the booking_id is missing."""
    farmer_token, _ = farmer

    response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "score": 5,
            "comment": "Great service"
        }
    )

    data = response.get_json()

    assert response.status_code == 400
    assert "error" in data
    assert "booking_id" in data["error"].lower()

#Test 3:Creating a rating with a missing score
def test_create_rating_missing_score(client, farmer, completed_booking):
    """Test that rating creation fails if score is missing."""
    farmer_token, _ = farmer
    booking_id = completed_booking

    response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "booking_id": booking_id,
            "comment": "Great service"
        }
    )

    data = response.get_json()

    assert response.status_code == 400
    assert "error" in data
    assert "score" in data["error"].lower()

#Test 4: Creating a rating before trip is completed
def test_create_rating_before_trip_completed(farmer, active_booking, client):
    """Test that rating is rejected if the booking is not yet completed/delivered."""
    farmer_token, _ = farmer
    booking_id = active_booking

    response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "booking_id": booking_id,
            "score": 3,
            "comment": "Great service"
        }
    )

    data = response.get_json()

    assert response.status_code == 403
    assert "error" in data
    assert "delivered" in data["error"].lower()

#Test 5: Rating a booking more than once
def test_create_duplicate_rating_for_same_booking(client, farmer, completed_booking):
    """Test that the same booking cannot be rated twice."""
    farmer_token, _ = farmer
    booking_id = completed_booking

    #First rating
    first_response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "booking_id": booking_id,
            "score": 5,
            "comment": "Great service"
        }
    )

    assert first_response.status_code == 201

    #Second rating for the sam booking
    second_response = client.post(
        '/api/ratings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "booking_id": booking_id,
            "score": 3,
            "comment": "Average service"
        }
    )

    data = second_response.get_json()
    assert second_response.status_code == 400
    assert "already rated" in data["error"].lower()

#Test 6: Creating a rating without authorization
def test_create_rating_unauthorized(client):
    """Test that creating a rating without login/token fails."""

    response = client.post(
        '/api/ratings',
        headers={"Content-Type": "application/json"},
        json={
            "booking_id": str(uuid.uuid4()),
            "score": 5,
            "comment": "Great service"
        }
    )

    data = response.get_json()

    assert response.status_code == 401
    assert "error" in data


# GET ENDPOINT TESTS

#Test 1: Transporter Accessing all their ratings
def test_get_transporter_ratings_success(client, created_rating):
    """Retrieving all ratings for a transporter."""

    _, _, transporter_id = created_rating

    response = client.get(f'/api/ratings/transporter/{transporter_id}')
    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)

    if len(data) > 0:
        rating = data[0]
        assert "rating_id" in rating
        assert "booking_id" in rating
        assert "rating_by" in rating
        assert "score" in rating
        assert "comment" in rating

#Test 2: Farmer accessing their ratings on their own dashboard
def test_get_farmer_ratings_success(client, farmer, created_rating):
    """Retrieving all ratings made by farmer."""

    farmer_token, farmer_id = farmer

    response = client.get(
        f'/api/ratings/farmer/{farmer_id}',
        headers={"Authorization": f"Bearer {farmer_token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert isinstance(data, list)

    if len(data) > 0:
        rating = data[0]
        assert "rating_id" in rating
        assert "booking_id" in rating
        assert "rating_for" in rating
        assert "score" in rating
        assert "comment" in rating

#Test 3: Farmer accessing another farmer's ratings
def test_get_farmer_ratings_unauthorized(client, farmer):
    """Test that farmer cannot access another farmer's ratings."""

    # First farmer (Farmer 1)
    farmer_token_1, farmer_id_1 = farmer

    # Create a second farmer (Farmer 2)
    farmer_token_2, farmer_id_2 = register_and_login(client, 'FARMER')

    # Farmer B tries to access Farmer A's ratings
    response = client.get(
        f'/api/ratings/farmer/{farmer_id_1}',
        headers={"Authorization": f"Bearer {farmer_token_2}"}
    )

    data = response.get_json()

    assert response.status_code == 403
    assert "error" in data
    assert "unauthorized" in data["error"].lower()

# PUT ENDPOINT TESTS
#Test 1: Updating a rating
def test_update_rating_success(client, farmer, created_rating):
    """Test that a farmer can successfully update their own rating."""

    farmer_token, _ = farmer
    rating_id, _, _ = created_rating

    response = client.put(
        f'/api/ratings/{rating_id}',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "score": 4,
            "comment": "Updated review"
        }
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Rating updated"

#DELETE ENDPOINT TESTS
#Test 1: Deleting a rating
def test_delete_rating_success(client, farmer, created_rating):
    """Test that farmer can successfully delete rating."""

    farmer_token, _ = farmer
    rating_id, _, _ = created_rating

    response = client.delete(
        f'/api/ratings/{rating_id}',
        headers={"Authorization": f"Bearer {farmer_token}"}
    )

    data = response.get_json()

    assert response.status_code == 200
    assert data["message"] == "Rating deleted"






