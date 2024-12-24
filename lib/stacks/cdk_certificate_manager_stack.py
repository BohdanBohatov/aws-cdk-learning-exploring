from aws_cdk import (
    Stack,
    aws_certificatemanager as acm,
    aws_route53 as route53,
    CfnOutput,
    RemovalPolicy
)
from constructs import Construct

#TODO not finished need to manually create records in route53 
class CdkCertificateStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, hosted_zone: route53.HostedZone, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create an ACM certificate
        certificate = acm.Certificate(
            self, 
            "ABGZ_DomainCertificate",
            domain_name="alphabetagamazeta.site",
            validation=acm.CertificateValidation.from_dns(hosted_zone),
            subject_alternative_names=["*.alphabetagamazeta.site"]
        )
        
        certificate.apply_removal_policy(RemovalPolicy.RETAIN)

        # Output the certificate ARN
        CfnOutput(
            self,
            "CertificateArn",
            value=certificate.certificate_arn,
            description="Certificate ARN"
        )
