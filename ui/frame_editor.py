"""
Windownimator — Frame Editor Panel
Right-side panel for editing properties of the selected animation frame.
"""

from __future__ import annotations
import os
import tkinter as tk
from tkinter import filedialog
from typing import Callable, Optional, TYPE_CHECKING
import customtkinter as ctk

if TYPE_CHECKING:
    from core.frame import Frame

# Colors
C_BG = "#12121f"
C_PANEL = "#16162a"
C_SECTION = "#1e1e38"
C_ACCENT = "#0078d4"
C_TEXT = "#e8e8ff"
C_TEXT_DIM = "#8888aa"
C_INPUT = "#1a1a30"
C_INPUT_BORDER = "#2a2a4a"

ICON_OPTIONS = ["info", "warning", "error", "question", "none"]
ICON_LABELS = {
    "info":     "ℹ️  Информация",
    "warning":  "⚠️  Предупреждение",
    "error":    "❌  Ошибка",
    "question": "❓  Вопрос",
    "none":     "🪟  Без иконки",
}

BUTTON_OPTIONS = ["ok", "okcancel", "yesno", "yesnocancel", "retrycancel", "abortretryignore"]
BUTTON_LABELS = {
    "ok":               "OK",
    "okcancel":         "OK / Отмена",
    "yesno":            "Да / Нет",
    "yesnocancel":      "Да / Нет / Отмена",
    "retrycancel":      "Повтор / Отмена",
    "abortretryignore": "Прервать / Повтор / Игнорировать",
}

ACTION_OPTIONS = ["next", "end", "repeat"]
ACTION_LABELS = {
    "next":   "→ Следующий кадр",
    "end":    "⏹ Завершить анимацию",
    "repeat": "🔁 Повторить кадр",
}

SYSTEM_SOUND_OPTIONS = ["", "info", "warning", "error", "question"]
SYSTEM_SOUND_LABELS = {
    "":         "— Нет системного звука",
    "info":     "🔔 Информация (Asterisk)",
    "warning":  "⚡ Предупреждение (Exclamation)",
    "error":    "🔴 Ошибка (Hand)",
    "question": "❓ Вопрос (Question)",
}

POSITION_OPTIONS = ["center", "random", "custom"]
POSITION_LABELS = {
    "center": "По центру",
    "random": "Случайно",
    "custom": "Свои координаты",
}


def _section_label(parent, text: str):
    f = ctk.CTkFrame(parent, fg_color=C_SECTION, corner_radius=6, height=28)
    f.pack(fill="x", pady=(10, 4))
    f.pack_propagate(False)
    ctk.CTkLabel(f, text=text, font=ctk.CTkFont(size=11, weight="bold"),
                 text_color=C_ACCENT).pack(side="left", padx=10)
    return f


def _row(parent, label: str, widget_factory):
    frame = ctk.CTkFrame(parent, fg_color="transparent")
    frame.pack(fill="x", pady=3)
    ctk.CTkLabel(frame, text=label, width=130, anchor="w",
                 font=ctk.CTkFont(size=11), text_color=C_TEXT_DIM).pack(side="left")
    w = widget_factory(frame)
    w.pack(side="left", fill="x", expand=True)
    return w


