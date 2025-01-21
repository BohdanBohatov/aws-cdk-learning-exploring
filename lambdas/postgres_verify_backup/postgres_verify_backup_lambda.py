import json
import boto3


def lambda_handler(event, context):

    ssm = boto3.client('ssm')
   
    instance_id = event.get('instance_id')
    database_backup_name = event.get('s3_database_backup')
    roles_users_backup_name = event.get('s3_roles_users_backup')
    path_to_backup = event.get('s3_backup_path')
    s3_bucket = event.get('s3_bucket')

    if not (instance_id or database_backup_name or roles_users_backup_name or path_to_backup or s3_bucket):
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Missing required parameters'
            })
        }
    
    try:
        # Execute the command on the EC2 instance
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',  # AWS SSM document to run shell commands
            Parameters={
                'commands': [
                    '#!/bin/bash',
                    'mkdir -p /tmp/data-backups',
                    'chown postgres:postgres /tmp/data-backups',
                    """ 
                        su postgres -c "echo 'listen_addresses=\\'*\\'' >> /etc/postgresql/17/main/postgresql.conf" 
                    """,
                    'su postgres -c "echo \\"host all all 0.0.0.0/0 md5\\" >> /etc/postgresql/17/main/pg_hba.conf"',
                    'su postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D /var/lib/postgresql/17/main restart"',
                    f"aws s3 cp s3://{s3_bucket}/{path_to_backup}{database_backup_name} /tmp/data-backups",
                    f"aws s3 cp s3://{s3_bucket}/{path_to_backup}{roles_users_backup_name} /tmp/data-backups",
                    'chown -R postgres:postgres /tmp/data-backups',
                    f"""
                        su postgres -c "grep -v 'rds_temp_tablespace\\|rdsdbdata\\|rdsadmin\\|pg_checkpoint\\|rds_' /tmp/data-backups/{roles_users_backup_name} > /tmp/data-backups/backup_filtered_roles.sql"
                    """,
                    'su postgres -c "psql -f /tmp/data-backups/backup_filtered_roles.sql postgres -U postgres"',
                    f'su postgres -c "pg_restore --create -U postgres -d postgres /tmp/data-backups/{database_backup_name}"',

                    #TODO code to check records in postgresql
                    #Umpload databases without system information to S3 and azure

                    #destroy instance
                    #"aws ec2 terminate-instances --instance-ids {instance_id}"
                ]
            }
        )
        
        command_id = response['Command']['CommandId']
        print(f"Command sent successfully. Command ID: {command_id}")

        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Command sent successfully',
                'commandId': command_id
            })
        }
        
    except Exception as e:
        print(f"Error executing command: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'message': f'Error executing command: {str(e)}'
            })
        }
