---
name: design-lessons
description: The DESIGN loop. What Vinay and the System Designer learn about BUILDING CareerVinny — architecture corrections, technical patterns, advisor-calibration. Read by the System Designer (Claude-in-chat) at the start of a new chat for continuity. Distinct from reference/lessons.md, which is the ROLE loop (career practice, read by Cowork's skills at runtime). Two loops, two readers, two files. Append-only; supersede with dated entries.
---

# CareerVinny — Design Lessons (the build loop)

This file is about getting the BUILD better, not getting role-finding better.
Role/career practice learning lives in `reference/lessons.md` (read by skills).
This file is read by the System Designer for continuity across chats.

## Entry format
`## DLnnn - YYYY-MM-DD - short-slug`
trigger · what happened · rule · status (proposed/accepted)

---

## DL001 - 2026-06-18 - advisor-states-system-claims-as-fact
trigger: During architecture work the System Designer asserted how Cowork
Projects map to chat project-knowledge (claimed one shared live filesystem) as
fact. It was a guess about internal plumbing; observable evidence (a stale
snapshot missing files the live folder had) proved it false. Vinay caught it.
signal: the advisor's errors cluster in ONE class — claims about how a tool or
system BEHAVES — not in design reasoning projected from stated principles. Design
reasoning held all session under stress-testing. The defect is narrow: infra
claims dressed as principle-derived fact.
rule: tag claims by SOURCE class —
  (1) follows-from-a-stated-principle → user-verifiable against own files;
  (2) general/external knowledge → externally checkable, search if load-bearing;
  (3) how-a-system-works → MUST be flagged unconfirmed or searched, never stated
      as fact. Class-3 belongs in the flagged-assumptions block, never in prose.
A self-assigned numeric confidence score is REJECTED — it would have read "high"
on the false claim. Real metric: did uncertain claims land in the flagged block
or leak into prose? Vinay-auditable per message.
unconfirmed claims from the founding session (re-check before relying):
  - Cowork Project ↔ project-knowledge sync mechanism
  - obsidian / mini-vinny MCP connectors live in Cowork, same vault on disk
  - Cowork can run obsidian write tools as a skill
  - exact KBAI ## Links heading strings — verify vs vault_taxonomy.yaml
  - Claude Code filesystem access spans both repos (machine-setup dependent)
watch: do class-3 claims keep leaking into prose after this? If yes, the
flagged-block mechanism is insufficient and the advisor should search-by-default
on system claims instead of self-policing.
status: accepted

## DL002 - 2026-06-18 - two-learning-loops-must-not-merge
trigger: "lessons" was being used for two different things — role-fit revealed
preference AND system-build learning. Vinay split them.
signal: they have different readers (skills vs the designer), different write
triggers (a role decision vs a build decision), and different homes (reference/
vs repo root). Merging them makes each reader load what it doesn't need.
rule: `reference/lessons.md` = ROLE loop (career practice: role-fit deltas +
outreach/networking/application/sourcing techniques; read by skills). This file =
DESIGN loop (build learning; read by the designer). Never merge. The
advisor-calibration entry (DL001) is a design-loop lesson, not a third category.
status: accepted

## DL003 - 2026-06-18 - advisor-asserted-source-fertility-before-checking-it
trigger: Designing scout's source layer, the System Designer concluded the public
ATS APIs (Greenhouse/Lever/Ashby) made the prestige-AI-lab target set "trivially
reachable" and said Vinay was "on solid ground." A turn later, an actual fertility
check (pulling Anthropic's live board + reading the London role mix) showed the
ground was mostly IC-chaff for Vinay's profile: the high-comp seats are RL-scaling
IC roles the north-star rejects, the "Applied AI" roles are disguised FDE-coding
jobs, and the genuine-fit GTM-strategy seats are rare and episodic. The pipe was
solid; the soil under it was not. Correct target weighting turned out to be the
INVERSE of what was first implied — consultancy AI practices fertile, labs
low-yield.
signal: SAME defect class as DL001 — confidence about how a part of the world
BEHAVES (here: what a data source actually CONTAINS) stated before the cheap
empirical check that would confirm it. The plumbing claim (APIs exist, are public)
was sound and verifiable; the fertility claim (those APIs carry roles Vinay wants)
was an inference dressed as a conclusion. Reachability of a source ≠ fertility of
a source.
rule: separate SOURCE-REACHABILITY (can the pipe connect — externally checkable,
class-2) from SOURCE-FERTILITY (does what comes through match the target spec —
must be SAMPLED, never assumed). Never declare a hunting ground good on
reachability alone. Before committing any source to the Tier-1 list, pull a real
sample and check it against the actual rubric gates (London + £100k +
strategic-not-IC + visa). "Stand on shoulders of giants" applies to plumbing
(reuse JobSpy, the ATS APIs); it does NOT transfer to fertility — their volume
strategy is built for a different candidate than Vinay.
watch: does DL001's watch now trip? Two entries (DL001, DL003) of the same class =
the pattern is real, not a one-off. If a third appears, stop self-policing: ban
outcome-confident language ("solid ground", "trivially", "you're set") on any
claim not yet sampled, and route fertility/behaviour questions to a mandatory
sample-first step BEFORE the recommendation, not after.
status: accepted

## DL004 - 2026-06-18 - advisor-called-scoring-testable-before-checking-dependencies
trigger: Vinay said the scoring/networking system was "testable right out the gate
in the MVP" and the System Designer initially ran with it. On reflection the
designer corrected: scoring is DESIGN-able now but not TEST-able now — it has
nothing to score until ingest produces jd.md and scout produces candidates
(score-fit is the consumer; the job flow is the producer, per D020). "Testable now"
was really "thinkable on paper now," which is just more design.
signal: SAME defect class as DL001 and DL003 — a claim about how something will
BEHAVE (here: "this is testable") asserted before checking it against the actual
dependency graph. The correction came from the designer this time, not Vinay, but
the class is identical: behaviour-confidence ahead of the cheap check.
rule: THREE instances of one class (DL001, DL003, DL004) trips DL001's
watch-condition. ESCALATE from self-policing to a hard rule: do NOT use
outcome/behaviour-confident framing ("testable", "trivially reachable", "solid
ground", "you're set", "this works") on any claim about how a part of the system
behaves until the dependency or sample has been checked. Route behaviour /
fertility / testability questions to a mandatory check-first step BEFORE the
framing. For "is X testable/buildable now?" specifically: trace X's input
dependencies first; if an input doesn't exist yet, X is design-able, not testable.
watch: the flagged-assumptions block at message-end has been catching these AFTER
the fact (the correction always landed). Open question: does the hard rule move the
catch BEFORE the prose? Vinay-auditable — do behaviour claims now arrive
pre-checked, or still get corrected a turn later?
status: accepted

## DL005 - 2026-06-19 - gate-on-role-content-not-on-tokens
trigger: A live multi-family fertility sample (QuantumBlack, BCG X, Anthropic,
Accenture, JPMorgan, Goldman, plus a Responsible-AI sweep across Lloyds, Elsevier/
RELX, E.ON) surfaced THREE distinct token-traps in one session, each of which the
existing rubric would have mis-handled:
  (a) ORG AI-BRAND ≠ fertility. "AI by McKinsey" (QuantumBlack) and "BCG X" are
      ENGINEERING brands; their London roles are Data Scientist / ML Engineer /
      Forward-Deployed-AI-Scientist — IC-chaff for Vinay. The AI-strategy work he
      wants lives under un-sexy titles (GTM Strategy, Value Strategy, Strategic PM,
      Responsible AI) and often NOT at the AI-branded sub-unit at all. DL003 said
      "consultancy AI practices fertile"; the refinement is "the BUILD-branded arms
      are also chaff — fertility is in the classic-strategy track and the
      governance/responsible-AI function, not the AI-brand."
  (b) TITLE-STRING ≠ seniority. "Vice President" at a bank (JPM) is the ~2-7yr
      INDIVIDUAL rung (Analyst→Associate→VP→ED→MD), i.e. Vinay's level — NOT a
      level above. The same string "VP" means executive at a startup and mid-level
      at a bank. The seniority drift-guard, applied to the title token, would
      auto-reject Vinay's most fertile finance roles as "titled a level above."
  (c) ONE FIRM ≠ a family. JPM has a named AI-strategy function (CDAO / SAIGE /
      AI Transformation Office) → fertile. Goldman buries AI inside Engineering and
      Product → low-yield for Vinay despite being the same "bank" block. Weighting
      "banks" as a block off JPM alone would have been the DL003 error again.
signal: SAME defect class as DL001/DL003/DL004 (now the FIFTH instance) — a claim
about how a slice of the world BEHAVES (which orgs/titles carry the roles Vinay
wants) is cheap to get wrong when read off a TOKEN (brand name, title word, single
firm) instead of the role's OBSERVABLE CONTENT. The token is a lossy, often
inverted proxy for the thing the gate actually cares about.
rule: GATE ON CONTENT, NEVER ON TOKENS. Every gate/score variable must read the
role's observable substance, not a label:
  - seniority → years-required + comp-band + reports-and-scope, NOT the title word.
    Maintain an industry title→rung map (VP@bank ≈ Manager@consultancy ≈ Lead/
    Strategist@lab ≈ Senior-Associate@MBB ≈ Vinay's entry rung).
  - fertility / source-weighting → sampled role-mix of the actual board, NOT the
    org's AI-branding. Build-branded arms (QuantumBlack, BCG X, BCG Platinion) are
    LOW-yield; governance/responsible-AI + classic-strategy + lab-commercial-
    strategy are the fertile veins.
  - "is this family fertile?" → sample ≥2 firms before weighting the family;
    firms within a nominal block (banks) are LUMPY (JPM≠Goldman).
escalation: DL001's watch has now tripped at the FIFTH instance. The hard rule
from DL004 (no behaviour-confident framing before the check) is RE-AFFIRMED and
EXTENDED: for any gate or source-weight decision, the cheap check is a TOKEN→
CONTENT translation — never let a brand name, title string, or single-firm sample
stand in for sampled role content. If a sixth instance appears, the flagged-block
mechanism is insufficient and source/seniority weighting must be moved behind a
MANDATORY sample step in the skill itself (not advisor self-policing).
status: accepted
