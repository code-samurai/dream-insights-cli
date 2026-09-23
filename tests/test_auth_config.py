"""Tests for auth and config commands."""

from __future__ import annotations

import os
from pathlib import Path

from click.testing import CliRunner

from dream_insights_cli.cli import main


def test_auth_login_stores_personal_key(tmp_path, monkeypatch):
    config_dir = tmp_path / ".dream-insights"
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_file)

    runner = CliRunner()
    result = runner.invoke(main, ["auth", "login"], input="di_user_fake_placeholder\n")
    assert result.exit_code == 0, result.output
    assert "personal" in result.output.lower() or "FOR ME" in result.output
    assert config_file.exists()
    assert oct(config_file.stat().st_mode)[-3:] == "600"
    assert "di_user_fake_placeholder" in config_file.read_text()


def test_auth_login_accepts_machine_reader(tmp_path, monkeypatch):
    config_dir = tmp_path / ".dream-insights"
    config_file = config_dir / "config.yaml"
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
    monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_file)

    runner = CliRunner()
    result = runner.invoke(main, ["auth", "login"], input="fleet_machine_reader_placeholder\n")
    assert result.exit_code == 0, result.output
    assert "machine" in result.output.lower() or "AGENT" in result.output


def test_auth_status_masks_key(mock_config):
    runner = CliRunner()
    result = runner.invoke(main, ["auth", "status"])
    assert result.exit_code == 0
    assert "di_user_te" in result.output or "Authenticated" in result.output
    assert "di_user_test_placeholder_key" not in result.output


def test_config_show_masks_key(mock_config):
    runner = CliRunner()
    result = runner.invoke(main, ["config", "show"])
    assert result.exit_code == 0
    assert "api_key:" in result.output
    assert "di_user_test_placeholder_key" not in result.output


def test_config_set_rejects_http_url(mock_config):
    runner = CliRunner()
    result = runner.invoke(main, ["config", "set", "api_url", "http://insecure.example"])
    assert result.exit_code != 0


def test_mcp_config_prints_placeholders():
    runner = CliRunner()
    result = runner.invoke(main, ["mcp-config", "--client", "cursor"])
    assert result.exit_code == 0
    assert "t.leadshook.com/mcp/fleet/" in result.output
    assert "<MACHINE_READER_API_KEY>" in result.output
