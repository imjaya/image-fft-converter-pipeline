# Use an AWS official base image for Python Lambda functions
FROM public.ecr.aws/lambda/python:3.11

# The AWS base image sets WORKDIR to /var/task, which is LAMBDA_TASK_ROOT.
# Files will be copied into /var/task.

# Copy requirements.txt and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the Lambda function code into LAMBDA_TASK_ROOT
COPY fft_tool.py .
COPY lambda_function.py .

# Set the CMD to your handler function (module.function)
# The AWS base image's entrypoint will use this.
CMD ["lambda_function.lambda_handler"]
