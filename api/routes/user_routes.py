from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone

from config.database import get_users_collection

user_bp = Blueprint('users', __name__)

@user_bp.route("/users", methods=["POST"])
@jwt_required()
def create_user():
    """
    Create or Reactivate User
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
              example: John Doe
            college:
              type: string
              example: RIT
            department:
              type: string
              example: CS
    responses:
      200:
        description: User created or reactivated
      401:
        description: Unauthorized
    """
    users = get_users_collection()
    email = get_jwt_identity()
    existing_user = users.find_one({"email": email})
    
    if existing_user:
        update_fields = {
            "name": request.json.get("name"),
            "college": request.json.get("college"),
            "department": request.json.get("department")
        }
        # remove None values
        update_fields = {k: v for k, v in update_fields.items() if v}

        if update_fields:
            users.update_one({"_id": existing_user["_id"]}, {"$set": update_fields})

        if existing_user.get("status") == "DELETED":
            users.update_one({"_id": existing_user["_id"]}, {"$set": {"status": "ACTIVE"}})

        updated_user = users.find_one({"_id": existing_user["_id"]})
        updated_user["_id"] = str(updated_user["_id"])
        return jsonify(updated_user), 200
    
    user_data = {
        "email": email,
        "name": request.json.get("name"),
        "college": request.json.get("college"),
        "department": request.json.get("department"),
        "created_at": datetime.now(timezone.utc),
        "status": "ACTIVE",
        "verified": True
    }
    result = users.insert_one(user_data)
    new_user = users.find_one({"_id": result.inserted_id})
    new_user["_id"] = str(new_user["_id"])
    return jsonify(new_user), 200

@user_bp.route("/users", methods=["PATCH"])
@jwt_required()
def update_user():
    """
    Update User Details
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            name:
              type: string
              example: Jane Doe
            college:
              type: string
              example: RIT
            department:
              type: string
              example: CS
    responses:
      200:
        description: User updated successfully
      400:
        description: No fields provided
      404:
        description: User not found
    """
    users = get_users_collection()
    email = get_jwt_identity()
    existing_user = users.find_one({"email": email})
    
    if not existing_user:
        return jsonify({"error": "User not found"}), 404
    
    data = request.get_json()
    update_fields = {k: v for k, v in data.items() if k in ["name", "college", "department"] and v}
    
    if not update_fields:
        return jsonify({"error": "No fields provided"}), 400
    
    users.update_one({"_id": existing_user["_id"]}, {"$set": update_fields})
    updated_user = users.find_one({"_id": existing_user["_id"]})
    updated_user["_id"] = str(updated_user["_id"])
    return jsonify(updated_user), 200

@user_bp.route("/users/me", methods=["GET"])
@jwt_required()
def get_user():
    """
    Get Current User
    ---
    tags:
      - Users
    security:
      - Bearer: []
    responses:
      200:
        description: Returns current user object
      404:
        description: User not found
    """
    users = get_users_collection()
    email = get_jwt_identity()
    user = users.find_one({"email": email})
    
    if not user:
        return jsonify({"error": "User not found"}), 404
    
    user["_id"] = str(user["_id"])
    return jsonify(user), 200

@user_bp.route("/users/<email>", methods=["GET"])
@jwt_required()
def get_user_by_email(email):
    """
    Get user by email
    ---
    tags:
      - Users
    security:
      - Bearer: []
    parameters:
      - name: email
        in: path
        required: true
        type: string
    responses:
      200:
        description: User found
      404:
        description: User not found
    """
    users = get_users_collection()
    
    try:
        # Decode URL-encoded email
        decoded_email = email.replace('%40', '@')
        user = users.find_one({"email": decoded_email, "status": {"$ne": "DELETED"}})
        
        if not user:
            return jsonify({"error": "User not found"}), 404
        
        user["_id"] = str(user["_id"])
        # Don't return sensitive information
        user.pop("password", None)
        user.pop("verification_code", None)
        
        return jsonify(user), 200
        
    except Exception as e:
        return jsonify({"error": "Invalid request"}), 400