import json
import boto3

def lambda_handler(event, context):
    try:
        myS3 = boto3.client('s3')
        response = myS3.list_buckets()
        bucket_names = [bucket['Name'] for bucket in response.get('Buckets', [])]
        response_body = {
            "buckets": bucket_names
        }

        return {
            "isBase64Encoded": "false",
            'statusCode': 200,
            "headers": { "Content-type": "text/plain" },
            'body': json.dumps(response_body)
        }
    
    except Exception as e:
        return {
            "isBase64Encoded": "false",
            "headers": { "Content-type": "text/plain" },
            'statusCode': 500,
            'body': f"Error: {str(e)}"
        }