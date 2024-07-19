import json
import logging
import openai
from neo4j import GraphDatabase

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)


class Neo4jEmbeddingManager:
    def __init__(self, url, username, password):
        self.url = url
        self.username = username
        self.password = password
        self.driver = GraphDatabase.driver(
            self.url, auth=(self.username, self.password)
        )
        self.node_label_to_indexed_properties = {
            "atlassian_user": ["id", "display_name"],
            "jira_comment": ["text", "author_id", "issue_id"],
            "jira_issue": ["description", "title", "issue_type", "status"],
            "slack_user": ["id", "name"],
            "slack_message": ["text", "user"],
            "jira_project": [
                "id",
                "project_key",
                "title",
                "description",
                "assignee_id",
            ],
        }

    def _generate_embeddings_for_node(
        self, node, properties, model="text-embedding-ada-002"
    ):
        text_data = json.dumps({k: node[k] for k in properties if k in node})
        text_data = text_data.replace("\n", " ")
        response = openai.Embedding.create(input=[text_data], model=model)
        embedding = response["data"][0][
            "embedding"
        ]  # Properly access the embedding data
        return embedding

    def update_embeddings_for_neo4j(self, node_label, node_id):
        indexed_properties = self.node_label_to_indexed_properties[node_label]
        with self.driver.session() as session:
            result = session.run(
                f"""MATCH (n:{node_label} {{id: $id}}) RETURN n""", id=node_id
            )
            record = result.single()
            if record is None:
                logger.error(f"No node found for label {node_label} with id {node_id}")
                return
            node = record["n"]
            new_embedding = self._generate_embeddings_for_node(node, indexed_properties)

            # Check if an existing embedding is present and append the new embedding
            existing_embedding = node.get("embedding", [])
            if existing_embedding:
                combined_embedding = existing_embedding + new_embedding
            else:
                combined_embedding = new_embedding

            session.run(
                f"""
                MATCH (n:{node_label} {{id: $id}})
                SET n.embedding = $embedding
            """,
                id=node_id,
                embedding=combined_embedding,
            )
            logger.info(f"Updated embedding for node: {node_label} with id: {node_id}")
