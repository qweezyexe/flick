"""Иконки, нарисованные QPainter'ом."""

import math

from PySide6.QtGui import (
    QPainter, QPixmap, QIcon, QColor, QPen, QPainterPath,
    QLinearGradient, QRadialGradient, QBrush, QFont,
)
from PySide6.QtCore import Qt, QPointF, QRectF

from theme import ACCENT, TEXT


def _draw_icon(p: QPainter, kind: str, color: QColor):
    stroke = 2.0
    p.setPen(QPen(color, stroke, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
    p.setBrush(Qt.NoBrush)

    if kind == "select":
        path = QPainterPath()
        path.moveTo(5, 3)
        path.lineTo(5, 19.5)
        path.lineTo(9.3, 14.8)
        path.lineTo(12.8, 21)
        path.lineTo(15.7, 19.6)
        path.lineTo(12.2, 13.4)
        path.lineTo(18.5, 13.4)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawPath(path)

    elif kind == "pen":
        body = QPainterPath()
        body.moveTo(3.5, 20.5)
        body.lineTo(4.5, 15.5)
        body.lineTo(15.5, 4.5)
        body.lineTo(19.5, 8.5)
        body.lineTo(8.5, 19.5)
        body.closeSubpath()
        p.drawPath(body)
        p.drawLine(QPointF(13.5, 6.5), QPointF(17.5, 10.5))

    elif kind == "marker":
        p.setPen(QPen(color, 4.2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(QPointF(6.5, 17.5), QPointF(17.5, 6.5))

    elif kind == "highlighter":
        p.setPen(QPen(color, 6.5, Qt.SolidLine, Qt.FlatCap))
        p.drawLine(QPointF(5, 17), QPointF(19, 7))

    elif kind == "neon":
        path = QPainterPath()
        path.moveTo(12, 3)
        path.quadTo(12.5, 11.5, 21, 12)
        path.quadTo(12.5, 12.5, 12, 21)
        path.quadTo(11.5, 12.5, 3, 12)
        path.quadTo(11.5, 11.5, 12, 3)
        path.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawPath(path)

    elif kind == "rect":
        p.drawRoundedRect(QRectF(4, 5, 16, 14), 2.5, 2.5)

    elif kind == "arrow":
        p.drawLine(QPointF(5, 19), QPointF(19, 5))
        head = QPainterPath()
        head.moveTo(19, 5)
        head.lineTo(11.5, 5.5)
        head.lineTo(18.5, 12.5)
        head.closeSubpath()
        p.setPen(Qt.NoPen)
        p.setBrush(color)
        p.drawPath(head)

    elif kind == "text":
        p.setPen(QPen(color, 2.4, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.drawLine(QPointF(5, 6.5), QPointF(19, 6.5))
        p.drawLine(QPointF(12, 6.5), QPointF(12, 19))

    elif kind == "number":
        p.setPen(QPen(color, 1.9, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(QPointF(12, 12), 8.5, 8.5)
        p.drawLine(QPointF(10, 10), QPointF(12.2, 8))
        p.drawLine(QPointF(12.2, 8), QPointF(12.2, 16))
        p.drawLine(QPointF(9, 16), QPointF(15.5, 16))

    elif kind == "copy":
        p.drawRoundedRect(QRectF(4, 4, 12, 12), 1.8, 1.8)
        p.drawRoundedRect(QRectF(8.5, 8.5, 12, 12), 1.8, 1.8)

    elif kind == "save":
        path = QPainterPath()
        path.moveTo(5, 4)
        path.lineTo(16, 4)
        path.lineTo(20, 8)
        path.lineTo(20, 20)
        path.lineTo(4, 20)
        path.lineTo(4, 5)
        path.closeSubpath()
        p.drawPath(path)
        p.drawRect(QRectF(7.5, 13, 9, 7))
        p.drawRect(QRectF(8.5, 4, 7, 5))

    elif kind == "folder":
        path = QPainterPath()
        path.moveTo(3, 6)
        path.lineTo(10, 6)
        path.lineTo(12, 9)
        path.lineTo(21, 9)
        path.lineTo(21, 19)
        path.lineTo(3, 19)
        path.closeSubpath()
        p.drawPath(path)

    elif kind == "link":
        p.setPen(QPen(color, 2.0, Qt.SolidLine, Qt.RoundCap))
        p.drawArc(QRectF(2.5, 8, 11, 8), 90 * 16, 180 * 16)
        p.drawArc(QRectF(10.5, 8, 11, 8), -90 * 16, 180 * 16)
        p.drawLine(QPointF(9.5, 12), QPointF(14.5, 12))

    elif kind == "settings":
        p.drawEllipse(QPointF(12, 12), 3.2, 3.2)
        p.setPen(QPen(color, 2.2, Qt.SolidLine, Qt.RoundCap))
        for i in range(8):
            a = i * math.pi / 4
            x1 = 12 + math.cos(a) * 6
            y1 = 12 + math.sin(a) * 6
            x2 = 12 + math.cos(a) * 8.8
            y2 = 12 + math.sin(a) * 8.8
            p.drawLine(QPointF(x1, y1), QPointF(x2, y2))


def _logo_pixmap(size: int) -> QPixmap:
    dpr = 2
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.setRenderHint(QPainter.TextAntialiasing)

    s = float(size)
    cx = cy = s / 2.0
    r = s / 2.0 - s * 0.03

    grad = QLinearGradient(0, 0, s, s)
    grad.setColorAt(0.0, QColor("#c084fc"))
    grad.setColorAt(0.45, QColor("#a855f7"))
    grad.setColorAt(1.0, QColor("#6d28d9"))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(grad))
    p.drawEllipse(QPointF(cx, cy), r, r)

    gloss = QRadialGradient(QPointF(cx, cy - r * 0.45),
                            r * 1.25,
                            QPointF(cx, cy - r * 0.45))
    gloss.setColorAt(0.0, QColor(255, 255, 255, 90))
    gloss.setColorAt(0.55, QColor(255, 255, 255, 0))
    gloss.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setBrush(QBrush(gloss))
    p.drawEllipse(QPointF(cx, cy), r, r)

    p.setBrush(Qt.NoBrush)
    p.setPen(QPen(QColor(255, 255, 255, 55), max(1.0, s * 0.02)))
    p.drawEllipse(QPointF(cx, cy), r - s * 0.015, r - s * 0.015)

    f = QFont()
    f.setBold(True)
    f.setPixelSize(int(size * 0.62))
    f.setFamily("Segoe UI")
    f.setStyleHint(QFont.SansSerif)
    p.setFont(f)
    p.setPen(QColor("#ffffff"))
    p.drawText(QRectF(0, 0, s, s), Qt.AlignCenter, "F")

    spark_cx = s * 0.78
    spark_cy = s * 0.22
    spark_r = s * 0.12
    spark_path = QPainterPath()
    spark_path.moveTo(spark_cx, spark_cy - spark_r)
    spark_path.quadTo(spark_cx + spark_r * 0.18, spark_cy - spark_r * 0.18,
                      spark_cx + spark_r, spark_cy)
    spark_path.quadTo(spark_cx + spark_r * 0.18, spark_cy + spark_r * 0.18,
                      spark_cx, spark_cy + spark_r)
    spark_path.quadTo(spark_cx - spark_r * 0.18, spark_cy + spark_r * 0.18,
                      spark_cx - spark_r, spark_cy)
    spark_path.quadTo(spark_cx - spark_r * 0.18, spark_cy - spark_r * 0.18,
                      spark_cx, spark_cy - spark_r)
    spark_path.closeSubpath()

    spark_glow = QRadialGradient(QPointF(spark_cx, spark_cy),
                                 spark_r * 2.2,
                                 QPointF(spark_cx, spark_cy))
    spark_glow.setColorAt(0.0, QColor(255, 255, 255, 130))
    spark_glow.setColorAt(1.0, QColor(255, 255, 255, 0))
    p.setPen(Qt.NoPen)
    p.setBrush(QBrush(spark_glow))
    p.drawEllipse(QPointF(spark_cx, spark_cy),
                  spark_r * 2.2, spark_r * 2.2)

    p.setBrush(QColor("#ffffff"))
    p.drawPath(spark_path)

    p.end()
    return pm


def make_icon(kind: str, color: str = TEXT, size: int = 22) -> QIcon:
    if kind == "logo":
        return QIcon(_logo_pixmap(size))
    dpr = 2
    px = int(size * dpr)
    pm = QPixmap(px, px)
    pm.setDevicePixelRatio(dpr)
    pm.fill(Qt.transparent)
    p = QPainter(pm)
    p.setRenderHint(QPainter.Antialiasing)
    p.scale(size / 24.0, size / 24.0)
    _draw_icon(p, kind, QColor(color))
    p.end()
    return QIcon(pm)


def app_icon() -> QIcon:
    return make_icon("logo", ACCENT, 32)
