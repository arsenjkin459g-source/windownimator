"""
Windownimator 2.0 — Discord Rich Presence (RPC) Manager
Single persistent thread with Queue to avoid IPC socket race conditions.
"""

from __future__ import annotations
import time
import queue
import threading
from typing import Optional

try:
    from pypresence import Presence
    PYPRESENCE_AVAILABLE = True
except ImportError:
    PYPRESENCE_AVAILABLE = False

CLIENT_ID = "1531348985174823023"


class DiscordRPCManager:
    _instance: Optional[DiscordRPCManager] = None

    def __init__(self, client_id: str = CLIENT_ID):
        self.client_id = client_id
        self.rpc: Optional[Presence] = None
        self.connected = False
        self.start_time = int(time.time())
        self._queue: queue.Queue = queue.Queue()
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._enabled = PYPRESENCE_AVAILABLE

    @classmethod
    def get_instance(cls) -> DiscordRPCManager:
        if cls._instance is None:
            cls._instance = DiscordRPCManager()
        return cls._instance

    def connect_async(self):
        if not self._enabled or self._running:
            return
        self._running = True
        self._thread = threading.Thread(target=self._worker_loop, daemon=True)
        self._thread.start()

    def _worker_loop(self):
        # 1. Connect to Discord IPC
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            self._send_rpc("Создает анимацию", "Редактирование")
        except Exception:
            self.connected = False
            self.rpc = None

        last_sent = (None, None)

        # 2. Main Event Loop
        while self._running:
            try:
                # Wait for status update request with 2s timeout
                details, state = self._queue.get(timeout=2.0)
                if not self.connected and self._enabled:
                    try:
                        self.rpc = Presence(self.client_id)
                        self.rpc.connect()
                        self.connected = True
                    except Exception:
                        self.connected = False
                        self.rpc = None

                if self.connected and (details, state) != last_sent:
                    if self._send_rpc(details, state):
                        last_sent = (details, state)
            except queue.Empty:
                pass
            except Exception:
                pass

    def _send_rpc(self, details: str, state: str = "") -> bool:
        if not self.rpc or not self.connected:
            return False
        try:
            kwargs = {"details": details[:128], "start": self.start_time}
            if state:
                kwargs["state"] = state[:128]
            self.rpc.update(**kwargs)
            return True
        except Exception:
            self.connected = False
            self.rpc = None
            return False

    def update_status(self, details: str = "Создает анимацию", state: str = "Редактирование"):
        if not self._enabled:
            return
        if not self._running:
            self.connect_async()
        
        # Enqueue status update
        self._queue.put((details, state))

    def close(self):
        self._running = False
        if self.rpc and self.connected:
            try:
                self.rpc.close()
            except Exception:
                pass
        self.connected = False
        self.rpc = None
