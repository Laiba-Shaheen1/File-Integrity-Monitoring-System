"""
FIM Application — Main Window  (ENHANCED)
Changes:
  - Toast notification banner for real-time alerts (slides in from top-right)
  - Sidebar unread badge updates immediately on every alert
  - Auto-refresh active page every 5 s (was refresh_all which hit every page)
  - _on_alert now also refreshes Monitoring page so path count stays live
"""

import threading
import tkinter as tk
import customtkinter as ctk

from gui.theme import COLORS, NAV_ITEMS, FONT_H3, FONT_SMALL, FONT_BODY

# ✅ FIXED IMPORTS (ONLY CHANGED PATHS)
from gui.core import database as db
from gui.core.file_watcher import FileWatcher
from gui.core.hash_engine import create_baseline


# ── Toast banner ──────────────────────────────────────────────────────────────

class ToastNotification(ctk.CTkToplevel):

    EVENT_COLORS = {
        "MODIFIED": "#e67e22",
        "DELETED":  "#e74c3c",
        "CREATED":  "#2ecc71",
    }

    def __init__(self, parent, file_path, event_type):
        super().__init__(parent)

        color = self.EVENT_COLORS.get(event_type, COLORS["accent"])
        short_path = ("…" + file_path[-45:]) if len(file_path) > 48 else file_path

        self.overrideredirect(True)
        self.attributes("-topmost", True)
        self.configure(fg_color=COLORS["bg_sidebar"])
        self.attributes("-alpha", 0.0)

        pw = parent.winfo_width()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()

        toast_w = 360
        x = px + pw - toast_w - 20
        y = py + 20

        self.geometry(f"{toast_w}x80+{x}+{y}")

        bar = tk.Frame(self, bg=color, width=5)
        bar.pack(side="left", fill="y")

        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(side="left", fill="both", expand=True, padx=10, pady=8)

        top_row = ctk.CTkFrame(body, fg_color="transparent")
        top_row.pack(fill="x")

        ctk.CTkLabel(
            top_row,
            text=f"⚠  {event_type}",
            font=("Segoe UI", 12, "bold"),
            text_color=color
        ).pack(side="left")

        ctk.CTkLabel(
            top_row,
            text="✕",
            font=("Segoe UI", 11),
            text_color=COLORS["text_muted"],
            cursor="hand2"
        ).pack(side="right")

        ctk.CTkLabel(
            body,
            text=short_path,
            font=("Consolas", 10),
            text_color=COLORS["text_secondary"],
            anchor="w"
        ).pack(fill="x")

        self._fade_in()
        self.after(4000, self._fade_out)

    def _fade_in(self, alpha=0.0):
        alpha = min(alpha + 0.08, 0.95)
        self.attributes("-alpha", alpha)
        if alpha < 0.95:
            self.after(20, lambda: self._fade_in(alpha))

    def _fade_out(self, alpha=0.95):
        alpha = max(alpha - 0.07, 0.0)
        self.attributes("-alpha", alpha)
        if alpha > 0:
            self.after(20, lambda: self._fade_out(alpha))
        else:
            self.destroy()


# ── MAIN APP ────────────────────────────────────────────────────────────────

