---
name: ingest
description: Convert a single job posting (a URL or pasted JD text) into a clean, stored state/roles/{key}/jd.md, so the posting is read and cleaned exactly once and never re-fetched. Use whenever a role has cleared the cheap eligibility gates (visa-sponsor, London/UK, strategic-not-IC — see reference/targets.md) and its full description needs capturing before scoring: handing over a job URL or pasted JD, "ingest this role", "save this posting". Not for finding roles (that is discovery) or scoring them (that is score-fit).
---

# ingest — one posting → jd.md

Ingest is the one expensive read in the pipeline: discovery lists roles cheaply, a hard-gate
pre-filter drops most of them on metadata alone, and only the survivors reach ingest for a
full clean read. The agent keeps nothing between runs, so the `jd.md` written here becomes
the only lasting record of the posting — score-fit, tailor-cv and everything downstream
read it, never the live page. Capture it well once and the original is never needed again.

## Procedure

Handle exactly one role per run.

1. **Get the posting text.** Pick the cheapest source that returns the *complete* description:
   - A public-ATS URL (Greenhouse / Lever / Ashby) → fetch the posting from the same public
     JSON API discovery uses; its per-posting endpoint returns the full content already free of
     nav and boilerplate (e.g. `boards-api.greenhouse.io/v1/boards/{token}/jobs/{id}`).
     These payloads often double-encode HTML entities, so decode twice before stripping tags.
   - A Workday URL (`{tenant}.{wd}.myworkdayjobs.com/.../job/...`) → GET the cxs DETAIL
     endpoint `https://{tenant}.{wd}.myworkdayjobs.com/wday/cxs/{tenant}/{site}/job{externalPath}`
     (same coords as the discovery registry, no login). Returns JSON with
     `jobPostingInfo.jobDescription` (HTML body) plus `title`, `location`, `startDate` — strip
     the HTML to readable text and read the identity facts from the JSON.
   - Any other career page → fetch the HTML and strip it to readable text.
   - An auth-walled or JS-only page → fall back to a browser fetch.
   - Pasted text → use it as-is.

2. **Read the identity facts off the source** — company, title, location, posted date,
   source URL. Take them from the posting; don't guess. Anything the posting doesn't state
   becomes the literal value `not stated`: a plausible-but-wrong value silently poisons later
   calibration, whereas `not stated` is honest and can be filled in later.

3. **Build the role key** `{company}-{role-slug}-{seniority}` — lowercase, hyphenated,
   reconstructable from the role's identity alone (no lookup needed). Seniority belongs in the
   key because the same role at two rungs scores differently and lives in two folders. When
   the title already carries the level (e.g. "Lead Business Analyst"), use that as the
   seniority and don't repeat it: `graphcore-business-analyst-lead`.

4. **Write `state/roles/{key}/jd.md`** in this shape:

   ```
   ---
   source-url: <url, or "not stated">
   company: <name>
   title: <title>
   location: <location, or "not stated">
   date-ingested: <YYYY-MM-DD>
   posting-age: <e.g. "18 days (posted 2026-06-05)", or "not stated">
   ---

   <the full job description as clean, readable markdown>
   ```

   Keep the body complete. Strip the page chrome — nav, cookie banners, legal footers — but
   don't summarise the description itself: a scoring variable you haven't invented yet (team
   newness, named leaders, responsible-AI framing) has to be derivable from this text later,
   and detail you drop can't be recovered without re-fetching a page that may be gone.

Read only what `reference/` holds, and write only into `state/`.

## A note on the visa gate

The decisive sponsorship statement usually lives in the body ("we are unable to provide visa
sponsorship"), and ingest is the first step that actually reads it — the upstream register
check only ever says "plausible". If the body refuses sponsorship the role has failed a hard
gate: flag it for rejection rather than letting a stored jd.md look like a clean pass.

## Example

Input: a Greenhouse URL for "Lead Business Analyst" at Graphcore, London-eligible, silent on visa.

Output: `state/roles/graphcore-business-analyst-lead/jd.md` — the six frontmatter fields filled
(location `Bristol, UK; Cambridge, UK; London, UK`; `posting-age` computed from the API's
first-published date), and a body carrying the complete About / responsibilities / requirements
text with page chrome removed.

## Done when

`state/roles/{key}/jd.md` exists; every frontmatter field is present and either real or the
literal `not stated`; the body is the full description as clean markdown; and the source was
read only this once. Show the path and the frontmatter block as evidence.
