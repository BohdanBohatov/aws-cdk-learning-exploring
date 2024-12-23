from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    
)
from constructs import Construct

class CdkLambdaLayerStack(Stack):

    @property
    def get_layer(self):
        return self.lambda_layer

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.lambda_layer = _lambda.LayerVersion(
            self,
            code=_lambda.Code.from_asset("layers"),
            compatible_runtimes=[_lambda.Runtime.PYTHON_3_12],
            description="Layer that has psycopg2, idna, request, urllib3",
            id="libraries"
        )