class FIMApp(ctk.CTk):

    def __init__(self):
        super().__init__()

        db.initialize_database()
        config = db.load_config()

        ctk.set_appearance_mode(config.get("theme", "dark"))
        ctk.set_default_color_theme("blue")

        self.title("File Integrity Monitoring System")
        self.geometry("1280x780")
        self.minsize(1100, 680)
        self.configure(fg_color=COLORS["bg_dark"])

        self.watcher = FileWatcher(alert_callback=self._on_alert)

        self._build_sidebar()
        self._build_content()
        self._build_pages()

        self._current_page = None
        self._active_btn = None

        self.navigate("Dashboard")
        self._schedule_refresh()

        if config.get("auto_baseline") and db.get_baseline_count() == 0:
            self.after(2000, self._auto_baseline)

        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build_sidebar(self):
        self.sidebar = ctk.CTkFrame(
            self,
            width=220,
            fg_color=COLORS["bg_sidebar"],
            corner_radius=0
        )
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)

        logo = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        logo.pack(fill="x", padx=16, pady=(24, 4))

        ctk.CTkLabel(logo, text="🛡️", font=("Segoe UI", 28)).pack(side="left")
        ctk.CTkLabel(
            logo,
            text="FIM",
            font=("Segoe UI", 20, "bold"),
            text_color=COLORS["accent"]
        ).pack(side="left", padx=6)

        ctk.CTkLabel(
            self.sidebar,
            text="File Integrity Monitor",
            font=("Segoe UI", 10),
            text_color=COLORS["text_muted"]
        ).pack(padx=16, anchor="w")

        ctk.CTkFrame(self.sidebar, height=1,
                     fg_color=COLORS["border"]).pack(fill="x", padx=16, pady=16)

        self._nav_buttons = {}
        for label, icon in NAV_ITEMS:
            btn = ctk.CTkButton(
                self.sidebar,
                text=f"  {icon}  {label}",
                anchor="w",
                height=42,
                fg_color="transparent",
                hover_color=COLORS["bg_card"],
                text_color=COLORS["text_secondary"],
                font=FONT_BODY,
                corner_radius=8,
                command=lambda l=label: self.navigate(l)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self._nav_buttons[label] = btn

        self.sidebar_status = ctk.CTkLabel(
            self.sidebar,
            text="● Stopped",
            font=FONT_SMALL,
            text_color=COLORS["danger"]
        )
        self.sidebar_status.pack(side="bottom", pady=12)

        self.alert_badge = ctk.CTkLabel(
            self.sidebar,
            text="",
            font=("Segoe UI", 10, "bold"),
            text_color=COLORS["accent"],
            fg_color=COLORS["bg_card"],
            corner_radius=10
        )
        self.alert_badge.pack(side="bottom", pady=0)

    def _build_content(self):
        self.content = ctk.CTkFrame(
            self,
            fg_color=COLORS["bg_dark"],
            corner_radius=0
        )
        self.content.pack(side="left", fill="both", expand=True)

    def _build_pages(self):
        from gui.pages.dashboard import DashboardPage
        from gui.pages.monitoring import MonitoringPage
        from gui.pages.alerts import AlertsPage
        from gui.pages.logs import LogsPage
        from gui.pages.reports import ReportsPage
        from gui.pages.settings import SettingsPage

        self._pages = {
            "Dashboard": DashboardPage(self.content, controller=self),
            "Monitoring": MonitoringPage(self.content, controller=self),
            "Alerts": AlertsPage(self.content, controller=self),
            "Logs": LogsPage(self.content, controller=self),
            "Reports": ReportsPage(self.content, controller=self),
            "Settings": SettingsPage(self.content, controller=self),
        }

        for page in self._pages.values():
            page.place(relx=0, rely=0, relwidth=1, relheight=1)
            page.lower()

    # ── Navigation ─────────────────────────────────────────────────────────

    def navigate(self, page_name):
        if self._active_btn:
            self._active_btn.configure(
                fg_color="transparent",
                text_color=COLORS["text_secondary"]
            )

        btn = self._nav_buttons.get(page_name)
        if btn:
            btn.configure(
                fg_color=COLORS["bg_card"],
                text_color=COLORS["text_primary"]
            )
            self._active_btn = btn

        page = self._pages.get(page_name)
        if page:
            page.lift()
            page.refresh()
            self._current_page = page_name

    # ── Refresh ────────────────────────────────────────────────────────────

    def _schedule_refresh(self):
        self._update_sidebar_status()

        page = self._pages.get(self._current_page)
        if page:
            try:
                page.refresh()
            except Exception:
                pass

        self.after(5000, self._schedule_refresh)

    def _update_sidebar_status(self):
        running = self.watcher and self.watcher.is_running()
        self.sidebar_status.configure(
            text="● Running" if running else "● Stopped",
            text_color=COLORS["accent_green"] if running else COLORS["danger"]
        )

        counts = db.get_alert_counts()
        unread = counts.get("unread", 0)

        self.alert_badge.configure(
            text=f"  {unread} new alert{'s' if unread != 1 else ''}  " if unread else ""
        )

    # ── Alert handler ─────────────────────────────────────────────────────

    def _on_alert(self, file_path, event_type, result):
        self.after(0, self._handle_alert_ui, file_path, event_type)

    def _handle_alert_ui(self, file_path, event_type):
        try:
            ToastNotification(self, file_path, event_type)
        except Exception:
            pass

        self._update_sidebar_status()

        if self._current_page in ("Dashboard", "Alerts", "Logs", "Monitoring"):
            page = self._pages.get(self._current_page)
            if page:
                try:
                    page.refresh()
                except Exception:
                    pass

    # ── Auto baseline ─────────────────────────────────────────────────────

    def _auto_baseline(self):
        paths = db.get_watch_paths()
        if paths:
            threading.Thread(
                target=lambda: create_baseline(paths),
                daemon=True
            ).start()

    # ── Close ─────────────────────────────────────────────────────────────

    def _on_close(self):
        if self.watcher:
            self.watcher.stop()
        self.destroy()