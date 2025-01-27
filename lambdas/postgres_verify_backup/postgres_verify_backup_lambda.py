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
    delete_ec2_lambda_name = os.environ["DELETE_EC2_LAMBDA_NAME"]
    topic_arn = os.environ["SNS_TOPIC_ARN"]
    environment = os.environ["ENVIRONMENT"]


    if not (instance_id or database_backup_name or roles_users_backup_name or s3_bucket or azure_secret_arn or delete_ec2_lambda_name or topic_arn):
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

                    su postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D /etc/postgresql/17/main/ -l /etc/postgresql/17/main/logfile.log stop"
                    su postgres -c "echo \\"listen_addresses=\'*\'\\" >> /etc/postgresql/17/main/postgresql.conf"
                    su postgres -c "echo \\"host all all 0.0.0.0/0 md5\\" >> /etc/postgresql/17/main/pg_hba.conf"
                    su postgres -c "/usr/lib/postgresql/17/bin/pg_ctl -D /etc/postgresql/17/main/ -l /etc/postgresql/17/main/logfile.log start"

                    aws s3 cp s3://{s3_bucket}/{database_backup_name} /tmp/data-backups
                    aws s3 cp s3://{s3_bucket}/{roles_users_backup_name} /tmp/data-backups

                    database_basename=$(basename {database_backup_name})
                    role_database_basename=$(basename {roles_users_backup_name})
                    chown -R postgres:postgres /tmp/data-backups

                    su postgres -c "grep -v 'rds_temp_tablespace\\|rdsdbdata\\|rdsadmin\\|pg_checkpoint\\|rds_' /tmp/data-backups/$role_database_basename > /tmp/data-backups/backup_filtered_roles.sql"
                    su postgres -c "psql -f /tmp/data-backups/backup_filtered_roles.sql postgres -U postgres"
                    su postgres -c "pg_restore --create -U postgres -d postgres /tmp/data-backups/$database_basename"

                    #RECORDS=$(sudo -u postgres psql -d dev_database -c "SELECT COUNT(*) AS record FROM test_table WHERE created_at >= CURRENT_DATE - INTERVAL '1 day'" -t)

                    RECORDS=$(sudo -u postgres psql -d dev_database -c "SELECT COUNT(*) FROM test_table where created_at = '2025-01-23 08:29:35.514166'" -t)
                    if [[ "$RECORDS" -eq 0 ]]; then
                        echo "Inform some SNS service that backup is broken or doesn't have yesterday's records" >> /var/log/record.log
                        exit 1
                    fi

                    export AZCOPY_SPA_CLIENT_SECRET=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["azurePostgresPrincipal"]')
                    export APPLICATION_ID=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["applicationId"]')
                    export TENANT_ID=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["tenantId"]')
                    export BUCKET_NAME=$(aws secretsmanager get-secret-value --secret-id '{azure_secret_arn}' --output text --query "SecretString" | jq -r '.["bucket_name"]')

                    azcopy login --login-type=SPN --application-id $APPLICATION_ID --tenant-id $TENANT_ID
                    azcopy copy "/tmp/data-backups/$database_basename" "$BUCKET_NAME/{database_backup_name}"
                    azcopy copy "/tmp/data-backups/$role_database_basename" "$BUCKET_NAME/{roles_users_backup_name}"

                    aws sns publish --topic-arn {topic_arn} --message "Backup for postgres created, environment: {environment}.\n\
                    S3 roles backup: {s3_bucket}/{roles_users_backup_name};\n\
                    S3 database backup: {s3_bucket}/{database_backup_name};\n\
                    Azure roles backup: $BUCKET_NAME/{roles_users_backup_name};\n\
                    Azure database backup: $BUCKET_NAME/{database_backup_name}" \
                        --subject "{environment}-Postgresql backup created sucessfully" --message-structure "string"

                    aws lambda invoke --function-name {delete_ec2_lambda_name} --invocation-type Event --cli-binary-format raw-in-base64-out --payload '{{"instance_id": "{instance_id}"}}' /dev/null
                    """

                    #Umpload databases without system information to S3 and azure
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
        return Exception(f"Error executing command: {str(e)}")
