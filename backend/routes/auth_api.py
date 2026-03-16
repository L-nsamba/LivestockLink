# API endpoint methods
# POST /api/auth/login      - verify credentials, return token
# POST /api/auth/logout     - invalidate token
import bcrypt
from flask import Blueprint, request, jsonify
from database.db import Session
from models.user import User
from models.farmer import Farmer
from models.transporter import Transporter
from backend.utils.jwt_utils import generate_token

auth = Blueprint('auth', __name__)

# Creation / Registering of a farmer or transporter
@auth.route('/auth/register', methods=['POST'])
def register():
    session = Session()
    data = request.get_json()

    # Ensuring the user enters all required fields
    required = ['full_name', 'contact', 'email', 'password', 'role']
    if not data or not all(k in data for k in required):
        return jsonify({"error": "Missing required fields"}), 400

    # Error handling incase user fills in form incorrectly i.e avoiding tracebacks
    try:
        # Confirming that the email is not already existing 
        # Email is the field we defined in our table to be fully unique hence it is our reference
        existing = session.query(User).filter_by(email=data['email']).first()
        if existing:
            return jsonify({"error": "Email already in use"}), 409
        
        # Hash the plain text password before storing
        plain_password = data['password']
        hashed_password = bcrypt.hashpw(plain_password.encode('utf-8'), bcrypt.gensalt())

        # Creation of new user
        new_user = User(
            full_name = data['full_name'],
            contact = data['contact'],
            email = data['email'],
            password_hash = hashed_password.decode('utf-8'),
            role = data['role']
        )

        # Rejecting admin creation by non-authorized personnel on this api endpoint path  
        if data['role'] == 'ADMIN':
            return jsonify({"error": "Cannot register as admin"}), 403

        session.add(new_user)
        session.flush()

        # Creation of role specifications for users
        if data['role'] == 'FARMER':
            farmer = Farmer(user_id=new_user.user_id, farm_location=data.get('farm_location', ''))
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
    except Exception as e:
        session.rollback()
        return jsonify({"error": str(e)}), 500
    finally:
        session.close()        


# POST /api/auth/login      - verify credentials, return token
@auth.route('/auth/login', methods=['POST'])
def login():
    session = Session()
    data = request.get_json()

    #Get email, password and role
    email = data.get('email') if data else None
    password = data.get('password') if data else None
    role = data.get('role') if data else None

    #Validate fields
    if not email or not password or not role:
        return jsonify({"error": "Email, password, and role are required"}), 400

    try:
        #Query user by email
        user = session.query(User).filter_by(email=email).first()

        #If no user, retuen an error
        if not user:
            return jsonify({"error": "Invalid email or password"}), 401

        #Check the password
        password_matches = bcrypt.checkpw(
            password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        )

        if not password_matches:
            return jsonify({"error": "Invalid password"}), 401

        #Check the role
        if user.role != role:
            return jsonify({"error": "Invalid role selected"}), 401

        # Token creation
        token = generate_token(user.user_id, user.role)
        #Retun Successful login response
        return jsonify({
            "message": "Login successful",
            "token": token,
            "user": {
                "user_id": user.user_id,
                "full_name": user.full_name,
                "email": user.email,
                "role": user.role
            }
        }), 200
    except Exception:
        return jsonify({"error": "Login failed"}), 500
    finally:
        session.close()

# POST /api/auth/logout     - invalidate token
@auth.route('/auth/logout', methods=['POST'])
def logout():
    """
    Simply logs the user out. Frontend will clear localStorage and redirect the user to the login page.
    As the project is developed, we will make use of authentification tokens
    """

    return jsonify({
        "message": "User logged out successfully"
    }), 200