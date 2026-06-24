#!/usr/bin/env python3
"""Read calibration-log.jsonl, summarise divergences per variable, and append
`status: proposed` deltas to reference/lessons.md. Gates are NEVER auto-edited;
the worst it does is propose a delta for a human to ratify."""
import datetime
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
LOG = os.path.join(REPO_ROOT, "calibration-log.jsonl")
LESSONS = os.path.join(REPO_ROOT, "reference", "lessons.md")
RUBRIC = os.path.join(REPO_ROOT, "reference", "fit-rubric.md")

ORD_VERDICT = {"pursue": 3, "on-ramp": 2, "no": 0}
ORD_BAND = {"safety": 4, "achievable": 3, "stretch": 2, "moonshot": 1}


def _read_log():
    if not os.path.exists(LOG):
        return []
    out = []
    for line in open(LOG, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except Exception:
            continue
    return out


def _rubric_version():
    if not os.path.exists(RUBRIC):
        return "unknown"
    m = re.search(r"(?m)^rubric-version:\s*(\S+)", open(RUBRIC, encoding="utf-8").read())
    return m.group(1) if m else "unknown"


def summarise(rows):
    by_var = {}
    divs = []
    for r in rows:
        ex = (r.get("extraction_snapshot") or {}).get("variables") or {}
        for vid, v in ex.items():
            slot = by_var.setdefault(vid, {"pursue_at_unmet": 0, "no_at_met": 0, "samples": []})
            verdict = r.get("verdict")
            ext = (v or {}).get("verdict")
            if verdict == "pursue" and ext == "UNMET":
                slot["pursue_at_unmet"] += 1
                slot["samples"].append(r.get("role_key"))
            elif verdict == "no" and ext == "MET":
                slot["no_at_met"] += 1
                slot["samples"].append(r.get("role_key"))
        vo = ORD_VERDICT.get(r.get("verdict"))
        mb = (r.get("machine_band") or "").split()[0]
        mo = 0 if r.get("machine_screen") == "reject" else ORD_BAND.get(mb)
        if vo is not None and mo is not None and abs(vo - mo) > 1:
            divs.append({"type": "band-distance>1", "role_key": r.get("role_key"),
                         "reason": r.get("reason"), "distance": abs(vo - mo)})
    return {"by_variable": by_var, "divergences": divs, "count": len(rows)}


def propose_deltas(summary, rubric_version):
    today = datetime.date.today().isoformat()
    out = []
    n = 1
    for vid, slot in sorted(summary["by_variable"].items()):
        if slot["pursue_at_unmet"] >= 3:
            out.append(_delta(today, n, vid, "weight-up",
                "Vinay said pursue on %d roles where %s extracted UNMET. Variable likely under-weighted "
                "or its how-to-read misses the signal. Sample roles: %s." %
                (slot["pursue_at_unmet"], vid, ", ".join(slot["samples"][:6])),
                rubric_version)); n += 1
        if slot["no_at_met"] >= 3:
            out.append(_delta(today, n, vid, "weight-down",
                "Vinay said no on %d roles where %s extracted MET. Variable likely over-weighted "
                "or its how-to-read fires on the wrong signal. Sample roles: %s." %
                (slot["no_at_met"], vid, ", ".join(slot["samples"][:6])),
                rubric_version)); n += 1
    return out


def _delta(date, n, vid, kind, signal, rubric_version):
    return (
        "\n## L%s-%d - %s - calibration:%s\n"
        "trigger: review of calibration-log.jsonl (rubric v%s)\n"
        "type: %s (propose-ratify)\n"
        "target: fit-rubric.md row id=%s\n"
        "signal: %s\n"
        "delta: PROPOSED — review the row, decide a weight nudge or how-to-read refinement; "
        "do NOT add or remove any gate row autonomously.\n"
        "status: proposed\n"
        % (date.replace("-", ""), n, vid, kind, rubric_version, kind, vid, signal))


def main():
    rows = _read_log()
    if not rows:
        print("calibration-log.jsonl is empty.")
        return 0
    summary = summarise(rows)
    print("=== calibration review ===")
    print("verdicts logged: %d" % summary["count"])
    print("divergences (band distance > 1): %d" % len(summary["divergences"]))
    for vid, slot in sorted(summary["by_variable"].items()):
        print("  %-22s pursue@UNMET=%d  no@MET=%d  n=%d" %
              (vid, slot["pursue_at_unmet"], slot["no_at_met"], len(slot["samples"])))
    deltas = propose_deltas(summary, _rubric_version())
    if not deltas:
        print("no delta thresholds met yet.")
        return 0
    with open(LESSONS, "a", encoding="utf-8") as f:
        f.write("\n<!-- calibration review %s — proposed deltas, ratify or reject -->\n" %
                datetime.date.today().isoformat())
        for d in deltas:
            f.write(d)
    print("appended %d status:proposed deltas to reference/lessons.md" % len(deltas))
    return 0


if __name__ == "__main__":
    sys.exit(main())
