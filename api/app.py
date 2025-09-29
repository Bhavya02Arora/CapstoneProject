from flask import Flask
from flask_cors import CORS
from flasgger import Swagger
from flask_jwt_extended import JWTManager
from datetime import timedelta
import os

from config.database import init_db
from config.jwt_config import init_jwt
from routes.auth_routes import auth_bp
from routes.user_routes import user_bp
from routes.post_routes import post_bp
from utils.file_utils import setup_upload_directories

def create_app():
    app = Flask(__name__)
    
    # CORS Configuration
    CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
    
    # Swagger Configuration
    swagger = Swagger(app)
    
    # JWT Configuration
    app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)
    
    # Initialize extensions
    init_db(app)
    init_jwt(app)
    
    # Setup upload directories
    setup_upload_directories()
    
    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp, url_prefix='/api')
    app.register_blueprint(post_bp, url_prefix='/api')
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, threaded=True, port=8080)


# from flask import Flask, request, jsonify
# from flask_cors import CORS
# from flasgger import Swagger
# from pymongo import MongoClient
# from werkzeug.security import generate_password_hash, check_password_hash
# import os, random, string, smtplib
# from email.mime.text import MIMEText
# from datetime import datetime, timezone
# from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
# from bson import ObjectId
# from enum import Enum
# from models import *
# import os
# import uuid
# import base64
# from PIL import Image
# import io
# from flask import send_from_directory
# from werkzeug.utils import secure_filename
# from flask_jwt_extended import create_refresh_token, jwt_required, get_jwt_identity, get_jwt
# from datetime import timedelta
# import threading
# import base64
# from datetime import datetime, timezone
# from flask import Flask, request, jsonify
# # Import the spam detector
# from spam_detector import SpamDetector, detect_spam

# app = Flask(__name__)
# # CORS(app)
# CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
# swagger = Swagger(app)

# # MongoDB
# client = MongoClient("mongodb://localhost:27017/")
# db = client["unicom_db"]
# users = db["users"]
# posts = db["posts"]

# # JWT Config
# app.config["JWT_SECRET_KEY"] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
# app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)  # Access token expires in 1 hour
# app.config["JWT_REFRESH_TOKEN_EXPIRES"] = timedelta(days=30)  # Refresh token expires in 30 days
# jwt = JWTManager(app)

# # Configuration for Images
# UPLOAD_FOLDER = os.path.join('static', 'uploads')
# ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
# MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
# IMAGE_SIZES = {
#     'thumbnails': (150, 150),
#     'medium': (500, 500),
#     'large': (1200, 1200)
# }
# # To store blacklisted tokens (in production, using Redis database)
# blacklisted_tokens = set()

# # Spam detector
# spam_detector = SpamDetector()

# # JWT token blacklist checker
# @jwt.token_in_blocklist_loader
# def check_if_token_revoked(jwt_header, jwt_payload):
#     jti = jwt_payload['jti']  # JWT ID
#     return jti in blacklisted_tokens

# # Create upload directories - Add after your MongoDB setup
# def setup_upload_directories():
#     directories = [
#         UPLOAD_FOLDER,
#         os.path.join(UPLOAD_FOLDER, 'thumbnails'),
#         os.path.join(UPLOAD_FOLDER, 'medium'),
#         os.path.join(UPLOAD_FOLDER, 'large')
#     ]
#     for directory in directories:
#         os.makedirs(directory, exist_ok=True)


# setup_upload_directories()

# # Image processing functions
# def allowed_file(filename):
#     return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# def save_image_from_base64(base64_string, post_id):
#     """Convert base64 to image file and save multiple sizes"""
#     try:
#         if base64_string.startswith('data:image'):
#             base64_string = base64_string.split(',')[1]

#         image_data = base64.b64decode(base64_string)

#         if len(image_data) > MAX_FILE_SIZE:
#             raise ValueError("Image too large (max 5MB)")

#         image = Image.open(io.BytesIO(image_data))

#         image_id = uuid.uuid4().hex[:12]
#         filename = f"{post_id}_{image_id}.jpg"

#         if image.mode in ('RGBA', 'P'):
#             image = image.convert('RGB')

#         image_urls = {}

#         for size_name, dimensions in IMAGE_SIZES.items():
#             resized = image.copy()
#             resized.thumbnail(dimensions, Image.Resampling.LANCZOS)

#             # ✅ Save inside static/uploads/<size>/
#             folder_path = os.path.join(app.root_path, UPLOAD_FOLDER, size_name)
#             os.makedirs(folder_path, exist_ok=True)

#             file_path = os.path.join(folder_path, filename)
#             print(f"Saving {size_name} image to: {file_path}")

#             resized.save(file_path, 'JPEG', quality=85, optimize=True)

