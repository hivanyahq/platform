import os
import json
import boto3
import base64
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

# import logging
# logging.basicConfig(level=logging.DEBUG)

# Set up logging
# logger = logging.getLogger()

# Configure logging for SlackRequestHandler
# slack_request_handler_logger = logging.getLogger('slack_bolt.adapter.aws_lambda.SlackRequestHandler')
# slack_request_handler_logger.setLevel(logging.DEBUG)
# # Define a custom handler to capture logs from SlackRequestHandler
# slack_request_handler_log_handler = logging.StreamHandler()
# slack_request_handler_log_handler.setLevel(logging.DEBUG)
# formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
# slack_request_handler_log_handler.setFormatter(formatter)
# slack_request_handler_logger.addHandler(slack_request_handler_log_handler)


# def log_message(logger, event):
#     logger.info(f"(MSG) User: {event['user']}\nMessage: {event['text']}")


class SlackAuthHandler:
    def __init__(self):
        # Init and configure Bolt App
        secret_name = os.environ['SLACK_SECRETS_NAME']
        secret_result = boto3.client('secretsmanager').get_secret_value(SecretId=secret_name)
        secret_object = json.loads(secret_result['SecretString'])

        self.app = App(
            token=secret_object['botToken'],
            signing_secret=secret_object['signingSecret']
        )

    def handler(self, event, context):
        event['isBase64Encoded'] = True
        handler = SlackRequestHandler(self.app)

        response = handler.handle(event, context)
        print(f"response: {response}")

        if response["statusCode"] != 200:
            raise Exception('Failed to validate slack message')

        payload = json.loads(base64.b64decode(event['body']).decode('utf-8'))
        response['requestType'] = payload.get('type')
        response['challenge'] = payload.get('challenge')

        return response
        

# Create an instance of the handler class
slack_auth_handler = SlackAuthHandler()

def lambda_handler(event, context):
    print(f"slack_auth_lambda:lambda_handler:event: {event}")
    return slack_auth_handler.handler(event, context)
