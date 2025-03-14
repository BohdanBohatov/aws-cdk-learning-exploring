from aws_cdk import (
    Stack,
    Duration,
    aws_rds as rds,
    aws_ec2 as ec2,
)

from constructs import Construct

class CdkPostgresStack(Stack):

    @property
    def get_db_instance(self):
        return self.database

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, instance_name: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        postgres_sg = ec2.SecurityGroup(
            self, "PostgresSecurityGroup",
            vpc=vpc,
            description="Security group for Postgres database",
            allow_all_outbound=True
        )

        postgres_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL traffic from within VPC"
        )

        postgres_sg.add_ingress_rule(
            peer=ec2.Peer.ipv4(cidr_ip="193.238.38.96/32"),
            connection=ec2.Port.tcp(5432),
            description="Allow PostgreSQL traffic from my IP"
        )

        self.database = rds.DatabaseInstance(
            self, instance_name,
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_17_2
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.SMALL
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_groups=[postgres_sg],
            allocated_storage=20,
            max_allocated_storage=100,
            storage_type=rds.StorageType.GP2,
            backup_retention=Duration.days(2),
            preferred_backup_window="03:00-04:00",
            deletion_protection=True,
            delete_automated_backups=True,
            storage_encrypted=True,
            multi_az=False,
            publicly_accessible=True,
            credentials=rds.Credentials.from_generated_secret(
                username="postgres_admin",

            )
        )

