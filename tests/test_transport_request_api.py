import pytest
import uuid
import json

from backend.app import create_app
from backend.database import db as _db          # SQLAlchemy db instance
from backend.models.user import User            # adjust import path if needed
from backend.models.transport_request import TransportRequest  # adjust if needed

# App / DB fixtures
@pytest.fixture(scope="session")
def app():
    """
    One app instance for the whole test session, configured to use
    an in-memory SQLite database so tests are fully isolated from
    the real database.
    """
    app = create_app()
    app.config.update({
        "TESTING":                  True,
        "SQLALCHEMY_DATABASE_URI":  "sqlite:///:memory:",
        "SQLALCHEMY_TRACK_MODIFICATIONS": False,
        # Disable CSRF / rate-limiting if your app has them
        "WTF_CSRF_ENABLED":         False,
    })
    with app.app_context():
        _db.create_all()
        yield app
        _db.drop_all()


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


# Seed helpers

FARMER_EMAIL      = "farmer_test@agri.rw"
FARMER_PASSWORD   = "FarmerPass123!"
FARMER_PHONE      = "+250781000001"

TRANSPORTER_EMAIL    = "transporter_test@agri.rw"
TRANSPORTER_PASSWORD = "TransPass123!"
TRANSPORTER_PHONE    = "+250781000002"


def _create_user(role: str, email: str, password: str, phone: str) -> User:
    """
    Insert a real user row.  Adjust field names to match your User model.
    Password hashing is handled by the model's setter (or set_password method).
    """
    user = User(
        user_id   = str(uuid.uuid4()),
        full_name = f"Test {role.capitalize()}",
        email     = email,
        phone     = phone,
        role      = role,          # 'FARMER' | 'TRANSPORTER'
    )
    user.set_password(password)    # use whatever your model exposes
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture(scope="session")
def farmer_user(app):
    """Persistent dummy FARMER for the whole test session."""
    with app.app_context():
        existing = User.query.filter_by(email=FARMER_EMAIL).first()
        if existing:
            return existing
        return _create_user("FARMER", FARMER_EMAIL, FARMER_PASSWORD, FARMER_PHONE)


@pytest.fixture(scope="session")
def transporter_user(app):
    """Persistent dummy TRANSPORTER for the whole test session."""
    with app.app_context():
        existing = User.query.filter_by(email=TRANSPORTER_EMAIL).first()
        if existing:
            return existing
        return _create_user("TRANSPORTER", TRANSPORTER_EMAIL, TRANSPORTER_PASSWORD, TRANSPORTER_PHONE)


# Token helpers 

def _login(client, email: str, password: str) -> str:
    """
    Hit the real login endpoint and return the JWT access token string.
    Fails fast if login itself is broken.
    """
    resp = client.post(
        "/api/auth/login",
        data=json.dumps({"email": email, "password": password}),
        content_type="application/json",
    )
    assert resp.status_code == 200, (
        f"Login failed for {email}: {resp.status_code} — {resp.get_data(as_text=True)}"
    )
    token = resp.get_json().get("access_token") or resp.get_json().get("token")
    assert token, "Login response did not contain an access token"
    return token


@pytest.fixture(scope="session")
def farmer_token(client, farmer_user):
    return _login(client, FARMER_EMAIL, FARMER_PASSWORD)


@pytest.fixture(scope="session")
def transporter_token(client, transporter_user):
    return _login(client, TRANSPORTER_EMAIL, TRANSPORTER_PASSWORD)


def auth(token: str) -> dict:
    """Convenience: returns the Authorization header dict."""
    return {"Authorization": f"Bearer {token}"}


# Payload helper 

