# Use pytest to test import pytest
import uuid
import pytest
import json
from unittest.mock import patch, MagicMock
from backend.app import create_app

#  Fixtures

@pytest.fixture
def app():
    """Create a fresh Flask test app instance."""
    app = create_app()
    app.config["TESTING"] = True
    return app


@pytest.fixture
def client(app):
    """Return a test client for the app."""
    return app.test_client()


@pytest.fixture
def farmer_id():
    """Dummy farmer UUID — maps to USERS.user_id (role=FARMER)."""
    return str(uuid.uuid4())


@pytest.fixture
def request_id():
    """Dummy transport request UUID — maps to TRANSPORT_REQUESTS.request_id."""
    return str(uuid.uuid4())


@pytest.fixture
def valid_transport_payload(farmer_id):
    """
    Well-formed POST body mirroring the TRANSPORT_REQUESTS table from the ERD:
        farmer_id, pickup_location, destination_location,
        pickup_date, animal_type, animal_quantity, notes (optional)
    Status is NOT sent — it defaults to PENDING server-side per ERD.
    """
    return {
        "farmer_id":             farmer_id,
        "pickup_location":       "Kigali, Rwanda",
        "destination_location":  "Musanze, Rwanda",
        "pickup_date":           "2025-08-15T08:00:00",
        "animal_type":           "Cattle",
        "animal_quantity":       5,
        "notes":                 "Handle with care"
    }

#  Helper — mock DB row shaped like TRANSPORT_REQUESTS for testing GET responses

def make_mock_request(farmer_id, request_id, status="PENDING"):
    """
    Returns a MagicMock shaped like a TRANSPORT_REQUESTS row.
    Field names match the ERD exactly.
    """
    mock = MagicMock()
    mock.request_id           = request_id
    mock.farmer_id            = farmer_id           # FK → USERS.user_id
    mock.pickup_location      = "Kigali, Rwanda"
    mock.destination_location = "Musanze, Rwanda"   # ERD: destination_location
    mock.pickup_date          = "2025-08-15T08:00:00"
    mock.animal_type          = "Cattle"            # ERD: animal_type
    mock.animal_quantity      = 5                   # ERD: animal_quantity INT
    mock.status               = status              # PENDING|BOOKED|IN_TRANSIT|DELIVERED|CANCELLED
    mock.notes                = "Handle with care"  # ERD: notes TEXT NULL
    mock.created_at           = "2025-07-01T10:00:00"
    return mock

#  POST /api/requests/
#  Farmer creates a transport request

