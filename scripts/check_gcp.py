"""Verify local application configuration and GCP credentials."""

import google.auth
from google.auth.transport.requests import Request

from media_platform.settings import Settings


def main() -> None:
    settings = Settings.from_env()

    credentials, detected_project = google.auth.default(
        scopes=["https://www.googleapis.com/auth/cloud-platform"]
    )

    if detected_project != settings.project_id:
        raise RuntimeError(
            "Detected GCP project does not match the application configuration."
        )

    quota_project = getattr(
        credentials,
        "quota_project_id",
        None,
    )

    if quota_project != settings.project_id:
        raise RuntimeError(
            "ADC quota project does not match the application configuration."
        )

    credentials.refresh(Request())

    if not credentials.valid:
        raise RuntimeError("ADC credentials are invalid.")

    print("GCP ENVIRONMENT CHECK")
    print("-" * 45)
    print(f"Configured project: {settings.project_id}")
    print(f"Detected project: {detected_project}")
    print(f"Quota project: {quota_project}")
    print(f"Region: {settings.region}")
    print(f"BigQuery location: {settings.bq_location}")
    print(f"Environment: {settings.environment}")
    print(f"ADC authentication: {credentials.valid}")
    print(f"Paid jobs enabled: {settings.allow_paid_cloud_jobs}")
    print(f"Composer deployment enabled: {settings.allow_composer_deployment}")
    print("-" * 45)
    print("Environment check completed successfully.")


if __name__ == "__main__":
    main()
