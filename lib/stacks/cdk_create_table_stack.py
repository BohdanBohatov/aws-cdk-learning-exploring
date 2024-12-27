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
    
)
from constructs import Construct

class CdkCreatePostgresDatabaseStack(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 vpc: ec2.Vpc,
                 db_instance: rds.DatabaseInstance,
                 postgres_layer: _lambda.LayerVersion,
                 database_name: str,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        create_table_lambda = _lambda.Function(
            self, "CreateTableLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="postgres_new_table.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/postgres_new_table"),
            layers=[postgres_layer],
            environment={
                "DB_ADMIN_SECRET_NAME": db_instance.secret.secret_name,
                "NEW_DATABASE_NAME": database_name
            },
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            timeout=Duration.seconds(120),
        )

        db_instance.secret.grant_read(create_table_lambda)
        db_instance.grant_connect(create_table_lambda)
        
        custom_resource = cr.AwsCustomResource(
            self, "DatabaseCustomResource",
            resource_type='Custom::CdkCreatePostgresTable',
            log_retention=logs.RetentionDays.ONE_WEEK,
            on_create=cr.AwsSdkCall(
                physical_resource_id=cr.PhysicalResourceId.of("DatabaseCustomResourceCreate"),
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": create_table_lambda.function_name,
                    "Payload": '{"RequestType": "Create"}'
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["lambda:InvokeFunction"],
                    resources=[create_table_lambda.function_arn]
                )
            ])
        )


