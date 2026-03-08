import bcrypt
from flask import Blueprint, request, jsonify
from database.db import Session
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter

admin = Blueprint('admin', __name__)

# Get request to retrieve existing users by id
@admin.route('/admin/users/<user_id>', methods=['GET'])
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
    
    session.commit()
    return jsonify({"message": "User updated"}), 200

# DELETE method to remove user
@admin.route('/admin/users/<user_id>', methods=['DELETE'])
def delete_user(user_id):
    session = Session()
    user = session.query(User).filter_by(user_id=user_id).first()
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    session.delete(user)
    session.commit()
    return jsonify({"message": "User deleted"}), 200