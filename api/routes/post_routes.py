from flask import Blueprint, app, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from datetime import datetime, timezone
from bson import ObjectId

from config.database import get_posts_collection, get_users_collection
from models import PostStatus, PostCategory
from services.moderation_service import ModerationService
from utils.image_utils import save_image_from_base64, delete_post_images

post_bp = Blueprint('posts', __name__)
moderation_service = ModerationService()

@post_bp.route("/posts", methods=["POST"])
@jwt_required()
def create_post():
    """
    Create a new post with enhanced text and image moderation
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          required:
            - category
            - title
            - description
          properties:
            category:
              type: string
              enum: [ROOMMATE, SELL, CARPOOL]
            title:
              type: string
              example: Need a roommate near campus
            description:
              type: string
              example: Looking for a roommate starting Fall 2025
            images:
              type: array
              items:
                type: string
                description: Base64 encoded images
            community:
              type: string
            rent:
              type: number
            start_date:
              type: string
              example: 2025-09-01
            gender_preference:
              type: string
              enum: [MALE, FEMALE, ANY]
            preferences:
              type: array
              items:
                type: string
            price:
              type: number
            item:
              type: string
            sub_category:
              type: string
              enum: [BOOKS, FURNITURE, ELECTRONICS, KITCHEN, OTHER]
            from_location:
              type: string
            to_location:
              type: string
            departure_time:
              type: string
              example: 2025-09-05T08:30:00
            seats_available:
              type: integer
    responses:
      202:
        description: Post created and under moderation
      400:
        description: Missing fields, validation error, or content flagged
    """
    posts = get_posts_collection()
    user_email = get_jwt_identity()
    data = request.get_json()

    # Validate required fields
    for f in ["category", "title", "description"]:
        if f not in data:
            return jsonify({"error": f"{f} is required"}), 400

    # Quick pre-check for obvious spam/inappropriate content
    quick_check = moderation_service.check_spam_preview(
        data.get('title', ''),
        data.get('description', ''),
        data['category']
    )
    
    # Reject immediately if very high confidence of violation
    if quick_check['confidence'] > 0.85:
        print(f"[WARNING] Post rejected at submission - confidence: {quick_check['confidence']:.3f}")
        print(f"User: {user_email}, Issues: {', '.join(quick_check['issues'])}")
        
        return jsonify({
            "error": "Post content violates community guidelines",
            "details": "Your post has been flagged for review. Please ensure your content follows our community standards.",
            "confidence": quick_check['confidence']
        }), 400
    
    # Create base post object
    post = {
        "owner": user_email,
        "category": data["category"],
        "title": data["title"],
        "description": data["description"],
        "status": PostStatus.PROCESSING.value,
        "created_at": datetime.now(timezone.utc),
        "images": []
    }

    # Insert post first to get ID
    result = posts.insert_one(post)
    post_id = str(result.inserted_id)
    
    # Process images if provided
    image_metadata = []
    if data.get("images") and len(data["images"]) > 0:
        try:
            for base64_image in data["images"]:
                if base64_image:
                    image_info = save_image_from_base64(base64_image, post_id)
                    image_metadata.append({
                        'image_id': image_info['image_id'],
                        'filename': image_info['filename'],
                        'urls': image_info['urls'],
                        'uploaded_at': datetime.now(timezone.utc)
                    })
                    
        except Exception as e:
            posts.delete_one({"_id": result.inserted_id})
            if image_metadata:
                delete_post_images(image_metadata)
            return jsonify({"error": f"Image processing failed: {str(e)}"}), 400

    # Category-specific validation
    try:
        if data["category"] == PostCategory.ROOMMATE.value:
            required_fields = ["community", "rent", "start_date"]
            for f in required_fields:
                if f not in data or not data[f]:
                    posts.delete_one({"_id": result.inserted_id})
                    delete_post_images(image_metadata)
                    return jsonify({"error": f"{f} is required for ROOMMATE"}), 400
            
            try:
                start_date = datetime.fromisoformat(data["start_date"])
            except ValueError:
                posts.delete_one({"_id": result.inserted_id})
                delete_post_images(image_metadata)
                return jsonify({"error": "Invalid start_date format. Use YYYY-MM-DD"}), 400
                
            post.update({
                "community": data["community"],
                "rent": float(data["rent"]),
                "start_date": start_date,
                "gender_preference": data.get("gender_preference", "ANY"),
                "preferences": data.get("preferences", [])
            })

        elif data["category"] == PostCategory.SELL.value:
            required_fields = ["price", "item"]
            for f in required_fields:
                if f not in data or not data[f]:
                    posts.delete_one({"_id": result.inserted_id})
                    delete_post_images(image_metadata)
                    return jsonify({"error": f"{f} is required for SELL"}), 400
            
            post.update({
                "price": float(data["price"]),
                "item": data["item"],
                "sub_category": data.get("sub_category", "OTHER")
            })

        elif data["category"] == PostCategory.CARPOOL.value:
            required_fields = ["from_location", "to_location", "departure_time"]
            for f in required_fields:
                if f not in data or not data[f]:
                    posts.delete_one({"_id": result.inserted_id})
                    delete_post_images(image_metadata)
                    return jsonify({"error": f"{f} is required for CARPOOL"}), 400
            
            try:
                departure_time = datetime.fromisoformat(data["departure_time"])
            except ValueError:
                posts.delete_one({"_id": result.inserted_id})
                delete_post_images(image_metadata)
                return jsonify({"error": "Invalid departure_time format"}), 400
                
            post.update({
                "from_location": data["from_location"],
                "to_location": data["to_location"],
                "departure_time": departure_time,
                "seats_available": int(data.get("seats_available", 1))
            })
        else:
            posts.delete_one({"_id": result.inserted_id})
            delete_post_images(image_metadata)
            return jsonify({"error": "Invalid category"}), 400

    except (ValueError, TypeError) as e:
        posts.delete_one({"_id": result.inserted_id})
        delete_post_images(image_metadata)
        return jsonify({"error": f"Validation error: {str(e)}"}), 400

    # Update post with all data including images
    update_data = {**post, "images": image_metadata}
    posts.update_one({"_id": result.inserted_id}, {"$set": update_data})
    
    # Start async moderation (both text and images)
    images = data.get("images", [])
    moderation_service.moderate_post_async(result.inserted_id, post, images)
    
    return jsonify({
        "message": "Post submitted successfully and is under moderation",
        "post_id": post_id,
        "status": "PROCESSING",
        "images_uploaded": len(image_metadata)
    }), 202

