#!/usr/bin/env python3
"""score-fit engine — the fixed, dumb scorer.

It hardcodes NO variable name. It loads the variable table from reference/fit-rubric.md
(D024), takes an evidence-anchored per-variable extraction (the LLM's judgment, produced
by the score-fit SKILL), and deterministically computes the two axes:
  * fit  (0-100, gated weighted SUM with a spine floor-gate, D023)
  * odds (0-1, anti-compensatory PRODUCT, from reference/odds-rubric.md)
then a band (D019) and a MACHINE screen (reject/flag/pass). It NEVER writes a human
verdict (CLAUDE.md) and stamps rubric-version on every score.md (D025).

Add a variable = add a row in fit-rubric.md. Change a weight/floor = edit the table.
The engine knows only a fixed vocabulary of KINDs (gate, spine, heavy, supporting,
penalty, comp-curve, multiplier, band-router) — a genuinely new operation is the only
thing that touches this code.

Python 3.8, stdlib only. Paths resolve relative to this file (mirrors scout.py).
"""
import argparse
import datetime
import json
import os
import re
import sys
import unicodedata

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.join(HERE, "..", "..", "..")
RUBRIC_PATH = os.path.join(REPO, "reference", "fit-rubric.md")
ODDS_PATH = os.path.join(REPO, "reference", "odds-rubric.md")
ROLES_DIR = os.path.join(REPO, "state", "roles")

ENUM_VALUE = {"MET": 1.0, "PARTIAL": 0.5, "UNMET": 0.0}
ADDITIVE_KINDS = ("spine", "heavy", "supporting")
KNOWN_KINDS = ("gate", "spine", "heavy", "supporting", "penalty",
               "comp-curve", "multiplier", "band-router")
ENUM_DOWNGRADE = {"MET": "PARTIAL", "PARTIAL": "UNMET", "UNMET": "UNMET"}


# ---------------------------------------------------------------------------
# Rubric loading (strict — fail loud, never silently drop a row)
# ---------------------------------------------------------------------------
def _frontmatter_value(text, key):
    m = re.search(r"(?m)^%s:\s*(.+)$" % re.escape(key), text)
    return m.group(1).strip() if m else None


def load_rubric(path=RUBRIC_PATH):
    text = open(path, encoding="utf-8").read()
    version = _frontmatter_value(text, "rubric-version") or "unknown"
    rows = []
    in_table = False
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if in_table:
                break  # the variable table has ended
            continue
        cells = [c.strip() for c in stripped.strip("|").split("|")]
        joined = "".join(cells)
        is_sep = bool(joined) and set(joined) <= set("-: ")
        if not in_table:
            if cells and cells[0] == "id" and "kind" in cells:
                in_table = True  # header row found
            continue
        if is_sep:
            continue  # the |---| separator row under the header
        if len(cells) != 6:
            raise ValueError("fit-rubric.md: variable-table row has %d cells, expected 6 "
                             "(fail loud, never silently drop): %r" % (len(cells), stripped))
        rid, variable, kind, weight, floor, how = cells
        if kind not in KNOWN_KINDS:
            raise ValueError("fit-rubric.md: row %r has unknown kind %r" % (rid, kind))
        rows.append({
            "id": rid, "variable": variable, "kind": kind,
            "weight": None if weight == "—" else float(weight),
            "floor": None if floor == "—" else float(floor),
            "how": how,
        })
    if not rows:
        raise ValueError("fit-rubric.md: no variable table rows parsed")
    comp_curve = []
    for m in re.finditer(r"(?m)^- *(\d+) *→ *(-?\d+)\s*$", text):
        comp_curve.append((int(m.group(1)), int(m.group(2))))
    comp_curve.sort()
    return {"version": version, "rows": rows, "comp_curve": comp_curve}


