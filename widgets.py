"""
Reusable GUI widgets used across all pages.
"""

import tkinter as tk
import customtkinter as ctk
from .theme import COLORS, FONT_H2, FONT_H3, FONT_BODY, FONT_SMALL, FONT_MONO_S


class StatCard(ctk.CTkFrame):
    """A stat card showing a number + label + optional color accent."""

    def __init__(self, parent, title, value="0", color=None, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_card"],
                         corner_radius=10, **kwargs)
        self.configure(border_width=1, border_color=COLORS["border"])

        accent_color = color or COLORS["accent_blue"]

        # Top accent bar
        bar = tk.Frame(self, bg=accent_color, height=4)
        bar.pack(fill="x", side="top")

        self.value_label = ctk.CTkLabel(
            self, text=str(value),
            font=("Segoe UI", 32, "bold"),
            text_color=accent_color
        )
        self.value_label.pack(pady=(14, 2))

        self.title_label = ctk.CTkLabel(
            self, text=title,
            font=FONT_SMALL,
            text_color=COLORS["text_secondary"]
        )
        self.title_label.pack(pady=(0, 14))

    def update_value(self, value, color=None):
        self.value_label.configure(text=str(value))
        if color:
            self.value_label.configure(text_color=color)


class SectionHeader(ctk.CTkFrame):
    """A section header with title and optional subtitle."""

    def __init__(self, parent, title, subtitle=None, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)
        ctk.CTkLabel(self, text=title, font=FONT_H2,
                     text_color=COLORS["text_primary"]).pack(anchor="w")
        if subtitle:
            ctk.CTkLabel(self, text=subtitle, font=FONT_SMALL,
                         text_color=COLORS["text_secondary"]).pack(anchor="w")


class SimpleTable(ctk.CTkFrame):
    """
    A scrollable table built from a tkinter Treeview.
    columns: list of (col_id, header_text, width) tuples
    """

    def __init__(self, parent, columns, height=15, **kwargs):
        super().__init__(parent, fg_color="transparent", **kwargs)

        # Style the treeview
        import tkinter.ttk as ttk
        style = ttk.Style()
        style.theme_use("default")
        style.configure("FIM.Treeview",
                        background=COLORS["bg_panel"],
                        foreground=COLORS["text_primary"],
                        rowheight=28,
                        fieldbackground=COLORS["bg_panel"],
                        bordercolor=COLORS["border"],
                        borderwidth=0,
                        font=("Segoe UI", 11))
        style.configure("FIM.Treeview.Heading",
                        background=COLORS["bg_card"],
                        foreground=COLORS["text_secondary"],
                        font=("Segoe UI", 11, "bold"),
                        borderwidth=0,
                        relief="flat")
        style.map("FIM.Treeview",
                  background=[("selected", COLORS["bg_card"])],
                  foreground=[("selected", COLORS["accent"])])
        style.layout("FIM.Treeview", [("FIM.Treeview.treearea", {"sticky": "nswe"})])

        col_ids = [c[0] for c in columns]
        self.tree = ttk.Treeview(self, columns=col_ids, show="headings",
                                 height=height, style="FIM.Treeview",
                                 selectmode="browse")

        for col_id, header, width in columns:
            self.tree.heading(col_id, text=header)
            self.tree.column(col_id, width=width, minwidth=40, anchor="w")

        # Scrollbars
        vsb = ctk.CTkScrollbar(self, command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)

        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")

        # Alternating row colors
        self.tree.tag_configure("odd",  background=COLORS["bg_panel"])
        self.tree.tag_configure("even", background="#12192e")
        self.tree.tag_configure("modified", foreground=COLORS["warning"])
        self.tree.tag_configure("deleted",  foreground=COLORS["danger"])
        self.tree.tag_configure("created",  foreground=COLORS["accent_green"])
        self.tree.tag_configure("error",    foreground=COLORS["danger"])

    def clear(self):
        for item in self.tree.get_children():
            self.tree.delete(item)

    def insert_row(self, values, tags=None):
        count = len(self.tree.get_children())
        row_tag = "even" if count % 2 == 0 else "odd"
        all_tags = [row_tag] + (list(tags) if tags else [])
        self.tree.insert("", "end", values=values, tags=all_tags)

    def load_rows(self, rows_data, tag_fn=None):
        """Bulk-load rows. tag_fn(row_values) → list of extra tag strings."""
        self.clear()
        for i, row in enumerate(rows_data):
            base_tag = "even" if i % 2 == 0 else "odd"
            extra = tag_fn(row) if tag_fn else []
            self.tree.insert("", "end", values=row, tags=[base_tag] + extra)


class StatusBadge(ctk.CTkLabel):
    """Colored inline badge for event types / severity."""

    PRESETS = {
        "MODIFIED": ("#e67e22", "#1a1000"),
        "DELETED":  ("#e74c3c", "#1a0000"),
        "CREATED":  ("#2ecc71", "#001a00"),
        "OK":       ("#27ae60", "#001a00"),
        "HIGH":     ("#e74c3c", "#1a0000"),
        "MEDIUM":   ("#e67e22", "#1a0800"),
        "LOW":      ("#2ecc71", "#001a00"),
        "RUNNING":  ("#2ecc71", "#001a00"),
        "STOPPED":  ("#e74c3c", "#1a0000"),
        "WARNING":  ("#e67e22", "#1a0800"),
        "ERROR":    ("#e74c3c", "#1a0000"),
    }

    def __init__(self, parent, text, **kwargs):
        fg, bg = self.PRESETS.get(text.upper(), (COLORS["text_secondary"], COLORS["bg_card"]))
        super().__init__(parent, text=f"  {text}  ",
                         font=("Segoe UI", 10, "bold"),
                         text_color=fg,
                         fg_color=bg,
                         corner_radius=4,
                         **kwargs)


class AlertRow(ctk.CTkFrame):
    """Single alert row card for the recent alerts panel."""

    def __init__(self, parent, alert_dict, **kwargs):
        super().__init__(parent, fg_color=COLORS["bg_panel"],
                         corner_radius=8,
                         border_width=1,
                         border_color=COLORS["border"],
                         **kwargs)

        event = alert_dict.get("event_type", "?")
        from .theme import EVENT_COLORS
        color = EVENT_COLORS.get(event, COLORS["text_secondary"])

        left = ctk.CTkFrame(self, fg_color=color, width=4, corner_radius=0)
        left.pack(side="left", fill="y")
        left.pack_propagate(False)

        inner = ctk.CTkFrame(self, fg_color="transparent")
        inner.pack(side="left", fill="both", expand=True, padx=8, pady=6)

        top = ctk.CTkFrame(inner, fg_color="transparent")
        top.pack(fill="x")
        ctk.CTkLabel(top, text=event, font=("Segoe UI", 11, "bold"),
                     text_color=color).pack(side="left")
        ctk.CTkLabel(top, text=alert_dict.get("timestamp", ""),
                     font=FONT_SMALL,
                     text_color=COLORS["text_muted"]).pack(side="right")

        path = alert_dict.get("file_path", "")
        if len(path) > 60:
            path = "..." + path[-57:]
        ctk.CTkLabel(inner, text=path, font=FONT_MONO_S,
                     text_color=COLORS["text_secondary"],
                     anchor="w").pack(fill="x")
