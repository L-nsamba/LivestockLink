# Use pytest to test the API endpoint logic in the corresponding routes folder
import pytest
import uuid
from backend.app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

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

    client.post('/api/auth/register', json=reg_data)

    login_resp = client.post('/api/auth/login', json={
        "email": unique_email,
        "password": password,
        "role": role
    })
    data = login_resp.get_json()
    return data['token'], data['user']['user_id']

@pytest.fixture
def transporter(client):
    """Registers and logs in a transporter, returns (token, user_id)"""
    return register_and_login(client, 'TRANSPORTER')

@pytest.fixture
def farmer(client):
    """Registers and logs in a farmer, returns (token, user_id)"""
    return register_and_login(client, 'FARMER')

@pytest.fixture
def pending_request_id(client, farmer):
    """Creates a PENDING transport request as a farmer and returns its request_id"""
    farmer_token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={
            "pickup_location": "Farm A",
            "destination_location": "Market B",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5
        }
    )
    return resp.get_json()['request_id']


# Test 1: Creating a booking successfully
def test_create_booking_success(client, transporter, pending_request_id):
    """Test that a transporter can create a booking"""
    token, _ = transporter
    response = client.post('/api/bookings',
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": pending_request_id}
    )

    assert response.status_code == 201
    assert "booking_id" in response.get_json()
    assert response.get_json()["message"] == "Booking created successfully"


# Test 2: Creating booking with missing request_id
def test_create_booking_missing_request_id(client, transporter):
    """Test that creating a booking without request_id fails"""
    token, _ = transporter
    response = client.post('/api/bookings',
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )

    assert response.status_code == 400
    assert "error" in response.get_json()
    assert "request_id" in response.get_json()["error"].lower()


# Test 3: Creating booking without authorization
def test_create_booking_no_auth(client):
    """Test that creating a booking without a token fails"""
    response = client.post('/api/bookings',
        headers={"Content-Type": "application/json"},
        json={"request_id": "some-uuid"}
    )

    assert response.status_code == 401
    assert "error" in response.get_json()


# Test 4: Farmer trying to create booking (wrong role)
def test_create_booking_wrong_role(client, farmer):
    """Test that farmers cannot create bookings"""
    farmer_token, _ = farmer
    response = client.post('/api/bookings',
        headers={"Authorization": f"Bearer {farmer_token}"},
        json={"request_id": "some-uuid"}
    )

    assert response.status_code == 403


# Test 5: Get transporter bookings
def test_get_transporter_bookings(client, transporter):
    """Test retrieving all bookings for a transporter"""
    token, user_id = transporter
    response = client.get(f'/api/bookings/transporter/{user_id}',
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 200
    assert isinstance(response.get_json(), list)

    if len(response.get_json()) > 0:
        booking = response.get_json()[0]
        assert "booking_id" in booking
        assert "request_id" in booking
        assert "status" in booking


# Test 6: Update booking status
def test_update_booking_status(client, transporter, pending_request_id):
    """Test updating a booking status"""
    token, _ = transporter

    create_response = client.post('/api/bookings',
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": pending_request_id}
    )
    booking_id = create_response.get_json()["booking_id"]

    update_response = client.put(f'/api/bookings/{booking_id}',
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "IN_TRANSIT"}
    )

    assert update_response.status_code == 200
    assert "message" in update_response.get_json()


# Test 7: Update with invalid status
def test_update_booking_invalid_status(client, transporter, pending_request_id):
    """Test that invalid status values are rejected"""
    token, _ = transporter

    create_response = client.post('/api/bookings',
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": pending_request_id}
    )
    booking_id = create_response.get_json()["booking_id"]

    response = client.put(f'/api/bookings/{booking_id}',
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "INVALID_STATUS"}
    )

    assert response.status_code == 400
    assert "error" in response.get_json()


# Test 8: Delete/cancel a booking
def test_cancel_booking(client, transporter, pending_request_id):
    """Test cancelling a booking"""
    token, _ = transporter

    create_response = client.post('/api/bookings',
        headers={"Authorization": f"Bearer {token}"},
        json={"request_id": pending_request_id}
    )
    booking_id = create_response.get_json()["booking_id"]

    delete_response = client.delete(f'/api/bookings/{booking_id}',
        headers={"Authorization": f"Bearer {token}"}
    )

    assert delete_response.status_code == 200
    assert "cancelled" in delete_response.get_json()["message"].lower()


# Test 9: Unauthorized access to another transporter's bookings
def test_unauthorized_access_to_bookings(client, transporter):
    """Test that a transporter cannot access a different transporter's bookings"""
    token, _ = transporter
    other_transporter_id = "different-transporter-id"

    response = client.get(f'/api/bookings/transporter/{other_transporter_id}',
        headers={"Authorization": f"Bearer {token}"}
    )

    assert response.status_code == 403
