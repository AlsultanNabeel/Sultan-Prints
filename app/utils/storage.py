import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
from werkzeug.utils import secure_filename
import secrets
from PIL import Image
import io
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class SpacesStorage:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SpacesStorage, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.client = None
        self.bucket_name = None
        self.region_name = None
        self.endpoint_url = None
        
    def init_app(self, app):
        """تهيئة التخزين مع إعدادات التطبيق"""
        self.bucket_name = app.config.get('SPACES_BUCKET_NAME')
        self.region_name = app.config.get('SPACES_REGION', 'fra1')
        self.endpoint_url = f'https://{self.region_name}.digitaloceanspaces.com'
        
        self.client = boto3.client('s3',
            region_name=self.region_name,
            endpoint_url=self.endpoint_url,
            aws_access_key_id=app.config.get('SPACES_KEY'),
            aws_secret_access_key=app.config.get('SPACES_SECRET')
        )
        
        logger.info(f"تم تهيئة SpacesStorage بنجاح - المنطقة: {self.region_name}, البكت: {self.bucket_name}")

    def save_image(self, file, folder='designs'):
        """حفظ الصورة في DigitalOcean Spaces"""
        if not file:
            return None

        try:
            # إنشاء اسم فريد للملف
            random_hex = secrets.token_hex(8)
            _, f_ext = os.path.splitext(secure_filename(file.filename))
            picture_fn = f"{random_hex}{f_ext}"
            
            # معالجة الصورة
            image = Image.open(file)
            image.verify()  # التحقق من صحة الصورة
            file.seek(0)  # إعادة تعيين المؤشر
            
            image = Image.open(file)
            # تحجيم الصورة
            image.thumbnail((1200, 1200), Image.LANCZOS)
            
            # تحويل الصورة إلى bytes
            img_byte_arr = io.BytesIO()
            if f_ext.lower() in ('.png', '.webp'):
                image.save(img_byte_arr, format=image.format, optimize=True)
            else:
                image.save(img_byte_arr, format=image.format, quality=90, optimize=True)
            img_byte_arr.seek(0)
            
            # المسار الكامل في Spaces
            spaces_path = f"uploads/{folder}/{picture_fn}"
            
            # رفع الملف إلى Spaces
            self.client.upload_fileobj(
                img_byte_arr,
                self.bucket_name,
                spaces_path,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': file.content_type
                }
            )
            
            # إرجاع المسار النسبي للصورة
            if self.endpoint_url:
                return f"https://{self.endpoint_url}/{spaces_path}"
            return f"https://{self.bucket_name}.{self.region_name}.digitaloceanspaces.com/{spaces_path}"
            
        except Exception as e:
            logger.error(f"Error saving image to Spaces: {str(e)}", exc_info=True)
            return None

    def delete_image(self, image_url):
        """حذف صورة من DigitalOcean Spaces"""
        try:
            # استخراج المسار من URL
            if self.endpoint_url and image_url.startswith(f"https://{self.endpoint_url}/"):
                key = image_url.replace(f"https://{self.endpoint_url}/", "")
            else:
                key = image_url.split(f"{self.bucket_name}.{self.region_name}.digitaloceanspaces.com/")[-1]
            
            # حذف الملف
            self.client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except Exception as e:
            logger.error(f"Error deleting image from Spaces: {str(e)}", exc_info=True)
            return False

# تهيئة كائن التخزين
spaces_storage = SpacesStorage()

def init_storage(app):
    """تهيئة التخزين مع تطبيق Flask"""
    spaces_storage.init_app(app) 