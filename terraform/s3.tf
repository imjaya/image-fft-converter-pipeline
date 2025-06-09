resource "aws_s3_bucket" "bucket" {
  bucket = local.effective_bucket_name
  tags   = local.tags
}

resource "aws_s3_bucket_notification" "bucket_notify" {
  bucket = aws_s3_bucket.bucket.id

  lambda_function {
    lambda_function_arn = aws_lambda_function.fft_function.arn
    events              = ["s3:ObjectCreated:*"]
    filter_prefix       = "input/"
    filter_suffix       = ".png" # Ensure only PNG files trigger the lambda
  }

  depends_on = [aws_lambda_permission.allow_bucket]
}
