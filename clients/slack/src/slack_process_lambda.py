import os
import json
import boto3
import requests

from query_engine import core  as qe_core

# Initialize AWS clients
secrets_client = boto3.client('secretsmanager')

# Get Slack secrets from AWS Secrets Manager
def get_slack_secrets(secret_name):
    response = secrets_client.get_secret_value(SecretId=secret_name)
    return json.loads(response['SecretString'])

# Lambda handler
def send_slack_message(channel_id, text):
    slack_secrets = get_slack_secrets(os.environ['SLACK_SECRETS_NAME'])
    slack_token = slack_secrets['botToken']

    try:
        # response = requests.post(
        #     "https://slack.com/api/chat.postMessage",
        #     json={'channel': channel_id, 'text': text},
        #     headers={'Authorization': f'Bearer {slack_token}', 'Content-Type': 'application/json'}
        # )
        # response.raise_for_status()
        # return {'statusCode': response.status_code, 'body': response.json()}
        return {'statusCode': 200, 'body': "Uncomment posting to slack"}
    except requests.exceptions.HTTPError as err:
        #return {'statusCode': response.status_code, 'body': {'error': str(err)}}
        return {'statusCode': 200, 'body': {'error': str(err)}}
    except Exception as e:
        return {'statusCode': 500, 'body': {'error': str(e)}}


def handler(event, context):
    print(f"Event: {event}")
    channel_id = event["request"]["channelId"]
    text = event['request']['text']
    is_bot = event['request']['is_bot']

    if not is_bot:
        processed_text = qe_core.generate_reponse(text)
        return send_slack_message(channel_id, processed_text)

    return {
        'statusCode': 200,
        'body': {'message': "Slack-bot message event"}
    }
