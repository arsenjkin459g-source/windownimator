"""
Windownimator — Main Application Window
"""

from __future__ import annotations
import os
import sys
import ctypes
from typing import Optional

from PySide6.QtCore import Qt, QThread, Signal, QSettings, QStandardPaths
from PySide6.QtGui import QFont, QIcon, QKeySequence, QShortcut, QAction, QPixmap
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QSplitter, QStatusBar, QMessageBox, QFileDialog, QDialog,
    QProgressBar, QLabel, QLineEdit, QPlainTextEdit, QTextEdit, QPushButton, QToolButton,
    QGraphicsBlurEffect
)

from core.animation import Animation
from core.keyframe import Keyframe
from core.window_object import WindowObject
from core.player import AnimationPlayer
from core.exporter import export_to_exe

from ui.styles import DARK_THEME_QSS, THEMES, get_theme_qss, set_current_theme
from ui.stage import QtStage
from ui.timeline import QtTimeline
from ui.window_list import QtWindowListPanel
from ui.properties import QtPropertiesPanel

APP_TITLE = "Windownimator"
APP_VERSION = "2.0.0"


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

        icon_path = os.path.join(os.path.dirname(__file__), "windownimator.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.animation: Animation = Animation.new()
        self._selected_kf_id:   Optional[str] = None
        self._selected_win_id:  Optional[str] = None
        self._selected_win_ids: List[str]     = []
        self._undo_stack: List[dict]           = []
        self._player: Optional[AnimationPlayer] = None

        self._build_ui()
        saved_theme = QSettings("Windownimator", "Windownimator2").value("theme", "navy")
        self._set_theme(str(saved_theme))
        self._select_kf(self.animation.keyframes[0].id if self.animation.keyframes else None)
        self._refresh_all()
        self.animation.modified = False

    def _push_undo(self):
        snapshot = self.animation.to_dict()
        self._undo_stack.append(snapshot)
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)

    def _undo(self):
        if not self._undo_stack:
            self.status_bar.showMessage("Нечего отменять.")
            return
        snapshot = self._undo_stack.pop()
        fp = self.animation.file_path
        self.animation = Animation.from_dict(snapshot, file_path=fp)
        self.animation.modified = True
        self._refresh_all()

        wins = [self.animation.get_window(wid) for wid in self._selected_win_ids if self.animation.get_window(wid)]
        kf = self.animation.get_keyframe(self._selected_kf_id) if self._selected_kf_id else (self.animation.keyframes[0] if self.animation.keyframes else None)
        self.properties_panel.load_windows(wins, kf)
        self.win_list_panel.set_selected(self._selected_win_ids)
        self.stage.set_selected_windows(self._selected_win_ids)
        self.status_bar.showMessage("Действие отменено (Ctrl+Z).")

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
        self.win_list_panel.window_selected_ctrl.connect(self._on_select_window)
        self.win_list_panel.add_window_requested.connect(self._add_window)
        self.win_list_panel.delete_window_requested.connect(self._del_window)
        h_splitter.addWidget(self.win_list_panel)

        # Stage
        self.stage = QtStage()
        self.stage.window_selected_ctrl.connect(self._on_select_window)
        self.stage.window_move_started.connect(self._on_stage_move_start)
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

        # File Menu
        file_menu = menubar.addMenu("Файл")
        file_menu.addAction("Новый проект", self._new, QKeySequence("Ctrl+N"))
        file_menu.addAction("Открыть проект...", self._open, QKeySequence("Ctrl+O"))
        file_menu.addSeparator()
        file_menu.addAction("Сохранить", self._save, QKeySequence("Ctrl+S"))
        file_menu.addSeparator()
        file_menu.addAction("Выход", self.close)

        # Project Menu
        proj_menu = menubar.addMenu("Проект")
        proj_menu.addAction("Добавить кадр", self._add_kf)
        proj_menu.addAction("Удалить кадр", self._del_kf)
        proj_menu.addSeparator()
        proj_menu.addAction("Экспорт в EXE...", lambda: ExportDialog(self, self.animation).exec())

        # View / Theme Menu
        view_menu = menubar.addMenu("Вид")
        theme_menu = view_menu.addMenu("Тема оформления")
        for key, theme_info in THEMES.items():
            act = theme_menu.addAction(theme_info["name"])
            act.triggered.connect(lambda checked=False, k=key: self._set_theme(k))

        # Help Menu
        help_menu = menubar.addMenu("Справка")
        help_menu.addAction("О программе...", self._show_about)

    def _set_theme(self, theme_key: str):
        qss = get_theme_qss(theme_key)
        QApplication.instance().setStyleSheet(qss)
        self.menuBar().setStyleSheet("")
        QSettings("Windownimator", "Windownimator2").setValue("theme", theme_key)
        # Update all panel structural styles
        self.win_list_panel.update_theme()
        self.timeline.update_theme()
        self.properties_panel.update_theme()
        # Redraw stage background with new theme colors
        self.stage.scene.clear()
        self.stage._items_map.clear()
        self.stage._draw_stage_background()
        self._refresh_all()





    def _build_toolbar(self):
        toolbar = self.addToolBar("Основная панель")
        toolbar.setMovable(False)

        # Play / Stop Button
        self.btn_play = QPushButton("Проиграть анимацию")
        self.btn_play.setObjectName("btnSuccess")
        self.btn_play.setFixedHeight(34)
        self.btn_play.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_play.clicked.connect(self._toggle_play)
        toolbar.addWidget(self.btn_play)



    def _bind_shortcuts(self):
        sc_play  = QShortcut(QKeySequence("F5"), self, self._toggle_play)
        sc_stop  = QShortcut(QKeySequence("Escape"), self, self._stop_play)
        sc_dup   = QShortcut(QKeySequence("Ctrl+D"), self, self._dup_selected_kf)
        sc_undo  = QShortcut(QKeySequence("Ctrl+Z"), self, self._undo)
        sc_del   = QShortcut(QKeySequence("Delete"), self, self._del_selected_windows)
        sc_del2  = QShortcut(QKeySequence("Del"), self, self._del_selected_windows)
        sc_back  = QShortcut(QKeySequence("Backspace"), self, self._del_selected_windows)

        for sc in (sc_play, sc_stop, sc_dup, sc_undo, sc_del, sc_del2, sc_back):
            sc.setContext(Qt.ShortcutContext.WindowShortcut)

    def keyPressEvent(self, event):
        focused = QApplication.focusWidget()
        if focused and isinstance(focused, (QLineEdit, QPlainTextEdit, QTextEdit)):
            super().keyPressEvent(event)
            return

        key = event.key()
        is_ctrl = bool(event.modifiers() & Qt.KeyboardModifier.ControlModifier)

        if key in (Qt.Key.Key_Delete, Qt.Key.Key_Backspace):
            self._del_selected_windows()
            event.accept()
            return
        elif is_ctrl and key == Qt.Key.Key_Z:
            self._undo()
            event.accept()
            return

        super().keyPressEvent(event)

    # ── Actions ─────────────────────────────────────────────────────────────

    def _new(self, prompt_save: bool = True):
        if prompt_save and self.animation.modified:
            reply = QMessageBox.question(self, "Новый проект", "Сохранить текущие изменения?")
            if reply == QMessageBox.StandardButton.Yes:
                self._save()
        self._stop_play()
        self.animation = Animation.new()
        self.animation.modified = False
        self._undo_stack.clear()
        self._selected_kf_id = None
        self._selected_win_id = None
        self._selected_win_ids = []
        self._select_kf(self.animation.keyframes[0].id)
        self._refresh_all()
        self.animation.modified = False
        self.status_bar.showMessage("Новый проект создан.")

    def _get_default_projects_dir(self) -> str:
        docs_dir = QStandardPaths.writableLocation(QStandardPaths.StandardLocation.DocumentsLocation)
        projects_dir = os.path.join(docs_dir, "windownimator_projects")
        os.makedirs(projects_dir, exist_ok=True)
        return projects_dir

    def _open(self):
        default_dir = self._get_default_projects_dir()
        file_path, _ = QFileDialog.getOpenFileName(self, "Открыть проект", default_dir, "Windownimator Project (*.wa)")
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
        default_dir = self._get_default_projects_dir()
        default_path = os.path.join(default_dir, self.animation.name + ".wa")
        file_path, _ = QFileDialog.getSaveFileName(self, "Сохранить проект как", default_path, "Windownimator Project (*.wa)")
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
        self._selected_win_ids = [win.id]
        self._selected_win_id = win.id
        self._refresh_all()
        kf = self.animation.get_keyframe(self._selected_kf_id) if self._selected_kf_id else None
        self.properties_panel.load_windows([win], kf)

    def _del_window(self, win_id: str):
        if win_id not in self._selected_win_ids:
            self._selected_win_ids = [win_id]
        self._del_selected_windows()

    def _del_selected_windows(self):
        if not self._selected_win_ids:
            return
        count = len(self._selected_win_ids)
        msg = f"Удалить выбранные окна ({count})?" if count > 1 else f"Удалить выбранное окно?"
        reply = QMessageBox.question(self, "Удаление", msg)
        if reply == QMessageBox.StandardButton.Yes:
            self._push_undo()
            for wid in list(self._selected_win_ids):
                self.animation.remove_window(wid)
            self._selected_win_ids = []
            self._selected_win_id = None
            self.properties_panel.load_windows([], None)
            self._refresh_all()

    # ── Selection & Property Updates ────────────────────────────────────────

    def _select_kf(self, kf_id: Optional[str]):
        self._selected_kf_id = kf_id
        kf = self.animation.get_keyframe(kf_id) if kf_id else (self.animation.keyframes[0] if self.animation.keyframes else None)
        self.stage.set_keyframe(kf)
        self.properties_panel.load_keyframe(kf)
        if self._selected_win_ids:
            wins = [self.animation.get_window(wid) for wid in self._selected_win_ids if self.animation.get_window(wid)]
            if wins:
                self.properties_panel.load_windows(wins, kf)

    def _on_kf_select(self, kf_id: str):
        self._select_kf(kf_id)
        self.timeline.refresh(self.animation, self._selected_kf_id)

    def _on_select_window(self, win_id: Optional[str], is_ctrl: bool = False):
        if not win_id:
            self._selected_win_ids = []
            self._selected_win_id = None
        elif is_ctrl:
            if win_id in self._selected_win_ids:
                self._selected_win_ids.remove(win_id)
            else:
                self._selected_win_ids.append(win_id)
            self._selected_win_id = self._selected_win_ids[-1] if self._selected_win_ids else None
        else:
            self._selected_win_ids = [win_id]
            self._selected_win_id = win_id

        wins = [self.animation.get_window(wid) for wid in self._selected_win_ids if self.animation.get_window(wid)]
        kf = self.animation.get_keyframe(self._selected_kf_id) if self._selected_kf_id else (self.animation.keyframes[0] if self.animation.keyframes else None)
        
        self.properties_panel.load_windows(wins, kf)
        self.win_list_panel.set_selected(self._selected_win_ids)
        self.stage.set_selected_windows(self._selected_win_ids)

    def _on_stage_move_start(self, win_id: str):
        self._push_undo()

    def _on_stage_move(self, win_id: str, x: int, y: int):
        self.animation.modified = True
        self._update_title()

    def _on_win_prop_change(self):
        self.animation.modified = True
        self.win_list_panel.refresh(self.animation, self._selected_win_ids)
        self.stage.refresh()
        self.stage.set_selected_windows(self._selected_win_ids)
        self._update_title()
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
        ver = f" {APP_VERSION}" if APP_VERSION else ""
        self.setWindowTitle(f"{APP_TITLE}{ver}{fp}{mod}")

    def changeEvent(self, event):
        if event.type() == event.Type.WindowStateChange:
            self._update_title()
        super().changeEvent(event)

    def resizeEvent(self, event):
        self._update_title()
        super().resizeEvent(event)

    def _show_about(self):
        AboutDialog(self).exec()

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


