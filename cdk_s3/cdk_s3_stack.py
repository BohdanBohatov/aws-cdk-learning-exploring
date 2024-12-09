from aws_cdk import (
    Duration,
    Stack,
    aws_apigateway as apigw,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_iam as iam
)
from constructs import Construct

class CdkS3Stack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        stage_environment="development"

        list_s3_lambda=_lambda.Function(
            self, "list-s3",
            runtime=_lambda.Runtime.PYTHON_3_13,
            code=_lambda.Code.from_asset("lambdas"),
            handler="list-s3.lambda_handler",
            timeout=Duration.seconds(60),
        )

        list_s3_lambda.add_to_role_policy(
            statement = iam.PolicyStatement(
                actions=["s3:ListAllMyBuckets"],
                resources=["*"]
            )
        )

        api_gateway = apigw.RestApi(
            self, "list-s3-api",
            rest_api_name="List S3 Buckets",
            description="This service lists all S3 buckets.",
            deploy_options=apigw.StageOptions(
                stage_name=stage_environment
            )
        )


        api_arn = api_gateway.arn_for_execute_api(
            method="*",
            path="/",
            stage=stage_environment
        )

        auth_lambda=_lambda.Function(
            self, "authorization",
            runtime=_lambda.Runtime.PYTHON_3_13,
            code=_lambda.Code.from_asset("lambdas"),
            handler="auth_s3.lambda_handler",
            environment= {
                "API_GATEWAY_ARN": api_arn
            }
        )

        authorizer = apigw.RequestAuthorizer(
            self, "s3-authorizer",
            handler=auth_lambda,
            identity_sources=[apigw.IdentitySource.header('auth-s3'),
                               apigw.IdentitySource.query_string('test-s3')],
            results_cache_ttl=Duration.seconds(60)
        )


        #This code to enable this need to reconfigure "methodArn" in authorization lambda more details here https://stackoverflow.com/questions/50331588/aws-api-gateway-custom-authorizer-strange-showing-error
        protected_integration=apigw.LambdaIntegration(list_s3_lambda, proxy=False)
        resource = api_gateway.root
        resource.add_method("GET", protected_integration, authorizer=authorizer,)
        resource.add_method("POST", protected_integration, authorizer=authorizer,)


        #proxy = api_gateway.root.add_proxy(
        #    any_method=False,
        #    default_integration=apigw.LambdaIntegration(list_s3_lambda),
        #)
        #proxy.add_method("GET", apigw.LambdaIntegration(list_s3_lambda))
        #proxy.add_method("POST", apigw.LambdaIntegration(list_s3_lambda))+