#             if not os.path.exists(file_path):
#                 raise ValueError(f"Failed to save image: {file_path}")

#             # ✅ All URLs consistent: /static/uploads/<size>/<filename>
#             image_urls[size_name] = f"/static/uploads/{size_name}/{filename}"

#         return {
#             'image_id': image_id,
#             'filename': filename,
#             'urls': image_urls
#         }

#     except Exception as e:
#         print(f"Image processing error: {str(e)}")
#         raise ValueError(f"Invalid image data: {str(e)}")

# def delete_post_images(image_metadata_list):
#     """Delete all image files when post is deleted"""
#     for image_meta in image_metadata_list:
#         filename = image_meta.get('filename')
#         if filename:
#             # Delete all sizes using proper paths
#             for size_name in IMAGE_SIZES.keys():
#                 file_path = os.path.join(app.root_path, UPLOAD_FOLDER, size_name, filename)
#                 if os.path.exists(file_path):
#                     try:
#                         os.remove(file_path)
#                         print(f"Deleted: {file_path}")
#                     except Exception as e:
#                         print(f"Error deleting {file_path}: {e}")

# # Routes for serving images
# @app.route('/static/uploads/<filename>')
# def serve_image(filename):
#     """Serve uploaded images (large size)"""
#     filename = secure_filename(filename)
#     folder = os.path.join(app.root_path, UPLOAD_FOLDER)
    
#     # Add error handling for missing files
#     file_path = os.path.join(folder, filename)
#     if not os.path.exists(file_path):
#         return jsonify({"error": "File not found"}), 404
    
#     return send_from_directory(folder, filename)

# # ---- Serve Images ----
# @app.route('/static/uploads/<size>/<filename>')
# def serve_image_sized(size, filename):
#     """Serve different sized images"""
#     if size not in ['thumbnails', 'medium', 'large']:
#         return jsonify({"error": "Invalid size"}), 400
    
#     filename = secure_filename(filename)
#     folder = os.path.join(app.root_path, UPLOAD_FOLDER, size)
    
#     # Add error handling for missing files
#     file_path = os.path.join(folder, filename)
#     if not os.path.exists(file_path):
#         return jsonify({"error": "File not found"}), 404
    
#     return send_from_directory(folder, filename)

# # ========== Utility Functions ==========
# def is_valid_email(email):
#     return email.endswith("@rit.edu") or email.endswith("@g.rit.edu")

# def generate_verification_code(length=6):
#     return ''.join(random.choices(string.digits, k=length))

# def send_verification_email(to_email, code):
#     from_email = "noreply@unifamily.com"
#     subject = "Unifamily Email Verification"
#     body = f"Your verification code is: {code}"
#     msg = MIMEText(body)
#     msg['Subject'] = subject
#     msg['From'] = from_email
#     msg['To'] = to_email
#     try:
#         with smtplib.SMTP('localhost', 1025) as server:
#             server.sendmail(from_email, [to_email], msg.as_string())
#         return True
#     except Exception as e:
#         print("Email sending failed:", e)
#         return False

# # ========== Auth Routes ==========
# @app.route('/register', methods=['POST'])
# def register():
#     """
#     User Registration (request verification code)
#     ---
#     tags:
#       - Auth
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           type: object
#           required:
#             - email
#             - password
#           properties:
#             email:
#               type: string
#               example: student@rit.edu
#             password:
#               type: string
#               example: secret123
#     responses:
#       200:
#         description: Verification code sent
#       400:
#         description: Invalid input or user exists
#       500:
#         description: Email sending failed
#     """
#     data = request.get_json()
#     email = data.get("email")
#     password = data.get("password")
#     if not email or not password:
#         return jsonify({"error": "Email and password required"}), 400
#     if not is_valid_email(email):
#         return jsonify({"error": "Only rit.edu or g.rit.edu emails allowed"}), 400
#     if users.find_one({"email": email}):
#         return jsonify({"error": "User already exists"}), 400
#     verification_code = generate_verification_code()
#     if not send_verification_email(email, verification_code):
#         return jsonify({"error": "Failed to send verification email"}), 500
#     users.insert_one({
#         "email": email,
#         "password": generate_password_hash(password),
#         "verified": False,
#         "verification_code": verification_code,
#         "status": "ACTIVE",
#         "created_at": datetime.now(timezone.utc)
#     })
#     return jsonify({"message": "Verification code sent to email"}), 200

