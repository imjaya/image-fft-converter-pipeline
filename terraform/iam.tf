resource "aws_iam_role" "lambda_role" {
  name               = "fft_lambda_execution_role"
  assume_role_policy = data.aws_iam_policy_document.lambda_assume_role_policy.json
  tags               = local.tags
}

data "aws_iam_policy_document" "lambda_assume_role_policy" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["lambda.amazonaws.com"]
    }
  }
}

resource "aws_iam_role_policy_attachment" "lambda_basic_execution" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_iam_role_policy" "lambda_s3_access" {
  name   = "fft_lambda_s3_access_policy"
  role   = aws_iam_role.lambda_role.id
  policy = data.aws_iam_policy_document.lambda_s3_access_policy.json
}

data "aws_iam_policy_document" "lambda_s3_access_policy" {
  statement {
    effect    = "Allow"
    actions   = ["s3:GetObject"]
    resources = ["${aws_s3_bucket.bucket.arn}/input/*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["s3:PutObject"]
    resources = ["${aws_s3_bucket.bucket.arn}/output/*"]
  }
  statement {
    effect    = "Allow"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }
  statement {
    effect = "Allow"
    actions = [
      "ecr:BatchGetImage",
      "ecr:GetDownloadUrlForLayer"
    ]
    resources = [aws_ecr_repository.repo.arn]
  }
}
