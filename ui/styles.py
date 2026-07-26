"""
Windownimator — PySide6 Modern Dark Theme QSS
"""

DARK_THEME_QSS = """
/* Global Application Style */
QWidget {
    color: #e2e8f0;
    font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    font-size: 13px;
    selection-background-color: #2563eb;
    selection-color: #ffffff;
}

QMainWindow, QSplitter {
    background-color: transparent;
}

QLabel {
    background-color: transparent;
}

QGraphicsView, QtStage {
    background-color: transparent;
    background: transparent;
    border: none;
}

/* Menubar */
QMenuBar {
    background-color: #0f172a;
    color: #f8fafc;
    border-bottom: 1px solid #1e293b;
}

QMenuBar::item {
    background-color: transparent;
    padding: 6px 12px;
}

QMenuBar::item:selected {
    background-color: #1e293b;
    color: #3b82f6;
}

QMenu {
    background-color: #0f172a;
    color: #f8fafc;
    border: 1px solid #334155;
}

QMenu::item {
    padding: 6px 20px;
}

QMenu::item:selected {
    background-color: #2563eb;
    color: #ffffff;
}

/* ToolBar & Header */
QToolBar {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #0f172a, stop:1 #1e1b4b);
    border-bottom: 1px solid #1e293b;
    spacing: 8px;
    padding: 6px 12px;
}

QToolButton {
    background-color: rgba(30, 41, 59, 0.7);
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 14px;
    color: #f1f5f9;
    font-weight: 600;
}

QToolButton:hover {
    background-color: #3b82f6;
    border-color: #60a5fa;
    color: #ffffff;
}

QToolButton:pressed {
    background-color: #1d4ed8;
}

/* Cards & Frames */
QFrame.panelFrame {
    background-color: #0f172a;
    border: 1px solid #1e293b;
    border-radius: 10px;
}

QFrame.card {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 8px;
}

QFrame.card:hover {
    border-color: #3b82f6;
}

/* ScrollArea */
QScrollArea, QScrollArea > QWidget > QWidget {
    background-color: #0f172a;
    border: none;
}

/* Input Fields */
QLineEdit, QTextEdit, QPlainTextEdit, QSpinBox, QDoubleSpinBox, QComboBox {
    background-color: #020617;
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 6px 10px;
    color: #f8fafc;
}

QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus, QSpinBox:focus, QDoubleSpinBox:focus, QComboBox:focus {
    border: 1px solid #3b82f6;
    background-color: #090d16;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #334155;
}

QComboBox QAbstractItemView {
    background-color: #0f172a;
    border: 1px solid #334155;
    selection-background-color: #2563eb;
    padding: 4px;
}

/* Push Buttons */
QPushButton {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #1e293b, stop:1 #0f172a);
    border: 1px solid #334155;
    border-radius: 6px;
    padding: 7px 16px;
    color: #f8fafc;
    font-weight: 600;
}

QPushButton:hover {
    background: #3b82f6;
    border-color: #60a5fa;
    color: #ffffff;
}

QPushButton:pressed {
    background: #1d4ed8;
}

QPushButton#btnPrimary {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #2563eb, stop:1 #1d4ed8);
    border: 1px solid #60a5fa;
    color: #ffffff;
}

QPushButton#btnPrimary:hover {
    background: #3b82f6;
}

QPushButton#btnSuccess {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #16a34a, stop:1 #15803d);
    border: 1px solid #4ade80;
    color: #ffffff;
}

QPushButton#btnSuccess:hover {
    background: #22c55e;
}

QPushButton#btnDanger {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1, stop:0 #dc2626, stop:1 #b91c1c);
    border: 1px solid #f87171;
    color: #ffffff;
}

QPushButton#btnDanger:hover {
    background: #ef4444;
}

/* ScrollBars */
QScrollBar:vertical {
    background: #0f172a;
    width: 10px;
    margin: 0px;
}

QScrollBar::handle:vertical {
    background: #334155;
    min-height: 20px;
    border-radius: 5px;
}

QScrollBar::handle:vertical:hover {
    background: #475569;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}

QScrollBar:horizontal {
    background: #0f172a;
    height: 10px;
    margin: 0px;
}

QScrollBar::handle:horizontal {
    background: #334155;
    min-width: 20px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background: #475569;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}

/* Status Bar */
QStatusBar {
    background: #090d16;
    border-top: 1px solid #1e293b;
    color: #64748b;
}

/* Tab Widget */
QTabWidget::pane {
    border: 1px solid #1e293b;
    background: #0f172a;
    border-radius: 6px;
}

QTabBar::tab {
    background: #090d16;
    border: 1px solid #1e293b;
    padding: 8px 16px;
    color: #94a3b8;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
}

QTabBar::tab:selected {
    background: #0f172a;
    color: #3b82f6;
    border-bottom-color: #0f172a;
    font-weight: bold;
}
"""
