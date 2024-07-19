# platform
Repo for ETL pipelines, knowledge-base and query-bots.

### Infra Deployment
```
$ cd <path-to>/platform
$ pip install -r requirements.txt
$ cdk deploy -e HiVanyaCoreStack --profile hivanya  # update secrets on AWS console
$ cdk deploy -e HiVanyaEtlStack --profile hivanya
$ cdk deploy -e HiVanyaSlackStack --profile hivanya
```

### Code Formatting
```
$ pip install ruff
$ ruff check
$ ruff format
```
More: https://github.com/astral-sh/ruff


