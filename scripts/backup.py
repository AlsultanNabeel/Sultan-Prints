import os
import datetime
import subprocess
import boto3
from botocore.exceptions import ClientError
import schedule
import time

class DatabaseBackup:
    def __init__(self):
        self.backup_dir = 'backups'
        self.s3_bucket = os.environ.get('AWS_BACKUP_BUCKET')
        self.db_name = os.environ.get('DB_NAME', 'tshirt_shop')
        self.db_user = os.environ.get('DB_USER')
        self.db_password = os.environ.get('DB_PASSWORD')
        
        # Create backup directory if it doesn't exist
        if not os.path.exists(self.backup_dir):
            os.makedirs(self.backup_dir)
    
    def create_backup(self):
        """Create a MySQL backup"""
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = f"{self.backup_dir}/{self.db_name}_{timestamp}.sql"
        
        # MySQL dump command
        command = [
            'mysqldump',
            f'--user={self.db_user}',
            f'--password={self.db_password}',
            '--databases',
            self.db_name,
            f'--result-file={backup_file}'
        ]
        
        try:
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
        """Delete backups older than 7 days from S3"""
        if not self.s3_bucket:
            return
        
        try:
            s3 = boto3.client('s3')
            week_ago = datetime.datetime.now() - datetime.timedelta(days=7)
            
            # List objects in bucket
            response = s3.list_objects_v2(
                Bucket=self.s3_bucket,
                Prefix='database_backups/'
            )
            
            # Delete old backups
            for obj in response.get('Contents', []):
                if obj['LastModified'].replace(tzinfo=None) < week_ago:
                    s3.delete_object(
                        Bucket=self.s3_bucket,
                        Key=obj['Key']
                    )
                    print(f"Deleted old backup: {obj['Key']}")
        except ClientError as e:
            print(f"Error cleaning up old backups: {e}")
    
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

if __name__ == "__main__":
    schedule_backups() 