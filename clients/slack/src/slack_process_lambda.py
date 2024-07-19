import os
import json
import boto3
import logging
from slack_bolt import App
from slack_bolt.adapter.aws_lambda import SlackRequestHandler

from query_engine import core as qe_core

SlackRequestHandler.clear_all_log_handlers()
logging.basicConfig(format="%(asctime)s %(message)s", level=logging.DEBUG)


IGNORED_MESSAGE_EVENTS = ("bot_message", "message_deleted")

app = App(
    process_before_response=True,
    token=os.environ["BOT_TOKEN"],
    signing_secret=os.environ["SIGNING_SECRET"],
)


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
    #reply = qe_core.generate_reponse(body)
    say(f"Did you say {body['event']['text']} ?")


def lambda_handler(event, context):
    slack_handler = SlackRequestHandler(app=app)
    slack_response = slack_handler.handle(event, context)
    print(f"slack_response: {slack_response}")
    return slack_response
