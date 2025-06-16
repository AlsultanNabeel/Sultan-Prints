import os
import datetime
import subprocess
import boto3
from botocore.exceptions import ClientError
import schedule
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

class DatabaseBackup:
    def __init__(self):
        self.backup_dir = 'backups'
        self.s3_bucket = os.environ.get('AWS_BACKUP_BUCKET')
        self.db_url = os.environ.get('DATABASE_URL')
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self):
        """Create a PostgreSQL backup"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.backup_dir}/sultan_prints_{timestamp}.sql"
        
        try:
            # استخدام pg_dump لإنشاء نسخة احتياطية
            command = [
                'pg_dump',
                '--dbname=' + self.db_url,
                '--format=custom',  # استخدام التنسيق المخصص لـ PostgreSQL
                '--file=' + backup_file
            ]
            
            subprocess.run(command, check=True)
            print(f"Local backup created: {backup_file}")
            return backup_file
        except subprocess.CalledProcessError as e:
            print(f"Error creating backup: {e}")
            return None
    
    def upload_to_s3(self, file_path):
        """Upload backup to S3"""
        if not self.s3_bucket:
            print("S3 bucket not configured, skipping upload")
            return
        
        try:
            s3 = boto3.client('s3')
            file_name = os.path.basename(file_path)
            
            # Upload file
            s3.upload_file(file_path, self.s3_bucket, f"database_backups/{file_name}")
            print(f"Backup uploaded to S3: {file_name}")
            
            # Delete local file after upload
            os.remove(file_path)
            print(f"Local backup deleted: {file_path}")
        except ClientError as e:
            print(f"Error uploading to S3: {e}")
    
    def cleanup_old_backups(self):
        """Delete backups older than retention period from S3"""
        if not self.s3_bucket:
            return
        
        try:
            s3 = boto3.client('s3')
            retention_days = int(os.environ.get('BACKUP_RETENTION_DAYS', 7))
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=retention_days)
            
            # List objects in bucket
            response = s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix='database_backups/'
            )
            
            # Delete old backups
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < cutoff_date:
                    s3.delete_object(
                        Bucket=self.s3_bucket,
                        Key=obj['Key']
                    )
                    print(f"Deleted old backup: {obj['Key']}")
        except ClientError as e:
            print(f"Error cleaning up old backups: {e}")
    
    def restore_backup(self, backup_file):
        """Restore database from backup"""
        try:
            # استخدام pg_restore لاستعادة النسخة الاحتياطية
            command = [
                'pg_restore',
                '--dbname=' + self.db_url,
                '--clean',  # تنظيف قاعدة البيانات قبل الاستعادة
                '--if-exists',  # تجاهل الأخطاء إذا كانت الكائنات غير موجودة
                backup_file
            ]
            
            subprocess.run(command, check=True)
            print(f"Database restored from backup: {backup_file}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error restoring backup: {e}")
            return False
    
    def run_backup(self):
        """Run the complete backup process"""
        backup_file = self.create_backup()
        if backup_file:
            self.upload_to_s3(backup_file)
            self.cleanup_old_backups()

def schedule_backups():
    """Schedule daily backups at 3 AM"""
    backup = DatabaseBackup()
    schedule.every().day.at("03:00").do(backup.run_backup)
    
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == '__main__':
    schedule_backups() 