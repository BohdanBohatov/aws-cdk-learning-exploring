from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

class CdkEc2Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        #Create Security Group
        security_group = ec2.SecurityGroup(
            self, "EC2SecurityGroup",
            vpc=vpc,
            description="Allow SSH (TCP port 22) in",
            allow_all_outbound=True,
        )
        
        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(22),
            "allow ssh access from anywhere",
        )

        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.icmp_ping(),
            "allow ping from anywhere",
        )

        # Create Role for EC2
        role = iam.Role(
            self, "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )

        key_pair = self.get_key_pair()

        # Create EC2 Instance
        instance = ec2.Instance(
            self, "EC2Instance-1",
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            ),
            security_group=security_group,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.SMALL
            ),
            machine_image=ec2.AmazonLinuxImage(
                generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2023
            ),
            role=role,
            key_pair=key_pair,
        )

    
    def get_key_pair(self):
        return ec2.KeyPair.from_key_pair_name(
            self,
            "ImportedKeyPair",
            key_pair_name="bohdan-ssh-key"
        )

