from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_secretsmanager as secretsmanager,
)
import json
from constructs import Construct

class CdkLearnSecrets(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 vpc: ec2.Vpc,
                 db: rds.DatabaseInstance,
                 config: dict,
                 db_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        secret = secretsmanager.Secret(
            self,
            id=f"{config['environment']}-DatabaseSecret",
            secret_name=f"{config['environment']}/database/{db_name}/credentials",
            description=f"Database credentials for {db_name} in {config['environment']}",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                # Customize password generation rules
                password_length=32,
                exclude_characters="@%*()/'\"\\",
                exclude_punctuation=False,
                include_space=False,
                require_each_included_type=True,
                generate_string_key="password",
                secret_string_template=json.dumps({
                    "username": f"{db_name}_user",
                    "engine": db.engine.engine_type,
                    "host": db.db_instance_endpoint_address,
                    "port": db.db_instance_endpoint_port,
                    "dbname": db_name,
                    "schema": "public"
                })
            ),
        )

        secret.secret_value_from_json("password").to_string()

