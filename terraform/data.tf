data "aws_caller_identity" "current" {}

locals {
  effective_bucket_name = var.bucket_name != null ? var.bucket_name : "image-fft-pipeline-${data.aws_caller_identity.current.account_id}-${var.region}"
  tags = {
    Project     = "ImageFFTConverterPipeline"
    Environment = "Dev"
    ManagedBy   = "Terraform"
  }
}
