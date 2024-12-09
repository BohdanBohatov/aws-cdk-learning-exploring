#!/usr/bin/env python3
import os
import aws_cdk as cdk

from cdk_s3.cdk_s3_stack import CdkS3Stack


app = cdk.App()
CdkS3Stack(app, "CdkS3Stack"
    )

app.synth()
