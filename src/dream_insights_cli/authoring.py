"""Outside-in ontology authoring (FOR ME) — peer of /mcp/author/.

Fleet MCP (/mcp/fleet/) and machine readers stay read-only. Authoring uses a
personal Connect-apps key (di_user_…) or an operator admin key via env.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Literal
from urllib.parse import quote

import httpx
import yaml

from dream_insights_cli import config
from dream_insights_cli.client import ClickExit, click_exit, _safe_detail

AUTHORING_MCP_PATH = "/mcp/author/"
AUTHORING_MCP_URL = "https://t.leadshook.com/mcp/author/"
AUTHORING_API_KEY_ENV = "DREAM_INSIGHTS_AUTHORING_API_KEY"
AUTHORING_MCP_URL_ENV = "DREAM_INSIGHTS_AUTHORING_MCP_URL"
MACHINE_READER_PREFIX = "di_fleet_"
AUTHORING_MACHINE_DETAIL = "Machine readers cannot author ontologies"

IMPORT_PATH = "/authoring/ontologies/{property_id}/{ontology_id}/import"
DRAFT_PATH = "/authoring/ontologies/{property_id}/draft"
PUBLISH_PATH = "/authoring/ontologies/{property_id}/publish"
QUALITY_PATH = "/authoring/ontologies/{property_id}/draft/quality"
COMPETENCY_QUESTIONS_PATH = "/authoring/ontologies/{property_id}/competency-questions"
COMPETENCY_QUESTION_CONFIRM_PATH = (
    "/authoring/ontologies/{property_id}/competency-questions/{question_id}/confirm"
)

AUTHORING_TOOLS = (
    "import_ontology",
    "write_ontology",
    "publish_ontology",
    "check_ontology",
    "list_competency_questions",
    "write_competency_question",
    "confirm_competency_question",
)

DEFAULT_TIMEOUT = 60.0
AuthMode = Literal["bearer", "x-api-key"]


def is_machine_reader_secret(presented: str) -> bool:
    """True for a fleet consumer key prefix. Personal keys use di_user_."""
    return bool(presented) and presented.startswith(MACHINE_READER_PREFIX)


def refuse_machine_reader_key(api_key: str) -> str | None:
    """Return an error detail when the secret cannot author. Else None."""
    key = (api_key or "").strip()
    if not key:
        return "Missing API key"
    if is_machine_reader_secret(key):
        return AUTHORING_MACHINE_DETAIL
    return None


def load_authoring_document(path: str) -> dict:
    """Read an ActivatedOntology JSON or YAML file."""
    file = Path(path)
    try:
        text = file.read_text(encoding="utf-8")
    except OSError as exc:
        raise click_exit(f"could not read {path}: {exc}") from exc
    suffix = file.suffix.lower()
    try:
        if suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        else:
            data = json.loads(text)
    except (json.JSONDecodeError, yaml.YAMLError) as exc:
        raise click_exit(f"{path} is not valid JSON or YAML: {exc}") from exc
    if not isinstance(data, dict):
        raise click_exit(f"{path} must contain an object")
    return data


def _render_path(template: str, **values: Any) -> str:
    encoded = {name: quote(str(value), safe="") for name, value in values.items()}
    return template.format(**encoded)


def resolve_authoring_api_key(explicit: str | None = None) -> str:
    """Resolve authoring credential.

    Prefer DREAM_INSIGHTS_AUTHORING_API_KEY, then an explicit override, then
    DREAM_INSIGHTS_API_KEY / stored config. Never reads DREAM_INSIGHTS_FLEET_API_KEY.
    """
    if explicit is not None and str(explicit).strip():
        return str(explicit).strip()
    env_author = (os.environ.get(AUTHORING_API_KEY_ENV) or "").strip()
    if env_author:
        return env_author
    env_personal = (os.environ.get("DREAM_INSIGHTS_API_KEY") or "").strip()
    if env_personal:
        return env_personal
    stored = (config.get("api_key") or "")
    if isinstance(stored, str) and stored.strip():
        return stored.strip()
    return ""


class AuthoringClient:
    """HTTP client for /authoring/ontology import, draft, publish."""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        auth: AuthMode = "bearer",
        timeout: float = DEFAULT_TIMEOUT,
    ):
        cfg = config.load()
        env_url = os.environ.get("DREAM_INSIGHTS_BASE_URL") or os.environ.get(
            "DREAM_INSIGHTS_API_URL"
        )
        self.api_url = (api_url or env_url or cfg.get("api_url") or "").rstrip("/")
        self.api_key = resolve_authoring_api_key(api_key)
        self.auth: AuthMode = auth
        self.timeout = timeout

    def _headers(self) -> dict[str, str]:
        h: dict[str, str] = {"Accept": "application/json", "Content-Type": "application/json"}
        key = self.api_key
        if self.auth == "x-api-key":
            h["X-API-Key"] = key
        else:
            h["Authorization"] = f"Bearer {key}"
        return h

    def _ensure_ready(self) -> None:
        detail = refuse_machine_reader_key(self.api_key)
        if detail == "Missing API key":
            raise click_exit(
                "Missing authoring API key. Set DREAM_INSIGHTS_AUTHORING_API_KEY "
                "or run: di auth login (personal di_user_… key). "
                "Fleet keys cannot author."
            )
        if detail == AUTHORING_MACHINE_DETAIL:
            raise click_exit(AUTHORING_MACHINE_DETAIL)
        if not self.api_url.startswith("https://"):
            raise click_exit("api_url must use https://")

    def _handle_error(self, resp: httpx.Response) -> None:
        if resp.status_code == 401:
            raise click_exit("Not authenticated. Check DREAM_INSIGHTS_AUTHORING_API_KEY / di auth login")
        if resp.status_code == 403:
            raise click_exit(_safe_detail(resp) or "Access denied. Authoring needs a FOR ME personal key (or admin).")
        if resp.status_code == 404:
            raise click_exit(_safe_detail(resp) or f"Not found: {resp.url.path}")
        if resp.status_code == 409:
            raise click_exit(_safe_detail(resp) or "Conflict (draft matches live, empty, or publish in flight)")
        if resp.status_code >= 400:
            raise click_exit(f"API error ({resp.status_code}): {_safe_detail(resp) or resp.text[:200]}")

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Any | None = None,
        params: dict[str, str] | None = None,
    ) -> Any:
        self._ensure_ready()
        url = self.api_url + path
        try:
            with httpx.Client(timeout=self.timeout, follow_redirects=False) as client:
                resp = client.request(
                    method,
                    url,
                    headers=self._headers(),
                    json=json_body,
                    params=params,
                )
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

    def import_ontology(self, property_id: Any, ontology_id: Any, document: dict) -> Any:
        """POST import onto the property draft. Does not publish."""
        path = _render_path(IMPORT_PATH, property_id=property_id, ontology_id=ontology_id)
        return self._request("POST", path, json_body={"document": document})

    def write_ontology(self, property_id: Any, document: dict) -> Any:
        """PUT full-replace property draft. Creates draft when missing. Does not publish."""
        path = _render_path(DRAFT_PATH, property_id=property_id)
        return self._request("PUT", path, json_body=document)

    def publish_ontology(self, property_id: Any, *, allow_breaking: bool = False) -> Any:
        """POST publish. Materialise follows the existing publish saga."""
        path = _render_path(PUBLISH_PATH, property_id=property_id)
        params = {"allow_breaking": "true"} if allow_breaking else None
        return self._request("POST", path, params=params)

    def check_ontology(self, property_id: Any) -> Any:
        """GET the draft quality report. Read-only. No grade."""
        path = _render_path(QUALITY_PATH, property_id=property_id)
        return self._request("GET", path)

    def list_competency_questions(self, property_id: Any) -> Any:
        """GET current competency questions for the property."""
        path = _render_path(COMPETENCY_QUESTIONS_PATH, property_id=property_id)
        return self._request("GET", path)

    def write_competency_question(self, property_id: Any, body: dict) -> Any:
        """POST a new question or the next revision. Does not confirm."""
        path = _render_path(COMPETENCY_QUESTIONS_PATH, property_id=property_id)
        return self._request("POST", path, json_body=body)

    def confirm_competency_question(self, property_id: Any, question_id: Any) -> Any:
        """POST person-confirm. The server records the caller."""
        path = _render_path(
            COMPETENCY_QUESTION_CONFIRM_PATH,
            property_id=property_id,
            question_id=question_id,
        )
        return self._request("POST", path, json_body={})