# @app.route('/verify', methods=['POST'])
# def verify():
#     """
#     Verify User Email
#     ---
#     tags:
#       - Auth
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           type: object
#           required:
#             - email
#             - code
#           properties:
#             email:
#               type: string
#               example: student@rit.edu
#             code:
#               type: string
#               example: 123456
#     responses:
#       200:
#         description: User verified successfully
#       400:
#         description: Invalid email or code
#     """
#     data = request.get_json()
#     email = data.get("email", "").strip().lower()
#     code = data.get("code", "").strip()
#     if not email or not code:
#         return jsonify({"error": "Email and code required"}), 400
#     user = users.find_one({"email": email})
#     if not user:
#         return jsonify({"error": "User not found"}), 400
#     if user.get("verified"):
#         return jsonify({"message": "User already verified"}), 200
#     if str(user.get("verification_code", "")) != code:
#         return jsonify({"error": "Invalid verification code"}), 400
#     users.update_one({"email": email}, {"$set": {"verified": True}, "$unset": {"verification_code": ""}})
#     return jsonify({"message": "User verified successfully"}), 200

# @app.route('/login', methods=['POST'])
# def login():
#     """
#     User Login with Refresh Token
#     ---
#     tags:
#       - Auth
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           type: object
#           required:
#             - email
#             - password
#           properties:
#             email:
#               type: string
#               example: student@rit.edu
#             password:
#               type: string
#               example: secret123
#     responses:
#       200:
#         description: Login successful with JWT tokens
#       401:
#         description: Invalid credentials or not verified
#     """
#     data = request.get_json()
#     email = data.get("email")
#     password = data.get("password")
    
#     user = users.find_one({"email": email})
#     if not user or not check_password_hash(user["password"], password):
#         return jsonify({"error": "Invalid email or password"}), 401
    
#     if not user.get("verified"):
#         return jsonify({"error": "Please verify your email first"}), 401
    
#     # Create both access and refresh tokens
#     access_token = create_access_token(identity=email)
#     refresh_token = create_refresh_token(identity=email)
    
#     return jsonify({
#         "message": "Login successful",
#         "user_id": str(user["_id"]),
#         "token": access_token,
#         "refreshToken": refresh_token
#     }), 200

# @app.route('/logout', methods=['POST'])
# @jwt_required()
# def logout():
#     """
#     Logout and blacklist current token
#     ---
#     tags:
#       - Auth
#     security:
#       - Bearer: []
#     responses:
#       200:
#         description: Successfully logged out
#     """
#     jti = get_jwt()['jti']  # JWT ID
#     blacklisted_tokens.add(jti)
#     return jsonify({"message": "Successfully logged out"}), 200


# @app.route('/refresh', methods=['POST'])
# @jwt_required(refresh=True)
# def refresh():
#     """
#     Refresh Access Token
#     ---
#     tags:
#       - Auth
#     security:
#       - Bearer: []
#     responses:
#       200:
#         description: New access token generated
#       401:
#         description: Invalid refresh token
#     """
#     current_user = get_jwt_identity()
#     new_token = create_access_token(identity=current_user)
#     return jsonify({
#         "token": new_token
#     }), 200

# # ========== User CRUD Routes ==========
# @app.route("/api/users", methods=["POST"])
# @jwt_required()
# def create_user():
#     """
#     Create or Reactivate User
#     ---
#     tags:
#       - Users
#     security:
#       - Bearer: []
#     parameters:
#       - in: body
#         name: body
#         schema:
#           type: object
#           properties:
#             name:
#               type: string
#               example: John Doe
#             college:
#               type: string
#               example: RIT
#             department:
#               type: string
#               example: CS
#     responses:
#       200:
#         description: User created or reactivated
#       401:
#         description: Unauthorized
#     """
#     email = get_jwt_identity()
#     existing_user = users.find_one({"email": email})
#     if existing_user:
#       update_fields = {
#           "name": request.json.get("name"),
#           "college": request.json.get("college"),
#           "department": request.json.get("department")
#       }
#       # remove None values
#       update_fields = {k: v for k, v in update_fields.items() if v}

#       if update_fields:
#           users.update_one({"_id": existing_user["_id"]}, {"$set": update_fields})

#       if existing_user.get("status") == "DELETED":
#           users.update_one({"_id": existing_user["_id"]}, {"$set": {"status": "ACTIVE"}})

#       updated_user = users.find_one({"_id": existing_user["_id"]})
#       updated_user["_id"] = str(updated_user["_id"])
#       return jsonify(updated_user), 200
#     user_data = {
#         "email": email,
#         "name": request.json.get("name"),
#         "college": request.json.get("college"),
#         "department": request.json.get("department"),
#         "created_at": datetime.now(timezone.utc),
#         "status": "ACTIVE",
#         "verified": True
#     }
#     result = users.insert_one(user_data)
#     new_user = users.find_one({"_id": result.inserted_id})
#     new_user["_id"] = str(new_user["_id"])
#     return jsonify(new_user), 200

