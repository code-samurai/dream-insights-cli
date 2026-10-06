# REST Reference — fleet standing reads

**Base:** `https://t.leadshook.com`
**Auth:** `X-API-Key: <key>` (or `Authorization: Bearer <key>`)
**OpenAPI:** `GET /api/v1/fleet/openapi.json`
**Docs UI:** `GET /api/v1/fleet/docs`
**Health:** `GET /health` (no key)

Path grain is always `property_id`. Replace placeholders; never commit real UUIDs or keys.

---

## Extract

```
GET /api/v1/properties/{property_id}/ontology/live
GET /api/v1/properties/{property_id}/events?limit=50&offset=0&event_name=&page_domain=
GET /api/v1/properties/{property_id}/events/{event_id}
GET /api/v1/properties/{property_id}/entities/{entity_type}?person_id=&status=&limit=50&offset=0
GET /api/v1/properties/{property_id}/entities/{entity_type}/{entity_id}
GET /api/v1/properties/{property_id}/persons/{person_id}/timeline
GET /api/v1/properties/{property_id}/transitions?person_id=&from_type=&to_type=&limit=50&offset=0
```

Event **list** rows omit `properties` and `context`. Event **detail** includes both.

## Query helpers

```
GET /api/v1/properties/{property_id}/search/similar-persons?person_id=<uuid>&limit=10
GET /api/v1/properties/{property_id}/search/similar-cohorts?cohort_id=<uuid>&limit=10
GET /api/v1/properties/{property_id}/search/similar-pathways?channels=organic,paid&limit=10
GET /api/v1/properties/{property_id}/search/semantic?collection=EntityProfile&query=quiz+lead&limit=10
```

`collection` allow-list: `PersonProfile`, `CohortProfile`, `PathwayPattern`, `EntityProfile`.

## Overlays

```
GET /api/v1/properties/{property_id}/roas?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD&model_type=linear
GET /api/v1/properties/{property_id}/campaign-roas?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
GET /api/v1/properties/{property_id}/findings?severity_floor=notable&limit=100
GET /api/v1/properties/{property_id}/ledger/metrics?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD
```

## Example

```bash
HOST=https://t.leadshook.com
PID=<property-uuid>
# KEY from your secret store — do not commit

curl -sS -H "X-API-Key: $KEY" \
  "$HOST/api/v1/properties/$PID/ontology/live"
```

Empty `items` / `results` is HTTP 200 success.

---

## Ontology authoring (FOR ME — not fleet OpenAPI)

Authoring is separate from fleet standing reads. Prefer MCP `/mcp/author/` or `di author`.

```
POST /authoring/ontologies/{property_id}/{ontology_id}/import
PUT  /authoring/ontologies/{property_id}/draft
POST /authoring/ontologies/{property_id}/publish
```

Auth: personal `di_user_YOUR_PERSONAL_KEY` via `Authorization: Bearer` or `X-API-Key`.
Fleet machine readers are refused. See skill `dream-insights-author`.
