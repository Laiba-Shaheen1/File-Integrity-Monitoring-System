"""
Theme constants for the FIM GUI.
Uses CustomTkinter color system.
"""

# ── Palette ───────────────────────────────────────────────────────────────────
COLORS = {
    "bg_dark":     "#1a1a2e",
    "bg_panel":    "#16213e",
    "bg_card":     "#0f3460",
    "bg_sidebar":  "#0d0d1a",

    "accent":      "#e94560",
    "accent_dim":  "#a8304a",
    "accent_green":"#2ecc71",
    "accent_yellow":"#f39c12",
    "accent_blue": "#3498db",

    "text_primary":   "#e0e0e0",
    "text_secondary": "#a0a0b0",
    "text_muted":     "#606070",

    "success":  "#27ae60",
    "warning":  "#e67e22",
    "danger":   "#e74c3c",
    "info":     "#2980b9",
    "ok":       "#27ae60",

    "border":   "#2a2a4a",
}

# ── Event type → color ────────────────────────────────────────────────────────
EVENT_COLORS = {
    "MODIFIED": "#e67e22",
    "DELETED":  "#e74c3c",
    "CREATED":  "#2ecc71",
    "BASELINE": "#3498db",
    "OK":       "#27ae60",
    "ERROR":    "#e74c3c",
    "WARNING":  "#e67e22",
    "MONITOR_START": "#2ecc71",
    "MONITOR_STOP":  "#e74c3c",
    "WATCH":    "#3498db",
}

SEVERITY_COLORS = {
    "HIGH":   "#e74c3c",
    "MEDIUM": "#e67e22",
    "LOW":    "#2ecc71",
}

# ── Nav items ─────────────────────────────────────────────────────────────────
NAV_ITEMS = [
    ("Dashboard",   "📊"),
    ("Monitoring",  "🔍"),
    ("Alerts",      "🚨"),
    ("Logs",        "📋"),
    ("Reports",     "📄"),
    ("Settings",    "⚙️"),
]

FONT_TITLE  = ("Segoe UI", 22, "bold")
FONT_H2     = ("Segoe UI", 16, "bold")
FONT_H3     = ("Segoe UI", 13, "bold")
FONT_BODY   = ("Segoe UI", 12)
FONT_SMALL  = ("Segoe UI", 10)
FONT_MONO   = ("Consolas", 11)
FONT_MONO_S = ("Consolas", 10)
