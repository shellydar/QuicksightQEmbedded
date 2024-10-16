from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_logs as logs,
    # aws_sqs as sqs,
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct


class QuicksightQEmbeddedStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # create IAM policy
        policy = iam.ManagedPolicy(self, "quicksight-qembedded-policy",
            statements=[
                iam.PolicyStatement(
                    effect=iam.Effect.ALLOW,
                    actions=["logs:CreateLogStream",
                             "quicksight:GenerateEmbedUrlForAnonymousUser",
                            "quicksight:GenerateEmbedUrlForRegisteredUser",
                            "logs:CreateLogGroup",
                            "logs:PutLogEvents"
                            ],
                    resources=["*"]
                    )
            ]
        )
        # create IAM role
        role = iam.Role(self, "quicksight-qembedded-role",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[policy]
        )
        #create lambda function
        lambda_function = _lambda.Function(self, "quicksight-qembedded-lambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="lambda_function.lambda_handler",
            code=_lambda.Code.from_asset("lambda"),
            role=role,
            timeout=Duration.seconds(120)
        )
        # create API Gateway
        api = apigateway.RestApi(self, "quicksight-qembedded-api",
            rest_api_name="quicksight-qembedded-api",
            deploy_options=apigateway.StageOptions(stage_name="prod"),
            default_method_options=apigateway.MethodOptions(
                authorization_type=apigateway.AuthorizationType.IAM
            )
        )                