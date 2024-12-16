from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_iam as iam,
    CfnOutput,
    aws_elasticloadbalancingv2 as elbv2,
    Duration,
    aws_elasticloadbalancingv2_targets as targets
)
from constructs import Construct

class CdkEc2LbStack(Stack):
    
    @property
    def vpc(self):
        return self._vpc
    
    @property
    def security_group(self):
        return self._security_group
    
    @property
    def role(self):
        return self._role
    
    @property
    def key_pair(self):
        return self._key_pair
    
    @property
    def nat_instance(self):
        return self._nat_instance
    
    @property
    def application_load_balancer(self):
        return self._load_balancer
    

    def __init__(self, scope: Construct, construct_id: str, vpc: ec2.Vpc, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        self._vpc = vpc
        self._security_group = self._get_security_group()
        self._role = self._get_ec2_role()
        self._key_pair = self._get_key_pair()
        self._nat_instance = self._get_nat_ec2_instance()
        self._load_balancer = self._get_load_balancer()


    def _get_nat_ec2_instance(self):
        machine_image = ec2.MachineImage.generic_linux({
            "eu-north-1": "ami-004709b136249dff4"
        })

        nat_ec2_instance = ec2.Instance(
            self, "EC2Instance-ngix-nat",
            vpc=self.vpc,
            availability_zone=self.vpc.public_subnets[0].availability_zone,   
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            ),
            security_group=self.security_group,
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.T3,
                ec2.InstanceSize.SMALL
            ),
            machine_image=machine_image,
            role=self.role,
            key_pair=self.key_pair,
            detailed_monitoring=False,
        )

        return nat_ec2_instance


    #Security group with allowed icmp and ssh
    def _get_security_group(self):
        security_group = ec2.SecurityGroup(
            self, "EC2SecurityGroup",
            vpc=self.vpc,
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

        security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow http access from anywhere",
        )


        return security_group
    

    def _get_ec2_role(self):
        # Create Role for EC2
        role = iam.Role(
            self, "EC2Role",
            assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
        )
        return role


    def _get_key_pair(self):
        key = ec2.KeyPair.from_key_pair_name(
            self,
            "ImportedKeyPair",
            key_pair_name="bohdan-ssh-key"
        )
        return key


    def _get_load_balancer(self):
        lb = elbv2.ApplicationLoadBalancer(
            self, "ApplicationLoadBalancer",
            vpc=self.vpc,
            internet_facing=True,
            security_group=self.security_group,
            cross_zone_enabled=True,
            load_balancer_name="ec2-lb",
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            )
        )

        # Create target group
        target_group = elbv2.ApplicationTargetGroup(
            self, "EC2TargetGroup",
            vpc=self.vpc,
            port=80,
            protocol=elbv2.ApplicationProtocol.HTTP,
            target_type=elbv2.TargetType.INSTANCE,
            health_check=elbv2.HealthCheck(
                path="/",
                healthy_http_codes="200",
                interval=Duration.seconds(30),
                timeout=Duration.seconds(5)
            ),
        )

        instance_target = targets.InstanceTarget(
            self.nat_instance, 80
        )

        target_group.add_target(instance_target)

        # Add listener
        lb.add_listener(
            "Ec2Instance",
            port=80,
            default_target_groups=[target_group]
        )

        # Output the load balancer DNS name
        CfnOutput(
            self, "LoadBalancerDNS",
            value=lb.load_balancer_dns_name
        )
        return lb
        