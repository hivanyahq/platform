import os
import json
import boto3
import logging
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from query_engine import core  as qe_core

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


IGNORED_SLACK_EVENTS = ("bot_message", "message_deleted")
SLACK_BOT_SECRET = json.loads(
    boto3.client('secretsmanager').get_secret_value(
        SecretId=os.environ['SLACK_SECRETS_NAME']
    )['SecretString']
)
os.environ["SLACK_SIGNING_SECRET"] = SLACK_BOT_SECRET['signingSecret']
os.environ["SLACK_BOT_TOKEN"] = SLACK_BOT_SECRET['botToken']

app = App(
    process_before_response=True,
    token=SLACK_BOT_SECRET['botToken'],
    signing_secret=SLACK_BOT_SECRET['signingSecret'],
)

@app.event("message", matchers=[lambda m: m.get("subtype") not in IGNORED_SLACK_EVENTS])
def handle_message(body, say, logger):
    logger.info(body)
    reply = qe_core.generate_reponse(body)
    say(f"{body} >> {reply}")

def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    slack_response = slack_handler.handle(event, context)
    print("slack_response: {slack_response}")
    return slack_response

# class SlackAuthHandler:
#     def __init__(self):
#         # Init and configure Bolt App
#         secret_name = os.environ['SLACK_SECRETS_NAME']
#         secret_result = boto3.client('secretsmanager').get_secret_value(SecretId=secret_name)
#         secret_object = json.loads(secret_result['SecretString'])
#         self.text = None
#         self.is_human_message = False

#         self.app = App(
#             token=secret_object['botToken'],
#             signing_secret=secret_object['signingSecret'],
#         )

#         # Add a message event listener
#         @self.app.event(
#             "message",
#             matchers=[
#                 lambda message: message.get("subtype") not in ("bot_message", "message_deleted")
#             ]
#         )
#         def handle_message_events(event, say, logger):
#             print(f"text is: {event['text']}")
#             say(f"Text was {event['text']}")

#     def handler(self, event, context):
#         handler = SlackRequestHandler(self.app)

#         response = handler.handle(event, context)
#         print(f"Slack Validation Response: {response}")
#         if response["statusCode"] != 200:
#             raise Exception("Failed to validate slack message")
#         return response


# def lambda_handler(event, context):
#     # print(f"slack_auth_lambda:lambda_handler:event: {event}")
#     # print(f"slack_auth_lambda:lambda_handler:context: {context}")
#     slack_auth_handler = SlackAuthHandler()
#     return slack_auth_handler.handler(event, context)
