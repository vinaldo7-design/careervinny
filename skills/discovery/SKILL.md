---
name: discovery
description: Find new candidate roles cheaply — across the public ATS boards (Greenhouse/Lever/Ashby) AND the Workday `cxs` verticals (management consulting, large banks, big pharma) the public boards cannot see. Use whenever the candidate pool needs refreshing or roles need finding to feed ingest: "find roles", "run discovery / the scout", "what's live", "any new consulting/bank/pharma roles". Emits a cheap ranked candidate list after eligibility gates — never reads full pages; survivors go to ingest. Not for converting one posting (that is ingest) or scoring one (that is score-fit).
---

# discovery — cheap candidate list across public boards + Workday

Discovery is the wide, cheap top of the funnel (D014): it lists roles by metadata alone
(title, company, URL, location, freshness), kills most of them on eligibility, and hands the
few survivors to ingest for the one expensive full read. It never opens a job page — that
boundary is what keeps it cheap at scale. Its Workday `cxs` layer is the fix for the
2026-06-23 audit blind spot: consulting, banks, and pharma post via Workday, invisible to
the Greenhouse/Lever/Ashby boards, and that is bullseye role-family #1.

## Procedure

1. **Run the scout.** From the repo root:
   `python3 skills/discovery/scripts/scout.py` — polls the public boards *and* every Workday
   tenant in `reference/workday-registry.md`. Useful flags: `--workday-only` (just the cxs
   verticals), `--no-workday` (just the public boards), `--per-firm N` (cap kept roles per
   firm; `0` = no cap), `--out PATH`. The visa gate needs `data/sponsor-register.csv` (large,
   git-ignored — refresh per `data/README.md`).

2. **Know what it filters on.** Public boards are title-keyword matched (the D027 function
   set); Workday tenants are POSTed the same query set as `searchText`, which narrows
   server-side, so the Workday rows skip the title gate. Then it applies ELIGIBILITY gates
   only — visa (sponsor register), location (London/UK), comp (£60k floor; the cxs list view
   carries no comp, so Workday comp reads "not stated" and is kept per the soft-floor rule).
   Preference signals (frontier, agency, ic_tell, esg_edge, seniority) are OBSERVATIONS for
   triage, never filters. Eligibility is physics — you cannot get a role you can't be
   sponsored for, in the wrong country. Role-fit and strategic-not-IC need the body, so they
   wait for ingest / score-fit.

3. **Read the output.** `out/roles.md` (human triage) and `out/kept.json` (machine) — both
   regenerable and git-ignored. Each candidate carries company, title, URL, location, posting
   freshness, the three gate decisions, the matched query, and the signals. Scan for
   role-family #1 in the *titles* (Responsible AI / AI governance / AI strategy): `searchText`
   matches the body too, so a gate-passing Workday row is not always in-family — the title and
   `matched_kw` tell you which are.

4. **Hand survivors to ingest.** Choose the gate-passing, in-family roles worth a full read
   and pass each URL to ingest, which writes `state/roles/{key}/jd.md`. Discovery itself never
   writes `state/` and never reads a full page.

Read only what `reference/` holds (targets, fit-rubric gates, the Workday registry); write
only a candidate list into `out/`.

## Growing the Workday registry

The cxs API is the easy part; the curated tenant registry is the hard part. Add a tenant only
after probe-verifying its endpoint returns HTTP 200 with a `jobPostings` array — HTTP 422 is a
trap (wrong coordinates that look alive), and the `wd` number is per-tenant (seen from wd3 to
wd103), so never guess it; mirror `scripts/probe.py`. Grow the table from real verdicts (D025):
a tenant earns its place when one of its roles earns a would-pursue verdict; demote tenants
that never yield a kept role. A company not on Workday (e.g. Capgemini = SAP SuccessFactors) is
not in this table — that is the Taleo/SuccessFactors fallback deferred under Q8.

## A note on Workday location

Workday reports location inconsistently: some tenants omit `locationsText` (the city is in the
`externalPath` or `bulletFields`); multi-location roles show a bare "N Locations" count. The
gate reads those sources in that order and gates a multi-location role on its FIRST location
only — the complete list needs the detail endpoint, which is ingest's read. A London role
whose first-listed location is elsewhere can slip the net; that is an acceptable miss for a
cheap pass, not a silent one.

## Example

`python3 skills/discovery/scripts/scout.py --workday-only --per-firm 0` → 144 gate-passing,
currently-live UK roles the public boards cannot see, across all three families (consulting,
bank, pharma) — e.g. Accenture "Data & AI Strategy Manager" (London), GSK "AI/ML Engineer,
Responsible AI" (London). See `proof-discovery-v0.md`.

## Done when

`out/roles.md` and `out/kept.json` are written; each candidate carries its gate decisions,
freshness, and signals; and the gate-passing, in-family survivors are identified for ingest.
Show the kept-by-vertical counts and a couple of bullseye examples (with URLs) as evidence.
