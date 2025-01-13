import boto3
import subprocess
import os
from datetime import datetime
from botocore.exceptions import ClientError
import json

def lambda_handler(event, context):

    bucket_name = event["bucket_name"]
    backup_folder = {event["db_folder"]}
    backup_roles_users_file = f"{backup_folder}/{event["db_roles_users_file"]}"
    backup_database_file = f"{backup_folder}/{event["db_file"]}"

    database_backup = "database.dump"
    user_roles_file = "users_roles.dump"

    try:

        print("Init postgresql database")
        result = subprocess.run([
            'su',
            'postgres',
            '-c',
            '/usr/pgsql-17/bin/pg_ctl -D /var/lib/pgsql/17/data start'
        ], check=True, capture_output=True, text=True
        )
        print("Command output:", result.stdout)
        print("Postgresql server initiated successfully")


        print("Download users backup file")

        # Upload to S3
        s3_client = boto3.client('s3')
        s3_client.download_file(
           backup_roles_users_file,
           bucket_name,
           user_roles_file
        )

        print("Download database backup file")

        s3_client.download_file(
           backup_database_file,
           bucket_name,
           database_backup
        )

        print("File uploaded to S3")

        return {
            'statusCode': 200,
            'body': f'Backup successfully downloaded'
        }

    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Backup failed: {str(e)}'
        }
