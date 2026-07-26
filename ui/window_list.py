"""
Windownimator 2.0 — PySide6 Window List Panel
Left sidebar showing all WindowObjects in the animation project.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QToolButton,
    QScrollArea, QFrame
)

if TYPE_CHECKING:
    from core.animation import Animation
    from core.window_object import WindowObject

ICON_SYMBOLS = {
    "info":     "ℹ️",
    "warning":  "⚠️",
    "error":    "❌",
    "question": "❓",
    "none":     "🪟",
}


class WindowListItemWidget(QFrame):
    selected = Signal(str)
    delete_requested = Signal(str)

    def __init__(self, win_obj: "WindowObject", is_selected: bool, parent=None):
        super().__init__(parent)
        self.win_obj = win_obj
        self.setObjectName("winItem")

        bg_col = "#1e293b" if is_selected else "#0f172a"
        border_col = "#3b82f6" if is_selected else "#1e293b"

        self.setStyleSheet(f"""
            QFrame#winItem {{
                background-color: {bg_col};
                border: 1px solid {border_col};
                border-radius: 8px;
            }}
            QFrame#winItem:hover {{
                border-color: #3b82f6;
            }}
            QFrame#winItem QLabel {{
                background-color: transparent;
                background: transparent;
                border: none;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 8, 10, 8)
        layout.setSpacing(10)

        # Icon Symbol
        icon_lbl = QLabel(ICON_SYMBOLS.get(win_obj.icon, "🪟"))
        icon_lbl.setFont(QFont("Segoe UI", 14))
        layout.addWidget(icon_lbl)

        # Info Box
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)

        name_lbl = QLabel(win_obj.name)
        name_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        name_lbl.setStyleSheet("color: #f8fafc;")
        info_layout.addWidget(name_lbl)

        title_txt = win_obj.title
        if len(title_txt) > 20:
            title_txt = title_txt[:19] + "…"
        title_lbl = QLabel(title_txt)
        title_lbl.setFont(QFont("Segoe UI", 8))
        title_lbl.setStyleSheet("color: #94a3b8;")
        info_layout.addWidget(title_lbl)

        layout.addLayout(info_layout)
        layout.addStretch()

        # Delete Button
        del_btn = QToolButton()
        del_btn.setText("✕")
        del_btn.setFixedSize(26, 26)
        del_btn.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        del_btn.setStyleSheet("""
            QToolButton {
                background: #3b1116;
                color: #f87171;
                border: 1px solid #ef4444;
                border-radius: 6px;
                padding: 0px;
                margin: 0px;
            }
            QToolButton:hover {
                background: #dc2626;
                color: #ffffff;
                border-color: #f87171;
            }
        """)
        del_btn.clicked.connect(lambda: self.delete_requested.emit(win_obj.id))
        layout.addWidget(del_btn)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.selected.emit(self.win_obj.id)


class QtWindowListPanel(QWidget):
    window_selected = Signal(str)
    add_window_requested = Signal(str)  # icon_type
    delete_window_requested = Signal(str)  # win_id

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation: Optional["Animation"] = None
        self._selected_id: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        hdr = QWidget()
        hdr.setFixedHeight(36)
        hdr.setStyleSheet("background-color: #0f172a; border-bottom: 1px solid #1e293b;")
        hdr_layout = QHBoxLayout(hdr)
        hdr_layout.setContentsMargins(12, 0, 12, 0)

        title = QLabel("СПИСОК ОКОН")
        title.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        title.setStyleSheet("color: #94a3b8; letter-spacing: 1px;")
        hdr_layout.addWidget(title)

        hdr_layout.addStretch()
        self.count_lbl = QLabel("0")
        self.count_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.count_lbl.setStyleSheet("color: #38bdf8;")
        hdr_layout.addWidget(self.count_lbl)

        layout.addWidget(hdr)

        # Quick Add Strip
        add_strip = QWidget()
        add_strip.setStyleSheet("background-color: #0b0d19; border-bottom: 1px solid #1e293b;")
        add_layout = QVBoxLayout(add_strip)
        add_layout.setContentsMargins(10, 8, 10, 8)
        add_layout.setSpacing(6)

        lbl_add = QLabel("Быстрое добавление:")
        lbl_add.setFont(QFont("Segoe UI", 8))
        lbl_add.setStyleSheet("color: #64748b;")
        add_layout.addWidget(lbl_add)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)

        quick_types = [("ℹ️ Info", "info"), ("⚠️ Warn", "warning"), ("❌ Error", "error"), ("❓ Quest", "question")]
        for label, icon_type in quick_types:
            btn = QPushButton(label)
            btn.setFont(QFont("Segoe UI", 9))
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e293b;
                    border: 1px solid #334155;
                    border-radius: 6px;
                    padding: 5px 8px;
                }
                QPushButton:hover {
                    background-color: #3b82f6;
                    border-color: #60a5fa;
                    color: white;
                }
            """)
            btn.clicked.connect(lambda _, t=icon_type: self.add_window_requested.emit(t))
            btn_row.addWidget(btn)

        add_layout.addLayout(btn_row)
        layout.addWidget(add_strip)

        # Scroll Area for List
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background-color: #0b0d19; border: none; }")

        self.list_container = QWidget()
        self.list_container.setStyleSheet("background-color: #0b0d19;")
        self.list_layout = QVBoxLayout(self.list_container)
        self.list_layout.setContentsMargins(8, 8, 8, 8)
        self.list_layout.setSpacing(6)
        self.list_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        scroll.setWidget(self.list_container)
        layout.addWidget(scroll)

    def refresh(self, animation: Optional["Animation"] = None, selected_id: Optional[str] = None):
        if animation is not None:
            self._animation = animation
        if selected_id is not None:
            self._selected_id = selected_id

        while self.list_layout.count():
            child = self.list_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._animation:
            self.count_lbl.setText("0")
            return

        wins = self._animation.windows
        self.count_lbl.setText(str(len(wins)))

        for win in wins:
            is_sel = (win.id == self._selected_id)
            item_widget = WindowListItemWidget(win, is_sel)
            item_widget.selected.connect(self.window_selected.emit)
            item_widget.delete_requested.connect(self.delete_window_requested.emit)
            self.list_layout.addWidget(item_widget)

    def set_selected(self, win_id: Optional[str]):
        self._selected_id = win_id
        self.refresh()
