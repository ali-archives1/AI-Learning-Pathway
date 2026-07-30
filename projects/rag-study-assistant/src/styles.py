"""Dark visual system and programmatic application icon."""

from __future__ import annotations

from PySide6.QtCore import QRectF, Qt
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontDatabase,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
)


COLORS = {
    "background": "#0B0F17",
    "surface": "#111827",
    "surface_alt": "#172033",
    "surface_hover": "#1D2940",
    "border": "#273449",
    "text": "#F4F7FB",
    "muted": "#98A6BA",
    "accent": "#6EE7D8",
    "accent_dark": "#113A3A",
    "blue": "#75A7FF",
    "danger": "#FF7D8A",
    "warning": "#F8C56C",
    "success": "#57D99A",
}


def make_app_icon(size: int = 128) -> QIcon:
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)
    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    painter.setBrush(QColor(COLORS["accent"]))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(QRectF(8, 8, size - 16, size - 16), 30, 30)

    path = QPainterPath()
    path.moveTo(32, 38)
    path.quadTo(58, 32, 64, 48)
    path.quadTo(70, 32, 96, 38)
    path.lineTo(96, 88)
    path.quadTo(72, 82, 64, 96)
    path.quadTo(56, 82, 32, 88)
    path.closeSubpath()
    painter.setBrush(QColor("#0B1D24"))
    painter.drawPath(path)

    painter.setPen(QPen(QColor(COLORS["accent"]), 4))
    painter.drawLine(64, 48, 64, 94)
    painter.end()
    return QIcon(pixmap)


def load_preferred_font() -> str:
    """Load Windows' UI font explicitly for restricted/off-screen Qt sessions."""

    windows_fonts = (
        r"C:\Windows\Fonts\segoeui.ttf",
        r"C:\Windows\Fonts\arial.ttf",
    )
    for font_path in windows_fonts:
        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id >= 0:
            families = QFontDatabase.applicationFontFamilies(font_id)
            if families:
                return families[0]
    return QFontDatabase.systemFont(QFontDatabase.SystemFont.GeneralFont).family()


APP_STYLESHEET = f"""
* {{
    color: {COLORS["text"]};
    font-family: "Segoe UI";
    font-size: 10pt;
}}
QWidget {{
    background: transparent;
}}
QMainWindow, QWidget#Root {{
    background: {COLORS["background"]};
}}
QFrame#Header {{
    background: {COLORS["surface"]};
    border-bottom: 1px solid {COLORS["border"]};
}}
QFrame#Sidebar, QFrame#Inspector {{
    background: {COLORS["surface"]};
}}
QFrame#Sidebar {{
    border-right: 1px solid {COLORS["border"]};
}}
QFrame#Inspector {{
    border-left: 1px solid {COLORS["border"]};
}}
QFrame#Card {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 12px;
}}
QFrame#UserBubble {{
    background: #1B3A55;
    border: 1px solid #285274;
    border-radius: 14px;
}}
QFrame#AssistantBubble {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 14px;
}}
QFrame#ChunkCard {{
    background: #131D2D;
    border: 1px solid {COLORS["border"]};
    border-radius: 10px;
}}
QFrame#ErrorBanner {{
    background: #3A1C26;
    border: 1px solid #7A3042;
    border-radius: 9px;
}}
QLabel#Title {{
    font-size: 16pt;
    font-weight: 700;
}}
QLabel#SectionTitle {{
    font-size: 11pt;
    font-weight: 650;
}}
QLabel#Muted, QLabel#MessageMeta {{
    color: {COLORS["muted"]};
}}
QLabel#Accent {{
    color: {COLORS["accent"]};
    font-weight: 600;
}}
QLabel#Success {{
    color: {COLORS["success"]};
}}
QLabel#Warning {{
    color: {COLORS["warning"]};
}}
QLabel#Danger {{
    color: {COLORS["danger"]};
}}
QLabel#SourcePill {{
    color: {COLORS["accent"]};
    background: {COLORS["accent_dark"]};
    border: 1px solid #245D59;
    border-radius: 8px;
    padding: 4px 8px;
}}
QPushButton {{
    background: {COLORS["surface_alt"]};
    border: 1px solid {COLORS["border"]};
    border-radius: 9px;
    min-height: 36px;
    padding: 0 14px;
    font-weight: 600;
}}
QPushButton:hover {{
    background: {COLORS["surface_hover"]};
    border-color: #40516C;
}}
QPushButton:pressed {{
    background: #101827;
}}
QPushButton:disabled {{
    color: #667287;
    background: #111827;
    border-color: #202A3B;
}}
QPushButton#PrimaryButton {{
    color: #071412;
    background: {COLORS["accent"]};
    border: none;
}}
QPushButton#PrimaryButton:hover {{
    background: #8FEFE3;
}}
QPushButton#DangerButton {{
    color: #FFABB4;
}}
QPlainTextEdit {{
    background: #0F1624;
    border: 1px solid {COLORS["border"]};
    border-radius: 11px;
    padding: 10px;
    selection-background-color: #285274;
}}
QPlainTextEdit:focus {{
    border-color: {COLORS["accent"]};
}}
QScrollArea {{
    border: none;
    background: transparent;
}}
QWidget#qt_scrollarea_viewport {{
    background: transparent;
}}
QScrollBar:vertical {{
    background: transparent;
    width: 10px;
    margin: 2px;
}}
QScrollBar::handle:vertical {{
    background: #344158;
    border-radius: 4px;
    min-height: 28px;
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}
QProgressBar {{
    background: #141D2B;
    border: 1px solid {COLORS["border"]};
    border-radius: 4px;
    height: 6px;
    text-align: center;
}}
QProgressBar::chunk {{
    background: {COLORS["accent"]};
    border-radius: 3px;
}}
QSplitter::handle {{
    background: {COLORS["border"]};
    width: 1px;
}}
QToolTip {{
    color: {COLORS["text"]};
    background: #1B2537;
    border: 1px solid {COLORS["border"]};
    padding: 6px;
}}
"""
