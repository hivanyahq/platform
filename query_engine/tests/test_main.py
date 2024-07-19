import os
from dotenv import load_dotenv

from query_engine import QueryEngine

load_dotenv('.env')

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USER = os.getenv("NEO4J_USER")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


engine = QueryEngine(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY)
questions = [
    "Who is working on building knowledge graph in neo4j?",
    "Who is working on implementing ETL pipeline to create a unified index?",
]
for  question in questions:
    response = engine.ask(question)
    print(f"response: {response}")
