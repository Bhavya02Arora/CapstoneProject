import os
import uuid
import base64
from PIL import Image
import io
from flask import current_app

# Configuration
UPLOAD_FOLDER = os.path.join('static', 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
IMAGE_SIZES = {
    'thumbnails': (150, 150),
    'medium': (500, 500),
    'large': (1200, 1200)
}

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_from_base64(base64_string, post_id):
    """
    Convert base64 to image file and save multiple sizes
    
    Args:
        base64_string: Base64 encoded image data
        post_id: ID of the post this image belongs to
        
    Returns:
        Dict with image_id, filename, and URLs for different sizes
    """
    try:
        if base64_string.startswith('data:image'):
            base64_string = base64_string.split(',')[1]

        image_data = base64.b64decode(base64_string)

        if len(image_data) > MAX_FILE_SIZE:
            raise ValueError("Image too large (max 5MB)")

        image = Image.open(io.BytesIO(image_data))

        image_id = uuid.uuid4().hex[:12]
        filename = f"{post_id}_{image_id}.jpg"

        if image.mode in ('RGBA', 'P'):
            image = image.convert('RGB')

        image_urls = {}

        for size_name, dimensions in IMAGE_SIZES.items():
            resized = image.copy()
            resized.thumbnail(dimensions, Image.Resampling.LANCZOS)

            # Save inside static/uploads/<size>/
            folder_path = os.path.join(UPLOAD_FOLDER, size_name)
            os.makedirs(folder_path, exist_ok=True)

            file_path = os.path.join(folder_path, filename)
            print(f"Saving {size_name} image to: {file_path}")

            resized.save(file_path, 'JPEG', quality=85, optimize=True)

            if not os.path.exists(file_path):
                raise ValueError(f"Failed to save image: {file_path}")

            # All URLs consistent: /static/uploads/<size>/<filename>
            image_urls[size_name] = f"/static/uploads/{size_name}/{filename}"

        return {
            'image_id': image_id,
            'filename': filename,
            'urls': image_urls
        }

    except Exception as e:
        print(f"Image processing error: {str(e)}")
        raise ValueError(f"Invalid image data: {str(e)}")

def delete_post_images(image_metadata_list):
    """
    Delete all image files when post is deleted
    
    Args:
        image_metadata_list: List of image metadata dictionaries
    """
    for image_meta in image_metadata_list:
        filename = image_meta.get('filename')
        if filename:
            # Delete all sizes
            for size_name in IMAGE_SIZES.keys():
                file_path = os.path.join(UPLOAD_FOLDER, size_name, filename)
                if os.path.exists(file_path):
                    try:
                        os.remove(file_path)
                        print(f"Deleted: {file_path}")
                    except Exception as e:
                        print(f"Error deleting {file_path}: {e}")