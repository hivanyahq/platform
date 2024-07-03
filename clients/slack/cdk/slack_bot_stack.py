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
from constructs import Construct

class SlackBotStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Secrets and Parameters
        slack_secrets = secretsmanager.Secret(self, "SlackSecrets",
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

        # Lambda Functions
        self.slack_auth_function = lambda_.Function(
            self, 
            "slack-auth-lambda",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="slack_auth_lambda.handler",
            code=lambda_.Code.from_asset("./clients/slack/src/")
        )

        process_lambda_function = lambda_.Function(
            self, 
            "slack-process-lambda",
            runtime=lambda_.Runtime.PYTHON_3_8,
            handler="slack_process_lambda.handler",
            code=lambda_.Code.from_asset("./clients/slack/src/")
        )

        # State Machines
        validation_and_processing_state_machine = self.build_validation_and_processing_state_machine(process_lambda_function)
        

        # Grant Permissions
        slack_secrets.grant_read(self.slack_auth_function)
        self.channel_id_parameter.grant_read(validation_and_processing_state_machine)
        slack_secrets.grant_read(process_lambda_function)

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
                validation_and_processing_state_machine,
                passthrough_behavior=apigateway.PassthroughBehavior.NEVER,
                request_templates={
                    "application/json": cdk_fn.sub(
                        """
                        {
                            "stateMachineArn": "${StateMachineArn}",
                            "input": "{\\"body\\": $util.escapeJavaScript($input.json('$')), \\"headers\\": {\\"X-Slack-Signature\\": \\"$input.params().header.get('X-Slack-Signature')\\", \\"X-Slack-Request-Timestamp\\": \\"$input.params().header.get('X-Slack-Request-Timestamp')\\", \\"Content-Type\\": \\"application/json\\"}}"
                        }
                        """,
                        {"StateMachineArn": validation_and_processing_state_machine.state_machine_arn}
                    )
                },
                integration_responses=[{
                    "statusCode": "200",
                    "responseTemplates": {
                        "application/json": '''
                          #set($context.responseOverride.status = 204)
                          {}
                        '''
                    }
                }]
            )
        )


    def build_validation_and_processing_state_machine(self, process_lambda_function: lambda_.Function) -> sfn.StateMachine:
        log_group = logs.LogGroup(self, "ValidationAndProcessingStateMachineLogGroup")

        # Validate Slack message
        validate_slack_message = tasks.LambdaInvoke(self, "Validate Slack Message",
            lambda_function=self.slack_auth_function,
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

        # Validate Channel ID and process if valid
        validate_channel_id_and_process = sfn.Choice(self, "Validate and Process Channel ID").when(
            sfn.Condition.string_equals_json_path("$.getParameterResult.Parameter.Value", "$.request.channelId"),
            tasks.LambdaInvoke(self, "Process Lambda", lambda_function=process_lambda_function, result_path="$.lambdaResult"),
        ).otherwise(
            self.send_message(
                "Unauthorized User Message",
                {"text": "You are not authorized to use this command here", "response_type": "ephemeral"},
            )
        )

        # Coordinate states
        definition = validate_slack_message.next(get_channel_id).next(validate_channel_id_and_process)

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
            lambda_function=self.slack_auth_function,  # Use the slack_auth_function for sending messages
            payload=sfn.TaskInput.from_object({"url.$": f"$.{response_url_path}", "body": body}),
            result_path=sfn.JsonPath.DISCARD
        )


# app = core.App()
# AppStack(app, "AppStack")
# app.synth()
