variable "region" {
  description = "AWS region"
  default     = "us-west-2"
}

variable "bucket_name" {
  description = "Name of S3 bucket for processing. If not provided, a default name will be generated using the pattern: 'image-fft-pipeline-AWS_ACCOUNT_ID-AWS_REGION'."
  type        = string
  default     = null
}