# @app.route("/api/users", methods=["PATCH"])
# @jwt_required()
# def update_user():
#     """
#     Update User Details
#     ---
#     tags:
#       - Users
#     security:
#       - Bearer: []
#     parameters:
#       - in: body
#         name: body
#         schema:
#           type: object
#           properties:
#             name:
#               type: string
#               example: Jane Doe
#             college:
#               type: string
#               example: RIT
#             department:
#               type: string
#               example: CS
#     responses:
#       200:
#         description: User updated successfully
#       400:
#         description: No fields provided
#       404:
#         description: User not found
#     """
#     email = get_jwt_identity()
#     existing_user = users.find_one({"email": email})
#     if not existing_user:
#         return jsonify({"error": "User not found"}), 404
#     data = request.get_json()
#     update_fields = {k: v for k, v in data.items() if k in ["name","college","department"] and v}
#     if not update_fields:
#         return jsonify({"error": "No fields provided"}), 400
#     users.update_one({"_id": existing_user["_id"]}, {"$set": update_fields})
#     updated_user = users.find_one({"_id": existing_user["_id"]})
#     updated_user["_id"] = str(updated_user["_id"])
#     return jsonify(updated_user), 200

# @app.route("/api/users/me", methods=["GET"])
# @jwt_required()
# def get_user():
#     """
#     Get Current User
#     ---
#     tags:
#       - Users
#     security:
#       - Bearer: []
#     responses:
#       200:
#         description: Returns current user object
#       404:
#         description: User not found
#     """
#     email = get_jwt_identity()
#     user = users.find_one({"email": email})
#     if not user:
#         return jsonify({"error": "User not found"}), 404
#     user["_id"] = str(user["_id"])
#     return jsonify(user), 200

# # ========== Post CRUD Routes ==========

# # Detect Spam:
# def async_moderate_post_with_spam_detection(post_id, post_data, images, posts):
#     """
#     Enhanced moderation function that includes spam detection
#     """
#     try:
#         # Step 1: Spam detection
#         category_map = {
#             'ROOMMATE': 'roommate',
#             'SELL': 'sell', 
#             'CARPOOL': 'carpool'
#         }
        
#         spam_category = category_map.get(post_data.get('category', ''), 'general')
#         print(f"[DEBUG] Async moderation started for {post_id}")
        
#         # Prepare context for spam detection
#         spam_context = {
#             'price': post_data.get('price'),
#             'rent': post_data.get('rent'),
#             'location': post_data.get('community') or post_data.get('from_location'),
#             'user_email': post_data.get('owner')
#         }
        
#         # Check title and description for spam
#         title_spam = spam_detector.detect_spam(
#             post_data.get('title', ''), 
#             spam_category, 
#             **spam_context
#         )
#         description_spam = spam_detector.detect_spam(
#             post_data.get('description', ''), 
#             spam_category, 
#             **spam_context
#         )
        
#         # Combine spam analysis
#         is_spam = title_spam['is_spam'] or description_spam['is_spam']
#         spam_confidence = max(title_spam['confidence'], description_spam['confidence'])
#         all_reasons = title_spam['reasons'] + description_spam['reasons']
        
#         if is_spam:
            
#             # Update post status to FAILED due to spam
#             posts.update_one(
#                 {"_id": post_id}, 
#                 {"$set": {
#                     "status": PostStatus.FAILED.value,
#                     "moderation_reason": "Flagged as spam",
#                     "spam_analysis": {
#                         "is_spam": True,
#                         "confidence": spam_confidence,
#                         "reasons": all_reasons,
#                         "title_analysis": title_spam,
#                         "description_analysis": description_spam,
#                         "detected_at": datetime.now(timezone.utc)
#                     },
#                     "moderation_completed_at": datetime.now(timezone.utc)
#                 }}
#             )
#             return
#         # Step 2: Log successful spam check
#         # logger.info(f"Post {post_id} passed spam detection. Confidence: {spam_confidence:.3f}")
#         print(f"[DEBUG] Post {post_id} passed spam detection. Confidence: {spam_confidence:.3f}")

#         update_data = {
#             "status": PostStatus.PUBLISHED.value,
#             "moderation_passed_at": datetime.now(timezone.utc),
#             "spam_analysis": {
#                 "is_spam": False,
#                 "confidence": spam_confidence,
#                 "title_analysis": title_spam,
#                 "description_analysis": description_spam,
#                 "checked_at": datetime.now(timezone.utc)
#             }
#         }

