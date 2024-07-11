import json
import logging
import os
import boto3
from neo4j_embedding_manager import Neo4jEmbeddingManager
from graph_processor import GraphProcessor 

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize the S3 client
s3 = boto3.client('s3')

def extract_folder_from_s3_uri(s3_uri):
    # Example: "s3://hivanya-integrations/airbyte_llm/jira/2024_05_01_1714536886878_0.csv"
    parts = s3_uri.split('/')
    if len(parts) > 4:
        return parts[4]  # "jira" in this case
    return None

def lambda_handler(event, context):
    try:
        logger.info(f"Received event: {json.dumps(event)}")

        bucket_name = event['Records'][0]['s3']['bucket']['name']
        object_key = event['Records'][0]['s3']['object']['key']
        s3_uri = f"s3://{bucket_name}/{object_key}"
        logger.info(f"S3 URI: {s3_uri}")

        bucket_folder = extract_folder_from_s3_uri(s3_uri).capitalize()
        logger.info(f"Extracted bucket folder: {bucket_folder}")

        download_path = f'/tmp/{object_key.replace("/", "_")}'
        s3.download_file(bucket_name, object_key, download_path)

        # Initialize GraphProcessor with extracted bucket folder as allowed_nodes
        graph_processor = GraphProcessor(allowed_nodes=[bucket_folder])
        graph_processor.process_document(download_path, batch_size=1)
        
        nodes_data = "./nodes_data.json"
        
        # Initialize Neo4jEmbeddingManager
        logger.info(f"loading neo4j manager with nodes_data: {nodes_data}")
        neo4j_manager = Neo4jEmbeddingManager(
            url=os.getenv("NEO4J_URI"),
            username=os.getenv("NEO4J_USERNAME"),
            password=os.getenv("NEO4J_PASSWORD"),
            config_path=nodes_data,
            folder_name=bucket_folder
        )
        
        # Update embeddings for neo4j
        logger.info(f"updating embedings for node : {bucket_folder}")
        neo4j_manager.update_embeddings_for_neo4j(bucket_folder)

        return {'statusCode': 200, 'body': json.dumps('File processed and graph updated successfully')}

    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        return {'statusCode': 500, 'body': json.dumps(f"Error processing file: {str(e)}")}
