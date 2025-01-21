from aws_cdk import (
    Stack,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    aws_iam as iam,
    Duration
)
import json
from constructs import Construct

class CdkVerifyPostgresBackup(Stack):

    def __init__(self, scope: Construct, construct_id: str,
                 environment: str,
                 vpc: ec2.Vpc,
                 ec2_configuration: dict,
                 security_group: ec2.SecurityGroup,
                 **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # IAM role for Lambda
        lambda_create_ec2_role = iam.Role(
            self, f"LambdaEC2Role-{environment}",
            role_name= f"LambdaEC2Role-{environment}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        # Add required policies for EC2 creation and CloudWatch Logs
        lambda_create_ec2_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonEC2FullAccess")
        )
        lambda_create_ec2_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        lambda_create_ec2_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:RunInstances",
                    "ec2:CreateTags",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeVpcs",
                    "iam:PassRole"
                ],
                resources=["*"]
            )
        )

        #Lambda function
        ec2_creator_lambda = _lambda.Function(
            self, f"EC2CreatorFunction-{environment}",
            function_name=f"EC2CreatorFunction-{environment}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create_ec2_lambda.handler",
            code=_lambda.Code.from_asset("lambdas/postgres_create_EC2"),
            role=lambda_create_ec2_role,
            timeout=Duration.minutes(3),
            environment= {
                "INSTANCE_NAME": f"EC2-postgres-{environment}",
                "AMI_IMAGE": ec2_configuration["ami"],
                "VPC_ID": vpc.vpc_id,
                "KEY_NAME": ec2_configuration["keyPairName"],
                "INSTANCE_TYPE":  ec2_configuration["instanceType"],
                "SECURITY_GROUP_ID": security_group.security_group_id,
                "ENVIRONMENT": environment
            }
        )


        ec2_verify_postgres_lambda = _lambda.Function(
            self, f"EC2VerifyPostgresFunction-{environment}",
            function_name=f"EC2VerifyPostgresFunction-{environment}",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="postgres_verify_lambda.handler",
            code=_lambda.Code.from_asset("lambdas/postgres_verify_backup"),
            timeout=Duration.minutes(3),
        )



        ec2_verify_postgres_lambda.grant_invoke(ec2_creator_lambda)