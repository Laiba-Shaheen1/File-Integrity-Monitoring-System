"""
Settings Page
Configure theme, scan interval, log retention, report path, etc.
"""

import os
import tkinter as tk
import customtkinter as ctk
from tkinter import filedialog, messagebox
from gui.theme import COLORS, FONT_TITLE, FONT_H3, FONT_BODY, FONT_SMALL
from gui.core import database as db


class SettingsPage(ctk.CTkFrame):

    def __init__(self, parent, controller, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        self.controller = controller
        self._build()

    def _build(self):
        top = ctk.CTkFrame(self, fg_color="transparent")
        top.pack(fill="x", padx=24, pady=(20, 10))
        ctk.CTkLabel(top, text="Settings", font=FONT_TITLE,
                     text_color=COLORS["text_primary"]).pack(side="left")

        scroll = ctk.CTkScrollableFrame(self, fg_color="transparent",
                                        label_text="")
        scroll.pack(fill="both", expand=True, padx=24, pady=(0, 20))

        config = db.load_config()

        # ── Appearance ────────────────────────────────────────────────────
        self._section(scroll, "Appearance")

        theme_row = self._row(scroll, "Theme")
        self.theme_var = tk.StringVar(value=config.get("theme", "dark"))
        ctk.CTkOptionMenu(
            theme_row, values=["dark", "light", "system"],
            variable=self.theme_var,
            width=140,
            fg_color=COLORS["bg_card"],
            button_color=COLORS["accent_blue"]
        ).pack(side="right")

        # ── Monitoring ────────────────────────────────────────────────────
        self._section(scroll, "Monitoring")

        interval_row = self._row(scroll, "Periodic scan interval (seconds)",
                                 "Full scan runs every N seconds when monitoring is active.")
        self.interval_var = tk.StringVar(value=str(config.get("scan_interval", 30)))
        ctk.CTkEntry(interval_row,
                     textvariable=self.interval_var,
                     width=80,
                     fg_color=COLORS["bg_card"],
                     border_color=COLORS["border"]).pack(side="right")

        alert_row = self._row(scroll, "Alert sound",
                              "Play a sound when a new alert is detected.")
        self.sound_var = tk.BooleanVar(value=config.get("alert_sound", True))
        ctk.CTkSwitch(alert_row, text="", variable=self.sound_var,
                      onvalue=True, offvalue=False,
                      progress_color=COLORS["accent_blue"]).pack(side="right")

        auto_row = self._row(scroll, "Auto-baseline on startup",
                             "Automatically create a new baseline when the app starts.")
        self.auto_var = tk.BooleanVar(value=config.get("auto_baseline", False))
        ctk.CTkSwitch(auto_row, text="", variable=self.auto_var,
                      onvalue=True, offvalue=False,
                      progress_color=COLORS["accent_blue"]).pack(side="right")

        # ── Storage ───────────────────────────────────────────────────────
        self._section(scroll, "Storage")

        retention_row = self._row(scroll, "Log retention (days)",
                                  "Logs older than this are removed automatically.")
        self.retention_var = tk.StringVar(
            value=str(config.get("log_retention_days", 30)))
        ctk.CTkEntry(retention_row,
                     textvariable=self.retention_var,
                     width=80,
                     fg_color=COLORS["bg_card"],
                     border_color=COLORS["border"]).pack(side="right")

        report_row = self._row(scroll, "Reports folder",
                               "Where generated CSV reports are saved.")
        self.report_path_var = tk.StringVar(
            value=config.get("report_path", "reports"))
        path_frame = ctk.CTkFrame(report_row, fg_color="transparent")
        path_frame.pack(side="right")
        self.report_path_entry = ctk.CTkEntry(
            path_frame,
            textvariable=self.report_path_var,
            width=260,
            fg_color=COLORS["bg_card"],
            border_color=COLORS["border"])
        self.report_path_entry.pack(side="left", padx=(0, 4))
        ctk.CTkButton(
            path_frame, text="Browse", width=70,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["accent_blue"],
            command=self._browse_folder
        ).pack(side="left")

        # ── Database ──────────────────────────────────────────────────────
        self._section(scroll, "Database")

        db_row = self._row(scroll, "Clear all alerts")
        ctk.CTkButton(
            db_row, text="Clear Alerts", width=120,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            command=self._clear_alerts
        ).pack(side="right")

        log_row = self._row(scroll, "Clear all logs")
        ctk.CTkButton(
            log_row, text="Clear Logs", width=120,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            command=self._clear_logs
        ).pack(side="right")

        baseline_row = self._row(scroll, "Clear baseline")
        ctk.CTkButton(
            baseline_row, text="Clear Baseline", width=120,
            fg_color=COLORS["bg_card"],
            hover_color=COLORS["danger"],
            command=self._clear_baseline
        ).pack(side="right")

        # ── Save ──────────────────────────────────────────────────────────
        save_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        save_frame.pack(fill="x", pady=(20, 10))
        ctk.CTkButton(
            save_frame, text="💾  Save Settings", width=180,
            fg_color=COLORS["accent_blue"],
            hover_color="#1a5fa8",
            command=self._save
        ).pack(side="right")

        self.save_status = ctk.CTkLabel(save_frame, text="",
                                         font=FONT_SMALL,
                                         text_color=COLORS["accent_green"])
        self.save_status.pack(side="right", padx=10)

    def _section(self, parent, title):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=(16, 4))
        ctk.CTkLabel(frame, text=title, font=FONT_H3,
                     text_color=COLORS["accent_blue"]).pack(side="left")
        line = ctk.CTkFrame(frame, height=1, fg_color=COLORS["border"])
        line.pack(side="left", fill="x", expand=True, padx=(10, 0))

    def _row(self, parent, label, subtitle=None):
        row = ctk.CTkFrame(parent, fg_color=COLORS["bg_panel"],
                           corner_radius=8,
                           border_width=1,
                           border_color=COLORS["border"])
        row.pack(fill="x", pady=3)
        txt = ctk.CTkFrame(row, fg_color="transparent")
        txt.pack(side="left", padx=16, pady=10)
        ctk.CTkLabel(txt, text=label, font=FONT_BODY,
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(txt, text=subtitle, font=FONT_SMALL,
                         text_color=COLORS["text_muted"]).pack(anchor="w")
        return row

    def _browse_folder(self):
        path = filedialog.askdirectory(title="Select reports folder")
        if path:
            self.report_path_var.set(path)

    def _save(self):
        try:
            interval = int(self.interval_var.get())
            retention = int(self.retention_var.get())
        except ValueError:
            messagebox.showerror("Invalid value",
                                 "Scan interval and retention must be integers.")
            return

        config = {
            "theme": self.theme_var.get(),
            "scan_interval": interval,
            "alert_sound": self.sound_var.get(),
            "auto_baseline": self.auto_var.get(),
            "log_retention_days": retention,
            "report_path": self.report_path_var.get(),
        }
        db.save_config(config)

        # Apply theme
        ctk.set_appearance_mode(config["theme"])

        self.save_status.configure(text="✓ Saved")
        self.after(2000, lambda: self.save_status.configure(text=""))

    def _clear_alerts(self):
        if messagebox.askyesno("Clear alerts", "Delete ALL alerts permanently?"):
            conn = db.get_connection()
            conn.execute("DELETE FROM alerts")
            conn.commit()
            conn.close()
            self.controller.refresh_all()

    def _clear_logs(self):
        if messagebox.askyesno("Clear logs", "Delete ALL logs permanently?"):
            db.clear_logs()
            self.controller.refresh_all()

    def _clear_baseline(self):
        if messagebox.askyesno("Clear baseline",
                               "Delete entire baseline? You will need to re-baseline."):
            db.clear_baseline()
            self.controller.refresh_all()

    def refresh(self):
        pass  # settings page doesn't auto-refresh data
