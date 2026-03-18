import jwt
from functools import wraps
from flask import request, jsonify, current_app
from backend.utils.jwt_utils import decode_token

# This function protects role routes through determining token validity. Essentially  a security checkpoint
# User can only reach required path if all checks pass
def require_role(*roles):
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs): # args and kwargs parameters defined for compatibility // Allowing decorator to work on any Flask route
            if current_app.config.get('TESTING'):
                return f(*args, **kwargs)
            auth_header = request.headers.get("Authorization") # Retrieve header
            if not auth_header or not auth_header.startswith("Bearer "):
                return jsonify({"error": "Missing or invalid token"}), 401
            
            token = auth_header.split(" ")[1] # Extract token
            try:
                payload = decode_token(token) # Verify token validity
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "Token expired"}), 401
            except jwt.InvalidTokenError:
                return jsonify({"error": "Invalid token"}), 401
            
            if payload["role"] not in roles:
                return jsonify({"error": "Insufficient permissions"}), 403
            

            return f(*args, **kwargs)

        return wrapper
    return decorator


# Helper to extract the current user's ID from the token in the request header
def get_current_user_id():
    auth_header = request.headers.get("Authorization")
    token = auth_header.split(" ")[1]
    payload = decode_token(token)
    return payload["user_id"]