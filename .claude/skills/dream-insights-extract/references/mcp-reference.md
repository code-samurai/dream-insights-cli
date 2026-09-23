# MCP Reference — fleet MCP (reads)

**Endpoint:** `https://t.leadshook.com/mcp/fleet/` (trailing slash)
**Auth:** `X-API-Key: <MACHINE_READER_API_KEY>`
**Transport:** Streamable HTTP; JSON responses
**Key class:** Machine reader (**FOR AGENT**) only — personal `di_user_` keys are refused

Ontology authoring is a **different** MCP: `https://t.leadshook.com/mcp/author/`
(see skill `dream-insights-author`). Fleet MCP does not register
`import_ontology`, `write_ontology`, or `publish_ontology`. Machine readers cannot author.

---

## Client config placeholders

Claude Code / Cursor:

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

Env:

| Name | Value |
|------|--------|
| `DREAM_INSIGHTS_MCP_URL` | `https://t.leadshook.com/mcp/fleet/` |
| `DREAM_INSIGHTS_FLEET_API_KEY` | machine reader |

---

## Extract tools

| Tool | Purpose |
|------|---------|
| `get_ontology` | Live ontology for `property_id` |
| `list_events` | Paginated events (`limit`, `offset`, `event_name`, `page_domain`) |
| `get_event` | One event (`event_id`) with properties + context |
| `list_entities` | Instances of `entity_type` |
| `get_entity` | One instance (`entity_type`, `entity_id`) |
| `get_person_timeline` | Timeline for `person_id` |
| `list_transitions` | Transitions (`person_id`, `from_type`, `to_type`) |

## Query helpers

| Tool | Purpose |
|------|---------|
| `search_similar_persons` | Neighbors for `person_id` |
| `search_similar_cohorts` | Neighbors for `cohort_id` |
| `search_similar_pathways` | Near-text on `channels` |
| `search_semantic` | `collection` + `query` |

## Overlays

| Tool | Purpose |
|------|---------|
| `get_roas` | Channel ROAS |
| `get_campaign_roas` | Campaign ROAS |
| `get_findings` | Findings feed |

Arguments match HTTP query/path params, including `property_id`.
Empty `rows` / `items` / `results` is success. Out-of-scope property → error.
