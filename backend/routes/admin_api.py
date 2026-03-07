# API endpoint methods
# GET (View all users) --> /api/admin/users
# GET (View all transport requests) --> /api/admin/requests
# GET (View all active bookings) --> /api/admin/bookings
# DELETE (delete a user) --> /api/admin/users/<id>
import bcrypt
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
    
    # Hash the plain text password before storing
    plain_password = data['password']
    hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

    # Creation of dummy user
    new_user = User(
        full_name = data['full_name'],
        contact = data['contact'],
        email = data['email'],
        password_hash = hashed_password.decode('utf-8'),
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
            vehicle_capacity=data.get('vehicle_capacity'),
            license_number=data.get('license_number'),
            organization_name=data.get('organization_name')
        )
        session.add(transporter)

    session.commit()
    return jsonify({"message": "User created", "user_id": new_user.user_id}), 201


# Get request to retrieve existing users by id
@auth.route('/api/auth/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    session = Session
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
@auth.route('/api/auth/users/<int: user_id>', methods=['PUT'])
def update_user(user_id):
    session = Session
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

# DELETE method to remove user
@auth.route('/api/auth/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    session = Session
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    session.delete(user)
    session.commit()
    return jsonify({"message": "User deleted"}), 200