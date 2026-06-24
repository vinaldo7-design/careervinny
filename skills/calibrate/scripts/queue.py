#!/usr/bin/env python3
"""Build and load the dashboard's role queue from state/roles/ + extraction + score."""
import html
import json
import os
import re

SCREEN_RANK = {"pass": 0, "flag": 1, "reject": 2}
BATCH_SIZE = 20


def _fm(text, key):
    m = re.search(r"(?m)^%s:\s*(.+)$" % re.escape(key), text)
    return m.group(1).strip() if m else ""


def _parse_frontmatter(text):
    out = {}
    if not text.startswith("---"):
        return out
    end = text.find("\n---", 3)
    if end == -1:
        return out
    for line in text[3:end].splitlines():
        m = re.match(r"^([a-zA-Z_-]+):\s*(.*)$", line)
        if m:
            out[m.group(1)] = m.group(2).strip()
    return out


def _already_labelled(repo_root):
    p = os.path.join(repo_root, "calibration-log.jsonl")
    if not os.path.exists(p):
        return set()
    seen = set()
    for line in open(p, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        try:
            seen.add(json.loads(line)["role_key"])
        except Exception:
            continue
    return seen


def build_queue(repo_root):
    labelled = _already_labelled(repo_root)
    roles_dir = os.path.join(repo_root, "state", "roles")
    if not os.path.isdir(roles_dir):
        return []
    rows = []
    for key in sorted(os.listdir(roles_dir)):
        if key in labelled or key.startswith("."):
            continue
        d = os.path.join(roles_dir, key)
        if not os.path.isdir(d):
            continue
        jd_p = os.path.join(d, "jd.md")
        sc_p = os.path.join(d, "score.md")
        if not (os.path.exists(jd_p) and os.path.exists(sc_p)):
            continue
        jd_fm = _parse_frontmatter(open(jd_p, encoding="utf-8").read())
        sc_fm = _parse_frontmatter(open(sc_p, encoding="utf-8").read())
        rows.append({
            "key": key,
            "company": jd_fm.get("company", ""),
            "title": jd_fm.get("title", ""),
            "location": jd_fm.get("location", ""),
            "posted": jd_fm.get("posting-age", ""),
            "screen": sc_fm.get("screen", "?"),
            "fit": sc_fm.get("fit", "?"),
            "band": sc_fm.get("band", "?"),
            "jd_path": jd_p,
        })
    rows.sort(key=lambda r: (SCREEN_RANK.get(r["screen"], 9), -int(str(r["fit"]).split()[0]) if str(r["fit"]).isdigit() else 0))
    return rows[:BATCH_SIZE]


def load_role(repo_root, role_key):
    d = os.path.join(repo_root, "state", "roles", role_key)
    jd_md = open(os.path.join(d, "jd.md"), encoding="utf-8").read()
    extraction = json.load(open(os.path.join(d, "extraction.json"), encoding="utf-8"))
    score_md = open(os.path.join(d, "score.md"), encoding="utf-8").read()
    return {
        "key": role_key,
        "jd_md": jd_md,
        "jd_html_safe": html.escape(jd_md),
        "extraction": extraction,
        "score_md": score_md,
        "score_frontmatter": _parse_frontmatter(score_md),
    }
