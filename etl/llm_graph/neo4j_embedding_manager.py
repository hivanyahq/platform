import json
import logging
from openai import OpenAI
from neo4j import GraphDatabase

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class Neo4jEmbeddingManager:
    def __init__(self, url, username, password, config_path, folder_name):
        self.url = url
        self.username = username
        self.password = password
        self.driver = GraphDatabase.driver(self.url, auth=(self.username, self.password))
        self.node_label_to_indexed_properties = self.load_config(config_path, folder_name)
        
    def load_config(self, config_path, folder_name):
        """
        Load node label configuration from a JSON file for the specified folder name.
        """
        with open(config_path, 'r') as file:
            config_data = json.load(file)
            node_label_to_properties = {}
            for item in config_data:
                if item['label'] == folder_name:
                    node_label_to_properties[item['label']] = item['props']
            return node_label_to_properties
        
    def _generate_embeddings_for_node(self, node, properties, model="text-embedding-ada-002"):
        text_data = json.dumps({k: node[k] for k in properties if k in node})
        text_data = text_data.replace("\n", " ")
        openai_client = OpenAI()
        response = openai_client.embeddings.create(input=[text_data], model=model)
        embedding = response.data[0].embedding  # Correctly access the embedding data using dot notation
        return embedding

    def update_embeddings_for_neo4j(self, node_label):
        indexed_properties = self.node_label_to_indexed_properties[node_label]
        with self.driver.session() as session:
            result = session.run(f"""MATCH (n:{node_label}) RETURN n""")
            record = result.single()
            if record is None:
                logger.error(f"No node found for label {node_label}")
                return
            node = record["n"]
            new_embedding = self._generate_embeddings_for_node(node, indexed_properties)

            # Check if an existing embedding is present and append the new embedding
            existing_embedding = node.get("embedding", [])
            if existing_embedding:
                combined_embedding = existing_embedding + new_embedding
            else:
                combined_embedding = new_embedding

            session.run(f"""
                MATCH (n:{node_label} {{id: $id}})
                SET n.embedding = $embedding
            """, id=node['id'], embedding=combined_embedding)
            logger.info(f"Updated embedding for node: {node_label}")
