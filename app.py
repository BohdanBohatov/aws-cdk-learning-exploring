#!/usr/bin/env python3
import aws_cdk as cdk

from lib.utils.config import Configuration
from lib.stacks.cdk_certificate_manager_stack import CdkCertificateStack
from lib.stacks.cdk_create_table_stack import CdkCreatePostgresDatabaseStack
from lib.stacks.cdk_lambda_layer_stack import CdkLambdaLayerStack
from lib.stacks.cdk_route53_stack import CdkRoute53Stack
from lib.stacks.cdk_rsd_postgres_stack import CdkPostgresStack
from lib.stacks.cdk_vpc_stack import CdkVpcStack
from lib.stacks.cdl_ec2B_lb_stack import CdkEc2LbStack
from lib.stacks.cdk_create_db_user_stack import CdkCreatePostgresUserStack
from lib.stacks.cdk_S3_postgres_db_backup import CdkPostgresBackupStack
from lib.stacks.old_stacks.cdk_verify_postgres_17_backup import CdkVerifyPostgresBackup


class ApplicationStack:
    def __init__(self, application: cdk.App, environment_name: str) -> None:
        self.app = application
        self.config = Configuration(environment_name)
        self.env_name = self.config.get_config()["environment"]

        self._init_infrastructure_stacks()
        self._database_stacks()
        self._postgres_backup_stack()


    def _init_infrastructure_stacks(self) -> None:
        """Initialize core infrastructure stacks"""
        self.vpc_stack = CdkVpcStack( self.app,f"CdkVpcStack-{self.env_name}", self.config.get_vpc_config())
        self.lambda_layer_stack = CdkLambdaLayerStack( self.app,f"CdkLambdaLayerStack-{self.env_name}")

    def _init_dns_stack(self) -> None:
        """Initialize Route53 stack"""
        self.route53_stack = CdkRoute53Stack(
            self.app,
            f"CdkRoute53Stack-{self.env_name}"
        )
        self.route53_stack.add_dependency(self.ec2_lb_stack)

        self.certificate_stack = CdkCertificateStack(
            self.app,
            f"CdkCertificateStack",
            hosted_zone=self.route53_stack.get_hosted_zone
        )
        self.certificate_stack.add_dependency(self.route53_stack)

    def _database_stacks(self) -> None:
        """Initialize database-related stacks"""
        # RDS stack - depends on VPC
        db_config = self.config.get_database_config()

        self.rds_stack = CdkPostgresStack(
            self.app,
            f"CdkRdsPostgresInstanceStack-{self.env_name}",
            instance_name=db_config["instanceName"],
            vpc=self.vpc_stack.get_vpc
        )
        self.rds_stack.add_dependency(self.vpc_stack)

        # Database creation stack
        self.create_database_stack = CdkCreatePostgresDatabaseStack(
            self.app,
            f"CdkCreateDatabaseStack-{self.env_name}",
            vpc=self.vpc_stack.get_vpc,
            db_instance=self.rds_stack.get_db_instance,
            postgres_layer=self.lambda_layer_stack.get_layer,
            database_name=db_config["databaseName"],
        )
        self.create_database_stack.add_dependency(self.rds_stack)
        self.create_database_stack.add_dependency(self.lambda_layer_stack)

        # Database user creation stack
        self.db_user_stack = CdkCreatePostgresUserStack(
            self.app,
            f"CdkCreatePostgresUserStack-{self.env_name}",
            vpc=self.vpc_stack.get_vpc,
            db_instance=self.rds_stack.get_db_instance,
            environment=self.env_name,
            postgres_layer=self.lambda_layer_stack.get_layer,
            db_name=db_config["databaseName"],
            user_name=db_config['username']
        )
        self.db_user_stack.add_dependency(self.create_database_stack)

    def _init_application_stacks(self) -> None:
        """Initialize application and networking stacks"""
        # EC2 and Load Balancer stack - depends on VPC
        self.ec2_lb_stack = CdkEc2LbStack(
            self.app,
            f"CdkEc2LbStack-{self.env_name}",
            vpc=self.vpc_stack.get_vpc
        )
        self.ec2_lb_stack.add_dependency(self.vpc_stack)

    def _postgres_backup_stack(self) -> None:
        """Initialize S3 backup stack"""
        self.postgres_backup_stack = CdkPostgresBackupStack(
            self.app,
            f"CdkPostgresBackupStack-{self.env_name}",
            environment=self.env_name,
            db_instance=self.rds_stack.get_db_instance,
            vpc=self.vpc_stack.vpc,
            ec2_configuration=self.config.get_ec2_config(),
            ec2_security_group=self.vpc_stack.get_ec2_group,
        )

        self.postgres_backup_stack.add_dependency(self.create_database_stack)
        self.postgres_backup_stack.add_dependency(self.lambda_layer_stack)


def main() -> None:
    application = cdk.App()
    environment_name = application.node.try_get_context('env') or 'dev'
    ApplicationStack(application, environment_name)
    application.synth()

if __name__ == "__main__":
    main()



