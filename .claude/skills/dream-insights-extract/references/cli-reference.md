# CLI Reference — di (dream-insights-cli)

**Install:** `pip install "git+https://github.com/code-samurai/dream-insights-cli.git"` (Python 3.10+)
**Config:** `~/.dream-insights/config.yaml` (mode 0600)
**Host:** `https://t.leadshook.com`
**Auth:** `X-API-Key` (personal `di_user_…` or machine reader)
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
di mcp-config --client claude-code|cursor|generic
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
```

Empty collections are success.
