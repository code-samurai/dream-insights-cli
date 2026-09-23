"""Configuration management — ~/.dream-insights/config.yaml."""

from __future__ import annotations

import os
from pathlib import Path

import click
import yaml

CONFIG_DIR = Path.home() / ".dream-insights"
CONFIG_FILE = CONFIG_DIR / "config.yaml"

DEFAULTS = {
    "api_url": "https://t.leadshook.com",
    "api_key": None,
    "default_property_id": None,
    "output_format": "json",
}


def _ensure_dir() -> None:
    CONFIG_DIR.mkdir(mode=0o700, parents=True, exist_ok=True)


def load() -> dict:
    """Load config from disk, merging with defaults."""
    config = dict(DEFAULTS)
    if CONFIG_FILE.exists():
        with open(CONFIG_FILE) as f:
            try:
                on_disk = yaml.safe_load(f) or {}
            except yaml.YAMLError as e:
                raise click.ClickException(
                    f"Config file is malformed: {e}. "
                    f"Delete {CONFIG_FILE} and run `di auth login`."
                ) from e
        if not isinstance(on_disk, dict):
            raise click.ClickException(
                f"Config file must be a YAML mapping. Delete {CONFIG_FILE} and run `di auth login`."
            )
        config.update(on_disk)
    return config


def save(config: dict) -> None:
    """Save config to disk with user-only permissions."""
    _ensure_dir()
    with open(CONFIG_FILE, "w") as f:
        yaml.safe_dump(config, f, default_flow_style=False)
    os.chmod(CONFIG_FILE, 0o600)


def get(key: str, default=None):
    """Get a single config value."""
    return load().get(key, default)


def set_value(key: str, value) -> None:
    """Set a single config value."""
    config = load()
    config[key] = value
    save(config)


def clear_key(key: str) -> None:
    """Remove a config key (resets to default on next load merge)."""
    config = load()
    config.pop(key, None)
    save(config)
