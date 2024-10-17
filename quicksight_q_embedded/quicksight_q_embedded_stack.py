from aws_cdk import (
    aws_iam as iam,
    aws_lambda as _lambda,
    aws_apigateway as apigateway,
    aws_logs as logs,
    aws_quicksight as quicksight,
    Stack,
    RemovalPolicy,
    Duration,
    CfnOutput,
    Stack
)
from constructs import Construct


class QuicksightQEmbeddedStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        quicksightdataset = quicksight.CfnDataSet(self, "MyDataset",
            aws_account_id=self.account,
            data_set_id="my-dataset-id",  # Choose a unique ID for your dataset
            name="My Dataset",
            import_mode="SPICE",
            physical_table_map={
                "YourTableId": quicksight.CfnDataSet.PhysicalTableMapProperty(
                    custom_sql=quicksight.CfnDataSet.CustomSqlProperty(
                        data_source_arn="arn:aws:quicksight:REGION:ACCOUNT_ID:datasource/YOUR_DATASOURCE_ID",
                        name="YourCustomSqlName",
                        sql="SELECT * FROM your_table"
                    )
                )
            })
        quicksightTopic = quicksight.CfnTopic(self, "MyTopic",
            aws_account_id=self.account,  
            name="My Topic",
            description="Description of my topic",
            data_set_references=[
                quicksight.CfnTopic.DataSetReferenceProperty(
                    data_set_arn=quicksightdataset.attr_arn,
                    data_set_placeholder="PRIMARY_DATASET"
                )
            ]
        )
        
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
            environment={
                "TopicId": quicksightTopic.id,  
                "DashboardRegion": self.region,  # Use the stack's region
                "DEBUG_MODE": "false",  # Add any other environment variables you need
                "LOG_LEVEL": "INFO"
            }          
        )
        # create API Gateway
        api = apigateway.RestApi(self, "quicksight-qembedded-api",
            rest_api_name="quicksight-qembedded-api",
            deploy_options=apigateway.StageOptions(stage_name="prod"),
            default_method_options=apigateway.MethodOptions(
                authorization_type=apigateway.AuthorizationType.IAM
            )
        )                
        proxy_resource = api.root.add_proxy(
            default_integration=api.LambdaIntegration(lambda_function),
            path_part="{proxy+}")
        
        CfnOutput(self, "ApiUrl",value=f"https://{api.rest_api_id}.execute-api.{self.region}.amazonaws.com/prod",
                  description="API Gateway endpoint URL for Prod stage")