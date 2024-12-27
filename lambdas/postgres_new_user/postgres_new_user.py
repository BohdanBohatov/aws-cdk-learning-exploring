import os
import json
import psycopg2
import boto3
from botocore.exceptions import ClientError

""" Connect to main db as super admin to create new user in another db """
def get_sa_secret(secret_name: str):
    print("Get sa secret")
    secret_name = secret_name
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


def create_db_user(cur, db_name, username, password):
    """Create a new database user with full database permissions"""
    try:
        # Check if user exists
        cur.execute(f"SELECT 1 FROM pg_roles WHERE rolname = %s;", (username,))
        if not cur.fetchone():
            # Create user with password
            cur.execute(f"CREATE USER {username} WITH PASSWORD %s;", (password, ))

            # Grant privileges on database
            cur.execute(f"GRANT ALL PRIVILEGES ON DATABASE {db_name} TO {username};")
            cur.execute(f"GRANT USAGE ON SCHEMA public TO {username};")
            cur.execute(f"GRANT CREATE ON SCHEMA public TO {username}")

            cur.execute(f"GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO {username};")
            cur.execute(f"GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO {username};")
            cur.execute(f"GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO {username};")

            cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO {username};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO {username};")
            cur.execute(f"ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO {username};")

            return True
        else:
            return Exception(f"User {username} already exists")

    except Exception as e:
        print(f"Error creating user: {str(e)}")
        raise e


def lambda_handler(event: object, context: object) -> object:
    print("Start event: " + event['RequestType'])

    try:

        request_type = event['RequestType']

        if request_type == 'Create':

            print("Event is create")
            # Get DB credentials
            main_secret = get_sa_secret(os.environ['MAIN_DB_SECRET_NAME'])
            new_user_secret = get_sa_secret(os.environ['NEW_DB_SECRET_NAME'])

            db_name = new_user_secret["dbname"]
            new_db_user = new_user_secret["username"]
            new_db_password = new_user_secret["password"]

            # Connect to default postgres database
            conn = psycopg2.connect(
                host=main_secret['host'],
                database=main_secret['engine'],
                user=main_secret['username'],
                password=main_secret['password']
            )
            conn.autocommit = True  # Required for creating database

            try:
                with conn.cursor() as cur:
                    # Check if database exists
                    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s;", (db_name,))
                    db_existence = cur.fetchone()

                    if not db_existence:
                        conn.close()
                        raise Exception(f'Database {db_name} does not exists. Need to create DB before adding new user')

                    else:
                        conn.close()
                        # Connect to the specific database
                        connection = psycopg2.connect(
                            host=main_secret['host'],
                            database=db_name,
                            user=main_secret['username'],
                            password=main_secret['password']
                        )
                        connection.autocommit = True

                        create_db_user(connection.cursor(), db_name, new_db_user, new_db_password)
                        connection.close()

                return {
                    'statusCode': 200,
                    'body': json.dumps(f'User {new_db_user} created successfully')
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


