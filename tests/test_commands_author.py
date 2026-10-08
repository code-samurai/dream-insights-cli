"""Unit tests for ontology authoring commands — mocked HTTP."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import respx
from click.testing import CliRunner

from dream_insights_cli.cli import main
from tests.conftest import API_URL, PROPERTY_ID

ONTOLOGY_ID = "00000000-0000-4000-8000-0000000000ee"
EXAMPLE = Path(__file__).resolve().parents[1] / "examples" / "activated-ontology.outside-in.yaml"


class TestAuthorDraft:
    def test_draft_put(self, mock_config):
        payload = {"status": "draft", "property_id": PROPERTY_ID}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.put(f"/authoring/ontologies/{PROPERTY_ID}/draft").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "author",
                    "draft",
                    "--property-id",
                    PROPERTY_ID,
                    "--file",
                    str(EXAMPLE),
                ],
            )
        assert result.exit_code == 0, result.output
        assert route.called
        req = route.calls[0].request
        assert req.headers.get("Authorization", "").startswith("Bearer di_user_")
        assert "X-API-Key" not in req.headers or not req.headers.get("X-API-Key")
        body = json.loads(req.content.decode())
        assert body["name"] == "Outside-in quiz funnel"
        assert json.loads(result.output)["status"] == "draft"

    def test_draft_x_api_key_auth(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.put(f"/authoring/ontologies/{PROPERTY_ID}/draft").mock(
                return_value=httpx.Response(200, json={"ok": True})
            )
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "author",
                    "draft",
                    "--auth",
                    "x-api-key",
                    "--property-id",
                    PROPERTY_ID,
                    "--file",
                    str(EXAMPLE),
                ],
            )
        assert result.exit_code == 0, result.output
        assert route.calls[0].request.headers.get("X-API-Key") == "di_user_test_placeholder_key"
        assert "Authorization" not in route.calls[0].request.headers


class TestAuthorImport:
    def test_import_post(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(
                f"/authoring/ontologies/{PROPERTY_ID}/{ONTOLOGY_ID}/import"
            ).mock(return_value=httpx.Response(200, json={"imported": True}))
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "author",
                    "import",
                    "--property-id",
                    PROPERTY_ID,
                    "--ontology-id",
                    ONTOLOGY_ID,
                    "--file",
                    str(EXAMPLE),
                ],
            )
        assert result.exit_code == 0, result.output
        assert route.called
        body = json.loads(route.calls[0].request.content.decode())
        assert "document" in body
        assert body["document"]["entities"][0]["name"] == "lead"


class TestAuthorPublish:
    def test_publish_post(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/publish").mock(
                return_value=httpx.Response(200, json={"status": "publishing"})
            )
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["author", "publish", "--property-id", PROPERTY_ID],
            )
        assert result.exit_code == 0, result.output
        assert route.called
        assert "allow_breaking" not in str(route.calls[0].request.url)

    def test_publish_allow_breaking_query(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/publish").mock(
                return_value=httpx.Response(200, json={"status": "publishing"})
            )
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["author", "publish", "--property-id", PROPERTY_ID, "--allow-breaking"],
            )
        assert result.exit_code == 0, result.output
        assert "allow_breaking=true" in str(route.calls[0].request.url)


class TestAuthorKeyPolicy:
    def test_refuses_di_fleet_key(self, tmp_path, monkeypatch):
        import yaml

        config_dir = tmp_path / ".dream-insights"
        config_dir.mkdir()
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_dir / "config.yaml")
        with open(config_dir / "config.yaml", "w") as f:
            yaml.safe_dump(
                {
                    "api_url": API_URL,
                    "api_key": "di_fleet_test_placeholder",
                    "default_property_id": PROPERTY_ID,
                },
                f,
            )

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "author",
                "draft",
                "--property-id",
                PROPERTY_ID,
                "--file",
                str(EXAMPLE),
            ],
        )
        assert result.exit_code != 0
        assert "cannot author" in result.output.lower() or "Machine readers" in result.output

    def test_does_not_use_fleet_env_key(self, tmp_path, monkeypatch):
        """Authoring must not fall back to DREAM_INSIGHTS_FLEET_API_KEY."""
        import yaml

        config_dir = tmp_path / ".dream-insights"
        config_dir.mkdir()
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_dir / "config.yaml")
        with open(config_dir / "config.yaml", "w") as f:
            yaml.safe_dump({"api_url": API_URL}, f)
        monkeypatch.setenv("DREAM_INSIGHTS_FLEET_API_KEY", "di_fleet_should_not_be_used")

        runner = CliRunner()
        result = runner.invoke(
            main,
            [
                "author",
                "publish",
                "--property-id",
                PROPERTY_ID,
            ],
        )
        assert result.exit_code != 0
        assert "Missing" in result.output or "auth" in result.output.lower()

    def test_prefers_authoring_env_key(self, tmp_path, monkeypatch):
        import yaml

        config_dir = tmp_path / ".dream-insights"
        config_dir.mkdir()
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_DIR", config_dir)
        monkeypatch.setattr("dream_insights_cli.config.CONFIG_FILE", config_dir / "config.yaml")
        with open(config_dir / "config.yaml", "w") as f:
            yaml.safe_dump(
                {
                    "api_url": API_URL,
                    "api_key": "di_user_stored_should_lose",
                },
                f,
            )
        monkeypatch.setenv("DREAM_INSIGHTS_AUTHORING_API_KEY", "di_user_authoring_env_key")

        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/publish").mock(
                return_value=httpx.Response(200, json={"ok": True})
            )
            runner = CliRunner()
            result = runner.invoke(
                main,
                ["author", "publish", "--property-id", PROPERTY_ID],
            )
        assert result.exit_code == 0, result.output
        assert route.calls[0].request.headers.get("Authorization") == (
            "Bearer di_user_authoring_env_key"
        )


class TestMcpConfigSurfaces:
    def test_fleet_surface(self):
        runner = CliRunner()
        result = runner.invoke(main, ["mcp-config", "--client", "generic", "--surface", "fleet"])
        assert result.exit_code == 0
        assert "/mcp/fleet/" in result.output
        assert "MACHINE_READER" in result.output

    def test_author_surface(self):
        runner = CliRunner()
        result = runner.invoke(main, ["mcp-config", "--client", "cursor", "--surface", "author"])
        assert result.exit_code == 0
        assert "/mcp/author/" in result.output
        assert "di_user_YOUR_PERSONAL_KEY" in result.output
        assert "dream-insights-authoring" in result.output


class TestAuthorCheck:
    def test_check_gets_the_quality_report(self, mock_config):
        payload = {
            "breaks_extraction": [],
            "worth_fixing": [],
            "questions": [],
            "schema_diff": {"added_entities": [], "breaking_flags": []},
        }
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(f"/authoring/ontologies/{PROPERTY_ID}/draft/quality").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(main, ["author", "check", "--property", PROPERTY_ID])
        assert result.exit_code == 0, result.output
        assert route.called
        body = json.loads(result.output)
        assert body["breaks_extraction"] == []
        assert "grade" not in body


class TestAuthorCompetencyQuestions:
    def test_cq_write_posts_the_structured_path(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(
                f"/authoring/ontologies/{PROPERTY_ID}/competency-questions"
            ).mock(return_value=httpx.Response(200, json={"revision": 1}))
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "author",
                    "cq",
                    "write",
                    "--property",
                    PROPERTY_ID,
                    "--text",
                    "How many leads?",
                    "--critical",
                    "--entity",
                    "lead",
                    "--status",
                    "new",
                    "--time-window",
                    "7d",
                ],
            )
        assert result.exit_code == 0, result.output
        sent = json.loads(route.calls[0].request.content.decode())
        assert sent == {
            "text": "How many leads?",
            "critical": True,
            "entity_name": "lead",
            "status_name": "new",
            "time_window": "7d",
        }  # unset fields are not sent (the server keeps them on a revision)


class TestWalkD5425884:
    """Revise sends only what changed; failure fields and plain 422 sentences."""

    def _run(self, args):
        return CliRunner().invoke(main, args)

    def test_revise_sends_only_changed_fields(self, mock_config):
        qid = "00000000-0000-4000-8000-0000000000aa"
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/competency-questions").mock(
                return_value=httpx.Response(200, json={"id": qid})
            )
            result = self._run(["author", "cq", "write", "--property-id", PROPERTY_ID,
                                "--question-id", qid, "--status", "paid"])
        assert result.exit_code == 0, result.output
        assert json.loads(route.calls[0].request.content) == {"status_name": "paid", "question_id": qid}

    def test_revise_can_unmark_and_clear(self, mock_config):
        qid = "00000000-0000-4000-8000-0000000000aa"
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/competency-questions").mock(
                return_value=httpx.Response(200, json={"id": qid})
            )
            result = self._run(["author", "cq", "write", "--property-id", PROPERTY_ID,
                                "--question-id", qid, "--not-critical", "--dimension", ""])
        assert result.exit_code == 0, result.output
        assert json.loads(route.calls[0].request.content) == {
            "critical": False, "dimension_name": "", "question_id": qid}

    def test_create_needs_text_and_omits_unset_critical(self, mock_config):
        result = self._run(["author", "cq", "write", "--property-id", PROPERTY_ID])
        assert result.exit_code == 1 and "--text is required" in result.output
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/competency-questions").mock(
                return_value=httpx.Response(200, json={"id": "q"})
            )
            result = self._run(["author", "cq", "write", "--property-id", PROPERTY_ID,
                                "--text", "How many leads reach paid?"])
        assert result.exit_code == 0, result.output
        assert json.loads(route.calls[0].request.content) == {"text": "How many leads reach paid?"}

    def test_empty_revision_is_refused_locally(self, mock_config):
        result = self._run(["author", "cq", "write", "--property-id", PROPERTY_ID,
                            "--question-id", "00000000-0000-4000-8000-0000000000aa"])
        assert result.exit_code == 1 and "Nothing to revise" in result.output

    def test_plain_422_sentence_with_fix(self, mock_config):
        body = {
            "detail": "Publish failed: the names step2 and step_2 would be stored under the same name.",
            "message": "Publish failed: the names step2 and step_2 would be stored under the same name.",
            "wrong": "the names step2 and step_2 would be stored under the same name",
            "next": "Rename step_2 (for example to step_2_alt)",
            "fix": {"kind": "rename_entity", "target": "step_2"},
            "retry": False,
        }
        with respx.mock(base_url=API_URL) as rsps:
            rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/publish").mock(
                return_value=httpx.Response(422, json=body)
            )
            result = self._run(["author", "publish", "--property-id", PROPERTY_ID])
        assert result.exit_code == 1
        assert "API error" not in result.output
        assert "Error: Publish failed: the names step2 and step_2" in result.output
        assert "Next: Rename step_2 (for example to step_2_alt)." in result.output
        assert "Fix: rename_entity step_2" in result.output

    def test_store_failure_fields(self, mock_config):
        body = {
            "detail": "Publish failed: the search store didn't respond.",
            "next": "Wait a moment for the store to recover, then try again",
            "retry": True, "action": "retry", "stale": False,
            "details": "Weaviate 503 Service Unavailable",
            "fix": {"kind": "publish", "target": ""},
        }
        with respx.mock(base_url=API_URL) as rsps:
            rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/publish").mock(
                return_value=httpx.Response(503, json=body)
            )
            result = self._run(["author", "publish", "--property-id", PROPERTY_ID])
        assert result.exit_code == 1
        lines = result.output.strip().splitlines()
        assert lines[0] == "Error: Publish failed: the search store didn't respond."
        assert "Retry: run `di author publish` again" in lines
        assert lines[-1] == "Details: Weaviate 503 Service Unavailable"  # vendor words last

    def test_stale_failure_points_at_the_draft(self, mock_config):
        body = {"detail": "This publish failed, then v4 went live after it, so there's nothing to retry.",
                "stale": True, "action": "open_wizard", "draft_ontology_id": "d-5", "retry": False}
        with respx.mock(base_url=API_URL) as rsps:
            rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/publish").mock(
                return_value=httpx.Response(409, json=body)
            )
            result = self._run(["author", "publish", "--property-id", PROPERTY_ID])
        assert "Draft: d-5 (make the next changes there, then publish)" in result.output
        assert "Stale: a newer publish replaced this one" in result.output

    def test_expected_updated_at_and_draft_changed(self, mock_config):
        changed = {"detail": "This draft changed after you opened it. Reload to get the latest, then save again."}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.put(f"/authoring/ontologies/{PROPERTY_ID}/draft").mock(
                return_value=httpx.Response(409, json=changed)
            )
            result = self._run(["author", "draft", "--property-id", PROPERTY_ID, "--file", str(EXAMPLE),
                                "--expected-updated-at", "2026-10-08T16:06:00.123456Z"])
        assert result.exit_code == 1
        assert json.loads(route.calls[0].request.content)["expected_updated_at"] == "2026-10-08T16:06:00.123456Z"
        assert "This draft changed after you opened it." in result.output
        assert "--expected-updated-at" in result.output

    def test_import_sends_token_and_prints_notice(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/{ONTOLOGY_ID}/import").mock(
                return_value=httpx.Response(200, json={"status": "draft", "notice": "Added 2 questions from the file to Quality."})
            )
            result = CliRunner().invoke(main, [
                "author", "import", "--property-id", PROPERTY_ID, "--ontology-id", ONTOLOGY_ID,
                "--file", str(EXAMPLE), "--expected-updated-at", "2026-10-08T16:06:00Z"])
        assert result.exit_code == 0, result.output
        sent = json.loads(route.calls[0].request.content)
        assert sent["expected_updated_at"] == "2026-10-08T16:06:00Z" and "document" in sent
        assert "Added 2 questions from the file to Quality." in result.stderr
        assert json.loads(result.stdout)["status"] == "draft"

    def test_validation_422_is_one_line_per_field(self, mock_config):
        body = {"detail": [{"loc": ["body", "critical"], "msg": "Input should be a valid boolean", "type": "bool"}]}
        with respx.mock(base_url=API_URL) as rsps:
            rsps.post(f"/authoring/ontologies/{PROPERTY_ID}/competency-questions").mock(
                return_value=httpx.Response(422, json=body)
            )
            result = self._run(["author", "cq", "write", "--property-id", PROPERTY_ID, "--text", "Q?"])
        assert "Error: critical: Input should be a valid boolean" in result.output
