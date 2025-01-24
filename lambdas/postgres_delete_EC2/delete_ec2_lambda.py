import boto3
from botocore.exceptions import WaiterError


def handler(event, context):
    instance_id = event.get('instance_id')
    
    if not instance_id:
        raise Exception("Missing instance_id in event parameters")
    
    try:
        ec2 = boto3.resource('ec2')
        instance = ec2.Instance(instance_id)
        instance.terminate()
        print(f"Instace {instance_id} terminated")

    except Exception as e:
       raise Exception(str(e))
