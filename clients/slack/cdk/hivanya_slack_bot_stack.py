from aws_cdk import (
    Stack,
    Duration,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_iam as iam,
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

        # Define lambda for auth
        self.slack_process_function = lambda_.DockerImageFunction(
            self,
            "SlackProcessLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                ".",
                file="Dockerfile.clients.slack",
                cmd=["slack_process_lambda.lambda_handler"],
            ),
            environment={
                "BOT_TOKEN": secrets.secret_value_from_json("botToken").to_string(),
                "SIGNING_SECRET": secrets.secret_value_from_json("signingSecret").to_string(),
                "NEO4J_URI": secrets.secret_value_from_json("NEO4J_URI").to_string(),
                "NEO4J_USER": secrets.secret_value_from_json("NEO4J_USER").to_string(),
                "NEO4J_PASSWORD": secrets.secret_value_from_json("NEO4J_PASSWORD").to_string(),
                "OPENAI_API_KEY": secrets.secret_value_from_json("OPENAI_API_KEY").to_string(),
            },
            architecture=lambda_.Architecture.ARM_64,
            role=self.lambda_role,
            timeout=Duration.minutes(5),
        )

        # Grant Permissions
        #secrets.grant_read(self.slack_process_function)

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
            default_integration=apigateway.LambdaIntegration(self.slack_process_function)
        )
