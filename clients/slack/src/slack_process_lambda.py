import os
import json
import boto3
import requests

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
        response = requests.post(
            "https://slack.com/api/chat.postMessage",
            json={'channel': channel_id, 'text': text},
            headers={'Authorization': f'Bearer {slack_token}', 'Content-Type': 'application/json'}
        )
        response.raise_for_status()
        return {
            'statusCode': response.status_code,
            'body': response.json()
        }
    except requests.exceptions.HTTPError as http_err:
        return {
            'statusCode': response.status_code,
            'body': {'error': str(http_err)}
        }
    except Exception as e:
        return {
            'statusCode': 500,
            'body': {'error': str(e)}

        }


def handler(event, context):
    print(f"Event: {event}")
    channel_id = event["request"]["channelId"]
    text = event['request']['text']
    is_bot = event['request']['is_bot']

    if not is_bot:
        processed_text = f"Hello from Hivanya! {text}",
        return send_slack_message(channel_id, processed_text)

    # Add your message processing logic here
    return {
        'statusCode': 200,
        'body': {'message': "Slack-bot message event"}
    }
