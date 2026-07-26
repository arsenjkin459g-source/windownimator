"""
Windownimator 2.0 — PySide6 Keyframe Timeline Widget
Horizontal timeline with interactive Keyframe cards.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QMenu, QGraphicsDropShadowEffect
)

if TYPE_CHECKING:
    from core.animation import Animation
    from core.keyframe import Keyframe

from ui.styles import get_current_theme

EASING_SHORT = {
    "linear":      "—",
    "ease_in":     "▶",
    "ease_out":    "◀",
    "ease_in_out": "◈",
    "bounce":      "⤷",
    "elastic":     "〜",
}


class KeyframeCard(QFrame):
    clicked = Signal(str)
    context_requested = Signal(str, object)

    def __init__(self, kf: "Keyframe", index: int, selected: bool, win_count: int, parent=None):
        super().__init__(parent)
        self.kf = kf
        self.index = index
        self.selected = selected
        
        self.setFixedSize(130, 95)
        self.setObjectName("kfCard")

        # Dynamic Styling
        t = get_current_theme()
        bg_col = t["accent"] if selected else t["bg_card"]
        border_col = t["accent_hover"] if selected else t["border_input"]
        self.setStyleSheet(f"""
            QFrame#kfCard {{
                background-color: {bg_col};
                border: 2px solid {border_col};
                border-radius: 10px;
            }}
            QFrame#kfCard:hover {{
                border-color: {t['accent']};
            }}
            QFrame#kfCard QLabel {{
                background-color: transparent;
                background: transparent;
                border: none;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(2)

        # Header Badge
        hdr_layout = QHBoxLayout()
        idx_lbl = QLabel(f"#{index + 1}")
        idx_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        idx_lbl.setStyleSheet("background: transparent; color: #cbd5e1;" if selected else "background: transparent; color: #94a3b8;")
        hdr_layout.addWidget(idx_lbl)
        hdr_layout.addStretch()

        win_lbl = QLabel(f"Окна: {win_count}")
        win_lbl.setFont(QFont("Segoe UI", 9))
        win_lbl.setStyleSheet("background: transparent; color: #ffffff;" if selected else "background: transparent; color: #cbd5e1;")
        hdr_layout.addWidget(win_lbl)
        layout.addLayout(hdr_layout)

        # Label
        lbl_text = kf.get_display_label()
        if len(lbl_text) > 13:
            lbl_text = lbl_text[:12] + "…"
        main_lbl = QLabel(lbl_text)
        main_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        main_lbl.setStyleSheet("background: transparent; color: #ffffff;" if selected else "background: transparent; color: #f8fafc;")
        main_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(main_lbl)

        layout.addStretch()

        # Easing & Duration
        eas_symbol = EASING_SHORT.get(kf.easing, "◈")
        dur_lbl = QLabel(f"{eas_symbol} {kf.duration_ms} ms")
        dur_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
        dur_lbl.setStyleSheet("background: transparent; color: #ffffff;" if selected else f"background: transparent; color: {t['accent']};")
        dur_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(dur_lbl)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.kf.id)
        elif event.button() == Qt.MouseButton.RightButton:
            self.context_requested.emit(self.kf.id, event.globalPos())


