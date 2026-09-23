"""Main CLI entry point — click command groups for Dream Insights fleet reads."""

from __future__ import annotations

import sys
from typing import Any
from uuid import UUID

import click

from dream_insights_cli.client import ClickExit, DreamInsightsClient
from dream_insights_cli.output import format_output

# Placeholder UUIDs for help text only — never real production IDs.
_PLACEHOLDER_PROPERTY = "<property-uuid>"
_PLACEHOLDER_EVENT = "<event-uuid>"
_PLACEHOLDER_ENTITY = "<entity-uuid>"
_PLACEHOLDER_PERSON = "<person-uuid>"


def _emit_error(exc: ClickExit) -> None:
    click.echo(f"Error: {exc.message}", err=True)
    sys.exit(1)


def _get_format(ctx) -> str:
    fmt = ctx.obj.get("format") if ctx.obj else None
    if not fmt:
        from dream_insights_cli import config

        fmt = config.get("output_format", "json")
    return fmt or "json"


def _resolve_property_id(property_id: UUID | None) -> UUID:
    if property_id is not None:
        return property_id
    from dream_insights_cli import config

    stored = config.get("default_property_id")
    if stored:
        try:
            return UUID(str(stored))
        except ValueError as e:
            raise click.ClickException(
                f"default_property_id in config is not a UUID: {stored}"
            ) from e
    raise click.ClickException(
        "Missing --property-id. Pass it or set: di config set default_property_id <uuid>"
    )


def _client() -> DreamInsightsClient:
    return DreamInsightsClient()


def _run_read(
    ctx,
    command: str,
    *,
    property_id: UUID | None,
    path_params: dict[str, Any] | None = None,
    **query: Any,
) -> None:
    pid = _resolve_property_id(property_id)
    filled = {"property_id": pid, **(path_params or {})}
    try:
        data = _client().get(command, path_params=filled, query=query or None)
    except ClickExit as e:
        _emit_error(e)
    format_output(data, _get_format(ctx))


def _optional_text(_ctx, _param, value: str | None) -> str | None:
    if value is None:
        return None
    text = value.strip()
    if not text:
        raise click.BadParameter("must not be empty")
    return text


def _required_text(_ctx, _param, value: str) -> str:
    text = value.strip()
    if not text:
        raise click.BadParameter("must not be empty")
    return text


def _iso_date(_ctx, _param, value: str) -> str:
    from datetime import date

    try:
        date.fromisoformat(value)
    except ValueError as e:
        raise click.BadParameter("must be YYYY-MM-DD") from e
    return value


def _property_option(required: bool = False):
    return click.option(
        "--property-id",
        type=click.UUID,
        required=False,
        default=None,
        help=f"Property UUID (path grain). Default from config. Example: {_PLACEHOLDER_PROPERTY}",
    )


@click.group()
@click.version_option(package_name="dream-insights-cli")
@click.option(
    "--format",
    "output_format",
    type=click.Choice(["json", "table", "text"]),
    default=None,
    help="Output format (default: json)",
)
@click.pass_context
def main(ctx, output_format):
    """Dream Insights CLI — fleet standing reads (data only; you build the insight).

    Authenticate with a personal key (di_user_…) or a machine reader.
    Host: https://t.leadshook.com  ·  Auth: X-API-Key
    """
    ctx.ensure_object(dict)
    if output_format:
        ctx.obj["format"] = output_format


# ---------------------------------------------------------------------------
# auth
# ---------------------------------------------------------------------------


@main.group()
def auth():
    """Authenticate with Dream Insights."""


@auth.command("login")
def auth_login():
    """Store an API key in ~/.dream-insights/config.yaml (mode 0600).

    Accepts a personal key (di_user_…) or a machine reader (FOR AGENT).
    """
    from dream_insights_cli import config

    api_key = click.prompt(
        "Enter your API key (di_user_… personal, or machine reader)",
        hide_input=True,
    ).strip()
    if not api_key:
        click.echo("Error: empty key", err=True)
        sys.exit(1)
    if api_key.lower().startswith("admin") or "ADMIN_API_KEY" in api_key:
        click.echo("Error: admin keys are not accepted by this CLI", err=True)
        sys.exit(1)

    config.set_value("api_key", api_key)
    kind = "personal (FOR ME)" if api_key.startswith("di_user_") else "machine reader (FOR AGENT)"
    click.echo(f"Stored {kind} key in {config.CONFIG_FILE} (0600).")
    click.echo("Tip: set a default property with: di config set default_property_id <uuid>")


