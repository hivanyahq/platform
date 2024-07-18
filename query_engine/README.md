## Query Engine

Testing query engine

1. Create virtualenv and install
```
$ mkvirtualenv hivanya_qe -a <path-to>/platform/query_engine
$ workon hivanya_qe
$ pip install -e .
```

2. Create and update .env (using .env.example) and the test:
```
>>> from query_engine import QueryEngine
>>> engine = QueryEngine()
>>> engine.ask("Who is working on building smart bot?")
>>> {"response": "Cool devs"}
```