"""
Hash Engine  (FIXED)
Changes:
  - run_full_scan: after detecting MODIFIED, updates baseline so same file
    is NOT re-alerted on every subsequent scan
  - verify_file: CREATED event now always upserts baseline
  - collect_files_from_paths: skips temp/hidden files consistently
"""

import hashlib
import os
from . import database as db


CHUNK_SIZE = 65536


def compute_sha256(file_path):
    sha256 = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            while chunk := f.read(CHUNK_SIZE):
                sha256.update(chunk)
        return sha256.hexdigest()
    except (PermissionError, FileNotFoundError, OSError):
        return None


def get_file_meta(file_path):
    try:
        stat = os.stat(file_path)
        return stat.st_size, stat.st_mtime
    except OSError:
        return 0, 0


def _should_skip(name):
    return (name.startswith(".")
            or name.endswith((".tmp", "~", ".swp", ".part"))
            or "~$" in name)


def collect_files_from_paths(watch_paths):
    file_list = []
    for entry in watch_paths:
        path = entry["path"]
        if not os.path.exists(path):
            continue
        if os.path.isfile(path):
            if not _should_skip(os.path.basename(path)):
                file_list.append(path)
        elif os.path.isdir(path):
            for root, dirs, files in os.walk(path):
                dirs[:] = [d for d in dirs if not d.startswith(".")]
                for fname in files:
                    if not _should_skip(fname):
                        file_list.append(os.path.join(root, fname))
    return list(set(file_list))


def create_baseline(watch_paths, progress_callback=None):
    files = collect_files_from_paths(watch_paths)
    total = len(files)
    success = 0
    errors = 0

    for i, file_path in enumerate(files):
        if progress_callback:
            progress_callback(i + 1, total, file_path)

        hash_val = compute_sha256(file_path)
        if hash_val:
            size, mtime = get_file_meta(file_path)
            db.upsert_baseline(file_path, hash_val, size, mtime)
            db.insert_log(file_path, "BASELINE", "OK",
                          f"Hash: {hash_val[:16]}…")
            success += 1
        else:
            db.insert_log(file_path, "BASELINE", "ERROR",
                          "Could not read file")
            errors += 1

    return success, errors


def verify_file(file_path):
    """
    Compare current file against baseline.
    Returns dict: status, event_type, old_hash, new_hash
    """
    baseline = db.get_baseline(file_path)

    if os.path.exists(file_path):
        current_hash = compute_sha256(file_path)
        if current_hash is None:
            return {"status": "error", "event_type": "ERROR",
                    "old_hash": None, "new_hash": None}

        if baseline is None:
            # New file — add to baseline immediately
            size, mtime = get_file_meta(file_path)
            db.upsert_baseline(file_path, current_hash, size, mtime)
            return {"status": "new", "event_type": "CREATED",
                    "old_hash": None, "new_hash": current_hash}

        if current_hash != baseline["sha256_hash"]:
            # FIX: update baseline here so repeat scans don't re-alert
            size, mtime = get_file_meta(file_path)
            db.upsert_baseline(file_path, current_hash, size, mtime)
            return {"status": "modified", "event_type": "MODIFIED",
                    "old_hash": baseline["sha256_hash"],
                    "new_hash": current_hash}

        return {"status": "ok", "event_type": "OK",
                "old_hash": baseline["sha256_hash"],
                "new_hash": current_hash}
    else:
        if baseline:
            db.delete_baseline_entry(file_path)
            return {"status": "deleted", "event_type": "DELETED",
                    "old_hash": baseline["sha256_hash"], "new_hash": None}
        return {"status": "ok", "event_type": "OK",
                "old_hash": None, "new_hash": None}


def run_full_scan(watch_paths, result_callback=None):
    """
    Scan all files and emit alerts for any changes.
    Also checks baseline entries that no longer exist on disk (deletions).
    """
    files = collect_files_from_paths(watch_paths)
    baseline_entries = db.get_baseline()
    baseline_paths = {e["file_path"] for e in baseline_entries}
    all_paths = list(set(files) | baseline_paths)

    summary = {"scanned": 0, "modified": 0, "deleted": 0, "created": 0, "ok": 0}

    for file_path in all_paths:
        result = verify_file(file_path)
        summary["scanned"] += 1

        status = result["status"]
        if status == "ok":
            summary["ok"] += 1
            continue

        event = result["event_type"]
        severity = {"DELETED": "HIGH", "MODIFIED": "MEDIUM", "CREATED": "LOW"}.get(event, "MEDIUM")

        db.insert_alert(file_path, event,
                        result["old_hash"], result["new_hash"], severity)
        new_preview = result["new_hash"][:16] + "…" if result["new_hash"] else "N/A"
        db.insert_log(file_path, event, "ALERT",
                      f"Change detected — new hash: {new_preview}")

        if event == "MODIFIED":
            summary["modified"] += 1
        elif event == "DELETED":
            summary["deleted"] += 1
        elif event == "CREATED":
            summary["created"] += 1

        if result_callback:
            result_callback(file_path, result)

    return summary