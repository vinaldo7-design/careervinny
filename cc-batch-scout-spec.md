---
name: cc-batch-scout-spec
description: Spec for the Claude Code wide-pull batch scout — pull ~200 takeable roles, apply ONLY the three hard eligibility gates, leave all preference gates open, emit a paste-able scoring file + per-role signal fields. Built for calibration-at-volume, not for a finished pipeline. Human scores; the script never writes weights.
status: spec v1, 2026-06-19
---

# Claude Code — Batch Scout Spec (200-role wide pull)

## Purpose
Collide with reality at volume. Pull ~200 roles that Vinay COULD take, varying
widely on fit, so scoring them reveals true preferences. The interview was false
intent; real roles are the test. Drop preference gates; keep only eligibility.

## THE ONE DESIGN RULE
Two gate classes, treated oppositely:
- **ELIGIBILITY gates (KEEP — hard filter):** visa-sponsorable, London/UK-anchored,
  comp floor. These are physics, not preference. A role failing these is not a
  pattern to discover — it's a role Vinay cannot accept. Filter them OUT.
- **PREFERENCE gates (DROP for this pull):** prestige, seniority-rung, frontier-
  strength, agency, IC-tell-softness, ESG-edge. These are the hypotheses being
  recalibrated. Do NOT filter on them. Let them vary; SCORE them; let Vinay's
  verdicts move them. Emit them as fields, not filters.
Result: ~200 roles that are all TAKEABLE, spread across the full fit range.

## Sources (wide + dumb, but keyworded right per D027/L-series)
Pull from public ATS boards + aggregators, NOT LinkedIn-recommended (low fertility
for a career-changer — see vault note linkedin-recommends-past-not-target).
- Greenhouse / Lever / Ashby public APIs for target-company slugs.
- Hunt by FUNCTION keyword, not buzzword org names:
  "Responsible AI", "AI Governance", "AI Ethics", "AI Strategy", "AI Transformation",
  "GTM Strategy", "Value Strategy", "Data & AI Strategy", "Strategic Product Manager",
  "AI Adoption", "AI Enablement".
- Spread across verticals: consulting AI-strategy practices, in-house enterprise
  AI-strategy/governance (banks, pharma, energy, publishing, telco), vendor/lab
  commercial-strategy. Sample firm-by-firm; banks are lumpy (JPM≠Goldman).
- Egress note: ATS APIs are blocked from inference sandboxes — run from the real
  machine (this is why it's a Claude Code job, not a sandboxed one).

## ELIGIBILITY gate logic (the only filter)
1. **Visa — Register of Licensed Sponsors lookup.**
   - Download the UK gov "Register of licensed sponsors: workers" CSV (published on
     gov.uk, updated ~daily). Cache locally; refresh per run.
   - For each role's company, fuzzy-match against the register.
     - On register → `visa: plausible` → PASS.
     - Not on register AND small/unknown firm → `visa: unlikely` → FILTER OUT.
     - Not on register BUT large multinational (likely licensed under a parent/
       variant name) → `visa: check` → KEEP, flag for manual check (don't kill a
       likely-sponsor on a name-match miss).
   - Caveat to record in output: licensed ≠ will sponsor THIS role. Register
     membership is necessary, not sufficient.
2. **Location** — London or London-anchored / UK hybrid. Remote-only-non-UK →
   filter out. UK-remote → keep, flag.
3. **Comp floor** — drop only if posted comp is clearly below ~£80k AND stated.
   Unstated comp → KEEP (LinkedIn norm; do not kill on absence). This is a soft
   floor per D026 — when in doubt, keep and flag.

## PER-ROLE FIELDS (emit all; these are signals, NOT filters)
Metadata: company, title, location+pattern, comp (or "not stated"), visa-status
(plausible/check/unlikely), source URL.
Preference signals (read from JD, scored 0/low/med/high or a short tag):
- `frontier`: named frontier-AI in responsibilities (agentic/LLM/GenAI/RAG/named
  model) vs vague "AI/ML" vs none.
- `agency`: sets-strategy / advises-C-suite (high) | influences/scoped (med) |
  supports/delivers/executes-fixed-plan (low). Quote the load-bearing verb.
- `ic_tell`: named coding stack as HARD requirement? (Python/SQL/Spark/cloud/K8s)
  → yes/no + list. (yes = likely build role; the Deloitte-vs-JPM line.)
- `seniority`: title + years + level word; map by industry (VP@bank≈Mgr@consult≈
  Vinay's rung). Flag content-rung, not title string.
- `esg_edge`: responsible-AI / AI-governance / AI-ethics / ESG / sustainability
  language present? quote it.
- `client_facing`: client/customer-facing, workshops, C-suite relationships? (now
  a heavy want, L002.)
- `origination`: owns BD/pitch/SoW/relationship? (wanted IF bundled w/ strategy,
  L003 — flag whether strategy-bundled or pure-sales.)
- `networkability`: can a named human be identified (hiring manager, team lead,
  2nd-degree contact)? yes/maybe/no. (Tests L006 — is networkability a real fit
  signal or just client-facing re-described.)

## OUTPUT 1 — paste-able scoring file (roles.md)
Markdown Vinay pastes into a fresh chat to run a scoring session. Structure:
- **Header:** run date, total pulled, total after eligibility filter, count by
  source/vertical.
- **Gate-pressure table:** per eligibility gate — how many roles it filtered, and
  the SOLE-KILLER count (roles it alone removed that passed everything else). This
  is the "which gate to interrogate" dashboard. (Reporting only — script never
  acts on it. Goodhart guard: market reveals what EXISTS; only Vinay's verdict
  reveals what he WANTS. Weights move on verdicts, never on volume.)
- **Roles**, grouped into rough provisional bands (high/med/low fit) using the
  CURRENT rubric weights, each with: metadata line + the 8 preference-signal tags
  + the single most load-bearing JD quote. Compact — one role = ~6 lines. Built
  for fast human scan, not exhaustive reading.
- Batch in chunks of ~25 so a scoring session is digestible.

## OUTPUT 2 — calibration ledger (calibration-ledger.md) — I (chat) maintain this
NOT generated by CC. This is the compounding artifact. Per scored role:
`role-id | verdict (pursue/no/on-ramp) | one-line why (Vinay's words) | rubric
provisional band | GAP (did verdict match the band? where it diverged)`.
The GAP column accumulated across ~30-50 roles is what weights get fitted to
(D025 Phase 2). Below the ledger: a running "extrapolated lessons" section that
generalises the per-role deltas into rubric edits (the L-series, compacted).

## HARD CONSTRAINTS (the difference between calibration and capitulation)
- The script READS the rubric to score; it NEVER writes weights. Rubric → script,
  one direction only. Weight changes are a separate human-gated step.
- Gate-pressure stats are FLAGS for human review, not auto-adjustments. A gate
  with a high sole-killer count gets surfaced to Vinay, who pulls those specific
  roles and decides — his verdict moves the weight, not the stat.
- No fabricated fields. Absent → "not stated". (Same discipline that keeps bad
  data out of the calibration set.)
- Human scores every role that reaches the scoring file. CC finds and stages;
  Vinay decides; nothing is applied or sent.

## SEQUENCING
1. CC builds the eligibility filter + register lookup first; prove it on ~20 roles.
2. Then the wide pull to ~200; emit roles.md.
3. Vinay + chat score in ~25-role chunks, logging verdicts to the ledger.
4. At ~30-50 verdicts: drill the math — fit the weights to the accumulated GAP
   column. THIS is when scoring math gets precise (not before — too few labels).
