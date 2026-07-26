"""
Windownimator 2.0 — Real-time Playback Engine
Uses REAL Windows MessageBoxW dialogs animated with SetWindowPos at 60 FPS.
"""

from __future__ import annotations
import ctypes
import ctypes.wintypes as wt
import os
import threading
import time
from typing import Callable, Dict, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from core.animation import Animation
    from core.window_object import WindowObject
    from core.keyframe import Keyframe

from core.tweener import interpolate_pos, interpolate_rect, apply_easing

# ── WinAPI Setup ───────────────────────────────────────────────────────────────
user32   = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

# CRITICAL: set correct return types AND argtypes so 64-bit handle passing works
user32.GetWindowThreadProcessId.restype  = wt.DWORD
user32.GetWindowThreadProcessId.argtypes = [wt.HWND, ctypes.POINTER(wt.DWORD)]

user32.IsWindowVisible.restype           = wt.BOOL
user32.IsWindowVisible.argtypes          = [wt.HWND]

user32.IsWindow.restype                  = wt.BOOL
user32.IsWindow.argtypes                 = [wt.HWND]

user32.SetWindowPos.restype              = wt.BOOL
user32.SetWindowPos.argtypes             = [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.UINT]

user32.PostMessageW.restype              = wt.BOOL
user32.PostMessageW.argtypes             = [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM]

user32.MessageBoxW.restype               = ctypes.c_int
user32.MessageBoxW.argtypes              = [wt.HWND, wt.LPCWSTR, wt.LPCWSTR, wt.UINT]

user32.GetClassNameW.restype             = ctypes.c_int
user32.GetClassNameW.argtypes            = [wt.HWND, wt.LPWSTR, ctypes.c_int]

user32.EndDialog.restype                 = wt.BOOL
user32.EndDialog.argtypes                = [wt.HWND, ctypes.c_int]

kernel32.GetCurrentThreadId.restype      = wt.DWORD
kernel32.GetCurrentThreadId.argtypes     = []

EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wt.HWND, wt.LPARAM)

# MessageBox constants
MB_ICONS = {
    "info":     0x00000040,
    "warning":  0x00000030,
    "error":    0x00000010,
    "question": 0x00000020,
    "none":     0x00000000,
}
MB_BUTTONS = {
    "ok":               0x00000000,
    "okcancel":         0x00000001,
    "yesno":            0x00000004,
    "yesnocancel":      0x00000003,
    "retrycancel":      0x00000005,
    "abortretryignore": 0x00000002,
}

# SetWindowPos flags
SWP_NOSIZE     = 0x0001
SWP_NOACTIVATE = 0x0010
SWP_SHOWWINDOW = 0x0040
SWP_NOZORDER   = 0x0004
HWND_TOPMOST   = -1
HWND_TOP       = 0

WM_CLOSE = 0x0010

# Dialog box class name used by MessageBoxW
DIALOG_CLASS = "#32770"

FPS      = 60
FRAME_DT = 1.0 / FPS

SYS_SOUNDS = {
    "info":     "SystemAsterisk",
    "warning":  "SystemExclamation",
    "error":    "SystemHand",
    "question": "SystemQuestion",
}


# ── Sound ──────────────────────────────────────────────────────────────────────

def _play_sound(win_obj: "WindowObject"):
    sp = (win_obj.sound_path or "").strip()
    if sp and os.path.isfile(sp):
        # 1. Try winsound for .wav files
        if sp.lower().endswith(".wav"):
            try:
                import winsound
                winsound.PlaySound(sp, winsound.SND_FILENAME | winsound.SND_ASYNC)
                return
            except Exception as e:
                print(f"[Sound Error winsound]: {e}")

        # 2. Try pygame.mixer for mp3 / ogg / wav
        try:
            import pygame.mixer as mx
            if not mx.get_init():
                mx.init()
            mx.Sound(sp).play()
            return
        except Exception as e:
            print(f"[Sound Error pygame]: {e}")

    # System sound fallback
    snd = win_obj.system_sound or win_obj.icon
    name = SYS_SOUNDS.get(snd)
    if name:
        try:
            import winsound
            winsound.PlaySound(name, winsound.SND_ALIAS | winsound.SND_ASYNC)
        except Exception as e:
            print(f"[Sound Error sys_sound]: {e}")


def stop_all_sounds():
    """Immediately stop any playing audio from winsound or pygame.mixer."""
    try:
        import winsound
        winsound.PlaySound(None, winsound.SND_PURGE)
    except Exception:
        pass

    try:
        import pygame.mixer as mx
        if mx.get_init():
            mx.stop()
    except Exception:
        pass


# ── HWND search ────────────────────────────────────────────────────────────────