def load_odds_rubric(path=ODDS_PATH):
    text = open(path, encoding="utf-8").read()
    curve = []
    for m in re.finditer(r"(?m)^- *(\d+) *→ *([0-9.]+)\s*$", text):
        curve.append((int(m.group(1)), float(m.group(2))))
    curve.sort()
    return {"version": _frontmatter_value(text, "rubric-version") or "unknown",
            "recency_curve": curve}


def by_kind(rubric, *kinds):
    return [r for r in rubric["rows"] if r["kind"] in kinds]


# ---------------------------------------------------------------------------
# Evidence gate (Rulers) — a verdict's quote must appear in the JD body
# ---------------------------------------------------------------------------
_PUNCT_MAP = {
    "‘": "'", "’": "'", "‚": "'", "‛": "'",
    "“": '"', "”": '"', "„": '"',
    "‐": "-", "‑": "-", "‒": "-", "–": "-", "—": "-", "―": "-",
    " ": " ", " ": " ", "…": "...",
}


def _norm(s):
    # Real scraped JDs carry smart quotes, en/em dashes, NBSP, non-breaking hyphens —
    # normalise them so the evidence gate matches on meaning, not on codepoint.
    s = unicodedata.normalize("NFKC", s or "")
    s = "".join(_PUNCT_MAP.get(ch, ch) for ch in s)
    return re.sub(r"\s+", " ", s.lower()).strip()


def evidence_present(quote, jd_body):
    q = _norm(quote)
    return bool(q) and q in _norm(jd_body)


# ---------------------------------------------------------------------------
# Comp curve (linear interpolation between breakpoints)
# ---------------------------------------------------------------------------
def comp_penalty(stated_gbp, curve):
    if stated_gbp is None or not curve:
        return 0.0
    if stated_gbp <= curve[0][0]:
        return float(curve[0][1])
    if stated_gbp >= curve[-1][0]:
        return float(curve[-1][1])
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= stated_gbp <= x1:
            t = (stated_gbp - x0) / (x1 - x0)
            return round(y0 + t * (y1 - y0), 4)
    return 0.0


def recency_factor(days, curve):
    """Odds multiplier from posting age (a fresh role is more gettable). Linear between
    breakpoints; unknown age -> 1.0 (don't punish missing data). Affects ODDS, never fit."""
    if days is None or not curve:
        return 1.0
    if days <= curve[0][0]:
        return float(curve[0][1])
    if days >= curve[-1][0]:
        return float(curve[-1][1])
    for (x0, y0), (x1, y1) in zip(curve, curve[1:]):
        if x0 <= days <= x1:
            t = (days - x0) / (x1 - x0)
            return round(y0 + t * (y1 - y0), 4)
    return 1.0


def _posting_age_days(jd_text):
    m = re.search(r"(?m)^posting-age:\s*(\d+)\s*days", jd_text)
    return int(m.group(1)) if m else None


