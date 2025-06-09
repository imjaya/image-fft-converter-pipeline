resource "aws_lambda_function" "fft_function" {
  function_name = "fft_image_processor"
  image_uri     = "${aws_ecr_repository.repo.repository_url}:latest"
  role          = aws_iam_role.lambda_role.arn
  package_type  = "Image"
  timeout       = 300 # Increased timeout for potentially long image processing
  memory_size   = 512 # Increased memory for image processing
  tags          = local.tags

  environment {
    variables = {
      S3_OUTPUT_PREFIX = "output/"
      LOG_LEVEL        = "INFO"
    }
  }
}

resource "aws_lambda_permission" "allow_bucket" {
  statement_id  = "AllowExecutionFromS3"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.fft_function.function_name
  principal     = "s3.amazonaws.com"
  source_arn    = aws_s3_bucket.bucket.arn
  # To be more specific, you can add source_account if known
  # source_account = data.aws_caller_identity.current.account_id
}
