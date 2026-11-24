
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


## BigQuery Data Warehouse

The data warehouse follows a Medallion Architecture
with three dedicated BigQuery datasets.

| Dataset | Purpose | Default table expiration |
|---|---|---|
| media_bronze | Raw source data | 30 days |
| media_silver | Validated and standardized data | 60 days |
| media_gold | Business-ready analytical models | 90 days |

All datasets are deployed in us-central1.

Infrastructure safeguards include:

- Terraform prevent_destroy.
- Disabled automatic dataset content deletion.
- Default table expiration policies.
- Standardized resource labels.
- Explicit API dependencies.

Dataset identifiers and fully qualified references
are exposed through Terraform outputs.

Query cost management includes:

- On-demand query processing.
- Dry-run validation.
- Maximum bytes billed limits.
- Column selection and partition pruning.
- Small synthetic datasets.

Partitioned tables, clustering and analytical models
will be implemented in subsequent milestones.

The expiration periods are development-environment
settings and must be reviewed for production use.


## Pub/Sub Messaging Infrastructure

The platform uses Google Cloud Pub/Sub to support
asynchronous and event-driven data processing.

### Resources

| Resource | Purpose |
|---|---|
| Main topic | Synthetic media events |
| Main subscription | Streaming pipeline consumption |
| Dead-letter topic | Repeated delivery failures |
| Dead-letter subscription | Failure investigation |

### Messaging Configuration

- Pull-based subscriptions.
- 30-second acknowledgement deadline.
- 24-hour message retention.
- Acknowledged message retention disabled.
- Exponential retry backoff between 10 and 60 seconds.
- Dead-letter forwarding after approximately five attempts.
- Regional message storage in us-central1.
- At-least-once delivery semantics.

The Pub/Sub service agent receives resource-level IAM
permissions required for dead-letter message forwarding.

Application-generated event identifiers will support
deduplication and idempotent downstream processing.

Basic messaging functionality is validated through
Google Cloud CLI publish, pull and acknowledgement tests.

End-to-end dead-letter forwarding and streaming processing
will be validated in subsequent milestones.
