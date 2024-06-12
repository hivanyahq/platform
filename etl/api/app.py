from flask import Flask, request, jsonify
import subprocess
import json
import boto3

app = Flask(__name__)

@app.route('/create_customer', methods=['POST'])
def create_customer():
    customer_id = request.json.get('customer_id')
    config = request.json.get('config')

    # Fetch secrets from AWS Secrets Manager
    secrets_manager_client = boto3.client('secretsmanager')
    secret_value = secrets_manager_client.get_secret_value(SecretId=config['neo4j_secret_name'])
    secrets = json.loads(secret_value['SecretString'])

    # Save config and secrets to a temporary file
    config_file = f"/tmp/{customer_id}_config.json"
    secrets_file = f"/tmp/{customer_id}_secrets.json"
    with open(config_file, 'w') as f:
        json.dump(config, f)
    with open(secrets_file, 'w') as f:
        json.dump(secrets, f)

    # Run the CDK deployment script for the specific customer
    result = subprocess.run(['python', 'etl/cdk/create_customer_stack.py', customer_id, config_file, secrets_file], capture_output=True, text=True)

    if result.returncode == 0:
        return jsonify({'status': 'success'}), 200
    else:
        return jsonify({'status': 'failure', 'error': result.stderr}), 500

if __name__ == '__main__':
    app.run(debug=True)



# curl -X POST http://127.0.0.1:5000/create_customer -H "Content-Type: application/json" -d '{
#     "customer_id": "customer1",
#     "config": {
#         "bucket_name": "customer1-bucket",
#         "neo4j_secret_name": "customer1-neo4j-secret"
#     }
# }'
