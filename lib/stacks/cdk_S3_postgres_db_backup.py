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
                **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        backup_bucket = s3.Bucket(
            self, f"PostgresBackupBucket-{environment}",
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

        backup_lambda = _lambda.DockerImageFunction(
            self, f"backup-postgres-function-{environment}",
            code=_lambda.DockerImageCode.from_ecr(
                repository=ecr.Repository.from_repository_name(
                    self, "lambda-images",
                    repository_name="lambda-images/fedora41-postgresql"  # Replace with your ECR repo name
                ),
                tag_or_digest="1.13"
            ),
            timeout=Duration.seconds(20),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            memory_size=512,
            environment={
                "BUCKET_NAME": backup_bucket.bucket_name,
                "DB_ADMIN_SECRET": db_instance.secret.secret_name,
                "DB_TO_BACKUP": "dev_database"
            }
        )

        events.Rule(
           self, "DailyBackupRule",
           schedule=events.Schedule.cron(hour="3", minute="0"),
           targets=[targets.LambdaFunction(backup_lambda)]
        )

        db_instance.secret.grant_read(backup_lambda)
        db_instance.grant_connect(backup_lambda)
        backup_bucket.grant_write(backup_lambda)


