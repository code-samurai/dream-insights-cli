"""Unit tests for semantic / similar search commands — mocked HTTP."""

from __future__ import annotations

import json

import httpx
import respx
from click.testing import CliRunner

from dream_insights_cli.cli import main
from tests.conftest import API_URL, PERSON_ID, PROPERTY_ID


class TestSemantic:
    def test_semantic_search(self, mock_config):
        payload = {"results": [{"id": "x", "score": 0.9}]}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(f"/api/v1/properties/{PROPERTY_ID}/search/semantic").mock(
                return_value=httpx.Response(200, json=payload)
            )
            runner = CliRunner()
            result = runner.invoke(
                main,
                [
                    "semantic",
                    "--collection",
                    "EntityProfile",
                    "--query",
                    "quiz lead",
                    "--limit",
                    "5",
                ],
            )
        assert result.exit_code == 0, result.output
        assert route.called
        url = str(route.calls[0].request.url)
        assert "collection=EntityProfile" in url
        assert "query=quiz+lead" in url or "query=quiz%20lead" in url
        assert json.loads(result.output)["results"][0]["score"] == 0.9

    def test_semantic_empty_results(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            rsps.get(f"/api/v1/properties/{PROPERTY_ID}/search/semantic").mock(
                return_value=httpx.Response(200, json={"results": []})
            )
            runner = CliRunner()
            result = runner.invoke(
                main, ["semantic", "--collection", "PersonProfile", "--query", "none"]
            )
        assert result.exit_code == 0
        assert json.loads(result.output)["results"] == []


class TestSimilar:
    def test_similar_persons(self, machine_config):
        payload = {"results": []}
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(
                f"/api/v1/properties/{PROPERTY_ID}/search/similar-persons"
            ).mock(return_value=httpx.Response(200, json=payload))
            runner = CliRunner()
            result = runner.invoke(main, ["similar-persons", "--person-id", PERSON_ID])
        assert result.exit_code == 0, result.output
        assert route.called
        assert route.calls[0].request.headers.get("X-API-Key") == "machine_reader_test_placeholder"

    def test_similar_pathways(self, mock_config):
        with respx.mock(base_url=API_URL) as rsps:
            route = rsps.get(
                f"/api/v1/properties/{PROPERTY_ID}/search/similar-pathways"
            ).mock(return_value=httpx.Response(200, json={"results": []}))
            runner = CliRunner()
            result = runner.invoke(
                main, ["similar-pathways", "--channels", "organic,paid"]
            )
        assert result.exit_code == 0
        assert "channels=organic" in str(route.calls[0].request.url)
