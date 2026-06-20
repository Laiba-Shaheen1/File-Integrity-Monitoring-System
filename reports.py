"""
Reports Page
Generate and download security reports in CSV format.
"""

import os
import threading
import subprocess
import sys
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox, filedialog
from gui.theme import COLORS, FONT_TITLE, FONT_H3, FONT_BODY, FONT_SMALL
from gui.core import database as db
from gui.core import report_generator as rg


class ReportsPage(ctk.CTkFrame):

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(top, text="Reports", font=FONT_TITLE,
                     text_color=COLORS["text_primary"]).pack(side="left")

        # Report cards grid
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=24, pady=(0, 16))
        cards_frame.columnconfigure((0, 1, 2, 3), weight=1, uniform="rcard")

        reports = [
            {
                "title": "Full Security Report",
                "desc": "Complete report including alerts, logs, watched paths, and summary statistics.",
                "icon": "📊",
                "color": COLORS["accent_blue"],
                "fn": "full",
            },
            {
                "title": "Alerts Report",
                "desc": "All security alerts with event types, severity, file paths, and hash values.",
                "icon": "🚨",
                "color": COLORS["danger"],
                "fn": "alerts",
            },
            {
                "title": "Logs Report",
                "desc": "Complete audit trail with timestamps, events, statuses, and details.",
                "icon": "📋",
                "color": COLORS["warning"],
                "fn": "logs",
            },
            {
                "title": "Baseline Snapshot",
                "desc": "Current baseline with SHA-256 hashes, file sizes, and modification times.",
                "icon": "🔒",
                "color": COLORS["accent_green"],
                "fn": "baseline",
            },
        ]

        for i, r in enumerate(reports):
            self._make_report_card(cards_frame, r, i)

        # Recent reports list
        list_card = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                                 corner_radius=10,
                                 border_width=1,
                                 border_color=COLORS["border"])
        list_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        hdr = ctk.CTkFrame(list_card, fg_color="transparent")
        hdr.pack(fill="x", padx=16, pady=(12, 4))
        ctk.CTkLabel(hdr, text="Generated Reports",
                     font=FONT_H3,
                     text_color=COLORS["text_primary"]).pack(side="left")
        ctk.CTkButton(
            hdr, text="↻ Refresh", width=90,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_blue"],
            command=self._reload_file_list
        ).pack(side="right")
        ctk.CTkButton(
            hdr, text="📁 Open folder", width=110,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_blue"],
            command=self._open_reports_folder
        ).pack(side="right", padx=6)

        self.files_scroll = ctk.CTkScrollableFrame(
            list_card, fg_color="transparent", label_text="")
        self.files_scroll.pack(fill="both", expand=True, padx=12, pady=(0, 12))

        self._reload_file_list()

    def _make_report_card(self, parent, data, col):
        card = ctk.CTkFrame(parent, fg_color=COLORS["bg_panel"],
                            corner_radius=10,
                            border_width=1,
                            border_color=COLORS["border"])
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        # Top accent
        bar = tk.Frame(card, bg=data["color"], height=4)
        bar.pack(fill="x")

        ctk.CTkLabel(card, text=data["icon"], font=("Segoe UI", 28)).pack(pady=(14, 4))
        ctk.CTkLabel(card, text=data["title"], font=FONT_H3,
                     text_color=COLORS["text_primary"],
                     wraplength=200).pack(padx=12)
        ctk.CTkLabel(card, text=data["desc"], font=FONT_SMALL,
                     text_color=COLORS["text_secondary"],
                     wraplength=200).pack(padx=12, pady=8)

        ctk.CTkButton(
            card, text="Generate & Download",
            fg_color=data["color"],
            hover_color=COLORS["bg_card"],
            command=lambda fn=data["fn"]: self._generate(fn)
        ).pack(pady=(0, 16))

    def _generate(self, report_type):
        config = db.load_config()
        report_path = config.get("report_path", "reports")

        def run():
            try:
                if report_type == "full":
                    path = rg.generate_full_report(report_path)
                elif report_type == "alerts":
                    path = rg.generate_alerts_report(report_path)
                elif report_type == "logs":
                    path = rg.generate_logs_report(report_path)
                else:
                    path = rg.generate_baseline_report(report_path)
                self.after(0, lambda: self._report_done(path))
            except Exception as e:
                self.after(0, lambda: messagebox.showerror(
                    "Error", f"Failed to generate report:\n{e}"))

        threading.Thread(target=run, daemon=True).start()

    def _report_done(self, filepath):
        self._reload_file_list()
        if messagebox.askyesno("Report ready",
                               f"Report saved to:\n{filepath}\n\nOpen file?"):
            self._open_file(filepath)

    def _reload_file_list(self):
        for w in self.files_scroll.winfo_children():
            w.destroy()

        config = db.load_config()
        report_path = config.get("report_path", "reports")
        if not os.path.isdir(report_path):
            ctk.CTkLabel(self.files_scroll,
                         text="No reports generated yet.",
                         font=FONT_SMALL,
                         text_color=COLORS["text_muted"]).pack(pady=20)
            return

        files = sorted(
            [f for f in os.listdir(report_path) if f.endswith(".csv")],
            reverse=True
        )
        if not files:
            ctk.CTkLabel(self.files_scroll,
                         text="No reports yet.",
                         font=FONT_SMALL,
                         text_color=COLORS["text_muted"]).pack(pady=20)
            return

        for fname in files[:30]:
            full = os.path.join(report_path, fname)
            row = ctk.CTkFrame(self.files_scroll, fg_color=COLORS["bg_card"],
                               corner_radius=6)
            row.pack(fill="x", pady=2)

            size_kb = os.path.getsize(full) // 1024
            ctk.CTkLabel(row, text=f"📄  {fname}",
                         font=FONT_SMALL,
                         text_color=COLORS["text_primary"],
                         anchor="w").pack(side="left", padx=10, pady=6)
            ctk.CTkLabel(row, text=f"{size_kb} KB",
                         font=FONT_SMALL,
                         text_color=COLORS["text_muted"]).pack(side="right", padx=10)
            ctk.CTkButton(row, text="Open", width=70,
                          fg_color=COLORS["bg_panel"],
                          hover_color=COLORS["accent_blue"],
                          command=lambda p=full: self._open_file(p)
                          ).pack(side="right", padx=4, pady=4)

    def _open_file(self, path):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception as e:
            messagebox.showerror("Cannot open", str(e))

    def _open_reports_folder(self):
        config = db.load_config()
        folder = config.get("report_path", "reports")
        os.makedirs(folder, exist_ok=True)
        self._open_file(folder)

    def refresh(self):
        self._reload_file_list()
