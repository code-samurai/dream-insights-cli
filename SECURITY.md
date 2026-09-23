# Security

## Credential storage

`di` stores your API key in plain text at `~/.dream-insights/config.yaml`.
The file is created with `0600` permissions (owner read/write only) and the
parent directory with `0700`. No other user on the same machine can read your key.

Prefer your OS keychain on shared machines and inject the key only for the
session:

```bash
export DREAM_INSIGHTS_API_KEY="$(keyring get dream-insights api_key)"
```

## Key classes (FOR ME vs FOR AGENT)

| Class | Prefix / mint | Use |
|-------|---------------|-----|
| **Personal (FOR ME)** | `di_user_…` from Discovery Settings → Your keys | You: CLI, personal scripts, Cloud Code/Desktop |
| **Machine reader (FOR AGENT)** | Minted Agent & integration reader | Hermes, fleet bots, coding-agent skills, fleet MCP |

- Do **not** put a personal key in a shared agent runtime or commit it to git.
- Do **not** share one machine-reader secret across unrelated agents.
- Never send `ADMIN_API_KEY`, Discovery session cookies, or tenant UUIDs in this public repo or in chat logs.

## API key hygiene

- **Never pass your API key as a CLI argument** — use `di auth login` (hidden prompt), not `di config set api_key <key>` (shell history / process list risk).
- Prefer environment variables for CI: `DREAM_INSIGHTS_API_KEY` or `DREAM_INSIGHTS_FLEET_API_KEY`.
- All requests use HTTPS. `api_url` must start with `https://`.
- Revoke unused keys in Discovery Settings (or ask ops to revoke a machine reader).

## Auth header

This CLI sends `X-API-Key: <key>` by default. Bearer is also accepted by the
fleet HTTP surface; prefer `X-API-Key` for consistency with MCP clients.

## Reporting a vulnerability

Email **security@leadshook.com** with a description. Do not open a public
GitHub issue for security vulnerabilities.
