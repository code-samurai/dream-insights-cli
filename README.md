# dream-insights-cli

Terminal and agent access to [Dream Insights](https://t.leadshook.com) **fleet standing reads**.

Dream Insights returns **data** (ontology, events, entities, timelines, semantic neighbors).
**You** (or your agent) build the insight. No free-form SQL. No narrative minting.

| | |
|---|---|
| Host | `https://t.leadshook.com` |
| Auth | `X-API-Key` |
| OpenAPI | `GET /api/v1/fleet/openapi.json` |
| Fleet MCP | `https://t.leadshook.com/mcp/fleet/` |
| CLI | `di` |

## Install

Requires Python 3.10+.

```bash
pip install "git+https://github.com/code-samurai/dream-insights-cli.git"
```

Editable checkout:

```bash
git clone https://github.com/code-samurai/dream-insights-cli.git
cd dream-insights-cli
pip install -e ".[dev]"
```

## FOR ME vs FOR AGENT keys

Mint keys in **Discovery Settings** (Connect apps).

| Audience | Key | Where to use |
|----------|-----|--------------|
| **FOR ME** | Personal `di_user_…` | Your laptop CLI, personal scripts, Cloud Code / Desktop as *you* |
| **FOR AGENT** | Machine reader | Hermes, Cursor/Claude skills, fleet bots, **fleet MCP** |

- Fleet MCP (`/mcp/fleet/`) **refuses** personal `di_user_` keys — use a machine reader.
- This CLI accepts **either** key class over HTTP with `X-API-Key`.
- Never commit keys. Never put a personal key in a shared agent runtime. See [SECURITY.md](SECURITY.md).

## Quick start

```bash
di auth login
# paste di_user_… (FOR ME) or a machine reader (FOR AGENT)
# stored at ~/.dream-insights/config.yaml (mode 0600)

di config set default_property_id <property-uuid>
di ontology
di events --limit 20
di entities --entity-type lead --limit 20
di semantic --collection EntityProfile --query "quiz lead"
```

All query commands default to `--format json` (agent-friendly). Use `--format table` for humans.

## Commands

### Auth & config

```bash
di auth login
di auth logout
di auth status
di config show
di config set api_url https://t.leadshook.com
di config set default_property_id <property-uuid>
di health
di mcp-config --client claude-code
di mcp-config --client cursor
```

### Extract reads

```bash
di ontology --property-id <property-uuid>
di events --property-id <property-uuid> [--limit N] [--event-name NAME]
di event --property-id <property-uuid> --event-id <event-uuid>
di entities --property-id <property-uuid> --entity-type lead [--status STATUS]
di entity --property-id <property-uuid> --entity-type lead --entity-id <entity-uuid>
di timeline --property-id <property-uuid> --person-id <person-uuid>
di transitions --property-id <property-uuid>
```

### Query helpers

```bash
di semantic --property-id <property-uuid> --collection EntityProfile --query "quiz lead"
di similar-persons --property-id <property-uuid> --person-id <person-uuid>
di similar-cohorts --property-id <property-uuid> --cohort-id <cohort-uuid>
di similar-pathways --property-id <property-uuid> --channels organic,paid
```

### Overlays (optional)

```bash
di roas --property-id <property-uuid> --date-from 2026-01-01 --date-to 2026-01-31
di campaign-roas --property-id <property-uuid> --date-from 2026-01-01 --date-to 2026-01-31
di findings --property-id <property-uuid>
```

Empty `items` / `results` lists are **success** — do not invent rows.

## Claude Code / Cursor — MCP JSON placeholders

Fleet MCP URL (machine reader only):

```bash
di mcp-config --client claude-code
di mcp-config --client cursor
```

Paste-ready shape (replace the placeholder; do not commit real keys):

```json
{
  "mcpServers": {
    "dream-insights": {
      "url": "https://t.leadshook.com/mcp/fleet/",
      "headers": {
        "X-API-Key": "<MACHINE_READER_API_KEY>"
      }
    }
  }
}
```

Claude Code: merge into `~/.claude/claude.json` (or project `.mcp.json`).
Cursor: MCP settings JSON (same shape).

Env vars agents often use:

| Variable | Value |
|----------|--------|
| `DREAM_INSIGHTS_BASE_URL` | `https://t.leadshook.com` |
| `DREAM_INSIGHTS_API_KEY` / `DREAM_INSIGHTS_FLEET_API_KEY` | Your key (prefer machine reader for agents) |
| `DREAM_INSIGHTS_MCP_URL` | `https://t.leadshook.com/mcp/fleet/` |

## Agent skill install

This repo ships a Claude Code skill under:

```
.claude/skills/dream-insights-extract/
```

Install from GitHub (Claude Code `/install` or skill sync — adjust to your tooling):

```text
https://github.com/code-samurai/dream-insights-cli/tree/main/.claude/skills/dream-insights-extract
```

Skill name: `dream-insights-extract`. References cover CLI, MCP, and REST.

## Configuration file

`~/.dream-insights/config.yaml` (directory `0700`, file `0600`):

```yaml
api_url: https://t.leadshook.com
api_key: <redacted>
default_property_id: <property-uuid>
output_format: json
```

## Development

```bash
pip install -e ".[dev]"
pytest tests/ -v
```

Unit tests mock HTTP with `respx`. No live calls. No real secrets in fixtures.

## Privacy

This public repo uses **placeholders only** — no production property UUIDs, no real API keys, no internal docs.

## License

MIT