class TestCreateTransportRequest:

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_request_success(self, mock_session_cls, client, valid_transport_payload):
        """Valid payload → 201 + new request_id returned."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        response = client.post(
            "/api/requests/",
            data=json.dumps(valid_transport_payload),
            content_type="application/json"
        )

        assert response.status_code == 201
        body = response.get_json()
        assert "request_id" in body
        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_status_defaults_to_pending(self, mock_session_cls, client, valid_transport_payload):
        """
        ERD defines status DEFAULT 'PENDING'.
        Even if client sends a status field it must be ignored/overridden.
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session

        payload = {**valid_transport_payload, "status": "DELIVERED"}

        response = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json"
        )
        assert response.status_code == 201

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_missing_pickup_location(self, mock_session_cls, client, valid_transport_payload):
        """pickup_location VARCHAR(150) NOT NULL in ERD → 400 if absent."""
        mock_session_cls.return_value = MagicMock()
        payload = {k: v for k, v in valid_transport_payload.items() if k != "pickup_location"}
        assert client.post("/api/requests/", data=json.dumps(payload),
                           content_type="application/json").status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_missing_destination_location(self, mock_session_cls, client, valid_transport_payload):
        """destination_location VARCHAR(150) NOT NULL in ERD → 400 if absent."""
        mock_session_cls.return_value = MagicMock()
        payload = {k: v for k, v in valid_transport_payload.items() if k != "destination_location"}
        assert client.post("/api/requests/", data=json.dumps(payload),
                           content_type="application/json").status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_missing_animal_type(self, mock_session_cls, client, valid_transport_payload):
        """animal_type VARCHAR(50) NOT NULL in ERD → 400 if absent."""
        mock_session_cls.return_value = MagicMock()
        payload = {k: v for k, v in valid_transport_payload.items() if k != "animal_type"}
        assert client.post("/api/requests/", data=json.dumps(payload),
                           content_type="application/json").status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_invalid_animal_quantity(self, mock_session_cls, client, valid_transport_payload):
        """animal_quantity INT NOT NULL — zero or negative is invalid."""
        mock_session_cls.return_value = MagicMock()
        payload = {**valid_transport_payload, "animal_quantity": 0}
        assert client.post("/api/requests/", data=json.dumps(payload),
                           content_type="application/json").status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_notes_is_optional(self, mock_session_cls, client, valid_transport_payload):
        """notes TEXT NULL in ERD — omitting it should still succeed."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        payload = {k: v for k, v in valid_transport_payload.items() if k != "notes"}
        assert client.post("/api/requests/", data=json.dumps(payload),
                           content_type="application/json").status_code == 201

    @patch("backend.routes.transport_requests_api.Session")
    def test_create_invalid_farmer_id(self, mock_session_cls, client, valid_transport_payload):
        """
        farmer_id is FK → USERS.user_id.
        If the user doesn't exist the server should reject with 404.
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None

        payload = {**valid_transport_payload, "farmer_id": str(uuid.uuid4())}
        assert client.post("/api/requests/", data=json.dumps(payload),
                           content_type="application/json").status_code == 404

#  GET /api/requests/
#  View all PENDING requests (transporter browses)

class TestGetPendingRequests:

    @patch("backend.routes.transport_requests_api.Session")
    def test_returns_200_and_list(self, mock_session_cls, client, farmer_id, request_id):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            make_mock_request(farmer_id, request_id)
        ]
        response = client.get("/api/requests/")
        assert response.status_code == 200
        assert isinstance(response.get_json(), list)

    @patch("backend.routes.transport_requests_api.Session")
    def test_empty_when_no_pending(self, mock_session_cls, client):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = []
        response = client.get("/api/requests/")
        assert response.status_code == 200
        assert response.get_json() == []

    @patch("backend.routes.transport_requests_api.Session")
    def test_only_pending_status_returned(self, mock_session_cls, client, farmer_id, request_id):
        """Endpoint filters by PENDING — no BOOKED or IN_TRANSIT should appear."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            make_mock_request(farmer_id, request_id, status="PENDING")
        ]
        body = client.get("/api/requests/").get_json()
        for item in body:
            assert item.get("status") == "PENDING"

    @patch("backend.routes.transport_requests_api.Session")
    def test_response_contains_all_erd_fields(self, mock_session_cls, client, farmer_id, request_id):
        """
        Every item must expose the ERD columns:
        request_id, farmer_id, pickup_location, destination_location,
        pickup_date, animal_type, animal_quantity, status, notes, created_at
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            make_mock_request(farmer_id, request_id)
        ]
        body = client.get("/api/requests/").get_json()
        for field in ["request_id", "farmer_id", "pickup_location",
                      "destination_location", "pickup_date",
                      "animal_type", "animal_quantity", "status", "created_at"]:
            assert field in body[0], f"ERD field missing: {field}"

#  GET /api/requests/farmer/<farmer_id>
#  Farmer views their own full history

