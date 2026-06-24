#!/usr/bin/env python3
"""Render roles.md from the cached kept-set (kept.json). NO network, NO scout run.

Ordering (by calibration value, not firm):
  uk-ai-specialist -> energy -> fintech/enterprise -> tech-scaleup -> vendor/lab,
  and within each vertical by frontier+agency signal strength (best first).
vendor/lab is capped to ~20 best-signal roles (<=5/firm); the rest are held back
(still present in kept.json, available on request). All other verticals render in full.
This script READS the cache and WRITES roles.md only — it never scores or writes weights.
"""
import argparse
import json
from collections import defaultdict, OrderedDict

CACHE = "/Users/vinaynair/Downloads/ssdhj/scout/kept.json"
OUTFILE = "/Users/vinaynair/Downloads/ssdhj/scout/roles.md"
VERTICAL_ORDER = ["uk-ai-specialist", "energy", "fintech/enterprise", "tech-scaleup", "vendor/lab"]
VENDOR_FIRM_CAP = 5

COVERAGE_NOTE = (
    "60 live public ATS boards (Greenhouse / Lever / Ashby). THIN or ABSENT "
    "verticals — these post mainly via Workday/Taleo, which expose no public API: "
    "**management consulting** (Accenture, BCG, McKinsey, Deloitte), **large banks** "
    "(JPMorgan, Goldman, Barclays, HSBC), **big pharma** (GSK, AstraZeneca, Novartis), "
    "**telco**, and **publishing** (FT, Economist, Guardian were probed but are not on "
    "these APIs). Net effect: bullseye role-family #1 (consulting AI-strategy advisory) "
    "is under-represented here. Fintech/enterprise covers challenger banks, not "
    "tier-1 investment banks."
)


def frank(s):
    return 2 if s.startswith("named") else (1 if s.startswith("vague") else 0)


def arank(s):
    for k, v in (("high", 3), ("med", 2), ("low", 1)):
        if s.startswith(k):
            return v
    return 0


def score(r):
    return frank(r["frontier"]) + arank(r["agency"])


