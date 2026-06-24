#!/usr/bin/env python3
"""Fixture tests for the score-fit engine — deterministic, no network.
Loads the REAL reference/fit-rubric.md + odds-rubric.md (so it also validates the live
table), feeds synthetic evidence-anchored extractions, asserts the math. Run:
    python3 test_scorer.py
"""
import copy
import scorer

RUBRIC = scorer.load_rubric()
ODDS = scorer.load_odds_rubric()

JD = ("We are hiring a Data and AI Strategy Manager in London. You will advise C-suite "
      "executives and shape the responsible AI and agentic LLM strategy. There is a legible "
      "path to people leadership with direct reports within two years. Your judgment shapes "
      "the roadmap. The role is client-facing with workshops and senior stakeholders. You "
      "lead a small team while still doing the craft, surrounded by elite peers. You own the "
      "pitch and the statement of work bundled with the strategy at a large, stable, "
      "successful firm with strong AI governance and AI ethics practices.")

# A fully-MET extraction whose quotes are all substrings of JD.
def base():
    return copy.deepcopy({
        "gates": {r["id"]: "pass" for r in scorer.by_kind(RUBRIC, "gate")},
        "variables": {
            "frontier-strategy": {"verdict": "MET", "quote": "shape the responsible AI and agentic LLM strategy"},
            "mgmt-ladder": {"verdict": "MET", "quote": "legible path to people leadership with direct reports within two years"},
            "intellectual-agency": {"verdict": "MET", "quote": "Your judgment shapes the roadmap"},
            "client-facing": {"verdict": "MET", "quote": "client-facing with workshops and senior stakeholders"},
            "player-coach": {"verdict": "MET", "quote": "lead a small team while still doing the craft"},
            "peer-bar": {"verdict": "MET", "quote": "surrounded by elite peers"},
            "origination-bd": {"verdict": "MET", "quote": "own the pitch and the statement of work bundled with the strategy"},
            "firm-stability": {"verdict": "MET", "quote": "large, stable, successful firm"},
        },
        "penalties": {"pen-no-agency": False, "pen-frontier-free": False},
        "comp": {"stated_gbp": None},
        "multipliers": {"mult-esg-ai": {"verdict": "UNMET", "quote": ""}},
        "prestige": "high",
        "odds": {"seniority_match": 1.0, "requirement_match": 1.0, "odds_confidence": "low"},
        "guards": {"recency": "ok", "agency": "clear"},
    })


fails = []
def check(name, cond):
    print(("PASS" if cond else "FAIL"), name)
    if not cond:
        fails.append(name)


# --- rubric parse integrity ---
add = [r for r in RUBRIC["rows"] if r["kind"] in scorer.ADDITIVE_KINDS]
check("21 variable rows parsed", len(RUBRIC["rows"]) == 21)
check("additive weights sum to 100", sum(r["weight"] for r in add) == 100)
check("two spine rows with floor 0.4",
      sorted(r["floor"] for r in RUBRIC["rows"] if r["kind"] == "spine") == [0.4, 0.4])
check("comp curve has 5 breakpoints", len(RUBRIC["comp_curve"]) == 5)

# --- comp curve interpolation ---
cc = RUBRIC["comp_curve"]
check("comp 70k -> -15", scorer.comp_penalty(70000, cc) == -15)
check("comp 85k -> -7.5", scorer.comp_penalty(85000, cc) == -7.5)
check("comp 100k+ -> 0", scorer.comp_penalty(120000, cc) == 0)
check("comp 60k -> -20", scorer.comp_penalty(60000, cc) == -20)
check("comp unstated -> 0", scorer.comp_penalty(None, cc) == 0)

# --- evidence gate ---
check("evidence present", scorer.evidence_present("advise C-suite executives", JD))
check("evidence absent", not scorer.evidence_present("quantum blockchain synergy", JD))

# --- fully-MET role: fit 100, pass, safety band ---
r = scorer.score(base(), RUBRIC, ODDS, JD)
check("fully-MET fit == 100", r["fit"] == 100)
check("fully-MET screen pass", r["screen"] == "pass")
check("fully-MET odds == 1.0 (seniority×requirement, no competition)", r["odds"] == 1.0)
check("fully-MET band safety", r["band"] == "safety")
check("no spine breach", r["spine_breached"] is False)

# --- gate fail -> reject, no fit ---
e = base(); e["gates"]["comp-floor"] = "fail"
r = scorer.score(e, RUBRIC, ODDS, JD)
check("gate fail -> screen reject", r["screen"] == "reject")
check("gate fail -> fit None", r["fit"] is None)
check("gate fail -> pipeline-stage-failed", r["pipeline_stage_failed"] == "comp-floor")

