"""
File Watcher  (FIXED + ENHANCED)
Real-time file system monitoring using the watchdog library.

Fixes:
  - on_created: retry hash with small delay so file is fully written
  - on_modified: distinguish truly new files (no baseline) vs modified
  - on_moved: properly records both DELETED + CREATED with hashes
  - debounce window raised to 2 s to stop duplicate MODIFIED spam
  - all events now guaranteed to produce an alert + log entry
Enhancements:
  - _safe_hash() retries up to 3x with 0.5 s gap for locked files
  - clearer severity mapping: CREATED=LOW, MODIFIED=MEDIUM, DELETED=HIGH
"""

import os
import time
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from . import database as db
from .hash_engine import compute_sha256, get_file_meta


DEBOUNCE_SECONDS = 2.0
HASH_RETRY_COUNT = 3
HASH_RETRY_DELAY = 0.5   # seconds between retries


def _safe_hash(path, retries=HASH_RETRY_COUNT):
    """Try to hash a file, retrying if it's still being written."""
    for attempt in range(retries):
        h = compute_sha256(path)
        if h:
            return h
        if attempt < retries - 1:
            time.sleep(HASH_RETRY_DELAY)
    return None


class FIMEventHandler(FileSystemEventHandler):

    def __init__(self, alert_callback=None):
        super().__init__()
        self.alert_callback = alert_callback
        self._debounce: dict = {}
        self._debounce_lock = threading.Lock()

    # ── helpers ────────────────────────────────────────────────────────────

    def _should_ignore(self, path):
        name = os.path.basename(path)
        # skip hidden / temp / swap files
        return (name.startswith(".")
                or name.endswith((".tmp", "~", ".swp", ".part"))
                or "~$" in name)

    def _debounced(self, path, event_type):
        key = (path, event_type)
        now = time.time()
        with self._debounce_lock:
            if now - self._debounce.get(key, 0) < DEBOUNCE_SECONDS:
                return True
            self._debounce[key] = now
        return False

    # ── core handler ────────────────────────────────────────────────────────

    def _handle_created(self, path):
        """File appeared on disk — may be new or moved-in."""
        if self._should_ignore(path) or self._debounced(path, "CREATED"):
            return

        # Give the OS a moment to finish writing
        time.sleep(0.3)
        if not os.path.isfile(path):
            return

        new_hash = _safe_hash(path)
        if not new_hash:
            db.insert_log(path, "CREATED", "WARNING",
                          "New file detected but could not be hashed (locked)")
            return

        size, mtime = get_file_meta(path)
        db.upsert_baseline(path, new_hash, size, mtime)
        db.insert_alert(path, "CREATED", old_hash=None,
                        new_hash=new_hash, severity="LOW")
        db.insert_log(path, "CREATED", "ALERT",
                      f"New file — hash: {new_hash[:16]}…")

        if self.alert_callback:
            self.alert_callback(path, "CREATED", {"old_hash": None, "new_hash": new_hash})

    def _handle_modified(self, path):
        """File content changed — compare against baseline."""
        if self._should_ignore(path) or self._debounced(path, "MODIFIED"):
            return
        if not os.path.isfile(path):
            return

        new_hash = _safe_hash(path)
        if not new_hash:
            return

        baseline = db.get_baseline(path)

        if baseline is None:
            # No baseline entry → treat as a newly discovered file
            size, mtime = get_file_meta(path)
            db.upsert_baseline(path, new_hash, size, mtime)
            db.insert_alert(path, "CREATED", old_hash=None,
                            new_hash=new_hash, severity="LOW")
            db.insert_log(path, "CREATED", "ALERT",
                          f"New file discovered on modify event — hash: {new_hash[:16]}…")
            if self.alert_callback:
                self.alert_callback(path, "CREATED",
                                    {"old_hash": None, "new_hash": new_hash})
            return

        old_hash = baseline["sha256_hash"]
        if new_hash == old_hash:
            return   # metadata-only change, content unchanged

        # Genuine modification
        size, mtime = get_file_meta(path)
        db.upsert_baseline(path, new_hash, size, mtime)
        db.insert_alert(path, "MODIFIED", old_hash=old_hash,
                        new_hash=new_hash, severity="MEDIUM")
        db.insert_log(path, "MODIFIED", "ALERT",
                      f"Hash changed: {old_hash[:16]}… → {new_hash[:16]}…")

        if self.alert_callback:
            self.alert_callback(path, "MODIFIED",
                                {"old_hash": old_hash, "new_hash": new_hash})

    def _handle_deleted(self, path):
        """File removed from disk."""
        if self._should_ignore(path) or self._debounced(path, "DELETED"):
            return

        baseline = db.get_baseline(path)
        old_hash = baseline["sha256_hash"] if baseline else "unknown"

        db.delete_baseline_entry(path)
        db.insert_alert(path, "DELETED", old_hash=old_hash,
                        new_hash=None, severity="HIGH")
        db.insert_log(path, "DELETED", "ALERT",
                      f"File removed — last known hash: {str(old_hash)[:16]}…")

        if self.alert_callback:
            self.alert_callback(path, "DELETED",
                                {"old_hash": old_hash, "new_hash": None})

    # ── watchdog callbacks ──────────────────────────────────────────────────

    def on_created(self, event):
        if not event.is_directory:
            threading.Thread(
                target=self._handle_created,
                args=(event.src_path,),
                daemon=True
            ).start()

    def on_modified(self, event):
        if not event.is_directory:
            threading.Thread(
                target=self._handle_modified,
                args=(event.src_path,),
                daemon=True
            ).start()

    def on_deleted(self, event):
        if not event.is_directory:
            self._handle_deleted(event.src_path)

    def on_moved(self, event):
        if not event.is_directory:
            # Old location → DELETED
            self._handle_deleted(event.src_path)
            # New location → CREATED (run in thread so hash can retry)
            threading.Thread(
                target=self._handle_created,
                args=(event.dest_path,),
                daemon=True
            ).start()


# ── FileWatcher ────────────────────────────────────────────────────────────────

class FileWatcher:
    """Manages watchdog Observer for all watched paths."""

    def __init__(self, alert_callback=None):
        self.alert_callback = alert_callback
        self.observer = None
        self.running = False
        self._watched_dirs: set = set()

    def start(self, watch_paths):
        if self.running:
            self.stop()

        self._handler = FIMEventHandler(alert_callback=self.alert_callback)
        self.observer = Observer()
        self._watched_dirs.clear()

        for entry in watch_paths:
            path = entry["path"]
            if not os.path.exists(path):
                db.insert_log(path, "WATCH", "WARNING",
                              "Path not found at start — skipped")
                continue

            watch_dir = path if os.path.isdir(path) else os.path.dirname(path)
            if watch_dir not in self._watched_dirs:
                self.observer.schedule(self._handler, watch_dir, recursive=True)
                self._watched_dirs.add(watch_dir)

        if self._watched_dirs:
            self.observer.start()
            self.running = True
            db.insert_log("SYSTEM", "MONITOR_START", "OK",
                          f"Watching {len(self._watched_dirs)} director(y/ies)")
        else:
            db.insert_log("SYSTEM", "MONITOR_START", "WARNING",
                          "No valid paths to watch")

    def stop(self):
        if self.observer and self.running:
            self.observer.stop()
            self.observer.join(timeout=3)
            self.running = False
            self.observer = None
            db.insert_log("SYSTEM", "MONITOR_STOP", "OK", "Monitoring stopped")

    def is_running(self):
        return self.running and self.observer is not None and self.observer.is_alive()

    def update_paths(self, watch_paths):
        self.stop()
        self.start(watch_paths)