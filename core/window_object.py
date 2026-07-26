"""
Windownimator 2.0 — Window Object Model
A persistent animated entity that exists across all keyframes.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Literal, Optional

IconType    = Literal["info", "warning", "error", "question", "none"]
ButtonType  = Literal["ok", "okcancel", "yesno", "yesnocancel", "retrycancel", "abortretryignore"]

ICON_EMOJI = {
    "info":     "ℹ️",
    "warning":  "⚠️",
    "error":    "❌",
    "question": "❓",
    "none":     "🪟",
}

ICON_COLORS = {
    "info":     "#4fc3f7",
    "warning":  "#ffb74d",
    "error":    "#ef5350",
    "question": "#ab47bc",
    "none":     "#78909c",
}

BUTTON_LABELS = {
    "ok":               "OK",
    "okcancel":         "OK / Отмена",
    "yesno":            "Да / Нет",
    "yesnocancel":      "Да / Нет / Отмена",
    "retrycancel":      "Повтор / Отмена",
    "abortretryignore": "Прервать / Повтор / Игнорировать",
}


@dataclass
class WindowObject:
    """
    A dialog window entity that persists throughout the animation.
    Its position/visibility are defined per-keyframe in WindowState.
    """
    id:       str       = field(default_factory=lambda: str(uuid.uuid4()))
    name:     str       = "Окно"           # display name in window list
    title:    str       = "Windownimator"
    message:  str       = "Сообщение"
    icon:     IconType  = "info"
    buttons:  ButtonType = "ok"

    # Sound played when this window becomes visible/triggered
    sound_path:   Optional[str] = None
    system_sound: Optional[str] = None   # "info" | "warning" | "error" | "question"
    sound_start_kf_index: int = 0         # Keyframe index when sound starts playing (0-based)

    # Display color accent (used in editor only)
    color: str = "#0078d4"

    def get_emoji(self) -> str:
        return ICON_EMOJI.get(self.icon, "🪟")

    def get_color(self) -> str:
        return ICON_COLORS.get(self.icon, "#78909c")

    def to_dict(self) -> dict:
        return {
            "id":                   self.id,
            "name":                 self.name,
            "title":                self.title,
            "message":              self.message,
            "icon":                 self.icon,
            "buttons":              self.buttons,
            "sound_path":           self.sound_path,
            "system_sound":         self.system_sound,
            "sound_start_kf_index": self.sound_start_kf_index,
            "color":                self.color,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "WindowObject":
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            name=d.get("name", "Окно"),
            title=d.get("title", "Windownimator"),
            message=d.get("message", "Сообщение"),
            icon=d.get("icon", "info"),
            buttons=d.get("buttons", "ok"),
            sound_path=d.get("sound_path"),
            system_sound=d.get("system_sound"),
            sound_start_kf_index=d.get("sound_start_kf_index", 0),
            color=d.get("color", "#0078d4"),
        )

    def copy(self) -> "WindowObject":
        d = self.to_dict()
        d["id"] = str(uuid.uuid4())
        d["name"] = self.name + " (копия)"
        return WindowObject.from_dict(d)
