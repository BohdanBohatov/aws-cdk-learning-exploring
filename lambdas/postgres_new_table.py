import os
import json
import psycopg2
import boto3
from botocore.exceptions import ClientError

def get_secret():
    print("Get secret")
    secret_name = os.environ['DB_SECRET_NAME']
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
    print("Start event: " + event['RequestType'])

    try:
        
        request_type = event['RequestType']

        if request_type == 'Create':

            print("Event is create")
            # Get DB credentials
            secret = get_secret()
            new_db_name = os.environ['NEW_DATABASE_NAME']
            
            # Connect to default postgres database
            conn = psycopg2.connect(
                host=secret['host'],
                database=secret['engine'],
                user=secret['username'],
                password=secret['password']
            )
            conn.autocommit = True  # Required for creating database
            
            try:
                with conn.cursor() as cur:
                    # Check if database exists
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (new_db_name,))
                    exists = cur.fetchone()
                    
                    if not exists:
                        # Create new database
                        cur.execute(f'CREATE DATABASE {new_db_name};')
                        conn.close() #close connection

                        # Connect to new database to create extensions if needed
                        conn = psycopg2.connect(
                            host=secret['host'],
                            database=new_db_name,
                            user=secret['username'],
                            password=secret['password']
                        )
                        conn.autocommit = True
                        
                        with conn.cursor() as new_cur:
                            # Add extensions to database
                            new_cur.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
                            new_cur.execute('CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";')
                            new_cur.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

                    else:
                        raise Exception(f'Database {new_db_name} already exists.')
                return {
                    'statusCode': 200,
                    'body': json.dumps(f'Database {new_db_name} created successfully')
                }

            except Exception as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps(f'Error creating database: {str(e)}')
                }
            
            finally:
                conn.close()

        else:
            return {
                'statusCode': 200,
                'body': json.dumps('No action taken.')
            }

    except Exception as e:
        print(f'Error: {str(e)}')
        return {
            'statusCode': 500,
            'body': json.dumps(f'Error: {str(e)}')
        }


