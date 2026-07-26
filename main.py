"""
Windownimator — Main Application Window
"""

from __future__ import annotations
import os
import sys
import ctypes
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QAction
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QFileDialog, QDialog,
    QProgressBar, QLabel, QLineEdit, QPushButton
)

from core.animation import Animation
from core.keyframe import Keyframe
from core.window_object import WindowObject
from core.player import AnimationPlayer
from core.exporter import export_to_exe

from ui.styles import DARK_THEME_QSS
from ui.stage import QtStage
from ui.timeline import QtTimeline
from ui.window_list import QtWindowListPanel
from ui.properties import QtPropertiesPanel

APP_TITLE = "Windownimator"
APP_VERSION = "1.0.0"


# ── Export Dialog ─────────────────────────────────────────────────────────────

class ExporterWorker(QThread):
    progress = Signal(str)
    finished = Signal(str)
    failed = Signal(str)

    def __init__(self, animation: Animation, out_dir: str, exe_name: str):
        super().__init__()
        self.animation = animation
        self.out_dir = out_dir
        self.exe_name = exe_name

    def run(self):
        try:
            exe_path = export_to_exe(
                self.animation,
                self.out_dir,
                exe_name=self.exe_name,
                on_progress=lambda msg: self.progress.emit(msg)
            )
            self.finished.emit(exe_path)
        except Exception as e:
            self.failed.emit(str(e))


