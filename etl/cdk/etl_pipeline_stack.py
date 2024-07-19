import os
from aws_cdk import (
    Stack,
    Duration,
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

        # todo: setup in core stack and read from there
        bucket_name = "hivanya-integrations"
        neo4j_uri = os.getenv("NEO4J_URI", "not-set")
        neo4j_user = os.getenv("NEO4J_USER", "not-set")
        neo4j_password = os.getenv("NEO4J_PASSWORD", "not-set")
        openai_api_key = os.getenv("OPENAI_API_KEY", "not-set")

        etl_lambda = aws_lambda.DockerImageFunction(
            self,
            "EtlLambda",
            code=aws_lambda.DockerImageCode.from_image_asset(directory="etl"),
            architecture=aws_lambda.Architecture.ARM_64,
            environment={
                "NEO4J_URI": neo4j_uri,
                "NEO4J_USER": neo4j_user,
                "NEO4J_PASSWORD": neo4j_password,
                "OPENAI_API_KEY": openai_api_key,
            },
            timeout=Duration.minutes(5),
        )

        try:
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
                    removal_policy=RemovalPolicy.RETAIN,
                )
            else:
                raise

        notification = s3_notifications.LambdaDestination(etl_lambda)
        s3_bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED_PUT,
            notification,
            s3.NotificationKeyFilter(prefix="airbyte/", suffix=".csv"),
        )

        s3_bucket.grant_read(etl_lambda)
