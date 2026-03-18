# API endpoint methods
# POST (Farmer submits rating after delivery) --> /api/ratings
# GET (Get all ratings for a transporter) --> /api/ratings/transporter/<id>
# GET (Get all ratings made by a farmer) --> /api/ratings/farmer/<id>
# GET (Get a single rating) --> /api/ratings/<rating_id>
# PUT (Edit a rating) --> /api/ratings/<rating_id>
# DELETE (Delete a rating) --> /api/ratings/<rating_id>

from flask import Blueprint, request, jsonify
from database.db import Session
from models.rating import Rating
from models.booking import Bookings
from backend.utils.auth_decorator import require_role, get_current_user_id

ratings = Blueprint('ratings', __name__)

#POST (Farmer submits rating after delivery)
@ratings.route('/api/ratings', methods=['POST'])
@require_role('FARMER')
def create_rating():
    session = Session()
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid or missing JSON"}), 400

        required_fields = ['booking_id', 'score']
        for field in required_fields:
            if field not in data:
                return jsonify({"error": f"Missing field: {field}"}), 400

        if not isinstance(data['score'], int) or not (1 <= data['score'] <= 5):
            return jsonify({"error": "Score must be an integer between 1 and 5"}), 400

        current_user = get_current_user_id()

        booking = session.query(Bookings).join(
            Bookings.transport_request
        ).filter(
            Bookings.booking_id == data['booking_id'],
            Bookings.status == 'DELIVERED'
        ).first()

        if not booking:
            return jsonify({"error": "No delivered booking found with that ID"}), 403

        if booking.transport_request.farmer_id != current_user:
            return jsonify({"error": "You can only rate your own deliveries"}), 403

        existing = session.query(Rating).filter_by(
            booking_id=data['booking_id']
        ).first()

        if existing:
            return jsonify({"error": "You already rated this delivery"}), 400

        new_rating = Rating(
            booking_id=data['booking_id'],
            rating_by=current_user,
            rating_for=booking.transporter_id,
            score=data['score'],
            comment=data.get('comment', None)
        )

        session.add(new_rating)
        session.commit()

        return jsonify({"message": "Rating created", "rating_id": new_rating.rating_id}), 201

    except Exception as e:
        session.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        session.close()

#GET all ratings for a transporter
@ratings.route('/api/ratings/transporter/<transporter_id>', methods=['GET'])
def get_transporter_ratings(transporter_id):
    session = Session()
    try:
        ratings_list = session.query(Rating).filter_by(rating_for=transporter_id).all()

        return jsonify([{
            "rating_id": r.rating_id,
            "booking_id": r.booking_id,
            "rating_by": r.rating_by,
            "score": r.score,
            "comment": r.comment
        } for r in ratings_list]), 200

    except Exception:
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

#GET all ratings made by a farmer
@ratings.route('/api/ratings/farmer/<farmer_id>', methods=['GET'])
@require_role('FARMER')
def get_farmer_ratings(farmer_id):
    session = Session()
    try:
        if get_current_user_id() != farmer_id:
            return jsonify({"error": "Unauthorized"}), 403

        ratings_list = session.query(Rating).filter_by(rating_by=farmer_id).all()

        return jsonify([{
            "rating_id": r.rating_id,
            "booking_id": r.booking_id,
            "rating_for": r.rating_for,
            "score": r.score,
            "comment": r.comment
        } for r in ratings_list]), 200

    except Exception:
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

#GET single rating
@ratings.route('/api/ratings/<rating_id>', methods=['GET'])
def get_single_rating(rating_id):
    session = Session()
    try:
        r = session.query(Rating).filter_by(rating_id=rating_id).first()

        if not r:
            return jsonify({"error": "Rating not found"}), 404

        return jsonify({
            "rating_id": r.rating_id,
            "booking_id": r.booking_id,
            "rating_by": r.rating_by,
            "rating_for": r.rating_for,
            "score": r.score,
            "comment": r.comment
        }), 200

    except Exception:
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()

#PUT (Edit rating)
@ratings.route('/api/ratings/<rating_id>', methods=['PUT'])
@require_role('FARMER')
def update_rating(rating_id):
    session = Session()
    try:
        r = session.query(Rating).filter_by(rating_id=rating_id).first()

        if not r:
            return jsonify({"error": "Rating not found"}), 404

        if r.rating_by != get_current_user_id():
            return jsonify({"error": "Unauthorized"}), 403

        data = request.get_json()

        if not data:
            return jsonify({"error": "Invalid JSON"}), 400

        if 'score' in data:
            if not isinstance(data['score'], int) or not (1 <= data['score'] <= 5):
                return jsonify({"error": "Score must be between 1 and 5"}), 400

        for field in ['score', 'comment']:
            if field in data:
                setattr(r, field, data[field])

        session.commit()
        return jsonify({"message": "Rating updated"}), 200

    except Exception as e:
        session.rollback()
        return jsonify({"error": "Internal server error", "details": str(e)}), 500
    finally:
        session.close()

#DELETE rating
@ratings.route('/api/ratings/<rating_id>', methods=['DELETE'])
@require_role('FARMER')
def delete_rating(rating_id):
    session = Session()
    try:
        r = session.query(Rating).filter_by(rating_id=rating_id).first()

        if not r:
            return jsonify({"error": "Rating not found"}), 404

        if r.rating_by != get_current_user_id():
            return jsonify({"error": "Unauthorized"}), 403

        session.delete(r)
        session.commit()

        return jsonify({"message": "Rating deleted"}), 200

    except Exception:
        session.rollback()
        return jsonify({"error": "Internal server error"}), 500
    finally:
        session.close()