# ---------------------------------------------------------------------------
# Banding (D019 — v1 heuristic; thresholds documented in fit-rubric.md)
# ---------------------------------------------------------------------------
def band_for(fit, odds, prestige, spine_breached):
    if fit is None or fit < 50 or spine_breached:
        return None  # below the bar — a wanted role never sits here
    hi_fit = fit >= 70
    if odds >= 0.5:
        b = "safety" if hi_fit else "achievable"
    elif odds >= 0.25:
        b = "achievable" if hi_fit else "stretch"
    else:
        b = "stretch"
    # prestige band-router: high-fit + low-odds + prestige -> moonshot (never gated out)
    if prestige == "high" and hi_fit and odds < 0.25:
        b = "moonshot"
    return b


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------
def score(extraction, rubric, odds_rubric, jd_body, posting_days=None):
    flags = []
    result = {"rubric_version": rubric["version"],
              "odds_rubric_version": odds_rubric["version"]}

    # --- gates (any fail -> reject, no scoring) ---
    gate_results = {}
    failed = None
    for r in by_kind(rubric, "gate"):
        g = (extraction.get("gates") or {}).get(r["id"], "pass")
        gate_results[r["id"]] = g
        if g == "fail" and failed is None:
            failed = r["id"]
    result["gates"] = gate_results
    if failed:
        result.update({"screen": "reject", "pipeline_stage_failed": failed,
                       "fit": None, "odds": None, "band": None,
                       "flags": ["gate-failed:%s" % failed], "rows": [],
                       "spine_breached": False})
        return result
    result["pipeline_stage_failed"] = "none"

    # --- per-variable additive rows ---
    variables = extraction.get("variables") or {}
    rows_out, num, den = [], 0.0, 0.0
    spine_breached = False
    for r in by_kind(rubric, *ADDITIVE_KINDS):
        ex = variables.get(r["id"]) or {}
        verdict = ex.get("verdict", "CANNOT_ASSESS")
        quote = ex.get("quote", "")
        note = ""
        if verdict in ("MET", "PARTIAL"):
            if not evidence_present(quote, jd_body):
                verdict = ENUM_DOWNGRADE[verdict]
                note = "unverifiable-quote -> downgraded"
                flags.append("unverifiable:%s" % r["id"])
        if verdict == "CANNOT_ASSESS":
            if r["kind"] == "spine":
                # never silently drop a spine variable: treat as floor breach
                value = 0.0
                spine_breached = True
                note = "CANNOT_ASSESS on spine -> floor breach"
                flags.append("spine-cannot-assess:%s" % r["id"])
                num += value * r["weight"]; den += r["weight"]
            else:
                note = "CANNOT_ASSESS -> excluded from fit"
                rows_out.append({**r, "verdict": verdict, "value": None,
                                 "contribution": None, "quote": quote, "note": note})
                continue
        else:
            value = ENUM_VALUE[verdict]
            num += value * r["weight"]; den += r["weight"]
            if r["kind"] == "spine" and r["floor"] is not None and value < r["floor"]:
                spine_breached = True
                flags.append("spine-floor:%s(%.2f<%.2f)" % (r["id"], value, r["floor"]))
        rows_out.append({**r, "verdict": verdict, "value": value,
                         "contribution": round(value * r["weight"], 1),
                         "quote": quote, "note": note})
    fit_base = round(100.0 * num / den, 1) if den else 0.0

    # --- penalties ---
    pen_total = 0.0
    pens = extraction.get("penalties") or {}
    for r in by_kind(rubric, "penalty"):
        if pens.get(r["id"]):
            pen_total += abs(r["weight"])
            flags.append("penalty:%s(-%d)" % (r["id"], int(abs(r["weight"]))))

    # --- comp curve ---
    stated = (extraction.get("comp") or {}).get("stated_gbp")
    comp_pen = comp_penalty(stated, rubric["comp_curve"])
    if stated is None:
        flags.append("comp-unstated")

    # --- ESG x AI multiplier (evidence-gated; only genuine presence fires) ---
    esg = (extraction.get("multipliers") or {}).get("mult-esg-ai") or {}
    esg_mult, esg_fires = 1.0, False
    if esg.get("verdict") == "MET" and evidence_present(esg.get("quote", ""), jd_body):
        esg_mult, esg_fires = 1.25, True

    # --- compose fit in the fixed order, single final clamp ---
    fit = (fit_base - pen_total - comp_pen) * esg_mult
    fit = int(round(max(0.0, min(100.0, fit))))

    # --- odds (anti-compensatory product) ---
    o = extraction.get("odds") or {}
    sm = float(o.get("seniority_match", 0.0))
    rm = float(o.get("requirement_match", 0.0))
    cp = float(o.get("competition", 0.5))
    rf = recency_factor(posting_days, odds_rubric.get("recency_curve") or [])
    odds = round(sm * rm * cp * rf, 3)
    odds_conf = o.get("competition_confidence", "low")
    weeks = round(posting_days / 7.0, 1) if posting_days is not None else None
    if posting_days is None:
        flags.append("recency-unknown")
    elif rf < 0.75:
        flags.append("recency-aged:%swk(x%.2f)" % (weeks, rf))

    # --- guards / confidence flags ---
    guards = extraction.get("guards") or {}
    if guards.get("agency") in ("verify-live", "absorbed-risk"):
        flags.append("agency-%s" % guards["agency"])

    prestige = extraction.get("prestige", "med")
    band = band_for(fit, odds, prestige, spine_breached)

    # --- machine screen ---
    if spine_breached:
        screen = "reject"
        flags.insert(0, "spine-floor-breached")
    elif fit < 50:
        screen = "reject"
    elif fit >= 70 and not [f for f in flags if f.startswith(("unverifiable",
                            "recency-aged", "agency-", "spine-cannot-assess"))]:
        screen = "pass"
    else:
        screen = "flag"

    result.update({
        "screen": screen, "fit": fit, "fit_base": fit_base,
        "penalties": round(pen_total, 1), "comp_penalty": round(comp_pen, 1),
        "esg_fires": esg_fires, "odds": odds, "odds_confidence": odds_conf,
        "odds_factors": {"seniority_match": sm, "requirement_match": rm,
                         "competition": cp, "recency": rf},
        "recency": {"days": posting_days, "weeks": weeks, "factor": rf},
        "band": band, "prestige": prestige, "spine_breached": spine_breached,
        "rows": rows_out, "flags": flags,
    })
    return result


