"""Unit tests for application configuration."""

from dataclasses import FrozenInstanceError

import pytest

from media_platform.settings import Settings


@pytest.fixture
def valid_config() -> dict[str, str]:
    return {
        "GCP_PROJECT_ID": "gcp-media-platform-test",
        "GCP_REGION": "us-central1",
        "BQ_LOCATION": "us-central1",
        "APP_ENV": "dev",
    }


def test_valid_configuration(valid_config):
    settings = Settings.from_env(valid_config)

    assert settings.project_id == "gcp-media-platform-test"
    assert settings.region == "us-central1"
    assert settings.environment == "dev"


def test_missing_project_id():
    with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
        Settings.from_env({})


def test_invalid_project_id(valid_config):
    valid_config["GCP_PROJECT_ID"] = "Invalid Project"

    with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
        Settings.from_env(valid_config)


def test_placeholder_project_id(valid_config):
    valid_config["GCP_PROJECT_ID"] = "your-gcp-project-id"

    with pytest.raises(ValueError, match="GCP_PROJECT_ID"):
        Settings.from_env(valid_config)


def test_invalid_environment(valid_config):
    valid_config["APP_ENV"] = "unknown"

    with pytest.raises(ValueError, match="APP_ENV"):
        Settings.from_env(valid_config)


def test_location_mismatch(valid_config):
    valid_config["BQ_LOCATION"] = "europe-west1"

    with pytest.raises(ValueError, match="locations must match"):
        Settings.from_env(valid_config)


def test_invalid_log_level(valid_config):
    valid_config["LOG_LEVEL"] = "UNKNOWN"

    with pytest.raises(ValueError, match="LOG_LEVEL"):
        Settings.from_env(valid_config)


def test_paid_jobs_disabled_by_default(valid_config):
    settings = Settings.from_env(valid_config)

    assert settings.allow_paid_cloud_jobs is False

    with pytest.raises(PermissionError):
        settings.require_paid_cloud_jobs()


def test_paid_jobs_explicitly_enabled(valid_config):
    valid_config["ALLOW_PAID_CLOUD_JOBS"] = "true"

    settings = Settings.from_env(valid_config)

    settings.require_paid_cloud_jobs()

    assert settings.allow_paid_cloud_jobs is True


def test_composer_requires_separate_permission(valid_config):
    valid_config["ALLOW_PAID_CLOUD_JOBS"] = "true"

    settings = Settings.from_env(valid_config)

    with pytest.raises(PermissionError):
        settings.require_composer_deployment()


def test_composer_requires_paid_jobs_permission(valid_config):
    valid_config["ALLOW_COMPOSER_DEPLOYMENT"] = "true"

    settings = Settings.from_env(valid_config)

    with pytest.raises(PermissionError):
        settings.require_composer_deployment()


def test_composer_explicitly_enabled(valid_config):
    valid_config["ALLOW_PAID_CLOUD_JOBS"] = "true"
    valid_config["ALLOW_COMPOSER_DEPLOYMENT"] = "true"

    settings = Settings.from_env(valid_config)

    settings.require_composer_deployment()


@pytest.mark.parametrize("value", ["yes", "1", "maybe", ""])
def test_invalid_boolean_configuration(valid_config, value):
    valid_config["ALLOW_PAID_CLOUD_JOBS"] = value

    with pytest.raises(ValueError, match="Invalid boolean"):
        Settings.from_env(valid_config)


def test_settings_are_immutable(valid_config):
    settings = Settings.from_env(valid_config)

    with pytest.raises(FrozenInstanceError):
        settings.allow_paid_cloud_jobs = True


def test_environment_overrides_dotenv(monkeypatch, tmp_path):
    monkeypatch.chdir(tmp_path)

    (tmp_path / ".env").write_text(
        "GCP_PROJECT_ID=example-project-dev\nALLOW_PAID_CLOUD_JOBS=true\n",
        encoding="utf-8",
    )

    monkeypatch.setenv("GCP_PROJECT_ID", "gcp-media-platform-test")
    monkeypatch.setenv("ALLOW_PAID_CLOUD_JOBS", "false")
    monkeypatch.setenv("GCP_REGION", "us-central1")
    monkeypatch.setenv("BQ_LOCATION", "us-central1")
    monkeypatch.setenv("APP_ENV", "dev")
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    monkeypatch.setenv("ALLOW_COMPOSER_DEPLOYMENT", "false")

    settings = Settings.from_env()

    assert settings.project_id == "gcp-media-platform-test"
    assert settings.allow_paid_cloud_jobs is False