@post_bp.route("/posts/<string:post_id>/moderation-status", methods=["GET"])
@jwt_required()
def get_moderation_status(post_id):
    """
    Get detailed moderation status of a post
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Moderation status returned
      404:
        description: Post not found
      403:
        description: Unauthorized - not post owner
    """
    posts = get_posts_collection()
    user_email = get_jwt_identity()
    
    try:
        post = posts.find_one({"_id": ObjectId(post_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400

    if not post:
        return jsonify({"error": "Post not found"}), 404
    
    if post["owner"] != user_email:
        return jsonify({"error": "Unauthorized - only post owner can view moderation details"}), 403
    
    moderation_info = {
        "post_id": post_id,
        "status": post["status"],
        "created_at": post["created_at"],
        "moderation_reason": post.get("moderation_reason", ""),
        "moderation_passed_at": post.get("moderation_passed_at"),
        "moderation_completed_at": post.get("moderation_completed_at"),
        "failed_at": post.get("failed_at"),
        "moderation_error": post.get("moderation_error", "")
    }
    
    if "moderation_analysis" in post:
        moderation_info["moderation_analysis"] = post["moderation_analysis"]
    
    return jsonify(moderation_info), 200

@post_bp.route("/posts/check-spam", methods=["POST"])
@jwt_required()
def check_spam():
    """
    Check if text would be flagged (for testing purposes)
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            title:
              type: string
            description:
              type: string
            category:
              type: string
              enum: [ROOMMATE, SELL, CARPOOL]
    responses:
      200:
        description: List of posts
    """
    posts = get_posts_collection()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    query = {"status": PostStatus.PUBLISHED.value}

    cursor = posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
    results = []
    for p in cursor:
        p["_id"] = str(p["_id"])
        if "images" not in p:
            p["images"] = []
        # Remove detailed moderation info from public feed
        if "moderation_analysis" in p:
            p["moderation_analysis"] = {"passed": True}
        results.append(p)

    total = posts.count_documents(query)
    return jsonify({"posts": results, "page": page, "limit": limit, "total": total}), 200

@post_bp.route("/posts/<string:post_id>", methods=["GET"])
@jwt_required()
def get_post(post_id):
    """
    Get a post by ID
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        required: true
        type: string
    responses:
      200:
        description: Post returned
      404:
        description: Not found
    """
    posts = get_posts_collection()
    user_email = get_jwt_identity()
    
    try:
        post = posts.find_one({"_id": ObjectId(post_id)})
    except:
        return jsonify({"error": "Invalid ID"}), 400

    if not post or post.get("status") == PostStatus.DELETED.value:
        return jsonify({"error": "Post not found"}), 404

    if post["status"] != PostStatus.PUBLISHED.value and post["owner"] != user_email:
        return jsonify({"error": "Unauthorized"}), 403

    post["_id"] = str(post["_id"])
    if "images" not in post:
        post["images"] = []
    
    # Remove detailed moderation analysis unless owner
    if "moderation_analysis" in post and post["owner"] != user_email:
        post["moderation_analysis"] = {"passed": True}
    
    return jsonify(post), 200

@post_bp.route("/posts/<string:post_id>", methods=["PATCH"])
@jwt_required()
def update_post(post_id):
    """
    Update post status (PUBLISHED or CLOSED)
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        required: true
        type: string
      - in: body
        name: body
        schema:
          type: object
          properties:
            status:
              type: string
              enum: [PUBLISHED, CLOSED]
    """
    posts = get_posts_collection()
    user_email = get_jwt_identity()
    
    try:
        post = posts.find_one({"_id": ObjectId(post_id)})
    except:
        return jsonify({"error": "Invalid post ID"}), 400
        
    if not post:
        return jsonify({"error": "Post not found"}), 404
    if post["owner"] != user_email:
        return jsonify({"error": "Unauthorized"}), 403

    status = request.json.get("status")
    if status not in [PostStatus.PUBLISHED.value, PostStatus.CLOSED.value]:
        return jsonify({"error": "Invalid status"}), 400

    posts.update_one({"_id": post["_id"]}, {"$set": {"status": status}})
    return jsonify({"message": f"Post updated to {status}"}), 200

@post_bp.route("/posts/<string:post_id>", methods=["DELETE"])
@jwt_required()
def delete_post(post_id):
    """
    Delete a post (soft delete)
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - name: post_id
        in: path
        required: true
        type: string
    """
    posts = get_posts_collection()
    user_email = get_jwt_identity()
    
    try:
        post = posts.find_one({"_id": ObjectId(post_id)})
    except:
        return jsonify({"error": "Invalid post ID"}), 400
        
    if not post:
        return jsonify({"error": "Post not found"}), 404
    if post["owner"] != user_email:
        return jsonify({"error": "Unauthorized"}), 403

    # Delete associated images from filesystem
    if post.get("images"):
        delete_post_images(post["images"])

    # Soft delete the post
    posts.update_one({"_id": post["_id"]}, {"$set": {"status": PostStatus.DELETED.value}})
    
    return jsonify({"message": "Post and associated images deleted"}), 200

@post_bp.route("/myposts", methods=["GET"])
@jwt_required()
def get_my_posts():
    """
    Get current user's posts with optional filters
    ---
    tags:
      - Posts
    security:
      - Bearer: []
    parameters:
      - name: status
        in: query
        type: string
      - name: category
        in: query
        type: string
      - name: search
        in: query
        type: string
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    """
    posts = get_posts_collection()
    user_email = get_jwt_identity()
    query = {"owner": user_email, "status": {"$ne": PostStatus.DELETED.value}}

    if request.args.get("status"):
        query["status"] = request.args["status"]
    if request.args.get("category"):
        query["category"] = request.args["category"]

    search = request.args.get("search")
    if search:
        query["$or"] = [
            {"title": {"$regex": search, "$options": "i"}},
            {"description": {"$regex": search, "$options": "i"}}
        ]

    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    cursor = posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
    results = []
    for p in cursor:
        p["_id"] = str(p["_id"])
        if "images" not in p:
            p["images"] = []
        results.append(p)

    total = posts.count_documents(query)
    return jsonify({"posts": results, "page": page, "limit": limit, "total": total}), 200

@post_bp.route("/posts/semanticsearch", methods=["POST"])
def semantic_search():
    """
    Semantic search placeholder
    ---
    tags:
      - Posts
    parameters:
      - in: body
        name: body
        schema:
          type: object
          properties:
            query:
              type: string
    """
    data = request.json
    query = data.get("query", "")

    # Return dummy data so frontend doesn't hang
    sample_posts = [
        {"_id": "1", "title": "Looking for a roommate", "content": "RIT student, near campus"},
        {"_id": "2", "title": "Selling bike", "content": "Good condition, cheap"},
    ]
    return jsonify(sample_posts), 200

@post_bp.route("/posts", methods=["GET"])
@jwt_required()  
def list_posts():
    """
    List all published posts for the feed (requires login)
    ---
    tags:
      - Posts
    parameters:
      - name: page
        in: query
        type: integer
      - name: limit
        in: query
        type: integer
    responses:
      200:
        description: List of posts
    """
    posts = get_posts_collection()
    page = int(request.args.get("page", 1))
    limit = int(request.args.get("limit", 10))
    skip = (page - 1) * limit

    # Only show published posts
    query = {"status": PostStatus.PUBLISHED.value}

    cursor = posts.find(query).sort("created_at", -1).skip(skip).limit(limit)
    results = []
    for p in cursor:
        p["_id"] = str(p["_id"])
        # Ensure images are included in response
        if "images" not in p:
            p["images"] = []
        # Remove spam analysis details from public feed
        if "spam_analysis" in p:
            p["spam_analysis"] = {"is_spam": False}  # Only show basic info
        results.append(p)

    total = posts.count_documents(query)
    return jsonify({"posts": results, "page": page, "limit": limit, "total": total}), 200
