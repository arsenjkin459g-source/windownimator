"""
Windownimator 2.0 — Animation Project Model
The top-level container: list of WindowObjects + list of Keyframes.
Saved/loaded as .wa (JSON).
"""

from __future__ import annotations
import json
import uuid
from dataclasses import dataclass, field
from typing import List, Optional

from core.window_object import WindowObject
from core.keyframe import Keyframe, WindowState

WA_VERSION = "2.0"

# Default screen size for stage coordinates
DEFAULT_SCREEN_W = 1920
DEFAULT_SCREEN_H = 1080


@dataclass
class Animation:
    """Complete Windownimator 2.0 project."""

    name:      str = "Без названия"
    file_path: Optional[str] = None
    modified:  bool = False

    windows:   List[WindowObject] = field(default_factory=list)
    keyframes: List[Keyframe]     = field(default_factory=list)

    loop: bool = False

    # ── Window management ──────────────────────────────────────────────────

    def add_window(self, win: Optional[WindowObject] = None) -> WindowObject:
        if win is None:
            win = WindowObject(name=f"Окно {len(self.windows) + 1}")
        self.windows.append(win)
        # Add default state in every existing keyframe
        for kf in self.keyframes:
            if win.id not in kf.states:
                # Spread them out a bit
                idx = len(self.windows) - 1
                kf.states[win.id] = WindowState(
                    x=200 + (idx % 5) * 180,
                    y=200 + (idx // 5) * 140,
                )
        self.modified = True
        return win

    def remove_window(self, win_id: str) -> bool:
        before = len(self.windows)
        self.windows = [w for w in self.windows if w.id != win_id]
        for kf in self.keyframes:
            kf.states.pop(win_id, None)
        self.modified = True
        return len(self.windows) < before

    def get_window(self, win_id: str) -> Optional[WindowObject]:
        for w in self.windows:
            if w.id == win_id:
                return w
        return None

    # ── Keyframe management ────────────────────────────────────────────────

    def add_keyframe(self, after_index: Optional[int] = None) -> Keyframe:
        kf = Keyframe()
        # Copy positions from the last keyframe (or default)
        if self.keyframes:
            src = self.keyframes[-1] if after_index is None else self.keyframes[after_index]
            for wid, state in src.states.items():
                kf.states[wid] = WindowState(x=state.x, y=state.y, visible=state.visible)
        else:
            # First keyframe — spread windows
            for i, win in enumerate(self.windows):
                kf.states[win.id] = WindowState(
                    x=200 + (i % 5) * 200,
                    y=200 + (i // 5) * 160,
                )

        # Ensure every window has a state
        for win in self.windows:
            if win.id not in kf.states:
                kf.states[win.id] = WindowState()

        if after_index is None:
            self.keyframes.append(kf)
        else:
            self.keyframes.insert(after_index + 1, kf)

        self.modified = True
        return kf

    def remove_keyframe(self, kf_id: str) -> bool:
        before = len(self.keyframes)
        self.keyframes = [k for k in self.keyframes if k.id != kf_id]
        self.modified = True
        return len(self.keyframes) < before

    def get_keyframe(self, kf_id: str) -> Optional[Keyframe]:
        for kf in self.keyframes:
            if kf.id == kf_id:
                return kf
        return None

    def get_keyframe_index(self, kf_id: str) -> int:
        for i, kf in enumerate(self.keyframes):
            if kf.id == kf_id:
                return i
        return -1

    def duplicate_keyframe(self, kf_id: str) -> Optional[Keyframe]:
        idx = self.get_keyframe_index(kf_id)
        if idx < 0:
            return None
        new_kf = self.keyframes[idx].copy()
        self.keyframes.insert(idx + 1, new_kf)
        self.modified = True
        return new_kf

    def move_keyframe(self, from_idx: int, to_idx: int):
        if 0 <= from_idx < len(self.keyframes) and 0 <= to_idx < len(self.keyframes):
            kf = self.keyframes.pop(from_idx)
            self.keyframes.insert(to_idx, kf)
            self.modified = True

    # ── Serialisation ──────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "version":   WA_VERSION,
            "name":      self.name,
            "loop":      self.loop,
            "windows":   [w.to_dict() for w in self.windows],
            "keyframes": [kf.to_dict() for kf in self.keyframes],
        }

    @classmethod
    def from_dict(cls, data: dict, file_path: Optional[str] = None) -> "Animation":
        windows   = [WindowObject.from_dict(d) for d in data.get("windows", [])]
        keyframes = [Keyframe.from_dict(d)     for d in data.get("keyframes", [])]
        return cls(
            name=data.get("name", "Без названия"),
            file_path=file_path,
            windows=windows,
            keyframes=keyframes,
            loop=data.get("loop", False),
        )

    def save(self, path: Optional[str] = None) -> str:
        save_path = path or self.file_path
        if not save_path:
            raise ValueError("No file path specified")
        if not save_path.endswith(".wa"):
            save_path += ".wa"
        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, ensure_ascii=False, indent=2)
        self.file_path = save_path
        self.modified  = False
        return save_path

    @classmethod
    def load(cls, path: str) -> "Animation":
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return cls.from_dict(data, file_path=path)

    @classmethod
    def new(cls) -> "Animation":
        anim = cls(name="Новая анимация")

        # Create 3 default windows
        w1 = WindowObject(name="Ошибка 1",          title="Критическая ошибка",   message="Система не отвечает!\nОбратитесь к администратору.", icon="error",   buttons="ok")
        w2 = WindowObject(name="Предупреждение",    title="Предупреждение",        message="Обнаружена нестабильность.\nПродолжить?",              icon="warning", buttons="yesno")
        w3 = WindowObject(name="Информация",        title="Информация",             message="Операция выполнена успешно.",                          icon="info",    buttons="ok")
        anim.windows = [w1, w2, w3]

        # Keyframe 1 — starting positions
        kf1 = Keyframe(label="Старт")
        kf1.states = {
            w1.id: WindowState(x=150,  y=150),
            w2.id: WindowState(x=600,  y=150),
            w3.id: WindowState(x=1050, y=150),
        }
        kf1.duration_ms = 1000
        kf1.easing = "ease_in_out"

        # Keyframe 2 — windows move to center cluster
        kf2 = Keyframe(label="Сближение")
        kf2.states = {
            w1.id: WindowState(x=350,  y=400),
            w2.id: WindowState(x=620,  y=350),
            w3.id: WindowState(x=850,  y=400),
        }
        kf2.duration_ms = 1200
        kf2.easing = "bounce"

        # Keyframe 3 — scatter
        kf3 = Keyframe(label="Разлёт")
        kf3.states = {
            w1.id: WindowState(x=100,  y=600),
            w2.id: WindowState(x=620,  y=700),
            w3.id: WindowState(x=1150, y=600),
        }
        kf3.duration_ms = 800
        kf3.easing = "ease_out"

        anim.keyframes = [kf1, kf2, kf3]
        anim.modified = False
        return anim

    def get_sounds(self) -> list:
        sounds = []
        for w in self.windows:
            if w.sound_path and w.sound_path not in sounds:
                sounds.append(w.sound_path)
        return sounds
