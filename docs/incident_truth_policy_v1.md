# Incident Truth Policy v1

Incident records are evolving timelines. Claims can be corrected over time.

## Source Precedence

1. Regulatory/government filings
2. Court/legal records
3. Primary organization disclosures
4. Reputable security reporting

## Conflict Handling

- Preserve all conflicting claims in `incident_sources`.
- Compute aggregate confidence using source precedence and recency.
- Keep one canonical incident state while retaining claim history.

## Merge/Split Rules

- Analysts can merge incidents when separate records refer to the same event.
- Analysts can split incidents when a combined record contains distinct events.
- Merge/split operations require reason codes and audit notes.

## Retractions and Corrections

- Do not hard-delete prior claims.
- Append correction events and recalculate canonical fields.
