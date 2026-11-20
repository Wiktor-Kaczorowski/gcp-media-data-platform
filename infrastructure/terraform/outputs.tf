
output "project_id" {
  description = "Target Google Cloud project."
  value       = var.project_id
}

output "region" {
  description = "Primary deployment region."
  value       = var.region
}

output "environment" {
  description = "Deployment environment."
  value       = var.environment
}

output "bigquery_location" {
  description = "BigQuery dataset location."
  value       = var.bq_location
}

output "required_services" {
  description = "Google Cloud API services managed by Terraform."
  value = sort([
    for service in google_project_service.required :
    service.service
  ])
}
