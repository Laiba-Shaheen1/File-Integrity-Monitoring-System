"""
Alerts Page
Displays all security alerts with filtering and acknowledge controls.
"""

import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from gui.theme import COLORS, FONT_TITLE, FONT_H3, FONT_SMALL, FONT_MONO_S
from gui.widgets import SimpleTable
from gui.core import database as db


class AlertsPage(ctk.CTkFrame):

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller
        self._filter = "ALL"
        self._build()

    def _build(self):
        # Title
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(top, text="Alerts", font=FONT_TITLE,
                     text_color=COLORS["text_primary"]).pack(side="left")
        self.count_label = ctk.CTkLabel(top, text="",
                                         font=FONT_SMALL,
                                         text_color=COLORS["text_muted"])
        self.count_label.pack(side="left", padx=12)

        # Filter + action buttons
        bar = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                           corner_radius=10,
                           border_width=1,
                           border_color=COLORS["border"])
        bar.pack(fill="x", padx=24, pady=(0, 12))
        inner = ctk.CTkFrame(bar, fg_color="transparent")
        inner.pack(padx=16, pady=10, anchor="w")

        ctk.CTkLabel(inner, text="Filter:", font=FONT_SMALL,
                     text_color=COLORS["text_secondary"]).grid(
            row=0, column=0, padx=(0, 8))

        self.filter_var = tk.StringVar(value="ALL")
        filters = ["ALL", "MODIFIED", "DELETED", "CREATED", "UNREAD"]
        col = 1
        for f in filters:
            btn = ctk.CTkButton(
                inner, text=f, width=90,
                fg_color=COLORS["bg_card"],
                hover_color=COLORS["accent_blue"],
                command=lambda x=f: self._apply_filter(x))
            btn.grid(row=0, column=col, padx=4)
            col += 1

        sep = ctk.CTkFrame(inner, width=2, height=32,
                           fg_color=COLORS["border"])
        sep.grid(row=0, column=col, padx=10)
        col += 1

        ctk.CTkButton(
            inner, text="✓ Acknowledge All", width=150,
            fg_color="#1a2a1a",
            hover_color=COLORS["success"],
            command=self._acknowledge_all
        ).grid(row=0, column=col, padx=4)
        col += 1

        ctk.CTkButton(
            inner, text="↻ Refresh", width=100,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_blue"],
            command=self.refresh
        ).grid(row=0, column=col, padx=4)

        # Table
        table_card = ctk.CTkFrame(self, fg_color=COLORS["bg_panel"],
                                  corner_radius=10,
                                  border_width=1,
                                  border_color=COLORS["border"])
        table_card.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        self.table = SimpleTable(
            table_card,
            columns=[
                ("id",       "ID",        50),
                ("time",     "Timestamp", 160),
                ("path",     "File Path", 360),
                ("event",    "Event",      90),
                ("severity", "Severity",   80),
                ("ack",      "Ack",        50),
            ],
            height=18
        )
        self.table.pack(fill="both", expand=True, padx=12, pady=12)

        # Double-click to acknowledge
        self.table.tree.bind("<Double-1>", self._on_double_click)

    def refresh(self):
        alerts = db.get_alerts(limit=500,
                               unacknowledged_only=(self._filter == "UNREAD"))
        if self._filter not in ("ALL", "UNREAD"):
            alerts = [a for a in alerts if a["event_type"] == self._filter]

        self.count_label.configure(text=f"{len(alerts)} alerts")

        def tag_fn(row):
            event = row[3].upper()
            tags = []
            if event == "MODIFIED":
                tags.append("modified")
            elif event == "DELETED":
                tags.append("deleted")
            elif event == "CREATED":
                tags.append("created")
            return tags

        rows = [
            (a["id"], a["timestamp"], a["file_path"],
             a["event_type"], a["severity"],
             "✓" if a["acknowledged"] else "")
            for a in alerts
        ]
        self.table.load_rows(rows, tag_fn=tag_fn)

    def _apply_filter(self, f):
        self._filter = f
        self.refresh()

    def _acknowledge_all(self):
        db.acknowledge_all_alerts()
        self.refresh()
        self.controller.refresh_all()

    def _on_double_click(self, event):
        selected = self.table.tree.selection()
        if selected:
            item = self.table.tree.item(selected[0])
            alert_id = item["values"][0]
            db.acknowledge_alert(alert_id)
            self.refresh()
