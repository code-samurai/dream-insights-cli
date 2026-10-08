"""HTTP client for Dream Insights public fleet reads."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote

import httpx

from dream_insights_cli import config

# Standing fleet extract + query-helper routes (public OpenAPI).
ROUTES: dict[str, str] = {
    "ontology": "/api/v1/properties/{property_id}/ontology/live",
    "events": "/api/v1/properties/{property_id}/events",
    "event": "/api/v1/properties/{property_id}/events/{event_id}",
    "entities": "/api/v1/properties/{property_id}/entities/{entity_type}",
    "entity": "/api/v1/properties/{property_id}/entities/{entity_type}/{entity_id}",
    "timeline": "/api/v1/properties/{property_id}/persons/{person_id}/timeline",
    "transitions": "/api/v1/properties/{property_id}/transitions",
    "similar-persons": "/api/v1/properties/{property_id}/search/similar-persons",
    "similar-cohorts": "/api/v1/properties/{property_id}/search/similar-cohorts",
    "similar-pathways": "/api/v1/properties/{property_id}/search/similar-pathways",
    "semantic": "/api/v1/properties/{property_id}/search/semantic",
    "roas": "/api/v1/properties/{property_id}/roas",
    "campaign-roas": "/api/v1/properties/{property_id}/campaign-roas",
    "findings": "/api/v1/properties/{property_id}/findings",
    "ledger-metrics": "/api/v1/properties/{property_id}/ledger/metrics",
}

MCP_FLEET_PATH = "/mcp/fleet/"
DEFAULT_TIMEOUT = 30.0


class ClickExit(Exception):
    """Raised to exit with a user-friendly message."""

    def __init__(self, message: str):
        self.message = message
        super().__init__(message)


def click_exit(message: str) -> ClickExit:
    return ClickExit(message)


def _render_path(template: str, **values: Any) -> str:
    encoded = {name: quote(str(value), safe="") for name, value in values.items()}
    return template.format(**encoded)


class DreamInsightsClient:
    """Thin httpx wrapper for standing fleet GET routes."""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        timeout: float = DEFAULT_TIMEOUT,
    ):
        import os

        cfg = config.load()
        env_url = os.environ.get("DREAM_INSIGHTS_BASE_URL") or os.environ.get(
            "DREAM_INSIGHTS_API_URL"
        )
        self.api_url = (api_url or env_url or cfg.get("api_url") or "").rstrip("/")
        env_key = (
            os.environ.get("DREAM_INSIGHTS_API_KEY")
            or os.environ.get("DREAM_INSIGHTS_FLEET_API_KEY")
            or os.environ.get("DREAM_INSIGHTS_FLEET_READ_TOKEN")
        )
        if api_key is not None:
            self.api_key = api_key
        else:
            self.api_key = env_key or cfg.get("api_key")
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Accept": "application/json"}
        if self.api_key:
            h["X-API-Key"] = self.api_key
        return h

    def _handle_error(self, resp: httpx.Response) -> None:
        if resp.status_code == 401:
            raise click_exit("Not authenticated. Run: di auth login")
        if resp.status_code == 403:
            detail = _safe_detail(resp) or "Access denied. Check key class and property scope."
            raise click_exit(detail)
        if resp.status_code == 404:
            raise click_exit(_safe_detail(resp) or f"Not found: {resp.url.path}")
        if resp.status_code >= 400:
            raise click_exit(f"API error ({resp.status_code}): {_safe_detail(resp) or resp.text[:200]}")

    def get(
        self,
        command: str,
        *,
        path_params: dict[str, Any] | None = None,
        query: dict[str, Any] | None = None,
    ) -> Any:
        """GET a standing fleet route by command name. Returns parsed JSON."""
        if command not in ROUTES:
            raise click_exit(f"Unknown command route: {command}")
        key = (self.api_key or "").strip()
        if not key:
            raise click_exit("Missing API key. Run: di auth login")
        if not self.api_url.startswith("https://"):
            raise click_exit("api_url must use https://")

        path = _render_path(ROUTES[command], **(path_params or {}))
        url = self.api_url + path
        params = {k: str(v) for k, v in (query or {}).items() if v is not None}

        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                resp = client.get(url, params=params, headers=self._headers())
        except httpx.TimeoutException as e:
            raise click_exit(f"Request timed out: {e}") from e
        except httpx.RequestError as e:
            raise click_exit(f"Connection error: {e}") from e

        self._handle_error(resp)
        if not resp.content:
            return None
        try:
            return resp.json()
        except ValueError:
            return {"detail": resp.text, "status": resp.status_code}

    def health(self) -> Any:
        """GET /health (no auth)."""
        url = self.api_url.rstrip("/") + "/health"
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                resp = client.get(url, headers={"Accept": "application/json"})
        except httpx.RequestError as e:
            raise click_exit(f"Connection error: {e}") from e
        if resp.status_code >= 400:
            raise click_exit(f"Health check failed ({resp.status_code})")
        try:
            return resp.json()
        except ValueError:
            return {"status": resp.text}


def _json_body(resp: httpx.Response) -> dict | None:
    if not resp.headers.get("content-type", "").startswith("application/json"):
        return None
    try:
        body = resp.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def _sentence(text: Any) -> str:
    clause = " ".join(str(text or "").split()).rstrip(" .")
    return f"{clause}." if clause else ""


def failure_text(resp: httpx.Response) -> str | None:
    """Owner text for a refused or failed request, or None when the body has none.

    Dream Insights failures carry ``detail`` (one plain sentence) and, for
    publish and quality refusals, ``wrong``/``why``/``next``/``fix`` plus
    ``details``, ``stale``, ``action`` and ``draft_ontology_id``. The sentence
    comes first; the next step and where to do it follow; the store detail
    (vendor words) stays last, under "Details:".
    """
    body = _json_body(resp)
    if body is None:
        return None
    detail = body.get("detail")
    if isinstance(detail, list):
        # Request validation: one line per field, no internal pydantic noise.
        parts = []
        for item in detail[:5]:
            if isinstance(item, dict):
                loc = ".".join(str(x) for x in item.get("loc", []) if x not in ("body", "query", "path"))
                parts.append(f"{loc}: {item.get('msg')}" if loc else str(item.get("msg")))
        return "; ".join(parts) or None
    head = body.get("message") if isinstance(body.get("message"), str) and body.get("message") else detail
    lines = [str(head)] if head else []
    nxt = body.get("next")
    if nxt and (not head or _sentence(nxt).rstrip(".") not in str(head)):
        lines.append(f"Next: {_sentence(nxt)}")
    fix = body.get("fix")
    if isinstance(fix, dict) and fix.get("kind"):
        target = f" {fix['target']}" if fix.get("target") else ""
        lines.append(f"Fix: {fix['kind']}{target}")
    action = body.get("action")
    draft = body.get("draft_ontology_id")
    if action in ("open_draft", "open_wizard") and draft:
        lines.append(f"Draft: {draft} (make the next changes there, then publish)")
    elif action == "start_draft":
        lines.append("Draft: none yet (write one with `di author draft`, then publish)")
    elif action == "retry" or body.get("retry") is True:
        lines.append("Retry: run `di author publish` again")
    if body.get("stale") is True:
        lines.append("Stale: a newer publish replaced this one, so there is nothing to retry")
    details = body.get("details")
    if details:
        lines.append(f"Details: {details}")
    return "\n".join(lines) or None


def _safe_detail(resp: httpx.Response) -> str | None:
    ctype = resp.headers.get("content-type", "")
    if not ctype.startswith("application/json"):
        return None
    try:
        body = resp.json()
    except ValueError:
        return None
    if isinstance(body, dict):
        detail = body.get("detail")
        if isinstance(detail, str):
            return detail
        if detail is not None:
            return str(detail)[:200]
    return None