def _find_dialog_hwnd(thread_id: int, timeout: float = 3.0) -> Optional[int]:
    """
    Poll EnumWindows until we find a #32770 dialog belonging to thread_id.
    Uses class-name matching (#32770 = dialog box class used by MessageBoxW).
    """
    deadline = time.time() + timeout
    cls_buf  = ctypes.create_unicode_buffer(64)

    while time.time() < deadline:
        found = [None]

        def _cb(hwnd, _):
            # Check thread ownership
            owner_tid = user32.GetWindowThreadProcessId(hwnd, None)
            if owner_tid != thread_id:
                return True  # continue

            # Check window class: MessageBoxW uses #32770
            user32.GetClassNameW(hwnd, cls_buf, 64)
            if cls_buf.value == DIALOG_CLASS:
                found[0] = hwnd
                return False  # stop enum
            return True

        user32.EnumWindows(EnumWindowsProc(_cb), 0)

        if found[0]:
            return found[0]

        time.sleep(0.03)

    return None


# ── Native Dialog ──────────────────────────────────────────────────────────────

class NativeDialog:
    """
    A real Windows MessageBox running in its own thread.
    We locate its HWND by thread ID + class name, then move it with SetWindowPos.
    """

    def __init__(self, win_obj: "WindowObject"):
        self.win_obj = win_obj
        self.hwnd:   Optional[int]            = None
        self._tid:   Optional[int]            = None
        self._tid_ready = threading.Event()
        self._thread: Optional[threading.Thread] = None

    def open(self, x: int, y: int) -> bool:
        """
        Start the MessageBox thread, wait for its HWND, snap to (x, y).
        Returns True if HWND was found successfully.
        """
        self._thread = threading.Thread(target=self._run_msgbox, daemon=True)
        self._thread.start()

        # Wait for thread ID (set at the very start of _run_msgbox)
        self._tid_ready.wait(timeout=2.0)
        if not self._tid:
            return False

        # Search for the dialog's HWND
        hwnd = _find_dialog_hwnd(self._tid, timeout=3.0)
        if not hwnd:
            return False

        self.hwnd = hwnd

        # Position it
        user32.SetWindowPos(
            self.hwnd, HWND_TOPMOST, x, y, 0, 0,
            SWP_NOSIZE | SWP_SHOWWINDOW,
        )
        return True

    def _run_msgbox(self):
        # Set thread ID FIRST, before calling MessageBoxW
        self._tid = kernel32.GetCurrentThreadId()
        self._tid_ready.set()

        icon  = MB_ICONS.get(self.win_obj.icon, 0)
        btns  = MB_BUTTONS.get(self.win_obj.buttons, 0)
        # MB_TOPMOST = 0x00040000
        flags = icon | btns | 0x00040000

        user32.MessageBoxW(
            None,
            self.win_obj.message,
            self.win_obj.title,
            flags,
        )

    def move_to(self, x: int, y: int, w: int = 0, h: int = 0):
        if self.hwnd and user32.IsWindow(self.hwnd):
            if w > 0 and h > 0:
                user32.SetWindowPos(
                    self.hwnd, HWND_TOPMOST, int(x), int(y), int(w), int(h),
                    SWP_NOACTIVATE,
                )
            else:
                user32.SetWindowPos(
                    self.hwnd, HWND_TOPMOST, int(x), int(y), 0, 0,
                    SWP_NOSIZE | SWP_NOACTIVATE,
                )

    def close(self):
        if self.hwnd and user32.IsWindow(self.hwnd):
            user32.EndDialog(self.hwnd, 0)
            user32.PostMessageW(self.hwnd, 0x0111, 1, 0)  # WM_COMMAND IDOK=1
            user32.PostMessageW(self.hwnd, 0x0111, 2, 0)  # WM_COMMAND IDCANCEL=2
            user32.PostMessageW(self.hwnd, WM_CLOSE, 0, 0)
            self.hwnd = None

    def is_alive(self) -> bool:
        return bool(self.hwnd and user32.IsWindow(self.hwnd))


from PySide6.QtCore import QObject, Signal