class TestGetFarmerHistory:

    @patch("backend.routes.transport_requests_api.Session")
    def test_farmer_history_success(self, mock_session_cls, client, farmer_id, request_id):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            make_mock_request(farmer_id, request_id)
        ]
        response = client.get(f"/api/requests/farmer/{farmer_id}")
        assert response.status_code == 200
        assert len(response.get_json()) == 1

    @patch("backend.routes.transport_requests_api.Session")
    def test_farmer_no_requests_returns_empty(self, mock_session_cls, client, farmer_id):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = []
        response = client.get(f"/api/requests/farmer/{farmer_id}")
        assert response.status_code == 200
        assert response.get_json() == []

    @patch("backend.routes.transport_requests_api.Session")
    def test_all_results_belong_to_farmer(self, mock_session_cls, client, farmer_id, request_id):
        """Verifies FK: TRANSPORT_REQUESTS.farmer_id → USERS.user_id."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            make_mock_request(farmer_id, request_id)
        ]
        body = client.get(f"/api/requests/farmer/{farmer_id}").get_json()
        for item in body:
            assert item.get("farmer_id") == farmer_id

    @patch("backend.routes.transport_requests_api.Session")
    def test_history_includes_all_erd_statuses(self, mock_session_cls, client, farmer_id):
        """
        History shows ALL status values from the ERD ENUM:
        PENDING, BOOKED, IN_TRANSIT, DELIVERED, CANCELLED
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        all_statuses = ["PENDING", "BOOKED", "IN_TRANSIT", "DELIVERED", "CANCELLED"]
        mock_session.query.return_value.filter_by.return_value.all.return_value = [
            make_mock_request(farmer_id, str(uuid.uuid4()), s) for s in all_statuses
        ]
        body = client.get(f"/api/requests/farmer/{farmer_id}").get_json()
        assert {item["status"] for item in body} == set(all_statuses)

    @patch("backend.routes.transport_requests_api.Session")
    def test_unknown_farmer_returns_404(self, mock_session_cls, client):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        response = client.get(f"/api/requests/farmer/{str(uuid.uuid4())}")
        assert response.status_code == 404

#  GET /api/requests/<request_id>
#  View a single transport request

class TestGetSingleRequest:

    @patch("backend.routes.transport_requests_api.Session")
    def test_found_returns_200(self, mock_session_cls, client, farmer_id, request_id):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id)
        )
        response = client.get(f"/api/requests/{request_id}")
        assert response.status_code == 200
        assert response.get_json()["request_id"] == request_id

    @patch("backend.routes.transport_requests_api.Session")
    def test_not_found_returns_404(self, mock_session_cls, client):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        response = client.get(f"/api/requests/{str(uuid.uuid4())}")
        assert response.status_code == 404
        assert "error" in response.get_json()

    @patch("backend.routes.transport_requests_api.Session")
    def test_response_has_all_erd_fields(self, mock_session_cls, client, farmer_id, request_id):
        """
        All ERD columns for TRANSPORT_REQUESTS must appear in the response:
        request_id, farmer_id, pickup_location, destination_location,
        pickup_date, animal_type, animal_quantity, status, notes, created_at
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id)
        )
        body = client.get(f"/api/requests/{request_id}").get_json()
        for field in ["request_id", "farmer_id", "pickup_location",
                      "destination_location", "pickup_date", "animal_type",
                      "animal_quantity", "status", "notes", "created_at"]:
            assert field in body, f"ERD field missing from response: {field}"

    @patch("backend.routes.transport_requests_api.Session")
    def test_farmer_id_matches_users_fk(self, mock_session_cls, client, farmer_id, request_id):
        """farmer_id in response must match USERS.user_id (FK integrity check)."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id)
        )
        body = client.get(f"/api/requests/{request_id}").get_json()
        assert body["farmer_id"] == farmer_id

#  PUT /api/requests/<request_id>
#  Farmer edits a request

