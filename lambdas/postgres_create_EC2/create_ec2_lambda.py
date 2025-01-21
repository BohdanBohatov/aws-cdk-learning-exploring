import boto3
import os
import json
from botocore.exceptions import WaiterError


def handler(event, context):
    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')
    lambda_client = boto3.client('lambda')


    instance_name = os.environ['INSTANCE_NAME']
    image_id = os.environ["AMI_IMAGE"]
    vpc_id = os.environ["VPC_ID"]
    key_name = os.environ["KEY_NAME"]
    instance_type = os.environ["INSTANCE_TYPE"]
    security_group_id = os.environ["SECURITY_GROUP_ID"]
    
    lambda_name = os.environ["LAMBDA_NAME"]

    s3_bucket_name = event.get('s3_bucket')
    s3_database_backup = event.get('s3_database_backup')
    s3_roles_users_backup = event.get('s3_roles_users_backup')
    s3_backup_path = event.get('s3_backup_path')
    


    try:

        subnets = ec2_client.describe_subnets(
            Filters=[
                {
                    'Name': 'vpc-id',
                    'Values': [vpc_id]
                },
                {
                    'Name': 'map-public-ip-on-launch',
                    'Values': ['true'] #TODO to false when finished, to do not allow ec2 to go in internet or place to NAT subnet
                }
            ]
        )

        if not subnets['Subnets']:
            raise Exception("No subnet found")

        # Select the first available subnet
        subnet_id = subnets['Subnets'][0]['SubnetId']

        instances = ec2_resource.create_instances(
            ImageId=image_id,
            InstanceType=instance_type,
            KeyName=key_name,
            MaxCount=1,
            MinCount=1,
            IamInstanceProfile={
                'Arn': os.environ['EC2_IAM_INSTANCE_ARN']
            },
            NetworkInterfaces=[
                {
                    'AssociatePublicIpAddress': True,
                    'DeviceIndex': 0,
                    'SubnetId': subnet_id,
                    'DeleteOnTermination': True,
                    'Groups': [security_group_id]
                }
            ],
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name
                        }
                    ]
                }
            ]
        )

        instance= instances[0]

        print("Role attached to instance")


        # Wait for the instance to be running
        try:
            waiter = ec2_client.get_waiter('instance_running')
            waiter.wait(
                InstanceIds=[instance.instance_id],
                WaiterConfig={
                    'Delay': 45,  # Number of seconds to wait between attempts
                    'MaxAttempts': 5  # Maximum number of attempts
                }
            )
            
            # Refresh the instance attributes
            instance.reload()

            print(f"Invoke {lambda_name} function to test backup")

            payload = {
                's3_database_backup': s3_database_backup,
                's3_roles_users_backup': s3_roles_users_backup,
                's3_backup_path': s3_backup_path,
                's3_bucket': s3_bucket_name,
                'instance_id': instance.instance_id,
            }
            
            lambda_client.invoke(
                FunctionName=lambda_name,
                InvocationType='Event',
                Payload=json.dumps(payload)
            ) 
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'EC2 instance created and running successfully',
                    'instanceId': instance.instance_id,
                    'privateIp': instance.private_ip_address,
                    'publicIp': instance.public_ip_address if instance.public_ip_address else None,
                    'state': instance.state['Name'],
                    's3_bucket': s3_bucket_name,
                    's3_database_backup': s3_database_backup,
                    's3_roles_users_backup': s3_roles_users_backup,
                    's3_backup_path': s3_backup_path,
                }
            }
            
        except WaiterError as we:
            return {
                'statusCode': 500,
                'body': f'Instance created but failed to reach running state: {str(we)}'
            }


    except Exception as e:
        return {
            'statusCode': 500,
            'body': f'Error creating EC2 instance: {str(e)}'
        }