@auth.command("logout")
def auth_logout():
    """Clear the stored API key."""
    from dream_insights_cli import config

    config.clear_key("api_key")
    click.echo("Logged out.")


@auth.command("status")
def auth_status():
    """Show current authentication status (key masked)."""
    from dream_insights_cli import config

    cfg = config.load()
    key = cfg.get("api_key")
    if key:
        prefix = key[:10] + "…" if len(key) > 10 else key[:4] + "…"
        kind = "personal" if key.startswith("di_user_") else "machine-reader"
        click.echo(f"Authenticated: {prefix} ({kind})")
        click.echo(f"API URL: {cfg.get('api_url', 'not set')}")
        if cfg.get("default_property_id"):
            click.echo(f"Default property: {cfg['default_property_id']}")
        else:
            click.echo("No default_property_id. Pass --property-id on each read.")
    else:
        click.echo("Not authenticated. Run: di auth login")


# ---------------------------------------------------------------------------
# config
# ---------------------------------------------------------------------------


@main.group("config")
def config_cmd():
    """View and modify configuration."""


@config_cmd.command("show")
def config_show():
    """Display current configuration (API key masked)."""
    from dream_insights_cli import config

    cfg = config.load()
    for k, v in sorted(cfg.items()):
        if k == "api_key" and v:
            v = (v[:10] + "…") if len(str(v)) > 10 else "***"
        click.echo(f"{k}: {v}")


@config_cmd.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key, value):
    """Set a configuration value.

    Prefer `di auth login` for api_key (avoids shell history).
    """
    from dream_insights_cli import config

    if key == "api_url" and not value.startswith("https://"):
        raise click.ClickException("api_url must use https:// to protect your API key in transit.")
    if key == "api_key":
        click.echo(
            "Warning: prefer `di auth login` so the key is not stored in shell history.",
            err=True,
        )
    config.set_value(key, value)
    display = (value[:4] + "***") if key == "api_key" else value
    click.echo(f"Set {key} = {display}")


# ---------------------------------------------------------------------------
# health / mcp helpers
# ---------------------------------------------------------------------------


@main.command("health")
@click.pass_context
def health_cmd(ctx):
    """GET /health (no auth)."""
    try:
        data = _client().health()
    except ClickExit as e:
        _emit_error(e)
    format_output(data, _get_format(ctx))


@main.command("mcp-config")
@click.option(
    "--client",
    type=click.Choice(["claude-code", "cursor", "generic"]),
    default="generic",
    show_default=True,
    help="Which MCP client JSON shape to print.",
)
def mcp_config_cmd(client: str):
    """Print paste-ready MCP JSON placeholders (fleet MCP URL).

    Fleet MCP requires a machine reader (FOR AGENT). Personal di_user_ keys
    are refused by /mcp/fleet/.
    """
    import json

    url = "https://t.leadshook.com/mcp/fleet/"
    headers = {"X-API-Key": "<MACHINE_READER_API_KEY>"}

    if client == "claude-code":
        payload = {
            "mcpServers": {
                "dream-insights": {
                    "url": url,
                    "headers": headers,
                }
            }
        }
        click.echo("# ~/.claude/claude.json (or project .mcp.json) — replace the placeholder key")
    elif client == "cursor":
        payload = {
            "mcpServers": {
                "dream-insights": {
                    "url": url,
                    "headers": headers,
                }
            }
        }
        click.echo("# Cursor MCP settings (JSON) — replace the placeholder key")
    else:
        payload = {"url": url, "headers": headers}
        click.echo("# Generic fleet MCP connection")

    click.echo(json.dumps(payload, indent=2))
    click.echo(
        "\n# Note: use a machine reader (FOR AGENT). Personal di_user_ keys are refused by fleet MCP.",
        err=True,
    )