#         posts.update_one({"_id": post_id}, {"$set": update_data})
#         # logger.info(f"Post {post_id} successfully moderated and published")
#         print(f"[DEBUG] Post {post_id} successfully moderated and published")
#         print(f"[DEBUG] Async moderation finished for {post_id}")
#     except Exception as e:
#         # logger.error(f"Moderation error for post {post_id}: {e}")
#         print(f"[ERROR] Moderation failed for {post_id}: {e}")
#         posts.update_one(
#             {"_id": post_id}, 
#             {"$set": {
#                 "status": PostStatus.FAILED.value,
#                 "moderation_error": str(e),
#                 "failed_at": datetime.now(timezone.utc)
#             }}
#         )

# @app.route("/api/posts", methods=["POST"])
# @jwt_required()
# def create_post():
#     """
#     Create a new post with enhanced spam detection
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           type: object
#           required:
#             - category
#             - title
#             - description
#           properties:
#             category:
#               type: string
#               enum: [ROOMMATE, SELL, CARPOOL]
#             title:
#               type: string
#               example: Need a roommate near campus
#             description:
#               type: string
#               example: Looking for a roommate starting Fall 2025
#             images:
#               type: array
#               items:
#                 type: string
#                 description: Base64 encoded images
#             community:
#               type: string
#             rent:
#               type: number
#             start_date:
#               type: string
#               example: 2025-09-01
#             gender_preference:
#               type: string
#               enum: [MALE, FEMALE, ANY]
#             preferences:
#               type: array
#               items:
#                 type: string
#             price:
#               type: number
#             item:
#               type: string
#             sub_category:
#               type: string
#               enum: [BOOKS, FURNITURE, ELECTRONICS, KITCHEN, OTHER]
#             from_location:
#               type: string
#             to_location:
#               type: string
#             departure_time:
#               type: string
#               example: 2025-09-05T08:30:00
#             seats_available:
#               type: integer
#     responses:
#       202:
#         description: Post created and under moderation
#       400:
#         description: Missing fields, validation error, or spam detected
#     """
#     user_email = get_jwt_identity()
#     data = request.get_json()

#     # Validate required fields
#     for f in ["category", "title", "description"]:
#         if f not in data:
#             return jsonify({"error": f"{f} is required"}), 400

#     # Quick spam pre-check before processing
#     category_map = {
#         'ROOMMATE': 'roommate',
#         'SELL': 'sell', 
#         'CARPOOL': 'carpool'
#     }
#     spam_category = category_map.get(data['category'], 'general')
    
#     # Prepare context for spam detection
#     spam_context = {
#         'price': data.get('price'),
#         'rent': data.get('rent'),
#         'location': data.get('community') or data.get('from_location'),
#         'user_email': user_email
#     }
    
#     # Pre-check for obvious spam
#     title_spam = spam_detector.detect_spam(
#         data.get('title', ''), 
#         spam_category, 
#         **spam_context
#     )
#     description_spam = spam_detector.detect_spam(
#         data.get('description', ''), 
#         spam_category, 
#         **spam_context
#     )
    
#     # Reject immediately if very high spam confidence
#     max_confidence = max(title_spam['confidence'], description_spam['confidence'])
#     if max_confidence > 0.85:
#         all_reasons = title_spam['reasons'] + description_spam['reasons']
#         logger.warning(f"Post rejected at submission - spam confidence: {max_confidence:.3f}")
#         logger.warning(f"User: {user_email}, Reasons: {', '.join(all_reasons)}")
        
#         return jsonify({
#             "error": "Post content violates community guidelines",
#             "details": "Your post has been flagged for review. Please ensure your content follows our community standards.",
#             "spam_confidence": max_confidence
#         }), 400
    
#     # Create base post object
#     post = {
#         "owner": user_email,
#         "category": data["category"],
#         "title": data["title"],
#         "description": data["description"],
#         "status": PostStatus.PROCESSING.value,
#         "created_at": datetime.now(timezone.utc),
#         "images": []  # Will store image metadata
#     }

#     # Insert post first to get ID
#     result = posts.insert_one(post)
#     post_id = str(result.inserted_id)
    
#     # Process images if provided
#     image_metadata = []
#     if data.get("images") and len(data["images"]) > 0:
#         try:
#             for base64_image in data["images"]:
#                 if base64_image:  # Skip empty strings
#                     image_info = save_image_from_base64(base64_image, post_id)
#                     image_metadata.append({
#                         'image_id': image_info['image_id'],
#                         'filename': image_info['filename'],
#                         'urls': image_info['urls'],
#                         'uploaded_at': datetime.now(timezone.utc)
#                     })
                    
#         except Exception as e:
#             # Clean up post if image processing fails
#             posts.delete_one({"_id": result.inserted_id})
#             # Also clean up any images that were successfully processed
#             if image_metadata:
#                 delete_post_images(image_metadata)
#             return jsonify({"error": f"Image processing failed: {str(e)}"}), 400

