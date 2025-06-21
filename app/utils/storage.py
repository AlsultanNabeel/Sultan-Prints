import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
from werkzeug.utils import secure_filename
import secrets
from PIL import Image
import io
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
        self.bucket_name = None
        self.region_name = None
        self.cdn_domain = None

    def init_app(self, app):
        """تهيئة التخزين مع إعدادات التطبيق الأساسية."""
        self.bucket_name = app.config.get('SPACES_BUCKET_NAME')
        self.region_name = app.config.get('SPACES_REGION')
        self.cdn_domain = app.config.get('SPACES_CDN_DOMAIN')

        if not all([self.bucket_name, self.region_name, app.config.get('SPACES_KEY'), app.config.get('SPACES_SECRET')]):
            logger.warning("DigitalOcean Spaces is not fully configured. File operations will be disabled.")
        else:
            logger.info(f"SpacesStorage initialized for bucket '{self.bucket_name}' in region '{self.region_name}'.")

    def _get_s3_client(self):
        """ينشئ عميل S3 جديد ومؤقت لضمان العزل بين الطلبات."""
        if not all([self.bucket_name, self.region_name]):
            logger.error("Spaces storage is not configured, cannot create S3 client.")
            return None
        
        return boto3.client('s3',
            region_name=self.region_name,
            endpoint_url=f'https://{self.region_name}.digitaloceanspaces.com',
            aws_access_key_id=current_app.config.get('SPACES_KEY'),
            aws_secret_access_key=current_app.config.get('SPACES_SECRET')
        )

    def save_image(self, file, folder='designs'):
        """حفظ الصورة في DigitalOcean Spaces باستخدام اتصال معزول."""
        s3_client = self._get_s3_client()
        if not file or not s3_client:
            return None

        try:
            random_hex = secrets.token_hex(16)
            _, f_ext = os.path.splitext(secure_filename(file.filename))
            picture_fn = f"{random_hex}{f_ext}"
            logger.info(f"DEBUG: Generated unique filename for upload: {picture_fn}")
            
            image = Image.open(file)
            image.thumbnail((1200, 1200), Image.Resampling.LANCZOS)
            
            img_byte_arr = io.BytesIO()
            image_format = image.format or 'JPEG'
            if image_format.upper() in ['PNG', 'WEBP']:
                image.save(img_byte_arr, format=image_format, optimize=True)
            else:
                image.save(img_byte_arr, format='JPEG', quality=90, optimize=True)
            img_byte_arr.seek(0)
            
            spaces_path = f"uploads/{folder}/{picture_fn}"
            
            s3_client.upload_fileobj(
                img_byte_arr,
                self.bucket_name,
                spaces_path,
                ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
            )
            
            final_url = ""
            if self.cdn_domain:
                final_url = f"https://{self.cdn_domain}/{spaces_path}"
            else:
                final_url = f"https://{self.bucket_name}.{self.region_name}.cdn.digitaloceanspaces.com/{spaces_path}"

            logger.info(f"DEBUG: Returning image URL from save_image: {final_url}")
            return final_url
            
        except Exception as e:
            logger.error(f"Error saving image to Spaces: {str(e)}", exc_info=True)
            return None

    def delete_image(self, image_url):
        """حذف صورة من DigitalOcean Spaces باستخدام اتصال معزول."""
        s3_client = self._get_s3_client()
        if not image_url or not s3_client:
            return False

        try:
            # استخراج المسار من أي نوع من الروابط (CDN أو مباشر)
            if 'digitaloceanspaces.com/' in image_url:
                key = image_url.split('digitaloceanspaces.com/')[1]
            else:
                # محاولة أخيرة إذا كان الرابط بدون اسم البكت
                key = image_url.split('/', 3)[-1]

            s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted image from Spaces: {key}")
            return True
        except Exception as e:
            logger.error(f"Error deleting image '{image_url}' from Spaces: {str(e)}", exc_info=True)
            return False

spaces_storage = SpacesStorage()

def init_storage(app):
    """تهيئة التخزين مع تطبيق Flask."""
    spaces_storage.init_app(app) 