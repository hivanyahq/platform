import json
import os
import hmac
import hashlib
import urllib.parse
from time import time
from base64 import b64decode

import boto3

def handler(event, context):
    slack_secrets = boto3.client('secretsmanager').get_secret_value(SecretId=os.environ['SLACK_SECRETS_NAME'])
    secrets = json.loads(slack_secrets['SecretString'])
    
    signing_secret = secrets['signingSecret']
    slack_signature = event['headers']['X-Slack-Signature']
    slack_request_timestamp = event['headers']['X-Slack-Request-Timestamp']
    request_body = event['body']
    # url_encoded_request_body = urllib.parse.parse_qs(json.loads(request_body))
    
    if abs(time() - int(slack_request_timestamp)) > 60 * 5:
        raise Exception("Request is too old.")
    
    basestring = f"v0:{slack_request_timestamp}:{request_body}".encode('utf-8')
    my_signature = 'v0=' + hmac.new(signing_secret.encode('utf-8'), basestring, hashlib.sha256).hexdigest()
    
    if not hmac.compare_digest(my_signature, slack_signature):
        raise Exception(f"Invalid request signature. request_body: {request_body}, url_encoded_request_body:{url_encoded_request_body}")
    
    payload = json.loads(request_body)
    return {
        'statusCode': 200,
        'body': json.dumps({
            'channelId': payload['event']['channel'],
            'userId': payload['event']['user'],
            'responseUrl': payload['response_url']
        })
    }
