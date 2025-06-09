# Image FFT Converter Pipeline

This repository contains a simple tool and infrastructure to convert PNG images
into their 2‑D Fast Fourier Transform (FFT) representations.

## Project Structure

```
.
├── Dockerfile
├── fft_tool.py             # Python script for FFT conversion
├── lambda_function.py      # AWS Lambda handler
├── LICENSE
├── README.md
├── requirements-dev.txt    # Development dependencies
├── requirements.txt        # Application dependencies
├── terraform/
│   └── main.tf             # Terraform configuration for AWS infrastructure
└── tests/
    ├── test_fft_tool.py    # Unit tests for fft_tool.py
    └── test_lambda_function.py # Unit tests for lambda_function.py
```

## Deployment and Testing Steps

Below are the steps to deploy and test each component of the pipeline individually and then the entire pipeline.

### 1. Python FFT Tool (`fft_tool.py`)

This script performs a 2D FFT on a given grayscale PNG image and outputs the resulting image.

**Prerequisites:**

- Python 3.x
- PIP (Python package installer)

**Setup and Local Testing:**

1.  **Create a virtual environment (recommended):**

    ```bash
    python -m venv .venv
    source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
    ```

2.  **Install dependencies:**

    ```bash
    pip install -r requirements.txt
    ```

3.  **Run the script:**
    You'll need a grayscale PNG image as input (e.g., `input.png`).

    ```bash
    python fft_tool.py input.png output_fft.png
    ```

    This will create `output_fft.png` in the current directory.

4.  **Run unit tests for the FFT tool:**
    Install development dependencies first if you haven't already:
    ```bash
    pip install -r requirements-dev.txt
    ```
    Then run pytest for the specific test file:
    ```bash
    pytest tests/test_fft_tool.py
    ```

### 2. Docker Container

The `Dockerfile` containerizes the Python tool.

**Prerequisites:**

- Docker installed and running.

**Build and Test Locally:**

1.  **Build the Docker image:**
    From the root directory of the project:

    ```bash
    docker build -t fft-tool:latest .
    ```

2.  **Test the container locally:**
    Ensure you have an `input.png` in your current directory. The following command mounts the current directory (`$PWD` or `%CD%` on Windows) to `/data` inside the container.

    ```bash
    # For Linux/macOS
    docker run --rm -v "$PWD":/data fft-tool:latest python fft_tool.py /data/input.png /data/output_docker_fft.png

    # For Windows (Command Prompt)
    # docker run --rm -v "%CD%":/data fft-tool:latest python fft_tool.py /data/input.png /data/output_docker_fft.png

    # For Windows (PowerShell)
    # docker run --rm -v "${PWD}:/data" fft-tool:latest python fft_tool.py /data/input.png /data/output_docker_fft.png
    ```

    This will create `output_docker_fft.png` in your local current directory.

### 3. AWS Infrastructure (Terraform)

The Terraform configuration in the `terraform/` directory defines the AWS infrastructure (S3, ECR, Lambda, IAM roles/policies).

**Deployment Order and Image Dependency:**

**IMPORTANT:** The Terraform configuration creates an AWS Lambda function that expects a Docker image to be present in the AWS ECR repository. Therefore, the deployment process must be done in a specific order:

