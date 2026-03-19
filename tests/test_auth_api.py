# Use pytest to test the API endpoint logic in the corresponding routes folder
import json

import pytest
from backend.app import app

@pytest.fixture
# We create a test client to send fake requests to the server
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

# Registration tests
# This contains all the necessary tests that could be done when a user is registering their profile

# Test 1 : registration with missing required fields
def test_register_missing_fields(client):
    response = client.post('/api/auth/register', json={
        "full_name": "Mufaro"
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Missing required fields"

# Test 2 : registration which fails if user is trying to create ADMIN through this endpoint
def test_register_admin_forbidden(client):
    response = client.post('/api/auth/register', json={
        "full_name": "Admin Mufaro",
        "contact": "0795000000",
        "email": "mufaro@livestocklink.com",
        "password": "12345678",
        "role": "ADMIN"
    })

    assert response.status_code == 403
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Cannot register as admin"

# Test 3: A successful farmer registration
def test_register_farmer_success(client):
    response = client.post('/api/auth/register', json={
        "full_name": "Farmer Queen",
        "contact": "0795111111",
        "email": "farmerqueen@livestocklink.com",
        "password": "abcd1234",
        "role": "FARMER",
        "farm_location": "Gasabo"
    })

    assert response.status_code in [201, 409]
    data = response.get_json()

    # If the user already exists, then response code 409 is also accepted during repeated tests
    if response.status_code == 201:
        assert data["message"] == "User created"
        assert "user_id" in data
    else:
        assert data["error"] == "Email already in use"

# Test 4: A successful transporter registration
def test_registration_transporter_success(client):
    response = client.post('/api/auth/register', json={
        "full_name": "Michael Transporter",
        "contact": "0795222222",
        "email": "michaeltransporter@livestocklink.com",
        "password": "efgh5678",
        "role": "TRANSPORTER",
        "vehicle_type": "Truck",
        "vehicle_capacity": 15,
        "license_number": "RAB123X",
        "organisation_name": "MoveFast Ltd"
    })

    assert response.status_code in [201, 409]
    data = response.get_json()

    if response.status_code == 201:
        assert data["message"] == "User created"
        assert "user_id" in data
    else:
        assert data["error"] == "Email already in use"

# Login Tests

# Test 1 : Test login with missing fields
def test_lgin_missing_fields(client):
    response = client.post('/api/auth/login', json={
        "email": "leon@livestocklink.com",
    })

    assert response.status_code == 400
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Email, password, and role are required"

# Test 2 : Login fails if email does not exist
def test_login_invalid_email(client):
    response = client.post('/api/auth/login', json={
        "email": "nonexistent@livestocklink.com",
        "password": "12345678",
        "role": "FARMER"
    })

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid email or password"

# Test 3 : Login fails with wrong password
def test_login_invalid_password(client):
    response = client.post('/api/auth/login', json={
        "email": "leon@livestocklink.com",
        "password": "wrongpassword",
        "role": "ADMIN"
    })

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid password"

# Test 4: Login fails when the wrong role is selected
def test_login_invalid_role(client):
    response = client.post('/api/auth/login', json={
        "email": "leontransporter@livestocklink.com",
        "password": "12345678",
        "role": "FARMER"
    })

    assert response.status_code == 401
    data = response.get_json()
    assert "error" in data
    assert data["error"] == "Invalid role selected"

# Test 5: Successful Admin Login
def test_login_admin_success(client):
    response = client.post('/api/auth/login', json={
        "email" : "leon@livestocklink.com",
        "password" : "12345678",
        "role" : "ADMIN"
    })

    assert response.status_code == 200
    data = response.get_json()

    assert data["message"] == "Login successful"
    assert "token" in data
    assert "user" in data
    assert data["user"]["email"] == "leon@livestocklink.com"
    assert data["user"]["role"] == "ADMIN"

# LOGOUT TEST

# Test for successful logout
def test_logout_success(client):
    response = client.post('/api/auth/logout')

    assert response.status_code == 200
    data = response.get_json()
    assert data["message"] == "User logged out successfully"
