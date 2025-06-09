resource "aws_ecr_repository" "repo" {
  name                 = "fft-tool-repo"
  image_tag_mutability = "MUTABLE"
  tags                 = local.tags

  image_scanning_configuration {
    scan_on_push = true
  }
}
