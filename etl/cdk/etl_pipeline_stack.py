import os
from aws_cdk import (
    aws_lambda as lambda_,
    aws_events as events,
    aws_events_targets as targets,
    aws_s3 as s3,
    Stack,
    RemovalPolicy,
)
from constructs import Construct

class EtlPipelineStack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        # Read environment variables
        bucket_name = 'hivanya-integrations'
        neo4j_uri = os.getenv('NEO4J_URI', 'not-set')
        neo4j_user = os.getenv('NEO4J_USER', 'not-set')
        neo4j_password = os.getenv('NEO4J_PASSWORD', 'not-set')

        # Create S3 bucket if it does not exist
        try:
            # Try to reference an existing bucket
            bucket = s3.Bucket.from_bucket_name(self, "ExistingBucket", bucket_name=bucket_name)
        except: #todo: add specific exception
            # Create the bucket if it does not exist
            bucket = s3.Bucket(
                self, "HivanyaIntegrationsBucket",
                bucket_name=bucket_name,
                removal_policy=RemovalPolicy.RETAIN  # Retain the bucket on stack deletion
            )


        # Define the Docker-based Lambda function
        etl_lambda = lambda_.DockerImageFunction(
            self, 
            "EtlLambda",
            code=lambda_.DockerImageCode.from_image_asset(directory="etl/pipelines"),
            architecture=lambda_.Architecture.ARM_64,
            environment={
                "NEO4J_URI": neo4j_uri,
                "NEO4J_USER": neo4j_user,
                "NEO4J_PASSWORD": neo4j_password
            }
        )

        # Grant necessary permissions
        bucket.grant_read(etl_lambda)

        # Create the EventBridge rule to trigger the Lambda function on S3 events
        # rule = events.Rule(
        #     self, "Rule",
        #     event_pattern={
        #         "source": ["aws.s3"],
        #         "detail-type": ["Object Created"],
        #         "detail": {
        #             "bucket": {
        #                 "name": [bucket.bucket_name]
        #             }
        #         }
        #     }
        # )
        # rule.add_target(targets.LambdaFunction(etl_lambda))

# .env file example
# BUCKET_NAME=my-bucket-name
# NEO4J_URI=your-neo4j-uri
# NEO4J_USER=your-neo4j-user
# NEO4J_PASSWORD=your-neo4j-password
# SECRETS_MANAGER_ARN=arn:aws:secretsmanager:your-region:your-account-id:secret:your-secret-id
