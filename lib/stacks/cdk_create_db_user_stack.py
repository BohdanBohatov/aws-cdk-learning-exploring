from aws_cdk import (
    aws_logs as logs,
    Stack,
    Duration,
    CfnOutput,
    aws_iam as iam,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    custom_resources as cr,
    aws_secretsmanager as secretsmanager,
)
import json
from constructs import Construct

class CdkCreatePostgresUserStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 vpc: ec2.Vpc,
                 db_instance: rds.DatabaseInstance,
                 environment: str,
                 db_name: str,
                 postgres_layer: _lambda.LayerVersion,
                 user_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        secret = secretsmanager.Secret(
            self,
            id=f"{environment}-DatabaseSecret",
            secret_name=f"{environment}/database/{db_name}/credentials",
            description=f"Database credentials for {db_name} in {environment}",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                password_length=30,
                exclude_characters="@%*()/'\"\\",
                exclude_punctuation=False,
                include_space=False,
                require_each_included_type=True,
                generate_string_key="password",
                secret_string_template=json.dumps({
                    "username": user_name,
                    "engine": db_instance.engine.engine_type,
                    "host": db_instance.db_instance_endpoint_address,
                    "port": db_instance.db_instance_endpoint_port,
                    "dbname": db_name,
                    "schema": "public"
                })
            ),
        )

        create_user_lambda = _lambda.Function(
            self, "CreateDBUserLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="postgres_new_user.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/postgres_new_user"),
            layers=[postgres_layer],
            environment={
                "MAIN_DB_SECRET_NAME": db_instance.secret.secret_name,
                "NEW_DB_SECRET_NAME": secret.secret_name
            },
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            timeout=Duration.seconds(120),
        )

        secret.grant_read(create_user_lambda)
        db_instance.secret.grant_read(create_user_lambda)
        db_instance.grant_connect(create_user_lambda)
        
        custom_resource = cr.AwsCustomResource(
            self, "DatabaseCreateUserCustomResource",
            resource_type='Custom::CdkCreatePostgresUser',
            log_retention=logs.RetentionDays.ONE_WEEK,
            on_create=cr.AwsSdkCall(
                physical_resource_id=cr.PhysicalResourceId.of("DatabaseCustomResourceUserCreate"),
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": create_user_lambda.function_name,
                    "Payload": '{"RequestType": "Create"}'
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["lambda:InvokeFunction"],
                    resources=[create_user_lambda.function_arn]
                )
            ])
        )


