import os
import json
import boto3
import logging
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from query_engine import core  as qe_core

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


IGNORED_MESSAGE_EVENTS = ("bot_message", "message_deleted")
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

@app.event(
        "message",
        matchers=[lambda message: message.get("subtype") not in IGNORED_MESSAGE_EVENTS]
)
def handle_message(body, say, logger):
    logger.info(body)
    reply = qe_core.generate_reponse(body)
    say(f"{reply}")

def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    slack_response = slack_handler.handle(event, context)
    print(f"slack_response: {slack_response}")
    return slack_response