class TestUpdateTransportRequest:

    @patch("backend.routes.transport_requests_api.Session")
    def test_update_pending_success(self, mock_session_cls, client, farmer_id, request_id):
        """PENDING request + valid fields → 200."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="PENDING")
        )
        response = client.put(
            f"/api/requests/{request_id}",
            data=json.dumps({"pickup_location": "Nyamata, Rwanda"}),
            content_type="application/json"
        )
        assert response.status_code == 200
        assert "message" in response.get_json()
        mock_session.commit.assert_called_once()

    @patch("backend.routes.transport_requests_api.Session")
    def test_update_not_found(self, mock_session_cls, client):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        response = client.put(
            f"/api/requests/{str(uuid.uuid4())}",
            data=json.dumps({"pickup_location": "Nowhere"}),
            content_type="application/json"
        )
        assert response.status_code == 404

    @patch("backend.routes.transport_requests_api.Session")
    def test_update_booked_request_rejected(self, mock_session_cls, client, farmer_id, request_id):
        """
        BOOKED = a transporter accepted via BOOKINGS table.
        Editing now would conflict with the existing booking FK.
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="BOOKED")
        )
        response = client.put(
            f"/api/requests/{request_id}",
            data=json.dumps({"pickup_location": "Kigali"}),
            content_type="application/json"
        )
        assert response.status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_update_in_transit_rejected(self, mock_session_cls, client, farmer_id, request_id):
        """IN_TRANSIT — livestock already moving, editing is not allowed."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="IN_TRANSIT")
        )
        response = client.put(
            f"/api/requests/{request_id}",
            data=json.dumps({"animal_quantity": 10}),
            content_type="application/json"
        )
        assert response.status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_update_status_directly_rejected(self, mock_session_cls, client, farmer_id, request_id):
        """
        Status is managed by the booking flow (BOOKINGS table), not this endpoint.
        Direct status changes here must be blocked.
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="PENDING")
        )
        response = client.put(
            f"/api/requests/{request_id}",
            data=json.dumps({"status": "DELIVERED"}),
            content_type="application/json"
        )
        assert response.status_code == 400

    @patch("backend.routes.transport_requests_api.Session")
    def test_update_empty_body_rejected(self, mock_session_cls, client, farmer_id, request_id):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id)
        )
        response = client.put(
            f"/api/requests/{request_id}",
            data=json.dumps({}),
            content_type="application/json"
        )
        assert response.status_code == 400

#  DELETE /api/requests/<request_id>
#  Farmer cancels a request

class TestDeleteTransportRequest:

    @patch("backend.routes.transport_requests_api.Session")
    def test_cancel_pending_success(self, mock_session_cls, client, farmer_id, request_id):
        """PENDING request can be cancelled — no booking exists yet."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="PENDING")
        )
        response = client.delete(f"/api/requests/{request_id}")
        assert response.status_code == 200
        assert "message" in response.get_json()
        mock_session.delete.assert_called_once()
        mock_session.commit.assert_called_once()

    @patch("backend.routes.transport_requests_api.Session")
    def test_cancel_not_found(self, mock_session_cls, client):
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = None
        response = client.delete(f"/api/requests/{str(uuid.uuid4())}")
        assert response.status_code == 404
        assert "error" in response.get_json()

    @patch("backend.routes.transport_requests_api.Session")
    def test_cancel_booked_rejected(self, mock_session_cls, client, farmer_id, request_id):
        """
        BOOKED → BOOKINGS table has a row with FK → this request_id.
        Deleting would orphan the booking. Must return 400.
        """
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="BOOKED")
        )
        response = client.delete(f"/api/requests/{request_id}")
        assert response.status_code == 400
        mock_session.delete.assert_not_called()

    @patch("backend.routes.transport_requests_api.Session")
    def test_cancel_in_transit_rejected(self, mock_session_cls, client, farmer_id, request_id):
        """Livestock already in transit — cannot cancel."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="IN_TRANSIT")
        )
        response = client.delete(f"/api/requests/{request_id}")
        assert response.status_code == 400
        mock_session.delete.assert_not_called()

    @patch("backend.routes.transport_requests_api.Session")
    def test_cancel_delivered_rejected(self, mock_session_cls, client, farmer_id, request_id):
        """DELIVERED — trip is complete, retroactive cancellation must be blocked."""
        mock_session = MagicMock()
        mock_session_cls.return_value = mock_session
        mock_session.query.return_value.filter_by.return_value.first.return_value = (
            make_mock_request(farmer_id, request_id, status="DELIVERED")
        )
        response = client.delete(f"/api/requests/{request_id}")
        assert response.status_code == 400
        mock_session.delete.assert_not_called()
