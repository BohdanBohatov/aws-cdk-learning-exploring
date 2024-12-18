from aws_cdk import (
    Stack,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    CfnOutput,
    Duration,
    RemovalPolicy
)
from constructs import Construct

class CdkRoute53Stack(Stack):

    @property
    def get_hosted_zone(self):
        return self.hosted_zone

    def __init__(self, scope: Construct, construct_id: str, load_balancer: elbv2.ApplicationLoadBalancer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.hosted_zone = route53.HostedZone(
            self, "HostedZone",
            zone_name="alphabetagamazeta.site"
        )
        
        self.hosted_zone.apply_removal_policy(RemovalPolicy.RETAIN)

        #route53.ARecord(
        #    self, "A_Record",
        #    zone=self.hosted_zone,
        #    target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(load_balancer)),
        #    record_name=""
        #)

        #route53.ARecord(
        #    self, "WWW_Record",
        #    zone=self.hosted_zone,
        #    target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(load_balancer)),
        #    record_name="www"
        #)

        CfnOutput(
            self, "HostedZoneArn",
            value=self.hosted_zone.hosted_zone_arn
        )