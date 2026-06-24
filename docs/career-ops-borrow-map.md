---
name: career-ops-borrow-map
description: What to lift / adapt / skip from santifer/career-ops (https://github.com/santifer/career-ops) while building CareerVinny, and WHERE each borrow lands in the pipeline. Planning doc — skills never read this. Source: the 2026-06-23 career-ops analysis.
status: v1, 2026-06-23
---

# CareerVinny ← career-ops borrow map

## Principle: borrow hands, protect the brain
career-ops scores roles on FIXED configured weights (A–F over 10 dims) and optimises for
throughput (740+ offers, 100+ CVs). CareerVinny's moat is the opposite: weights LEARNED
from real revealed-preference verdicts (calibration loop, D025; L001–L009) + two-axis
fit×attainability (D018). So: lift career-ops's already-engineered mechanical pieces;
never let its fixed-weight scoring model leak into fit-rubric.md.

## Lift / adapt / skip (career-ops's ~15 modes)
| career-ops mode | verdict | where it lands |
|---|---|---|
| scan (Playwright portal scan, 45+ co registry) | ADAPT ⭐ | discovery v0 (Q8) — Playwright fallback for Workday/Taleo the cxs JSON can't reach; portals.example.yml seeds the registry |
| pdf + cv-template.html (Playwright HTML→PDF, ATS) | LIFT ⭐ | tailor-cv v0 |
| oferta (A–F scoring) | ALREADY-BETTER | keep fit-rubric.md; borrow only the report layout |
| cover (4 angles + approval gate) | ADAPT | network v0 |
| contacto + deep (outreach + company research) | ADAPT | network v0 |
| interview-prep (STAR bank) | LIFT later | new skill, post-network |
| batch (headless parallel eval) | ADAPT later | calibration at 200-role scale, after score-fit |
| tracker (TSV + dedup/reconcile) | DON'T lift the TSV | folder-per-role (D002/D021) is deliberate; borrow dedup/reconcile IDEAS only |
| role-matcher (archetype buckets) | careful | gate on content not title tokens (DL005/D006); a signal at most, never a gate |
| apply (form automation) | SKIP | violates "never send" (CLAUDE.md hard constraint #1) |
| training / project eval | SKIP | out of scope |
| dashboard (Go TUI) | DEFER | matches D013 deferral |
| AGENTS.md multi-CLI wrappers | SKIP | Claude-Code-only (D028); SKILL.md self-containment already adopted |

## Stack mismatch (practical)
career-ops is JS/Go; CareerVinny is Python + markdown skills. Configs/templates
(portals.yml, cv-template.html) port for free; .mjs LOGIC is reimplemented in Python to
fit scout — don't bolt on a Node runtime. career-ops's license must be checked before
copying any code verbatim (this repo doubles as a public portfolio).

## The HOW layers (not feature donors)
- **Anthropic's Agent Skills guide** (via the `skill-creator` skill) = the SKILL.md
  authoring standard. Description carries all when-to-use (and is written slightly "pushy"
  against under-triggering); the body is lean, imperative, and explains the WHY rather than
  leaning on rigid MUST/NEVER tables; progressive disclosure keeps SKILL.md < 500 lines with
  optional scripts/ + references/. House style for CareerVinny's own skills; applied to
  `skills/ingest/SKILL.md`. (Replaced an earlier addyosmani/agent-skills-style structure on
  2026-06-24 — see D029.)
- **obra/Superpowers** (MIT) = the build METHODOLOGY plugin (brainstorming, writing-plans,
  TDD, verification-before-completion, subagent-driven-development, git-worktrees).
  Global Claude Code plugin; governs HOW we build. CareerVinny's CLAUDE.md hard
  constraints OVERRIDE any generic Superpowers workflow on conflict.
