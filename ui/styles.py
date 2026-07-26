"""
Windownimator — PySide6 Dynamic Color Theme QSS System
"""

THEMES = {
    "navy": {
        "name": "Тёмно-синяя",
        "bg_dark": "#0f172a",
        "bg_card": "#1e293b",
        "bg_input": "#020617",
        "border": "#1e293b",
        "border_input": "#334155",
        "accent": "#3b82f6",
        "accent_hover": "#60a5fa",
        "accent_press": "#1d4ed8",
        "text": "#e2e8f0",
        "text_muted": "#94a3b8",
        "gradient_tb_end": "#1e1b4b",
    },
    "oled": {
        "name": "Чёрная",
        "bg_dark": "#000000",
        "bg_card": "#09090b",
        "bg_input": "#18181b",
        "border": "#27272a",
        "border_input": "#3f3f46",
        "accent": "#6366f1",
        "accent_hover": "#818cf8",
        "accent_press": "#4338ca",
        "text": "#f4f4f5",
        "text_muted": "#a1a1aa",
        "gradient_tb_end": "#18181b",
    },
    "cyber": {
        "name": "Фиолетовая",
        "bg_dark": "#11081f",
        "bg_card": "#201037",
        "bg_input": "#0a0414",
        "border": "#2e174d",
        "border_input": "#4c287a",
        "accent": "#a855f7",
        "accent_hover": "#c084fc",
        "accent_press": "#7e22ce",
        "text": "#f3e8ff",
        "text_muted": "#c084fc",
        "gradient_tb_end": "#3b0764",
    },
    "emerald": {
        "name": "Зелёная",
        "bg_dark": "#062016",
        "bg_card": "#0e3526",
        "bg_input": "#020f0a",
        "border": "#134e38",
        "border_input": "#1f6e52",
        "accent": "#10b981",
        "accent_hover": "#34d399",
        "accent_press": "#047857",
        "text": "#ecfdf5",
        "text_muted": "#6ee7b7",
        "gradient_tb_end": "#064e3b",
    },
    "crimson": {
        "name": "Красная",
        "bg_dark": "#1f0909",
        "bg_card": "#381010",
        "bg_input": "#0f0303",
        "border": "#4e1717",
        "border_input": "#702222",
        "accent": "#ef4444",
        "accent_hover": "#f87171",
        "accent_press": "#b91c1c",
        "text": "#fef2f2",
        "text_muted": "#fca5a5",
        "gradient_tb_end": "#450a0a",
    },
}

CURRENT_THEME_KEY = "navy"


def set_current_theme(key: str):
    global CURRENT_THEME_KEY
    if key in THEMES:
        CURRENT_THEME_KEY = key


def get_current_theme() -> dict:
    return THEMES.get(CURRENT_THEME_KEY, THEMES["navy"])


