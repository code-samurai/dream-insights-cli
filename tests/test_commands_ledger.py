"""Placeholder fleet read for ledger metrics. Host stays https://t.leadshook.com."""

from __future__ import annotations

import json

import httpx
import respx
from click.testing import CliRunner

from dream_insights_cli.cli import main
from tests.conftest import API_URL, PROPERTY_ID


def test_ledger_metrics_get_uses_the_standing_route(mock_config):
    payload = {
        "agree_with_person": {
            "numerator": 2,
            "n": 4,
            "rate": "2/4",
            "date_from": "2026-10-01",
            "date_to": "2026-10-31",
        }
    }
    with respx.mock(base_url=API_URL) as rsps:
        route = rsps.get(f"/api/v1/properties/{PROPERTY_ID}/ledger/metrics").mock(
            return_value=httpx.Response(200, json=payload)
        )
        result = CliRunner().invoke(
            main,
            [
                "ledger-metrics",
                "--date-from",
                "2026-10-01",
                "--date-to",
                "2026-10-31",
                "--product",
                "dream-insights",
                "--field",
                "alias",
            ],
        )
    assert result.exit_code == 0, result.output
    assert route.called
    url = str(route.calls[0].request.url)
    assert url.startswith(f"{API_URL}/api/v1/properties/{PROPERTY_ID}/ledger/metrics")
    assert "date_from=2026-10-01" in url
    assert "date_to=2026-10-31" in url
    assert "product=dream-insights" in url
    assert "field=alias" in url
    body = json.loads(result.output)
    assert body["agree_with_person"]["rate"] == "2/4"
    assert body["agree_with_person"]["n"] == 4
    assert "grade" not in result.output
    assert "score" not in result.output
