# API endpoint methods
# POST (create transport request) --> /api/requests/
# GET (View pending requests) --> /api/requests/
# GET (Farmer viewing own history) --> /api/requests/farmer/<farmer_id>
# GET (View single request) --> /api/requests/<request_id>
# PUT (Edit a request) --> /api/requests/<request_id>
# DELETE (Farmer cancels a request) --> /api/requests/<request_id>

from flask import Blueprint, request, jsonify
from database.db import Session
from models.transport_request import TransportRequest
from models.farmer import Farmer

transport_requests = Blueprint('transport_request', __name__)

# POST request which is basically the farmer initiating the creation of a transport request
@transport_requests.route('/api/requests', methods=['POST'])
def create_request():
    session = Session()
    try:
        data = request.get_json()
        required_fields = ['farmer_id', 'pickup_location', 'destination', 'pickup_date', 'animal_type', 'animal_quantity']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing required field: {field}"}), 400

        new_request = TransportRequest(
            farmer_id = data['farmer_id'],
            pickup_location = data['pickup_location'],
            destination = data['destination'],
            pickup_date = data['pickup_date'],
            animal_type = data['animal_type'],
            animal_quantity = data['animal_quantity'],
            notes = data.get('notes', None)
        )

        session.add(new_request)
        session.commit()
        return jsonify({"message": "Request created", "request_id": new_request.request_id}), 201
    finally:
        session.close()

# Get request which allows transporters to retrieve latest transport requests made by farmers
@transport_requests.route('/api/requests', methods=['GET'])
def get_all_requests():
    session = Session()
    try:
        pending_requests = session.query(TransportRequest).filter_by(status='PENDING').all()

        return jsonify([{
            "request_id" : r.request_id,
            "farmer_id" : r.farmer_id,
            "pickup_location" : r.pickup_location,
            "destination" : r.destination,
            "pickup_date" : str(r.pickup_date),
            "animal_type" : r.animal_type,
            "animal_quantity" : r.animal_quantity,
            "status" : r.status,
            "notes" : r.notes
        } for r in pending_requests]), 200
    finally:
        session.close()

# PUT request to allow farmers to update their request info/status
@transport_requests.route('/api/requests/<int:request_id>', methods=['PUT'])
def update_request(request_id):
    session = Session()
    try:
        req = session.query(TransportRequest).filter_by(request_id=request_id).first()
        if not req:
            return jsonify({"error": "Request not found"}), 404
        if req.status != 'PENDING':
            return jsonify({"error": "Cannot edit a request that is already booked by a transporter"}), 400

        data = request.get_json()
        for field in ['pickup_location', 'destination', 'pickup_date', 'animal_type', 'animal_quantity', 'notes']:
            if field in data:
                setattr(req, field, data[field])

        session.commit()
        return jsonify({"message": "Request updated"}), 200
    finally:
        session.close()

# Delete request to allow farmers to cancel a request they made
@transport_requests.route('/api/requests/<int:request_id>', methods=['DELETE'])
def delete_request(request_id):
    session = Session()
    try:
        req = session.query(TransportRequest).filter_by(request_id=request_id).first()
        if not req:
            return jsonify({"error": "Request not found"}), 404

        session.delete(req)
        session.commit()
        return jsonify({"message": "Request cancelled"}), 200
    finally:
        session.close()
