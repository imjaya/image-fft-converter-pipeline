output "bucket_name" {
  value = aws_s3_bucket.bucket.bucket
}

output "ecr_repo_url" {
  value = aws_ecr_repository.repo.repository_url
}

output "lambda_function_name" {
  value = aws_lambda_function.fft_function.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.fft_function.arn
}

output "lambda_role_name" {
  value = aws_iam_role.lambda_role.name
}

output "lambda_role_arn" {
  value = aws_iam_role.lambda_role.arn
}
