import os
import json
import boto3
import logging

from etl.embedding import Neo4jEmbeddingManager
from etl.transforms import (
    Airbyte2jsonlTransformer,
    ConfluenceGraphGenerator,
    SlackGraphGenerator,
    JiraGraphGenerator,
)
from etl.neo4j.upload import Neo4jUploader

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the S3 client
s3 = boto3.client("s3")

# Initialize the Transformer class
airbyte2jsonl_transformer = Airbyte2jsonlTransformer()

# Initialize Neo4jEmbeddingManager
neo4j_manager = Neo4jEmbeddingManager(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
)

# Initialize Neo4jUploader
uploader = Neo4jUploader(
    uri=os.getenv("NEO4J_URI"),
    user=os.getenv("NEO4J_USER"),
    password=os.getenv("NEO4J_PASSWORD"),
    neo4j_manager=neo4j_manager,
)

GRAPH_GENERATOR_MAP = {
    "jira": JiraGraphGenerator,
    "slack": SlackGraphGenerator,
    "confluence": ConfluenceGraphGenerator,
}

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        bucket_name = event["Records"][0]["s3"]["bucket"]["name"]
        object_key = event["Records"][0]["s3"]["object"]["key"]

        logger.info(f"Bucket: {bucket_name}, Object: {object_key}")

        download_path = f'/tmp/{object_key.replace("/", "_")}'
        s3.download_file(bucket_name, object_key, download_path)

        # mapkey = '/'.join(object_key.split('/')[1:-1])
        mapkey = "/".join(object_key.split("/")[1:3])
        logger.info(f"Mapkey: {mapkey}")

        if not airbyte2jsonl_transformer.can_transform(mapkey):
            logger.info(f"Skipping {object_key} as it does not match FIELD_MAP keys.")
            return {"statusCode": 200, "body": json.dumps(f"Skipped file {object_key}")}

        jsonl_output_path = (
            f'/tmp/transformed/{"/".join(object_key.split("/")[2:-1])}.jsonl'
        )
        os.makedirs(os.path.dirname(jsonl_output_path), exist_ok=True)

        airbyte2jsonl_transformer.transform_airbyte2jsonl_format(
            download_path, jsonl_output_path, mapkey
        )

        logger.info(f"File transformed and saved to: {jsonl_output_path}")

        graph_output_directory = "/tmp/graph_output"
        os.makedirs(graph_output_directory, exist_ok=True)

        def get_generator(object_key):
            for key in GRAPH_GENERATOR_MAP.keys():
                if key in object_key:
                    logger.info(
                        f"Selected {key} graph generator for object_key: {object_key}"
                    )
                    return GRAPH_GENERATOR_MAP[key]()
            logger.info(f"No graph generator matched for object_key: {object_key}")
            return None

        graph_generator = get_generator(object_key)
        if graph_generator:
            logger.info(f"Starting graph generation for {object_key}")
            graph_generator.generate_graph_schema_format_data_files(
                os.path.dirname(jsonl_output_path), graph_output_directory
            )
            logger.info(f"Graph generation completed for {object_key}")
        else:
            logger.info(f"No graph generator found for {object_key}")

        uploader.upload_files_to_neo4j(graph_output_directory)

        return {
            "statusCode": 200,
            "body": json.dumps(
                "File transformed, graph generated, and uploaded successfully"
            ),
        }

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps(f"Error processing file: {str(e)}"),
        }
