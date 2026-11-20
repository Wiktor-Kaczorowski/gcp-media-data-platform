
# Cloud Cost Management

## 1. Objective

The project is developed under a limited cloud budget.

The objective is to demonstrate real Google Cloud
engineering capabilities while minimizing unnecessary
resource consumption and avoiding out-of-pocket expenses.

## 2. Cost Management Principles

- Develop and test locally whenever possible.
- Use small synthetic datasets.
- Review infrastructure plans before deployment.
- Limit the lifetime of cloud processing jobs.
- Avoid unnecessary always-on services.
- Monitor cloud resource usage and billing.
- Remove temporary resources after validation.

## 3. Service-Level Strategy

| Service | Cost Management Strategy |
|---|---|
| Cloud Storage | Small datasets and lifecycle policies |
| BigQuery | Partitioning, dry runs, maximum bytes billed |
| Pub/Sub | Limited message volume and retention |
| Dataflow | Short jobs, limited workers, explicit termination |
| Cloud Composer | Disabled by default |
| Apache Airflow | Local Docker-based deployment |
| Artifact Registry | Small images and cleanup policies |
| Cloud Build | Limited builds and execution time |
| Cloud Logging | Relevant logs and controlled volume |

## 4. Application-Level Guardrails

The initial application configuration disables paid
cloud jobs and Composer deployment by default.

```dotenv
ALLOW_PAID_CLOUD_JOBS=false
ALLOW_COMPOSER_DEPLOYMENT=false
```

The application configuration layer validates these
settings before they are used by execution scripts.

The implementation follows a fail-closed approach:

- Missing permission settings default to false.
- Invalid boolean values raise an exception.
- Composer deployment requires both permissions.

These settings only protect execution paths that
explicitly enforce the corresponding guardrail methods.

## 5. Infrastructure Deployment Policy

Before deploying infrastructure:

1. Verify the active Google Cloud project.
2. Verify billing status and available credits.
3. Review current service pricing.
4. Review the Terraform execution plan.
5. Identify resources that can generate charges.
6. Obtain explicit approval for paid workloads.

Temporary infrastructure should be removed after
testing when it is no longer required.

## 6. Budget Monitoring

Google Cloud budget alerts should be configured
to monitor project spending.

Planned alert thresholds:

- 20% of the configured budget.
- 40% of the configured budget.
- 60% of the configured budget.
- 80% of the configured budget.
- 100% of the configured budget.

Budget alerts do not automatically cap spending
or stop running cloud resources.

Billing information and alerts may be delayed.

## 7. Authentication and Secrets

The project does not require long-lived service
account keys for local development.

Application Default Credentials are used locally.

Workload Identity Federation is planned for CI/CD
authentication.

Sensitive files must not be stored in Git.

## 8. Cloud Resource Cleanup

After cloud workload testing:

- Confirm that Dataflow jobs are no longer running.
- Remove unnecessary Pub/Sub subscriptions.
- Delete temporary Cloud Storage objects.
- Review temporary BigQuery datasets and tables.
- Remove unused container images.
- Review remaining infrastructure and billing.

Resource cleanup must be verified rather than assumed.

## 9. Limitations

Application guardrails are not a hard cloud spending limit.

Google Cloud free-tier quotas and promotional credits
are subject to service-specific eligibility conditions.

Cloud pricing and available credits must be verified
before executing paid workloads.
