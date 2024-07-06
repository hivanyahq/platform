import json
import os
import hmac
import hashlib
import base64
from time import time
from urllib.parse import urlencode, unquote_plus

import boto3

def handler(event, context):
    slack_secrets = boto3.client('secretsmanager').get_secret_value(SecretId=os.environ['SLACK_SECRETS_NAME'])
    secrets = json.loads(slack_secrets['SecretString'])
    signing_secret = secrets['signingSecret']

    slack_signature = event['headers']['X-Slack-Signature']
    slack_request_timestamp = event['headers']['X-Slack-Request-Timestamp']
    # request_body = event['body']

    # url_encoded_request_body = unquote_plus(request_body)

    encoded_request_body = event['body']
    # Decode the base64-encoded request body
    request_body = base64.b64decode(encoded_request_body).decode('utf-8')
    request_body_json = json.loads(request_body)

    
    if abs(time() - int(slack_request_timestamp)) > 60 * 5:
        raise Exception("Request is too old.")
    
    base_string = f"v0:{slack_request_timestamp}:{request_body}".encode('utf-8')
    my_signature = 'v0=' + hmac.new(signing_secret.encode('utf-8'), base_string, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(my_signature, slack_signature):
        raise Exception(f"Invalid request signature. request_body:{request_body} \n base_string: {base_string} \n  my_signature: {my_signature}")
    
    return {
        'statusCode': 200,
        'challenge': request_body_json.get('challenge', ''),
        'channelId': 'D07AM8G06RY',
        'body': json.dumps({})
    }