#     # Category-specific validation and field assignment
#     try:
#         if data["category"] == PostCategory.ROOMMATE.value:
#             # Required fields for ROOMMATE
#             required_fields = ["community", "rent", "start_date"]
#             for f in required_fields:
#                 if f not in data or not data[f]:
#                     posts.delete_one({"_id": result.inserted_id})
#                     delete_post_images(image_metadata)
#                     return jsonify({"error": f"{f} is required for ROOMMATE"}), 400
            
#             # Parse and validate start_date
#             try:
#                 start_date = datetime.fromisoformat(data["start_date"])
#             except ValueError:
#                 posts.delete_one({"_id": result.inserted_id})
#                 delete_post_images(image_metadata)
#                 return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
                
#             post.update({
#                 "community": data["community"],
#                 "rent": float(data["rent"]),
#                 "start_date": start_date,
#                 "gender_preference": data.get("gender_preference", "ANY"),
#                 "preferences": data.get("preferences", [])
#             })

#         elif data["category"] == PostCategory.SELL.value:
#             # Required fields for SELL
#             required_fields = ["price", "item"]
#             for f in required_fields:
#                 if f not in data or not data[f]:
#                     posts.delete_one({"_id": result.inserted_id})
#                     delete_post_images(image_metadata)
#                     return jsonify({"error": f"{f} is required for SELL"}), 400
            
#             post.update({
#                 "price": float(data["price"]),
#                 "item": data["item"],
#                 "sub_category": data.get("sub_category", "OTHER")
#             })

#         elif data["category"] == PostCategory.CARPOOL.value:
#             # Required fields for CARPOOL
#             required_fields = ["from_location", "to_location", "departure_time"]
#             for f in required_fields:
#                 if f not in data or not data[f]:
#                     posts.delete_one({"_id": result.inserted_id})
#                     delete_post_images(image_metadata)
#                     return jsonify({"error": f"{f} is required for CARPOOL"}), 400
            
#             # Parse and validate departure_time
#             try:
#                 departure_time = datetime.fromisoformat(data["departure_time"])
#             except ValueError:
#                 posts.delete_one({"_id": result.inserted_id})
#                 delete_post_images(image_metadata)
#                 return jsonify({"error": "Invalid departure_time format. Use YYYY-MM-DDTHH:MM:SS"}), 400
                
#             post.update({
#                 "from_location": data["from_location"],
#                 "to_location": data["to_location"],
#                 "departure_time": departure_time,
#                 "seats_available": int(data.get("seats_available", 1))
#             })
#         else:
#             posts.delete_one({"_id": result.inserted_id})
#             delete_post_images(image_metadata)
#             return jsonify({"error": "Invalid category"}), 400

#     except ValueError as ve:
#         posts.delete_one({"_id": result.inserted_id})
#         delete_post_images(image_metadata)
#         return jsonify({"error": f"Invalid data format: {str(ve)}"}), 400
#     except Exception as e:
#         posts.delete_one({"_id": result.inserted_id})
#         delete_post_images(image_metadata)
#         return jsonify({"error": f"Validation error: {str(e)}"}), 400

#     # Update post with all data including images
#     update_data = {**post, "images": image_metadata}
#     posts.update_one({"_id": result.inserted_id}, {"$set": update_data})
    
#     # Start async moderation with spam detection
#     images = data.get("images", [])
#     threading.Thread(
#         target=async_moderate_post_with_spam_detection,
#         args=(result.inserted_id, post, images, posts),
#         daemon=True
#     ).start()
    
#     return jsonify({
#         "message": "Post submitted successfully and is under moderation",
#         "post_id": post_id,
#         "status": "PROCESSING",
#         "images_uploaded": len(image_metadata)
#     }), 202

# # New endpoint to check moderation status
# @app.route("/api/posts/<string:post_id>/moderation-status", methods=["GET"])
# @jwt_required()
# def get_moderation_status(post_id):
#     """
#     Get detailed moderation status of a post
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - name: post_id
#         in: path
#         required: true
#         type: string
#     responses:
#       200:
#         description: Moderation status returned
#       404:
#         description: Post not found
#       403:
#         description: Unauthorized - not post owner
#     """
#     user_email = get_jwt_identity()
    
#     try:
#         post = posts.find_one({"_id": ObjectId(post_id)})
#     except:
#         return jsonify({"error": "Invalid ID"}), 400

#     if not post:
#         return jsonify({"error": "Post not found"}), 404
    
#     # Only allow owner to see detailed moderation info
#     if post["owner"] != user_email:
#         return jsonify({"error": "Unauthorized - only post owner can view moderation details"}), 403
    
