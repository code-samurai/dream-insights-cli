---
name: dream-insights-ontology-design
description: >-
  Use before writing or changing a Dream Insights ActivatedOntology from
  outside the app (authoring MCP /mcp/author/ or `di author`). Interview the
  owner in plain business language, write down who reads the data and what
  they will ask, ship a small ontology that publishes, materialises and links
  records, then improve it. Push mechanics live in dream-insights-author.
compatibility:
  cli: pip install "git+https://github.com/code-samurai/dream-insights-cli.git"
  mcp: https://t.leadshook.com/mcp/author/
  examples: examples/ontology-design/
---
# Dream Insights ontology design (outside agents)

This skill covers *what to model*. To *push* the result, use [`dream-insights-author`](../dream-insights-author/SKILL.md) (MCP/CLI calls and keys).
Part 1 is a product-neutral spine. Part 2 covers Dream Insights only.

Pass or fail always comes from the platform. Run `check_ontology` / `di author check`, then `publish_ontology`. Only `breaks_extraction` findings block. This skill never grades, never adds a checker and never overrides a finding.

The codes and examples below are kept in step with the platform by a contract test in the Dream Insights source repo. If the platform and this file disagree, the platform wins.

---

## PART 1 — Common spine

### 1. Talk to the owner first (plain language, no jargon)

Most owners have never heard the word ontology. Never say "entity", "ontology", "relationship", "alias", "status" or "schema" to them.

Follow the same interview rules as the in-app Discovery wizard:

- elicit, then infer, then confirm
- one question per message
- structural questions only
- business language only
- never ask about auto-captured data (UTMs, device, geo, timestamps, page views)
- mirror the owner's own words
- phases: business, then lifecycle (entity and status first; a lead, a customer and a sale are different things), then dimensions, relationships, context, team and review
- at most 3 exchanges per elicit phase and 2 per inference phase. That limit is also your stop rule.

