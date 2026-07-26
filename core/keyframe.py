"""
Windownimator 2.0 — Keyframe Model
A snapshot of all window positions/visibility at a point in time.
"""

from __future__ import annotations
import uuid
from dataclasses import dataclass, field
from typing import Dict, List, Literal, Optional

EasingType = Literal["linear", "ease_in", "ease_out", "ease_in_out", "bounce", "elastic"]

EASING_LABELS = {
    "linear":      "Линейное",
    "ease_in":     "Ease In (разгон)",
    "ease_out":    "Ease Out (торможение)",
    "ease_in_out": "Ease In-Out (плавное)",
    "bounce":      "Пружина (отскок)",
    "elastic":     "Упругое",
}


@dataclass
class WindowState:
    """Position, visibility, and optional custom easing of one window in a specific keyframe."""
    x:       int  = 400
    y:       int  = 300
    visible: bool = True
    easing:  Optional[EasingType] = None

    def to_dict(self) -> dict:
        d = {"x": self.x, "y": self.y, "visible": self.visible}
        if self.easing:
            d["easing"] = self.easing
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "WindowState":
        return cls(
            x=d.get("x", 400),
            y=d.get("y", 300),
            visible=d.get("visible", True),
            easing=d.get("easing", None),
        )


@dataclass
class Keyframe:
    """
    One keyframe: states of all windows + transition settings to NEXT keyframe.
    """
    id:       str = field(default_factory=lambda: str(uuid.uuid4()))
    label:    str = ""

    # States keyed by WindowObject.id
    states:   Dict[str, WindowState] = field(default_factory=dict)

    # Transition to the NEXT keyframe
    duration_ms: int        = 800          # duration of tween animation
    easing:      EasingType = "ease_in_out"
    hold_ms:     int        = 0            # pause AFTER tween completes

    def get_state(self, window_id: str) -> WindowState:
        return self.states.get(window_id, WindowState())

    def get_window_easing(self, window_id: str) -> EasingType:
        st = self.states.get(window_id)
        if st and st.easing:
            return st.easing
        return self.easing

    def set_state(self, window_id: str, state: WindowState):
        self.states[window_id] = state

    def set_pos(self, window_id: str, x: int, y: int):
        if window_id in self.states:
            self.states[window_id].x = x
            self.states[window_id].y = y
        else:
            self.states[window_id] = WindowState(x=x, y=y)

    def set_visible(self, window_id: str, visible: bool):
        if window_id in self.states:
            self.states[window_id].visible = visible
        else:
            self.states[window_id] = WindowState(visible=visible)

    def get_display_label(self) -> str:
        return self.label if self.label else "Кадр"

    def to_dict(self) -> dict:
        return {
            "id":          self.id,
            "label":       self.label,
            "states":      {wid: s.to_dict() for wid, s in self.states.items()},
            "duration_ms": self.duration_ms,
            "easing":      self.easing,
            "hold_ms":     self.hold_ms,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "Keyframe":
        states = {
            wid: WindowState.from_dict(sd)
            for wid, sd in d.get("states", {}).items()
        }
        return cls(
            id=d.get("id", str(uuid.uuid4())),
            label=d.get("label", ""),
            states=states,
            duration_ms=d.get("duration_ms", 800),
            easing=d.get("easing", "ease_in_out"),
            hold_ms=d.get("hold_ms", 0),
        )

    def copy(self) -> "Keyframe":
        d = self.to_dict()
        d["id"] = str(uuid.uuid4())
        return Keyframe.from_dict(d)
