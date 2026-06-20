"""
Dashboard Page
Shows summary statistics, monitoring status, and recent alerts.
"""

import tkinter as tk
import customtkinter as ctk
from gui.theme import COLORS, FONT_TITLE, FONT_H2, FONT_H3, FONT_BODY, FONT_SMALL
from gui.widgets import StatCard, SectionHeader, AlertRow
from gui.core import database as db


class DashboardPage(ctk.CTkFrame):

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller
        self._build()

    def _build(self):
        # ── Title ──────────────────────────────────────────────────────────
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=24, pady=(20, 10))

        ctk.CTkLabel(header, text="Dashboard",
                     font=FONT_TITLE,
                     text_color=COLORS["text_primary"]).pack(side="left")

        self.status_badge = ctk.CTkLabel(
            header, text="  ● STOPPED  ",
            font=("Segoe UI", 12, "bold"),
            text_color=COLORS["danger"],
            fg_color="#1a0000",
            corner_radius=6
        )
        self.status_badge.pack(side="right", pady=4)

        # ── Stat cards ─────────────────────────────────────────────────────
        cards_frame = ctk.CTkFrame(self, fg_color="transparent")
        cards_frame.pack(fill="x", padx=24, pady=(0, 16))
        for i in range(5):
            cards_frame.columnconfigure(i, weight=1, uniform="card")

        self.stat_monitored = StatCard(cards_frame, "Monitored Files",
                                       color=COLORS["accent_blue"])
        self.stat_monitored.grid(row=0, column=0, padx=5, sticky="ew")

        self.stat_modified = StatCard(cards_frame, "Modified",
                                      color=COLORS["warning"])
        self.stat_modified.grid(row=0, column=1, padx=5, sticky="ew")

        self.stat_deleted = StatCard(cards_frame, "Deleted",
                                     color=COLORS["danger"])
        self.stat_deleted.grid(row=0, column=2, padx=5, sticky="ew")

        self.stat_created = StatCard(cards_frame, "New Files",
                                     color=COLORS["accent_green"])
        self.stat_created.grid(row=0, column=3, padx=5, sticky="ew")

        self.stat_unread = StatCard(cards_frame, "Unread Alerts",
                                    color=COLORS["accent"])
        self.stat_unread.grid(row=0, column=4, padx=5, sticky="ew")

        # ── Bottom split ───────────────────────────────────────────────────
        bottom = ctk.CTkFrame(self, fg_color="transparent")
        bottom.pack(fill="both", expand=True, padx=24, pady=(0, 20))
        bottom.columnconfigure(0, weight=3)
        bottom.columnconfigure(1, weight=2)
        bottom.rowconfigure(0, weight=1)

        # Recent alerts panel
        alerts_card = ctk.CTkFrame(bottom, fg_color=COLORS["bg_panel"],
                                   corner_radius=10,
                                   border_width=1,
                                   border_color=COLORS["border"])
        alerts_card.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        ctk.CTkLabel(alerts_card, text="Recent Alerts",
                     font=FONT_H3,
                     text_color=COLORS["text_primary"]).pack(
            anchor="w", padx=16, pady=(14, 6))

        self.alerts_scroll = ctk.CTkScrollableFrame(
            alerts_card, fg_color="transparent", label_text="")
        self.alerts_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        # Watch paths panel
        paths_card = ctk.CTkFrame(bottom, fg_color=COLORS["bg_panel"],
                                  corner_radius=10,
                                  border_width=1,
                                  border_color=COLORS["border"])
        paths_card.grid(row=0, column=1, sticky="nsew", padx=(8, 0))

        ctk.CTkLabel(paths_card, text="Watched Paths",
                     font=FONT_H3,
                     text_color=COLORS["text_primary"]).pack(
            anchor="w", padx=16, pady=(14, 6))

        self.paths_scroll = ctk.CTkScrollableFrame(
            paths_card, fg_color="transparent", label_text="")
        self.paths_scroll.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def refresh(self):
        """Reload all dashboard data from the database."""
        # Stat cards
        baseline_count = db.get_baseline_count()
        counts = db.get_alert_counts()

        self.stat_monitored.update_value(baseline_count, COLORS["accent_blue"])
        self.stat_modified.update_value(counts["modified"],
                                        COLORS["warning"] if counts["modified"] else COLORS["text_secondary"])
        self.stat_deleted.update_value(counts["deleted"],
                                       COLORS["danger"] if counts["deleted"] else COLORS["text_secondary"])
        self.stat_created.update_value(counts["created"],
                                       COLORS["accent_green"] if counts["created"] else COLORS["text_secondary"])
        self.stat_unread.update_value(counts["unread"],
                                      COLORS["accent"] if counts["unread"] else COLORS["text_secondary"])

        # Monitor status badge
        running = self.controller.watcher and self.controller.watcher.is_running()
        if running:
            self.status_badge.configure(
                text="  ● RUNNING  ",
                text_color=COLORS["accent_green"],
                fg_color="#001a00"
            )
        else:
            self.status_badge.configure(
                text="  ● STOPPED  ",
                text_color=COLORS["danger"],
                fg_color="#1a0000"
            )

        # Recent alerts
        for w in self.alerts_scroll.winfo_children():
            w.destroy()
        alerts = db.get_alerts(limit=10)
        if not alerts:
            ctk.CTkLabel(self.alerts_scroll,
                         text="No alerts yet.",
                         font=FONT_SMALL,
                         text_color=COLORS["text_muted"]).pack(pady=20)
        else:
            for a in alerts:
                row = AlertRow(self.alerts_scroll, a)
                row.pack(fill="x", pady=3)

        # Watch paths
        for w in self.paths_scroll.winfo_children():
            w.destroy()
        paths = db.get_watch_paths()
        if not paths:
            ctk.CTkLabel(self.paths_scroll,
                         text="No paths selected. Go to Monitoring.",
                         font=FONT_SMALL,
                         text_color=COLORS["text_muted"]).pack(pady=20)
        else:
            for p in paths:
                row = ctk.CTkFrame(self.paths_scroll, fg_color=COLORS["bg_card"],
                                   corner_radius=6)
                row.pack(fill="x", pady=2)
                icon = "📁" if p["path_type"] == "dir" else "📄"
                ctk.CTkLabel(row, text=f"{icon}  {p['path']}",
                             font=FONT_SMALL,
                             text_color=COLORS["text_secondary"],
                             anchor="w").pack(fill="x", padx=10, pady=6)
