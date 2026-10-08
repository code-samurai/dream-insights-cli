# dream-insights-cli

Terminal and agent access to [Dream Insights](https://t.leadshook.com).

Two surfaces, same Connect-apps key model as Discovery:

| Surface | What it does | Key class | Endpoint |
|---------|--------------|-----------|----------|
| **Fleet reads** | Live ontology, events, entities, timelines, semantic neighbors | Personal `di_user_…` **or** machine reader | HTTP + `/mcp/fleet/` |
| **Ontology authoring** | Import / draft / publish an `ActivatedOntology` from outside Discovery | **FOR ME** personal `di_user_…` (or admin) | HTTP `/authoring/…` + `/mcp/author/` |

Dream Insights returns **data**. **You** (or your agent) build the insight. No free-form SQL. No narrative minting. Fleet MCP and machine readers stay **read-only** — they cannot author.

| | |
|---|---|
| Host | `https://t.leadshook.com` |
| Fleet auth | `X-API-Key` |
| Authoring auth | `Authorization: Bearer` or `X-API-Key` |
| Fleet OpenAPI | `GET /api/v1/fleet/openapi.json` |
| Fleet MCP | `https://t.leadshook.com/mcp/fleet/` |
| Authoring MCP | `https://t.leadshook.com/mcp/author/` (trailing slash) |
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

Mint keys in **Discovery Settings → Connect apps**.

| Audience | Key | Where to use |
|----------|-----|--------------|
| **FOR ME** | Personal `di_user_…` | Your laptop CLI, personal scripts, Cloud Code / Desktop as *you*, **ontology authoring** (`/mcp/author/`, `di author …`) |
| **FOR AGENT** | Machine reader | Hermes, Cursor/Claude skills for **reads**, fleet bots, **fleet MCP** (`/mcp/fleet/`) |

- Fleet MCP (`/mcp/fleet/`) **refuses** personal `di_user_` keys — use a machine reader.
- Authoring MCP (`/mcp/author/`) **refuses** fleet / machine-reader keys — use a FOR ME personal key.
- Authoring tools (`import_ontology`, `write_ontology`, `publish_ontology`, `check_ontology`, `list_competency_questions`, `write_competency_question`, `confirm_competency_question`) are **not** registered on fleet MCP.
- This CLI accepts either key class for **fleet HTTP reads**. Authoring commands refuse `di_fleet_…` keys and do not read `DREAM_INSIGHTS_FLEET_API_KEY`.
- Never commit keys. Never put a personal key in a shared agent runtime. See [SECURITY.md](SECURITY.md).

## Quick start — fleet reads

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

## Quick start — ontology authoring (FOR ME)

Build an `ActivatedOntology` outside Discovery, then push: **draft → publish → materialise**. Materialise stays on publish (no separate CLI step).

```bash
export DREAM_INSIGHTS_BASE_URL=https://t.leadshook.com
export DREAM_INSIGHTS_AUTHORING_API_KEY=di_user_YOUR_PERSONAL_KEY
# or: di auth login  (personal key; authoring ignores fleet env keys)

# Create or full-replace the property draft (MCP: write_ontology)
di author draft \
  --property-id <property-uuid> \
  --file examples/activated-ontology.outside-in.yaml

# Or import onto an existing opened ontology version (MCP: import_ontology)
di author import \
  --property-id <property-uuid> \
  --ontology-id <version-uuid> \
  --file examples/activated-ontology.outside-in.yaml

# Publish when the draft differs from live (MCP: publish_ontology)
di author publish --property-id <property-uuid>

# Read-only quality report (MCP: check_ontology). No grade.
di author check --property <property-uuid>
```

- `--auth bearer` (default) or `--auth x-api-key`.
- Import and draft **full-replace** the property draft (no merge). Prefer a synthetic property for experiments.
- `allow_breaking` on publish is **admin-key only**.
- Empty documents against a real customer property are dangerous — do not do that.

Example document: [`examples/activated-ontology.outside-in.yaml`](examples/activated-ontology.outside-in.yaml) (JSON twin beside it).

Design before you push: skill [`dream-insights-ontology-design`](.claude/skills/dream-insights-ontology-design/SKILL.md) covers the owner interview, consumer questions, identity and links, and one good plus two bad worked examples in [`examples/ontology-design/`](examples/ontology-design/).

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
di mcp-config --client claude-code --surface fleet
di mcp-config --client claude-code --surface author
di mcp-config --client cursor --surface fleet
di mcp-config --client cursor --surface author
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
di ledger-metrics --property-id <property-uuid> --date-from 2026-01-01 --date-to 2026-01-31
```

Empty `items` / `results` lists are **success** — do not invent rows.

### Ontology authoring

```bash
di author draft --property-id <property-uuid> --file path/to/ontology.yaml
di author import --property-id <property-uuid> --ontology-id <version-uuid> --file path/to/ontology.yaml
di author publish --property-id <property-uuid>
di author check --property <property-uuid>
di author cq list --property <property-uuid>
di author cq write --property <property-uuid> --text "How many leads convert?" --entity lead --status new --time-window 7d
di author cq confirm --property <property-uuid> --question-id <question-uuid>
```

`di author check` returns `breaks_extraction`, `worth_fixing`, `questions`, and `schema_diff`. It does not write and it has no grade. Worth-fixing findings do not fail publish.

Revising a question (`--question-id`) sends only the fields you pass; the server keeps the rest. Use `--critical` / `--not-critical` to change the key-question flag, and `""` to clear a path field:

```bash
di author cq write --property <property-uuid> --question-id <question-uuid> --status paid
```

**Safe saves.** `di author draft` and `di author import` take `--expected-updated-at <draft updated_at>`. If someone saved the draft after you read it, the server refuses with 409 ("This draft changed after you opened it…") instead of overwriting their work. Without the flag, saves behave as before.

**Questions in a file.** A `questions` (or `competency_questions`) list next to the ontology in an import file is added to Quality; the response `notice` (printed on stderr) says how many.

**Failures.** Refusals print the server's plain sentence first, then `Next:`, `Fix: <kind> <target>`, the draft to work in (`Draft:`), whether to retry, and store detail last under `Details:`. A 422 is a refusal with a reason (for example a name clash: `Fix: rename_entity step_2`), not an "API error".

CLI ↔ MCP verbs:

| CLI | MCP tool |
|-----|----------|
| `di author import` | `import_ontology` |
| `di author draft` | `write_ontology` |
| `di author publish` | `publish_ontology` |
| `di author check` | `check_ontology` |
| `di author cq list` | `list_competency_questions` |
| `di author cq write` | `write_competency_question` |
| `di author cq confirm` | `confirm_competency_question` |
| `di ledger-metrics` | `get_ledger_metrics` |

## Claude Code / Cursor — MCP JSON placeholders

### Fleet (FOR AGENT — reads only)

```bash
di mcp-config --client claude-code --surface fleet
di mcp-config --client cursor --surface fleet
```

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

### Authoring (FOR ME — writes)

```bash
di mcp-config --client claude-code --surface author
di mcp-config --client cursor --surface author
```

```json
{
  "mcpServers": {
    "dream-insights-authoring": {
      "url": "https://t.leadshook.com/mcp/author/",
      "headers": {
        "Authorization": "Bearer di_user_YOUR_PERSONAL_KEY"
      }
    }
  }
}
```

`X-API-Key: di_user_YOUR_PERSONAL_KEY` is also accepted on authoring. Trailing slash on the URL is required.

Claude Code: merge into `~/.claude/claude.json` (or project `.mcp.json`).
Cursor: MCP settings JSON (same shape). You may register **both** servers when an agent needs reads and (as you) writes.

Env vars:

| Variable | Value |
|----------|--------|
| `DREAM_INSIGHTS_BASE_URL` | `https://t.leadshook.com` |
| `DREAM_INSIGHTS_API_KEY` | Personal or machine reader (fleet HTTP / CLI reads) |
| `DREAM_INSIGHTS_FLEET_API_KEY` | Machine reader for fleet agents (**not** used by authoring) |
| `DREAM_INSIGHTS_AUTHORING_API_KEY` | Personal `di_user_…` for authoring CLI |
| `DREAM_INSIGHTS_MCP_URL` | `https://t.leadshook.com/mcp/fleet/` |
| `DREAM_INSIGHTS_AUTHORING_MCP_URL` | `https://t.leadshook.com/mcp/author/` |

## Agent skill install

This repo ships Claude Code skills under:

```
.claude/skills/dream-insights-extract/     # fleet reads
.claude/skills/dream-insights-author/      # ontology authoring (FOR ME)
.claude/skills/dream-insights-ontology-design/  # what to model: owner interview, links, examples
```

```text
https://github.com/code-samurai/dream-insights-cli/tree/main/.claude/skills/dream-insights-extract
https://github.com/code-samurai/dream-insights-cli/tree/main/.claude/skills/dream-insights-author
https://github.com/code-samurai/dream-insights-cli/tree/main/.claude/skills/dream-insights-ontology-design
```

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