# ---------------------------------------------------------------------------
# score.md rendering
# ---------------------------------------------------------------------------
def _q(s, n=140):
    s = re.sub(r"\s+", " ", (s or "").strip())
    return (s[:n] + "…") if len(s) > n else s


def render_score_md(role_key, title, company, res, date_scored):
    L = []
    w = L.append
    w("---")
    w("name: %s" % role_key)
    w("description: score-fit MACHINE output for %s — %s. Two axes (fit + odds), a band, "
      "and a machine screen. NOT a verdict; the human pursue/on-ramp/no verdict is logged "
      "gut-first into the ledger and must not be anchored by this file." % (company, title))
    w("rubric-version: %s" % res["rubric_version"])
    w("odds-rubric-version: %s" % res["odds_rubric_version"])
    w("date-scored: %s" % date_scored)
    w("fit: %s" % ("null" if res["fit"] is None else res["fit"]))
    w("odds: %s" % ("null" if res["odds"] is None else res["odds"]))
    w("odds-confidence: %s" % res.get("odds_confidence", "low"))
    band_str = res["band"] or "—"
    if res["band"] and res.get("odds_confidence") == "low":
        band_str = "%s (provisional — odds low-confidence)" % res["band"]
    w("band: %s" % band_str)
    w("screen: %s" % res["screen"])
    w("pipeline-stage-failed: %s" % res.get("pipeline_stage_failed", "none"))
    w("spine-floor: %s" % ("breached" if res.get("spine_breached") else "ok"))
    rec = res.get("recency") or {}
    if rec.get("days") is None:
        rec_str = "unknown"
    elif (rec.get("factor") or 1.0) >= 1.0:
        rec_str = "fresh (%swk, ×1.0)" % rec.get("weeks")
    else:
        rec_str = "%swk (×%.2f)" % (rec.get("weeks"), rec.get("factor"))
    w("recency: %s" % rec_str)
    w("verdict:   # HUMAN field — score-fit NEVER writes this (CLAUDE.md)")
    w("---")
    w("")
    w("## Screen")
    for gid, g in res["gates"].items():
        w("- %s: **%s**" % (gid, g))
    if res["screen"] == "reject" and res.get("pipeline_stage_failed", "none") != "none":
        w("\n**Gated out** at `%s` — not scored." % res["pipeline_stage_failed"])
        w("\n_score.md is the machine screen; the human verdict is logged gut-first, never anchored by this file._")
        return "\n".join(L) + "\n"

    w("\n## Fit — %s/100 (rubric v%s)" % (res["fit"], res["rubric_version"]))
    w("base %.1f − penalties %.1f − comp %.1f, ×ESG-AI %s → **%s**"
      % (res["fit_base"], res["penalties"], res["comp_penalty"],
         "1.25" if res["esg_fires"] else "1.0", res["fit"]))
    w("\n| variable | kind | weight | verdict | value | contribution | evidence |")
    w("|---|---|---|---|---|---|---|")
    for r in res["rows"]:
        w("| %s | %s | %s | %s | %s | %s | %s |" % (
            r["id"], r["kind"], "" if r["weight"] is None else int(r["weight"]),
            r["verdict"], "—" if r["value"] is None else r["value"],
            "—" if r["contribution"] is None else r["contribution"],
            _q(r["quote"]) or ("— " + r["note"] if r["note"] else "—")))
    if res["spine_breached"]:
        w("\n**Spine floor-gate: BREACHED** — a co-dominant spine trait is below its floor "
          "(D023); the role drops below the bar regardless of the weighted sum.")

    w("\n## Odds — %s (confidence: %s)" % (res["odds"], res.get("odds_confidence", "low")))
    f = res["odds_factors"]
    w("seniority_match %s × requirement_match %s × competition %s × recency %s "
      "(anti-compensatory product). competition is a v0 placeholder and recency decays with "
      "posting age — odds is directional, not yet decision-grade."
      % (f["seniority_match"], f["requirement_match"], f["competition"], f.get("recency", 1.0)))

    w("\n## Band: %s%s" % (res["band"] or "— (below bar)",
      "  _(provisional — odds low-confidence: competition is a v0 placeholder)_"
      if res["band"] and res.get("odds_confidence") == "low" else ""))

    if res["flags"]:
        w("\n## Flags")
        for fl in res["flags"]:
            w("- %s" % fl)
    w("\n_score.md is the machine screen; the human verdict is logged gut-first, never anchored by this file._")
    return "\n".join(L) + "\n"


