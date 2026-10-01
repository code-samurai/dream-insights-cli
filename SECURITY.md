# Security

## Credential storage

`di` stores your API key in plain text at `~/.dream-insights/config.yaml`.
The file is created with `0600` permissions (owner read/write only) and the
parent directory with `0700`. No other user on the same machine can read your key.

Prefer your OS keychain on shared machines and inject the key only for the
session:

```bash
export DREAM_INSIGHTS_API_KEY="$(keyring get dream-insights api_key)"
# authoring (FOR ME):
export DREAM_INSIGHTS_AUTHORING_API_KEY="$(keyring get dream-insights authoring_api_key)"
```

## Key classes (FOR ME vs FOR AGENT)

| Class | Prefix / mint | Use |
|-------|---------------|-----|
| **Personal (FOR ME)** | `di_user_…` from Discovery Settings → Connect apps → FOR ME | You: CLI, personal scripts, Cloud Code/Desktop, **ontology authoring** (`/mcp/author/`, `di author …`) |
| **Machine reader (FOR AGENT)** | Minted Agent & integration reader | Hermes, fleet bots, coding-agent **read** skills, **fleet MCP** only |

- Do **not** put a personal key in a shared agent runtime or commit it to git.
- Do **not** share one machine-reader secret across unrelated agents.
- Do **not** document or treat fleet / machine-reader keys as able to author. Authoring refuses `di_fleet_…` and does not read `DREAM_INSIGHTS_FLEET_API_KEY`.
- Never send real `ADMIN_API_KEY` values, Discovery session cookies, or tenant UUIDs in this public repo or in chat logs. Placeholders only (`di_user_YOUR_PERSONAL_KEY`).

## API key hygiene

- **Never pass your API key as a CLI argument** — use `di auth login` (hidden prompt), or env vars for authoring (`DREAM_INSIGHTS_AUTHORING_API_KEY`). Avoid `di config set api_key <key>` (shell history / process list risk). Prefer `--api-key` only when your shell will not retain history.
- Prefer environment variables for CI: `DREAM_INSIGHTS_API_KEY` or `DREAM_INSIGHTS_FLEET_API_KEY` for reads; `DREAM_INSIGHTS_AUTHORING_API_KEY` for writes.
- All requests use HTTPS. `api_url` must start with `https://`.
- Revoke unused keys in Discovery Settings (or ask ops to revoke a machine reader).

## Auth headers

| Surface | Preferred header |
|---------|------------------|
| Fleet HTTP / fleet MCP | `X-API-Key: <key>` |
| Authoring HTTP / authoring MCP | `Authorization: Bearer <key>` or `X-API-Key: <key>` |

## Reporting a vulnerability

Email **security@leadshook.com** with a description. Do not open a public
GitHub issue for security vulnerabilities.
