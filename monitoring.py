"""
Monitoring Page
Add/remove watched paths, create baseline, start/stop real-time monitoring.
"""

import os
import threading
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from gui.theme import COLORS, FONT_TITLE, FONT_H2, FONT_H3, FONT_BODY, FONT_SMALL, FONT_MONO_S
from gui.widgets import SectionHeader, SimpleTable
from gui.core import database as db
from gui.core.hash_engine import create_baseline, run_full_scan


class MonitoringPage(ctk.CTkFrame):

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller
        self._build()

    def _build(self):
        # Title row
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(top, text="Monitoring", font=FONT_TITLE,
                     text_color=COLORS["text_primary"]).pack(side="left")

        # ── Control buttons ────────────────────────────────────────────────
        btn_frame = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                                 corner_radius=10,
                                 border_width=1,
                                 border_color=COLORS["border"])
        btn_frame.pack(fill="x", padx=24, pady=(0, 12))

        inner = ctk.CTkFrame(btn_frame, fg_color="transparent")
        inner.pack(padx=16, pady=12)

        self.btn_add_file = ctk.CTkButton(
            inner, text="+ Add File", width=120,
            fg_color=COLORS["accent_blue"],
            hover_color="#1a5fa8",
            command=self._add_file)
        self.btn_add_file.grid(row=0, column=0, padx=5)

        self.btn_add_folder = ctk.CTkButton(
            inner, text="+ Add Folder", width=120,
            fg_color=COLORS["accent_blue"],
            hover_color="#1a5fa8",
            command=self._add_folder)
        self.btn_add_folder.grid(row=0, column=1, padx=5)

        self.btn_remove = ctk.CTkButton(
            inner, text="✕ Remove", width=110,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            command=self._remove_path)
        self.btn_remove.grid(row=0, column=2, padx=5)

        sep = ctk.CTkFrame(inner, width=2, height=36,
                           fg_color=COLORS["border"])
        sep.grid(row=0, column=3, padx=12)

        self.btn_baseline = ctk.CTkButton(
            inner, text="🔒 Create Baseline", width=150,
            fg_color="#1a4a2a",
            hover_color="#27ae60",
            command=self._create_baseline)
        self.btn_baseline.grid(row=0, column=4, padx=5)

        self.btn_scan = ctk.CTkButton(
            inner, text="🔎 Run Full Scan", width=140,
            fg_color="#1a3a4a",
            hover_color="#2980b9",
            command=self._run_scan)
        self.btn_scan.grid(row=0, column=5, padx=5)

        sep2 = ctk.CTkFrame(inner, width=2, height=36,
                            fg_color=COLORS["border"])
        sep2.grid(row=0, column=6, padx=12)

        self.btn_start = ctk.CTkButton(
            inner, text="▶  Start Monitoring", width=160,
            fg_color=COLORS["success"],
            hover_color="#1e8449",
            command=self._start_monitoring)
        self.btn_start.grid(row=0, column=7, padx=5)

        self.btn_stop = ctk.CTkButton(
            inner, text="⏹  Stop", width=90,
            fg_color=COLORS["danger"],
            hover_color="#a93226",
            state="disabled",
            command=self._stop_monitoring)
        self.btn_stop.grid(row=0, column=8, padx=5)

        # ── Progress bar (hidden by default) ──────────────────────────────
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.progress_frame.pack(fill="x", padx=24, pady=(0, 8))
        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            fg_color=COLORS["bg_card"],
            progress_color=COLORS["accent_blue"])
        self.progress_bar.pack(fill="x")
        self.progress_bar.set(0)
        self.progress_label = ctk.CTkLabel(
            self.progress_frame, text="",
            font=FONT_SMALL,
            text_color=COLORS["text_muted"])
        self.progress_label.pack(anchor="w")
        self.progress_frame.pack_forget()

        # ── Watched paths table ────────────────────────────────────────────
        table_card = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                                  corner_radius=10,
                                  border_width=1,
                                  border_color=COLORS["border"])
        table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        header = ctk.CTkFrame(table_card, fg_color="transparent")
        header.pack(fill="x", padx=16, pady=(12, 6))
        ctk.CTkLabel(header, text="Watched Paths",
                     font=FONT_H3,
                     text_color=COLORS["text_primary"]).pack(side="left")
        self.path_count_label = ctk.CTkLabel(
            header, text="0 paths",
            font=FONT_SMALL,
            text_color=COLORS["text_muted"])
        self.path_count_label.pack(side="right")

        self.paths_table = SimpleTable(
            table_card,
            columns=[
                ("path",    "Path",     480),
                ("type",    "Type",      70),
                ("added",   "Added On", 180),
            ],
            height=12
        )
        self.paths_table.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        # ── Status label ──────────────────────────────────────────────────
        self.status_label = ctk.CTkLabel(
            self, text="",
            font=FONT_SMALL,
            text_color=COLORS["text_muted"])
        self.status_label.pack(pady=(0, 4))

    # ── Public ─────────────────────────────────────────────────────────────

    def refresh(self):
        self._reload_table()
        running = self.controller.watcher and self.controller.watcher.is_running()
        self.btn_start.configure(state="disabled" if running else "normal")
        self.btn_stop.configure(state="normal" if running else "disabled")

    # ── Internals ──────────────────────────────────────────────────────────

    def _reload_table(self):
        paths = db.get_watch_paths()
        rows = [(p["path"], p["path_type"], p["added_on"]) for p in paths]
        self.paths_table.load_rows(rows)
        self.path_count_label.configure(text=f"{len(paths)} paths")

    def _add_file(self):
        path = filedialog.askopenfilename(title="Select file to monitor")
        if path:
            db.add_watch_path(path, "file")
            db.insert_log(path, "WATCH", "OK", "Added to watch list")
            self._reload_table()
            self._set_status(f"Added file: {os.path.basename(path)}")

    def _add_folder(self):
        path = filedialog.askdirectory(title="Select folder to monitor")
        if path:
            db.add_watch_path(path, "dir")
            db.insert_log(path, "WATCH", "OK", "Folder added to watch list")
            self._reload_table()
            self._set_status(f"Added folder: {os.path.basename(path)}")

    def _remove_path(self):
        selected = self.paths_table.tree.selection()
        if not selected:
            messagebox.showinfo("Select a path", "Click a row to select it first.")
            return
        item = self.paths_table.tree.item(selected[0])
        path = item["values"][0]
        if messagebox.askyesno("Remove path",
                               f"Remove from watch list?\n\n{path}"):
            db.remove_watch_path(path)
            self._reload_table()
            self._set_status(f"Removed: {os.path.basename(path)}")

    def _create_baseline(self):
        paths = db.get_watch_paths()
        if not paths:
            messagebox.showwarning("No paths",
                                   "Add files or folders to monitor first.")
            return
        if not messagebox.askyesno("Create baseline",
                                   "This will hash all monitored files and store the baseline.\n"
                                   "Existing baseline will be overwritten. Continue?"):
            return

        self._show_progress("Creating baseline…")
        total_files = [0]

        def progress_cb(current, total, fpath):
            total_files[0] = total
            pct = current / total if total else 0
            self.progress_bar.set(pct)
            name = os.path.basename(fpath)
            self.progress_label.configure(
                text=f"Hashing ({current}/{total}): {name}")
            self.update_idletasks()

        def run():
            success, errors = create_baseline(paths, progress_cb)
            self.after(0, lambda: self._baseline_done(success, errors))

        threading.Thread(target=run, daemon=True).start()

    def _baseline_done(self, success, errors):
        self._hide_progress()
        self._set_status(f"Baseline created: {success} files hashed, {errors} errors.")
        messagebox.showinfo("Baseline complete",
                            f"✅ {success} files hashed successfully.\n"
                            f"⚠️ {errors} files could not be read.")
        self.controller.refresh_all()

    def _run_scan(self):
        paths = db.get_watch_paths()
        if not paths:
            messagebox.showwarning("No paths", "Add paths to monitor first.")
            return
        baseline_count = db.get_baseline_count()
        if baseline_count == 0:
            messagebox.showwarning("No baseline",
                                   "Create a baseline first before scanning.")
            return

        self._show_progress("Scanning…")

        def run():
            summary = run_full_scan(paths)
            self.after(0, lambda: self._scan_done(summary))

        threading.Thread(target=run, daemon=True).start()

    def _scan_done(self, summary):
        self._hide_progress()
        self._set_status(
            f"Scan complete — Modified: {summary['modified']}, "
            f"Deleted: {summary['deleted']}, New: {summary['created']}")
        messagebox.showinfo(
            "Scan complete",
            f"Files scanned: {summary['scanned']}\n"
            f"✅ OK: {summary['ok']}\n"
            f"⚠️  Modified: {summary['modified']}\n"
            f"🗑️  Deleted: {summary['deleted']}\n"
            f"🆕 New files: {summary['created']}"
        )
        self.controller.refresh_all()

    def _start_monitoring(self):
        paths = db.get_watch_paths()
        if not paths:
            messagebox.showwarning("No paths", "Add paths to monitor first.")
            return
        if db.get_baseline_count() == 0:
            if not messagebox.askyesno("No baseline",
                                       "No baseline exists. Create one now?"):
                return
            self._create_baseline()
            return

        self.controller.watcher.start(paths)
        self.btn_start.configure(state="disabled")
        self.btn_stop.configure(state="normal")
        self._set_status("Real-time monitoring started.")
        self.controller.refresh_all()

    def _stop_monitoring(self):
        self.controller.watcher.stop()
        self.btn_start.configure(state="normal")
        self.btn_stop.configure(state="disabled")
        self._set_status("Monitoring stopped.")
        self.controller.refresh_all()

    def _show_progress(self, msg="Working…"):
        self.progress_frame.pack(fill="x", padx=24, pady=(0, 8))
        self.progress_bar.set(0)
        self.progress_label.configure(text=msg)
        self.btn_baseline.configure(state="disabled")
        self.btn_scan.configure(state="disabled")

    def _hide_progress(self):
        self.progress_frame.pack_forget()
        self.btn_baseline.configure(state="normal")
        self.btn_scan.configure(state="normal")

    def _set_status(self, msg):
        self.status_label.configure(text=msg)
