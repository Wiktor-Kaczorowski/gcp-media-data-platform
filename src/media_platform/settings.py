"""Application configuration and deployment guardrails."""

import os
import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Self

from dotenv import dotenv_values


@dataclass(frozen=True)
class Settings:
    project_id: str
    region: str
    bq_location: str
    environment: str
    log_level: str
    allow_paid_cloud_jobs: bool
    allow_composer_deployment: bool

    @classmethod
    def from_env(
        cls,
        values: Mapping[str, str | None] | None = None,
    ) -> Self:
        if values is None:
            values = {
                **dotenv_values(".env"),
                **os.environ,
            }

        project_id = values.get("GCP_PROJECT_ID") or ""

        if project_id == "your-gcp-project-id" or not re.fullmatch(
            r"[a-z][a-z0-9-]{4,28}[a-z0-9]",
            project_id,
        ):
            raise ValueError("A valid GCP_PROJECT_ID is required.")

        environment = values.get("APP_ENV") or "dev"

        if environment not in {"dev", "test", "prod"}:
            raise ValueError("Invalid APP_ENV value.")

        region = values.get("GCP_REGION") or "us-central1"
        bq_location = values.get("BQ_LOCATION") or region

        if region != bq_location:
            raise ValueError("GCP and BigQuery locations must match.")

        log_level = (values.get("LOG_LEVEL") or "INFO").upper()

        if log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            raise ValueError("Invalid LOG_LEVEL value.")

        return cls(
            project_id=project_id,
            region=region,
            bq_location=bq_location,
            environment=environment,
            log_level=log_level,
            allow_paid_cloud_jobs=cls._parse_bool(values.get("ALLOW_PAID_CLOUD_JOBS")),
            allow_composer_deployment=cls._parse_bool(
                values.get("ALLOW_COMPOSER_DEPLOYMENT")
            ),
        )

    @staticmethod
    def _parse_bool(value: str | None) -> bool:
        normalized = "false" if value is None else value.strip().lower()

        if normalized not in {"true", "false"}:
            raise ValueError("Invalid boolean configuration.")

        return normalized == "true"

    def require_paid_cloud_jobs(self) -> None:
        if not self.allow_paid_cloud_jobs:
            raise PermissionError("Paid cloud jobs are disabled.")

    def require_composer_deployment(self) -> None:
        self.require_paid_cloud_jobs()

        if not self.allow_composer_deployment:
            raise PermissionError("Composer deployment is disabled.")