# --- frontier UNMET -> spine floor breach -> reject, no band (the negative-control shape) ---
e = base(); e["variables"]["frontier-strategy"] = {"verdict": "UNMET", "quote": ""}
r = scorer.score(e, RUBRIC, ODDS, JD)
check("frontier UNMET -> spine breached", r["spine_breached"] is True)
check("spine breach -> screen reject", r["screen"] == "reject")
check("spine breach -> band None", r["band"] is None)

# --- evidence-gate downgrade: MET with absent quote -> PARTIAL + flag ---
e = base(); e["variables"]["frontier-strategy"] = {"verdict": "MET", "quote": "no such text in jd"}
r = scorer.score(e, RUBRIC, ODDS, JD)
frow = [x for x in r["rows"] if x["id"] == "frontier-strategy"][0]
check("absent-quote MET downgraded to PARTIAL", frow["verdict"] == "PARTIAL")
check("unverifiable flag raised", any(f.startswith("unverifiable:frontier-strategy") for f in r["flags"]))

# --- ESG x AI multiplier fires (evidence-gated) ---
e = base()
e["variables"] = {k: {"verdict": "PARTIAL", "quote": v["quote"]} for k, v in e["variables"].items()}
e["multipliers"]["mult-esg-ai"] = {"verdict": "MET", "quote": "AI governance and AI ethics"}
r = scorer.score(e, RUBRIC, ODDS, JD)
# all PARTIAL -> base 50; spine 0.5 >= 0.4 floor (no breach); x1.25 -> 62 (capped at 100)
check("ESG multiplier fires", r["esg_fires"] is True)
check("all-PARTIAL base 50 x1.25 -> 62 (round)", r["fit"] == 62)
check("all-PARTIAL no spine breach", r["spine_breached"] is False)

# --- non-spine CANNOT_ASSESS excluded from denominator (no penalty) ---
e = base(); e["variables"]["client-facing"] = {"verdict": "CANNOT_ASSESS", "quote": ""}
r = scorer.score(e, RUBRIC, ODDS, JD)
check("non-spine CANNOT_ASSESS still fit 100 (excluded, not penalised)", r["fit"] == 100)

# --- spine CANNOT_ASSESS -> breach (never silently dropped) ---
e = base(); e["variables"]["mgmt-ladder"] = {"verdict": "CANNOT_ASSESS", "quote": ""}
r = scorer.score(e, RUBRIC, ODDS, JD)
check("spine CANNOT_ASSESS -> breach", r["spine_breached"] is True)
check("spine CANNOT_ASSESS flag", any(f.startswith("spine-cannot-assess:mgmt-ladder") for f in r["flags"]))

# --- recency is a STALENESS GUARD (not an odds factor) ---
r_fresh = scorer.score(base(), RUBRIC, ODDS, JD, posting_days=7)
r_stale = scorer.score(base(), RUBRIC, ODDS, JD, posting_days=scorer.STALE_DAYS + 1)
check("recency does NOT change odds (fresh==stale==1.0)", r_fresh["odds"] == r_stale["odds"] == 1.0)
check("stale role flagged likely-closed", any(f.startswith("likely-closed") for f in r_stale["flags"]))
check("stale role band is null (held)", r_stale["band"] is None)
check("stale role screen flag", r_stale["screen"] == "flag")
check("fresh role screen pass", r_fresh["screen"] == "pass")
check("unknown posting-age: no flag, screen pass",
      "likely-closed:verify-live" not in scorer.score(base(), RUBRIC, ODDS, JD)["flags"]
      and scorer.score(base(), RUBRIC, ODDS, JD)["screen"] == "pass")

# --- evidence gate normalises Unicode punctuation (real scraped JDs) ---
JD_UNI = "We report to the C‑suite and value Accenture’s “responsible” culture — truly."
check("evidence gate: non-breaking hyphen matches ascii", scorer.evidence_present("report to the c-suite", JD_UNI))
check("evidence gate: curly quotes/apostrophe match ascii", scorer.evidence_present('accenture\'s "responsible" culture', JD_UNI))

# --- rubric parser fails LOUD on a malformed table row (never silently drops) ---
import os as _os, tempfile as _tf
_bad = ("---\nrubric-version: 9\n---\n"
        "| id | variable | kind | weight | floor | how-to-read |\n"
        "|----|----------|------|--------|-------|-------------|\n"
        "| x | X | spine | 30 | 0.4 | ok |\n"
        "| y | Y | spine | 20 | 0.4 | has | a stray pipe |\n")
_p = _os.path.join(_tf.gettempdir(), "bad_rubric_scorefit.md")
open(_p, "w", encoding="utf-8").write(_bad)
_raised = False
try:
    scorer.load_rubric(_p)
except ValueError:
    _raised = True
check("malformed rubric row fails loud (not silently dropped)", _raised)

print()
print("FAILED:", fails if fails else "none")
raise SystemExit(1 if fails else 0)
