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

    db_host = admin_secret['host']
    db_user = admin_secret['username']
    db_password = admin_secret['password']

    db_name = os.environ['DB_TO_BACKUP']
    bucket_name = os.environ['BUCKET_NAME']
    lambda_name = os.environ['LAMBDA_NAME']

    if not (db_host or db_user or db_password or bucket_name or lambda_name or db_name ):
        raise ValueError("Some of value doesn't set")

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    s3_backup_path = f"backups/{timestamp}/"

    backup_database_file = f"/tmp/backup_database_{timestamp}.dump"
    s3_database_backup = f"{s3_backup_path}backup_database_{timestamp}.dump"

    backup_roles_users_file = f"/tmp/backup_roles_users_{timestamp}.dump"
    s3_roles_users_backup = f"{s3_backup_path}backup_roles_users_{timestamp}.sql"

    try:
        # Set environment variable for pg_dump
        os.environ['PGPASSWORD'] = db_password
        s3_client = boto3.client('s3')
        lambda_client = boto3.client('lambda')

        print("Create backup")
        # Create backup
        subprocess.run([
           'pg_dump',
           '-h', db_host,
           '-U', db_user,
           '-d', db_name,
           '-F', 'c',
           '-f', backup_database_file
        ], check=True
        )

        s3_client.upload_file(
            backup_database_file,
            bucket_name,
            s3_database_backup
        )

        print("Database backup created and downloaded to S3")

        print("Create users backup")
        subprocess.run([
           'pg_dumpall',
           '-h', db_host,
           '-U', db_user,
           '--no-role-passwords',
            '-g',
           '-f', backup_roles_users_file
        ], check=True
        )
        s3_client.upload_file(
            backup_roles_users_file,
            bucket_name,
            s3_roles_users_backup
        )
        print("Users and roles backup created and downloaded to S3")


        print(f"Invoke {lambda_name} function to test backup")
        payload = {
            's3_database_backup': s3_database_backup,
            's3_roles_users_backup': s3_roles_users_backup,
            's3_backup_path': s3_backup_path,
            's3_bucket': bucket_name
        }
        
        result = lambda_client.invoke(
            FunctionName=lambda_name,
            InvocationType='Event',
            Payload=json.dumps(payload)
        ) 

        print(result)



        return {
            'statusCode': 200,
            'body': f'Backups successfully created and uploaded to S3: {s3_database_backup}; {s3_roles_users_backup}'
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Backup failed: {str(e)}'
        }
