# MCP Reference — authoring MCP (FOR ME)

**Endpoint:** `https://t.leadshook.com/mcp/author/` (trailing slash)
**Auth:** `Authorization: Bearer di_user_YOUR_PERSONAL_KEY` or `X-API-Key: di_user_YOUR_PERSONAL_KEY`
**Key class:** Personal (**FOR ME**) or admin — fleet / machine readers are refused

Fleet MCP (`/mcp/fleet/`) does **not** expose these tools.

---

## Tools

| Tool | Purpose |
|------|---------|
| `import_ontology` | `property_id`, `ontology_id`, `document` → import onto draft (no publish) |
| `write_ontology` | `property_id`, `document` → create or full-replace draft (no publish) |
| `publish_ontology` | `property_id`, optional `allow_breaking` (admin only) → publish; materialise follows |
| `check_ontology` | `property_id` → read-only draft quality report (no grade, no write) |
| `list_competency_questions` | `property_id` → current questions |
| `write_competency_question` | `property_id`, `text`, optional path fields and `question_id` → create or revise, not confirm |
| `confirm_competency_question` | `property_id`, `question_id` → person-confirm the current revision |

`document` is an `ActivatedOntology` object. Full-replace. Identity envelope fields are ignored.

## Client config

```bash
di mcp-config --client claude-code --surface author
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

| Env | Value |
|-----|--------|
| `DREAM_INSIGHTS_AUTHORING_MCP_URL` | `https://t.leadshook.com/mcp/author/` |
| `DREAM_INSIGHTS_AUTHORING_API_KEY` | `di_user_YOUR_PERSONAL_KEY` |