class QtTimeline(QWidget):
    keyframe_selected = Signal(str)
    add_keyframe_requested = Signal()
    delete_keyframe_requested = Signal(str)
    duplicate_keyframe_requested = Signal(str)
    move_left_requested = Signal(str)
    move_right_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._animation: Optional["Animation"] = None
        self._selected_id: Optional[str] = None
        self._build_ui()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header Info Strip
        self._hdr = QWidget()
        self._hdr.setFixedHeight(28)
        hdr_layout = QHBoxLayout(self._hdr)
        hdr_layout.setContentsMargins(12, 0, 12, 0)

        self._title_lbl = QLabel("ТАЙМЛАЙН КЛЮЧЕВЫХ КАДРОВ")
        self._title_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        hdr_layout.addWidget(self._title_lbl)

        hdr_layout.addStretch()

        self.info_lbl = QLabel("0 кадров")
        self.info_lbl.setFont(QFont("Segoe UI", 9))
        hdr_layout.addWidget(self.info_lbl)

        main_layout.addWidget(self._hdr)

        # Scroll Area for Cards
        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self._scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.container = QWidget()
        self.card_layout = QHBoxLayout(self.container)
        self.card_layout.setContentsMargins(12, 8, 12, 8)
        self.card_layout.setSpacing(12)
        self.card_layout.setSizeConstraint(QHBoxLayout.SizeConstraint.SetMinAndMaxSize)

        self._scroll.setWidget(self.container)
        self._scroll.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop)
        main_layout.addWidget(self._scroll)

        self.update_theme()

    def update_theme(self):
        t = get_current_theme()
        self._hdr.setStyleSheet(f"background-color: {t['bg_input']}; border-top: 1px solid {t['border']};")
        self._title_lbl.setStyleSheet(f"color: {t['text_muted']}; letter-spacing: 1px;")
        self.info_lbl.setStyleSheet(f"color: {t['text_muted']};")
        self._scroll.setStyleSheet(f"QScrollArea {{ background-color: {t['bg_input']}; border: none; }}")
        self.container.setStyleSheet(f"background-color: {t['bg_input']};")

    def refresh(self, animation: Optional["Animation"] = None, selected_id: Optional[str] = None):
        if animation is not None:
            self._animation = animation
        if selected_id is not None:
            self._selected_id = selected_id

        # Clear layout
        while self.card_layout.count():
            child = self.card_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self._animation:
            return

        total_ms = 0
        for i, kf in enumerate(self._animation.keyframes):
            if i < len(self._animation.keyframes) - 1:
                total_ms += kf.duration_ms

            visible_count = sum(1 for w in self._animation.windows if kf.get_state(w.id).visible)
            is_sel = (kf.id == self._selected_id)

            card = KeyframeCard(kf, i, is_sel, visible_count)
            card.clicked.connect(self.keyframe_selected.emit)
            card.context_requested.connect(self._show_context_menu)
            self.card_layout.addWidget(card)

            # Arrow Separator between frames
            if i < len(self._animation.keyframes) - 1:
                arr_lbl = QLabel(f"➔\n{kf.duration_ms}ms")
                arr_lbl.setFont(QFont("Segoe UI", 8, QFont.Weight.Bold))
                arr_lbl.setStyleSheet(f"color: {get_current_theme()['accent']};")
                arr_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
                self.card_layout.addWidget(arr_lbl)

        # Add Button
        add_btn = QPushButton("＋")
        add_btn.setFixedSize(60, 95)
        add_btn.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        _t = get_current_theme()
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {_t['bg_dark']};
                border: 2px dashed {_t['accent']};
                border-radius: 10px;
                color: {_t['accent']};
            }}
            QPushButton:hover {{
                background-color: {_t['bg_card']};
                color: {_t['accent_hover']};
            }}
        """)
        add_btn.clicked.connect(self.add_keyframe_requested.emit)
        self.card_layout.addWidget(add_btn)

        self.card_layout.addStretch()

        num_kf = len(self._animation.keyframes)
        self.info_lbl.setText(f"{num_kf} кадров  |  ~{total_ms} ms ({total_ms/1000.0:.1f}s)")

    def _show_context_menu(self, kf_id: str, pos):
        menu = QMenu(self)
        _t = get_current_theme()
        menu.setStyleSheet(f"QMenu {{ background-color: {_t['bg_dark']}; color: {_t['text']}; border: 1px solid {_t['border_input']}; }}")
        
        del_act = menu.addAction("Удалить кадр")
        dup_act = menu.addAction("Дублировать")
        menu.addSeparator()
        left_act = menu.addAction("Сдвинуть влево")
        right_act = menu.addAction("Сдвинуть вправо")

        action = menu.exec(pos)
        if action == del_act:
            self.delete_keyframe_requested.emit(kf_id)
        elif action == dup_act:
            self.duplicate_keyframe_requested.emit(kf_id)
        elif action == left_act:
            self.move_left_requested.emit(kf_id)
        elif action == right_act:
            self.move_right_requested.emit(kf_id)
