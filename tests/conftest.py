"""Shared fixtures for dream-insights-cli tests."""

from __future__ import annotations

import pytest
import yaml

API_URL = "https://test.dream-insights.example"
PROPERTY_ID = "00000000-0000-4000-8000-0000000000aa"
EVENT_ID = "00000000-0000-4000-8000-0000000000bb"
ENTITY_ID = "00000000-0000-4000-8000-0000000000cc"
PERSON_ID = "00000000-0000-4000-8000-0000000000dd"

_ENV_KEYS = (
    "DREAM_INSIGHTS_BASE_URL",
    "DREAM_INSIGHTS_API_URL",
    "DREAM_INSIGHTS_API_KEY",
    "DREAM_INSIGHTS_FLEET_API_KEY",
    "DREAM_INSIGHTS_FLEET_READ_TOKEN",
    "DREAM_INSIGHTS_AUTHORING_API_KEY",
    "DREAM_INSIGHTS_AUTHORING_MCP_URL",
)


@pytest.fixture(autouse=True)
def _clear_di_env(monkeypatch):
    """Isolate tests from host env (box may export real DI URLs/keys)."""
    for key in _ENV_KEYS:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def mock_config(tmp_path, monkeypatch):
    """Redirect config to temp dir so tests never touch ~/.dream-insights."""
    config_dir = tmp_path / ".dream-insights"
    config_dir.mkdir()
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_dir / "config.yaml")

    config = {
        "api_url": API_URL,
        "api_key": "di_user_test_placeholder_key",
        "default_property_id": PROPERTY_ID,
        "output_format": "json",
    }
    with open(config_dir / "config.yaml", "w") as f:
        yaml.safe_dump(config, f)

    return config


@pytest.fixture
def machine_config(tmp_path, monkeypatch):
    """Config with a machine-reader style key (not di_user_)."""
    config_dir = tmp_path / ".dream-insights"
    config_dir.mkdir()
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_dir / "config.yaml")

    config = {
        "api_url": API_URL,
        "api_key": "machine_reader_test_placeholder",
        "default_property_id": PROPERTY_ID,
        "output_format": "json",
    }
    with open(config_dir / "config.yaml", "w") as f:
        yaml.safe_dump(config, f)

    return config
