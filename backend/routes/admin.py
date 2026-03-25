import os
import bcrypt
from dotenv import load_dotenv
from flask import Blueprint, request, jsonify
from database.db import Session
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter
from models.transport_request import TransportRequest
from models.booking import Bookings
from models.rating import Rating
from sqlalchemy import func
from backend.utils.auth_decorator import require_role

admin = Blueprint('admin', __name__)

load_dotenv()
ADMIN_KEY = os.getenv("ADMIN_REGISTRATION_KEY")

# ── Admin Registration ───────────────────────────────────────────
@admin.route('/admin/register', methods=['POST'])
def register_admin():
    data = request.get_json()

    if data.get('admin_key') != ADMIN_KEY:
        return jsonify({"error": "Invalid admin key"}), 403

    required = ['full_name', 'contact', 'email', 'password']
    if not data or not all(k in data for k in required):
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


# ── User CRUD ────────────────────────────────────────────────────
@admin.route('/admin/users', methods=['GET'])
@require_role('ADMIN')
def get_all_users():
    session = Session()
    try:
        users = session.query(User).all()
        return jsonify([
            {
                "user_id":   user.user_id,
                "full_name": user.full_name,
                "email":     user.email,
                "contact":   user.contact,
                "role":      user.role
            }
            for user in users
        ]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@admin.route('/admin/users/<user_id>', methods=['GET'])
@require_role('ADMIN')
def get_user(user_id):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404
        return jsonify({
            "user_id":   user.user_id,
            "full_name": user.full_name,
            "email":     user.email,
            "contact":   user.contact,
            "role":      user.role
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@admin.route('/admin/users/<user_id>', methods=['PUT'])
@require_role('ADMIN')
def update_user(user_id):
    session = Session()
    try:
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

        session.commit()
        return jsonify({"message": "User updated"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


@admin.route('/admin/users/<user_id>', methods=['DELETE'])
@require_role('ADMIN')
def delete_user(user_id):
    session = Session()
    try:
        user = session.query(User).filter_by(user_id=user_id).first()
        if not user:
            return jsonify({"error": "User not found"}), 404

        session.delete(user)
        session.commit()
        return jsonify({"message": "User deleted"}), 200
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── Chart: Stats summary ─────────────────────────────────────────
@admin.route('/admin/charts/stats', methods=['GET'])
@require_role('ADMIN')
def dashboard_stats():
    session = Session()
    try:
        total_users        = session.query(User).count()
        total_farmers      = session.query(User).filter_by(role='FARMER').count()
        total_transporters = session.query(User).filter_by(role='TRANSPORTER').count()
        total_requests     = session.query(TransportRequest).count()
        pending_requests   = session.query(TransportRequest).filter_by(status='PENDING').count()
        total_bookings     = session.query(Bookings).count()
        # DELIVERED is the terminal success state in your Bookings model
        completed_trips    = session.query(Bookings).filter_by(status='DELIVERED').count()

        return jsonify({
            'total_users':        total_users,
            'total_farmers':      total_farmers,
            'total_transporters': total_transporters,
            'total_requests':     total_requests,
            'pending_requests':   pending_requests,
            'total_bookings':     total_bookings,
            'completed_trips':    completed_trips,
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── Chart: Requests per day ──────────────────────────────────────
@admin.route('/admin/charts/requests-per-day', methods=['GET'])
@require_role('ADMIN')
def requests_per_day():
    session = Session()
    try:
        from backend.charts.requests_vs_dates import get_requests_per_day
        return jsonify(get_requests_per_day()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── Chart: Request status breakdown ─────────────────────────────
@admin.route('/admin/charts/status-breakdown', methods=['GET'])
@require_role('ADMIN')
def status_breakdown():
    session = Session()
    try:
        from backend.charts.status_breakdown import get_request_status_breakdown
        return jsonify(get_request_status_breakdown()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── Chart: Top pickup locations ──────────────────────────────────
@admin.route('/admin/charts/top-pickup-locations', methods=['GET'])
@require_role('ADMIN')
def top_pickup_locations():
    session = Session()
    try:
        from backend.charts.top_pickup_locations import get_top_pickup_locations
        return jsonify(get_top_pickup_locations()), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── Notifications: Completed trips ──────────────────────────────
# Uses transport_request relationship on Bookings to get full trip details
@admin.route('/admin/completed-trips', methods=['GET'])
@require_role('ADMIN')
def completed_trips():
    session = Session()
    try:
        results = session.query(Bookings).filter_by(status='DELIVERED').all()

        return jsonify([{
            'booking_id':           b.booking_id,
            'transporter_id':       b.transporter_id,
            'accepted_at':          str(b.accepted_at),
            'pickup_location':      b.transport_request.pickup_location,
            'destination_location': b.transport_request.destination_location,
            'pickup_date':          str(b.transport_request.pickup_date),
            'farmer_id':            b.transport_request.farmer_id,
            'animal_type':          b.transport_request.animal_type,
            'animal_quantity':      b.transport_request.animal_quantity,
        } for b in results]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()


# ── Notifications: All ratings ───────────────────────────────────
# Fields from Rating model: rating_id, booking_id, rating_by,
#                           rating_for, score, comment, created_at
@admin.route('/admin/ratings', methods=['GET'])
@require_role('ADMIN')
def all_ratings():
    session = Session()
    try:
        results = session.query(Rating).order_by(Rating.created_at.desc()).all()

        return jsonify([{
            'rating_id':  r.rating_id,
            'booking_id': r.booking_id,
            'rating_by':  r.rating_by,
            'rating_for': r.rating_for,
            'score':      r.score,
            'comment':    r.comment,
            'created_at': str(r.created_at),
        } for r in results]), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()