## Query Engine


1. Installation
```
$ mkvirtualenv hivanya_qe -a <path-to>/platform/query_engine
$ workon hivanya_qe
$ pip install -e .
```

2. Usage
```
>>> from query_engine import QueryEngine
>>> engine = QueryEngine(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD, OPENAI_API_KEY)
>>> engine.ask("Who is working on implementing ETL pipeline to create a unified index?")
{'response': 'Pawan Kumar is likely working on tasks related to the ETL pipeline to create a unified index'}
```

3. Testing from file 
```
$ cd platform/query_engine
$ cp .env.example .env  # then update values in .env
$ python tests/test_main.py
```