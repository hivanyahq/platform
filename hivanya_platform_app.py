#!/usr/bin/env python3
import os

from aws_cdk import App, Environment
from core.cdk.hivanya_core_stack import HiVanyaCoreStack
from etl.cdk.hivanya_etl_stack import HiVanyaEtlStack
from clients.slack.cdk.hivanya_slack_bot_stack import HiVanyaSlackBotStack

# Load from environment variables or provide default values
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "533267214222")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_VPC_ID = os.getenv("AWS_VPC_ID", "default-vpc-id")
AWS_ENV = os.getenv("AWS_ENV", "default-env")

env = Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION)

app = App()

# Core stack
core_stack = HiVanyaCoreStack(app, "HiVanyaCoreStack", env=env)

# ETL stack
etl_stack = HiVanyaEtlStack(
    app, "HiVanyaEtlStack", secrets=core_stack.secrets
)

# Slack bot stack
slack_bot_stack = HiVanyaSlackBotStack(
    app,
    "HiVanyaSlackBotStack",
    secrets=core_stack.secrets
)

app.synth()