# ---------------------------------------------------------------------------
# Extract reads
# ---------------------------------------------------------------------------


@main.command("ontology")
@_property_option()
@click.pass_context
def ontology_cmd(ctx, property_id):
    """Live ontology catalog for one property."""
    _run_read(ctx, "ontology", property_id=property_id)


@main.command("events")
@_property_option()
@click.option("--limit", type=click.IntRange(1, 200), default=50, show_default=True)
@click.option("--offset", type=click.IntRange(min=0), default=0, show_default=True)
@click.option("--event-name", default=None, callback=_optional_text)
@click.option("--page-domain", default=None, callback=_optional_text)
@click.pass_context
def events_cmd(ctx, property_id, limit, offset, event_name, page_domain):
    """Paginated events. List rows omit properties and context."""
    _run_read(
        ctx,
        "events",
        property_id=property_id,
        limit=limit,
        offset=offset,
        event_name=event_name,
        page_domain=page_domain,
    )


@main.command("event")
@_property_option()
@click.option("--event-id", type=click.UUID, required=True, help=f"Event UUID. Example: {_PLACEHOLDER_EVENT}")
@click.pass_context
def event_cmd(ctx, property_id, event_id):
    """One event, including properties and context."""
    _run_read(ctx, "event", property_id=property_id, path_params={"event_id": event_id})


@main.command("entities")
@_property_option()
@click.option("--entity-type", required=True, callback=_required_text, help="Entity type, e.g. lead.")
@click.option("--person-id", type=click.UUID, default=None)
@click.option("--status", default=None, callback=_optional_text)
@click.option("--limit", type=click.IntRange(1, 500), default=50, show_default=True)
@click.option("--offset", type=click.IntRange(min=0), default=0, show_default=True)
@click.pass_context
def entities_cmd(ctx, property_id, entity_type, person_id, status, limit, offset):
    """Entity instances of one type. Empty items is success."""
    _run_read(
        ctx,
        "entities",
        property_id=property_id,
        path_params={"entity_type": entity_type},
        person_id=person_id,
        status=status,
        limit=limit,
        offset=offset,
    )


@main.command("entity")
@_property_option()
@click.option("--entity-type", required=True, callback=_required_text)
@click.option("--entity-id", type=click.UUID, required=True, help=f"Entity UUID. Example: {_PLACEHOLDER_ENTITY}")
@click.pass_context
def entity_cmd(ctx, property_id, entity_type, entity_id):
    """One entity instance."""
    _run_read(
        ctx,
        "entity",
        property_id=property_id,
        path_params={"entity_type": entity_type, "entity_id": entity_id},
    )


@main.command("timeline")
@_property_option()
@click.option("--person-id", type=click.UUID, required=True, help=f"Person UUID. Example: {_PLACEHOLDER_PERSON}")
@click.pass_context
def timeline_cmd(ctx, property_id, person_id):
    """Person timeline: entity rows and transitions in time order."""
    _run_read(
        ctx,
        "timeline",
        property_id=property_id,
        path_params={"person_id": person_id},
    )


