# Use pytest to test the API endpoint logic in the corresponding routes folder
import pytest
import requests

BASE_URL = "http://127.0.0.1:5000/api"
TRANSPORTER_TOKEN = "your_jwt_token_here"
FARMER_TOKEN = "your_farmer_jwt_token_here"

@pytest.fixture
def transporter_headers():
    """Reusable headers for transporter requests"""
    return {
        "Authorization": f"Bearer {TRANSPORTER_TOKEN}",
        "Content-Type": "application/json"
    }

@pytest.fixture
def farmer_headers():
    """Reusable headers for farmer requests"""
    return {
        "Authorization": f"Bearer {FARMER_TOKEN}",
        "Content-Type": "application/json"
    }

# Test 1: Creating a booking successfully
def test_create_booking_success(transporter_headers):
    """Test that a transporter can create a booking"""
    response = requests.post(
        f"{BASE_URL}/bookings",
        headers=transporter_headers,
        json={"request_id": "valid-request-uuid"}
    )
    
    # Assertions - pytest checks these automatically
    assert response.status_code == 201
    assert "booking_id" in response.json()
    assert response.json()["message"] == "Booking created successfully"

# Test 2: Creating booking with missing request_id
def test_create_booking_missing_request_id(transporter_headers):
    """Test that creating a booking without request_id fails"""
    response = requests.post(
        f"{BASE_URL}/bookings",
        headers=transporter_headers,
        json={}
    )
    
    assert response.status_code == 400
    assert "error" in response.json()
    assert "request_id" in response.json()["error"].lower()

# Test 3: Creating booking without authorization
def test_create_booking_no_auth():
    """Test that creating a booking without token fails"""
    response = requests.post(
        f"{BASE_URL}/bookings",
        headers={"Content-Type": "application/json"},
        json={"request_id": "some-uuid"}
    )
    
    assert response.status_code == 401
    assert "error" in response.json()

# Test 4: Farmer trying to create booking (wrong role)
def test_create_booking_wrong_role(farmer_headers):
    """Test that farmers cannot create bookings"""
    response = requests.post(
        f"{BASE_URL}/bookings",
        headers=farmer_headers,
        json={"request_id": "some-uuid"}
    )
    
    assert response.status_code == 403

# Test 5: Get transporter bookings
def test_get_transporter_bookings(transporter_headers):
    """Test retrieving all bookings for a transporter"""
    transporter_id = "your-transporter-id"
    response = requests.get(
        f"{BASE_URL}/bookings/transporter/{transporter_id}",
        headers=transporter_headers
    )
    
    assert response.status_code == 200
    assert isinstance(response.json(), list)
    
    # If there are bookings, check structure
    if len(response.json()) > 0:
        booking = response.json()[0]
        assert "booking_id" in booking
        assert "request_id" in booking
        assert "status" in booking

# Test 6: Update booking status
def test_update_booking_status(transporter_headers):
    """Test updating a booking status"""
    # First create a booking
    create_response = requests.post(
        f"{BASE_URL}/bookings",
        headers=transporter_headers,
        json={"request_id": "valid-request-uuid"}
    )
    booking_id = create_response.json()["booking_id"]
    
    # Now update its status
    update_response = requests.put(
        f"{BASE_URL}/bookings/{booking_id}",
        headers=transporter_headers,
        json={"status": "IN_TRANSIT"}
    )
    
    assert update_response.status_code == 200
    assert "message" in update_response.json()

# Test 7: Update with invalid status
def test_update_booking_invalid_status(transporter_headers):
    """Test that invalid status values are rejected"""
    booking_id = "some-booking-id"
    
    response = requests.put(
        f"{BASE_URL}/bookings/{booking_id}",
        headers=transporter_headers,
        json={"status": "INVALID_STATUS"}
    )
    
    assert response.status_code == 400
    assert "error" in response.json()

# Test 8: Delete/cancel a booking
def test_cancel_booking(transporter_headers):
    """Test cancelling a booking"""
    # First create a booking
    create_response = requests.post(
        f"{BASE_URL}/bookings",
        headers=transporter_headers,
        json={"request_id": "valid-request-uuid"}
    )
    booking_id = create_response.json()["booking_id"]
    
    # Now cancel it
    delete_response = requests.delete(
        f"{BASE_URL}/bookings/{booking_id}",
        headers=transporter_headers
    )
    
    assert delete_response.status_code == 200
    assert "cancelled" in delete_response.json()["message"].lower()

# Test 9: Unauthorized access to other transporter's bookings
def test_unauthorized_access_to_bookings(transporter_headers):
    """Test that transporters can't access other transporters' bookings"""
    other_transporter_id = "different-transporter-id"
    
    response = requests.get(
        f"{BASE_URL}/bookings/transporter/{other_transporter_id}",
        headers=transporter_headers
    )
    
    assert response.status_code == 403