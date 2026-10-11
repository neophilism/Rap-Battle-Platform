> **Canonical PR work plan:** [`registry/roadmap.json`](../registry/roadmap.json). The detailed historic instructions below remain authoritative for scope, while all current planned work/PR links must be updated in the canonical registry.

# Rap Battle Platform — original twelve-milestone downstream development plan

**Recovery provenance:** original October 7, 2026 conversation specifying this downstream application and its 12-PR roadmap. **All 12 original milestone names recovered.** The implementation/acceptance expansion here is technical guidance grounded in that conversation, not a purported verbatim transcript. Milestone numbers are not necessarily GitHub PR issue numbers.

## Product purpose and boundary

A separate multi-tenant, white-label rap battle and local-league platform built on Live-Competition-Engine; multiple promoter-operated leagues must be independently branded, owned and operated. The platform cannot be implemented as MMS styling or a hardcoded engine mode.

## Non-negotiable product requirements

- Battle formats include 1v1, three-round, single-round, tournament and crew battles; freestyle and written performances.
- Contestants, producers, adjudicators and audiences have distinct capabilities; rounds, timers, brackets, judging and audience voting are configurable.
- Each local promoter controls its branding, domain, leagues, bookings, merchandising and sponsor slots subject to platform policy.
- Tickets, entry fees, PPV, subscriptions, platform cuts, creator memberships, tips/gifts, ads, sponsorship, merchandise and booking are independent monetization options with four-level enable/disable inheritance.
- No tenant may access another tenant's private artist agreements, payment ledgers, subscriber lists, panel scores or administrative controls.
- End-to-end acceptance uses three independent synthetic leagues representing New York, Atlanta and Los Angeles; those are fixtures, not endorsements/real partnerships.

## Dependencies and architecture

Use Live-Competition-Engine identity, tenancy, generic event/round/timer, producer control, judge, audience, commerce/ledger and SaaS primitives. Rap-specific scoring/wording/themes stay downstream.

## Original ordered implementation plan

### RAP-01 — Multi-tenant application shell

- **Implement:** Initialize separate app, versioned engine dependency, tenant routing/session boundary, health and CI.
- **Dependencies:** original milestones 1–0 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-02 — White-label design

- **Implement:** Operator branding, colors, domain mapping and templates with no custom fork required per league.
- **Dependencies:** original milestones 1–1 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-03 — Battle terminology

- **Implement:** Map generic event/stage/round/performer/score objects to battle, emcee, promoter, match, judge, round, league and champion.
- **Dependencies:** original milestones 1–2 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-04 — Battle presets

- **Implement:** Ship configurable 1v1, three-round, one-round, crew and tournament templates; written/freestyle; timers and tie/forfeit states.
- **Dependencies:** original milestones 1–3 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-05 — Artist profiles

- **Implement:** Artist roster, biographies, media, past battles, stats, permissions, consent and promoter booking visibility.
- **Dependencies:** original milestones 1–4 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-06 — Creator economy

- **Implement:** Artist memberships, fan support, optional tips, paid media, configurable platform/tenant shares, audited payout consent.
- **Dependencies:** original milestones 1–5 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-07 — Local league administration

- **Implement:** Per-league event calendar, promoters/staff, applicant/lineup, format defaults, brackets, judges, moderation and contracts.
- **Dependencies:** original milestones 1–6 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-08 — League discovery

- **Implement:** Local league discovery, location-independent browsing, public listings and tenant-owned promotional pages.
- **Dependencies:** original milestones 1–7 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-09 — Rankings and records

- **Implement:** Historical match outcomes, league standings, seeding, disputes/corrections and filters for styles/formats.
- **Dependencies:** original milestones 1–8 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-10 — Revenue sharing

- **Implement:** Revenue accounting for event/artist/promoter/platform; ticket/PPV/refund/chargeback splits and settlement evidence.
- **Dependencies:** original milestones 1–9 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-11 — Sponsorship package

- **Implement:** Sponsor inventory, approvals, ad placements, invoices, reports and tenant-by-tenant opt-in controls.
- **Dependencies:** original milestones 1–10 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Demonstrate the scoped workflow with unit/integration tests, authorization and relevant failure paths; round-trip every persisted setting/record; no unauthorized cross-tenant/private access or non-consensual publication.

### RAP-12 — Production validation

- **Implement:** Simulate three independently branded leagues and complete live-battle operations, streaming, votes, scored results, admin isolation, sponsor and split reconciliations.
- **Dependencies:** original milestones 1–11 as needed, plus the corresponding reviewed upstream core capability; do not represent missing upstream features as complete.
- **Acceptance:** Run three fictional NY/Atlanta/Los Angeles league fixtures with distinct branding, artists and sponsors; full live event with one-round and three-round presets; verified judge/audience counts; expected split receipts; payment-on/off; tenant isolation; operations, deployment and monitoring.

## Verified release acceptance

Run three fictional NY/Atlanta/Los Angeles league fixtures with distinct branding, artists and sponsors; full live event with one-round and three-round presets; verified judge/audience counts; expected split receipts; payment-on/off; tenant isolation; operations, deployment and monitoring.

Test both payment-enabled and no-payment modes, mobile/keyboard accessibility, public/private page leakage, signed media access, user consent, CI, backups/restore, telemetry and basic production smoke. Demo actors, streams, events and revenue must be clearly marked synthetic unless backed by a live service.

## Handoff for another ChatGPT account

1. First read this complete file and `README.md`, then inspect the newest `main` commit, open/closed PRs, CI, upstream engine branch, Render/Neon status, and `.exechub/project.yml` if present. Confirm that upstream APIs really support the next milestone.
2. Treat these milestones as **planned** until code + tests are merged; empty repo or a file commit does not constitute app implementation. Map milestone IDs to actual PRs in the work-status tracking system, keeping a source-of-truth and recording evidence links.
3. Choose ordinary technical decisions independently. Chain passing PRs; stop only on a failed gate, lacking credentials/permissions, legal/commercial commitment or material product change. Do not leak production secrets into commits or tests.
4. The app is a separate repository/deployment; do not edit the engine to bake in this app's labels, product defaults or branding.

## Recovery status

The original numbered plan and product constraints are recoverable; external API selections, credential readiness and present-day deployment cannot be certified from a past conversation. Do not infer current availability from this handoff document.
