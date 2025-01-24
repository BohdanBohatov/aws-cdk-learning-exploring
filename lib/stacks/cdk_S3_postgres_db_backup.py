from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_events as events,
    aws_events_targets as targets,
    aws_iam as iam,
    aws_s3 as s3,
    aws_rds as rds,
    aws_ec2 as ec2,
    aws_ecr as ecr
)
from aws_cdk.aws_events_targets import LambdaFunction
from constructs import Construct

class CdkPostgresBackupStack(Stack):

    
    def __init__(self, scope: Construct, construct_id: str,
                environment: str,
                vpc: ec2.Vpc,
                db_instance: rds.DatabaseInstance,
                ec2_configuration: dict,
                ec2_security_group: ec2.SecurityGroup,
                azure_configuration: dict,
                **kwargs) -> None:
                
        super().__init__(scope, construct_id, **kwargs)

        self.env_name = environment
        self.vpc = vpc
        self.db_instance = db_instance
        self.ec2_configuration = ec2_configuration
        self.ec2_security_group = ec2_security_group
        self.azure_configuration = azure_configuration

        """
            Lambdas names need to hand over to other lambdas to be able one lambda to run enother lambda 
        """
        self.create_ec2_lambda_name = f"EC2CreatorFunction-{self.env_name}"
        self.verify_ec2_lambda_name = f"EC2VerifyPostgresFunction-{self.env_name}"
        self.delete_ec2_lambda_name = f"DeleteEC2InstanceFunction-{self.env_name}"

        self.ec2_instance_name = f"EC2-verify-postgres-backup-{self.env_name}"

        self.create_backup()
        self.create_ec2_to_test_backup()


    def create_backup(self):

        self.backup_bucket = s3.Bucket(
            self, f"PostgresBackupBucket-{self.env_name}",
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            encryption=s3.BucketEncryption.S3_MANAGED,
            auto_delete_objects=False,
            lifecycle_rules=[
                s3.LifecycleRule(
                    id="DeleteAfter30Days",
                    expiration=Duration.days(30),
                    abort_incomplete_multipart_upload_after=Duration.days(1)
                )
            ]
        )

        self.backup_lambda = _lambda.DockerImageFunction(
            self, f"backup-postgres-function-{self.env_name}",
            code=_lambda.DockerImageCode.from_ecr(
                repository=ecr.Repository.from_repository_name(
                    self, "lambda-images",
                    repository_name="lambda-images/fedora41-postgresql"
                ),
                tag_or_digest="1.16"
            ),
            timeout=Duration.minutes(3),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            memory_size=512,
            environment={
                "BUCKET_NAME": self.backup_bucket.bucket_name,
                "DB_ADMIN_SECRET": self.db_instance.secret.secret_name,
                "DB_TO_BACKUP": "dev_database", #TODO change this database for production and other
                "LAMBDA_NAME": self.create_ec2_lambda_name
            }
        )

        events.Rule(
           self, "DailyBackupRule",
           schedule=events.Schedule.cron(hour="3", minute="0"),
           targets=[targets.LambdaFunction(self.backup_lambda)]
        )


        self.db_instance.secret.grant_read(self.backup_lambda)
        self.db_instance.grant_connect(self.backup_lambda)
        self.backup_bucket.grant_write(self.backup_lambda)


    def create_ec2_to_test_backup(self):

        """
            This role is used in EC2 instance, instance should be able to execute scripts, and download files from s3 bucket 
        """
        ec2_role = iam.Role(
            self, f"EC2Role-{self.env_name}",
            role_name= f"EC2Role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )

        instance_profile = iam.CfnInstanceProfile(
            self, f"EC2InstanceProfile-{self.env_name}",
            instance_profile_name=f"EC2InstanceProfile-{self.env_name}",
            roles=[ec2_role.role_name]
        )

        ec2_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "s3:ListBucket",
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:PutObject",
                ],
                resources=[
                    self.backup_bucket.bucket_arn,
                    f"{self.backup_bucket.bucket_arn}/*"
                ],
            )
        )

        ec2_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "secretsmanager:GetSecretValue"
                ],
                resources=[
                    self.azure_configuration["secretArn"]
                ],
            )
        )

        ec2_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        # IAM role for Lambda
        lambda_create_ec2_role = iam.Role(
            self, f"LambdaEC2Role-{self.env_name}",
            role_name= f"LambdaEC2Role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        lambda_create_ec2_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        lambda_create_ec2_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "iam:CreateInstanceProfile",
                    "iam:AddRoleToInstanceProfile",
                    "iam:CreateRole",
                    "iam:PutRolePolicy",
                    "iam:AttachRolePolicy",
                    "iam:PassRole",
                    "iam:TagRole"
                ],
                resources=[
                    "arn:aws:iam::*:role/*", 
                    "arn:aws:iam::*:instance-profile/*",
                    "arn:aws:iam::*:instance-profile/*",
                ],
            )
        )

        lambda_create_ec2_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:RunInstances",
                    "ec2:DescribeInstances",
                    "ec2:CreateTags",
                    "ec2:DescribeImages",
                    "ec2:DescribeSubnets",
                    "ec2:DescribeSecurityGroups",
                    "ec2:DescribeVpcs",
                    "ec2:AssociateIamInstanceProfile",
                    "ec2:ReplaceIamInstanceProfileAssociation",
                ],
                resources=["*"],
            )
        )

        ec2_creator_lambda = _lambda.Function(
            self, self.create_ec2_lambda_name,
            function_name=self.create_ec2_lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="create_ec2_lambda.handler",
            code=_lambda.Code.from_asset("lambdas/postgres_create_EC2"),
            role=lambda_create_ec2_role,
            timeout=Duration.minutes(3),
            environment= {
                "INSTANCE_NAME": self.ec2_instance_name,
                "AMI_IMAGE": self.ec2_configuration["ami"],
                "VPC_ID": self.vpc.vpc_id,
                "KEY_NAME": self.ec2_configuration["keyPairName"],
                "INSTANCE_TYPE":  self.ec2_configuration["instanceType"],
                "SECURITY_GROUP_ID": self.ec2_security_group.security_group_id,
                "ENVIRONMENT": self.env_name,
                "LAMBDA_NAME": self.verify_ec2_lambda_name,
                "EC2_IAM_INSTANCE_ARN": instance_profile.attr_arn
            }
        )

        lambda_verify_backup_role = iam.Role(
            self, f"Lambda_Verify_Backup_Role-{self.env_name}",
            role_name= f"Lambda_Verify_Backup_Role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        lambda_verify_backup_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
        )

        lambda_verify_backup_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore")
        )

        lambda_verify_backup_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ssm:SendCommand",
                    "ssm:GetCommandInvocation"
                ],
                resources=["*"],
            )
        )

        ec2_verify_postgres_lambda = _lambda.Function(
            self, self.verify_ec2_lambda_name,
            function_name=self.verify_ec2_lambda_name,
            role=lambda_verify_backup_role,
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="postgres_verify_backup_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/postgres_verify_backup"),
            timeout=Duration.minutes(3),
            environment={
                "AZURE_SECRET_ARN": self.azure_configuration["secretArn"],
                "DELETE_EC2_LAMBDA_NAME": self.delete_ec2_lambda_name,
            }
        )

        ec2_delete_instance_role = iam.Role(
            self, f"LambdaDeleteEC2Role-{self.env_name}",
            role_name= f"LambdaDeleteEC2Role-{self.env_name}",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com")
        )

        ec2_delete_instance_role.add_to_policy(
            iam.PolicyStatement(
                actions=[
                    "ec2:TerminateInstances",
                    "ec2:DescribeInstances",
                ],
                resources=["*"],
            )
        )

        ec2_delete_instnace_lambda = _lambda.Function(
            self, self.delete_ec2_lambda_name,
            function_name=self.delete_ec2_lambda_name,
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="delete_ec2_lambda.handler",
            code=_lambda.Code.from_asset("lambdas/postgres_delete_EC2"),
            timeout=Duration.minutes(3),
            role=ec2_delete_instance_role
        )

        
        ec2_creator_lambda.grant_invoke(self.backup_lambda)
        ec2_verify_postgres_lambda.grant_invoke(ec2_creator_lambda)
        self.backup_bucket.grant_read_write(ec2_verify_postgres_lambda)
        ec2_delete_instnace_lambda.grant_invoke(ec2_role)



