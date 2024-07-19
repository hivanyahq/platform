import json
from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
)
from constructs import Construct


class SlackBotStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        secret_template = {
            "botToken": "<insert bot token here in AWS Console>",
            "signingSecret": "<insert signing secret here in AWS Console>",
            "NEO4J_URI": "",
            "NEO4J_USER": "",
            "NEO4J_PASSWORD": "",
            "OPENAI_API_KEY": ""
        }
        # Secrets and Parameters
        slack_secrets = secretsmanager.Secret(
            self,
            "SlackSecrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template=json.dumps(secret_template),
                generate_string_key="signingSecret",
            ),
        )

        # Define lambda for auth
        self.slack_auth_function = lambda_.DockerImageFunction(
            self,
            "slackAuthLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                ".",
                file="Dockerfile.clients.slack",
                cmd=["slack_process_lambda.lambda_handler"],
            ),
            environment={"SLACK_SECRETS_NAME": slack_secrets.secret_name},
            architecture=lambda_.Architecture.ARM_64,
        )

        # Grant Permissions
        slack_secrets.grant_read(self.slack_auth_function)

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
            default_integration=apigateway.LambdaIntegration(self.slack_auth_function)
        )
