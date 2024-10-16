from aws_cdk import (
    # Duration,
    Stack,
    # aws_sqs as sqs,
)
from constructs import Construct

class QuicksightQEmbeddedStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # write lambda role
        role = self._create_lambda_role() 

        # write lambda function
        lambda_function = self._create_lambda_function(role, 'quicksight_q_embedded_lambda',)