#     moderation_info = {
#         "post_id": post_id,
#         "status": post["status"],
#         "created_at": post["created_at"],
#         "moderation_reason": post.get("moderation_reason", ""),
#         "moderation_passed_at": post.get("moderation_passed_at"),
#         "moderation_completed_at": post.get("moderation_completed_at"),
#         "failed_at": post.get("failed_at"),
#         "moderation_error": post.get("moderation_error", "")
#     }
    
#     # Include spam analysis if available
#     if "spam_analysis" in post:
#         moderation_info["spam_analysis"] = post["spam_analysis"]
    
#     return jsonify(moderation_info), 200


# # Optional: Endpoint to check if a text would be flagged as spam (for testing)
# @app.route("/api/posts/check-spam", methods=["POST"])
# @jwt_required()
# def check_spam():
#     """
#     Check if text would be flagged as spam (for testing purposes)
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - in: body
#         name: body
#         required: true
#         schema:
#           type: object
#           properties:
#             title:
#               type: string
#             description:
#               type: string
#             category:
#               type: string
#               enum: [ROOMMATE, SELL, CARPOOL]
#     responses:
#       200:
#         description: Spam analysis results
#     """
#     data = request.get_json()
    
#     title = data.get('title', '')
#     description = data.get('description', '')
#     category_map = {
#         'ROOMMATE': 'roommate',
#         'SELL': 'sell', 
#         'CARPOOL': 'carpool'
#     }
#     spam_category = category_map.get(data.get('category', ''), 'general')
    
#     # Analyze both title and description
#     title_result = spam_detector.detect_spam(title, spam_category)
#     description_result = spam_detector.detect_spam(description, spam_category)
    
#     # Combine results
#     max_confidence = max(title_result['confidence'], description_result['confidence'])
#     is_spam = title_result['is_spam'] or description_result['is_spam']
    
#     return jsonify({
#         "would_be_flagged": is_spam,
#         "max_confidence": max_confidence,
#         "title_analysis": {
#             "is_spam": title_result['is_spam'],
#             "confidence": title_result['confidence'],
#             "reasons": title_result['reasons']
#         },
#         "description_analysis": {
#             "is_spam": description_result['is_spam'],
#             "confidence": description_result['confidence'],
#             "reasons": description_result['reasons']
#         }
#     }), 200
    
# @app.route("/api/posts", methods=["GET"])
# @jwt_required()  
# def list_posts():
#     """
#     List all published posts for the feed (requires login)
#     ---
#     tags:
#       - Posts
#     parameters:
#       - name: page
#         in: query
#         type: integer
#       - name: limit
#         in: query
#         type: integer
#     responses:
#       200:
#         description: List of posts
#     """
#     page = int(request.args.get("page", 1))
#     limit = int(request.args.get("limit", 10))
#     skip = (page - 1) * limit

#     # Only show published posts
#     query = {"status": PostStatus.PUBLISHED.value}

#     cursor = posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
#     results = []
#     for p in cursor:
#         p["_id"] = str(p["_id"])
#         # Ensure images are included in response
#         if "images" not in p:
#             p["images"] = []
#         # Remove spam analysis details from public feed
#         if "spam_analysis" in p:
#             p["spam_analysis"] = {"is_spam": False}  # Only show basic info
#         results.append(p)

#     total = posts.count_documents(query)
#     return jsonify({"posts": results, "page": page, "limit": limit, "total": total}), 200


# @app.route("/api/posts/<string:post_id>", methods=["GET"])
# @jwt_required()
# def get_post(post_id):
#     """
#     Get a post by ID
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - name: post_id
#         in: path
#         required: true
#         type: string
#     responses:
#       200:
#         description: Post returned
#       404:
#         description: Not found
#     """
#     user_email = get_jwt_identity()
#     try:
#         post = posts.find_one({"_id": ObjectId(post_id)})
#     except:
#         return jsonify({"error": "Invalid ID"}), 400

#     if not post or post.get("status") == PostStatus.DELETED.value:
#         return jsonify({"error": "Post not found"}), 404

#     if post["status"] != PostStatus.PUBLISHED.value and post["owner"] != user_email:
#         return jsonify({"error": "Unauthorized"}), 403

#     post["_id"] = str(post["_id"])
#     # Ensure images are included in response
#     if "images" not in post:
#         post["images"] = []
    
#     # Remove detailed spam analysis unless it's the owner
#     if "spam_analysis" in post and post["owner"] != user_email:
#         post["spam_analysis"] = {"is_spam": False}
    
#     return jsonify(post), 200




# @app.route("/api/posts/<string:post_id>", methods=["PATCH"])
# @jwt_required()
# def update_post(post_id):
#     """
#     Update post status (PUBLISHED or CLOSED)
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - name: post_id
#         in: path
#         required: true
#         type: string
#       - in: body
#         name: body
#         schema:
#           type: object
#           properties:
#             status:
#               type: string
#               enum: [PUBLISHED, CLOSED]
#     """
#     user_email = get_jwt_identity()
#     try:
#         post = posts.find_one({"_id": ObjectId(post_id)})
#     except:
#         return jsonify({"error": "Invalid post ID"}), 400
        
