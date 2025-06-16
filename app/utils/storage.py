import os
import boto3
from botocore.exceptions import ClientError
from flask import current_app
from werkzeug.utils import secure_filename
import secrets
from PIL import Image
import io

class SpacesStorage:
    def __init__(self):
        self.spaces_client = boto3.client('s3',
            region_name=current_app.config.get('SPACES_REGION', 'fra1'),
            endpoint_url=f"https://{current_app.config.get('SPACES_REGION', 'fra1')}.digitaloceanspaces.com",
            aws_access_key_id=current_app.config.get('SPACES_KEY'),
            aws_secret_access_key=current_app.config.get('SPACES_SECRET')
        )
        self.bucket_name = current_app.config.get('SPACES_BUCKET')
        self.cdn_domain = current_app.config.get('SPACES_CDN_DOMAIN')

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
            self.spaces_client.upload_fileobj(
                img_byte_arr,
                self.bucket_name,
                spaces_path,
                ExtraArgs={
                    'ACL': 'public-read',
                    'ContentType': file.content_type
                }
            )
            
            # إرجاع المسار النسبي للصورة
            if self.cdn_domain:
                return f"https://{self.cdn_domain}/{spaces_path}"
            return f"https://{self.bucket_name}.{current_app.config.get('SPACES_REGION')}.digitaloceanspaces.com/{spaces_path}"
            
        except Exception as e:
            current_app.logger.error(f"Error saving image to Spaces: {str(e)}", exc_info=True)
            return None

    def delete_image(self, image_url):
        """حذف صورة من DigitalOcean Spaces"""
        try:
            # استخراج المسار من URL
            if self.cdn_domain and image_url.startswith(f"https://{self.cdn_domain}/"):
                key = image_url.replace(f"https://{self.cdn_domain}/", "")
            else:
                key = image_url.split(f"{self.bucket_name}.{current_app.config.get('SPACES_REGION')}.digitaloceanspaces.com/")[-1]
            
            # حذف الملف
            self.spaces_client.delete_object(
                Bucket=self.bucket_name,
                Key=key
            )
            return True
        except Exception as e:
            current_app.logger.error(f"Error deleting image from Spaces: {str(e)}", exc_info=True)
            return False

# إنشاء نسخة عامة من الكلاس
spaces_storage = SpacesStorage() 