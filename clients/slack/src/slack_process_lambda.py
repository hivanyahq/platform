import json

def handler(event, context):
    print(f"Event: {event}")
    body = json.loads(event['request']['body'])

    # Add your message processing logic here
    return {
        'statusCode': 200,
        'body': {
            'message': 'Hello from Hivanya!',
            "challenge": body['challenge']
        }
    }
