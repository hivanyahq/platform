import json
from neo4j import GraphDatabase
from langchain.embeddings.openai import OpenAIEmbeddings
from openai import OpenAI
from langchain.vectorstores import Neo4jVector


class Neo4jEmbeddingManager:
    def __init__(self, neo4j_url, neo4j_user, neo4j_password, openai_key):
        self.neo4j_url = neo4j_url
        self.neo4j_user = neo4j_user
        self.neo4j_password = neo4j_password
        self.openai_key = openai_key

        self.driver = GraphDatabase.driver(neo4j_url, auth=(neo4j_user, neo4j_password))
        self.driver.verify_connectivity()

        self.embeddings_model = OpenAIEmbeddings(openai_api_key=openai_key)
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
        openai_client = OpenAI(api_key=self.openai_key)
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
            url=self.neo4j_url,
            username=self.neo4j_user,
            password=self.neo4j_password,
            node_label=node_label,
            index_name=f"{node_label}s",
            text_node_properties=indexed_properties,
            embedding_node_property="embedding",
        )
        return vector_index
