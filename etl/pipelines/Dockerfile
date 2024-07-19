FROM public.ecr.aws/lambda/python:3.8

# Set the working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the entire etl directory into the container
COPY . ${LAMBDA_TASK_ROOT}

RUN ls -l ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip3 install -r requirements.txt

# Set the CMD to your handler
CMD ["lambda/neo4j.lambda_handler"]
