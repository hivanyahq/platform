FROM public.ecr.aws/lambda/python:3.8

# Set the working directory
WORKDIR ${LAMBDA_TASK_ROOT}

# Copy the contents of the etl/etl directory into the container
COPY etl ${LAMBDA_TASK_ROOT}/etl

# Copy the setup.py and any other required files to the container
COPY setup.py ${LAMBDA_TASK_ROOT}

#RUN ls -l ${LAMBDA_TASK_ROOT}

# Install dependencies
RUN pip3 install -e ${LAMBDA_TASK_ROOT}

# Set the CMD to your handler
CMD ["etl.neo4j.lambda.lambda_handler"]
