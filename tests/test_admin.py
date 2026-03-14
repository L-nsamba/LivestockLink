# Use pytest to test the API endpoint logic in the corresponding routes folder
import pytest
import json
from backend.app import app

@pytest.fixture # Automatically returns the functions results upon test completion
# Creation of a test client to send fake requests to server
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

@pytest.fixture
# Creation of a dummy admin to avoid having to repeat the login logic 
def admin_token(client):
    response = client.post('/auth/login', json={
        "email" : "admin@livestocklink.com",
        "password" : "adminpass1234",
        "role" : "ADMIN"
    })
    return response.get_json().get('token')

# Test to retrieve all existing users
def test_get_all_users(client, admin_token):
    response = client.get('/admin/users')
        # headers={"Authorization" : f"Bearer {admin_token}"}
        # )
    assert response.status_code == 200
    data = response.get_json()
    assert isinstance(data, list) # This returns the list of existing users

# ........................Test case in-progress..............