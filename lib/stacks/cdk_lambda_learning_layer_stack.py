from aws_cdk import (
    Stack,
    Duration,
    aws_iam as iam,
    aws_lambda as _lambda,
    custom_resources as cr,
)

from constructs import Construct


class CdkLambdaLearningLayerStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        layer = _lambda.LayerVersion(
            self, "CustomLayer",
            code=_lambda.Code.from_asset("layers"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Libraries for lambda",
            layer_version_name="libraries"
        )

        request_lambda = _lambda.Function(
            self, "SendRequestLambda",
            runtime=_lambda.Runtime.PYTHON_3_12,
            handler="request_lambda.lambda_handler",
            code=_lambda.Code.from_asset("lambdas/request_lambda"),
            layers=[layer],
            timeout=Duration.seconds(120),
        )

        custom_resource = cr.AwsCustomResource(
            self, "RequestCustomResource",
            on_create=cr.AwsSdkCall(
                physical_resource_id=cr.PhysicalResourceId.of("RequestCustomResourceCreate"),
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": request_lambda.function_name,
                    "Payload": '{"RequestType": "Create"}'
                }
            ),
            on_update=cr.AwsSdkCall(
                physical_resource_id=cr.PhysicalResourceId.of("RequestCustomResourceUpdate"),
                service="Lambda",
                action="invoke",
                parameters={
                    "FunctionName": request_lambda.function_name,
                    "Payload": '{"RequestType": "Update"}'
                }
            ),
            on_delete=cr.AwsSdkCall(
                physical_resource_id=cr.PhysicalResourceId.of("RequestCustomResourceDelete"),
                service="Lambda",
                action="ignore",
                parameters={
                    #No need to implement delete function
                }
            ),
            policy=cr.AwsCustomResourcePolicy.from_statements([
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["lambda:InvokeFunction"],
                    resources=[request_lambda.function_arn]
                )
            ])
        )