def role_block(n, r):
    comp = r["comp_disp"]
    if "flag" in r["comp_note"]:
        comp += " ⚠below £80k soft floor"
    return "\n".join([
        "**%d. %s — %s**  _(%s)_" % (n, r["company"], r["title"], r["vertical"]),
        "- meta: %s | comp: %s | visa: **%s** (%s) | %s" % (
            r["loc_display"] or "not stated", comp, r["visa_status"], r["visa_note"], r["url"]),
        "- loc-gate: %s (%s) | kw:`%s`" % (r["loc_decision"], r["loc_reason"], r["matched_kw"]),
        "- frontier: %s | ic_tell: %s | client_facing: %s | origination: %s" % (
            r["frontier"], r["ic_tell"], r["client_facing"], r["origination"]),
        "- agency: %s" % r["agency"],
        "- seniority: %s | esg_edge: %s" % (r["seniority"], r["esg_edge"]),
        "- networkability: — (tested separately)",
        '- quote: "%s"' % r["quote"],
        "",
    ])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--chunk", type=int, default=25)
    ap.add_argument("--vendor-cap", type=int, default=20, help="max vendor/lab roles surfaced")
    ap.add_argument("--out", default=OUTFILE)
    args = ap.parse_args()

    with open(CACHE, encoding="utf-8") as f:
        data = json.load(f)
    meta, recs = data["meta"], data["kept"]

    byv = defaultdict(list)
    for r in recs:
        byv[r["vertical"]].append(r)

    rendered, vendor_held, vendor_firms = [], 0, OrderedDict()
    for v in VERTICAL_ORDER:
        group = sorted(byv.get(v, []), key=lambda r: (-score(r), r["company"], r["title"]))
        if v == "vendor/lab":
            sel, firmc = [], defaultdict(int)
            for r in group:
                if len(sel) >= args.vendor_cap:
                    break
                if firmc[r["company"]] < VENDOR_FIRM_CAP:
                    sel.append(r)
                    firmc[r["company"]] += 1
                    vendor_firms[r["company"]] = 1
            vendor_held = len(group) - len(sel)
            group = sel
        rendered.extend(group)

    # flags recomputed over the FULL kept set
    visacheck = [r for r in recs if r["visa_status"] == "check"]
    undet = [r for r in recs if "UNDETERMINED" in r["loc_reason"]]
    locflag = [r for r in recs if ("flag" in r["loc_reason"] or "UNVERIFIED" in r["loc_reason"])]
    compflag = [r for r in recs if "flag" in r["comp_note"]]

    chunk = args.chunk
    breakdown = []
    for ci in range(0, len(rendered), chunk):
        grp = rendered[ci:ci + chunk]
        c = defaultdict(int)
        for r in grp:
            c[r["vertical"]] += 1
        breakdown.append((ci // chunk + 1, ci + 1, ci + len(grp), c))

    vendor_shown = len([r for r in rendered if r["vertical"] == "vendor/lab"])
    kbv = meta["kept_by_vertical"]

    O = []
    w = O.append
    w("# CareerVinny — batch scout roles (wide pull)\n")
    w("- **Run date:** %s" % meta["run_date"])
    w("- **Sponsor register:** %d rows, %d distinct normalised names (gov.uk, %s)" % (
        meta["nreg"], meta["ndistinct"], meta["run_date"]))
    w("- **Total roles pulled:** %d across %d boards" % (meta["total_pulled"], len(meta["source_report"])))
    w("- **Title-matched candidate pool:** %d" % meta["n_matched"])
    w("- **Kept after eligibility filter:** %d  (full set cached in kept.json)" % meta["n_kept"])
    w("- **Rendered for scoring:** %d" % len(rendered))
    w("- **Filtered out:** %d\n" % meta["n_filtered"])
    w("**Kept by vertical (full %d):** " % meta["n_kept"]
      + ", ".join("%s %d" % (k, kbv[k]) for k in sorted(kbv)) + "\n")
    w("**Render order (by calibration value, not firm):** uk-ai-specialist → energy → "
      "fintech/enterprise → tech-scaleup → vendor/lab. Within each vertical, ordered by "
      "frontier+agency signal strength (best first).\n")
    w("**vendor/lab held back:** %d of %d surfaced (best frontier+agency, ≤%d/firm across %d labs); "
      "the remaining %d are held back and available on request — the full set stays in kept.json.\n" % (
          vendor_shown, kbv.get("vendor/lab", 0), VENDOR_FIRM_CAP, len(vendor_firms), vendor_held))
    w("**Coverage:** " + COVERAGE_NOTE + "\n")

    w("**By-chunk vertical mix:**")
    w("| chunk | roles | uk-ai-specialist | energy | fintech/enterprise | tech-scaleup | vendor/lab |")
    w("|---|---|---|---|---|---|---|")
    for k, a, b, c in breakdown:
        w("| %d | %d–%d | %d | %d | %d | %d | %d |" % (
            k, a, b, c["uk-ai-specialist"], c["energy"], c["fintech/enterprise"],
            c["tech-scaleup"], c["vendor/lab"]))
    w("")

    gf, gs = meta["gate_filtered"], meta["gate_sole"]
    w("## Gate-pressure table (reporting only — never acted on)")
    w("| gate | roles filtered | sole-killer |")
    w("|---|---|---|")
    for g in ("visa", "location", "comp"):
        w("| %s | %d | %d |" % (g, gf.get(g, 0), gs.get(g, 0)))
    w("\n_Market reveals what EXISTS; only the human's verdict reveals what he WANTS. "
      "Weights move on verdicts, never on these volumes. Caveat: register membership is "
      "necessary, not sufficient — licensed ≠ will sponsor THIS role._\n")

    w("## Eligibility flags (over the full %d kept; verify before pursuing)" % meta["n_kept"])
    w("- **visa = check** (large/multinational, not exact-matched — verify on register): %d" % len(visacheck))
    w("- **location flagged** (UK-remote / agnostic remote — confirm London/in-person): %d" % len(locflag))
    w("- **location UNDETERMINED** (no location on posting): %d" % len(undet))
    w("- **comp flagged** (stated GBP below £80k soft floor): %d" % len(compflag))
    if visacheck:
        w("\n  visa-check: " + "; ".join("%s — %s" % (r["company"], r["title"]) for r in visacheck[:20]))
    w("")

    w("## Roles (%d rendered) — raw signal fields, NO scoring band (pre-calibration)\n" % len(rendered))
    for ci in range(0, len(rendered), chunk):
        grp = rendered[ci:ci + chunk]
        w("### Chunk %d (roles %d–%d)\n" % (ci // chunk + 1, ci + 1, ci + len(grp)))
        for i, r in enumerate(grp, ci + 1):
            w(role_block(i, r))

    w("## Appendix — source report")
    w("| provider | slug | company | vertical | status | pulled | title-matched |")
    w("|---|---|---|---|---|---|---|")
    for row in meta["source_report"]:
        w("| %s | %s | %s | %s | %s | %d | %d |" % tuple(row))
    w("")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(O))

    # console summary — the by-chunk breakdown the user asked to see
    print("Rendered %d roles -> %s" % (len(rendered), args.out))
    print("Order: " + " -> ".join(VERTICAL_ORDER))
    print("vendor/lab: %d surfaced (<=%d/firm, %d labs), %d held back" % (
        vendor_shown, VENDOR_FIRM_CAP, len(vendor_firms), vendor_held))
    print("\nBy-chunk vertical mix:")
    print("chunk | roles  | uk-ai | energy | fintech | tech-scaleup | vendor/lab")
    for k, a, b, c in breakdown:
        print("  %2d  | %3d-%-3d| %5d | %6d | %7d | %12d | %10d" % (
            k, a, b, c["uk-ai-specialist"], c["energy"], c["fintech/enterprise"],
            c["tech-scaleup"], c["vendor/lab"]))


if __name__ == "__main__":
    main()
