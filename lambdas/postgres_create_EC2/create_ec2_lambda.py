import boto3
import os
from botocore.exceptions import WaiterError


def handler(event, context):
    ec2_resource = boto3.resource('ec2')
    ec2_client = boto3.client('ec2')

    instance_name = os.environ['INSTANCE_NAME']
    image_id = os.environ["AMI_IMAGE"]
    vpc_id = os.environ["VPC_ID"]
    key_name = os.environ["KEY_NAME"]
    instance_type = os.environ["INSTANCE_TYPE"]
    security_group_id = os.environ["SECURITY_GROUP_ID"]
    environment = os.environ["ENVIRONMENT"]

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

        # Wait for the instance to be running
        try:
            waiter = ec2_client.get_waiter('instance_running')
            waiter.wait(
                InstanceIds=[instance.instance_id],
                WaiterConfig={
                    'Delay': 5,  # Number of seconds to wait between attempts
                    'MaxAttempts': 40  # Maximum number of attempts
                }
            )
            
            # Get instance details after it's running
            instance.reload()  # Refresh the instance attributes
            
            return {
                'statusCode': 200,
                'body': {
                    'message': 'EC2 instance created and running successfully',
                    'instanceId': instance.instance_id,
                    'privateIp': instance.private_ip_address,
                    'publicIp': instance.public_ip_address if instance.public_ip_address else None,
                    'state': instance.state['Name']
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
