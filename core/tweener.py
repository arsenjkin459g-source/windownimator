"""
Windownimator 2.0 — Tweening / Easing Functions
Interpolates window positions between keyframes.
"""

from __future__ import annotations
import math
from typing import Tuple


# ── Easing functions (t in [0, 1] → value in [0, 1]) ─────────────────────────

def linear(t: float) -> float:
    return t


def ease_in(t: float) -> float:
    return t * t * t


def ease_out(t: float) -> float:
    t = 1 - t
    return 1 - t * t * t


def ease_in_out(t: float) -> float:
    if t < 0.5:
        return 4 * t * t * t
    t = 2 * t - 2
    return 1 + t * t * t / 2


def bounce(t: float) -> float:
    """Bounce easing (ease-out bounce)."""
    if t < 1 / 2.75:
        return 7.5625 * t * t
    elif t < 2 / 2.75:
        t -= 1.5 / 2.75
        return 7.5625 * t * t + 0.75
    elif t < 2.5 / 2.75:
        t -= 2.25 / 2.75
        return 7.5625 * t * t + 0.9375
    else:
        t -= 2.625 / 2.75
        return 7.5625 * t * t + 0.984375


def elastic(t: float) -> float:
    """Elastic ease-out."""
    if t == 0 or t == 1:
        return t
    return math.pow(2, -10 * t) * math.sin((t - 0.075) * (2 * math.pi) / 0.3) + 1


EASING_FUNCS = {
    "linear":      linear,
    "ease_in":     ease_in,
    "ease_out":    ease_out,
    "ease_in_out": ease_in_out,
    "bounce":      bounce,
    "elastic":     elastic,
}


def apply_easing(t: float, easing: str = "ease_in_out") -> float:
    fn = EASING_FUNCS.get(easing, ease_in_out)
    return fn(max(0.0, min(1.0, t)))


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation."""
    return a + (b - a) * t


def interpolate_pos(
    x0: int, y0: int,
    x1: int, y1: int,
    t: float,
    easing: str = "ease_in_out",
) -> Tuple[int, int]:
    et = apply_easing(t, easing)
    return int(lerp(x0, x1, et)), int(lerp(y0, y1, et))


def interpolate_rect(
    x0: float, y0: float, w0: float, h0: float,
    x1: float, y1: float, w1: float, h1: float,
    t: float,
    easing: str = "ease_in_out",
) -> Tuple[int, int, int, int]:
    et = apply_easing(t, easing)
    return (
        int(lerp(x0, x1, et)),
        int(lerp(y0, y1, et)),
        int(lerp(w0, w1, et)),
        int(lerp(h0, h1, et)),
    )


def interpolate_alpha(
    a0: float, a1: float,
    t: float,
    easing: str = "ease_in_out",
) -> float:
    et = apply_easing(t, easing)
    return lerp(a0, a1, et)