1.  **Part 1: Create ECR Repository (and other non-Lambda resources)**:

    - Run `terraform apply` to create the ECR repository and other resources like the S3 bucket and IAM roles. This initial apply might **fail** when trying to create the Lambda function because the Docker image doesn't exist in ECR yet. This is expected for the first run if the image isn't pre-built.
    - Alternatively, you can use `terraform apply -target=aws_ecr_repository.repo` (and target other prerequisite resources like IAM roles and S3 bucket if they don't exist) to only create the ECR repository first.

2.  **Part 2: Build and Push Docker Image to ECR**:

    - Once the ECR repository is created (its URL will be in the Terraform output), build your Docker image and push it to this ECR repository. (Detailed steps in section 4).

3.  **Part 3: Create Lambda Function (and remaining resources)**:
    - After the image is successfully pushed to ECR, run `terraform apply` again. This time, Terraform will be able to find the image and successfully create the Lambda function and any dependent resources (like S3 bucket notifications).

**Prerequisites:**

- Terraform CLI installed.
- AWS CLI installed and configured with credentials that have permissions to create the required resources (S3, ECR, Lambda, IAM roles/policies).

**Deployment:**

1.  **Navigate to the terraform directory:**

    ```bash
    cd terraform
    ```

2.  **Initialize Terraform:**

    ```bash
    terraform init
    ```

3.  **Apply the Terraform configuration:**
    You can specify a bucket name or let Terraform generate a default one.

    ```bash
    # Option 1: Use a specific bucket name (replace <your-unique-bucket-name>)
    terraform apply -var="bucket_name=<your-unique-bucket-name>"

    # Option 2: Use the default generated bucket name (ensure your AWS region is set, e.g., via AWS_DEFAULT_REGION or provider block)
    terraform apply
    ```

    Review the plan and type `yes` when prompted.
    Note the outputs, especially `ecr_repo_url` and `bucket_name`.

    **If the apply fails at the Lambda function creation step due to "Source image ... does not exist", this is expected if you haven't pushed the image to ECR yet. Proceed to Step 4 to build and push the image, then re-run `terraform apply`.**

### 4. Push Docker Image to AWS ECR

After the ECR repository is created by Terraform, you need to build and push your Docker image to it.

**Prerequisites:**

- AWS CLI installed and configured.
- Docker installed and running.
- The `ecr_repo_url` from the Terraform output.
- The AWS region where the ECR repository was created (e.g., `us-west-2`).

**Steps:**

1.  **Get ECR login password and login Docker to ECR:**
    Replace `<region>` with your AWS region and `<ecr_repo_url>` with the ECR repository URL from Terraform output (it will look like `ACCOUNT_ID.dkr.ecr.REGION.amazonaws.com/fft-tool-repo`).
    The ECR URL for login does not include the repository name itself, just the registry part.
    Example: if `ecr_repo_url` is `123456789012.dkr.ecr.us-west-2.amazonaws.com/fft-tool-repo`, the login URL is `123456789012.dkr.ecr.us-west-2.amazonaws.com`.

    ```bash
    # Extract the registry URL from the full ECR repo URL
    # ECR_REPO_URL=$(terraform output -raw ecr_repo_url)
    # AWS_REGION=$(terraform output -raw region) # Assuming you have a region output or know it
    # ECR_REGISTRY=$(echo $ECR_REPO_URL | cut -d'/' -f1)

    aws ecr get-login-password --region <region> | docker login --username AWS --password-stdin <account_id>.dkr.ecr.<region>.amazonaws.com
    ```

    _(You can get `<account_id>` from `aws sts get-caller-identity --query Account --output text` or from the `ecr_repo_url` output)_

2.  **Tag your local Docker image:**
    Use the `ecr_repo_url` from the Terraform output.

    ```bash
    docker tag fft-tool:latest <ecr_repo_url>:latest
    ```

3.  **Push the image to ECR:**

    ```bash
    docker push <ecr_repo_url>:latest
    ```

    **After the image is pushed, re-run `terraform apply` in the `terraform` directory to complete the infrastructure setup, specifically to create the Lambda function.**

### 5. AWS Lambda Function (`lambda_function.py`)

The Lambda function is automatically deployed by Terraform, using the image from ECR.

**Testing the Lambda Function (Unit Tests):**

1.  **Install development dependencies (if not already done):**
    From the project root:

    ```bash
    pip install -r requirements-dev.txt
    ```

2.  **Run pytest for the Lambda test file:**
    ```bash
    pytest tests/test_lambda_function.py
    ```

### 6. End-to-End Pipeline Testing

Now, test the entire pipeline by uploading an image to the S3 bucket.

**Prerequisites:**

- AWS CLI configured.
- An input PNG image (e.g., `input.png`).
- The `bucket_name` from the Terraform output.

**Steps:**

1.  **Upload a PNG image to the `input/` prefix in the S3 bucket:**
    Replace `<your-bucket-name>` with the actual S3 bucket name and `input.png` with your test image file.

    ```bash
    aws s3 cp input.png s3://<your-bucket-name>/input/input.png
    ```

2.  **Check for a processed image in the `output/` prefix:**
    The Lambda function should be triggered, process the image, and place the result in `output/`.
    Wait a few moments for the processing to complete.

    ```bash
    aws s3 ls s3://<your-bucket-name>/output/
    ```

    You should see a file like `fft-input.png` listed.

3.  **Download and verify the output (optional):**

    ```bash
    aws s3 cp s3://<your-bucket-name>/output/fft-input.png ./downloaded_fft_output.png
    ```

    Open `downloaded_fft_output.png` to verify it's the FFT image.

4.  **Check Lambda Logs (Troubleshooting):**
    If the output doesn't appear, check the CloudWatch Logs for the `fft_image_processor` Lambda function in the AWS Management Console for any errors.

## Development

For local development and testing:

1.  **Set up a virtual environment and install all dependencies:**

    ```bash
    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt -r requirements-dev.txt
    ```

2.  **Install pre-commit hooks (optional but recommended):**
    This helps ensure code quality and consistency before committing.

    ```bash
    pre-commit install
    ```

    To run hooks on all files:

    ```bash
    pre-commit run --all-files
    ```

3.  **Run all unit tests:**
    ```bash
    pytest
    ```

## Cleanup

To remove the AWS resources created by Terraform:

1.  **Navigate to the terraform directory:**

    ```bash
    cd terraform
    ```

2.  **Destroy the infrastructure:**

    ```bash
    terraform destroy
    ```

    Type `yes` when prompted.

    **Note:** This will attempt to delete the S3 bucket. If the bucket is not empty, Terraform might fail to delete it. You may need to manually empty the S3 bucket (objects and versions) via the AWS CLI or console before `terraform destroy` can successfully remove it, or configure the bucket resource in Terraform to force delete its contents (e.g., `force_destroy = true` on the `aws_s3_bucket` resource - use with caution).

    To empty the bucket first (replace `<your-bucket-name>`):

    ```bash
    aws s3 rm s3://<your-bucket-name> --recursive
    ```

To remove the Docker image from ECR, you can do so via the AWS Management Console or AWS CLI (`aws ecr batch-delete-image`).

To remove local Docker images:

```bash
docker rmi fft-tool:latest <ecr_repo_url>:latest
```
