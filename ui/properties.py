"""
Windownimator 2.0 — PySide6 Properties Panel
Right sidebar with tabs for Window properties and Keyframe transition properties.
"""

from __future__ import annotations
from typing import Optional, TYPE_CHECKING
from PySide6.QtCore import Qt, Signal, QVariantAnimation, QPointF
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QTextEdit, QPlainTextEdit,
    QComboBox, QSpinBox, QTabWidget, QFileDialog, QPushButton, QFrame, QScrollArea
)

if TYPE_CHECKING:
    from core.window_object import WindowObject
    from core.keyframe import Keyframe

from ui.styles import get_current_theme

ICON_OPTIONS = [("ℹ️  Информация", "info"), ("⚠️  Предупреждение", "warning"),
                ("❌  Ошибка", "error"), ("❓  Вопрос", "question"), ("🪟  Без иконки", "none")]
BTN_OPTIONS  = [("OK", "ok"), ("OK / Отмена", "okcancel"), ("Да / Нет", "yesno"),
                ("Да / Нет / Отмена", "yesnocancel"), ("Повтор / Отмена", "retrycancel"),
                ("Прервать / Повтор / Игнорировать", "abortretryignore")]
SYS_SOUNDS   = [("— Нет звука", ""), ("🔔 Информация", "info"), ("⚡ Предупреждение", "warning"),
                ("🔴 Ошибка", "error"), ("❓ Вопрос", "question")]
EASINGS      = [("Линейное", "linear"), ("Ease In (разгон)", "ease_in"),
                ("Ease Out (торможение)", "ease_out"), ("Ease In-Out (плавно)", "ease_in_out"),
                ("Пружина (отскок)", "bounce"), ("Упругое (elastic)", "elastic")]


