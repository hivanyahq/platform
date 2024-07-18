import json
from neo4j import GraphDatabase
from langchain.embeddings.openai import OpenAIEmbeddings
from openai import OpenAI
from langchain.vectorstores import Neo4jVector
from config import NEO4J_URL, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY


class Neo4jEmbeddingManager:
    def __init__(self):
        self.driver = GraphDatabase.driver(NEO4J_URL, auth=(NEO4J_USER, NEO4J_PASSWORD))
        self.embeddings_model = OpenAIEmbeddings()
        self.node_label_to_indexed_properties = {
            "atlassian_user": ["id", "display_name", "email"],
            "jira_comment": ["text", "author_id", "issue_id"],
            "jira_issue": [
                "description",
                "title",
                "issue_type",
                "status",
                "created",
                "parent_key",
                "project_id",
                "key",
                "creator_id",
                "assignee_id",
                "display_name",
            ],
            "jira_sprint": ["name", "state", "start_date", "end_date", "board_id"],
            "jira_project": ["project_key", "id", "title"],
            "confluence_space": ["name", "key"],
            "confluence_page": [
                "title",
                "content",
                "author_name",
                "author_id",
                "created",
            ],
            "slack_user": ["id", "name", "last_name"],
            "slack_channel": [
                "id",
                "name",
                "purpose_value",
                "creator",
                "created",
                "num_members",
            ],
            "slack_message": ["text", "user", "created", "team", "channel_id"],
        }

    def _generate_embeddings_for_node(
        self, node, properties, model="text-embedding-ada-002"
    ):
        text_data = json.dumps({k: node[k] for k in properties if k in node})
        openai_client = OpenAI(api_key=OPENAI_API_KEY)
        return (
            openai_client.embeddings.create(input=[text_data], model=model)
            .data[0]
            .embedding
        )

    def update_embeddings_for_neo4j(self, node_label):
        indexed_properties = self.node_label_to_indexed_properties[node_label]
        with self.driver.session() as session:
            result = session.run(f"MATCH (n:{node_label}) RETURN n")
            nodes_to_update = result.data()
            for record in nodes_to_update:
                node = record["n"]
                if "id" not in node:
                    continue
                embedding = self._generate_embeddings_for_node(node, indexed_properties)
                session.run(
                    f"""
                MATCH (n:{node_label} {{id: $id}})
                SET n.embedding = $embedding
                """,
                    id=node["id"],
                    embedding=embedding,
                )

    def get_retriever(self, node_label):
        indexed_properties = self.node_label_to_indexed_properties[node_label]
        vector_index = Neo4jVector.from_existing_graph(
            embedding=self.embeddings_model,
            url=NEO4J_URL,
            username=NEO4J_USER,
            password=NEO4J_PASSWORD,
            node_label=node_label,
            index_name=f"{node_label}s",
            text_node_properties=indexed_properties,
            embedding_node_property="embedding",
        )
        return vector_index
