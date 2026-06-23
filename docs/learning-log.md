# CareerVinny — learning log

Plain-English notebook of what we build and the reusable idea behind each step.
Newest entry on top. (Workshop doc — no skill reads this.)

## 2026-06-23 — Entry 1: first build = the `ingest` skill

**What we're doing:** building the first working piece of the pipeline — smallest first.

**Concept — what a "skill" is.** A skill is a folder under `skills/` with a `SKILL.md`
file. SKILL.md is a *recipe*: it tells me how to do ONE repeatable job. Build it once,
run it many times. Our first one is `ingest`.

**Concept — `STATUS.md` (the build stack).** `docs/STATUS.md` lists what to build, in
order. The top item marked `next` is the current job. A scope is "done" only when it
PROVES its claim (the claim is the test). Finish one before starting the next.

**What `ingest` does:** takes one job posting (a URL or pasted text), cleans it up, and
saves it as `state/roles/{key}/jd.md`, so the rest of the pipeline never re-fetches the
original. Convert once.

**Why this first — not the Workday discovery fix, even though that's the bigger gap:**
- It's your settled call (decisions Q1: ingest-first).
- It's the smallest self-contained slice — ideal for learning the skill pattern.
- No dependencies: discovery needs a company list that should come from *calibration*
  (not done yet); ingest just needs one role to chew on.
- Discovery is scope #2 — that's where your free, calibration-grown Workday list plugs in.

**Next:** prove `ingest` works by running it on one real role and watching `jd.md` appear.
