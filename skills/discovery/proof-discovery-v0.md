# discovery v0 — proof (2026-06-24)

**Claim (STATUS):** the registry yields currently-live, gate-passing roles from at least one
consulting / bank / pharma target — bullseye role-family #1 that Greenhouse/Lever/Ashby
cannot see.

**Verdict: PROVED** — across all THREE families in a single run.

## Run
`python3 skills/discovery/scripts/scout.py --workday-only --per-firm 0`
- 5 Workday tenants polled (`reference/workday-registry.md`), D027 `searchText` query set.
- pulled **814** → kept **144** after eligibility gates.
- kept by vertical: **bank 92 · consulting 5 · pharma 47**.
- gate-pressure: location filtered 670 (non-UK, correctly dropped); visa 0; comp 0
  (cxs list view has no comp → "not stated" → kept per soft-floor).
- freshness ranged "Posted Today / Yesterday" → "30+ Days Ago" — i.e. currently live.

## Bullseye role-family #1, gate-passing (visa = plausible/Skilled Worker, location = London/UK)

| family | company | role | location |
|---|---|---|---|
| consulting | Accenture | Data & AI Strategy Manager | London |
| consulting | Accenture | Data & AI Value Strategy Consultant | London |
| pharma | GSK | AI/ML Engineer, Responsible AI | London (Stanley Building) |
| pharma | AstraZeneca | Senior Strategy Director (Consultant) — Clinical Development, Evinova | UK – Cambridge |
| bank | Lloyds Banking Group | Strategy Director — Corporate & Institutional Banking | UK |
| bank | NatWest Group | Reputation Strategy Lead | UK |

Example URL (clickable, login-free):
<https://accenture.wd103.myworkdayjobs.com/en-US/AccentureCareers/job/London/Data---AI-Strategy-Manager_R00234596>

## Why this is the blind-spot fix
The public ATS boards expose no tier-1 consulting/bank/pharma employer — they post via
Workday. The `cxs` layer reaches them directly. Coordinates were probe-verified, never
guessed (the `wd` number ranges wd3–wd103; HTTP 422 is a trap that looks alive). Capgemini was
probed and excluded — SAP SuccessFactors, not Workday.

Full output (regenerable, git-ignored): `skills/discovery/out/roles.md` · `out/kept.json`.
Fixture tests for the parse + gate wiring: `skills/discovery/scripts/test_workday.py` (18 pass).