Interview script (questions 1–4 follow the wizard's business and lifecycle phases; 5–7 are **new** because the wizard does not ask them yet):

| # | Ask (plain words) | You learn |
|---|---|---|
| 1 | "What does this business sell, and to whom?" | business type, B2B/B2C |
| 2 | "How do people find you? Which ads, sources or partners send them?" | acquisition channels (UTMs are captured automatically, so don't model them) |
| 3 | "Walk me through what happens from someone's first visit to paying you. What happens after X?" | lifecycle steps, terminal outcomes |
| 4 | "When do you call someone a lead? A customer? What counts as a sale? Can one person buy more than once? Do refunds happen?" | where one thing ends and the next begins |
| 5 **new** | "Which decisions should this data help you make?" (spend, offer, fixing a step) | what the model must answer |
| 6 **new** | "Who will read these numbers, and what will they ask every week?" | the consumer questions (step 2) |
| 7 **new** | "Which systems send the data, and what ID do they share for one person?" (ask their developer if needed) | the identity key (Part 2) |

Don't ask why things happen, what the biggest problem is, or which factors matter. The data answers those questions, and the wizard rules them out. Question 6 is different: it asks what the owner will *ask the data*, not for an opinion about the business.

### 2. Write down the consumer questions before drafting

Fill in this table:

| who reads it | question in their words | decision it drives | critical? |
|---|---|---|---|

Keep it to 3–7 rows, with at most 2 marked critical. Store each row as a competency question (`write_competency_question` / `di author cq write` with a structured path), and ask a person to confirm it. Confirmed questions are what the Quality tab checks.

### 3. Play it back and get a yes

Send a short plain summary, for example: "People come from A, B and C. They take the quiz. Leaving their email makes them a lead. The first purchase makes them a customer. Each purchase is a sale with an amount and an offer. Refunds happen. You want to know …".

Draft only after a yes, or after 2 correction rounds. In the second case, list your open assumptions.

Save what the owner confirmed with the import, so the next person (or the in-app wizard) does not start from zero:

- The readers' questions go in as competency questions (step 2), one per row, confirmed by a person.
- The plain summary (purpose, who reads it, their questions) goes in the document's top-level `description`. Begin it with "Owner-confirmed summary (brought in from an AI tool, <date>):".

### 4. Translate answers into structure (you do this; the owner never sees these words)

| Owner said | You model |
|---|---|
| a thing that moves through steps (lead, order) | an object with statuses |
| several names for one step ("form submit", "new lead") | one step with aliases |
| "becomes", "leads to", "belongs to" | a link between two objects |
| something to slice by (offer, quiz outcome) | a dimension with a named source field |
| "the same person" across systems | the identity key, which must be on every event |

Split objects when they differ (a person is not a transaction). Don't add objects nobody described.

### 5. Working first, better later

Version 1 is the smallest model that answers the critical questions. That is usually 3–5 objects, every object linked, using real event names. Publish it, send or replay events, materialise, and check that records link. Only then improve it. This mirrors the product's "It works. N ways to make it better" card.

### 6. Fixed loop (never skip a step)

draft → write → **check** → fix every Breaks line → re-check → test against the consumer questions → publish (owner's go) → materialise → extract a sample → verify links → improve → repeat.

- Fix Breaks lines with the platform's `fix_hint`. Don't invent other fixes.
- Worth-fixing lines are a to-do list and never block.
- A consumer question is done when the platform marks it `answerable` **and** a sample extract returns linked records.

### 7. Report

Report: Breaks N · Worth fixing N · questions answerable / partial / not yet · linked-record share on the sample · open assumptions. No grade.

---

## PART 2 — Dream Insights

### What the platform enforces

| What | Where you see it |
|---|---|
| Blocking findings | `breaks_extraction` in `check_ontology` / `di author check`; publish answers 422 |
| Warning findings (never block) | `worth_fixing` in the same report |
| Question check (structured path only, no language parsing) | competency questions marked `answerable` / `partial` / `not yet`; only confirmed questions count |
| Report and publish | the check report and publish use the same evaluation, so a clean check means publish will not 422 on quality |
| Breaking-change gate | publish answers 409 (not a quality finding) when a change would break existing data; `allow_breaking` is admin-only |
| Document shape | `ActivatedOntology`; see [`examples/activated-ontology.outside-in.yaml`](../../../examples/activated-ontology.outside-in.yaml) |
| Ingest only accepts bound event names | `/collect` and `/events` answer 422 `unbound_event_name` |

### Platform codes this skill names

Blocking: `relationship_unknown_end`, `duplicate_relationship_key`, `alias_routes_to_multiple`, `duplicate_producer_name`, `binding_status_unknown`, `terminal_status_unknown`.

Warning: `entity_kind_as_status`, `entity_no_relationship`, `alias_case_or_punctuation`, `status_unobserved`, `dimension_missing_source`, `critical_question_regressed`.

### Events must be bound before they are sent

Ingest rejects an event name that is not bound on the **live** version (422 `unbound_event_name`). A batch that contains one is rejected whole. So:

- bind every event name the stack sends (canonical name or alias), publish, and only then send events;
- any event you leave out of the model is lost, not just left unanalysed;
- the property also needs an ingest permit (open host or an approved host), set in Discovery property settings. Without one, `/collect` and `/events` answer 404 `unknown_property` even when the ontology is live.

### Names: check them before you write

- **Universal-graph names.** If an object has the same name as one in the Dream Insights universal graph (for example `lead`, `quiz`, `order`, `refund`), DI merges the two. The universal fields come first, and its required fields apply: an event without that key is skipped (`required_attribute`). For example, `refund` requires an `amount` key on the refund event. Either send that key or choose a name that is not in the catalog.
- **No name that is another name plus a suffix.** Publish checks its search store by object name word by word (`_` splits words). So `sale` and `sale_refund` (or `order` and `order_item`) in one document fail publish after the stores are written, with an error like "sale type uuid count 2 != 1". Pick names that share no whole word with another object's name, such as `sale` and `refund_given`.

### Identity and join keys (the most common reason records don't link)

- DI groups an event by its `person_id`, or by its `anonymous_id` (a UUID) when `person_id` is null. The ontology has no key field. Lead, customer and sale link only when their events resolve to the **same** id.
- Anonymous pre-optin events (quiz, visit) join the person only when a `$identify` event carries **both** `person_id` and `anonymous_id`. That backfills `person_id` onto earlier anonymous events (asynchronously, so wait for it before materialising). Sending `person_id` on the lead event alone does not join the earlier quiz events.
- A link (transition) is written when a new target instance appears and the same person already has a source instance. Order matters: the source event must come first.
- A transition's `source` and `campaign_id` come from the UTMs on the **source** instance's first event. The lead→customer transition therefore carries the ad source. The customer→sale transition carries whatever the customer event had, which is often nothing for server-side events. Answer source → revenue by going through the lead.
- Link sales from an object that **always exists before checkout**, usually the lead (`lead → sale`, `has_many`). A sale often opens at `checkout_started`, before `customer_created` arrives, so a `customer → sale` link misses the first sale. In a test, a customer→sale link caught only 15 of 40 sales; lead→sale caught all 40.
- Check 3 people with `get_person_timeline`. If the quiz, lead and sale events don't share one person, fix the tracking (send `$identify` at optin). Don't try to fix it in the ontology.

### Edges (no unconnected objects)

- Put every object on at least one relationship. `entity_no_relationship` only warns, but an object with no links can't answer a funnel question.
- `transition_type` must be one of: converts_to, produces, triggers, closes_as, has_many, belongs_to, escalates_to. Each `from__to__type` key may appear only once.

### Statuses, aliases, funnel events

- A producer name routes to exactly one object.status. If you route it twice, publish breaks (`alias_routes_to_multiple`).
  - That means one purchase event can't both create the customer and the sale. Emit `customer_created`, or start with lead → sale.
  - A lead that "converted" is the lead→customer link, not a lead status bound to the purchase event.
- Put every other producer name for the same step in `event_status_bindings[].aliases`. Every binding status and every terminal status must be in `valid_statuses`.
- Set `terminal_statuses` explicitly. A terminal status closes the instance, and the person's next event for that object opens a new one:
  - repeat purchases need `sale.paid` to be terminal;
  - a refund modelled as a sale status would create a second, amount-less sale, so make refunds their own object.
- Map each funnel step (visitor → lead → customer → revenue) to one status or object.
- For dimensions, set `is_dimension: true` and `source_field` to the event property key. Don't recreate UTMs or other envelope fields as attributes: they are platform fields.
- Any other field is read from the event key that **equals its name**, and `source_field` is ignored. Name the field after the key the events send (`amount`, `offer_id`).

### DI consumer questions → structured path → extract

| Question | Competency-question path | Extract (fleet) |
|---|---|---|
| Which source/campaign brings leads that become revenue | entity `lead`, relationship_key `lead__sale__has_many` | lead UTMs joined by person to sale `amount`; `get_campaign_roas` |
| Where people drop between visitor, lead and customer | entity `lead`, relationship_key `quiz_session__lead__produces` | entity counts by type and status |
| Revenue per campaign/offer | entity `sale`, dimension `offer_id` | sale instances, `amount` by `offer_id` |
| Time from lead to purchase | relationship_key `lead__customer__converts_to` | transition `duration_hours` |
| Repeat purchase and refunds | entity `sale`, status `paid`; relationship_key `sale__refund_given__triggers` | sales per person; refund instances |

Today a question path holds one relationship, so a question that spans several steps needs one competency question per step.

What the fleet extract can return today (October 2026): a person's timeline lists their objects, statuses and links. The entity list only accepts types from the universal graph, so `entities/sale` answers 404. Listed transitions carry no `person_id`, `source` or `campaign_id`. For money by source, check the answer against raw events too, and report the gap rather than reshaping the model to work around it. Fleet reads use skill [`dream-insights-extract`](../dream-insights-extract/SKILL.md).

### Worked good example — LeadsHook quiz funnel

File: [`examples/ontology-design/good-leadshook-quiz.json`](../../../examples/ontology-design/good-leadshook-quiz.json). Expected findings: [`good-leadshook-quiz.expected.json`](../../../examples/ontology-design/good-leadshook-quiz.expected.json) (0 Breaks, 0 Worth fixing with observation off). In a test it published first time, skipped 0 events, and linked all 30 buyers lead→customer and every sale lead→sale.

Objects:

- `quiz_session`: started, answering, completed. Dimensions `outcome_segment` and `quiz_score`.
- `lead`: new, qualified, disqualified. Aliases `form_submit` and `optin_submitted`.
- `customer`: active, churned. Field `offer_id`.
- `sale`: pending, paid (terminal), failed (terminal). Fields `amount` and `offer_id`.
- `refund_given`: issued. Not `refund` (universal name; it requires an `amount` key) and not `sale_refund` (shares the word `sale`).

Links: quiz_session→lead `produces`, lead→customer `converts_to`, lead→sale `has_many`, sale→refund_given `triggers`.

Version 1 is quiz_session, lead, customer and sale. Adding refund_given is improvement #1.

### Bad example 1 — one "contact" object with type-like statuses

File: [`examples/ontology-design/bad-contact-statuses.json`](../../../examples/ontology-design/bad-contact-statuses.json). Expected findings: Breaks 0 (it publishes), Worth fixing `entity_kind_as_status` (contact.customer) and `entity_no_relationship` ×2.

Why it's bad:

- No sale amount, so there's no revenue.
- No transitions, so it can't answer time-to-purchase or source → revenue.
- Repeat purchases collapse into one status.

### Bad example 2 — one purchase event routed twice, and an edge to a missing object

File: [`examples/ontology-design/bad-double-route.json`](../../../examples/ontology-design/bad-double-route.json). Expected findings: Breaks `alias_routes_to_multiple` (purchase_completed) and `relationship_unknown_end` (lead__order__converts_to:to); Worth fixing `entity_no_relationship` (customer). Publish returns 422.

Fix: give each producer name one route (emit `customer_created`), and point the edge at `customer`.

### DI guardrails

- Run experiments on synthetic properties. Draft writes replace the whole draft, so never send an empty document to a real property.
- Never pass `allow_breaking`. Never publish without the owner's go.
- If publish fails *after* the check passed (a store or verify error, not a 422 finding), stop and report it. The stores are not rolled back, so a retry on the same property can keep failing on what was left behind.
- The document `description` stays on the draft and the live version, and a wizard save keeps it. The wizard chat does not see it (the session seed drops `name` and `description`), so the competency questions are what carry the readers' questions into the app.
- Quality stays out of the Discovery chat and the wizard. It shows in check output and the Quality tab.
