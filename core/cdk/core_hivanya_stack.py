from aws_cdk import App, Stack
from constructs import Construct  # constructs is the correct package for Construct


class CoreHivanyaStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

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
