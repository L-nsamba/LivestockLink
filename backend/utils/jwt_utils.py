# This file handles the generation and verification of session tokens
import jwt
import os
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("JWT_SECRET_KEY")

# Function responsible for creation of session token
def generate_token(user_id, role):
    payload = {
        "user_id" : user_id,
        "role" : role,
        "exp" : datetime.now(timezone.utc) + timedelta(hours=8) # Setting a max session duration of 8 hours
    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256") # HS256 algorithm used to create a cryptographic signature

# Function responsible for session management i.e signature expired, token invalidation
def decode_token(token):
    return jwt.decode(token, SECRET_KEY, algorithms=["HS256"])