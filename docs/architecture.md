---
name: architecture
description: Execution spec for CareerVinny — folder layout, file schemas, role key, skill-addressing. Read by Claude Code at build/run time. Pure spec: WHAT and WHERE, not WHY. Rationale lives in decisions.md (D-numbers referenced inline). If a skill contract disagrees with this file, this is intent — fix the skill.
status: v2 lean, 2026-06-18
---

# CareerVinny — Architecture (execution spec)

## Root principle
The agent is stateless; the filesystem is the only memory. Every durable thing is
a file, addressable by entity identity. Each skill reads only what its verb needs.

## Folder layout
```
Career/
├── reference/          # skills read; rarely changes
│   ├── career-north-star.md
│   ├── targets.md
│   ├── fit-rubric.md         # v3: machine variable table (D024)
│   ├── odds-rubric.md        # the odds/attainability axis (D018)
│   ├── workday-registry.md   # discovery's Workday cxs tenants
│   ├── lessons.md            # ROLE loop (rubric overlay + career technique)
│   └── master-profile.md
├── state/              # agent-written, mutable, permanent
│   └── roles/
│       └── {company}-{role-slug}-{seniority}/   # primary key (D002, D003)
│           ├── jd.md             # ingest
│           ├── extraction.json   # score-fit input: per-variable evidence-gated judgment
│           ├── score.md          # score-fit output
│           └── outreach.md       # later (network)
├── inbound/            # transient staging; empties after ingest (D005)
│   └── jds/
├── skills/             # one folder per skill, lazy-loaded
│   └── {skill}/
│       ├── SKILL.md
│       └── scripts/          # stdlib helpers (discovery/scout.py, score-fit/scorer.py)
├── calibration-ledger.md   # the verdict record (repo root)
└── docs/               # human/executor planning — skills NEVER read this
    ├── architecture.md · decisions.md · STATUS.md · design-lessons.md
    ├── learning-log.md · cc-batch-scout-spec.md
    └── audit-*.md            # workshop notes
```

## Role key (D002, D003)
`state/roles/{company}-{role-slug}-{seniority}/` — lowercase, hyphenated,
deterministic (reconstructable from identity, no lookup). Same role at two rungs =
two folders. One folder per role; each skill writes its own file into it.

## File schemas (frontmatter: name / description / status)

### jd.md — written by `ingest`
Frontmatter: source URL, company, title, location, date-ingested, posting-age.
Body: cleaned JD markdown. Converted once; no skill re-fetches the original.

### extraction.json — written by `score-fit` (the judgment trail)
Per-variable evidence-gated judgment feeding the engine: gates, variables {verdict-enum,
verbatim quote, confidence}, penalties, comp, multipliers, prestige, odds factors, guards.
Committed as the reproducible audit-trail input behind score.md (D022); every quote is a
verbatim jd.md substring (the engine evidence-gates it).

### score.md — written by `score-fit`
Frontmatter: rubric-version (stamped from fit-rubric.md, D025), fit (0-100, or null if
gated out), odds (0-1 product, D018) + odds-confidence, band (safety/achievable/stretch/
moonshot, D019), screen (reject/flag/pass — the MACHINE pre-screen), pipeline-stage-failed,
confidence flags (frontier-confidence, ladder, agency, recency, spine-floor). `verdict:` is
the HUMAN field (pursue/on-ramp/no) — score-fit NEVER writes it (CLAUDE.md: never invent a
verdict); it is logged gut-first into the calibration ledger and must not be anchored by
this file.
Body: reasoning trail — gate results, per-variable table (verdict-enum + evidence quote +
contribution), spine floor-gate, penalties, multipliers, odds, band. Dashboard renders from
this; never recomputes. score.md is not surfaced before the human gut verdict is logged.

## Skill-addressing
No tree scans. Address by: (1) fixed reference/ paths; (2) role key; (3) a
manifest only if scanning becomes a measured cost. Grep frontmatter `description`
before opening full files.

## Skills (one verb each; share only via reference/; no skill calls another)
- `discovery` — cheap candidate list (title, company, URL, snippet) from job-board
  APIs + Workday cxs. No full-page reads. Not on LinkedIn (D015). (Was `scout`.)
- `ingest` — conversion. Deep clean-read on gate survivors only. Raw-HTML-strip
  preferred; a browser tool in Claude Code is the auth-walled fallback (later, when ingest needs it). Writes jd.md.
- `score-fit` — jd.md + spine → score.md. Composes rubric + accepted lessons.
  Fresh-context reviewer pass ONLY on agency-flagged roles.
- `tailor-cv` — master-profile.md + jd.md → tailored CV draft.
- `network` — drafts outreach into the role folder.
- `dashboard` — renders from score.md; computes nothing.

## Ingestion funnel (D014) — cheap gates before expensive reads
```
discovery (cheap list)
  → hard-gate pre-filter (kill on metadata: visa, £60k floor, London, IC-tell (comp is a floor + penalty curve, not a £100k gate — see D026))
  → ingest (expensive clean read — survivors only)
  → score-fit
```
A role failing a hard gate is never fully fetched.

## state/ is permanent (D006)
Never garbage-collected. Dashboard reads historically (closed + open), not just
current openings.

## Two learning loops (D017)
This file's reader is Claude Code. `reference/lessons.md` = ROLE loop (read by skills).
`design-lessons.md` = DESIGN loop (read by the designer, not by skills) — present
in the folder for durability, not loaded at runtime.

## Deferred (not built until earned)
DEV-LOG / process-memory · vault-manifest · runs/ logging · promotion seam ·
dashboard · Mini Vinny integration. See decisions.md D013.
