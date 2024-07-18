from setuptools import setup, find_packages

setup(
    name="query_engine",
    version="1.0",
    packages=find_packages(),
    install_requires=[
        'requests',
        'neo4j',
        'langchain',
        'openai',
        'python-dotenv'
        'langchain-community',
        'embeddings'
    ],
    entry_points={
        'console_scripts': [
            'query_engine=query_engine.main:main',
        ],
    },
)
