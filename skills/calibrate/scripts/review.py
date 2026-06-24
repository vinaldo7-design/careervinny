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

ALL_VERDICTS = ("pursue", "on-ramp", "no")

ORD_VERDICT = {"pursue": 3, "on-ramp": 2, "no": 0}
ORD_BAND = {"safety": 4, "achievable": 3, "stretch": 2, "moonshot": 1}
DIVERGENCE_THRESHOLD = 3


def _read_log():
    if not os.path.exists(LOG):
        return []
    out = []
    with open(LOG, encoding="utf-8") as fh:
        for line in fh:
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
    with open(RUBRIC, encoding="utf-8") as fh:
        content = fh.read()
    m = re.search(r"(?m)^rubric-version:\s*(\S+)", content)
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
        _parts = (r.get("machine_band") or "").split()
        mb = _parts[0] if _parts else ""
        mo = 0 if r.get("machine_screen") == "reject" else ORD_BAND.get(mb)
        if vo is not None and mo is not None and abs(vo - mo) > 1:
            divs.append({"type": "band-distance>1", "role_key": r.get("role_key"),
                         "reason": r.get("reason"), "distance": abs(vo - mo)})
    return {"by_variable": by_var, "divergences": divs, "count": len(rows)}


def _industry_for(role_key, repo_root=None):
    """Return the industry half of the domain tag from state/roles/<key>/jd.md frontmatter.

    Falls back to "unknown" if the file is missing or has no domain tag.
    """
    if repo_root is None:
        repo_root = REPO_ROOT
    jd_path = os.path.join(repo_root, "state", "roles", role_key, "jd.md")
    if not os.path.exists(jd_path):
        return "unknown"
    try:
        with open(jd_path, encoding="utf-8") as fh:
            content = fh.read()
    except OSError:
        return "unknown"
    m = re.search(r"(?m)^domain:\s*(\S+)", content)
    if not m:
        return "unknown"
    domain = m.group(1)
    # domain is "pharma:ml-research" → industry is "pharma"
    return domain.split(":")[0] if ":" in domain else domain


def batch_summary(rows, repo_root=None):
    """Return a structured overview dict for a list of calibration-log rows.

    Parameters
    ----------
    rows:
        List of dicts as stored in calibration-log.jsonl.
    repo_root:
        Override the repository root (used in tests).

    Returns
    -------
    dict with keys: count, verdict_mix, by_industry, machine_fit_by_verdict,
    divergences, proposed_deltas_summary.
    """
    if repo_root is None:
        repo_root = REPO_ROOT

    # --- counts -------------------------------------------------------
    verdict_mix = {v: 0 for v in ALL_VERDICTS}
    for r in rows:
        v = r.get("verdict")
        if v in verdict_mix:
            verdict_mix[v] += 1

    # --- by_industry --------------------------------------------------
    by_industry = {}
    for r in rows:
        industry = (
            r.get("industry")
            or (r.get("extraction_snapshot") or {}).get("industry")
            or _industry_for(r.get("role_key", ""), repo_root)
        )
        slot = by_industry.setdefault(industry, {
            "count": 0,
            "verdict_mix": {v: 0 for v in ALL_VERDICTS},
            "_fit_pursue": [],
            "_fit_no": [],
        })
        slot["count"] += 1
        v = r.get("verdict")
        if v in slot["verdict_mix"]:
            slot["verdict_mix"][v] += 1
        fit_raw = r.get("machine_fit")
        try:
            fit_int = int(fit_raw)
        except (TypeError, ValueError):
            fit_int = None
        if fit_int is not None:
            if v == "pursue":
                slot["_fit_pursue"].append(fit_int)
            elif v == "no":
                slot["_fit_no"].append(fit_int)

    # Compute means and drop the private accumulator lists
    def _mean_or_none(lst):
        return sum(lst) / len(lst) if lst else None

    clean_by_industry = {}
    for ind, slot in by_industry.items():
        clean_by_industry[ind] = {
            "count": slot["count"],
            "verdict_mix": slot["verdict_mix"],
            "mean_fit_pursue": _mean_or_none(slot["_fit_pursue"]),
            "mean_fit_no": _mean_or_none(slot["_fit_no"]),
        }

    # --- machine_fit_by_verdict ---------------------------------------
    fit_buckets = {v: [] for v in ALL_VERDICTS}
    for r in rows:
        v = r.get("verdict")
        if v not in fit_buckets:
            continue
        try:
            fit_int = int(r.get("machine_fit"))
        except (TypeError, ValueError):
            continue
        fit_buckets[v].append(fit_int)

    def _stats(lst):
        if not lst:
            return {"mean": None, "n": 0, "min": None, "max": None}
        return {
            "mean": sum(lst) / len(lst),
            "n": len(lst),
            "min": min(lst),
            "max": max(lst),
        }

    machine_fit_by_verdict = {v: _stats(fit_buckets[v]) for v in ALL_VERDICTS}

    # --- divergences (re-use summarise logic) -------------------------
    full_summary = summarise(rows)
    divergences = []
    for d in full_summary["divergences"]:
        divergences.append({
            "role_key": d.get("role_key"),
            "verdict": next((r.get("verdict") for r in rows if r.get("role_key") == d.get("role_key")), None),
            "machine_band": next((r.get("machine_band") for r in rows if r.get("role_key") == d.get("role_key")), None),
            "machine_screen": next((r.get("machine_screen") for r in rows if r.get("role_key") == d.get("role_key")), None),
            "distance": d.get("distance"),
            "reason": d.get("reason"),
        })

    # --- proposed_deltas_summary --------------------------------------
    proposed_deltas_summary = []
    for vid, slot in sorted(full_summary["by_variable"].items()):
        if slot["pursue_at_unmet"] >= DIVERGENCE_THRESHOLD:
            proposed_deltas_summary.append({
                "variable": vid,
                "kind": "weight-up",
                "count": slot["pursue_at_unmet"],
                "sample_roles": slot["samples"][:6],
            })
        if slot["no_at_met"] >= DIVERGENCE_THRESHOLD:
            proposed_deltas_summary.append({
                "variable": vid,
                "kind": "weight-down",
                "count": slot["no_at_met"],
                "sample_roles": slot["samples"][:6],
            })

    return {
        "count": len(rows),
        "verdict_mix": verdict_mix,
        "by_industry": clean_by_industry,
        "machine_fit_by_verdict": machine_fit_by_verdict,
        "divergences": divergences,
        "proposed_deltas_summary": proposed_deltas_summary,
    }


