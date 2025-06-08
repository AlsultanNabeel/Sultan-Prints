from PIL import Image
import os
from flask import current_app
import uuid

class ImageOptimizer:
    def __init__(self, max_size=(800, 800), quality=85, format='JPEG'):
        self.max_size = max_size
        self.quality = quality
        self.format = format
    
    def optimize_image(self, image_path):
        """Optimize an image by resizing and compressing it"""
        try:
            # Open the image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if larger than max_size
                if img.size[0] > self.max_size[0] or img.size[1] > self.max_size[1]:
                    img.thumbnail(self.max_size, Image.Resampling.LANCZOS)
                
                # Save optimized image
                optimized_filename = f"opt_{uuid.uuid4().hex}_{os.path.basename(image_path)}"
                optimized_path = os.path.join(os.path.dirname(image_path), optimized_filename)
                
                img.save(optimized_path, 
                        format=self.format,
                        quality=self.quality,
                        optimize=True)
                
                # Replace original with optimized version
                os.remove(image_path)
                os.rename(optimized_path, image_path)
                
                return True
        except Exception as e:
            print(f"Error optimizing image: {e}")
            return False

class ImageHandler:
    @staticmethod
    def save_image(file, subfolder=''):
        """Save and optimize an uploaded image"""
        if file:
            # Create unique filename
            filename = f"{uuid.uuid4().hex}_{file.filename}"
            
            # Ensure upload folder exists
            upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)
            os.makedirs(upload_path, exist_ok=True)
            
            # Save file path
            file_path = os.path.join(upload_path, filename)
            
            # Save original file
            file.save(file_path)
            
            # Optimize image
            optimizer = ImageOptimizer()
            optimizer.optimize_image(file_path)
            
            # Return relative path for database
            return os.path.join('uploads', subfolder, filename)
        return None
    
    @staticmethod
    def delete_image(file_path):
        """Delete an image file"""
        try:
            full_path = os.path.join(current_app.config['UPLOAD_FOLDER'], file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
        except Exception as e:
            print(f"Error deleting image: {e}")
        return False

    @staticmethod
    def create_thumbnail(image_path, size=(200, 200)):
        """Create a thumbnail version of an image"""
        try:
            with Image.open(image_path) as img:
                thumb_path = f"{os.path.splitext(image_path)[0]}_thumb{os.path.splitext(image_path)[1]}"
                img.copy()
                img.thumbnail(size, Image.Resampling.LANCZOS)
                img.save(thumb_path, quality=85, optimize=True)
                return os.path.basename(thumb_path)
        except Exception as e:
            print(f"Error creating thumbnail: {e}")
            return None 