@main.command("transitions")
@_property_option()
@click.option("--person-id", type=click.UUID, default=None)
@click.option("--from-type", default=None, callback=_optional_text)
@click.option("--to-type", default=None, callback=_optional_text)
@click.option("--limit", type=click.IntRange(1, 500), default=50, show_default=True)
@click.option("--offset", type=click.IntRange(min=0), default=0, show_default=True)
@click.pass_context
def transitions_cmd(ctx, property_id, person_id, from_type, to_type, limit, offset):
    """Entity transitions for one property. Empty items is success."""
    _run_read(
        ctx,
        "transitions",
        property_id=property_id,
        person_id=person_id,
        from_type=from_type,
        to_type=to_type,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Query helpers
# ---------------------------------------------------------------------------


@main.command("similar-persons")
@_property_option()
@click.option("--person-id", type=click.UUID, required=True)
@click.option("--limit", type=click.IntRange(1, 100), default=10, show_default=True)
@click.pass_context
def similar_persons_cmd(ctx, property_id, person_id, limit):
    """PersonProfile vector neighbors. Empty results is success."""
    _run_read(
        ctx,
        "similar-persons",
        property_id=property_id,
        person_id=person_id,
        limit=limit,
    )


@main.command("similar-cohorts")
@_property_option()
@click.option("--cohort-id", type=click.UUID, required=True)
@click.option("--limit", type=click.IntRange(1, 100), default=10, show_default=True)
@click.pass_context
def similar_cohorts_cmd(ctx, property_id, cohort_id, limit):
    """CohortProfile vector neighbors. Empty results is success."""
    _run_read(
        ctx,
        "similar-cohorts",
        property_id=property_id,
        cohort_id=cohort_id,
        limit=limit,
    )


@main.command("similar-pathways")
@_property_option()
@click.option("--channels", required=True, callback=_required_text, help="Channel path text, e.g. organic,paid")
@click.option("--limit", type=click.IntRange(1, 100), default=10, show_default=True)
@click.pass_context
def similar_pathways_cmd(ctx, property_id, channels, limit):
    """PathwayPattern near-text search."""
    _run_read(
        ctx,
        "similar-pathways",
        property_id=property_id,
        channels=channels,
        limit=limit,
    )


@main.command("semantic")
@_property_option()
@click.option(
    "--collection",
    required=True,
    type=click.Choice(("PersonProfile", "CohortProfile", "PathwayPattern", "EntityProfile")),
)
@click.option("--query", required=True, callback=_required_text)
@click.option("--limit", type=click.IntRange(1, 100), default=10, show_default=True)
@click.pass_context
def semantic_cmd(ctx, property_id, collection, query, limit):
    """Property-scoped semantic search. Empty results is success."""
    _run_read(
        ctx,
        "semantic",
        property_id=property_id,
        collection=collection,
        query=query,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Optional overlays
# ---------------------------------------------------------------------------


@main.command("roas")
@_property_option()
@click.option("--date-from", required=True, callback=_iso_date)
@click.option("--date-to", required=True, callback=_iso_date)
@click.option("--model-type", default="linear", show_default=True)
@click.option("--channel", default=None)
@click.pass_context
def roas_cmd(ctx, property_id, date_from, date_to, model_type, channel):
    """Channel-grain ROAS overlay for one property."""
    _run_read(
        ctx,
        "roas",
        property_id=property_id,
        date_from=date_from,
        date_to=date_to,
        model_type=model_type,
        channel=channel,
    )


@main.command("campaign-roas")
@_property_option()
@click.option("--date-from", required=True, callback=_iso_date)
@click.option("--date-to", required=True, callback=_iso_date)
@click.option("--model-type", default="linear", show_default=True)
@click.option("--platform", default=None)
@click.pass_context
def campaign_roas_cmd(ctx, property_id, date_from, date_to, model_type, platform):
    """Campaign-grain ROAS overlay for one property."""
    _run_read(
        ctx,
        "campaign-roas",
        property_id=property_id,
        date_from=date_from,
        date_to=date_to,
        model_type=model_type,
        platform=platform,
    )


@main.command("findings")
@_property_option()
@click.option(
    "--severity-floor",
    type=click.Choice(("info", "notable", "urgent")),
    default="notable",
    show_default=True,
)
@click.option("--limit", type=click.IntRange(1, 500), default=100, show_default=True)
@click.option(
    "--ack-status",
    type=click.Choice(("unread", "read", "useful", "known", "wrong")),
    default=None,
)
@click.pass_context
def findings_cmd(ctx, property_id, severity_floor, limit, ack_status):
    """Findings overlay for one property."""
    _run_read(
        ctx,
        "findings",
        property_id=property_id,
        severity_floor=severity_floor,
        limit=limit,
        ack_status=ack_status,
    )


if __name__ == "__main__":
    main()