class FrameEditorPanel(ctk.CTkFrame):
    """
    Panel for editing all properties of a single animation frame.
    """

    def __init__(
        self,
        master,
        on_change: Callable[[], None],
        on_preview: Callable[[], None],
        **kwargs,
    ):
        super().__init__(master, fg_color=C_PANEL, corner_radius=0, **kwargs)
        self.on_change = on_change
        self.on_preview = on_preview
        self._frame: Optional["Frame"] = None
        self._updating = False

        self._build()

    def _build(self):
        # Title bar
        title_bar = ctk.CTkFrame(self, fg_color="#0d0d1a", corner_radius=0, height=36)
        title_bar.pack(fill="x")
        title_bar.pack_propagate(False)

        ctk.CTkLabel(
            title_bar, text="  ✏️  РЕДАКТОР КАДРА",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=C_TEXT_DIM,
        ).pack(side="left", padx=8, pady=8)

        # Preview button
        self._preview_btn = ctk.CTkButton(
            title_bar,
            text="👁 Показать",
            width=100,
            height=26,
            fg_color=C_ACCENT,
            hover_color="#1a8ee8",
            font=ctk.CTkFont(size=11),
            command=self.on_preview,
        )
        self._preview_btn.pack(side="right", padx=8, pady=5)

        # Scrollable content
        self._scroll = ctk.CTkScrollableFrame(
            self,
            fg_color=C_PANEL,
            corner_radius=0,
            scrollbar_button_color=C_ACCENT,
        )
        self._scroll.pack(fill="both", expand=True, padx=12, pady=8)

        self._build_content(self._scroll)

        # Placeholder when no frame selected
        self._placeholder = ctk.CTkFrame(self, fg_color=C_PANEL, corner_radius=0)
        ctk.CTkLabel(
            self._placeholder,
            text="← Выберите кадр\nна таймлайне",
            font=ctk.CTkFont(size=14),
            text_color=C_TEXT_DIM,
        ).pack(expand=True)

        self._show_placeholder()

    def _build_content(self, parent):
        """Build all editor fields."""
        # ── ОСНОВНОЕ ──────────────────────────────────────────────────────
        _section_label(parent, "📝  СОДЕРЖИМОЕ")

        # Title
        ctk.CTkLabel(parent, text="Заголовок окна", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._title_var = ctk.StringVar()
        self._title_entry = ctk.CTkEntry(
            parent, textvariable=self._title_var,
            fg_color=C_INPUT, border_color=C_INPUT_BORDER,
            text_color=C_TEXT, font=ctk.CTkFont(size=12),
        )
        self._title_entry.pack(fill="x", pady=(0, 4))
        self._title_var.trace_add("write", self._on_field_change)

        # Message
        ctk.CTkLabel(parent, text="Текст сообщения", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._message_text = ctk.CTkTextbox(
            parent, height=90,
            fg_color=C_INPUT, border_color=C_INPUT_BORDER, border_width=1,
            text_color=C_TEXT, font=ctk.CTkFont(size=12),
        )
        self._message_text.pack(fill="x", pady=(0, 4))
        self._message_text.bind("<KeyRelease>", self._on_text_change)

        # Label (timeline name)
        ctk.CTkLabel(parent, text="Метка (в таймлайне)", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._label_var = ctk.StringVar()
        self._label_entry = ctk.CTkEntry(
            parent, textvariable=self._label_var,
            fg_color=C_INPUT, border_color=C_INPUT_BORDER,
            text_color=C_TEXT, font=ctk.CTkFont(size=12),
        )
        self._label_entry.pack(fill="x", pady=(0, 4))
        self._label_var.trace_add("write", self._on_field_change)

        # ── ВИД ──────────────────────────────────────────────────────────
        _section_label(parent, "🎨  ВИД")

        # Icon type
        ctk.CTkLabel(parent, text="Иконка", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._icon_var = ctk.StringVar(value="info")
        self._icon_menu = ctk.CTkOptionMenu(
            parent,
            values=[ICON_LABELS[k] for k in ICON_OPTIONS],
            variable=None,
            fg_color=C_INPUT, button_color=C_ACCENT,
            button_hover_color="#1a8ee8",
            dropdown_fg_color="#1e1e35",
            text_color=C_TEXT,
            font=ctk.CTkFont(size=11),
            command=self._on_icon_change,
        )
        self._icon_menu.pack(fill="x", pady=(0, 4))

        # Buttons
        ctk.CTkLabel(parent, text="Кнопки", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._buttons_menu = ctk.CTkOptionMenu(
            parent,
            values=[BUTTON_LABELS[k] for k in BUTTON_OPTIONS],
            fg_color=C_INPUT, button_color=C_ACCENT,
            button_hover_color="#1a8ee8",
            dropdown_fg_color="#1e1e35",
            text_color=C_TEXT,
            font=ctk.CTkFont(size=11),
            command=self._on_buttons_change,
        )
        self._buttons_menu.pack(fill="x", pady=(0, 4))

        # ── ТАЙМИНГ ───────────────────────────────────────────────────────
        _section_label(parent, "⏱  ТАЙМИНГ")

        ctk.CTkLabel(parent, text="Задержка перед кадром (мс)", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._delay_var = ctk.StringVar(value="0")
        self._delay_entry = ctk.CTkEntry(
            parent, textvariable=self._delay_var,
            fg_color=C_INPUT, border_color=C_INPUT_BORDER,
            text_color=C_TEXT, font=ctk.CTkFont(size=12),
        )
        self._delay_entry.pack(fill="x", pady=(0, 4))
        self._delay_var.trace_add("write", self._on_field_change)

        # ── ЗВУК ──────────────────────────────────────────────────────────
        _section_label(parent, "🔊  ЗВУК")

        ctk.CTkLabel(parent, text="Системный звук", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))
        self._sys_sound_menu = ctk.CTkOptionMenu(
            parent,
            values=[SYSTEM_SOUND_LABELS[k] for k in SYSTEM_SOUND_OPTIONS],
            fg_color=C_INPUT, button_color=C_ACCENT,
            button_hover_color="#1a8ee8",
            dropdown_fg_color="#1e1e35",
            text_color=C_TEXT,
            font=ctk.CTkFont(size=11),
            command=self._on_sys_sound_change,
        )
        self._sys_sound_menu.pack(fill="x", pady=(0, 4))

        ctk.CTkLabel(parent, text="Свой звуковой файл", font=ctk.CTkFont(size=11),
                     text_color=C_TEXT_DIM, anchor="w").pack(fill="x", pady=(2, 0))

        sound_row = ctk.CTkFrame(parent, fg_color="transparent")
        sound_row.pack(fill="x", pady=(0, 4))

        self._sound_var = ctk.StringVar()
        self._sound_entry = ctk.CTkEntry(
            sound_row, textvariable=self._sound_var,
            fg_color=C_INPUT, border_color=C_INPUT_BORDER,
            text_color=C_TEXT, font=ctk.CTkFont(size=11),
            placeholder_text="путь к файлу...",
        )
        self._sound_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self._sound_var.trace_add("write", self._on_field_change)

        ctk.CTkButton(
            sound_row, text="📂", width=36,
            fg_color=C_ACCENT, hover_color="#1a8ee8",
            command=self._browse_sound,
        ).pack(side="right")

        ctk.CTkButton(
            sound_row, text="✕", width=28,
            fg_color="#3a1a1a", hover_color="#5a2a2a",
            text_color="#ef5350",
            command=self._clear_sound,
        ).pack(side="right", padx=(0, 4))

        # ── ПОЛОЖЕНИЕ ─────────────────────────────────────────────────────
        _section_label(parent, "📐  ПОЛОЖЕНИЕ НА ЭКРАНЕ")

        self._pos_menu = ctk.CTkOptionMenu(
            parent,
            values=[POSITION_LABELS[k] for k in POSITION_OPTIONS],
            fg_color=C_INPUT, button_color=C_ACCENT,
            button_hover_color="#1a8ee8",
            dropdown_fg_color="#1e1e35",
            text_color=C_TEXT,
            font=ctk.CTkFont(size=11),
            command=self._on_pos_change,
        )
        self._pos_menu.pack(fill="x", pady=(0, 4))

        # ── ДЕЙСТВИЯ ──────────────────────────────────────────────────────
        _section_label(parent, "🎮  ДЕЙСТВИЯ ПО КНОПКАМ")

        self._action_widgets = {}
        self._build_action_row(parent, "OK", "on_ok")
        self._build_action_row(parent, "Да", "on_yes")
        self._build_action_row(parent, "Нет", "on_no")
        self._build_action_row(parent, "Отмена", "on_cancel")

    def _build_action_row(self, parent, label: str, attr: str):
        frame = ctk.CTkFrame(parent, fg_color="transparent")
        frame.pack(fill="x", pady=2)

        ctk.CTkLabel(frame, text=label, width=70, anchor="w",
                     font=ctk.CTkFont(size=11), text_color=C_TEXT_DIM).pack(side="left")

        menu = ctk.CTkOptionMenu(
            frame,
            values=[ACTION_LABELS[k] for k in ACTION_OPTIONS],
            fg_color=C_INPUT, button_color=C_ACCENT,
            button_hover_color="#1a8ee8",
            dropdown_fg_color="#1e1e35",
            text_color=C_TEXT,
            font=ctk.CTkFont(size=11),
            command=lambda v, a=attr: self._on_action_change(a, v),
        )
        menu.pack(side="left", fill="x", expand=True)
        self._action_widgets[attr] = menu

    # ── Load / Save ───────────────────────────────────────────────────────

    def load_frame(self, frame: Optional["Frame"]):
        """Populate editor fields from a frame object."""
        self._frame = frame
        if frame is None:
            self._show_placeholder()
            return
        self._show_editor()
        self._updating = True
        try:
            self._title_var.set(frame.title)
            self._message_text.delete("1.0", "end")
            self._message_text.insert("1.0", frame.message)
            self._label_var.set(frame.label)
            self._delay_var.set(str(frame.delay_ms))
            self._sound_var.set(frame.sound_path or "")

            # Icon menu
            label = ICON_LABELS.get(frame.icon, ICON_LABELS["info"])
            self._icon_menu.set(label)

            # Buttons menu
            label = BUTTON_LABELS.get(frame.buttons, BUTTON_LABELS["ok"])
            self._buttons_menu.set(label)

            # System sound
            label = SYSTEM_SOUND_LABELS.get(frame.system_sound or "", SYSTEM_SOUND_LABELS[""])
            self._sys_sound_menu.set(label)

            # Position
            label = POSITION_LABELS.get(frame.position, POSITION_LABELS["center"])
            self._pos_menu.set(label)

            # Actions
            for attr, widget in self._action_widgets.items():
                val = getattr(frame, attr, "next")
                widget.set(ACTION_LABELS.get(val, ACTION_LABELS["next"]))

        finally:
            self._updating = False

    def _read_to_frame(self):
        """Write editor values back into the current frame."""
        if self._frame is None or self._updating:
            return
        self._frame.title = self._title_var.get()
        self._frame.message = self._message_text.get("1.0", "end-1c")
        self._frame.label = self._label_var.get()
        try:
            self._frame.delay_ms = max(0, int(self._delay_var.get()))
        except ValueError:
            pass
        sp = self._sound_var.get().strip()
        self._frame.sound_path = sp if sp else None

    # ── Event handlers ────────────────────────────────────────────────────

    def _on_field_change(self, *args):
        if not self._updating:
            self._read_to_frame()
            self.on_change()

    def _on_text_change(self, event=None):
        if not self._updating and self._frame:
            self._frame.message = self._message_text.get("1.0", "end-1c")
            self.on_change()

    def _on_icon_change(self, label: str):
        if self._frame:
            for k, v in ICON_LABELS.items():
                if v == label:
                    self._frame.icon = k
                    break
            self.on_change()

    def _on_buttons_change(self, label: str):
        if self._frame:
            for k, v in BUTTON_LABELS.items():
                if v == label:
                    self._frame.buttons = k
                    break
            self.on_change()

    def _on_sys_sound_change(self, label: str):
        if self._frame:
            for k, v in SYSTEM_SOUND_LABELS.items():
                if v == label:
                    self._frame.system_sound = k if k else None
                    break
            self.on_change()

    def _on_pos_change(self, label: str):
        if self._frame:
            for k, v in POSITION_LABELS.items():
                if v == label:
                    self._frame.position = k
                    break
            self.on_change()

    def _on_action_change(self, attr: str, label: str):
        if self._frame:
            for k, v in ACTION_LABELS.items():
                if v == label:
                    setattr(self._frame, attr, k)
                    break
            self.on_change()

    def _browse_sound(self):
        path = filedialog.askopenfilename(
            title="Выберите звуковой файл",
            filetypes=[
                ("Звуковые файлы", "*.wav *.mp3 *.ogg *.flac"),
                ("WAV", "*.wav"),
                ("MP3", "*.mp3"),
                ("Все файлы", "*.*"),
            ],
        )
        if path and self._frame:
            self._sound_var.set(path)
            self._frame.sound_path = path
            self.on_change()

    def _clear_sound(self):
        self._sound_var.set("")
        if self._frame:
            self._frame.sound_path = None
            self.on_change()

    # ── Visibility ────────────────────────────────────────────────────────

    def _show_placeholder(self):
        self._scroll.pack_forget()
        self._preview_btn.configure(state="disabled")
        self._placeholder.pack(fill="both", expand=True)

    def _show_editor(self):
        self._placeholder.pack_forget()
        self._scroll.pack(fill="both", expand=True, padx=12, pady=8)
        self._preview_btn.configure(state="normal")
