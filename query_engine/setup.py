from setuptools import setup, find_packages

setup(
    name="query_engine",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "requests",
        "neo4j",
        "langchain",
        "openai",
        "python-dotenv",
        "langchain-community",
        "tiktoken",
        "embeddings",
    ],
)
