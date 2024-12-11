from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    CfnOutput
)
from constructs import Construct

class CdkVpcStack(Stack):

    @property
    def get_vpc(self):
        return self.vpc

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(
            self, 
            "CDK-VPC",
            ip_addresses=ec2.IpAddresses.cidr("10.0.0.0/16"),
            max_azs=2,  # Use 2 Availability Zones
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private-NAT",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24,
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24,
                )
            ],
            # Enable DNS hostnames and DNS support
            enable_dns_hostnames=True,
            enable_dns_support=True,
        )

        CfnOutput(self, "Public-1",
                 value=self.vpc.public_subnets[0].subnet_id)
        CfnOutput(self, "Public-2",
                 value=self.vpc.public_subnets[1].subnet_id)
        CfnOutput(self, "Private-NAT-1",
                 value=self.vpc.private_subnets[0].subnet_id)
        CfnOutput(self, "Private-NAT-2",
                 value=self.vpc.private_subnets[1].subnet_id)
        CfnOutput(self, "Private-1",
                 value=self.vpc.isolated_subnets[0].subnet_id)
        CfnOutput(self, "Private-2",
                 value=self.vpc.isolated_subnets[1].subnet_id)