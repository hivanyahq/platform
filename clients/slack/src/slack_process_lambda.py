import os
import json
import boto3
import requests

from query_engine import QueryEngine

# Slack token and channel
SLACK_TOKEN = os.getenv('BOT_TOKEN')
SLACK_CHANNEL = os.getenv('SLACK_CHANNEL')  # Add this environment variable if needed

engine = QueryEngine(
    os.environ["NEO4J_URI"],
    os.environ["NEO4J_USER"],
    os.environ["NEO4J_PASSWORD"],
    os.environ["OPENAI_API_KEY"], 
)

# Initialize SNS client
sns_client = boto3.client('sns')


def lambda_handler(event, context):
    for record in event['Records']:
        # Parse the SNS message
        sns_message = json.loads(record['Sns']['Message'])
        query = sns_message.get('query', '')
        channel_id = sns_message.get('channel_id', '')

        reply = engine.ask(query)
        # print(reply)

        # Post message to Slack
        response = post_message_to_slack(reply, channel_id)
        print(f"Slack Response: {response}")

    return {
        'statusCode': 200,
        'body': json.dumps('Message processed successfully')
    }


def post_message_to_slack(reply, channel_id):
    url = "https://slack.com/api/chat.postMessage"
    headers = {
        "Authorization": f"Bearer {SLACK_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "channel": channel_id,  # You can adjust this if needed
        "text": reply["response"]
    }
    
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    
    if response.status_code != 200:
        raise Exception(f"Request to Slack API failed with status code {response.status_code}. Response: {response.text}")

    return response.json()
