"""Unit tests for extract fleet commands — mocked HTTP."""

from __future__ import annotations

import json

import httpx
import respx
from click.testing import CliRunner

from dream_insights_cli.cli import main
from tests.conftest import API_URL, ENTITY_ID, EVENT_ID, PERSON_ID, PROPERTY_ID


class TestOntology:
    def test_ontology_json(self, mock_config):
        payload = {"entity_types": [{"name": "lead", "statuses": ["new"]}]}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(f"/api/v1/properties/{PROPERTY_ID}/ontology/live").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(main, ["--format", "json", "ontology"])
        assert result.exit_code == 0, result.output
        assert route.called
        assert route.calls[0].request.headers.get("X-API-Key") == "di_user_test_placeholder_key"
        data = json.loads(result.output)
        assert data["entity_types"][0]["name"] == "lead"

    def test_ontology_requires_auth(self, tmp_path, monkeypatch):
        config_dir = tmp_path / ".dream-insights"
        config_dir.mkdir()
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_dir / "config.yaml")
        import yaml

        with open(config_dir / "config.yaml", "w") as f:
            yaml.safe_dump({"api_url": API_URL, "default_property_id": PROPERTY_ID}, f)

        runner = CliRunner()
        result = runner.invoke(main, ["ontology"])
        assert result.exit_code != 0
        assert "auth login" in result.output.lower() or "Missing API key" in result.output


class TestEvents:
    def test_events_list(self, mock_config):
        payload = {"items": [{"id": EVENT_ID, "event_name": "quiz_completed"}], "total": 1}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(f"/api/v1/properties/{PROPERTY_ID}/events").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(
                main, ["events", "--limit", "10", "--event-name", "quiz_completed"]
            )
        assert result.exit_code == 0, result.output
        assert route.called
        assert "limit=10" in str(route.calls[0].request.url)
        assert "event_name=quiz_completed" in str(route.calls[0].request.url)
        data = json.loads(result.output)
        assert data["items"][0]["event_name"] == "quiz_completed"

    def test_events_empty_is_success(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(f"/api/v1/properties/{PROPERTY_ID}/events").mock(
                return_value=httpx.Response(200, json={"items": [], "total": 0})
            )
            runner = CliRunner()
            result = runner.invoke(main, ["events"])
        assert result.exit_code == 0
        assert json.loads(result.output)["items"] == []

    def test_event_detail(self, mock_config):
        payload = {"id": EVENT_ID, "properties": {"a": 1}, "context": {}}
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(f"/api/v1/properties/{PROPERTY_ID}/events/{EVENT_ID}").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(main, ["event", "--event-id", EVENT_ID])
        assert result.exit_code == 0
        assert json.loads(result.output)["properties"]["a"] == 1


class TestEntities:
    def test_entities_list(self, mock_config):
        payload = {"items": [{"id": ENTITY_ID, "status": "new"}]}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(f"/api/v1/properties/{PROPERTY_ID}/entities/lead").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(main, ["entities", "--entity-type", "lead"])
        assert result.exit_code == 0, result.output
        assert route.called
        assert json.loads(result.output)["items"][0]["id"] == ENTITY_ID

    def test_entity_detail(self, mock_config):
        payload = {"id": ENTITY_ID, "entity_type": "lead"}
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(f"/api/v1/properties/{PROPERTY_ID}/entities/lead/{ENTITY_ID}").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(
                main, ["entity", "--entity-type", "lead", "--entity-id", ENTITY_ID]
            )
        assert result.exit_code == 0
        assert json.loads(result.output)["id"] == ENTITY_ID


class TestTimelineTransitions:
    def test_timeline(self, mock_config):
        payload = {"person_id": PERSON_ID, "items": []}
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(
                f"/api/v1/properties/{PROPERTY_ID}/persons/{PERSON_ID}/timeline"
            ).mock(return_value=httpx.Response(200, json=payload))
            runner = CliRunner()
            result = runner.invoke(main, ["timeline", "--person-id", PERSON_ID])
        assert result.exit_code == 0
        assert json.loads(result.output)["person_id"] == PERSON_ID

    def test_transitions(self, mock_config):
        payload = {"items": []}
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(f"/api/v1/properties/{PROPERTY_ID}/transitions").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(main, ["transitions"])
        assert result.exit_code == 0
        assert json.loads(result.output)["items"] == []


class TestErrors:
    def test_403_surfaces_detail(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(f"/api/v1/properties/{PROPERTY_ID}/ontology/live").mock(
                return_value=httpx.Response(403, json={"detail": "property not in scope"})
            )
            runner = CliRunner()
            result = runner.invoke(main, ["ontology"])
        assert result.exit_code != 0
        assert "property not in scope" in result.output

    def test_explicit_property_id_overrides_default(self, mock_config):
        other = "00000000-0000-4000-8000-0000000000ee"
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(f"/api/v1/properties/{other}/ontology/live").mock(
                return_value=httpx.Response(200, json={"ok": True})
            )
            runner = CliRunner()
            result = runner.invoke(main, ["ontology", "--property-id", other])
        assert result.exit_code == 0
        assert route.called
