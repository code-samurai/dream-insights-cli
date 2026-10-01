# CLI Reference — di author (FOR ME)

**Host:** `https://t.leadshook.com`
**Credential:** `DREAM_INSIGHTS_AUTHORING_API_KEY` (preferred) or stored personal key from `di auth login`
**Does not read:** `DREAM_INSIGHTS_FLEET_API_KEY`
**Refuses:** `di_fleet_…` secrets

```bash
di author draft --property-id <property-uuid> --file examples/activated-ontology.outside-in.yaml
di author import --property-id <property-uuid> --ontology-id <version-uuid> --file examples/activated-ontology.outside-in.yaml
di author publish --property-id <property-uuid>
```

Options shared by all three:

| Option | Default | Meaning |
|--------|---------|---------|
| `--auth` | `bearer` | `bearer` or `x-api-key` |
| `--api-key` | env / config | Override; prefer env |
| `--allow-breaking` | off | Publish only; admin key required |

HTTP peers:

| CLI | Method + path |
|-----|----------------|
| `import` | `POST /authoring/ontologies/{property_id}/{ontology_id}/import` |
| `draft` | `PUT /authoring/ontologies/{property_id}/draft` |
| `publish` | `POST /authoring/ontologies/{property_id}/publish` |

MCP peers: `import_ontology`, `write_ontology`, `publish_ontology`.
