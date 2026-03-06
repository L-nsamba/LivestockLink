# API endpoint methods
# GET (View all users) --> /api/admin/users
# GET (View all transport requests) --> /api/admin/requests
# GET (View all active bookings) --> /api/admin/bookings
# DELETE (delete a user) --> /api/admin/users/<id>

from flask import Blueprint, request, jsonify
from database.db import Session
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter

auth = Blueprint('auth', __name__)

# Creation / Registering of user
@auth.route('/auth/register', methods=['POST'])
def register():
    session = Session()
    data = request.get_json()

    # Confirming that the email is not already existing 
    # Email is the field we defined in our table to be fully unique hence it is our reference
    existing = session.query(User).filter_by(email=data['email']).first()
    if existing:
        return jsonify({"error": "Email already in use"}), 409
    
    # Creation of dummy user
    new_user = User(
        full_name = data['full_name'],
        contact = data['contact'],
        email = data['email'],
        password_hash = data['password'],
        role = data['role']
        # created_at = data['created_at']
    )

    session.add(new_user)
    session.flush()

    # Creation of role specifications for users
    if data['role'] == 'FARMER':
        farmer = Farmer(user_id=new_user.user_id, farm_location=data.get('farm_location'), created_at=data.get('created_at'))
        session.add(farmer)
    elif data['role'] == 'TRANSPORTER':
        transporter = Transporter(
            user_id=new_user.user_id,
            vehicle_type=data.get('vehicle_type'),
            vehicle_capacity=data.get('vehicle_capacity')
        )
        session.add(transporter)

    session.commit()
    return jsonify({"message": "User created", "user_id": new_user.user_id}), 201


