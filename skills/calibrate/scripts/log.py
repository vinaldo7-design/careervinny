#!/usr/bin/env python3
"""Append-only writers for the calibration ledger and the structured log.

Two surfaces:
  * calibration-ledger.md — human-readable markdown rows (matches the legacy schema,
    plus a `key:<role-key>` token + `rubric:<n>` so machine guards can resolve rows).
  * calibration-log.jsonl — one JSON object per verdict (machine-readable).

Both are append-only (CLAUDE.md: never rewrite a past row).
"""
import json
import os
import re


def _ledger_path(repo_root):
    return os.path.join(repo_root, "calibration-ledger.md")


def _log_path(repo_root):
    return os.path.join(repo_root, "calibration-log.jsonl")


def count_ledger_rows(repo_root):
    n = 0
    if not os.path.exists(_ledger_path(repo_root)):
        return 0
    for line in open(_ledger_path(repo_root), encoding="utf-8"):
        line = line.strip()
        if not line.startswith("|"):
            continue
        first = line.strip("|").split("|", 1)[0].strip()
        if re.match(r"^\d+$", first):
            n += 1
    return n


def format_ledger_row(num, role, verdict, reason, rubric_version):
    """Build the markdown row. role is a dict with keys company/title/key.
    The role cell carries the human-readable name PLUS the machine-readable
    `key:<role-key>` and `rubric:<n>` tokens that the ledger guard parses."""
    role_cell = "%s — %s `key:%s` `rubric:%s`" % (
        role.get("company", ""), role.get("title", ""), role["key"], rubric_version)
    why = (reason or "").replace("|", "/").strip()
    return "| %d | %s | %s | %s | (machine reveal) | (computed on review) |\n" % (
        num, role_cell, verdict, why)


def append_ledger(repo_root, line):
    with open(_ledger_path(repo_root), "a", encoding="utf-8") as f:
        f.write(line)
    return count_ledger_rows(repo_root)


def append_log(repo_root, row):
    with open(_log_path(repo_root), "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")
