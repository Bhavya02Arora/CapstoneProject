from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity, create_access_token, create_refresh_token, get_jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timezone

from config.database import get_users_collection
from config.jwt_config import blacklist_token
from utils.email_utils import is_valid_email, generate_verification_code, send_verification_email

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """
    User Registration (request verification code)
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: student@rit.edu
            password:
              type: string
              example: secret123
    responses:
      200:
        description: Verification code sent
      400:
        description: Invalid input or user exists
      500:
        description: Email sending failed
    """
    users = get_users_collection()
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    if not email or not password:
        return jsonify({"error": "Email and password required"}), 400
    
    if not is_valid_email(email):
        return jsonify({"error": "Only rit.edu or g.rit.edu emails allowed"}), 400
    
    if users.find_one({"email": email}):
        return jsonify({"error": "User already exists"}), 400
    
    verification_code = generate_verification_code()
    
    if not send_verification_email(email, verification_code):
        return jsonify({"error": "Failed to send verification email"}), 500
    
    users.insert_one({
        "email": email,
        "password": generate_password_hash(password),
        "verified": False,
        "verification_code": verification_code,
        "status": "ACTIVE",
        "created_at": datetime.now(timezone.utc)
    })
    
    return jsonify({"message": "Verification code sent to email"}), 200

@auth_bp.route('/verify', methods=['POST'])
def verify():
    """
    Verify User Email
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - code
          properties:
            email:
              type: string
              example: student@rit.edu
            code:
              type: string
              example: 123456
    responses:
      200:
        description: User verified successfully
      400:
        description: Invalid email or code
    """
    users = get_users_collection()
    data = request.get_json()
    email = data.get("email", "").strip().lower()
    code = data.get("code", "").strip()
    
    if not email or not code:
        return jsonify({"error": "Email and code required"}), 400
    
    user = users.find_one({"email": email})
    if not user:
        return jsonify({"error": "User not found"}), 400
    
    if user.get("verified"):
        return jsonify({"message": "User already verified"}), 200
    
    if str(user.get("verification_code", "")) != code:
        return jsonify({"error": "Invalid verification code"}), 400
    
    users.update_one(
        {"email": email},
        {"$set": {"verified": True}, "$unset": {"verification_code": ""}}
    )
    
    return jsonify({"message": "User verified successfully"}), 200

@auth_bp.route('/login', methods=['POST'])
def login():
    """
    User Login with Refresh Token
    ---
    tags:
      - Auth
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - email
            - password
          properties:
            email:
              type: string
              example: student@rit.edu
            password:
              type: string
              example: secret123
    responses:
      200:
        description: Login successful with JWT tokens
      401:
        description: Invalid credentials or not verified
    """
    users = get_users_collection()
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")
    
    user = users.find_one({"email": email})
    if not user or not check_password_hash(user["password"], password):
        return jsonify({"error": "Invalid email or password"}), 401
    
    if not user.get("verified"):
        return jsonify({"error": "Please verify your email first"}), 401
    
    # Create both access and refresh tokens
    access_token = create_access_token(identity=email)
    refresh_token = create_refresh_token(identity=email)
    
    return jsonify({
        "message": "Login successful",
        "user_id": str(user["_id"]),
        "token": access_token,
        "refreshToken": refresh_token
    }), 200

@auth_bp.route('/logout', methods=['POST'])
@jwt_required()
def logout():
    """
    Logout and blacklist current token
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: Successfully logged out
    """
    jti = get_jwt()['jti']  # JWT ID
    blacklist_token(jti)
    return jsonify({"message": "Successfully logged out"}), 200

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh Access Token
    ---
    tags:
      - Auth
    security:
      - Bearer: []
    responses:
      200:
        description: New access token generated
      401:
        description: Invalid refresh token
    """
    current_user = get_jwt_identity()
    new_token = create_access_token(identity=current_user)
    return jsonify({"token": new_token}), 200