class AnimationPlayer(QObject):
    """
    Plays the animation: opens real MessageBox dialogs and tweens their
    screen positions at 60 FPS using SetWindowPos.
    """
    sig_keyframe = Signal(int)
    sig_finish   = Signal()
    sig_stopped  = Signal()

    def __init__(
        self,
        root,
        animation: "Animation",
        on_keyframe: Optional[Callable[[int], None]] = None,
        on_finish:   Optional[Callable[[], None]]    = None,
        on_stopped:  Optional[Callable[[], None]]    = None,
    ):
        super().__init__()
        self.root        = root
        self.animation   = animation

        if on_keyframe:
            self.sig_keyframe.connect(on_keyframe)
        if on_finish:
            self.sig_finish.connect(on_finish)
        if on_stopped:
            self.sig_stopped.connect(on_stopped)

        self._stop_event = threading.Event()
        self._thread:    Optional[threading.Thread]  = None
        self._dialogs:   Dict[str, NativeDialog]     = {}
        self.is_playing  = False

    # ── Public ─────────────────────────────────────────────────────────────

    def play(self, start_kf_index: int = 0):
        if self.is_playing:
            self.stop()
        self._stop_event.clear()
        self.is_playing = True
        self._thread = threading.Thread(
            target=self._run, args=(start_kf_index,), daemon=True
        )
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        self.is_playing = False
        # Close all open dialogs
        for dlg in list(self._dialogs.values()):
            try:
                dlg.close()
            except Exception:
                pass
        self._dialogs.clear()

    # ── Internal ───────────────────────────────────────────────────────────

    def _open_dialogs_for_kf(self, kf: "Keyframe"):
        """Open all windows that are visible in this keyframe."""
        for win in self.animation.windows:
            state = kf.get_state(win.id)
            dlg   = NativeDialog(win)
            self._dialogs[win.id] = dlg

            if state.visible and not self._stop_event.is_set():
                # Stagger slightly so HWND enumeration doesn't race
                ok = dlg.open(state.x, state.y)
                if not ok:
                    # Fallback: keep dialog running but hwnd=None (silent fail)
                    pass
                time.sleep(0.08)

    def _notify(self, callback, *args):
        if not callback:
            return
        if hasattr(self.root, "after"):
            self.root.after(0, callback, *args)
        else:
            callback(*args)

    def _run(self, start_kf_index: int):
        anim = self.animation

        if not anim.keyframes or not anim.windows:
            self.is_playing = False
            self.sig_finish.emit()
            return

        keyframes = anim.keyframes

        # ── Open dialogs at first keyframe ──────────────────────────────
        kf0 = keyframes[start_kf_index]
        self.sig_keyframe.emit(start_kf_index)

        # Play sound for windows configured to start at start_kf_index
        for win in anim.windows:
            if win.sound_start_kf_index == start_kf_index and kf0.get_state(win.id).visible:
                threading.Thread(target=_play_sound, args=(win,), daemon=True).start()

        self._open_dialogs_for_kf(kf0)

        if self._stop_event.is_set():
            self._cleanup()
            return

        # ── Main tween loop ─────────────────────────────────────────────
        loop_count = 0
        while not self._stop_event.is_set():
            for kf_idx in range(start_kf_index, len(keyframes) - 1):
                if self._stop_event.is_set():
                    break

                kf_from = keyframes[kf_idx]
                kf_to   = keyframes[kf_idx + 1]

                duration = kf_from.duration_ms / 1000.0
                easing   = kf_from.easing
                steps    = max(1, int(duration * FPS))

                next_kf_idx = kf_idx + 1
                self.sig_keyframe.emit(next_kf_idx)

                # Play sound for windows whose target start frame matches next_kf_idx
                for win in anim.windows:
                    if win.sound_start_kf_index == next_kf_idx and kf_to.get_state(win.id).visible:
                        threading.Thread(target=_play_sound, args=(win,), daemon=True).start()

                # Tween step loop
                t0 = time.perf_counter()
                for step in range(steps + 1):
                    if self._stop_event.is_set():
                        break

                    t = step / steps

                    for win in anim.windows:
                        wid = win.id
                        dlg = self._dialogs.get(wid)
                        if dlg is None:
                            continue

                        s0 = kf_from.get_state(wid)
                        s1 = kf_to.get_state(wid)

                        win_easing = s0.easing if s0.easing else kf_from.easing
                        ix, iy = interpolate_pos(s0.x, s0.y, s1.x, s1.y, t, win_easing)

                        was_visible = s0.visible
                        will_visible = s1.visible

                        if was_visible and will_visible:
                            dlg.move_to(ix, iy)

                        elif not was_visible and will_visible and t > 0.5:
                            if not dlg.is_alive():
                                new_dlg = NativeDialog(win)
                                self._dialogs[wid] = new_dlg
                                threading.Thread(
                                    target=new_dlg.open, args=(ix, iy), daemon=True
                                ).start()

                        elif was_visible and not will_visible and t > 0.8:
                            if dlg.is_alive():
                                dlg.close()

                    # Precise timing
                    elapsed  = time.perf_counter() - t0
                    expected = (step + 1) * FRAME_DT
                    wait     = expected - elapsed
                    if wait > 0:
                        time.sleep(wait)

                # Hold after tween
                if kf_from.hold_ms > 0 and not self._stop_event.is_set():
                    time.sleep(kf_from.hold_ms / 1000.0)

            # Check loop condition after processing keyframe transitions
            if anim.loop and not self._stop_event.is_set():
                start_kf_index = 0
                loop_count += 1
                if loop_count > 100:
                    break
            else:
                break

        self._cleanup()
        self.is_playing = False

        if self._stop_event.is_set():
            self.sig_stopped.emit()
        else:
            self.sig_finish.emit()

    def _cleanup(self):
        for dlg in list(self._dialogs.values()):
            try:
                dlg.close()
            except Exception:
                pass
        self._dialogs.clear()
        stop_all_sounds()
