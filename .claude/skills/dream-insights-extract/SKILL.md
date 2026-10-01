---
name: dream-insights-extract
description: Use when extracting Dream Insights fleet data — live ontology, events, entities, person timelines, transitions, and semantic/similar search. Covers CLI (di), fleet MCP tools, and REST with X-API-Key. Data only; consumer builds insight. For ontology writes use dream-insights-author instead.
compatibility:
  cli: pip install "git+https://github.com/code-samurai/dream-insights-cli.git"
  mcp: https://t.leadshook.com/mcp/fleet/
  rest: X-API-Key on https://t.leadshook.com
---

# dream-insights-extract

Enable agents to **read** Dream Insights standing fleet data and reason locally.
DI does not mint a narrative and does not accept free-form SQL.

Ontology **authoring** (import / draft / publish) is a different skill and MCP:
`dream-insights-author` → `https://t.leadshook.com/mcp/author/`. Fleet keys cannot author.

## Choose your access path

| Path | Best for | Key class |
|------|----------|-----------|
| **CLI** (`di`) | Local shell, scripts | Personal `di_user_…` **or** machine reader |
| **MCP** (`/mcp/fleet/`) | Claude Code, Cursor, Hermes | **Machine reader only** |
| **REST** (HTTP GET) | Any runtime | Personal or machine reader |

## Setup

### CLI

```bash
pip install "git+https://github.com/code-samurai/dream-insights-cli.git"
di auth login
di config set default_property_id <property-uuid>
di ontology --format json
```

Config: `~/.dream-insights/config.yaml` (mode 0600).

### MCP (FOR AGENT)

```json
{
  "mcpServers": {
    "dream-insights": {
      "url": "https://t.leadshook.com/mcp/fleet/",
      "headers": { "X-API-Key": "<MACHINE_READER_API_KEY>" }
    }
  }
}
```

Personal `di_user_` keys are **refused** by fleet MCP.
Fleet MCP does **not** expose `import_ontology`, `write_ontology`, or `publish_ontology`.

### REST

```
Base: https://t.leadshook.com
Header: X-API-Key: <key>
OpenAPI: GET /api/v1/fleet/openapi.json
```

## Extract path (always this order)

1. `get_ontology` / `di ontology` — entity types and statuses
2. `list_events` / `list_entities` / `list_transitions` — rows that exist
3. `get_event` / `get_entity` / `get_person_timeline` — detail when needed
4. Optional: `search_semantic`, `search_similar_*`
5. Reason locally. Write the insight in the consumer.

Empty `items` / `results` is success. **Do not invent rows.**

## CLI cheat sheet

```bash
di ontology --property-id <property-uuid>
di events --property-id <property-uuid> --limit 50
di event --property-id <property-uuid> --event-id <event-uuid>
di entities --property-id <property-uuid> --entity-type lead
di entity --property-id <property-uuid> --entity-type lead --entity-id <entity-uuid>
di timeline --property-id <property-uuid> --person-id <person-uuid>
di transitions --property-id <property-uuid>
di semantic --property-id <property-uuid> --collection EntityProfile --query "quiz lead"
```

## MCP tools

Extract: `get_ontology`, `list_events`, `get_event`, `list_entities`, `get_entity`,
`get_person_timeline`, `list_transitions`.

Query helpers: `search_similar_persons`, `search_similar_cohorts`,
`search_similar_pathways`, `search_semantic`.

Overlays: `get_roas`, `get_campaign_roas`, `get_findings`.

All take `property_id`. Tool JSON matches the HTTP body.

## Privacy

Placeholders only in prompts and commits. No production UUIDs, no real keys.

## References

- [CLI reference](references/cli-reference.md)
- [MCP reference](references/mcp-reference.md)
- [REST reference](references/rest-reference.md)
