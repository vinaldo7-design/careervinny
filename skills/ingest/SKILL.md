---
name: ingest
description: Convert ONE job posting (a URL or pasted text) into a clean, stored jd.md so no skill re-fetches the original. Run only on roles that already passed the cheap eligibility gates.
---

# ingest — one role → jd.md

**Job:** take a single job posting and store a cleaned, structured copy in state/.

## Input
A job posting URL, or pasted JD text. Run only on roles that already cleared the cheap
eligibility gates (see `reference/targets.md`): visa-sponsor, London/UK, strategic-not-IC.

## Steps
1. Get the posting text:
   - URL → fetch it (free): prefer a raw HTML fetch + strip to readable text. If the
     page is auth-walled or JS-only, fall back to a browser fetch.
   - Pasted text → use as-is.
2. Extract the key facts: company, title, location, posted date (or "not stated"), source URL.
3. Build the role key: `{company}-{role-slug}-{seniority}` — lowercase, hyphenated,
   reconstructable from identity (see `docs/architecture.md` role key).
4. Write `state/roles/{key}/jd.md`:
   - **Frontmatter:** `source-url`, `company`, `title`, `location`, `date-ingested`, `posting-age`.
   - **Body:** the cleaned JD as readable markdown — full responsibilities/requirements,
     stripped of nav/cookie/boilerplate.
5. Convert once. Nothing re-fetches the original after this.

## Rules
- No fabricated fields — missing data → "not stated" (CLAUDE.md).
- Writes to `state/` only. Reads nothing from `docs/`.
- One role per run.

## Done test
`state/roles/{key}/jd.md` exists, every frontmatter field is present (or "not stated"),
and the body is a clean, readable JD.
