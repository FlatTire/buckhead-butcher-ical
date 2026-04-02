terraform {
  backend "s3" {
    bucket         = "pe-tfstate-400331679889-us-east-1"
    key            = "buckhead-butcher-ical/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
