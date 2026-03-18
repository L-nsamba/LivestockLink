import pytest
import uuid
from backend.app import app


@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client


def register_and_login(client, role):
    """Helper: register a fresh user via API and return (token, user_id)."""
    unique_email = f"test_{uuid.uuid4().hex[:8]}@test.com"
    password = "testpass123"

    reg_data = {
        "full_name": f"Test {role.capitalize()}",
        "contact": "0700000000",
        "email": unique_email,
        "password": password,
        "role": role,
    }
    if role == 'TRANSPORTER':
        reg_data.update({
            "vehicle_type": "Truck",
            "vehicle_capacity": 5000,
            "license_number": f"LIC{uuid.uuid4().hex[:6].upper()}",
            "organization_name": "Test Transport Co",
        })
    elif role == 'FARMER':
        reg_data["farm_location"] = "Test Farm"

    client.post('/api/auth/register', json=reg_data)

    login_resp = client.post('/api/auth/login', json={
        "email": unique_email,
        "password": password,
        "role": role,
    })
    data = login_resp.get_json()
    return data['token'], data['user']['user_id']


@pytest.fixture
def farmer(client):
    """Registers and logs in a farmer, returns (token, user_id)."""
    return register_and_login(client, 'FARMER')


@pytest.fixture
def transporter(client):
    """Registers and logs in a transporter, returns (token, user_id)."""
    return register_and_login(client, 'TRANSPORTER')


@pytest.fixture
def pending_request_id(client, farmer):
    """Creates a PENDING transport request as the farmer, returns request_id."""
    token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali, Rwanda",
            "destination_location": "Musanze, Rwanda",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
            "notes": "Handle with care",
        }
    )
    return resp.get_json()['request_id']


# ── POST /api/requests ── Farmer creates a transport request ─────────────────

def test_create_request_success(client, farmer):
    """Valid payload + farmer token → 201 + request_id returned."""
    token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali, Rwanda",
            "destination_location": "Musanze, Rwanda",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 201
    assert "request_id" in resp.get_json()


def test_create_requires_auth(client):
    """No token → 401."""
    resp = client.post('/api/requests',
        json={
            "pickup_location": "Kigali",
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 401


def test_create_transporter_cannot_create_request(client, transporter):
    """Only FARMER role can create transport requests → 403 for transporter."""
    token, _ = transporter
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali",
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 403


def test_create_missing_pickup_location(client, farmer):
    """pickup_location NOT NULL → 400 when absent."""
    token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 400


def test_create_missing_destination_location(client, farmer):
    """destination_location NOT NULL → 400 when absent."""
    token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 400


def test_create_missing_animal_type(client, farmer):
    """animal_type NOT NULL → 400 when absent."""
    token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali",
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 400


def test_create_notes_is_optional(client, farmer):
    """notes is nullable — omitting it must still return 201."""
    token, _ = farmer
    resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali",
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_type": "Cattle",
            "animal_quantity": 5,
        }
    )
    assert resp.status_code == 201


def test_create_status_defaults_to_pending(client, farmer, pending_request_id):
    """Status must be PENDING on a freshly created request."""
    token, farmer_id = farmer
    body = client.get(f'/api/requests/farmer/{farmer_id}',
        headers={"Authorization": f"Bearer {token}"}
    ).get_json()
    match = next((r for r in body if r['request_id'] == pending_request_id), None)
    assert match is not None
    assert match['status'] == 'PENDING'


# ── GET /api/requests ── Transporter browses PENDING requests ────────────────