class EasingPreviewWidget(QWidget):
    """Custom paint widget rendering animated easing curve and dot preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.old_easing = "ease_in_out"
        self.new_easing = "ease_in_out"
        self.morph_progress = 1.0  # 0.0 to 1.0
        self.dot_progress = 0.0    # 0.0 to 1.0 (moving dot)

        _t = get_current_theme()
        self.setStyleSheet(f"background-color: {_t['bg_input']}; border: 1px solid {_t['border_input']}; border-radius: 6px;")

        # Morph Animation (smooth transition between curves)
        self.morph_anim = QVariantAnimation(self)
        self.morph_anim.setDuration(400)
        self.morph_anim.setStartValue(0.0)
        self.morph_anim.setEndValue(1.0)
        self.morph_anim.valueChanged.connect(self._on_morph_step)

        # Ball/Dot Loop Animation (moves along the curve)
        self.dot_anim = QVariantAnimation(self)
        self.dot_anim.setDuration(1200)
        self.dot_anim.setStartValue(0.0)
        self.dot_anim.setEndValue(1.0)
        self.dot_anim.valueChanged.connect(self._on_dot_step)

    def set_easing(self, easing: str):
        if easing == self.new_easing and self.morph_progress >= 1.0:
            return

        self.old_easing = self.new_easing
        self.new_easing = easing
        self.morph_progress = 0.0

        self.morph_anim.stop()
        self.morph_anim.start()

        self.dot_anim.stop()
        self.dot_anim.start()

    def _on_morph_step(self, val):
        self.morph_progress = float(val)
        self.update()

    def _on_dot_step(self, val):
        self.dot_progress = float(val)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        pad = 12

        # Draw grid
        _t = get_current_theme()
        painter.setPen(QPen(QColor(_t["border"]), 1, Qt.PenStyle.DashLine))
        painter.drawLine(pad, h - pad, w - pad, h - pad)
        painter.drawLine(pad, pad, pad, h - pad)

        try:
            from core.tweener import EASING_FUNCS
            fn_old = EASING_FUNCS.get(self.old_easing, EASING_FUNCS["ease_in_out"])
            fn_new = EASING_FUNCS.get(self.new_easing, EASING_FUNCS["ease_in_out"])

            steps = 80
            prev_point = None
            alpha = self.morph_progress

            # Current active interpolated curve function
            def interpolated_fn(t):
                return fn_old(t) * (1.0 - alpha) + fn_new(t) * alpha

            # Draw Morphing Curve
            painter.setPen(QPen(QColor(_t["accent"]), 2.5))
            for i in range(steps + 1):
                t = i / steps
                v = interpolated_fn(t)
                x = pad + t * (w - 2 * pad)
                y = (h - pad) - v * (h - 2 * pad)

                curr_point = (x, y)
                if prev_point:
                    painter.drawLine(prev_point[0], prev_point[1], curr_point[0], curr_point[1])
                prev_point = curr_point

            # Draw Animated Ball along current curve
            t_ball = self.dot_progress
            v_ball = interpolated_fn(t_ball)
            bx = pad + t_ball * (w - 2 * pad)
            by = (h - pad) - v_ball * (h - 2 * pad)

            # Outer glow dot
            painter.setPen(Qt.PenStyle.NoPen)
            r, g, b = tuple(int(QColor(_t["accent_hover"]).name()[i:i+2], 16) for i in (1, 3, 5))
            painter.setBrush(QBrush(QColor(r, g, b, 100)))
            painter.drawEllipse(QPointF(bx, by), 7, 7)

            # Inner bright dot
            painter.setBrush(QBrush(QColor("#ffffff")))
            painter.drawEllipse(QPointF(bx, by), 4, 4)

        except Exception:
            pass


class QtPropertiesPanel(QWidget):
    window_changed   = Signal()
    keyframe_changed = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._win: Optional["WindowObject"] = None
        self._kf:  Optional["Keyframe"]     = None
        self._updating = False
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        self._hdr = QWidget()
        self._hdr.setFixedHeight(36)
        hdr_layout = QHBoxLayout(self._hdr)
        hdr_layout.setContentsMargins(12, 0, 12, 0)

        self._title_lbl = QLabel("СВОЙСТВА")
        self._title_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        hdr_layout.addWidget(self._title_lbl)

        layout.addWidget(self._hdr)

        self._section_labels = []

        # Tabs
        self.tabs = QTabWidget()

        # --- Window Tab ---
        self._win_tab = QWidget()
        win_layout = QVBoxLayout(self._win_tab)
        win_layout.setContentsMargins(12, 12, 12, 12)
        win_layout.setSpacing(10)

        win_layout.addWidget(self._create_section_lbl("СОДЕРЖИМОЕ"))

        win_layout.addWidget(QLabel("Имя окна:"))
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.name_edit)

        win_layout.addWidget(QLabel("Заголовок окна:"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.title_edit)

        win_layout.addWidget(QLabel("Текст сообщения:"))
        self.msg_edit = QPlainTextEdit()
        self.msg_edit.setFixedHeight(55)
        self.msg_edit.textChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.msg_edit)

        win_layout.addSpacing(14)
        win_layout.addWidget(self._create_section_lbl("ВИД И ИКОНКА"))

        win_layout.addWidget(QLabel("Иконка:"))
        self.icon_combo = QComboBox()
        for label, val in ICON_OPTIONS:
            self.icon_combo.addItem(label, val)
        self.icon_combo.currentIndexChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.icon_combo)

        win_layout.addWidget(QLabel("Кнопки:"))
        self.btn_combo = QComboBox()
        for label, val in BTN_OPTIONS:
            self.btn_combo.addItem(label, val)
        self.btn_combo.currentIndexChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.btn_combo)

        win_layout.addSpacing(14)
        win_layout.addWidget(self._create_section_lbl("ЗВУКИ"))

        win_layout.addWidget(QLabel("Системный звук:"))
        self.sound_combo = QComboBox()
        for label, val in SYS_SOUNDS:
            self.sound_combo.addItem(label, val)
        self.sound_combo.currentIndexChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.sound_combo)

        win_layout.addWidget(QLabel("Кастомный звук (WAV/MP3):"))
        snd_row = QHBoxLayout()
        self.snd_edit = QLineEdit()
        self.snd_edit.textChanged.connect(self._on_win_changed)
        snd_row.addWidget(self.snd_edit)

        browse_btn = QPushButton("Обзор...")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_sound)
        snd_row.addWidget(browse_btn)
        win_layout.addLayout(snd_row)

        win_layout.addWidget(QLabel("Запуск звука с кадра №:"))
        self.snd_start_spin = QSpinBox()
        self.snd_start_spin.setRange(1, 100)
        self.snd_start_spin.valueChanged.connect(self._on_win_changed)
        win_layout.addWidget(self.snd_start_spin)

        win_layout.addStretch()

        self._win_scroll = QScrollArea()
        self._win_scroll.setWidgetResizable(True)
        self._win_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._win_scroll.setWidget(self._win_tab)
        self.tabs.addTab(self._win_scroll, "Окно")

        # --- Keyframe Tab ---
        self._kf_tab = QWidget()
        kf_layout = QVBoxLayout(self._kf_tab)
        kf_layout.setContentsMargins(12, 12, 12, 12)
        kf_layout.setSpacing(10)

        kf_layout.addWidget(self._create_section_lbl("НАСТРОЙКА ПЕРЕХОДА"))

        kf_layout.addWidget(QLabel("Длительность перехода (ms):"))
        self.dur_spin = QSpinBox()
        self.dur_spin.setRange(50, 10000)
        self.dur_spin.setSingleStep(50)
        self.dur_spin.valueChanged.connect(self._on_kf_changed)
        kf_layout.addWidget(self.dur_spin)

        kf_layout.addWidget(QLabel("Функция движения (easing):"))
        self.easing_combo = QComboBox()
        for label, val in EASINGS:
            self.easing_combo.addItem(label, val)
        self.easing_combo.currentIndexChanged.connect(self._on_kf_changed)
        kf_layout.addWidget(self.easing_combo)

        kf_layout.addWidget(QLabel("Пауза после перехода (ms):"))
        self.hold_spin = QSpinBox()
        self.hold_spin.setRange(0, 10000)
        self.hold_spin.setSingleStep(100)
        self.hold_spin.valueChanged.connect(self._on_kf_changed)
        kf_layout.addWidget(self.hold_spin)

        kf_layout.addWidget(QLabel("Метка кадра:"))
        self.label_edit = QLineEdit()
        self.label_edit.textChanged.connect(self._on_kf_changed)
        kf_layout.addWidget(self.label_edit)

        kf_layout.addWidget(self._create_section_lbl("КРИВАЯ ДВИЖЕНИЯ"))
        self.preview_widget = EasingPreviewWidget()
        kf_layout.addWidget(self.preview_widget)

        kf_layout.addStretch()

        self._kf_scroll = QScrollArea()
        self._kf_scroll.setWidgetResizable(True)
        self._kf_scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._kf_scroll.setWidget(self._kf_tab)
        self.tabs.addTab(self._kf_scroll, "Кадр")

        layout.addWidget(self.tabs)

        self.update_theme()

    def _create_section_lbl(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self._section_labels.append(lbl)
        return lbl

    def update_theme(self):
        t = get_current_theme()
        self.setStyleSheet(f"background-color: {t['bg_dark']};")
        self._hdr.setStyleSheet(f"background-color: {t['bg_dark']}; border-bottom: 1px solid {t['border']};")
        self._title_lbl.setStyleSheet(f"color: {t['text_muted']}; letter-spacing: 1px;")
        self.tabs.setStyleSheet(f"""
            QTabWidget {{ background-color: {t['bg_dark']}; background: {t['bg_dark']}; border: none; }}
            QTabWidget::pane {{ border: none; background-color: {t['bg_dark']}; background: {t['bg_dark']}; }}
            QTabWidget::tab-bar {{ left: 0px; background-color: {t['bg_dark']}; background: {t['bg_dark']}; }}
            QTabBar {{ background-color: {t['bg_dark']}; background: {t['bg_dark']}; }}
            QTabBar::tab {{ background-color: {t['bg_input']}; padding: 8px 16px; color: {t['text_muted']}; border: none; }}
            QTabBar::tab:selected {{ background-color: {t['bg_dark']}; color: {t['accent']}; font-weight: bold; }}
        """)
        scroll_qss = f"QScrollArea {{ background: {t['bg_dark']}; background-color: {t['bg_dark']}; border: none; }}"
        self._win_scroll.setStyleSheet(scroll_qss)
        self._kf_scroll.setStyleSheet(scroll_qss)
        if hasattr(self, '_win_tab'):
            self._win_tab.setStyleSheet(f"background-color: {t['bg_dark']};")
        if hasattr(self, '_kf_tab'):
            self._kf_tab.setStyleSheet(f"background-color: {t['bg_dark']};")
        for lbl in self._section_labels:
            lbl.setStyleSheet(f"color: {t['accent']}; background: transparent; border: none; padding: 2px 0px; margin: 0px; letter-spacing: 1px;")
        self.preview_widget.setStyleSheet(f"background-color: {t['bg_input']}; border: 1px solid {t['border_input']}; border-radius: 6px;")
        self.preview_widget.update()

    def load_window(self, win: Optional["WindowObject"]):
        self._win = win
        if not win:
            return

        self._updating = True
        try:
            self.name_edit.setText(win.name)
            self.title_edit.setText(win.title)
            self.msg_edit.setPlainText(win.message)

            # Combo Indexes
            for i in range(self.icon_combo.count()):
                if self.icon_combo.itemData(i) == win.icon:
                    self.icon_combo.setCurrentIndex(i)

            for i in range(self.btn_combo.count()):
                if self.btn_combo.itemData(i) == win.buttons:
                    self.btn_combo.setCurrentIndex(i)

            for i in range(self.sound_combo.count()):
                if self.sound_combo.itemData(i) == (win.system_sound or ""):
                    self.sound_combo.setCurrentIndex(i)

            self.snd_edit.setText(win.sound_path or "")
            self.snd_start_spin.setValue(win.sound_start_kf_index + 1)
        finally:
            self._updating = False

        self.tabs.setCurrentIndex(0)

    def load_keyframe(self, kf: Optional["Keyframe"]):
        self._kf = kf
        if not kf:
            return

        self._updating = True
        try:
            self.dur_spin.setValue(kf.duration_ms)
            self.hold_spin.setValue(kf.hold_ms)
            self.label_edit.setText(kf.label)

            for i in range(self.easing_combo.count()):
                if self.easing_combo.itemData(i) == kf.easing:
                    self.easing_combo.setCurrentIndex(i)

            self.preview_widget.set_easing(kf.easing)
        finally:
            self._updating = False

        self.tabs.setCurrentIndex(1)

    def _on_win_changed(self):
        if self._updating or not self._win:
            return
        self._win.name = self.name_edit.text()
        self._win.title = self.title_edit.text()
        self._win.message = self.msg_edit.toPlainText()
        self._win.icon = self.icon_combo.currentData()
        self._win.buttons = self.btn_combo.currentData()
        self._win.system_sound = self.sound_combo.currentData() or None
        self._win.sound_path = self.snd_edit.text().strip() or None
        self._win.sound_start_kf_index = max(0, self.snd_start_spin.value() - 1)
        self.window_changed.emit()

    def _on_kf_changed(self):
        if self._updating or not self._kf:
            return
        self._kf.duration_ms = self.dur_spin.value()
        self._kf.hold_ms = self.hold_spin.value()
        self._kf.label = self.label_edit.text()
        self._kf.easing = self.easing_combo.currentData()
        self.preview_widget.set_easing(self._kf.easing)
        self.keyframe_changed.emit()

    def _browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите аудиофайл", "", "Audio Files (*.wav *.mp3 *.ogg)"
        )
        if file_path:
            self.snd_edit.setText(file_path)
