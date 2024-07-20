import os
import json
import boto3
import logging
from slack_bolt import App
from slack_sdk import WebClient
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

#from query_engine import QueryEngine

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


IGNORED_MESSAGE_EVENTS = ("bot_message", "message_deleted")
SLACK_BOT_SECRET = json.loads(
    boto3.client("secretsmanager").get_secret_value(
        SecretId=os.environ["SLACK_SECRETS_NAME"]
    )["SecretString"]
)
NEO4J_URI = SLACK_BOT_SECRETS["NEO4J_URI"]
NEO4J_USER = SLACK_BOT_SECRETS["NEO4J_USER"]
NEO4J_PASSWORD = SLACK_BOT_SECRETS["NEO4J_PASSWORD"]
OPENAI_API_KEY = SLACK_BOT_SECRETS["OPENAI_API_KEY"]

#engine = QueryEngine(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY)
app = App(
    process_before_response=True,
    token=SLACK_BOT_SECRETS['botToken'],
    signing_secret=SLACK_BOT_SECRETS['signingSecret'],
)

client = WebClient(token=SLACK_BOT_SECRETS['botToken'])


# New functionality
@app.event("app_home_opened")
def update_home_tab(client, event, logger):
    try:
        client.views_publish(
            user_id=event["user"],
            view={
                "type": "home",
                "callback_id": "home_view",
                # body of the view
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Welcome to HiVanya! :tada:",
                        },
                    },
                    {"type": "divider"},
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "Single Source of Truth for all Product & Engineering Information.",
                        },
                    },
                    {
                        "type": "actions",
                        "elements": [
                            {
                                "type": "button",
                                "text": {
                                    "type": "plain_text",
                                    "text": "Visit HiVanya Webpage",
                                },
                                "url": "https://hivanya.com",
                            }
                        ],
                    },
                ],
            },
        )

    except Exception as e:
        logger.error(f"Error publishing home tab: {e}")


@app.event(
    "message",
    matchers=[lambda message: message.get("subtype") not in IGNORED_MESSAGE_EVENTS],
)
def handle_message(body, say, logger):
    logger.info(body)
    query = body['event']['text']
    print(f"query is: {query}")
    say(f"Hi, did you say {query}")
    #reply = engine.ask(body)
    #say(f"{reply.get('response')}")
    #client.chat_postMessage(channel='D07AM8G06RY', text=reply.get('response'))


def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    slack_response = slack_handler.handle(event, context)
    print(f"slack_response: {slack_response}")
    return slack_response