def get_theme_qss(theme_key: str = "navy") -> str:
    set_current_theme(theme_key)
    t = get_current_theme()
    return f"""
QWidget {{
    color: {t['text']};
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: {t['accent']};
    selection-color: #ffffff;
}}

QMainWindow, QSplitter {{
    background-color: transparent;
}}

QDialog, QMessageBox {{
    background-color: {t['bg_dark']};
}}

QGraphicsView, QtStage {{
    background-color: transparent;
    background: transparent;
    border: none;
}}

QLabel {{
    background-color: transparent;
    color: {t['text']};
}}

/* Menubar */
QMenuBar {{
    background-color: {t['bg_dark']};
    color: {t['text']};
    border-bottom: 1px solid {t['border']};
}}

QMenuBar::item {{
    background-color: transparent;
    padding: 6px 12px;
}}

QMenuBar::item:selected {{
    background-color: {t['bg_card']};
    color: {t['accent']};
}}

QMenu {{
    background-color: {t['bg_dark']};
    color: {t['text']};
    border: 1px solid {t['border_input']};
}}

QMenu::item {{
    padding: 6px 20px;
}}

QMenu::item:selected {{
    background-color: {t['accent']};
    color: #ffffff;
}}

/* ToolBar & Header */
QToolBar {{
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 {t['bg_dark']}, stop:1 {t['gradient_tb_end']});
    border-bottom: 1px solid {t['border']};
    spacing: 8px;
    padding: 6px 12px;
}}

QToolButton {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_input']};
    border-radius: 6px;
    padding: 6px 14px;
    color: {t['text']};
    font-weight: 600;
}}

QToolButton:hover {{
    background-color: {t['accent']};
    border-color: {t['accent_hover']};
    color: #ffffff;
}}

QToolButton:pressed {{
    background-color: {t['accent_press']};
}}

/* Cards & Frames */
QFrame, QGroupBox {{
    background-color: {t['bg_dark']};
}}

QFrame.panelFrame {{
    background-color: {t['bg_dark']};
    border: 1px solid {t['border']};
    border-radius: 10px;
}}

QFrame.card {{
    background-color: {t['bg_card']};
    border: 1px solid {t['border_input']};
    border-radius: 8px;
}}

QFrame.card:hover {{
    border-color: {t['accent']};
}}

/* ScrollArea */
QScrollArea, QScrollArea > QWidget > QWidget {{
    background-color: {t['bg_dark']};
    border: none;
}}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {{
    background-color: {t['bg_input']};
    border: 1px solid {t['border_input']};
    border-radius: 6px;
    padding: 6px 10px;
    color: {t['text']};
}}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {{
    border: 1px solid {t['accent']};
    background-color: {t['bg_dark']};
}}

QComboBox::drop-down {{
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid {t['border_input']};
}}

QComboBox QAbstractItemView {{
    background-color: {t['bg_dark']};
    border: 1px solid {t['border_input']};
    selection-background-color: {t['accent']};
    padding: 4px;
}}

/* Push Buttons */
QPushButton {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['bg_card']}, stop:1 {t['bg_dark']});
    border: 1px solid {t['border_input']};
    border-radius: 6px;
    padding: 7px 16px;
    color: {t['text']};
    font-weight: 600;
}}

QPushButton:hover {{
    background: {t['accent']};
    border-color: {t['accent_hover']};
    color: #ffffff;
}}

QPushButton:pressed {{
    background: {t['accent_press']};
}}

QPushButton#btnPrimary {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 {t['accent']}, stop:1 {t['accent_press']});
    border: 1px solid {t['accent_hover']};
    color: #ffffff;
}}

QPushButton#btnPrimary:hover {{
    background: {t['accent_hover']};
}}

QPushButton#btnSuccess {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #16a34a, stop:1 #15803d);
    border: 1px solid #4ade80;
    color: #ffffff;
}}

QPushButton#btnSuccess:hover {{
    background: #22c55e;
}}

QPushButton#btnDanger {{
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
    border: 1px solid #f87171;
    color: #ffffff;
}}

QPushButton#btnDanger:hover {{
    background: #ef4444;
}}

/* ScrollBars */
QScrollBar:vertical {{
    background: {t['bg_dark']};
    width: 10px;
    margin: 0px;
}}

QScrollBar::handle:vertical {{
    background: {t['border_input']};
    min-height: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:vertical:hover {{
    background: {t['accent']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

QScrollBar:horizontal {{
    background: {t['bg_dark']};
    height: 10px;
    margin: 0px;
}}

QScrollBar::handle:horizontal {{
    background: {t['border_input']};
    min-width: 20px;
    border-radius: 5px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {t['accent']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0px;
}}

/* Status Bar */
QStatusBar {{
    background: {t['bg_input']};
    border-top: 1px solid {t['border']};
    color: {t['text_muted']};
}}

/* Tab Widget */
QTabWidget::pane {{
    border: 1px solid {t['border']};
    background: {t['bg_dark']};
    border-radius: 6px;
}}

QTabBar::tab {{
    background: {t['bg_input']};
    border: 1px solid {t['border']};
    padding: 8px 16px;
    color: {t['text_muted']};
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}}

QTabBar::tab:selected {{
    background: {t['bg_dark']};
    color: {t['accent']};
    border-bottom-color: {t['bg_dark']};
    font-weight: bold;
}}
"""

DARK_THEME_QSS = get_theme_qss("navy")
