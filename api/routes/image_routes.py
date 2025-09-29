from flask import Blueprint, jsonify, current_app
from werkzeug.utils import secure_filename
from utils.file_utils import serve_image_file
import os

# Note: These routes should be registered in app.py if needed as separate blueprint
# Or can be added to post_routes.py

def register_image_routes(app):
    """Register image serving routes directly on the app"""
    
    @app.route('/static/uploads/<filename>')
    def serve_image(filename):
        """Serve uploaded images (large size)"""
        result, status = serve_image_file(filename)
        if status == 404:
            return jsonify({"error": "File not found"}), 404
        return result

    @app.route('/static/uploads/<size>/<filename>')
    def serve_image_sized(size, filename):
        """Serve different sized images"""
        if size not in ['thumbnails', 'medium', 'large']:
            return jsonify({"error": "Invalid size"}), 400
        
        result, status = serve_image_file(filename, size)
        if status == 404:
            return jsonify({"error": "File not found"}), 404
        return result