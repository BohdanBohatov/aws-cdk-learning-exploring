from aws_cdk import (
    Stack,
    aws_route53 as route53,
    aws_route53_targets as targets,
    aws_elasticloadbalancingv2 as elbv2,
    aws_iam as iam,
    CfnOutput,
    Duration,
)
from constructs import Construct

class CdkRoute53Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, load_balancer: elbv2.ApplicationLoadBalancer, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hosted_zone = route53.HostedZone(
            self, "HostedZone",
            zone_name="alphabetagamazeta.site"
        )

        route53.ARecord(
            self, "Record",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(load_balancer)),
            record_name=""
        )

        route53.ARecord(
            self, "WWW_Record",
            zone=hosted_zone,
            target=route53.RecordTarget.from_alias(targets.LoadBalancerTarget(load_balancer)),
            record_name="www"
        )

        CfnOutput(
            self, "HostedZoneName",
            value=hosted_zone.zone_name
        )

        CfnOutput(
            self, "HostedZoneId",
            value=hosted_zone.hosted_zone_id
        )

        CfnOutput(
            self, "HostedZoneArn",
            value=hosted_zone.hosted_zone_arn
        )