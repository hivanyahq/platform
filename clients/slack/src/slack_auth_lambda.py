import os
import json
import boto3
import base64
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler
from slack_bolt.error import BoltUnhandledRequestError



class SlackAuthHandler:
    def __init__(self):
        # Init and configure Bolt App
        secret_name = os.environ['SLACK_SECRETS_NAME']
        secret_result = boto3.client('secretsmanager').get_secret_value(SecretId=secret_name)
        secret_object = json.loads(secret_result['SecretString'])
        self.text = None
        self.is_human_message = False

        self.app = App(
            token=secret_object['botToken'],
            signing_secret=secret_object['signingSecret'],
        )

        # Add a message event listener
        @self.app.event(
            "message",
            matchers=[
                lambda message: message.get("subtype") not in ("bot_message", "message_deleted")
            ]
        )
        def handle_message_events(event):
            self.text = event['text']
            self.is_human_message = True


    def handler(self, event, context):
        event['isBase64Encoded'] = True
        handler = SlackRequestHandler(self.app)

        response = handler.handle(event, context)
        print(f"Slack Validation Response: {response}")
        if response["statusCode"] != 200:
            raise Exception("Failed to validate slack message")

        # create validated response payload for downstream tasks
        payload = json.loads(base64.b64decode(event["body"]).decode("utf-8"))
        validated_response = {
            "statusCode": 200,
            "requestType": payload.get('type'),
            "challenge": payload.get('challenge'),
            "channelId": payload.get('event').get('channel'),
            "text": self.text or '',
            "is_bot": not self.is_human_message,
        }
        print(f"validated_response: {validated_response}")

        return validated_response


def lambda_handler(event, context):
    print(f"slack_auth_lambda:lambda_handler:event: {event}")
    slack_auth_handler = SlackAuthHandler()
    return slack_auth_handler.handler(event, context)
