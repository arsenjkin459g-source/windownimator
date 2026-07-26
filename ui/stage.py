"""
Windownimator 2.0 — PySide6 Stage (Canvas Editor)
Interactive graphics view showing windows as draggable cards.
"""

from __future__ import annotations
from typing import Callable, Dict, Optional, TYPE_CHECKING
from PySide6.QtCore import Qt, QRectF, Signal, QPointF
from PySide6.QtGui import QColor, QPen, QBrush, QFont, QPainter, QLinearGradient, QAction, QPainterPath
from PySide6.QtWidgets import (
    QGraphicsView, QGraphicsScene, QGraphicsItem, QGraphicsRectItem, QGraphicsPathItem,
    QGraphicsTextItem, QMenu, QGraphicsDropShadowEffect
)

if TYPE_CHECKING:
    from core.animation import Animation
    from core.keyframe import Keyframe, WindowState
    from core.window_object import WindowObject

STAGE_W = 1920
STAGE_H = 1080
CARD_W = 340
CARD_H = 180

ICON_COLORS = {
    "info":     "#38bdf8",
    "warning":  "#fbbf24",
    "error":    "#f87171",
    "question": "#c084fc",
    "none":     "#94a3b8",
}

ICON_SYMBOLS = {
    "info":     "ℹ️",
    "warning":  "⚠️",
    "error":    "❌",
    "question": "❓",
    "none":     "🪟",
}


class WindowCardItem(QGraphicsItem):
    """Draggable QGraphicsItem representing a window in the Stage."""

    def __init__(self, win_obj: "WindowObject", state: "WindowState", stage_view: "QtStage"):
        super().__init__()
        self.win_obj = win_obj
        self.state = state
        self.stage_view = stage_view

        self.setFlags(
            QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
            QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
            QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges
        )
        self.setAcceptHoverEvents(True)
        self.setPos(state.x, state.y)

    def boundingRect(self) -> QRectF:
        return QRectF(0, 0, CARD_W, CARD_H)

    def paint(self, painter: QPainter, option, widget=None):
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        is_sel = self.isSelected()
        is_vis = self.state.visible

        # Card Background
        rect = self.boundingRect()
        bg_color = QColor("#1e293b") if is_vis else QColor("#0f172a")
        border_color = QColor("#3b82f6") if is_sel else QColor(ICON_COLORS.get(self.win_obj.icon, "#94a3b8"))
        
        if not is_vis:
            border_color = QColor("#334155")

        # Shadow / Glow
        if is_sel:
            painter.setPen(QPen(QColor("#60a5fa"), 3))
        else:
            painter.setPen(QPen(border_color, 1.5))

        painter.setBrush(QBrush(bg_color))
        painter.drawRoundedRect(rect, 10, 10)

        # Title Bar
        title_bg = QColor("#0f172a") if is_vis else QColor("#020617")
        painter.setBrush(QBrush(title_bg))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(QRectF(0, 0, CARD_W, 38), 10, 10)
        painter.drawRect(QRectF(0, 24, CARD_W, 14))  # Fill bottom rounded corners of title bar

        # Icon Symbol
        icon_sym = ICON_SYMBOLS.get(self.win_obj.icon, "🪟")
        icon_col = QColor(ICON_COLORS.get(self.win_obj.icon, "#94a3b8")) if is_vis else QColor("#475569")
        
        font_icon = QFont("Segoe UI", 15, QFont.Weight.Bold)
        painter.setFont(font_icon)
        painter.setPen(icon_col)
        painter.drawText(QRectF(12, 5, 28, 28), Qt.AlignmentFlag.AlignCenter, icon_sym)

        # Title Text
        font_title = QFont("Segoe UI", 13, QFont.Weight.Bold)
        painter.setFont(font_title)
        painter.setPen(QColor("#ffffff") if is_vis else QColor("#64748b"))
        title_txt = self.win_obj.title
        if len(title_txt) > 28:
            title_txt = title_txt[:27] + "…"
        painter.drawText(QRectF(44, 4, CARD_W - 54, 30), Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft, title_txt)

        # Body Message Text
        font_msg = QFont("Segoe UI", 13, QFont.Weight.DemiBold)
        painter.setFont(font_msg)
        painter.setPen(QColor("#f1f5f9") if is_vis else QColor("#64748b"))
        msg_txt = self.win_obj.message.replace("\n", " ")
        if len(msg_txt) > 50:
            msg_txt = msg_txt[:49] + "…"
        painter.drawText(QRectF(16, 44, CARD_W - 32, 90), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, msg_txt)

        # Footer Coords & Name
        font_sub = QFont("Segoe UI", 10, QFont.Weight.DemiBold)
        painter.setFont(font_sub)
        painter.setPen(QColor("#94a3b8") if is_vis else QColor("#475569"))
        painter.drawText(QRectF(14, CARD_H - 28, CARD_W - 28, 22), Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter, self.win_obj.name)
        painter.drawText(QRectF(14, CARD_H - 28, CARD_W - 28, 22), Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter, f"{int(self.pos().x())},{int(self.pos().y())}")

    def itemChange(self, change, value):
        if change == QGraphicsItem.GraphicsItemChange.ItemPositionChange:
            new_pos = value
            # Clamp position to Virtual Stage Bounds
            x = max(0, min(STAGE_W - CARD_W, new_pos.x()))
            y = max(0, min(STAGE_H - CARD_H, new_pos.y()))
            self.state.x = int(x)
            self.state.y = int(y)
            self.stage_view.window_moved.emit(self.win_obj.id, int(x), int(y))
            return QPointF(x, y)
        elif change == QGraphicsItem.GraphicsItemChange.ItemSelectedChange:
            if value is True:
                self.stage_view.window_selected.emit(self.win_obj.id)
        return super().itemChange(change, value)

    def contextMenuEvent(self, event):
        menu = QMenu()
        menu.setStyleSheet("QMenu { background-color: #0f172a; color: #f8fafc; border: 1px solid #334155; }")
        
        # ── TODO: [FEATURE NOTE FOR FUTURE] ──────────────────────────────────────────
        # Функция "Скрыть в кадре" (WindowState.visible = False) удалена по запросу пользователя.
        # Если понадобится восстановить возможность скрытия окон на конкретных кадрах:
        # 1. Раскомментировать пункт меню: vis_act = menu.addAction("🚫 Скрыть в кадре" if self.state.visible else "👁 Показать в кадре")
        # 2. Обработать action == vis_act: toggle self.state.visible и self.update()
        # 3. В paint() отрисовать надпись/иконку 🚫 при not self.state.visible
        # ─────────────────────────────────────────────────────────────────────────────

        center_act = menu.addAction("Центрировать")
        
        action = menu.exec(event.screenPos())
        if action == center_act:
            cx = (STAGE_W - CARD_W) // 2
            cy = (STAGE_H - CARD_H) // 2
            self.setPos(cx, cy)