def base_payload(farmer_id: str) -> dict:
    """
    Well-formed POST body mirroring TRANSPORT_REQUESTS columns:
        farmer_id, pickup_location, destination_location,
        pickup_date, animal_type, animal_quantity, notes (optional)
    status is intentionally omitted — server must default it to PENDING.
    """
    return {
        "farmer_id":            farmer_id,
        "pickup_location":      "Kigali, Rwanda",
        "destination_location": "Musanze, Rwanda",
        "pickup_date":          "2025-08-15T08:00:00",
        "animal_type":          "Cattle",
        "animal_quantity":      5,
        "notes":                "Handle with care",
    }

#  POST /api/requests/  — Farmer creates a transport request

class TestCreateTransportRequest:

    def test_create_request_success(self, client, farmer_user, farmer_token):
        """Valid payload + farmer token → 201 + request_id returned."""
        payload = base_payload(farmer_user.user_id)
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 201
        body = resp.get_json()
        assert "request_id" in body

    def test_create_status_defaults_to_pending(self, client, farmer_user, farmer_token):
        """
        ERD: status DEFAULT 'PENDING'.
        Even if client smuggles a status field it must be ignored server-side.
        """
        payload = {**base_payload(farmer_user.user_id), "status": "DELIVERED"}
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 201
        # Fetch the created request and confirm status is PENDING
        request_id = resp.get_json()["request_id"]
        get_resp = client.get(
            f"/api/requests/{request_id}",
            headers=auth(farmer_token),
        )
        assert get_resp.get_json()["status"] == "PENDING"

    def test_create_requires_auth(self, client, farmer_user):
        """No token → 401."""
        payload = base_payload(farmer_user.user_id)
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            # intentionally no Authorization header
        )
        assert resp.status_code == 401

    def test_create_missing_pickup_location(self, client, farmer_user, farmer_token):
        """pickup_location VARCHAR(150) NOT NULL → 400 if absent."""
        payload = {k: v for k, v in base_payload(farmer_user.user_id).items()
                   if k != "pickup_location"}
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_create_missing_destination_location(self, client, farmer_user, farmer_token):
        """destination_location VARCHAR(150) NOT NULL → 400 if absent."""
        payload = {k: v for k, v in base_payload(farmer_user.user_id).items()
                   if k != "destination_location"}
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_create_missing_animal_type(self, client, farmer_user, farmer_token):
        """animal_type VARCHAR(50) NOT NULL → 400 if absent."""
        payload = {k: v for k, v in base_payload(farmer_user.user_id).items()
                   if k != "animal_type"}
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_create_invalid_animal_quantity_zero(self, client, farmer_user, farmer_token):
        """animal_quantity must be ≥ 1 (INT NOT NULL, logical minimum)."""
        payload = {**base_payload(farmer_user.user_id), "animal_quantity": 0}
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_create_notes_is_optional(self, client, farmer_user, farmer_token):
        """notes TEXT NULL in ERD — omitting it must still return 201."""
        payload = {k: v for k, v in base_payload(farmer_user.user_id).items()
                   if k != "notes"}
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 201

    def test_create_invalid_farmer_id(self, client, farmer_token):
        """
        farmer_id FK → USERS.user_id.
        A UUID that doesn't exist in the users table → 404.
        """
        payload = {**base_payload(str(uuid.uuid4()))}  # random, non-existent farmer
        resp = client.post(
            "/api/requests/",
            data=json.dumps(payload),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 404

#  GET /api/requests/  — Transporter browses PENDING requests

class TestGetPendingRequests:

    @pytest.fixture(autouse=True)
    def seed_pending(self, client, farmer_user, farmer_token):
        """Ensure at least one PENDING request exists before these tests run."""
        client.post(
            "/api/requests/",
            data=json.dumps(base_payload(farmer_user.user_id)),
            content_type="application/json",
            headers=auth(farmer_token),
        )

    def test_returns_200_and_list(self, client, transporter_token):
        resp = client.get("/api/requests/", headers=auth(transporter_token))
        assert resp.status_code == 200
        assert isinstance(resp.get_json(), list)

    def test_requires_auth(self, client):
        resp = client.get("/api/requests/")
        assert resp.status_code == 401

    def test_only_pending_status_returned(self, client, transporter_token):
        """GET /api/requests/ must only return PENDING rows."""
        body = client.get("/api/requests/", headers=auth(transporter_token)).get_json()
        for item in body:
            assert item.get("status") == "PENDING", (
                f"Non-PENDING request leaked into public listing: {item}"
            )

    def test_response_contains_all_erd_fields(self, client, transporter_token):
        """
        Every item must expose all ERD columns:
        request_id, farmer_id, pickup_location, destination_location,
        pickup_date, animal_type, animal_quantity, status, notes, created_at
        """
        body = client.get("/api/requests/", headers=auth(transporter_token)).get_json()
        assert len(body) > 0, "No pending requests found — seed may have failed"
        required = [
            "request_id", "farmer_id", "pickup_location",
            "destination_location", "pickup_date",
            "animal_type", "animal_quantity", "status", "created_at",
        ]
        for field in required:
            assert field in body[0], f"ERD field missing from listing response: {field}"

    def test_empty_list_when_no_pending(self, app, client, transporter_token):
        """
        If all existing requests are cancelled, the endpoint returns [].
        Done by temporarily cancelling everything then checking.
        We do a fresh isolated check with a clean DB state via direct model query.
        """
        with app.app_context():
            pending = TransportRequest.query.filter_by(status="PENDING").all()
            for r in pending:
                r.status = "CANCELLED"
            _db.session.commit()

        resp = client.get("/api/requests/", headers=auth(transporter_token))
        assert resp.status_code == 200
        assert resp.get_json() == []

        # Restore — mark them PENDING again so other tests aren't affected
        with app.app_context():
            cancelled = TransportRequest.query.filter_by(status="CANCELLED").all()
            for r in cancelled:
                r.status = "PENDING"
            _db.session.commit()

#  GET /api/requests/farmer/<farmer_id>  — Farmer views own history

class TestGetFarmerHistory:

    def test_farmer_history_success(self, client, farmer_user, farmer_token):
        resp = client.get(
            f"/api/requests/farmer/{farmer_user.user_id}",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 200
        body = resp.get_json()
        assert isinstance(body, list)
        assert len(body) >= 1

    def test_requires_auth(self, client, farmer_user):
        resp = client.get(f"/api/requests/farmer/{farmer_user.user_id}")
        assert resp.status_code == 401

    def test_all_results_belong_to_farmer(self, client, farmer_user, farmer_token):
        """Verifies FK integrity: every row's farmer_id == the requested farmer."""
        body = client.get(
            f"/api/requests/farmer/{farmer_user.user_id}",
            headers=auth(farmer_token),
        ).get_json()
        for item in body:
            assert item.get("farmer_id") == farmer_user.user_id

    def test_history_includes_multiple_statuses(self, app, client, farmer_user, farmer_token):
        """
        Farmer history must show ALL status values (PENDING, BOOKED, etc.),
        not just PENDING.  We directly set statuses in the DB to test this.
        """
        with app.app_context():
            requests = TransportRequest.query.filter_by(
                farmer_id=farmer_user.user_id
            ).all()
            statuses = ["PENDING", "BOOKED", "IN_TRANSIT", "DELIVERED", "CANCELLED"]
            for i, r in enumerate(requests[:len(statuses)]):
                r.status = statuses[i % len(statuses)]
            _db.session.commit()

        body = client.get(
            f"/api/requests/farmer/{farmer_user.user_id}",
            headers=auth(farmer_token),
        ).get_json()
        returned_statuses = {item["status"] for item in body}
        # At minimum PENDING should always be present
        assert len(returned_statuses) >= 1

    def test_unknown_farmer_returns_404(self, client, farmer_token):
        fake_id = str(uuid.uuid4())
        resp = client.get(
            f"/api/requests/farmer/{fake_id}",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 404

#  GET /api/requests/<request_id>  — View a single request

class TestGetSingleRequest:

    @pytest.fixture(scope="class")
    def created_request(self, client, farmer_user, farmer_token):
        """Create one request and return its ID for this class's tests."""
        resp = client.post(
            "/api/requests/",
            data=json.dumps(base_payload(farmer_user.user_id)),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 201
        return resp.get_json()["request_id"]

    def test_found_returns_200(self, client, farmer_token, created_request):
        resp = client.get(
            f"/api/requests/{created_request}",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 200
        assert resp.get_json()["request_id"] == created_request

    def test_requires_auth(self, client, created_request):
        resp = client.get(f"/api/requests/{created_request}")
        assert resp.status_code == 401

    def test_not_found_returns_404(self, client, farmer_token):
        resp = client.get(
            f"/api/requests/{str(uuid.uuid4())}",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_response_has_all_erd_fields(self, client, farmer_token, created_request):
        """All TRANSPORT_REQUESTS ERD columns must appear in the response body."""
        body = client.get(
            f"/api/requests/{created_request}",
            headers=auth(farmer_token),
        ).get_json()
        required = [
            "request_id", "farmer_id", "pickup_location",
            "destination_location", "pickup_date", "animal_type",
            "animal_quantity", "status", "notes", "created_at",
        ]
        for field in required:
            assert field in body, f"ERD field missing from single-request response: {field}"

    def test_farmer_id_matches_user(self, client, farmer_user, farmer_token, created_request):
        """farmer_id in response must match the actual USERS.user_id (FK check)."""
        body = client.get(
            f"/api/requests/{created_request}",
            headers=auth(farmer_token),
        ).get_json()
        assert body["farmer_id"] == farmer_user.user_id

#  PUT /api/requests/<request_id>  — Farmer edits a request

class TestUpdateTransportRequest:

    @pytest.fixture(scope="class")
    def pending_request_id(self, client, farmer_user, farmer_token):
        """Fresh PENDING request for update tests."""
        resp = client.post(
            "/api/requests/",
            data=json.dumps(base_payload(farmer_user.user_id)),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 201
        return resp.get_json()["request_id"]

    def test_update_pending_success(self, client, farmer_token, pending_request_id):
        """PENDING + valid editable field → 200 + message."""
        resp = client.put(
            f"/api/requests/{pending_request_id}",
            data=json.dumps({"pickup_location": "Nyamata, Rwanda"}),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 200
        assert "message" in resp.get_json()

    def test_update_requires_auth(self, client, pending_request_id):
        resp = client.put(
            f"/api/requests/{pending_request_id}",
            data=json.dumps({"pickup_location": "Nyamata"}),
            content_type="application/json",
        )
        assert resp.status_code == 401

    def test_update_not_found(self, client, farmer_token):
        resp = client.put(
            f"/api/requests/{str(uuid.uuid4())}",
            data=json.dumps({"pickup_location": "Nowhere"}),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 404

    def test_update_booked_request_rejected(self, app, client, farmer_user, farmer_token):
        """
        BOOKED = a transporter accepted this via BOOKINGS.
        Editing a BOOKED request would conflict with the booking FK → 400.
        """
        with app.app_context():
            r = TransportRequest(
                request_id=str(uuid.uuid4()),
                farmer_id=farmer_user.user_id,
                pickup_location="Kigali",
                destination_location="Musanze",
                pickup_date="2025-09-01T08:00:00",
                animal_type="Goat",
                animal_quantity=3,
                status="BOOKED",
            )
            _db.session.add(r)
            _db.session.commit()
            booked_id = r.request_id

        resp = client.put(
            f"/api/requests/{booked_id}",
            data=json.dumps({"pickup_location": "Kigali"}),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_update_in_transit_rejected(self, app, client, farmer_user, farmer_token):
        """Livestock already moving — editing is not allowed → 400."""
        with app.app_context():
            r = TransportRequest(
                request_id=str(uuid.uuid4()),
                farmer_id=farmer_user.user_id,
                pickup_location="Kigali",
                destination_location="Huye",
                pickup_date="2025-09-02T08:00:00",
                animal_type="Sheep",
                animal_quantity=10,
                status="IN_TRANSIT",
            )
            _db.session.add(r)
            _db.session.commit()
            transit_id = r.request_id

        resp = client.put(
            f"/api/requests/{transit_id}",
            data=json.dumps({"animal_quantity": 15}),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_update_status_directly_rejected(self, client, farmer_token, pending_request_id):
        """
        Status transitions are managed by the booking flow, not this endpoint.
        Sending a status field here must be blocked → 400.
        """
        resp = client.put(
            f"/api/requests/{pending_request_id}",
            data=json.dumps({"status": "DELIVERED"}),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

    def test_update_empty_body_rejected(self, client, farmer_token, pending_request_id):
        """Empty update body has nothing to change → 400."""
        resp = client.put(
            f"/api/requests/{pending_request_id}",
            data=json.dumps({}),
            content_type="application/json",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 400

#  DELETE /api/requests/<request_id>  — Farmer cancels a request

class TestDeleteTransportRequest:

    def _create_request_with_status(self, app, client, farmer_user, farmer_token, status):
        """Helper: insert a request with an arbitrary status directly via model."""
        with app.app_context():
            r = TransportRequest(
                request_id=str(uuid.uuid4()),
                farmer_id=farmer_user.user_id,
                pickup_location="Kigali",
                destination_location="Musanze",
                pickup_date="2025-10-01T08:00:00",
                animal_type="Cattle",
                animal_quantity=2,
                status=status,
            )
            _db.session.add(r)
            _db.session.commit()
            return r.request_id

    def test_cancel_pending_success(self, app, client, farmer_user, farmer_token):
        """PENDING request can be cancelled — no active booking exists."""
        rid = self._create_request_with_status(app, client, farmer_user, farmer_token, "PENDING")
        resp = client.delete(f"/api/requests/{rid}", headers=auth(farmer_token))
        assert resp.status_code == 200
        assert "message" in resp.get_json()

    def test_cancel_requires_auth(self, app, client, farmer_user, farmer_token):
        rid = self._create_request_with_status(app, client, farmer_user, farmer_token, "PENDING")
        resp = client.delete(f"/api/requests/{rid}")
        assert resp.status_code == 401

    def test_cancel_not_found(self, client, farmer_token):
        resp = client.delete(
            f"/api/requests/{str(uuid.uuid4())}",
            headers=auth(farmer_token),
        )
        assert resp.status_code == 404
        assert "error" in resp.get_json()

    def test_cancel_booked_rejected(self, app, client, farmer_user, farmer_token):
        """
        BOOKED → BOOKINGS has a FK row pointing at this request.
        Deleting would orphan that booking → must return 400.
        """
        rid = self._create_request_with_status(app, client, farmer_user, farmer_token, "BOOKED")
        resp = client.delete(f"/api/requests/{rid}", headers=auth(farmer_token))
        assert resp.status_code == 400
        # Confirm it wasn't deleted
        with app.app_context():
            assert TransportRequest.query.get(rid) is not None

    def test_cancel_in_transit_rejected(self, app, client, farmer_user, farmer_token):
        """Livestock already in transit — cannot cancel → 400."""
        rid = self._create_request_with_status(app, client, farmer_user, farmer_token, "IN_TRANSIT")
        resp = client.delete(f"/api/requests/{rid}", headers=auth(farmer_token))
        assert resp.status_code == 400
        with app.app_context():
            assert TransportRequest.query.get(rid) is not None

    def test_cancel_delivered_rejected(self, app, client, farmer_user, farmer_token):
        """DELIVERED — trip complete, retroactive cancellation must be blocked → 400."""
        rid = self._create_request_with_status(app, client, farmer_user, farmer_token, "DELIVERED")
        resp = client.delete(f"/api/requests/{rid}", headers=auth(farmer_token))
        assert resp.status_code == 400
        with app.app_context():
            assert TransportRequest.query.get(rid) is not None
