import boto3
import subprocess
import os
from datetime import datetime
from botocore.exceptions import ClientError
import json


def get_secret():
    secret_name = os.environ['DB_ADMIN_SECRET']
    print(f"Getting secret {secret_name}")

    session = boto3.session.Session()
    client = session.client('secretsmanager')

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
        secret = json.loads(get_secret_value_response['SecretString'])
        return secret
    except ClientError as e:
        raise e


def lambda_handler(event, context):
    # Get parameters from environment variables
    print("Start script to backup db")
    admin_secret = get_secret()
    print("Got secret")

    db_host = admin_secret['host']
    db_user = admin_secret['username']
    db_password = admin_secret['password']

    db_name = os.environ['DB_TO_BACKUP']
    bucket_name = os.environ['BUCKET_NAME']

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"/tmp/backup_{timestamp}.dump"
    s3_key = f"backups/backup_{timestamp}.dump"

    try:
        # Set environment variable for pg_dump
        os.environ['PGPASSWORD'] = db_password

        print("Create backup")
        # Create backup
        subprocess.run([
           'pg_dump',
           '-h', db_host,
           '-U', db_user,
           '-d', db_name,
           '-F', 'c',
           '-f', backup_file
        ], check=True
        )
        print("Backup created")

        # Upload to S3
        s3_client = boto3.client('s3')
        s3_client.upload_file(
           backup_file,
           bucket_name,
           s3_key
        )

        print("File uploaded to S3")

        return {
            'statusCode': 200,
            'body': f'Backup successfully created and uploaded to S3: {s3_key}'
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Backup failed: {str(e)}'
        }
