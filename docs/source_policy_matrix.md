# Source Policy Matrix

Use this matrix as the legal go/no-go gate before enabling connectors.

## Status Rules

- `Allowed`: connector may run in production.
- `Conditional`: connector may run with documented constraints and mitigations.
- `Blocked`: connector must not run.

## Matrix

- Source: DataBreaches.net
  - Method: RSS/archive parsing
  - Status: Conditional
  - Attribution: Link back to source article
  - Retention: Store normalized metadata and citation URL
  - Rate limits: Max 1 request every 10 seconds
  - Reviewer: Founder
  - Review date: TBD
- Source: HHS OCR
  - Method: Structured public dataset/API
  - Status: Allowed
  - Attribution: Include HHS OCR citation
  - Retention: Retain raw payload hash + normalized fields
  - Rate limits: Respect published guidance
  - Reviewer: Founder
  - Review date: TBD
- Source: SEC EDGAR 8-K
  - Method: Filings feed/API
  - Status: Allowed
  - Attribution: Include filing accession reference
  - Retention: Store filing reference and extracted claims
  - Rate limits: SEC fair access constraints
  - Reviewer: Founder
  - Review date: TBD
- Source: BleepingComputer
  - Method: News parsing
  - Status: Conditional
  - Attribution: Direct story citation
  - Retention: Store extracted claims and source URL
  - Rate limits: Conservative crawl cadence
  - Reviewer: Founder
  - Review date: TBD
- Source: State AG Portals
  - Method: Per-state parser overrides
  - Status: Conditional
  - Attribution: Per-state source citation
  - Retention: Structured summary plus source link
  - Rate limits: Per-portal conservative limits
  - Reviewer: Founder
  - Review date: TBD
- Source: CourtListener
  - Method: API/search integration
  - Status: Allowed
  - Attribution: CourtListener and case reference
  - Retention: Case metadata and citation
  - Rate limits: Respect API limits
  - Reviewer: Founder
  - Review date: TBD
- Source: HIBP Historical List
  - Method: Public historical breach list
  - Status: Conditional
  - Attribution: Source citation required
  - Retention: Historical enrichment fields
  - Rate limits: N/A for static imports
  - Reviewer: Founder
  - Review date: TBD
