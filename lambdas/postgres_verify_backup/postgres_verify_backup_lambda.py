import json
import boto3
import os


def lambda_handler(event, context):

    ssm = boto3.client('ssm')
   
    instance_id = event.get('instance_id')
    database_backup_name = event.get('s3_database_backup')
    roles_users_backup_name = event.get('s3_roles_users_backup')
    s3_bucket = event.get('s3_bucket')
    azure_secret_arn = os.environ["AZURE_SECRET_ARN"]


    if not (instance_id or database_backup_name or roles_users_backup_name or s3_bucket or azure_secret_arn):
        Exception("Missing required parameters")
    
    try:
        # Execute the command on the EC2 instance
        response = ssm.send_command(
            InstanceIds=[instance_id],
            DocumentName='AWS-RunShellScript',  # AWS SSM document to run shell commands
            Parameters={
                'commands': [
                    f"""
                    #!/bin/bash
                    set -e
                    mkdir -p /tmp/data-backups

                    su postgres -c "echo \\"listen_addresses=\'*\'\\" >> /etc/postgresql/17/main/postgresql.conf"
                    su postgres -c "echo \\"host all all 0.0.0.0/0 md5\\" >> /etc/postgresql/17/main/pg_hba.conf"
                    su postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D /var/lib/postgresql/17/main restart"

                    aws s3 cp s3://{s3_bucket}/{database_backup_name} /tmp/data-backups
                    aws s3 cp s3://{s3_bucket}/{roles_users_backup_name} /tmp/data-backups

                    database_basename=$(basename {database_backup_name})
                    role_database_basename=$(basename {roles_users_backup_name})
                    chown -R postgres:postgres /tmp/data-backups

                    su postgres -c "grep -v 'rds_temp_tablespace\\|rdsdbdata\\|rdsadmin\\|pg_checkpoint\\|rds_' /tmp/data-backups/$role_database_basename > /tmp/data-backups/backup_filtered_roles.sql"
                    su postgres -c "psql -f /tmp/data-backups/backup_filtered_roles.sql postgres -U postgres"
                    su postgres -c "pg_restore --create -U postgres -d postgres /tmp/data-backups/$database_basename"

                    export AZCOPY_SPA_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["azurePostgresPrincipal"]')
                    export APPLICATION_ID=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["applicationId"]')
                    export TENANT_ID=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["tenantId"]')
                    export BUCKET_NAME=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["bucket_name"]')

                    azcopy login --login-type=SPN --application-id $APPLICATION_ID --tenant-id $TENANT_ID
                    azcopy copy "/tmp/data-backups/$database_basename" "$BUCKET_NAME/{database_backup_name}"
                    azcopy copy "/tmp/data-backups/$role_database_basename" "$BUCKET_NAME/{roles_users_backup_name}"
                    """
                   

                    #TODO code to check records in postgresql
                    #"sudo -u postgres psql -d dev_database -c \"SELECT * from test_table\""

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