#     if not post:
#         return jsonify({"error": "Post not found"}), 404
#     if post["owner"] != user_email:
#         return jsonify({"error": "Unauthorized"}), 403

#     status = request.json.get("status")
#     if status not in [PostStatus.PUBLISHED.value, PostStatus.CLOSED.value]:
#         return jsonify({"error": "Invalid status"}), 400

#     posts.update_one({"_id": post["_id"]}, {"$set": {"status": status}})
#     return jsonify({"message": f"Post updated to {status}"}), 200


# @app.route("/api/posts/<string:post_id>", methods=["DELETE"])
# @jwt_required()
# def delete_post(post_id):
#     """
#     Delete a post (soft delete)
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - name: post_id
#         in: path
#         required: true
#         type: string
#     """
#     user_email = get_jwt_identity()
    
#     try:
#         post = posts.find_one({"_id": ObjectId(post_id)})
#     except:
#         return jsonify({"error": "Invalid post ID"}), 400
        
#     if not post:
#         return jsonify({"error": "Post not found"}), 404
#     if post["owner"] != user_email:
#         return jsonify({"error": "Unauthorized"}), 403

#     # Delete associated images from filesystem
#     if post.get("images"):
#         delete_post_images(post["images"])

#     # Soft delete the post
#     posts.update_one({"_id": post["_id"]}, {"$set": {"status": PostStatus.DELETED.value}})
    
#     return jsonify({"message": "Post and associated images deleted"}), 200


# @app.route("/api/myposts", methods=["GET"])
# @jwt_required()
# def get_my_posts():
#     """
#     Get current user's posts with optional filters
#     ---
#     tags:
#       - Posts
#     security:
#       - Bearer: []
#     parameters:
#       - name: status
#         in: query
#         type: string
#       - name: category
#         in: query
#         type: string
#       - name: search
#         in: query
#         type: string
#       - name: page
#         in: query
#         type: integer
#       - name: limit
#         in: query
#         type: integer
#     """
#     user_email = get_jwt_identity()
#     query = {"owner": user_email, "status": {"$ne": PostStatus.DELETED.value}}

#     if request.args.get("status"):
#         query["status"] = request.args["status"]
#     if request.args.get("category"):
#         query["category"] = request.args["category"]

#     search = request.args.get("search")
#     if search:
#         query["$or"] = [
#             {"title": {"$regex": search, "$options": "i"}},
#             {"description": {"$regex": search, "$options": "i"}}
#         ]

#     page = int(request.args.get("page", 1))
#     limit = int(request.args.get("limit", 10))
#     skip = (page - 1) * limit

#     cursor = posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
#     results = []
#     for p in cursor:
#         p["_id"] = str(p["_id"])
#         # Ensure images are included in response
#         if "images" not in p:
#             p["images"] = []
#         results.append(p)

#     total = posts.count_documents(query)
#     return jsonify({"posts": results, "page": page, "limit": limit, "total": total}), 200

# # Add a route to get user info by email
# @app.route("/api/users/<email>", methods=["GET"])
# @jwt_required()
# def get_user_by_email(email):
#     """
#     Get user by email
#     ---
#     tags:
#       - Users
#     security:
#       - Bearer: []
#     parameters:
#       - name: email
#         in: path
#         required: true
#         type: string
#     responses:
#       200:
#         description: User found
#       404:
#         description: User not found
#     """
#     try:
#         # Decode URL-encoded email
#         decoded_email = email.replace('%40', '@')
#         user = users.find_one({"email": decoded_email, "status": {"$ne": "DELETED"}})
        
#         if not user:
#             return jsonify({"error": "User not found"}), 404
        
#         user["_id"] = str(user["_id"])
#         # Don't return sensitive information
#         user.pop("password", None)
#         user.pop("verification_code", None)
        
#         return jsonify(user), 200
        
#     except Exception as e:
#         return jsonify({"error": "Invalid request"}), 400

# @app.route("/api/posts/semanticsearch", methods=["POST"])
# def semantic_search():
#     data = request.json
#     query = data.get("query", "")

#     # Return dummy data so frontend doesn’t hang
#     sample_posts = [
#         {"_id": "1", "title": "Looking for a roommate", "content": "RIT student, near campus"},
#         {"_id": "2", "title": "Selling bike", "content": "Good condition, cheap"},
#     ]
#     return jsonify(sample_posts), 200

# if __name__ == '__main__':
#     app.run(debug=True, threaded=True, port=8080)
