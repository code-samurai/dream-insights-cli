---
name: dream-insights-author
description: >
  Build a Dream Insights ActivatedOntology outside Discovery and push it with
  the authoring MCP or CLI (import, draft write, publish). Use for Claude Code
  or Codex acting as the human (FOR ME). Do not use a fleet machine-reader key
  or /mcp/fleet/ for these writes.
compatibility:
  cli: pip install "git+https://github.com/code-samurai/dream-insights-cli.git"
  mcp: https://t.leadshook.com/mcp/author/
  example: examples/activated-ontology.outside-in.yaml
---

# dream-insights-author

Push an `ActivatedOntology` **outside → in**. Same document Discovery stores.
Path: **draft → publish → materialise**. Materialise stays on publish.

Fleet reads stay on skill `dream-insights-extract` and `/mcp/fleet/`.
A machine reader **cannot** author.

## Load

- Example: `examples/activated-ontology.outside-in.yaml` (JSON twin beside it)
- Document type: `ActivatedOntology` (do not invent another schema)
- `name` / `description` are draft labels. Server owns identity fields
  (`ontology_id`, `version`, `status`, timestamps, `created_by`, `changelog`).
  `phase_summaries` are discarded.

Import and draft PUT **full-replace** the property draft (no merge).
Do not send an empty document against a real customer property. Prefer a
synthetic property for experiments.

## Authenticate

1. Personal key from Discovery **Settings → Connect apps → FOR ME**. Prefix `di_user_`.
2. MCP URL `https://t.leadshook.com/mcp/author/` (trailing slash required).
3. Header `Authorization: Bearer di_user_YOUR_PERSONAL_KEY` or `X-API-Key: di_user_YOUR_PERSONAL_KEY`.
4. Admin key is the operator alternative. `allow_breaking` is admin-only.

Refuse `di_fleet_…` and `DREAM_INSIGHTS_FLEET_API_KEY`. Those keys read
`/mcp/fleet/` only. Fleet MCP does not register authoring tools.

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

Env: `DREAM_INSIGHTS_AUTHORING_MCP_URL`, `DREAM_INSIGHTS_AUTHORING_API_KEY`.

## Push

| Step | MCP tool | CLI | Notes |
|------|----------|-----|-------|
| 1a | `import_ontology` | `di author import` | Needs existing ontology version id; writes draft; does not publish |
| 1b | `write_ontology` | `di author draft` | Creates or full-replaces draft; does not publish |
| 2 | `publish_ontology` | `di author publish` | Publish saga; materialise follows |

```bash
export DREAM_INSIGHTS_BASE_URL=https://t.leadshook.com
export DREAM_INSIGHTS_AUTHORING_API_KEY=di_user_YOUR_PERSONAL_KEY

di author draft --property-id <property-uuid> --file examples/activated-ontology.outside-in.yaml
di author publish --property-id <property-uuid>
```

A draft that matches live, an empty new draft, or a publish already in flight
returns 409. Personal keys cannot set `allow_breaking`.

## Privacy

Placeholders only. No production property UUIDs, no real keys, no internal hosts.

## References

- [Authoring MCP](references/mcp-reference.md)
- [Authoring CLI](references/cli-reference.md)
