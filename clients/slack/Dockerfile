FROM public.ecr.aws/lambda/python:3.8

# Copy function code
COPY src/ ${LAMBDA_TASK_ROOT}

# Install the dependencies
COPY src/requirements.txt .
RUN pip install -r requirements.txt
