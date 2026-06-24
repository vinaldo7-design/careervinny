#!/usr/bin/env python3
"""Persistent batch counter + rubric snapshot."""
import os
import shutil


def _current_path(repo_root):
    return os.path.join(repo_root, "state", "batches", "current.txt")


def current_batch_id(repo_root):
    p = _current_path(repo_root)
    if not os.path.exists(p):
        return 1
    try:
        with open(p, encoding="utf-8") as fh:
            return int(fh.read().strip())
    except (ValueError, OSError):
        return 1


def _set_batch_id(repo_root, batch_id):
    p = _current_path(repo_root)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as fh:
        fh.write(str(int(batch_id)))


def advance_batch_id(repo_root):
    new = current_batch_id(repo_root) + 1
    _set_batch_id(repo_root, new)
    return new


def snapshot_rubric(repo_root, batch_id):
    src = os.path.join(repo_root, "reference", "fit-rubric.md")
    if not os.path.exists(src):
        return
    dst_dir = os.path.join(repo_root, "state", "batches", str(int(batch_id)))
    os.makedirs(dst_dir, exist_ok=True)
    shutil.copy2(src, os.path.join(dst_dir, "rubric-before.md"))
