"""Отрисовка инструментов на холсте."""

import math

from PySide6.QtGui import QPainter, QPen, QColor, QFont, QFontMetrics
from PySide6.QtCore import Qt, QRect, QPoint, QSize

from state import Item, BRUSHES, PEN_KINDS, number_radius


def draw_item(p: QPainter, item: Item):
    if item.kind in PEN_KINDS:
        _draw_stroke(p, item)
    elif item.kind == "rect" and len(item.points) >= 2:
        p.setPen(QPen(QColor(item.color), item.width, Qt.SolidLine,
                      Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        p.drawRect(QRect(item.points[0], item.points[-1]).normalized())
    elif item.kind == "arrow" and len(item.points) >= 2:
        p.setPen(QPen(QColor(item.color), item.width, Qt.SolidLine,
                      Qt.RoundCap, Qt.RoundJoin))
        _draw_arrow(p, item.points[0], item.points[-1], item.width)
    elif item.kind == "text":
        _draw_text(p, item)
    elif item.kind == "number":
        _draw_number(p, item)


def _draw_stroke(p: QPainter, item: Item):
    cfg = BRUSHES.get(item.kind, BRUSHES["pen"])
    if cfg.get("glow"):
        for mult, alpha in ((3.0, 60), (2.0, 120), (1.0, 255)):
            c = QColor(item.color)
            c.setAlpha(alpha)
            p.setPen(QPen(c,
                          max(1, int(item.width * cfg["scale"] * mult)),
                          Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
            for i in range(1, len(item.points)):
                p.drawLine(item.points[i - 1], item.points[i])
    else:
        c = QColor(item.color)
        c.setAlpha(cfg["alpha"])
        cap = Qt.FlatCap if item.kind == "highlighter" else Qt.RoundCap
        w = max(1, int(item.width * cfg["scale"]))
        p.setPen(QPen(c, w, Qt.SolidLine, cap, Qt.RoundJoin))
        for i in range(1, len(item.points)):
            p.drawLine(item.points[i - 1], item.points[i])


def _draw_arrow(p: QPainter, a: QPoint, b: QPoint, width: int):
    p.drawLine(a, b)
    angle = math.atan2(b.y() - a.y(), b.x() - a.x())
    size = max(10, width * 4)
    for da in (math.radians(150), -math.radians(150)):
        x = b.x() + size * math.cos(angle + da)
        y = b.y() + size * math.sin(angle + da)
        p.drawLine(b, QPoint(int(x), int(y)))


def _draw_text(p: QPainter, item: Item):
    f = QFont()
    f.setPointSize(item.font_size)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor(item.color))
    fm = QFontMetrics(f)
    rect = QRect(item.points[0],
                 QSize(fm.horizontalAdvance(item.text), fm.height()))
    p.drawText(rect, Qt.AlignLeft | Qt.AlignTop, item.text)


def _draw_number(p: QPainter, item: Item):
    radius = number_radius(item)
    center = item.points[0]
    p.setPen(Qt.NoPen)
    p.setBrush(QColor(item.color))
    p.drawEllipse(center, radius, radius)
    f = QFont()
    f.setPointSize(item.font_size)
    f.setBold(True)
    p.setFont(f)
    p.setPen(QColor("#ffffff"))
    r = QRect(center.x() - radius, center.y() - radius,
              radius * 2, radius * 2)
    p.drawText(r, Qt.AlignCenter, item.text)
