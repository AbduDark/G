from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont, QPalette, QColor

# Define color schemes
LIGHT_THEME = {
    "primary": "#2E3440",
    "secondary": "#3B4252", 
    "accent": "#5E81AC",
    "background": "#ECEFF4",
    "surface": "#FFFFFF",
    "text": "#2E3440",
    "text_secondary": "#5E81AC",
    "success": "#A3BE8C",
    "warning": "#EBCB8B",
    "error": "#BF616A",
    "border": "#D8DEE9"
}

DARK_THEME = {
    "primary": "#ECEFF4",
    "secondary": "#D8DEE9",
    "accent": "#88C0D0", 
    "background": "#2E3440",
    "surface": "#3B4252",
    "text": "#ECEFF4",
    "text_secondary": "#88C0D0",
    "success": "#A3BE8C",
    "warning": "#EBCB8B", 
    "error": "#BF616A",
    "border": "#434C5E"
}

def get_stylesheet(theme="light"):
    """Get QSS stylesheet for the application"""
    colors = LIGHT_THEME if theme == "light" else DARK_THEME
    
    return f"""
    QMainWindow {{
        background-color: {colors["background"]};
        color: {colors["text"]};
    }}
    
    QWidget {{
        background-color: {colors["background"]};
        color: {colors["text"]};
        font-family: "Noto Sans Arabic", "Segoe UI", Arial;
    }}
    
    QPushButton {{
        background-color: {colors["accent"]};
        color: white;
        border: none;
        padding: 8px 16px;
        border-radius: 4px;
        font-weight: bold;
        min-height: 32px;
    }}
    
    QPushButton:hover {{
        background-color: {colors["text_secondary"]};
    }}
    
    QPushButton:pressed {{
        background-color: {colors["secondary"]};
    }}
    
    QPushButton:disabled {{
        background-color: {colors["border"]};
        color: {colors["text_secondary"]};
    }}
    
    QLineEdit, QTextEdit, QPlainTextEdit {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        padding: 8px;
        border-radius: 4px;
        font-size: 11px;
    }}
    
    QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {{
        border: 2px solid {colors["accent"]};
    }}
    
    QComboBox {{
        background-color: {colors["surface"]};
        border: 1px solid {colors["border"]};
        padding: 8px;
        border-radius: 4px;
        min-height: 20px;
    }}
    
    QComboBox::drop-down {{
        border: none;
        width: 20px;
    }}
    
    QComboBox::down-arrow {{
        image: none;
        border-left: 5px solid transparent;
        border-right: 5px solid transparent;
        border-top: 5px solid {colors["text"]};
    }}
    
    QTableWidget {{
        background-color: {colors["surface"]};
        alternate-background-color: {colors["background"]};
        gridline-color: {colors["border"]};
        border: 1px solid {colors["border"]};
    }}
    
    QTableWidget::item {{
        padding: 8px;
        border-bottom: 1px solid {colors["border"]};
    }}
    
    QTableWidget::item:selected {{
        background-color: {colors["accent"]};
        color: white;
    }}
    
    QHeaderView::section {{
        background-color: {colors["secondary"]};
        color: {colors["text"]};
        padding: 8px;
        border: 1px solid {colors["border"]};
        font-weight: bold;
    }}
    
    QMenuBar {{
        background-color: {colors["surface"]};
        color: {colors["text"]};
        border-bottom: 1px solid {colors["border"]};
    }}
    
    QMenuBar::item {{
        padding: 8px 16px;
    }}
    
    QMenuBar::item:selected {{
        background-color: {colors["accent"]};
        color: white;
    }}
    
    QMenu {{
        background-color: {colors["surface"]};
        color: {colors["text"]};
        border: 1px solid {colors["border"]};
    }}
    
    QMenu::item {{
        padding: 8px 24px;
    }}
    
    QMenu::item:selected {{
        background-color: {colors["accent"]};
        color: white;
    }}
    
    QTabWidget::pane {{
        border: 1px solid {colors["border"]};
        background-color: {colors["surface"]};
    }}
    
    QTabBar::tab {{
        background-color: {colors["background"]};
        color: {colors["text"]};
        padding: 8px 16px;
        margin-right: 2px;
    }}
    
    QTabBar::tab:selected {{
        background-color: {colors["accent"]};
        color: white;
    }}
    
    QScrollBar:vertical {{
        background-color: {colors["background"]};
        width: 12px;
        border-radius: 6px;
    }}
    
    QScrollBar::handle:vertical {{
        background-color: {colors["border"]};
        border-radius: 6px;
        min-height: 20px;
    }}
    
    QScrollBar::handle:vertical:hover {{
        background-color: {colors["accent"]};
    }}
    
    QStatusBar {{
        background-color: {colors["surface"]};
        color: {colors["text"]};
        border-top: 1px solid {colors["border"]};
    }}
    
    QGroupBox {{
        font-weight: bold;
        border: 2px solid {colors["border"]};
        border-radius: 8px;
        margin: 8px 0px;
        padding-top: 16px;
    }}
    
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top right;
        padding: 0 8px;
        background-color: {colors["background"]};
    }}
    
    QLabel {{
        color: {colors["text"]};
    }}
    
    .title-label {{
        font-size: 18px;
        font-weight: bold;
        color: {colors["accent"]};
        margin: 8px 0px;
    }}
    
    .error-label {{
        color: {colors["error"]};
        font-weight: bold;
    }}
    
    .success-label {{
        color: {colors["success"]};
        font-weight: bold;
    }}
    
    .warning-label {{
        color: {colors["warning"]};
        font-weight: bold;
    }}
    """

def setup_arabic_font(app):
    """Setup Arabic font for the application"""
    # Try to load Arabic fonts in order of preference
    fonts = ["Noto Sans Arabic", "Cairo", "Amiri", "Scheherazade"]
    
    for font_name in fonts:
        font = QFont(font_name, 10)
        if font.exactMatch():
            app.setFont(font)
            break
    else:
        # Fallback to default font with Arabic support
        font = QFont("Arial Unicode MS", 10)
        app.setFont(font)
