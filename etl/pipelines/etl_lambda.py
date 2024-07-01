import json
# from etl.pipeline.load_neo4j import Neo4jLoader
# from etl.pipeline.transform_airtbyte import AirbyteTransformer


def lambda_handler(event, context):
    # Extract bucket name and object key from the event
    # bucket_name = event['Records'][0]['s3']['bucket']['name']
    # object_key = event['Records'][0]['s3']['object']['key']
    
    # Initialize the components
    # transformer = AirbyteTransformer()
    # loader = Neo4jLoader()
    
    # Mock: Read data from S3 (to be replaced with actual S3 read logic)
    # raw_data = "raw data from s3"

    # Transform the data
    # transformed_data = transformer.transform(raw_data)

    # Upload the data to Neo4j
    # loader.upload(transformed_data)
    print(event)
    print(context)

    return "Hello Lambda!"

    # return {
    #     'statusCode': 200,
    #     'body': json.dumps('Data processed successfully')
    # }
