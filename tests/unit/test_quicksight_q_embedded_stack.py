import aws_cdk as core
import aws_cdk.assertions as assertions

from quicksight_q_embedded.quicksight_q_embedded_stack import QuicksightQEmbeddedStack

# example tests. To run these tests, uncomment this file along with the example
# resource in quicksight_q_embedded/quicksight_q_embedded_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = QuicksightQEmbeddedStack(app, "quicksight-q-embedded")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