class QtStage(QGraphicsView):
    """Interactive Qt Virtual Stage."""

    window_selected = Signal(str)  # win_id
    window_moved    = Signal(str, int, int)  # win_id, x, y

    def __init__(self, parent=None):
        super().__init__(parent)
        self.scene = QGraphicsScene(0, 0, STAGE_W, STAGE_H, self)
        self.setScene(self.scene)

        self.setRenderHint(QPainter.RenderHint.Antialiasing)
        self.setViewportUpdateMode(QGraphicsView.ViewportUpdateMode.FullViewportUpdate)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet("background: transparent; border: none;")
        self.viewport().setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._animation: Optional["Animation"] = None
        self._keyframe: Optional["Keyframe"] = None
        self._items_map: Dict[str, WindowCardItem] = {}

        self.setBackgroundBrush(QBrush(QColor(0, 0, 0, 0)))
        self._draw_stage_background()

    def _draw_stage_background(self):
        # Outer Solid Mask (covers everything outside 1920x1080 virtual screen with solid dark color)
        outer_path = QPainterPath()
        outer_path.addRect(-5000, -5000, 12000, 12000)
        outer_path.addRect(0, 0, STAGE_W, STAGE_H)

        outer_bg = QGraphicsPathItem(outer_path)
        outer_bg.setPen(Qt.PenStyle.NoPen)
        outer_bg.setBrush(QBrush(QColor("#070a13")))
        outer_bg.setZValue(-102)
        self.scene.addItem(outer_bg)

        # Virtual Display Boundary (Inner 1920x1080 blurred glass area)
        border_item = QGraphicsRectItem(0, 0, STAGE_W, STAGE_H)
        border_item.setPen(QPen(QColor("#38bdf8"), 2, Qt.PenStyle.DashLine))
        border_item.setBrush(QBrush(QColor(15, 23, 42, 40)))
        border_item.setZValue(-100)
        self.scene.addItem(border_item)

        # Label
        text_item = QGraphicsTextItem(f"Virtual Screen Resolution: {STAGE_W} x {STAGE_H} px")
        text_item.setDefaultTextColor(QColor("#475569"))
        text_item.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        text_item.setPos(20, 20)
        text_item.setZValue(-99)
        self.scene.addItem(text_item)

    def load(self, animation: "Animation", keyframe: Optional["Keyframe"]):
        self._animation = animation
        self._keyframe = keyframe
        self.refresh()

    def set_keyframe(self, keyframe: Optional["Keyframe"]):
        self._keyframe = keyframe
        self.refresh()

    def refresh(self):
        # Clear card items
        for item in self._items_map.values():
            self.scene.removeItem(item)
        self._items_map.clear()

        if not self._animation or not self._keyframe:
            return

        for win in self._animation.windows:
            state = self._keyframe.get_state(win.id)
            card = WindowCardItem(win, state, self)
            self.scene.addItem(card)
            self._items_map[win.id] = card

        self.fitInView(0, 0, STAGE_W, STAGE_H, Qt.AspectRatioMode.KeepAspectRatio)

    def set_selected_window(self, win_id: Optional[str]):
        self.scene.clearSelection()
        if win_id and win_id in self._items_map:
            self._items_map[win_id].setSelected(True)

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.fitInView(0, 0, STAGE_W, STAGE_H, Qt.AspectRatioMode.KeepAspectRatio)
