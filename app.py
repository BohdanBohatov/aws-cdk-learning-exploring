#!/usr/bin/env python3
import os
import aws_cdk as cdk

from cdk_s3.cdk_s3_stack import CdkS3Stack
from cdk_vpc.cdk_vpc_stack import CdkVpcStack
from cdk_ec2.cdk_ec2_stack import CdkEc2Stack
from cdk_ec2_lb.cdl_ec2B_lb_stack import CdkEc2LbStack
from cdk_ec2_nginx.cdk_ec2_nginx_stack import CdkEcNginxStack
from cdk_route53.cdk_route53_stack import CdkRoute53Stack

app = cdk.App()
#CdkS3Stack(app, "CdkS3Stack")
vpc_stack = CdkVpcStack(app, "CdkVpcStack")
ec2_stack = CdkEc2LbStack(app, "CdkEc2LbStack", vpc=vpc_stack.get_vpc)
route53_stack = CdkRoute53Stack(app, "CdkRoute53Stack", load_balancer=ec2_stack.get_application_load_balancer) 
app.synth()
