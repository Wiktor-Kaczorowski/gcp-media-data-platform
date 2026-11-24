from pathlib import Path

import pytest
from pydantic import ValidationError

from media_platform.framework import (
    PipelineConfig,
    QualityConfig,
    check_quality,
    load_config,
    run_pipeline,
)

CONFIG_DIR = Path(__file__).resolve().parents[2] / "configs"


def test_valid_preview_config():
    config = load_config(CONFIG_DIR / "campaign_preview.yaml")

    assert config.execution.mode == "preview"
    assert config.source.count == 10


def test_valid_publish_config():
    config = load_config(CONFIG_DIR / "campaign_publish.yaml")

    assert config.execution.mode == "publish"
    assert config.target.table == "citizen_demo_events"


def test_invalid_configuration():
    with pytest.raises(ValidationError):
        load_config(CONFIG_DIR / "invalid_pipeline.yaml")


def test_unknown_config_field():
    config = load_config(CONFIG_DIR / "campaign_preview.yaml").model_dump()

    config["unauthorized_option"] = True

    with pytest.raises(ValidationError):
        PipelineConfig.model_validate(config)


def test_publish_requires_explicit_permission():
    config = load_config(CONFIG_DIR / "campaign_publish.yaml")

    with pytest.raises(
        ValueError,
        match="explicit --publish",
    ):
        run_pipeline(config)


def test_quality_gate_passes():
    config = QualityConfig(
        max_invalid_records=1,
        max_duplicate_records=1,
    )

    result = check_quality(
        valid_records=[
            {"event_id": "evt-1"},
            {"event_id": "evt-1"},
            {"event_id": "evt-2"},
        ],
        invalid_records=[
            {"error_reason": "invalid spend"},
        ],
        config=config,
    )

    assert result["status"] == "PASS"
    assert result["unique_events"] == 2
    assert result["duplicate_records"] == 1


def test_invalid_record_threshold():
    config = QualityConfig(
        max_invalid_records=0,
        max_duplicate_records=1,
    )

    with pytest.raises(
        ValueError,
        match="Invalid record threshold",
    ):
        check_quality(
            valid_records=[{"event_id": "evt-1"}],
            invalid_records=[{"error": "invalid"}],
            config=config,
        )


def test_duplicate_threshold():
    config = QualityConfig(
        max_invalid_records=1,
        max_duplicate_records=0,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate threshold",
    ):
        check_quality(
            valid_records=[
                {"event_id": "evt-1"},
                {"event_id": "evt-1"},
            ],
            invalid_records=[],
            config=config,
        )
