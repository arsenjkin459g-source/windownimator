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
WIN_EASINGS  = [("— По умолчанию для кадра", "")] + EASINGS


class EasingPreviewWidget(QWidget):
    """Custom paint widget rendering animated easing curve and dot preview."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedHeight(80)
        self.current_easing = "ease_in_out"
        self.dot_progress = 0.0    # 0.0 to 1.0 (moving dot)

        _t = get_current_theme()
        self.setStyleSheet(f"background-color: {_t['bg_input']}; border: 1px solid {_t['border_input']}; border-radius: 6px;")

        # Ball/Dot Loop Animation (moves along the curve continuously)
        self.dot_anim = QVariantAnimation(self)
        self.dot_anim.setDuration(1200)
        self.dot_anim.setStartValue(0.0)
        self.dot_anim.setEndValue(1.0)
        self.dot_anim.setLoopCount(-1)
        self.dot_anim.valueChanged.connect(self._on_dot_step)
        self.dot_anim.start()

    def set_easing(self, easing: str):
        target = easing if easing else "ease_in_out"
        if target != self.current_easing:
            self.current_easing = target
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
            fn = EASING_FUNCS.get(self.current_easing, EASING_FUNCS["ease_in_out"])

            steps = 80
            prev_point = None

            # Draw Curve
            painter.setPen(QPen(QColor(_t["accent"]), 2.5))
            for i in range(steps + 1):
                t = i / steps
                v = fn(t)
                x = pad + t * (w - 2 * pad)
                y = (h - pad) - v * (h - 2 * pad)

                curr_point = (x, y)
                if prev_point:
                    painter.drawLine(prev_point[0], prev_point[1], curr_point[0], curr_point[1])
                prev_point = curr_point

            # Draw Animated Ball along current curve
            t_ball = self.dot_progress
            v_ball = fn(t_ball)
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
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
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

        # No window notice label
        self.no_win_lbl = QLabel("Окно не выбрано для настройки\n\nВыберите окно на холсте или в списке слева.")
        self.no_win_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_win_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.no_win_lbl.setWordWrap(True)
        self.no_win_lbl.setStyleSheet("color: #94a3b8; padding: 50px 12px;")
        win_layout.addWidget(self.no_win_lbl)

        # Window Controls Container
        self.win_controls_widget = QWidget()
        win_ctrl_layout = QVBoxLayout(self.win_controls_widget)
        win_ctrl_layout.setContentsMargins(0, 0, 0, 0)
        win_ctrl_layout.setSpacing(10)

        win_ctrl_layout.addWidget(self._create_section_lbl("ДВИЖЕНИЕ В ТЕКУЩЕМ КАДРЕ"))
        win_ctrl_layout.addWidget(QLabel("Кривая движения окна (easing):"))
        self.win_easing_combo = QComboBox()
        for label, val in WIN_EASINGS:
            self.win_easing_combo.addItem(label, val)
        self.win_easing_combo.currentIndexChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.win_easing_combo)

        self.win_preview_widget = EasingPreviewWidget()
        win_ctrl_layout.addWidget(self.win_preview_widget)

        win_ctrl_layout.addSpacing(14)
        win_ctrl_layout.addWidget(self._create_section_lbl("СОДЕРЖИМОЕ"))

        win_ctrl_layout.addWidget(QLabel("Имя окна:"))
        self.name_edit = QLineEdit()
        self.name_edit.textChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.name_edit)

        win_ctrl_layout.addWidget(QLabel("Заголовок окна:"))
        self.title_edit = QLineEdit()
        self.title_edit.textChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.title_edit)

        win_ctrl_layout.addWidget(QLabel("Текст сообщения:"))
        self.msg_edit = QPlainTextEdit()
        self.msg_edit.setFixedHeight(55)
        self.msg_edit.textChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.msg_edit)

        win_ctrl_layout.addSpacing(14)
        win_ctrl_layout.addWidget(self._create_section_lbl("ВИД И ИКОНКА"))

        win_ctrl_layout.addWidget(QLabel("Иконка:"))
        self.icon_combo = QComboBox()
        for label, val in ICON_OPTIONS:
            self.icon_combo.addItem(label, val)
        self.icon_combo.currentIndexChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.icon_combo)

        win_ctrl_layout.addWidget(QLabel("Кнопки:"))
        self.btn_combo = QComboBox()
        for label, val in BTN_OPTIONS:
            self.btn_combo.addItem(label, val)
        self.btn_combo.currentIndexChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.btn_combo)

        win_ctrl_layout.addSpacing(14)
        win_ctrl_layout.addWidget(self._create_section_lbl("ЗВУКИ"))

        win_ctrl_layout.addWidget(QLabel("Системный звук:"))
        self.sound_combo = QComboBox()
        for label, val in SYS_SOUNDS:
            self.sound_combo.addItem(label, val)
        self.sound_combo.currentIndexChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.sound_combo)

        win_ctrl_layout.addWidget(QLabel("Кастомный звук (WAV/MP3):"))
        snd_row = QHBoxLayout()
        self.snd_edit = QLineEdit()
        self.snd_edit.textChanged.connect(self._on_win_changed)
        snd_row.addWidget(self.snd_edit)

        browse_btn = QPushButton("Обзор...")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse_sound)
        snd_row.addWidget(browse_btn)
        win_ctrl_layout.addLayout(snd_row)

        win_ctrl_layout.addWidget(QLabel("Запуск звука с кадра №:"))
        self.snd_start_spin = QSpinBox()
        self.snd_start_spin.setRange(1, 100)
        self.snd_start_spin.valueChanged.connect(self._on_win_changed)
        win_ctrl_layout.addWidget(self.snd_start_spin)

        win_ctrl_layout.addStretch()

        win_layout.addWidget(self.win_controls_widget)

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

        self.no_win_lbl.show()
        self.win_controls_widget.hide()

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
        if hasattr(self, 'win_preview_widget'):
            self.win_preview_widget.setStyleSheet(f"background-color: {t['bg_input']}; border: 1px solid {t['border_input']}; border-radius: 6px;")
            self.win_preview_widget.update()

    def load_window(self, win: Optional["WindowObject"], kf: Optional["Keyframe"] = None):
        self.load_windows([win] if win else [], kf)

    def load_windows(self, wins: List["WindowObject"], kf: Optional["Keyframe"] = None):
        self._wins = [w for w in wins if w is not None]
        self._win = self._wins[0] if self._wins else None
        if kf is not None:
            self._kf = kf

        if not self._wins:
            self._title_lbl.setText("СВОЙСТВА")
            self.no_win_lbl.show()
            self.win_controls_widget.hide()
            return

        self.no_win_lbl.hide()
        self.win_controls_widget.show()

        if len(self._wins) > 1:
            self._title_lbl.setText(f"СВОЙСТВА ({len(self._wins)} ОКОН)")
        else:
            self._title_lbl.setText("СВОЙСТВА")

        self._updating = True
        try:
            w0 = self._wins[0]

            if len(self._wins) == 1:
                self.name_edit.setText(w0.name)
                self.name_edit.setEnabled(True)
            else:
                self.name_edit.setText(f"Выбрано окон: {len(self._wins)}")
                self.name_edit.setEnabled(False)

            if all(w.title == w0.title for w in self._wins):
                self.title_edit.setText(w0.title)
            else:
                self.title_edit.setText("")
                self.title_edit.setPlaceholderText("(Разные заголовки)")

            if all(w.message == w0.message for w in self._wins):
                self.msg_edit.setPlainText(w0.message)
            else:
                self.msg_edit.setPlainText("")
                self.msg_edit.setPlaceholderText("(Разный текст сообщений)")

            if all(w.icon == w0.icon for w in self._wins):
                for i in range(self.icon_combo.count()):
                    if self.icon_combo.itemData(i) == w0.icon:
                        self.icon_combo.setCurrentIndex(i)
            else:
                self.icon_combo.setCurrentIndex(0)

            if all(w.buttons == w0.buttons for w in self._wins):
                for i in range(self.btn_combo.count()):
                    if self.btn_combo.itemData(i) == w0.buttons:
                        self.btn_combo.setCurrentIndex(i)
            else:
                self.btn_combo.setCurrentIndex(0)

            if all(w.system_sound == w0.system_sound for w in self._wins):
                for i in range(self.sound_combo.count()):
                    if self.sound_combo.itemData(i) == (w0.system_sound or ""):
                        self.sound_combo.setCurrentIndex(i)
            else:
                self.sound_combo.setCurrentIndex(0)

            if all(w.sound_path == w0.sound_path for w in self._wins):
                self.snd_edit.setText(w0.sound_path or "")
            else:
                self.snd_edit.setText("")

            if all(w.sound_start_kf_index == w0.sound_start_kf_index for w in self._wins):
                self.snd_start_spin.setValue(w0.sound_start_kf_index + 1)
            else:
                self.snd_start_spin.setValue(1)

            win_eas = ""
            if self._kf and self._wins:
                first_eas = self._kf.get_state(w0.id).easing or ""
                if all((self._kf.get_state(w.id).easing or "") == first_eas for w in self._wins):
                    win_eas = first_eas

            for i in range(self.win_easing_combo.count()):
                if self.win_easing_combo.itemData(i) == win_eas:
                    self.win_easing_combo.setCurrentIndex(i)

            active_eas = win_eas if win_eas else (self._kf.easing if self._kf else "ease_in_out")
            self.win_preview_widget.set_easing(active_eas)
        finally:
            self._updating = False

        self.tabs.setCurrentIndex(0)

    def load_keyframe(self, kf: Optional["Keyframe"]):
        self._kf = kf
        if not getattr(self, '_wins', None):
            self.no_win_lbl.show()
            self.win_controls_widget.hide()
        else:
            self.no_win_lbl.hide()
            self.win_controls_widget.show()

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

            if getattr(self, '_win', None):
                st = kf.get_state(self._win.id)
                win_eas = st.easing or ""
                active_eas = win_eas if win_eas else kf.easing
                self.win_preview_widget.set_easing(active_eas)
        finally:
            self._updating = False

        self.tabs.setCurrentIndex(1)

    def _on_win_changed(self, *args):
        if self._updating or not getattr(self, '_wins', None):
            return

        for win in self._wins:
            if len(self._wins) == 1:
                win.name = self.name_edit.text()

            if self.title_edit.text():
                win.title = self.title_edit.text()
            if self.msg_edit.toPlainText():
                win.message = self.msg_edit.toPlainText()

            win.icon = self.icon_combo.currentData()
            win.buttons = self.btn_combo.currentData()
            win.system_sound = self.sound_combo.currentData() or None
            if self.snd_edit.text().strip():
                win.sound_path = self.snd_edit.text().strip()
            win.sound_start_kf_index = max(0, self.snd_start_spin.value() - 1)

            if self._kf:
                eas = self.win_easing_combo.currentData()
                self._kf.get_state(win.id).easing = eas if eas else None

        eas = self.win_easing_combo.currentData()
        active_eas = eas if eas else (self._kf.easing if self._kf else "ease_in_out")
        self.win_preview_widget.set_easing(active_eas)

        self.window_changed.emit()

    def _on_kf_changed(self, *args):
        if self._updating or not self._kf:
            return
        self._kf.duration_ms = self.dur_spin.value()
        self._kf.hold_ms = self.hold_spin.value()
        self._kf.label = self.label_edit.text()
        self._kf.easing = self.easing_combo.currentData()
        self.preview_widget.set_easing(self._kf.easing)

        if self._win:
            st = self._kf.get_state(self._win.id)
            win_eas = st.easing or ""
            active_eas = win_eas if win_eas else self._kf.easing
            self.win_preview_widget.set_easing(active_eas)

        self.keyframe_changed.emit()

    def _browse_sound(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Выберите аудиофайл", "", "Audio Files (*.wav *.mp3 *.ogg)"
        )
        if file_path:
            self.snd_edit.setText(file_path)
