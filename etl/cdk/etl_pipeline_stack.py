import os
from aws_cdk import (
    Stack,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda,
    aws_s3_notifications as s3_notifications,
)
from constructs import Construct
from botocore.exceptions import ClientError



class EtlPipelineStack(Stack):
    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Read environment variables
        bucket_name = "hivanya-integrations"
        neo4j_uri = os.getenv("NEO4J_URI", "not-set")
        neo4j_user = os.getenv("NEO4J_USER", "not-set")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "not-set")

        # Define the Docker-based Lambda function
        etl_lambda = aws_lambda.DockerImageFunction(
            self,
            "EtlLambda",
            code=aws_lambda.DockerImageCode.from_image_asset(directory="etl/pipelines"),
            architecture=aws_lambda.Architecture.ARM_64,
            environment={
                "NEO4J_URI": neo4j_uri,
                "NEO4J_USER": neo4j_user,
                "NEO4J_PASSWORD": neo4j_password,
            },
        )

        # Create S3 bucket and event-trigger
        try:
            # Reference an existing bucket, if present
            s3_bucket = s3.Bucket.from_bucket_name(
                self, "ExistingBucket", bucket_name=bucket_name
            )
        except ClientError as e:
            # Create the bucket if it does not exist
            if e.response['Error']['Code'] == 'NoSuchBucket':
                s3_bucket = s3.Bucket(
                    self,
                    "HivanyaIntegrationsBucket",
                    bucket_name=bucket_name,
                    removal_policy=RemovalPolicy.RETAIN,  # Retain the bucket on stack deletion
                )
            else:
                raise

        # Create an S3 event notification to trigger the Lambda function on PutObject events
        notification = s3_notifications.LambdaDestination(etl_lambda)
        s3_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED_PUT,
            notification,
            s3.NotificationKeyFilter(prefix="airbyte/", suffix=".csv"),
        )

        # Grant necessary permissions
        s3_bucket.grant_read(etl_lambda)


# .env file example
# BUCKET_NAME=my-bucket-name
# NEO4J_URI=your-neo4j-uri
# NEO4J_USER=your-neo4j-user
# NEO4J_PASSWORD=your-neo4j-password
# SECRETS_MANAGER_ARN=arn:aws:secretsmanager:your-region:your-account-id:secret:your-secret-id
