import os
import json
from aws_cdk import Stack
from constructs import Construct
from aws_cdk.aws_secretsmanager import Secret, SecretStringGenerator


class HiVanyaCoreStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Create app secrets placeholder
        self.secrets = Secret(
            self,
            "HiVanyaCoreSecrets",
            secret_name="HiVanyaCoreSecrets",
            generate_secret_string=SecretStringGenerator(
                secret_string_template=json.dumps({
                    "botToken": "not-set",
                    "signingSecret": "not-set",
                    "NEO4J_URI": "not-set",
                    "NEO4J_USER": "not-set",
                    "NEO4J_PASSWORD": "not-set",
                    "OPENAI_API_KEY": "not-set",
                    "AIRBYTE_DELIVERY_BUCKET": "not-set"
                }),
                generate_string_key="randomPassword",
                exclude_characters="/\\\"'@"
            )
        )

    # Todo: Setup Core Stacks
    # For each define a stack files like platform/core/cdk/core/core_hivanya_s3_sack.py
    # CoreHivanyaS3Stack: S3Buckets
    # CoreHivanyaSecurityStack: vpcs/subnets
    # CoreHivanyaSecurityStack: security groups
    # CoreHivanyaSecretsStack: Secrets Manager,
    # CoreHivanyaIAMStack: IAM Role Stack
    # CoreHivanyaRdsStack, etc RDS/ESC CLuster/etc
    # CoreHivanyaCIStack
    # CoreHivanyaCDStack
    # CoreHivanyaLogMonitoringStack