def test_get_pending_requests_success(client, transporter, pending_request_id):
    """Transporter can retrieve the list of PENDING requests → 200 + list."""
    token, _ = transporter
    resp = client.get('/api/requests',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert isinstance(resp.get_json(), list)


def test_get_pending_requires_auth(client):
    """No token → 401."""
    resp = client.get('/api/requests')
    assert resp.status_code == 401


def test_get_pending_farmer_cannot_list(client, farmer):
    """FARMER role is not allowed to browse pending requests → 403."""
    token, _ = farmer
    resp = client.get('/api/requests',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_get_pending_only_pending_returned(client, transporter, pending_request_id):
    """Every item in the listing must have status == PENDING."""
    token, _ = transporter
    body = client.get('/api/requests',
        headers={"Authorization": f"Bearer {token}"}
    ).get_json()
    for item in body:
        assert item.get("status") == "PENDING", (
            f"Non-PENDING request in public listing: {item}"
        )


def test_get_pending_response_fields(client, transporter, pending_request_id):
    """All required ERD fields must be present in the listing response."""
    token, _ = transporter
    body = client.get('/api/requests',
        headers={"Authorization": f"Bearer {token}"}
    ).get_json()
    assert len(body) > 0, "No pending requests — seeding fixture may have failed"
    required = [
        "request_id", "farmer_id", "pickup_location",
        "destination_location", "pickup_date",
        "animal_type", "animal_quantity", "status",
    ]
    for field in required:
        assert field in body[0], f"ERD field missing from listing response: {field}"


# ── GET /api/requests/farmer/<farmer_id> ── Farmer views own history ─────────

def test_farmer_history_success(client, farmer, pending_request_id):
    """Farmer can view their own request history → 200 + non-empty list."""
    token, farmer_id = farmer
    resp = client.get(f'/api/requests/farmer/{farmer_id}',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    body = resp.get_json()
    assert isinstance(body, list)
    assert len(body) >= 1


def test_farmer_history_requires_auth(client, farmer):
    """No token → 401."""
    _, farmer_id = farmer
    resp = client.get(f'/api/requests/farmer/{farmer_id}')
    assert resp.status_code == 401


def test_farmer_history_cannot_view_others(client, farmer):
    """A farmer cannot view a different farmer's request history → 403."""
    token, _ = farmer
    other_farmer_id = str(uuid.uuid4())
    resp = client.get(f'/api/requests/farmer/{other_farmer_id}',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 403


def test_farmer_history_all_results_belong_to_farmer(client, farmer, pending_request_id):
    """Every row in the history must belong to the requesting farmer."""
    token, farmer_id = farmer
    body = client.get(f'/api/requests/farmer/{farmer_id}',
        headers={"Authorization": f"Bearer {token}"}
    ).get_json()
    for item in body:
        assert item.get("farmer_id") == farmer_id


# ── PUT /api/requests/<request_id> ── Farmer edits a PENDING request ─────────

def test_update_request_success(client, farmer, pending_request_id):
    """Valid field update on a PENDING request → 200 + message."""
    token, _ = farmer
    resp = client.put(f'/api/requests/{pending_request_id}',
        headers={"Authorization": f"Bearer {token}"},
        json={"pickup_location": "Nyamata, Rwanda"}
    )
    assert resp.status_code == 200
    assert "message" in resp.get_json()


def test_update_requires_auth(client, pending_request_id):
    """No token → 401."""
    resp = client.put(f'/api/requests/{pending_request_id}',
        json={"pickup_location": "Nyamata"}
    )
    assert resp.status_code == 401


def test_update_not_found(client, farmer):
    """Non-existent request_id → 404."""
    token, _ = farmer
    resp = client.put(f'/api/requests/{str(uuid.uuid4())}',
        headers={"Authorization": f"Bearer {token}"},
        json={"pickup_location": "Nowhere"}
    )
    assert resp.status_code == 404


def test_update_status_directly_rejected(client, farmer, pending_request_id):
    """Status must only change through the booking flow, not this endpoint → 400."""
    token, _ = farmer
    resp = client.put(f'/api/requests/{pending_request_id}',
        headers={"Authorization": f"Bearer {token}"},
        json={"status": "DELIVERED"}
    )
    assert resp.status_code == 400


def test_update_empty_body_rejected(client, farmer, pending_request_id):
    """An empty update body has nothing to change → 400."""
    token, _ = farmer
    resp = client.put(f'/api/requests/{pending_request_id}',
        headers={"Authorization": f"Bearer {token}"},
        json={}
    )
    assert resp.status_code == 400


# ── DELETE /api/requests/<request_id> ── Farmer cancels a request ────────────

def test_cancel_pending_success(client, farmer):
    """A PENDING request can be cancelled → 200 + message."""
    token, _ = farmer
    create_resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali",
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_type": "Goat",
            "animal_quantity": 3,
        }
    )
    rid = create_resp.get_json()['request_id']
    resp = client.delete(f'/api/requests/{rid}',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 200
    assert "message" in resp.get_json()


def test_cancel_requires_auth(client, farmer):
    """No token → 401."""
    token, _ = farmer
    create_resp = client.post('/api/requests',
        headers={"Authorization": f"Bearer {token}"},
        json={
            "pickup_location": "Kigali",
            "destination_location": "Musanze",
            "pickup_date": "2026-04-01",
            "animal_type": "Goat",
            "animal_quantity": 3,
        }
    )
    rid = create_resp.get_json()['request_id']
    resp = client.delete(f'/api/requests/{rid}')
    assert resp.status_code == 401


def test_cancel_not_found(client, farmer):
    """Non-existent request_id → 404 with error key."""
    token, _ = farmer
    resp = client.delete(f'/api/requests/{str(uuid.uuid4())}',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert resp.status_code == 404
    assert "error" in resp.get_json()
