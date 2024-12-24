#!/usr/bin/env python3
import os
import aws_cdk as cdk


from lib.stacks.cdk_s3_stack import CdkS3Stack
from lib.stacks.cdk_vpc_stack import CdkVpcStack
from lib.stacks.cdk_ec2_stack import CdkEc2Stack
from lib.stacks.cdl_ec2B_lb_stack import CdkEc2LbStack
from lib.stacks.cdk_ec2_nginx_stack import CdkEcNginxStack
from lib.stacks.cdk_route53_stack import CdkRoute53Stack
from lib.stacks.cdk_certificate_manager_stack import CdkCertificateStack
from lib.stacks.cdk_rsd_postgres_stack import CdkPostgresStack
from lib.stacks.cdk_lambda_layer_stack import CdkLambdaLayerStack
from lib.stacks.cdk_create_table_stack import CdkCreatePostgresTableStack
from lib.utils.config import Configuration



class InfrastructureStack(cdk.Stack):
    def __init__(self) -> None:

        self.app = cdk.App()
        self.env_name = self.app.node.try_get_context('env') or 'dev'
        self.config = Configuration(self.env_name)
        
        #CdkS3Stack(app, "CdkS3Stack")
        vpc_stack = CdkVpcStack(self.app, self.config.get_vpc_config(), "CdkVpcStack")
        ec2_lb_stack = CdkEc2LbStack(self.app, "CdkEc2LbStack", vpc=vpc_stack.get_vpc)
        route53_stack = CdkRoute53Stack(self.app, "CdkRoute53Stack", load_balancer=ec2_lb_stack.get_application_load_balancer) 
        tls_certificate_stack = CdkCertificateStack(self.app, "CdkCertificateStack", hosted_zone=route53_stack.get_hosted_zone)
        rds_postgres_stack = CdkPostgresStack(self.app, "CdkRdsPostgresStack", vpc=vpc_stack.get_vpc)
        lambda_layer_stack = CdkLambdaLayerStack(self.app, "CdkLambdaLayerStack")
        create_table_stack = CdkCreatePostgresTableStack(self.app, "CdkCreateTableStack", 
                                                        vpc=vpc_stack.get_vpc, 
                                                        database=rds_postgres_stack.get_database, 
                                                        postgres_layer=lambda_layer_stack.get_layer)


        self.app.synth()
