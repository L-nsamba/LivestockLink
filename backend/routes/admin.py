import os
import bcrypt
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from database.db import Session
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter
from models.booking import Bookings
from models.rating import Rating
from models.transport_request import TransportRequest
from backend.utils.auth_decorator import require_role
from charts.requests_vs_dates import get_requests_per_day
from charts.status_breakdown import get_request_status_breakdown, get_booking_status_breakdown
from charts.top_pickup_locations import get_top_pickup_locations, get_top_destination_locations

admin = Blueprint('admin', __name__)

load_dotenv()
ADMIN_KEY = os.getenv("ADMIN_REGISTRATION_KEY")

# Creation of an admin
@admin.route('/admin/register', methods=['POST'])
def register_admin():
    data = request.get_json()

    if data.get('admin_key') != ADMIN_KEY:
        return jsonify({"error": "Invalid admin key"}), 403
    
    required = ['full_name', 'contact', 'email', 'password']
    if not data or not all(k in data for k  in required):
        return jsonify({"error": "Missing required fields"}), 400
    
    session = Session()
    try:
        existing = session.query(User).filter_by(email=data['email']).first()
        if existing:
            return jsonify({"error": "Email already in use"}), 409
        
        hashed_password = bcrypt.hashpw(data['password'].encode('utf-8'), bcrypt.gensalt())

        new_admin = User(
            full_name=data['full_name'],
            contact=data['contact'],
            email=data['email'],
            password_hash=hashed_password.decode('utf-8'),
            role='ADMIN'
        )

        session.add(new_admin)
        session.commit()
        return jsonify({"message": "Admin created", "user_id": new_admin.user_id}), 201
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()
    

# Get all users
@admin.route('/admin/users', methods=['GET'])
@require_role('ADMIN')
def get_all_users():
    session = Session()
    users = session.query(User).all()

    result = []
    for user in users:
        entry = {
            "user_id": user.user_id,
            "full_name": user.full_name,
            "email": user.email,
            "contact": user.contact,
            "role": user.role,
            "created_at": user.created_at.strftime('%d %b %Y') if user.created_at else None
        }
        if user.role == 'FARMER':
            farmer = session.query(Farmer).filter_by(user_id=user.user_id).first()
            if farmer:
                entry['farm_location'] = farmer.farm_location
        elif user.role == 'TRANSPORTER':
            transporter = session.query(Transporter).filter_by(user_id=user.user_id).first()
            if transporter:
                entry['vehicle_type'] = transporter.vehicle_type
                entry['vehicle_capacity'] = transporter.vehicle_capacity
                entry['license_number'] = transporter.license_number
                entry['organization_name'] = transporter.organization_name
        result.append(entry)

    session.close()
    return jsonify(result), 200


# Get request to retrieve existing users by id
@admin.route('/admin/users/<user_id>', methods=['GET'])
@require_role('ADMIN')
def get_user(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    return jsonify({
        "user_id": user.user_id,
        "full_name": user.full_name,
        "email": user.email,
        "role": user.role
    }), 200

# PUT Method to update user info
@admin.route('/admin/users/<user_id>', methods=['PUT'])
@require_role('ADMIN')
def update_user(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    data = request.get_json()
    if 'full_name' in data:
        user.full_name = data['full_name']
    if 'email' in data:
        user.email = data['email']
    if 'contact' in data:
        user.contact = data['contact']

    if user.role == 'FARMER':
        farmer = session.query(Farmer).filter_by(user_id=user_id).first()
        if farmer and 'farm_location' in data:
            farmer.farm_location = data['farm_location']
    elif user.role == 'TRANSPORTER':
        transporter = session.query(Transporter).filter_by(user_id=user_id).first()
        if transporter:
            if 'vehicle_type' in data:
                transporter.vehicle_type = data['vehicle_type']
            if 'vehicle_capacity' in data:
                transporter.vehicle_capacity = data['vehicle_capacity']
            if 'license_number' in data:
                transporter.license_number = data['license_number']
            if 'organization_name' in data:
                transporter.organization_name = data['organization_name']

    session.commit()
    session.close()
    return jsonify({"message": "User updated"}), 200

# DELETE method to remove user
@admin.route('/admin/users/<user_id>', methods=['DELETE'])
@require_role('ADMIN')
def delete_user(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404

    session.delete(user)
    session.commit()
    return jsonify({"message": "User deleted"}), 200


# GET all bookings (for admin notifications / trip feed)
@admin.route('/admin/bookings', methods=['GET'])
@require_role('ADMIN')
def get_all_bookings():
    session = Session()
    try:
        bookings = session.query(Bookings).all()
        result = []
        for b in bookings:
            req = b.transport_request
            result.append({
                "booking_id": b.booking_id,
                "transporter_id": b.transporter_id,
                "farmer_id": req.farmer_id if req else None,
                "pickup_location": req.pickup_location if req else None,
                "destination_location": req.destination_location if req else None,
                "animal_type": req.animal_type if req else None,
                "animal_quantity": req.animal_quantity if req else None,
                "status": b.status,
                "accepted_at": b.accepted_at.isoformat() if b.accepted_at else None
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# GET all ratings (for admin notifications / ratings feed)
@admin.route('/admin/ratings', methods=['GET'])
@require_role('ADMIN')
def get_all_ratings():
    session = Session()
    try:
        ratings = session.query(Rating).all()
        result = []
        for r in ratings:
            result.append({
                "rating_id": r.rating_id,
                "booking_id": r.booking_id,
                "rating_by": r.rating_by,
                "rating_for": r.rating_for,
                "score": r.score,
                "comment": r.comment,
                "created_at": r.created_at.isoformat() if r.created_at else None
            })
        return jsonify(result), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── CHART ENDPOINTS ────────────────────────────────────────────────────────

@admin.route('/admin/charts/requests-per-day', methods=['GET'])
@require_role('ADMIN')
def chart_requests_per_day():
    try:
        return jsonify(get_requests_per_day()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/charts/status-breakdown', methods=['GET'])
@require_role('ADMIN')
def chart_status_breakdown():
    try:
        return jsonify(get_request_status_breakdown()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/charts/booking-status-breakdown', methods=['GET'])
@require_role('ADMIN')
def chart_booking_status_breakdown():
    try:
        return jsonify(get_booking_status_breakdown()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/charts/top-pickup-locations', methods=['GET'])
@require_role('ADMIN')
def chart_top_pickup_locations():
    try:
        return jsonify(get_top_pickup_locations()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@admin.route('/admin/charts/top-destination-locations', methods=['GET'])
@require_role('ADMIN')
def chart_top_destination_locations():
    try:
        return jsonify(get_top_destination_locations()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500