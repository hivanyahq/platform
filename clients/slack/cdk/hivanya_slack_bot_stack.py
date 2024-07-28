from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_iam as iam,
    aws_sns as sns,
    aws_sns_subscriptions as subscriptions,
)
from constructs import Construct
from aws_cdk.aws_secretsmanager import Secret



class HiVanyaSlackBotStack(Stack):
    def __init__(self, scope: Construct, id: str,  secrets: Secret, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create an IAM Role for the Lambda function
        self.lambda_role = iam.Role(
            self, "SlackLambdaExecutionRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AWSLambdaBasicExecutionRole")
            ]
        )

         # Create SNS Topic
        self.sns_topic = sns.Topic(
            self, "SlackMessageTopic",
            display_name="Slack Message Topic"
        )

        # Add policy to allow Lambda to publish to SNS topic
        self.lambda_role.add_to_policy(
            iam.PolicyStatement(
                actions=["SNS:Publish"],
                resources=[self.sns_topic.topic_arn]
            )
        )

        # Define lambda for auth
        self.slack_api_function = lambda_.DockerImageFunction(
            self,
            "SlackApiLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                ".",
                file="Dockerfile.clients.slack",
                cmd=["slack_api_lambda.lambda_handler"],
            ),
            environment={
                "SNS_TOPIC_ARN": self.sns_topic.topic_arn,
                "BOT_TOKEN": secrets.secret_value_from_json("botToken").to_string(),
                "SIGNING_SECRET": secrets.secret_value_from_json("signingSecret").to_string(),
            },
            architecture=lambda_.Architecture.ARM_64,
            role=self.lambda_role,
            timeout=Duration.minutes(1),  # todo: check if needed
        )

        # Define lambda for processing SNS messages
        self.slack_process_lambda = lambda_.DockerImageFunction(
            self,
            "SlackProcessLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                ".",
                file="Dockerfile.clients.slack",
                cmd=["slack_process_lambda.lambda_handler"],
            ),
            environment={
                "NEO4J_URI": secrets.secret_value_from_json("NEO4J_URI").to_string(),
                "NEO4J_USER": secrets.secret_value_from_json("NEO4J_USER").to_string(),
                "NEO4J_PASSWORD": secrets.secret_value_from_json("NEO4J_PASSWORD").to_string(),
                "OPENAI_API_KEY": secrets.secret_value_from_json("OPENAI_API_KEY").to_string(),
                "BOT_TOKEN": secrets.secret_value_from_json("botToken").to_string(),
                "SIGNING_SECRET": secrets.secret_value_from_json("signingSecret").to_string(),
            },
            architecture=lambda_.Architecture.ARM_64,
            role=self.lambda_role,
            timeout=Duration.minutes(5),
            memory_size=256,
        )

        # Subscribe the slack_process_lambda to the SNS topic
        self.sns_topic.add_subscription(subscriptions.LambdaSubscription(self.slack_process_lambda))


        # API Gateway
        bolt_api = apigateway.RestApi(
            self,
            "SlackBotApi",
            rest_api_name="Interactive Slack Bot API",
            description="This is the API service for the Interactive Slack Bot.",
            deploy_options=apigateway.StageOptions(
                logging_level=apigateway.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
                # access_log_format=apigateway.AccessLogFormat.clf()
            ),
        )
        # Add a proxy resource to the root of the API Gateway
        bolt_api.root.add_proxy(
            default_integration=apigateway.LambdaIntegration(self.slack_api_function)
        )
