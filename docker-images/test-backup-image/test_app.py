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

    database_folder = "/tmp/database"
    database_socket = "/tmp/pg_socket"

    try:

        print("Create database and socket folders")
        command = f"mkdir -p {database_folder}"
        result = subprocess.run(command, shell=True, check=True, text=True)

        command = f"mkdir -p {database_socket}"
        result = subprocess.run(command, shell=True, check=True, text=True)
        print("Folder created:", result.stdout)


        print("Initiate database")
        command = f"/usr/pgsql-17/bin/initdb -D {database_folder} --auth=trust"
        result = subprocess.run(command, shell=True, check=True, text=True)
        print("Database initiated:", result.stdout)


        print("Configure database")
        command = f"echo \"listen_addresses=''\" >> {database_folder}/postgresql.conf"
        result = subprocess.run(command, shell=True, check=True, text=True)

        command = f"echo \"unix_socket_directories='{database_socket}'\" >> {database_folder}/postgresql.conf"
        result = subprocess.run(command, shell=True, check=True, text=True)

        command = f"echo \"log_min_messages=info\" >> {database_folder}/postgresql.conf"
        result = subprocess.run(command, shell=True, check=True, text=True)

        command = f"echo \"log_min_error_statement=info\" >> {database_folder}/postgresql.conf"
        result = subprocess.run(command, shell=True, check=True, text=True)

        command = f"sed -i 's/^log_filename = 'postgresql-%a.log'$/log_filename = log_file/'  {database_folder}/postgresql.conf"
        result = subprocess.run(command, shell=True, check=True, text=True)

        command = f"sed -i 's/^dynamic_shared_memory_type = posix $/dynamic_shared_memory_type = mmap/'  {database_folder}/postgresql.conf"
        result = subprocess.run(command, shell=True, check=True, text=True)

        print("Database configured:", result.stdout)


        print("Start database")
        command = f"/usr/pgsql-17/bin/pg_ctl -D {database_folder}  -l {database_folder}/logfile start"
        result = subprocess.run(command, shell=True, check=True, text=True)
        print("Database started:", result.stdout)


        # print("Download users backup file")
        #
        # # Upload to S3
        # s3_client = boto3.client('s3')
        # s3_client.download_file(
        #    backup_roles_users_file,
        #    bucket_name,
        #    user_roles_file
        # )
        #
        # print("Download database backup file")
        #
        # s3_client.download_file(
        #    backup_database_file,
        #    bucket_name,
        #    database_backup
        # )
        #
        # print("Files downloaded from S3")

       # delete_folder(database_folder)
        return {

            'statusCode': 200,
            'body': f'Backup successfully downloaded'
        }

    except Exception as e:

        command = f"cat {database_folder}/logfile"
        result = subprocess.run(command, shell=True, check=True, text=True)
        print(result)

        print("The end")

        delete_folder(database_folder)
        return {
            'statusCode': 500,
            'body': f'Backup failed: {str(e)}'
        }


def delete_folder(folder_path):
        command = f"rm -rf {folder_path}"
        result = subprocess.run(command, shell=True, check=True, text=True)
        print("Folder deleted output:", result.stdout)