def propose_deltas(summary, rubric_version):
    today = datetime.date.today().isoformat()
    out = []
    n = 1
    for vid, slot in sorted(summary["by_variable"].items()):
        if slot["pursue_at_unmet"] >= DIVERGENCE_THRESHOLD:
            out.append(_delta(today, n, vid, "weight-up",
                "Vinay said pursue on %d roles where %s extracted UNMET. Variable likely under-weighted "
                "or its how-to-read misses the signal. Sample roles: %s." %
                (slot["pursue_at_unmet"], vid, ", ".join(slot["samples"][:6])),
                rubric_version)); n += 1
        if slot["no_at_met"] >= DIVERGENCE_THRESHOLD:
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


def _print_batch_summary(bs):
    """Print a human-readable batch summary to stdout."""
    print("=== batch summary (%d verdicts) ===" % bs["count"])
    vm = bs["verdict_mix"]
    print("verdict mix:  pursue=%d  on-ramp=%d  no=%d" %
          (vm.get("pursue", 0), vm.get("on-ramp", 0), vm.get("no", 0)))
    print()
    print("--- by industry ---")
    for ind, slot in sorted(bs["by_industry"].items()):
        ivm = slot["verdict_mix"]
        mfp = ("%.1f" % slot["mean_fit_pursue"]) if slot["mean_fit_pursue"] is not None else "n/a"
        mfn = ("%.1f" % slot["mean_fit_no"]) if slot["mean_fit_no"] is not None else "n/a"
        print("  %-20s n=%d  pursue=%d on-ramp=%d no=%d  fit(pursue)=%s fit(no)=%s" % (
            ind, slot["count"],
            ivm.get("pursue", 0), ivm.get("on-ramp", 0), ivm.get("no", 0),
            mfp, mfn))
    print()
    print("--- machine_fit by verdict ---")
    for v in ALL_VERDICTS:
        st = bs["machine_fit_by_verdict"][v]
        if st["n"] == 0:
            print("  %-10s  n=0" % v)
        else:
            print("  %-10s  n=%d  mean=%.1f  min=%s  max=%s" % (
                v, st["n"], st["mean"], st["min"], st["max"]))
    print()
    divs = bs["divergences"]
    print("--- divergences (band-distance > 1): %d ---" % len(divs))
    for d in divs:
        print("  %-30s verdict=%-8s band=%-12s screen=%-6s dist=%s" % (
            d.get("role_key", "?"), d.get("verdict", "?"),
            d.get("machine_band", "?"), d.get("machine_screen", "?"),
            d.get("distance", "?")))
    print()
    pds = bs["proposed_deltas_summary"]
    print("--- proposed_deltas_summary: %d entries ---" % len(pds))
    for entry in pds:
        print("  %-22s %-12s count=%d  samples=%s" % (
            entry["variable"], entry["kind"], entry["count"],
            ", ".join(entry["sample_roles"][:3])))


def main():
    batch_mode = "--batch-summary" in sys.argv
    rows = _read_log()
    if not rows:
        print("calibration-log.jsonl is empty.")
        return 0
    if batch_mode:
        tail = rows[-20:] if len(rows) > 20 else rows
        bs = batch_summary(tail)
        _print_batch_summary(bs)
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
