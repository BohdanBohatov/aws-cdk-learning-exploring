import aws_cdk as core
import aws_cdk.assertions as assertions

from lib.cdk_s3_stack import CdkS3Stack

# example tests. To run these tests, uncomment this file along with the example
# resource in cdk_s3/cdk_s3_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = CdkS3Stack(app, "cdk-s3")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
