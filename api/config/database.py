from pymongo import MongoClient

# Global database connection
client = None
db = None
users = None
posts = None

def init_db(app):
    """Initialize MongoDB connection"""
    global client, db, users, posts
    
    client = MongoClient("mongodb://localhost:27017/")
    db = client["unicom_db"]
    users = db["users"]
    posts = db["posts"]
    
    app.db = db
    app.users = users
    app.posts = posts

def get_db():
    """Get database instance"""
    return db

def get_users_collection():
    """Get users collection"""
    return users

def get_posts_collection():
    """Get posts collection"""
    return posts