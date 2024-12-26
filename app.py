#!/usr/bin/env python3
import aws_cdk as cdk

from lib.stacks.cdk_certificate_manager_stack import CdkCertificateStack
from lib.stacks.cdk_create_table_stack import CdkCreatePostgresTableStack
from lib.stacks.cdk_lambda_layer_stack import CdkLambdaLayerStack
from lib.stacks.cdk_route53_stack import CdkRoute53Stack
from lib.stacks.cdk_rsd_postgres_stack import CdkPostgresStack
from lib.stacks.cdk_s3_stack import CdkS3Stack
from lib.stacks.cdk_vpc_stack import CdkVpcStack
from lib.stacks.cdl_ec2B_lb_stack import CdkEc2LbStack
from lib.utils.config import Configuration

app = cdk.App()
env_name = app.node.try_get_context('env') or 'dev'
config = Configuration(env_name)

cdk_s3 = CdkS3Stack(app, "CdkS3Stack")
vpc_stack = CdkVpcStack(app, "CdkVpcStack", config.get_vpc_config() )
ec2_lb_stack = CdkEc2LbStack(app, "CdkEc2LbStack", vpc=vpc_stack.get_vpc)
route53_stack = CdkRoute53Stack(app, "CdkRoute53Stack", load_balancer=ec2_lb_stack.get_application_load_balancer) 
tls_certificate_stack = CdkCertificateStack(app, "CdkCertificateStack", hosted_zone=route53_stack.get_hosted_zone)
rds_postgres_stack = CdkPostgresStack(app, "CdkRdsPostgresStack", vpc=vpc_stack.get_vpc)
lambda_layer_stack = CdkLambdaLayerStack(app, "CdkLambdaLayerStack")
create_table_stack = CdkCreatePostgresTableStack(app, "CdkCreateTableStack", 
                                                vpc=vpc_stack.get_vpc, 
                                                database=rds_postgres_stack.get_database, 
                                                postgres_layer=lambda_layer_stack.get_layer)


app.synth()
