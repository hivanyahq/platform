from setuptools import setup, find_packages

setup(
    name="etl",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        "openai==0.28",
        "neo4j",
        "boto3",
        "langchain",
        "langchain-community",
    ],
)