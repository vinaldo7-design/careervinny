#!/usr/bin/env python3
"""Append-only event log for proposal status (deferred/accepted/rejected).

Current state of a proposal_id = latest event in the file. File is at
state/batches/proposal-events.jsonl. Never rewritten.
"""
import json
import os
import time


VALID_STATUSES = ("deferred", "accepted", "rejected")


def _path(repo_root):
    p = os.path.join(repo_root, "state", "batches")
    os.makedirs(p, exist_ok=True)
    return os.path.join(p, "proposal-events.jsonl")


def record_event(repo_root, proposal_id, status, batch_id, payload=None):
    if status not in VALID_STATUSES:
        raise ValueError("status must be one of %s" % (VALID_STATUSES,))
    row = {
        "proposal_id": proposal_id,
        "status": status,
        "batch_id": int(batch_id),
        "ts": int(time.time()),  # epoch seconds; deterministic order via file position
    }
    if payload is not None:
        row["payload"] = payload
    with open(_path(repo_root), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")


def _read_all(repo_root):
    p = _path(repo_root)
    if not os.path.exists(p):
        return []
    out = []
    with open(p, encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def currently_deferred(repo_root):
    events = _read_all(repo_root)
    latest = {}
    payloads = {}
    for ev in events:
        pid = ev.get("proposal_id")
        if not pid:
            continue
        latest[pid] = ev
        if ev.get("payload") is not None:
            payloads[pid] = ev["payload"]
    out = []
    for pid, ev in latest.items():
        if ev.get("status") == "deferred":
            out.append({
                "proposal_id": pid,
                "batch_id": ev.get("batch_id"),
                "payload": payloads.get(pid, {}),
            })
    return out
