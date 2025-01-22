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

    @property
    def get_ec2_group(self):
        return self.ec2_security_group

    def __init__(self, scope: Construct, construct_id: str, config: dict, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC
        self.vpc = ec2.Vpc(
            self,
            "CDK-VPC",
            ip_addresses=ec2.IpAddresses.cidr(config['cidr']),
            max_azs=config['maxAzs'],
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=config['publicSubnetMask'],
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=config['isolatedSubnetMask'],
                ),
                # ec2.SubnetConfiguration(
                #    name="Private-NAT",
                #    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                #    cidr_mask=config['privateSubnetMask'],
                # ),
            ],
            # Enable DNS hostnames and DNS support
            enable_dns_hostnames=config['enableDnsHostnames'],
            enable_dns_support=config['enableDnsSupport'],
            vpc_name="CDK-vpc"
        )

        self.ec2_security_group = ec2.SecurityGroup(
            self, "CDK-Allow-SSH",
            vpc=self.vpc,
            description="Allow inbound trafic from VPC",
            allow_all_outbound=True,
        )


        self.ec2_security_group.add_ingress_rule(
            peer=ec2.Peer.any_ipv4(),
            connection=ec2.Port.tcp(22),
            description="Allow ssh traffic"
        )

        security_group = ec2.SecurityGroup(
            self, "CDK-SecretManagerSecurityGroup",
            vpc=self.vpc,
            description="Allow inbound trafic from VPC",
            allow_all_outbound=True,
        )

        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(self.vpc.vpc_cidr_block),
            connection=ec2.Port.tcp_range(0, 65535),
            description="Allow all inbound traffic from VPC"
        )
        
        #Add endpoint to reach secret manger within VPC
        self.vpc.add_interface_endpoint(
            "SecretMangerEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.SECRETS_MANAGER,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups= [security_group],
        )

        # Add Lambda endpoint
        self.vpc.add_interface_endpoint(
            "LambdaEndpoint",
            service=ec2.InterfaceVpcEndpointAwsService.LAMBDA_,
            private_dns_enabled=True,
            subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[security_group],
        )

        self.vpc.add_gateway_endpoint("S3Endpoint",
                                 service=ec2.GatewayVpcEndpointAwsService.S3)

        
        CfnOutput(self, "Public-1",
                 value=self.vpc.public_subnets[0].subnet_id)
        CfnOutput(self, "Public-2",
                 value=self.vpc.public_subnets[1].subnet_id)
        #CfnOutput(self, "Private-NAT-1",
        #         value=self.vpc.private_subnets[0].subnet_id)
        #CfnOutput(self, "Private-NAT-2",
        #         value=self.vpc.private_subnets[1].subnet_id)
        CfnOutput(self, "Private-1",
                 value=self.vpc.isolated_subnets[0].subnet_id)
        CfnOutput(self, "Private-2",
                 value=self.vpc.isolated_subnets[1].subnet_id)
        CfnOutput(self, "Avaliability zone 1",
                 value=self.vpc.availability_zones[0])
        CfnOutput(self, "Avaliability zone 2",
                 value=self.vpc.availability_zones[1])