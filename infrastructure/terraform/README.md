
# Terraform Infrastructure

This directory contains the Infrastructure as Code
configuration for the GCP Media Data Platform.

## Authentication

The Google provider uses Application Default Credentials.
Long-lived service account keys are not required.

## Configuration

Copy the example variables file:

    cp terraform.tfvars.example terraform.tfvars

Update the project ID before running Terraform.

## Development Commands

    terraform init
    terraform fmt -recursive
    terraform validate
    terraform plan

## State Management

The initial development environment uses local Terraform
state. State files must never be committed to Git.

Remote state management will be introduced in a later
infrastructure milestone.

## Deployment Policy

Review all infrastructure changes and potential costs
before executing terraform apply.

Cloud Composer, Dataflow jobs and always-on compute
resources are not provisioned by the initial configuration.

## Region

The initial deployment region is us-central1, selected
to support regional compatibility and cost-conscious
development.


## Cloud Storage Infrastructure

Three regional Cloud Storage buckets are provisioned
using Terraform.

| Bucket layer | Purpose | Lifecycle |
|---|---|---|
| Raw | Original source data | 30 days |
| Staging | Intermediate processing files | 7 days |
| Temp | Temporary Dataflow files | 3 days |

All buckets use:

- Regional STANDARD storage in us-central1.
- Uniform bucket-level access.
- Enforced public access prevention.
- Disabled object versioning.
- Disabled force destroy.
- Standardized resource labels.

The Raw bucket uses a seven-day soft delete policy
to protect source data against accidental deletion.

Soft delete is disabled for reproducible staging
and temporary data to minimize storage costs.

The bucket names and URIs are exposed through
Terraform outputs.

Infrastructure deployment and basic data access
are validated using Terraform and Google Cloud CLI.