class ExportDialog(QDialog):
    def __init__(self, parent, animation: Animation):
        super().__init__(parent)
        self.animation = animation
        self.setWindowTitle("📦 Экспорт анимации в EXE")
        self.setFixedSize(480, 260)
        self.setStyleSheet("background-color: #0f172a; color: #f8fafc;")
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(14)

        hdr = QLabel("📦  Экспорт анимации в EXE")
        hdr.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        hdr.setStyleSheet("color: #38bdf8;")
        layout.addWidget(hdr)

        sub = QLabel("Создаёт автономный исполняемый файл Windows без установки Python.")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("color: #94a3b8;")
        layout.addWidget(sub)

        # Name row
        r1 = QHBoxLayout()
        r1.addWidget(QLabel("Имя EXE:"))
        safe_name = "".join(c if c.isalnum() or c in "-_" else "_" for c in self.animation.name) or "animation"
        self.name_edit = QLineEdit(safe_name)
        r1.addWidget(self.name_edit)
        layout.addLayout(r1)

        # Dir row
        r2 = QHBoxLayout()
        r2.addWidget(QLabel("Папка:"))
        self.dir_edit = QLineEdit(os.path.expanduser("~/Desktop"))
        r2.addWidget(self.dir_edit)
        
        browse_btn = QPushButton("Обзор...")
        browse_btn.setFixedWidth(70)
        browse_btn.clicked.connect(self._browse)
        r2.addWidget(browse_btn)
        layout.addLayout(r2)

        # Progress / Status
        self.status_lbl = QLabel("")
        self.status_lbl.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
        self.status_lbl.setStyleSheet("color: #60a5fa;")
        layout.addWidget(self.status_lbl)

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate
        self.progress_bar.hide()
        layout.addWidget(self.progress_bar)

        # Buttons
        btn_box = QHBoxLayout()
        btn_box.addStretch()

        self.export_btn = QPushButton("Компилировать")
        self.export_btn.setObjectName("btnPrimary")
        self.export_btn.clicked.connect(self._start_export)
        btn_box.addWidget(self.export_btn)

        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        btn_box.addWidget(cancel_btn)

        layout.addLayout(btn_box)

    def _browse(self):
        d = QFileDialog.getExistingDirectory(self, "Выберите папку для сохранения EXE")
        if d:
            self.dir_edit.setText(d)

    def _start_export(self):
        exe_name = self.name_edit.text().strip()
        out_dir = self.dir_edit.text().strip()

        if not exe_name or not os.path.isdir(out_dir):
            QMessageBox.warning(self, "Ошибка", "Укажите верное имя файла и существующую папку.")
            return

        self.export_btn.setEnabled(False)
        self.progress_bar.show()

        self.worker = ExporterWorker(self.animation, out_dir, exe_name)
        self.worker.progress.connect(self.status_lbl.setText)
        self.worker.finished.connect(self._on_finished)
        self.worker.failed.connect(self._on_failed)
        self.worker.start()

    def _on_finished(self, exe_path: str):
        self.progress_bar.hide()
        self.export_btn.setEnabled(True)
        self.status_lbl.setText("Готово!")
        
        reply = QMessageBox.question(
            self, "Успех", f"EXE файл успешно создан:\n{exe_path}\n\nОткрыть папку с файлом?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        if reply == QMessageBox.StandardButton.Yes:
            os.startfile(os.path.dirname(exe_path))
        self.accept()

    def _on_failed(self, err_msg: str):
        self.progress_bar.hide()
        self.export_btn.setEnabled(True)
        self.status_lbl.setText("Ошибка компиляции")
        QMessageBox.critical(self, "Ошибка экспорта", err_msg)


def enable_window_blur(hwnd: int):
    dwmapi = ctypes.windll.dwmapi
    
    # 1. Official Windows DWM BlurBehind API
    class DWM_BLURBEHIND(ctypes.Structure):
        _fields_ = [
            ('dwFlags', ctypes.c_ulong),
            ('fEnable', ctypes.c_int),
            ('hRgnBlur', ctypes.c_void_p),
            ('fTransitionOnMaximized', ctypes.c_int)
        ]

    try:
        bb = DWM_BLURBEHIND()
        bb.dwFlags = 1  # DWM_BB_ENABLE
        bb.fEnable = True
        bb.hRgnBlur = None
        bb.fTransitionOnMaximized = False
        dwmapi.DwmEnableBlurBehindWindow(ctypes.c_void_p(hwnd), ctypes.byref(bb))
    except Exception:
        pass

    # 2. Windows 10/11 SetWindowCompositionAttribute
    try:
        user32 = ctypes.windll.user32
        class ACCENT_POLICY(ctypes.Structure):
            _fields_ = [
                ('AccentState', ctypes.c_int),
                ('AccentFlags', ctypes.c_int),
                ('GradientColor', ctypes.c_uint),
                ('AnimationId', ctypes.c_int)
            ]

        class WINDOWCOMPOSITIONATTRIBDATA(ctypes.Structure):
            _fields_ = [
                ('Attribute', ctypes.c_int),
                ('Data', ctypes.c_void_p),
                ('SizeOfData', ctypes.c_size_t)
            ]

        accent = ACCENT_POLICY()
        accent.AccentState = 3  # ACCENT_ENABLE_BLURBEHIND
        accent.GradientColor = 0x440b0d19

        data = WINDOWCOMPOSITIONATTRIBDATA()
        data.Attribute = 19
        data.Data = ctypes.addressof(accent)
        data.SizeOfData = ctypes.sizeof(accent)

        user32.SetWindowCompositionAttribute(ctypes.c_void_p(hwnd), ctypes.byref(data))
    except Exception:
        pass


# ── MainWindow ────────────────────────────────────────────────────────────────

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(f"{APP_TITLE}")
        self.resize(1400, 850)
        self.setMinimumSize(1000, 650)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self.animation: Animation = Animation.new()
        self._selected_kf_id:  Optional[str] = None
        self._selected_win_id: Optional[str] = None
        self._player: Optional[AnimationPlayer] = None

        self._build_ui()
        self._select_kf(self.animation.keyframes[0].id if self.animation.keyframes else None)
        self._refresh_all()

    def showEvent(self, event):
        super().showEvent(event)
        enable_window_blur(int(self.winId()))

    def _build_ui(self):
        self._build_menubar()
        self._build_toolbar()

        # Central Layout with Splitters
        central_widget = QWidget()
        central_widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setCentralWidget(central_widget)
        main_vbox = QVBoxLayout(central_widget)
        main_vbox.setContentsMargins(0, 0, 0, 0)
        main_vbox.setSpacing(0)

        # Horizontal Splitter: Left Sidebar | Stage Canvas | Right Sidebar
        h_splitter = QSplitter(Qt.Orientation.Horizontal)
        h_splitter.setHandleWidth(2)

        # Left Window List
        self.win_list_panel = QtWindowListPanel()
        self.win_list_panel.window_selected.connect(self._on_select_window)
        self.win_list_panel.add_window_requested.connect(self._add_window)
        self.win_list_panel.delete_window_requested.connect(self._del_window)
        h_splitter.addWidget(self.win_list_panel)

        # Stage
        self.stage = QtStage()
        self.stage.window_selected.connect(self._on_stage_select_window)
        self.stage.window_moved.connect(self._on_stage_move)
        h_splitter.addWidget(self.stage)

        # Right Properties
        self.properties_panel = QtPropertiesPanel()
        self.properties_panel.window_changed.connect(self._on_win_prop_change)
        self.properties_panel.keyframe_changed.connect(self._on_kf_prop_change)
        h_splitter.addWidget(self.properties_panel)

        h_splitter.setSizes([260, 860, 280])
        
        # Vertical Splitter: Top (Stage & Sidebars) | Bottom (Timeline)
        v_splitter = QSplitter(Qt.Orientation.Vertical)
        v_splitter.setHandleWidth(2)
        v_splitter.addWidget(h_splitter)

        # Timeline Widget
        self.timeline = QtTimeline()
        self.timeline.keyframe_selected.connect(self._on_kf_select)
        self.timeline.add_keyframe_requested.connect(self._add_kf)
        self.timeline.delete_keyframe_requested.connect(self._del_kf_by_id)
        self.timeline.duplicate_keyframe_requested.connect(self._dup_kf)
        self.timeline.move_left_requested.connect(self._move_kf_left)
        self.timeline.move_right_requested.connect(self._move_kf_right)

        self.timeline.setMinimumHeight(150)
        v_splitter.addWidget(self.timeline)
        v_splitter.setStretchFactor(0, 4)
        v_splitter.setStretchFactor(1, 1)
        v_splitter.setSizes([600, 180])

        main_vbox.addWidget(v_splitter)

        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("  Готово")

        self._bind_shortcuts()

    def _build_menubar(self):
        menubar = self.menuBar()
        menubar.setStyleSheet("background-color: #0f172a; color: #f8fafc;")

        # File Menu
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Новый проект", self._new, QKeySequence("Ctrl+N"))
        file_menu.addAction("Открыть проект...", self._open, QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("Сохранить", self._save, QKeySequence("Ctrl+S"))
        file_menu.addAction("Сохранить как...", self._save_as, QKeySequence("Ctrl+Shift+S"))
        file_menu.addSeparator()
        file_menu.addAction("Выход", self.close)

        # Project Menu
        proj_menu = menubar.addMenu("Проект")
        proj_menu.addAction("Добавить кадр", self._add_kf)
        proj_menu.addAction("Удалить кадр", self._del_kf)
        proj_menu.addSeparator()
        proj_menu.addAction("Экспорт в EXE...", lambda: ExportDialog(self, self.animation).exec())

    def _build_toolbar(self):
        toolbar = self.addToolBar("Основная панель")
        toolbar.setMovable(False)

        # Quick Actions
        act_new = QAction("Новый", self)
        act_new.triggered.connect(self._new)
        toolbar.addAction(act_new)

        act_open = QAction("Открыть", self)
        act_open.triggered.connect(self._open)
        toolbar.addAction(act_open)

        act_save = QAction("Сохранить", self)
        act_save.triggered.connect(self._save)
        toolbar.addAction(act_save)

        toolbar.addSeparator()

        act_add_kf = QAction("Добавить кадр", self)
        act_add_kf.triggered.connect(self._add_kf)
        toolbar.addAction(act_add_kf)

        act_del_kf = QAction("Удалить кадр", self)
        act_del_kf.triggered.connect(self._del_kf)
        toolbar.addAction(act_del_kf)

        toolbar.addSeparator()

        # Play / Stop Button
        self.btn_play = QPushButton("Проиграть анимацию")
        self.btn_play.setObjectName("btnSuccess")
        self.btn_play.setFixedHeight(34)
        self.btn_play.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_play.clicked.connect(self._toggle_play)
        toolbar.addWidget(self.btn_play)

        toolbar.addSeparator()

        btn_export = QPushButton("Экспорт в EXE")
        btn_export.setObjectName("btnPrimary")
        btn_export.setFixedHeight(34)
        btn_export.clicked.connect(lambda: ExportDialog(self, self.animation).exec())
        toolbar.addWidget(btn_export)

    def _bind_shortcuts(self):
        QShortcut(QKeySequence("F5"), self, self._toggle_play)
        QShortcut(QKeySequence("Escape"), self, self._stop_play)
        QShortcut(QKeySequence("Ctrl+D"), self, self._dup_selected_kf)

    # ── Actions ─────────────────────────────────────────────────────────────

    def _new(self):
        if self.animation.modified:
            reply = QMessageBox.question(self, "Новый проект", "Сохранить текущие изменения?")
            if reply == QMessageBox.StandardButton.Yes:
                self._save()
        self._stop_play()
        self.animation = Animation.new()
        self._selected_kf_id = None
        self._selected_win_id = None
        self._select_kf(self.animation.keyframes[0].id)
        self._refresh_all()
        self.status_bar.showMessage("Новый проект создан.")

    def _open(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть проект", "", "Windownimator Project (*.wa)")
        if file_path:
            self._stop_play()
            self.animation = Animation.load(file_path)
            self._selected_kf_id = None
            self._selected_win_id = None
            if self.animation.keyframes:
                self._select_kf(self.animation.keyframes[0].id)
            self._refresh_all()
            self.status_bar.showMessage(f"Открыт: {os.path.basename(file_path)}")

    def _save(self):
        if not self.animation.file_path:
            return self._save_as()
        self.animation.save()
        self._update_title()
        self.status_bar.showMessage(f"Сохранено: {os.path.basename(self.animation.file_path)}")

    def _save_as(self):
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить проект как", self.animation.name + ".wa", "Windownimator Project (*.wa)")
        if file_path:
            self.animation.save(file_path)
            self._update_title()
            self.status_bar.showMessage(f"Сохранено: {os.path.basename(file_path)}")

    # ── Keyframe & Window Handling ──────────────────────────────────────────

    def _add_kf(self):
        idx = None
        if self._selected_kf_id:
            idx = self.animation.get_keyframe_index(self._selected_kf_id)
        kf = self.animation.add_keyframe(after_index=idx)
        self._select_kf(kf.id)
        self._refresh_all()

    def _del_kf(self):
        if self._selected_kf_id:
            self._del_kf_by_id(self._selected_kf_id)

    def _del_kf_by_id(self, kf_id: str):
        if len(self.animation.keyframes) <= 1:
            QMessageBox.warning(self, "Предупреждение", "Нельзя удалить единственный ключевой кадр.")
            return
        idx = self.animation.get_keyframe_index(kf_id)
        self.animation.remove_keyframe(kf_id)
        kfs = self.animation.keyframes
        new_id = kfs[min(idx, len(kfs)-1)].id if kfs else None
        self._select_kf(new_id)
        self._refresh_all()

    def _dup_kf(self, kf_id: str):
        new_kf = self.animation.duplicate_keyframe(kf_id)
        if new_kf:
            self._select_kf(new_kf.id)
            self._refresh_all()

    def _dup_selected_kf(self):
        if self._selected_kf_id:
            self._dup_kf(self._selected_kf_id)

    def _move_kf_left(self, kf_id: str):
        idx = self.animation.get_keyframe_index(kf_id)
        if idx > 0:
            self.animation.move_keyframe(idx, idx - 1)
            self.timeline.refresh(self.animation, self._selected_kf_id)

    def _move_kf_right(self, kf_id: str):
        idx = self.animation.get_keyframe_index(kf_id)
        if idx < len(self.animation.keyframes) - 1:
            self.animation.move_keyframe(idx, idx + 1)
            self.timeline.refresh(self.animation, self._selected_kf_id)

    def _add_window(self, icon_type: str = "info"):
        titles = {"info":"Информация","warning":"Предупреждение","error":"Ошибка","question":"Вопрос","none":"Окно"}
        msgs = {
            "info": "Информационное сообщение.",
            "warning": "Предупредительное сообщение!",
            "error": "Критическая ошибка системного уровня!",
            "question": "Вы действительно хотите выполнить действие?",
            "none": "Произвольное окно."
        }
        count = sum(1 for w in self.animation.windows if w.icon == icon_type) + 1
        name = f"{titles.get(icon_type, 'Окно')} {count}"
        win = WindowObject(name=name, title=titles.get(icon_type, "Окно"), message=msgs.get(icon_type, ""), icon=icon_type)
        self.animation.add_window(win)
        self._selected_win_id = win.id
        self._refresh_all()
        self.properties_panel.load_window(win)

    def _del_window(self, win_id: str):
        win = self.animation.get_window(win_id)
        name = win.name if win else "Окно"
        reply = QMessageBox.question(self, "Удаление", f"Удалить «{name}»?")
        if reply == QMessageBox.StandardButton.Yes:
            self.animation.remove_window(win_id)
            if self._selected_win_id == win_id:
                self._selected_win_id = None
                self.properties_panel.load_window(None)
            self._refresh_all()

    # ── Selection & Property Updates ────────────────────────────────────────

    def _select_kf(self, kf_id: Optional[str]):
        self._selected_kf_id = kf_id
        kf = self.animation.get_keyframe(kf_id) if kf_id else None
        self.stage.set_keyframe(kf)
        self.properties_panel.load_keyframe(kf)

    def _on_kf_select(self, kf_id: str):
        self._select_kf(kf_id)
        self.timeline.refresh(self.animation, self._selected_kf_id)

    def _on_select_window(self, win_id: Optional[str]):
        self._selected_win_id = win_id
        win = self.animation.get_window(win_id) if win_id else None
        self.properties_panel.load_window(win)
        self.stage.set_selected_window(win_id)

    def _on_stage_select_window(self, win_id: Optional[str]):
        self._selected_win_id = win_id
        win = self.animation.get_window(win_id) if win_id else None
        self.properties_panel.load_window(win)
        self.win_list_panel.set_selected(win_id)

    def _on_stage_move(self, win_id: str, x: int, y: int):
        self.animation.modified = True
        self._update_title()

    def _on_win_prop_change(self):
        self.animation.modified = True
        self.win_list_panel.refresh(self.animation, self._selected_win_id)
        self.stage.refresh()
        self._update_title()

    def _on_kf_prop_change(self):
        self.animation.modified = True
        self.timeline.refresh(self.animation, self._selected_kf_id)
        self._update_title()

    # ── Playback Engine ─────────────────────────────────────────────────────

    def _toggle_play(self):
        if self._player and self._player.is_playing:
            self._stop_play()
        else:
            self._start_play()

    def _start_play(self):
        if not self.animation.keyframes or not self.animation.windows:
            QMessageBox.warning(self, "Ошибка", "Для запуска добавьте хотя бы 1 окно и 1 кадр.")
            return

        self.btn_play.setText("Остановить")
        self.btn_play.setObjectName("btnDanger")
        self.btn_play.setStyleSheet("")

        start_idx = 0

        self._player = AnimationPlayer(
            root=self,
            animation=self.animation,
            on_keyframe=self._on_play_kf,
            on_finish=self._on_play_done,
            on_stopped=self._on_play_done
        )
        self._player.play(start_kf_index=start_idx)
        self.status_bar.showMessage("Воспроизведение анимации...")

    def _stop_play(self):
        if self._player:
            self._player.stop()
            self._player = None
        self.btn_play.setText("Проиграть анимацию")
        self.btn_play.setObjectName("btnSuccess")
        self.btn_play.setStyleSheet("")
        self.status_bar.showMessage("Воспроизведение остановлено.")

    def _on_play_kf(self, idx: int):
        kfs = self.animation.keyframes
        if 0 <= idx < len(kfs):
            kf_id = kfs[idx].id
            self._selected_kf_id = kf_id
            self.timeline.refresh(self.animation, self._selected_kf_id)

    def _on_play_done(self):
        self._stop_play()
        self.timeline.refresh(self.animation, self._selected_kf_id)
        self.status_bar.showMessage("Анимация завершена.")

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _refresh_all(self):
        self.win_list_panel.refresh(self.animation, self._selected_win_id)
        self.timeline.refresh(self.animation, self._selected_kf_id)
        kf = self.animation.get_keyframe(self._selected_kf_id) if self._selected_kf_id else None
        self.stage.load(self.animation, kf)
        self._update_title()

    def _update_title(self):
        mod = " •" if self.animation.modified else ""
        fp = f" — {os.path.basename(self.animation.file_path)}" if self.animation.file_path else ""
        warn = "" if self.isMaximized() else " [ВНИМАНИЕ: Окно не развёрнуто на весь экран — возможны проблемы с отображением интерфейса]"
        ver = f" {APP_VERSION}" if APP_VERSION else ""
        self.setWindowTitle(f"{APP_TITLE}{ver}{fp}{mod}{warn}")

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self._update_title()
        super().changeEvent(event)

    def resizeEvent(self, event):
        self._update_title()
        super().resizeEvent(event)

    def closeEvent(self, event):
        if self.animation.modified:
            reply = QMessageBox.question(
                self, "Выход", "Сохранить проект перед выходом?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No | QMessageBox.StandardButton.Cancel
            )
            if reply == QMessageBox.StandardButton.Yes:
                self._save()
            elif reply == QMessageBox.StandardButton.Cancel:
                event.ignore()
                return
        event.accept()


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
