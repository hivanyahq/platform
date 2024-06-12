import boto3
import json
import subprocess
from aws_cdk import core
from etl_pipeline_stack import EtlPipelineStack

class EtlApiStack(core.App):
    def __init__(self, customer_id, config, secrets):
        super().__init__()
        EtlPipelineStack(self, f"CustomerStack-{customer_id}", config, secrets)

# def main():
#     # Fetch customer_id and config from an external source
#     # For example, you can pass these as arguments or read from a file/database

#     customer_id = 'customer_id_here'
#     config = {
#         "bucket_name": "bucket_name_here",
#         "neo4j_secret_name": "your-neo4j-secret-id"
#     }

#     # Fetch secrets from AWS Secrets Manager
#     secrets_manager_client = boto3.client('secretsmanager')
#     secret_value = secrets_manager_client.get_secret_value(SecretId=config['neo4j_secret_name'])
#     secrets = json.loads(secret_value['SecretString'])

#     app = EtlApiStack(customer_id, config, secrets)
#     app.synth()

#     # Deploy the synthesized stack using AWS CDK CLI
#     deploy_command = [
#         "cdk", "deploy", f"CustomerStack-{customer_id}",
#         "--require-approval", "never"
#     ]
#     subprocess.run(deploy_command)

# if __name__ == "__main__":
#     main()
