---
name: workday-registry
description: Curated, calibration-grown registry of Workday `cxs` tenants for the consulting / bank / pharma verticals the public ATS boards (Greenhouse/Lever/Ashby) cannot see. Read by skills/discovery (scout.py fetch_workday). The API is the easy part — this registry is the hard part.
status: v0, 2026-06-24 (seeded from probe; grows from real verdicts)
---

# Workday tenant registry

Each row is a Workday tenant whose public `cxs` JSON endpoint
(`https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/jobs`, POST,
login-free) has been **probe-verified** to return live UK roles. This closes the
2026-06-23 audit blind spot: management consulting, large banks, and big pharma
post here, not on the public boards (D014 · D027 · Q8).

`scout.py` parses the table below — the `wd<N>` column guard skips the header and
separator rows, so keep that column well-formed. Columns after `vertical` are
human notes the parser ignores. Coordinates could not be guessed (`wd` ranges
wd3–wd103); each is verified, never asserted (DL001).

| company | tenant | wd | site | vertical | verified | notes |
|---|---|---|---|---|---|---|
| Accenture | accenture | wd103 | AccentureCareers | consulting | 2026-06-24 | no locationsText — city in externalPath/bulletFields; wd103 (not wd1–5) |
| Lloyds Banking Group | lbg | wd3 | LBG_Careers | bank | 2026-06-24 | site has an underscore; tier-1 UK bank |
| NatWest Group | rbs | wd3 | RBS | bank | 2026-06-24 | legacy `rbs` tenant (not `natwest`); site is capitalised |
| GSK | gsk | wd5 | GSKCareers | pharma | 2026-06-24 | wd5; UK roles tagged UK--London--… in externalPath |
| AstraZeneca | astrazeneca | wd3 | Careers | pharma | 2026-06-24 | locationsText present (UK - London / UK - Cambridge) |

## searchText query set (D027 — hunt functions, not org names)
Lives in `scout.py:WORKDAY_QUERIES`, mirroring the D027 keyword set:
Responsible AI · AI Governance · AI Ethics · AI Strategy · AI Transformation ·
Data and AI · GTM Strategy · Strategic Product · AI Adoption · Value Strategy.
(NOT bare AI-branded sub-unit names — those return IC-build roles.)

## How this grows (calibration-driven, never hardcoded — D025)
- Add a tenant only after probe-verifying its `cxs` endpoint returns HTTP 200 with
  a `jobPostings` array (HTTP 422 is a trap — wrong coords that look alive). Mirror
  `scripts/probe.py`.
- Grow from real verdicts: when a Workday role earns a would-pursue verdict, its
  tenant has earned its place. Demote tenants that never yield a kept role.
- NOT on Workday → not here. Capgemini (SAP SuccessFactors), for example, needs the
  Taleo/SuccessFactors fallback deferred under Q8, not this table.

## Provenance
Seeded 2026-06-24 from a 6-tenant parallel probe (Accenture, Capgemini, Lloyds,
NatWest, GSK, AstraZeneca). Capgemini excluded — SuccessFactors, not Workday.
