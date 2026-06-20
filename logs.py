"""
Logs Page
Full audit log with timestamp, path, event type, status, details.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from gui.theme import COLORS, FONT_TITLE, FONT_H3, FONT_SMALL
from gui.widgets import SimpleTable
from gui.core import database as db


class LogsPage(ctk.CTkFrame):

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(top, text="Logs", font=FONT_TITLE,
                     text_color=COLORS["text_primary"]).pack(side="left")
        self.count_label = ctk.CTkLabel(top, text="",
                                         font=FONT_SMALL,
                                         text_color=COLORS["text_muted"])
        self.count_label.pack(side="left", padx=12)

        # Action bar
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                           corner_radius=10,
                           border_width=1,
                           border_color=COLORS["border"])
        bar.pack(fill="x", padx=24, pady=(0, 12))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(padx=16, pady=10, anchor="w")

        ctk.CTkButton(
            inner, text="↻ Refresh", width=100,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_blue"],
            command=self.refresh
        ).grid(row=0, column=0, padx=4)

        ctk.CTkButton(
            inner, text="🗑  Clear Logs", width=120,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            command=self._clear_logs
        ).grid(row=0, column=1, padx=4)

        # Search
        ctk.CTkLabel(inner, text="Search:", font=FONT_SMALL,
                     text_color=COLORS["text_secondary"]).grid(
            row=0, column=2, padx=(20, 4))
        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", lambda *_: self.refresh())
        ctk.CTkEntry(inner, textvariable=self.search_var,
                     width=260,
                     placeholder_text="Filter by path or event…",
                     fg_color=COLORS["bg_card"],
                     border_color=COLORS["border"]).grid(
            row=0, column=3, padx=4)

        # Table
        table_card = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                                  corner_radius=10,
                                  border_width=1,
                                  border_color=COLORS["border"])
        table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.table = SimpleTable(
            table_card,
            columns=[
                ("id",      "ID",         50),
                ("time",    "Timestamp",  160),
                ("path",    "File Path",  340),
                ("event",   "Event",       90),
                ("status",  "Status",      80),
                ("details", "Details",    200),
            ],
            height=20
        )
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

    def refresh(self):
        logs = db.get_logs(limit=500)
        q = self.search_var.get().lower() if hasattr(self, "search_var") else ""
        if q:
            logs = [l for l in logs
                    if q in l["file_path"].lower()
                    or q in l["event_type"].lower()
                    or q in (l.get("status") or "").lower()]

        self.count_label.configure(text=f"{len(logs)} entries")

        def tag_fn(row):
            event = str(row[3]).upper()
            status = str(row[4]).upper()
            if status == "ALERT" or event in ("MODIFIED", "DELETED", "CREATED"):
                return ["modified"] if event == "MODIFIED" else \
                       ["deleted"] if event == "DELETED" else \
                       ["created"] if event == "CREATED" else []
            return []

        rows = [
            (l["id"], l["timestamp"], l["file_path"],
             l["event_type"], l["status"], l.get("details", ""))
            for l in logs
        ]
        self.table.load_rows(rows, tag_fn=tag_fn)

    def _clear_logs(self):
        if messagebox.askyesno("Clear logs",
                               "Delete all log entries? This cannot be undone."):
            db.clear_logs()
            self.refresh()
