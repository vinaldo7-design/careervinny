#!/usr/bin/env python3
"""Background subprocess manager for the discovery scout."""
import json
import os
import secrets
import subprocess
import sys


def _state_dir(repo_root):
    d = os.path.join(repo_root, "state", "scout")
    os.makedirs(d, exist_ok=True)
    return d


def _state_path(repo_root):
    return os.path.join(_state_dir(repo_root), "current.json")


def _load(repo_root):
    p = _state_path(repo_root)
    if not os.path.exists(p):
        return None
    try:
        with open(p, encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        return None


def _save(repo_root, data):
    with open(_state_path(repo_root), "w", encoding="utf-8") as fh:
        json.dump(data, fh)


def _pid_alive(pid):
    if int(pid) <= 0:
        return False
    try:
        os.kill(int(pid), 0)
        return True
    except (ProcessLookupError, PermissionError, ValueError):
        return False


def start(domains, repo_root):
    existing = _load(repo_root)
    if existing and _pid_alive(existing.get("pid", 0)) and not _completed(existing, repo_root):
        raise RuntimeError("scout already running (job_id=%s)" % existing.get("job_id"))
    if not isinstance(domains, (list, tuple)) or not domains or not all(isinstance(x, str) and x for x in domains):
        raise ValueError("domains must be a non-empty list of non-empty strings")
    job_id = secrets.token_hex(6)
    log_path = os.path.join(_state_dir(repo_root), "%s.log" % job_id)
    scout_py = os.path.join(repo_root, "skills", "discovery", "scripts", "scout.py")
    cmd = [sys.executable, scout_py] + list(domains)
    log_fh = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(cmd, stdout=log_fh, stderr=subprocess.STDOUT, cwd=repo_root)
    info = {"job_id": job_id, "pid": proc.pid, "log_path": log_path,
            "domains": list(domains), "returncode": None}
    _save(repo_root, info)
    return info


def _completed(info, repo_root):
    if info.get("returncode") is not None:
        return True
    pid = info.get("pid", 0)
    if int(pid) <= 0:
        return False
    # Try waitpid with WNOHANG first — this handles the zombie case where
    # os.kill(pid, 0) returns True but the process has already exited.
    try:
        child_pid, wstatus = os.waitpid(pid, os.WNOHANG)
        if child_pid != 0:
            # Process has exited and was reaped.
            info["returncode"] = (os.waitstatus_to_exitcode(wstatus)
                                  if hasattr(os, "waitstatus_to_exitcode") else (wstatus >> 8))
            _save(repo_root, info)
            return True
        # child_pid == 0 means the process is still running.
        return False
    except (ChildProcessError, OSError):
        # ECHILD: process was already reaped elsewhere or not a child.
        # In that case fall back to pid-alive check.
        if not _pid_alive(pid):
            info["returncode"] = 0
            _save(repo_root, info)
            return True
        return False


def status(job_id, repo_root):
    info = _load(repo_root)
    if info is None:
        return {"job_id": None, "state": "none", "returncode": None, "log_tail": ""}
    if job_id is not None and info.get("job_id") != job_id:
        return {"job_id": None, "state": "none", "returncode": None, "log_tail": ""}
    done = _completed(info, repo_root)
    log_tail = ""
    lp = info.get("log_path")
    if lp and os.path.exists(lp):
        with open(lp, encoding="utf-8") as fh:
            log_tail = "".join(fh.readlines()[-20:])
    state = "running"
    if done:
        state = "done" if (info.get("returncode") == 0) else "failed"
    return {"job_id": info.get("job_id"), "state": state, "returncode": info.get("returncode"),
            "log_tail": log_tail, "domains": info.get("domains", [])}
