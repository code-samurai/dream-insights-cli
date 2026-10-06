# CLI Reference — di (dream-insights-cli)

**Install:** `pip install "git+https://github.com/code-samurai/dream-insights-cli.git"` (Python 3.10+)
**Config:** `~/.dream-insights/config.yaml` (mode 0600)
**Host:** `https://t.leadshook.com`
**Auth (reads):** `X-API-Key` (personal `di_user_…` or machine reader)
**Auth (authoring):** `Authorization: Bearer` or `X-API-Key` (FOR ME personal key; see `di author`)
**Output:** `json` (default), `table`, `text`

---

## Auth & config

```bash
di auth login
di auth logout
di auth status
di config show
di config set api_url https://t.leadshook.com
di config set default_property_id <property-uuid>
di config set output_format json
di health
di mcp-config --client claude-code|cursor|generic --surface fleet|author
```

Set `api_key` via `di auth login` — not `config set` (shell history risk).

---

## Extract

```bash
di ontology [--property-id UUID]
di events [--property-id UUID] [--limit N] [--offset N] [--event-name NAME] [--page-domain DOMAIN]
di event --event-id UUID [--property-id UUID]
di entities --entity-type TYPE [--property-id UUID] [--person-id UUID] [--status S] [--limit N]
di entity --entity-type TYPE --entity-id UUID [--property-id UUID]
di timeline --person-id UUID [--property-id UUID]
di transitions [--property-id UUID] [--person-id UUID] [--from-type T] [--to-type T] [--limit N]
```

---

## Query helpers

```bash
di semantic --collection EntityProfile|PersonProfile|CohortProfile|PathwayPattern --query TEXT [--limit N]
di similar-persons --person-id UUID [--limit N]
di similar-cohorts --cohort-id UUID [--limit N]
di similar-pathways --channels organic,paid [--limit N]
```

---

## Overlays

```bash
di roas --date-from YYYY-MM-DD --date-to YYYY-MM-DD [--model-type linear] [--channel C]
di campaign-roas --date-from YYYY-MM-DD --date-to YYYY-MM-DD [--platform P]
di findings [--severity-floor notable] [--limit N] [--ack-status unread]
di ledger-metrics --date-from YYYY-MM-DD --date-to YYYY-MM-DD [--product dream-insights|weezdom|hermes|cloudflare] [--ontology-version ID] [--field alias]
```

Empty collections are success.

---

## Ontology authoring (FOR ME)

```bash
di author draft --property-id UUID --file path/to/ontology.yaml|json
di author import --property-id UUID --ontology-id UUID --file path/to/ontology.yaml|json
di author publish --property-id UUID [--allow-breaking]
```

Env: `DREAM_INSIGHTS_AUTHORING_API_KEY=di_user_YOUR_PERSONAL_KEY`.
Fleet keys (`di_fleet_…`, `DREAM_INSIGHTS_FLEET_API_KEY`) cannot author.
Materialise follows publish — no separate CLI verb.
