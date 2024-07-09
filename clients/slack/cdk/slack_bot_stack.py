import json
from aws_cdk import (
    Stack,
    aws_apigateway as apigateway,
    aws_lambda as lambda_,
    aws_logs as logs,
    aws_secretsmanager as secretsmanager,
    aws_ssm as ssm,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    Fn as cdk_fn,
    RemovalPolicy
)
from aws_cdk.aws_stepfunctions import Pass, Result, JsonPath

from constructs import Construct

class SlackBotStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Secrets and Parameters
        slack_secrets = secretsmanager.Secret(
            self,
            "SlackSecrets",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"botToken":"<insert bot token here in AWS Console>","signingSecret":"<insert signing secret here in AWS Console>"}',
                generate_string_key="signingSecret"
            )
        )

        self.channel_id_parameter = ssm.StringParameter(self, "SlackChannelIdParameter",
            parameter_name="SlackChannelIdParameter",
            description="The permitted slack channel ID for Slack Bot requests",
            string_value="<insert channel ID here in AWS Console>"
        )

        # Define lambda for auth
        self.slack_auth_function  = lambda_.DockerImageFunction(
            self, 
            "slackAuthLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "./clients/slack/",
                cmd=["slack_auth_lambda.lambda_handler"],
            ),
            environment={"SLACK_SECRETS_NAME": slack_secrets.secret_name},
            architecture=lambda_.Architecture.ARM_64,
        )

        # Define lambda for processing, post auth
        self.slack_process_function = lambda_.DockerImageFunction(
            self, 
            "slackProcessLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "./clients/slack/",
                cmd=["slack_process_lambda.handler"],
            ),
            # environment={"SLACK_SECRETS_NAME": slack_secrets.secret_name},
            architecture=lambda_.Architecture.ARM_64,
        )

        # Define lambda for sending back messages
        self.slack_https_client_function = lambda_.DockerImageFunction(
            self, 
            "slackHttpsClientLambda",
            code=lambda_.DockerImageCode.from_image_asset(
                "./clients/slack/",
                cmd=["slack_https_client.lambda_handler"],
            ),
            environment={"SLACK_SECRETS_NAME": slack_secrets.secret_name},
            architecture=lambda_.Architecture.ARM_64,
        )

        # State Machine
        processing_state_machine = self.build_validate_and_process_state_machine(
            self.slack_auth_function,
            self.slack_process_function
        )
        
        # Grant Permissions
        slack_secrets.grant_read(self.slack_auth_function)
        self.channel_id_parameter.grant_read(processing_state_machine)
        slack_secrets.grant_read(self.slack_process_function)

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
            )
        )

        bolt_api.root.add_proxy(
            default_integration=apigateway.StepFunctionsIntegration.start_execution(
                processing_state_machine,
                passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                #headers=True,
                #request_context={"http_method": True},
                #content_handling=apigateway.ContentHandling.CONVERT_TO_BINARY,
                request_templates={
                    "application/json": cdk_fn.sub(
                        """
                        {
                            "stateMachineArn": "${StateMachineArn}",
                            "input": "{\\"body\\": \\"${encodedBody}\\",\\"headers\\": {${headers}}, \\"requestContext\\": {${requestContext}} }"
                        }
                        """,
                        {
                            "StateMachineArn": processing_state_machine.state_machine_arn,
                            "encodedBody": "$util.base64Encode($input.body)",
                            "headers": """\\"X-Slack-Signature\\": \\"$input.params().header.get('X-Slack-Signature')\\", \\"X-Slack-Request-Timestamp\\": \\"$input.params().header.get('X-Slack-Request-Timestamp')\\", \\"Content-Type\\": \\"application/json\\" """,
                            "requestContext": """\\"http\\": {\\"method\\": \\"$context.httpMethod\\"}"""
                        }
                    )
                },
                integration_responses=[
                    {
                        "statusCode": "200",
                        "responseTemplates": {"application/json": """{"challenge": $input.json('$.output')"}"""},
                    }
                ]
            )
        )
        #$util.toJson($inputRoot.body.output)
        # {"challenge3": "$inputRoot.body"} # empty!!

        #set($inputRoot = $input.path('$'))
        #set($body = $util.parseJson($inputRoot.body))
        #{"challenge4": "$body.Cahllenge"}

        #  {"challenge8": "$inputRoot"} => "{billingDetails={billedD...}"
        # {"challenge9": $util.parseJson($inputRoot)} ==> empty
        # {"challenge12": "$input.body"} =>  "{billingDetails={billedD...}
        #{"challenge65": $input.json('$')

        #{"challenge": $input.json('$.output')"} 500 but verified


    def build_validate_and_process_state_machine(
            self,
            auth_function: lambda_.Function,
            process_lambda_function: lambda_.Function,
    ) -> sfn.StateMachine:
        log_group = logs.LogGroup(self, "ValidationAndProcessingStateMachineLogGroup")

        # Validate Slack message
        validate_slack_message = tasks.LambdaInvoke(self, "Validate Slack Message",
            lambda_function=auth_function,
            result_selector={"request.$": "$.Payload"}
        ).add_catch(sfn.Fail(self, "Validate Slack Message Failure"), errors=["States.ALL"])

        # Get Channel ID value
        get_channel_id = sfn.CustomState(self, "Get Channel ID Value",
            state_json={
                "Type": "Task",
                "Resource": "arn:aws:states:::aws-sdk:ssm:getParameter",
                "Parameters": {"Name": self.channel_id_parameter.parameter_name},
                "ResultPath": "$.getParameterResult",
            }
        )

        definition = validate_slack_message.next(
            sfn.Choice(
                self, 
                "Is Event Verification Call"
            ).when(
                sfn.Condition.string_equals("$.request.requestType", "url_verification"),
                Pass(
                    self, 
                    "Return Challenge Response",
                    parameters={
                        "challenge": sfn.JsonPath.string_at("$.request.challenge"),
                        "content-type": "application/json"
                    },
                    # result=sfn.Result.from_object({"body": "$.request.body"}),
                    # result_path="$.request.body"
                )
            ).otherwise(
                get_channel_id.next(
                    sfn.Choice(
                        self, 
                        "Validate and Process Channel ID"
                    ).when(
                        sfn.Condition.string_equals_json_path("$.getParameterResult.Parameter.Value", "$.request.channelId"),
                        tasks.LambdaInvoke(
                            self, "Process Lambda", lambda_function=process_lambda_function, result_path="$.lambdaResult"
                        )
                    ).otherwise(
                        self.send_message(
                            "Unauthorized User Message",
                            {"text": "You are not authorized to use this command here", "response_type": "ephemeral"},
                        )
                    )
                )
            )
        )

        return sfn.StateMachine(self, "SlackBotValidateAndProcess",
            definition=definition,
            state_machine_type=sfn.StateMachineType.EXPRESS,
            logs=sfn.LogOptions(
                destination=log_group,
                level=sfn.LogLevel.ALL,
                include_execution_data=True
            )
        )


    def send_message(self, id: str, body: dict, response_url_path: str = "request.responseUrl") -> tasks.LambdaInvoke:
        return tasks.LambdaInvoke(self, id,
            lambda_function=self.slack_https_client_function,
            payload=sfn.TaskInput.from_object({"url.$": f"$.{response_url_path}", "body": body}),
            result_path=sfn.JsonPath.DISCARD
        )

