from aws_cdk import (
    Stack,
    Duration,
    RemovalPolicy,
    aws_s3 as s3,
    aws_lambda,
    aws_s3_notifications as s3_notifications,
)
from aws_cdk.aws_secretsmanager import Secret
from constructs import Construct
from botocore.exceptions import ClientError


class HiVanyaEtlStack(Stack):
    def __init__(self, scope: Construct, id: str, secrets: Secret, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # ETL Lambda
        etl_lambda = aws_lambda.DockerImageFunction(
            self,
            "EtlLambda",
            code=aws_lambda.DockerImageCode.from_image_asset(directory="etl"),
            architecture=aws_lambda.Architecture.ARM_64,
            environment={
                "NEO4J_URI": secrets.secret_value_from_json("NEO4J_URI").to_string(),
                "NEO4J_USER": secrets.secret_value_from_json("NEO4J_USER").to_string(),
                "NEO4J_PASSWORD": secrets.secret_value_from_json(
                    "NEO4J_PASSWORD"
                ).to_string(),
                "OPENAI_API_KEY": secrets.secret_value_from_json(
                    "OPENAI_API_KEY"
                ).to_string(),
            },
            timeout=Duration.minutes(5),
        )

        # Create bucket
        bucket_name = "hivanya-integrations"  # todo: this should be updated to be genrated using CDK
        try:
            s3_bucket = s3.Bucket.from_bucket_name(
                self, "ExistingBucket", bucket_name=bucket_name
            )
        except ClientError as e:
            # Create the bucket if it does not exist
            if e.response["Error"]["Code"] == "NoSuchBucket":
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
