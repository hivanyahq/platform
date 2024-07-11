import os
import logging
from langchain.graphs import Neo4jGraph
from langchain_experimental.graph_transformers import LLMGraphTransformer
from langchain_openai import ChatOpenAI
from langchain_community.document_loaders.csv_loader import CSVLoader

# Initialize the logger
logger = logging.getLogger()
logger.setLevel(logging.INFO)

class GraphProcessor:
    def __init__(self, allowed_nodes):
        self.neo4j_url = os.getenv("NEO4J_URI")
        self.neo4j_user = os.getenv("NEO4J_USERNAME")
        self.neo4j_password = os.getenv("NEO4J_PASSWORD")
        self.graph = Neo4jGraph(url=self.neo4j_url, username=self.neo4j_user, password=self.neo4j_password)

        self.llm = ChatOpenAI(temperature=0, model_name="gpt-4o")
        self.llm_transformer_props = LLMGraphTransformer(
            llm=self.llm,
            allowed_nodes=allowed_nodes,
            node_properties=True,
            relationship_properties=True,
            # prompt="Create a graph representation of the document."
        )

    def process_document(self, file_path, batch_size=1):
        loader = CSVLoader(file_path=file_path)
        docs = loader.load()
        
        for i in range(0, len(docs), batch_size):
            try:
                batch_docs = docs[i:i + batch_size]
                graph_documents_props = self.llm_transformer_props.convert_to_graph_documents(batch_docs)
                self.graph.add_graph_documents(graph_documents_props)
                logging.info(f"Batch {i // batch_size + 1} processed successfully.")
            except Exception as e:
                logging.error(f"Error processing batch {i // batch_size + 1}: {str(e)}")
