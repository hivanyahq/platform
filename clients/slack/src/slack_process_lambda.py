import json

def handler(event, context):
    # Add your message processing logic here
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Hello from Hivanya!'
        })
    }
