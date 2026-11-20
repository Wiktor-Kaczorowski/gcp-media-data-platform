
# Architecture

## 1. Purpose

The GCP Media Data Platform is designed to demonstrate
modern cloud data engineering practices in the context
of digital media and advertising analytics.

The platform aims to provide reliable data ingestion,
processing, transformation and analytical consumption
while supporting standardized self-service development.

## 2. Architectural Requirements

### Functional Requirements

- Ingest synthetic advertising data from REST APIs.
- Support batch and streaming data processing.
- Store raw data for reprocessing and auditing.
- Transform data into analytical models.
- Calculate standardized marketing KPIs.
- Orchestrate multi-stage data pipelines.
- Support configuration-driven pipeline development.

### Non-Functional Requirements

- Security and least-privilege access.
- Scalability and maintainability.
- Data quality and reliability.
- Reproducible infrastructure.
- Automated testing and deployment.
- Observability and cost efficiency.

## 3. Architectural Decisions

### ADR-001: Google Cloud Platform

Status: Accepted

Google Cloud provides managed services for storage,
distributed processing, messaging and analytical workloads.

Selected services include Cloud Storage, BigQuery,
Pub/Sub and Dataflow.

### ADR-002: Apache Beam for Data Processing

Status: Accepted, implementation planned

Apache Beam provides a unified programming model for
batch and streaming pipelines.

The DirectRunner will be used for local development,
while the DataflowRunner will be used for cloud processing.

This approach supports local testing before executing
distributed cloud workloads.

### ADR-003: ELT and Layered Data Architecture

Status: Accepted, implementation planned

The platform will separate raw, cleaned and business-ready
data into logical processing layers.

- Bronze: Raw and minimally processed data.
- Silver: Validated, standardized and deduplicated data.
- Gold: Business-oriented analytical data marts.

BigQuery and dbt will support SQL-based transformations
and analytical modeling.

### ADR-004: Infrastructure as Code

Status: Accepted, implementation planned

Terraform will manage cloud infrastructure through
declarative, version-controlled configuration.

Infrastructure changes should be reviewed through
Terraform plans before deployment.

### ADR-005: Local Airflow Orchestration

Status: Accepted, implementation planned

Apache Airflow will initially run locally using Docker.

The orchestration environment will communicate with
actual GCP services rather than cloud service emulators.

Cloud Composer remains an optional deployment target
and is disabled by default due to its operating costs.

### ADR-006: Keyless Authentication

Status: Partially implemented

Local development uses Application Default Credentials.

Cloud workloads will use dedicated service accounts
with least-privilege permissions.

GitHub Actions will use Workload Identity Federation
instead of long-lived service account keys.

### ADR-007: Configuration-Driven Development

Status: Initial implementation completed

Application configuration is managed separately
from processing logic.

The Settings class validates project configuration,
environment values and cost-related permissions.

Missing paid-workload permissions are interpreted
as disabled. Invalid boolean settings are rejected.

### ADR-008: Automated Quality Checks

Status: Initial implementation completed

The project uses pytest for automated testing
and Ruff for linting and formatting.

A Makefile provides standardized development commands.

The same checks will be integrated into the planned
CI/CD workflow.

## 4. Deployment Environments

The initial deployment environment is DEV.

The target architecture supports separate DEV, TEST
and PROD configurations.

Additional cloud environments are not provisioned
during the initial development phase.

## 5. Initial Regional Configuration

| Parameter | Value |
|---|---|
| GCP region | us-central1 |
| BigQuery location | us-central1 |
| Initial environment | dev |

The current design assumes that regional data processing
components are deployed in compatible locations.

## 6. Data Security and Privacy

The project uses synthetic advertising data.

Credentials must never be committed to version control.

Local configuration files and Terraform state files
are excluded from Git.

Production workloads will use dedicated identities,
restricted access and short-lived credentials.

## 7. Current Implementation Status

Implemented:

- Local development environment.
- Google Cloud CLI authentication.
- Application Default Credentials.
- Python application configuration.
- Configuration validation.
- Initial application-level cost guardrails.
- Automated unit tests.
- Developer tooling and smoke tests.

Cloud infrastructure and data processing pipelines
will be implemented in subsequent milestones.
