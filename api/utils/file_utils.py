import os
from flask import send_from_directory
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = os.path.join('static', 'uploads')

def setup_upload_directories():
    """Create upload directories if they don't exist"""
    directories = [
        UPLOAD_FOLDER,
        os.path.join(UPLOAD_FOLDER, 'thumbnails'),
        os.path.join(UPLOAD_FOLDER, 'medium'),
        os.path.join(UPLOAD_FOLDER, 'large')
    ]
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"Created directory: {directory}")

def serve_image_file(filename, size=None):
    """
    Serve image file from upload directory
    
    Args:
        filename: Name of the file to serve
        size: Size variant (thumbnails, medium, large) or None for original
        
    Returns:
        Flask send_from_directory response
    """
    filename = secure_filename(filename)
    
    if size:
        folder = os.path.join(UPLOAD_FOLDER, size)
    else:
        folder = UPLOAD_FOLDER
    
    file_path = os.path.join(folder, filename)
    if not os.path.exists(file_path):
        return None, 404
    
    return send_from_directory(folder, filename)