# ── About Dialog ──────────────────────────────────────────────────────────────

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("О программе Windownimator")
        self.setFixedSize(460, 220)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)

        icon_path = os.path.join(os.path.dirname(__file__), "windownimator.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QDialog {
                background-color: #232323;
                color: #f4f4f5;
            }
            QLabel {
                color: #f4f4f5;
            }
            QPushButton {
                background-color: #2f2f2f;
                color: #f4f4f5;
                border: 1px solid #444444;
                border-radius: 8px;
                padding: 8px 24px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #3a3a3a;
                border-color: #555555;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(14)

        # Header App Title
        title_box = QVBoxLayout()
        title_box.setSpacing(4)
        app_name_lbl = QLabel(f"Windownimator {APP_VERSION}")
        app_name_lbl.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title_box.addWidget(app_name_lbl)

        desc_lbl = QLabel("Инструмент для создания анимаций системных диалоговых окон Windows.")
        desc_lbl.setStyleSheet("color: #a1a1aa;")
        desc_lbl.setWordWrap(True)
        title_box.addWidget(desc_lbl)

        layout.addLayout(title_box)

        # Repo URL
        repo_url = "https://github.com/arsenjkin459g-source/windownimator"
        repo_lbl = QLabel(f'Репозиторий GitHub:<br><a href="{repo_url}" style="color: #60a5fa; text-decoration: underline;">{repo_url}</a>')
        repo_lbl.setOpenExternalLinks(True)
        repo_lbl.setFont(QFont("Segoe UI", 10))
        layout.addWidget(repo_lbl)

        layout.addStretch()

        # Close button
        btn_box = QHBoxLayout()
        btn_box.addStretch()
        ok_btn = QPushButton("Закрыть")
        ok_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        ok_btn.clicked.connect(self.accept)
        btn_box.addWidget(ok_btn)

        layout.addLayout(btn_box)


# ── Welcome Dialog ─────────────────────────────────────────────────────────────

class WelcomeDialog(QDialog):
    ACTION_NONE  = 0
    ACTION_NEW   = 1
    ACTION_OPEN  = 2
    ACTION_CLOSE = 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Добро пожаловать в Windownimator 2.0")
        self.setFixedSize(580, 420)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowTitleHint | Qt.WindowType.WindowCloseButtonHint)
        self.action = self.ACTION_NONE

        icon_path = os.path.join(os.path.dirname(__file__), "windownimator.ico")
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.setStyleSheet("""
            QDialog {
                background-color: #232323;
                color: #f4f4f5;
            }
            QLabel {
                color: #f4f4f5;
            }
            QPushButton#welcomeBtn {
                background-color: #2f2f2f;
                color: #f4f4f5;
                border: 1px solid #444444;
                border-radius: 10px;
                padding: 16px;
                text-align: left;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton#welcomeBtn:hover {
                background-color: #3a3a3a;
                border-color: #555555;
                color: #ffffff;
            }
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 20)
        layout.setSpacing(14)

        # ── Banner Header Container ──────────────────────────────────────────
        banner_container = QWidget()
        banner_container.setFixedHeight(150)

        self.banner_lbl = QLabel(banner_container)
        self.banner_lbl.setGeometry(0, 0, 580, 150)

        banner_path = os.path.join(os.path.dirname(__file__), "assets", "welcome_banner.jpg")
        if not os.path.exists(banner_path):
            banner_path = os.path.join(os.path.dirname(__file__), "assets", "readme_header.jpg")

        if os.path.exists(banner_path):
            pixmap = QPixmap(banner_path).scaled(580, 150, Qt.AspectRatioMode.KeepAspectRatioByExpanding, Qt.TransformationMode.SmoothTransformation)
            self.banner_lbl.setPixmap(pixmap)

            blur = QGraphicsBlurEffect()
            blur.setBlurRadius(8.0)
            self.banner_lbl.setGraphicsEffect(blur)

        layout.addWidget(banner_container)

        # ── Action Text & Buttons ───────────────────────────────────────────
        sub_lbl = QLabel("   Выберите действие для начала работы над анимацией:")
        sub_lbl.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        sub_lbl.setStyleSheet("color: #e4e4e7;")
        layout.addWidget(sub_lbl)

        btn_box = QVBoxLayout()
        btn_box.setContentsMargins(24, 0, 24, 0)
        btn_box.setSpacing(12)

        btn_new = QPushButton("Создать новую анимацию\nНачать проект с чистого листа")
        btn_new.setObjectName("welcomeBtn")
        btn_new.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_new.clicked.connect(self._on_new)
        btn_box.addWidget(btn_new)

        btn_open = QPushButton("Открыть файл анимации (.wa)\nЗагрузить существующий проект из файла")
        btn_open.setObjectName("welcomeBtn")
        btn_open.setCursor(Qt.CursorShape.PointingHandCursor)
        btn_open.clicked.connect(self._on_open)
        btn_box.addWidget(btn_open)

        layout.addLayout(btn_box)
        layout.addStretch()

    def _on_new(self):
        self.action = self.ACTION_NEW
        self.accept()

    def _on_open(self):
        self.action = self.ACTION_OPEN
        self.accept()

    def _on_close(self):
        self.action = self.ACTION_CLOSE
        self.reject()

    def reject(self):
        self.action = self.ACTION_CLOSE
        super().reject()


# ── Entry Point ───────────────────────────────────────────────────────────────

def main():
    try:
        myappid = "Windownimator.Windownimator2.App.2.0"
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setStyleSheet(DARK_THEME_QSS)

    icon_path = os.path.join(os.path.dirname(__file__), "windownimator.ico")
    if os.path.exists(icon_path):
        app.setWindowIcon(QIcon(icon_path))

    window = MainWindow()

    dlg = WelcomeDialog(window)
    res = dlg.exec()

    if dlg.action == WelcomeDialog.ACTION_OPEN:
        window.show()
        window._open()
    elif dlg.action == WelcomeDialog.ACTION_NEW:
        window.show()
        window._new(prompt_save=False)
    else:
        sys.exit(0)

    sys.exit(app.exec())


if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    main()
