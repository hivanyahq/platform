import os
import json
import logging
from neo4j import GraphDatabase

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Neo4jUploader:
    def __init__(self, uri, user, password, neo4j_manager):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        self.neo4j_manager = neo4j_manager

    def merge_node(self, tx, label, properties):
        key_value_string = ", ".join([f"{key}: ${key}" for key in properties.keys() if properties[key]])
        query = f"MERGE (n:{label} {{{key_value_string}}})"
        tx.run(query, **properties)
        print(f"Uploaded node: {label} with properties: {properties}")
        # Update embeddings for the newly created/updated node
        try:
            self.neo4j_manager.update_embeddings_for_neo4j(label, properties['id'])
        except Exception as e:
            logger.error(f"Error updating embedding for node: {label} with id: {properties['id']}, error: {str(e)}")

    def merge_relationship(self, tx, label1, properties1, relationship, label2, properties2):
        key_value_string1 = ", ".join([f"{key}: ${key}1" for key in properties1.keys() if properties1[key] and key not in ['label']])
        key_value_string2 = ", ".join([f"{key}: ${key}2" for key in properties2.keys() if properties2[key] and key not in ['label']])
        query = (
            f"MERGE (a:{label1} {{{key_value_string1}}}) "
            f"MERGE (b:{label2} {{{key_value_string2}}}) "
            f"MERGE (a)-[r:{relationship}]->(b)"
        )
        params = {**{f"{key}1": value for key, value in properties1.items()}, **{f"{key}2": value for key, value in properties2.items()}}
        tx.run(query, **params)
        print(f"Uploaded relationship: {relationship} between {label1} and {label2}")

    def upload_file_to_neo4j(self, filepath):
        with self.driver.session() as session:
            with open(filepath, 'r') as file:
                for line in file:
                    obj = json.loads(line.strip())
                    if obj['type'] == 'node':
                        label = obj.get('label')
                        properties = obj.get('properties', {})
                        if label and properties:
                            session.execute_write(self.merge_node, label, properties)
                            print(f"Uploaded node: {label} with properties: {properties}")
                    elif obj['type'] == 'relationship':
                        start_node = obj.get('start_node', {})
                        end_node = obj.get('end_node', {})
                        relationship = obj.get('relationship')
                        label1 = start_node.get('label')
                        properties1 = start_node
                        label2 = end_node.get('label')
                        properties2 = end_node
                        if label1 and properties1 and label2 and properties2 and relationship:
                            session.execute_write(self.merge_relationship, label1, properties1, relationship, label2, properties2)
                            print(f"Uploaded relationship: {relationship} between {label1} and {label2}")

    def upload_files_to_neo4j(self, jsonl_files_directory):
        for root, dirs, files in os.walk(jsonl_files_directory):
            for file in files:
                filepath = os.path.join(root, file)
                self.upload_file_to_neo4j(filepath)
        self.driver.close()
