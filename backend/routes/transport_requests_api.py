# API endpoint methods
# POST (create transport request) --> /api/requests
# GET (View pending requests) --> /api/requests
# GET (Farmer viewing own history) --> /api/requests/farmer/<farmer_id>
# PUT (Edit a request) --> /api/requests/<request_id>
# DELETE (Farmer cancels a request) --> /api/requests/<request_id>

from flask import Blueprint, request, jsonify
from database.db import Session
from models.transport_request import TransportRequest
from models.booking import Bookings
from backend.utils.auth_decorator import require_role, get_current_user_id

transport_requests = Blueprint('transport_request', __name__)

# POST request - farmer initiates a transport request
# farmer_id is taken from the JWT token, not the request body, to prevent spoofing
@transport_requests.route('/api/requests', methods=['POST'])
@require_role('FARMER')
def create_request():
    session = Session()
    try:
        data = request.get_json()
        required_fields = ['pickup_location', 'destination_location', 'pickup_date', 'animal_type', 'animal_quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        farmer_id = get_current_user_id()

        new_request = TransportRequest(
            farmer_id = farmer_id,
            pickup_location = data['pickup_location'],
            destination_location = data['destination_location'],
            pickup_date = data['pickup_date'],
            animal_type = data['animal_type'],
            animal_quantity = data['animal_quantity'],
            notes = data.get('notes', None)
        )

        session.add(new_request)
        session.commit()
        return jsonify({"message": "Request created", "request_id": new_request.request_id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# GET all pending requests - transporters browse available jobs
@transport_requests.route('/api/requests', methods=['GET'])
@require_role('TRANSPORTER')
def get_all_requests():
    session = Session()
    try:
        pending_requests = session.query(TransportRequest).filter_by(status='PENDING').all()

        return jsonify([{
            "request_id" : r.request_id,
            "farmer_id" : r.farmer_id,
            "pickup_location" : r.pickup_location,
            "destination_location" : r.destination_location,
            "pickup_date" : str(r.pickup_date),
            "animal_type" : r.animal_type,
            "animal_quantity" : r.animal_quantity,
            "status" : r.status,
            "notes" : r.notes,
            "created_at" : str(r.created_at),
        } for r in pending_requests]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# GET farmer's own request history
@transport_requests.route('/api/requests/farmer/<farmer_id>', methods=['GET'])
@require_role('FARMER')
def get_farmer_requests(farmer_id):
    session = Session()
    try:
        if get_current_user_id() != farmer_id:
            return jsonify({"error": "Unauthorized"}), 403

        results = session.query(TransportRequest, Bookings).outerjoin(
            Bookings, Bookings.request_id == TransportRequest.request_id
        ).filter(TransportRequest.farmer_id == farmer_id).all()

        return jsonify([{
            "request_id" : r.request_id,
            "farmer_id" : r.farmer_id,
            "pickup_location" : r.pickup_location,
            "destination_location" : r.destination_location,
            "pickup_date" : str(r.pickup_date),
            "animal_type" : r.animal_type,
            "animal_quantity" : r.animal_quantity,
            "status" : r.status,
            "notes" : r.notes,
            "created_at" : str(r.created_at),
            "booking_id" : b.booking_id if b else None,
            "transporter_id" : b.transporter_id if b else None,
        } for r, b in results]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# PUT request to allow farmers to update their PENDING request details
@transport_requests.route('/api/requests/<request_id>', methods=['PUT'])
@require_role('FARMER')
def update_request(request_id):
    session = Session()
    try:
        req = session.query(TransportRequest).filter_by(request_id=request_id).first()
        if not req:
            return jsonify({"error": "Request not found"}), 404

        if req.farmer_id != get_current_user_id():
            return jsonify({"error": "Unauthorized"}), 403

        if req.status != 'PENDING':
            return jsonify({"error": "Cannot edit a request that is not PENDING"}), 400

        data = request.get_json()

        if 'status' in data:
            return jsonify({"error": "Status cannot be changed directly; use the booking flow"}), 400

        editable_fields = ['pickup_location', 'destination_location', 'pickup_date', 'animal_type', 'animal_quantity', 'notes']
        updates = {f: data[f] for f in editable_fields if f in data}

        if not updates:
            return jsonify({"error": "No valid fields to update"}), 400

        for field, value in updates.items():
            setattr(req, field, value)

        session.commit()
        return jsonify({"message": "Request updated"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

# DELETE request to allow farmers to cancel a PENDING request
@transport_requests.route('/api/requests/<request_id>', methods=['DELETE'])
@require_role('FARMER')
def delete_request(request_id):
    session = Session()
    try:
        req = session.query(TransportRequest).filter_by(request_id=request_id).first()
        if not req:
            return jsonify({"error": "Request not found"}), 404

        if req.farmer_id != get_current_user_id():
            return jsonify({"error": "Unauthorized"}), 403

        if req.status != 'PENDING':
            return jsonify({"error": f"Cannot cancel a request with status '{req.status}'"}), 400

        session.delete(req)
        session.commit()
        return jsonify({"message": "Request cancelled"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
