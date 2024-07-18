#!/usr/bin/env python3
import os

from aws_cdk import App, Environment
from core.cdk.core_hivanya_stack import CoreHivanyaStack
from etl.cdk.etl_pipeline_stack import EtlPipelineStack
from clients.slack.cdk.slack_bot_stack import SlackBotStack

# Load from environment variables or provide default values
AWS_ACCOUNT_ID = os.getenv("AWS_ACCOUNT_ID", "533267214222")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_VPC_ID = os.getenv("AWS_VPC_ID", "default-vpc-id")
AWS_ENV = os.getenv("AWS_ENV", "default-env")

env = Environment(account=AWS_ACCOUNT_ID, region=AWS_REGION)

app = App()

# Pass env directly to the stack
core_hivanya_stack = CoreHivanyaStack(app, "CoreHivanyaStack", env=env)

# Assuming EtlPipelineStack requires additional parameters from CoreHivanyaStack
# etl_pipeline_stack = EtlPipelineStack(app, "EtlPipelineStack", env=env, core_hivanya_stack=core_hivanya_stack)
etl_pipeline_stack = EtlPipelineStack(app, "EtlPipelineStack", env=env)
slack_bot_stack = SlackBotStack(app, "SlackBotStack", env=env)

app.synth()