def _read_jd(role_key):
    p = os.path.join(ROLES_DIR, role_key, "jd.md")
    text = open(p, encoding="utf-8").read()
    title = _frontmatter_value(text, "title") or role_key
    company = _frontmatter_value(text, "company") or ""
    posting_days = _posting_age_days(text)
    body = text.split("---", 2)[-1] if text.count("---") >= 2 else text
    return title, company, body, posting_days


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--role", required=True, help="role key under state/roles/")
    ap.add_argument("--extraction", help="path to extraction JSON (default: the role folder)")
    ap.add_argument("--date", default=datetime.date.today().isoformat())
    ap.add_argument("--rubric", default=RUBRIC_PATH)
    ap.add_argument("--odds-rubric", default=ODDS_PATH)
    ap.add_argument("--print", action="store_true", help="print score.md instead of writing")
    args = ap.parse_args()

    rubric = load_rubric(args.rubric)
    odds_rubric = load_odds_rubric(args.odds_rubric)
    title, company, jd_body, posting_days = _read_jd(args.role)
    ex_path = args.extraction or os.path.join(ROLES_DIR, args.role, "extraction.json")
    extraction = json.load(open(ex_path, encoding="utf-8"))

    res = score(extraction, rubric, odds_rubric, jd_body, posting_days)
    md = render_score_md(args.role, title, company, res, args.date)
    if args.print:
        sys.stdout.write(md)
    else:
        out = os.path.join(ROLES_DIR, args.role, "score.md")
        open(out, "w", encoding="utf-8").write(md)
        sys.stderr.write("Wrote %s — screen=%s fit=%s odds=%s band=%s\n"
                         % (out, res["screen"], res["fit"], res["odds"], res["band"]))


if __name__ == "__main__":
    main()
