# API endpoint methods
# POST (Transporter accepts request/ creates a booking) --> /api/bookings/
# GET (Transporter views assigned job) --> /api/bookings/transporter/<id>
# GET (View single booking detail) --> /api/bookings/<booking_id>
# PUT (Updating status(picked up, in transit, delivered)) --> /api/bookings/<booking_id>/status
# DELETE (Transporter cancels or rejects booking) --> /api/bookings/<booking_id>

from flask import Blueprint, request, jsonify
from database.db import Session
from models.booking import Bookings
from models.transport_request import TransportRequest
from backend.utils.auth_decorator import require_role, get_current_user_id

bookings = Blueprint('bookings', __name__)

# POST - transporter accepts a transport request and creates a booking
@bookings.route('/api/bookings', methods=['POST'])
@require_role('TRANSPORTER')
def create_booking():
    session = Session()
    try:
        data = request.get_json()
        if 'request_id' not in data:
            return jsonify({"error": "Missing required field: request_id"}), 400

        transporter_id = get_current_user_id()

        # Check if the request exists and is still pending
        transport_request = session.query(TransportRequest).filter_by(
            request_id=data['request_id']
        ).first()

        if not transport_request:
            return jsonify({"error": "Transport request not found"}), 404

        if transport_request.status != 'PENDING':
            return jsonify({"error": "Request is no longer available"}), 400

        # Check if booking already exists for this request
        existing_booking = session.query(Bookings).filter_by(
            request_id=data['request_id']
        ).first()

        if existing_booking:
            return jsonify({"error": "This request has already been booked"}), 400

        # Create the booking
        new_booking = Bookings(
            request_id=data['request_id'],
            transporter_id=transporter_id
        )

        # Update the transport request status to BOOKED
        transport_request.status = 'BOOKED'

        session.add(new_booking)
        session.commit()
        return jsonify({
            "message": "Booking created successfully",
            "booking_id": new_booking.booking_id
        }), 201

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# GET all bookings for a specific transporter
@bookings.route('/api/bookings/transporter/<transporter_id>', methods=['GET'])
@require_role('TRANSPORTER')
def get_transporter_bookings(transporter_id):
    session = Session()
    try:
        # Ensure transporter can only view their own bookings
        if get_current_user_id() != transporter_id:
            return jsonify({"error": "Unauthorized"}), 403

        transporter_bookings = session.query(Bookings).filter_by(
            transporter_id=transporter_id
        ).all()

        return jsonify([{
            "booking_id": b.booking_id,
            "request_id": b.request_id,
            "transporter_id": b.transporter_id,
            "accepted_at": str(b.accepted_at),
            "status": b.status
        } for b in transporter_bookings]), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# GET single booking details
@bookings.route('/api/bookings/<booking_id>', methods=['GET'])
@require_role('TRANSPORTER')
def get_booking(booking_id):
    session = Session()
    try:
        booking = session.query(Bookings).filter_by(booking_id=booking_id).first()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        # Ensure transporter can only view their own bookings
        if booking.transporter_id != get_current_user_id():
            return jsonify({"error": "Unauthorized"}), 403

        return jsonify({
            "booking_id": booking.booking_id,
            "request_id": booking.request_id,
            "transporter_id": booking.transporter_id,
            "accepted_at": str(booking.accepted_at),
            "status": booking.status
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# PUT - update booking status (e.g., PICKED_UP, IN_TRANSIT, DELIVERED)
@bookings.route('/api/bookings/<booking_id>', methods=['PUT'])
@require_role('TRANSPORTER')
def update_booking_status(booking_id):
    session = Session()
    try:
        booking = session.query(Bookings).filter_by(booking_id=booking_id).first()

        if not booking:
            return jsonify({"error": "Booking not found"}), 404

        if booking.transporter_id != get_current_user_id():
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()
        if 'status' not in data:
            return jsonify({"error": "Missing required field: status"}), 400

        valid_statuses = ['ACCEPTED', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'CANCELLED']
        if data['status'] not in valid_statuses:
            return jsonify({"error": f"Invalid status. Must be one of: {valid_statuses}"}), 400

        booking.status = data['status']

        # If booking is delivered or cancelled, update the transport request status
        if data['status'] == 'DELIVERED':
            transport_request = session.query(TransportRequest).filter_by(
                request_id=booking.request_id
            ).first()
            if transport_request:
                transport_request.status = 'COMPLETED'

        elif data['status'] == 'CANCELLED':
            transport_request = session.query(TransportRequest).filter_by(
                request_id=booking.request_id
            ).first()
            if transport_request:
                transport_request.status = 'PENDING'  # Make it available again

        session.commit()
        return jsonify({"message": "Booking status updated successfully"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()

