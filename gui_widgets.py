from PyQt6.QtWidgets import QListWidget, QLineEdit, QPushButton, QProgressBar, QAbstractItemView, QComboBox, QStyledItemDelegate
from PyQt6.QtGui import QPalette, QColor, QIcon, QPainter, QPixmap
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtSvg import QSvgRenderer
from PyQt6.QtGui import QIntValidator

class StyleParameters:
    # 通用样式
    BORDER_RADIUS = "4px"
    BORDER_WIDTH = "1px"
    FONT_SIZE = "16px"

    # 颜色
    PRIMARY_COLOR = "#4CAF50"
    SECONDARY_COLOR = "#f44336"
    BORDER_COLOR = "#c0c0c0"
    HOVER_COLOR = "#e0e0e0"
    PRESSED_COLOR = "#d0d0d0"
    DISABLED_COLOR = "#cccccc"
    TEXT_COLOR = "white"
    BACKGROUND_COLOR = "white"

    # 路径输入框和小按钮（+、-、清空）样式
    INPUT_GROUP = {
        "PADDING": "5px",
        "BUTTON_WIDTH": "30px",  # 确保+、-、清空按钮宽度相同
    }

    # 路径列表样式
    LIST_GROUP = {
        "ITEM_PADDING": "3px",
        "ITEM_BORDER_COLOR": "#e0e0e0",
    }

    # 开始和终止按钮样式
    MAIN_BUTTON_GROUP = {
        "PADDING": "10px 24px",
        "MARGIN": "4px 2px",
    }

    # 进度条样式
    PROGRESS_GROUP = {
        "HEIGHT": "20px",
        "BACKGROUND_COLOR": "#F0F0F0",  # 进度条背景色
        "CHUNK_COLOR": "#4CAF50",  # 进度条填充色
        "BORDER_RADIUS": "4px",  # 进度条边框圆角
        "CHUNK_RADIUS": "4px",  # 进度条填充圆角
    }

    # 新增颜色定义
    INPUT_BORDER_COLOR = "#d0d0d0"  # 浅灰色，��于未选中状态
    INPUT_FOCUS_COLOR = "#4CAF50"  # 绿色，用于选中状态

# 自定义列表控件
class CustomListWidget(QListWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
        QListWidget {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.BORDER_COLOR};
            border-radius: {StyleParameters.BORDER_RADIUS};
            background-color: {StyleParameters.BACKGROUND_COLOR};
        }}
        QListWidget::item {{
            border-bottom: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.LIST_GROUP['ITEM_BORDER_COLOR']};
            padding: {StyleParameters.LIST_GROUP['ITEM_PADDING']};
        }}
        QListWidget::item:selected {{
            background-color: {StyleParameters.HOVER_COLOR};
            color: black;
        }}
        QListWidget::item:focus {{
            outline: none;
        }}
        QListWidget {{
            outline: 0;
        }}
        """)
        
        # 设置选择模式为扩展选择（允许Ctrl和Shift多选）
        self.setSelectionMode(QAbstractItemView.SelectionMode.ExtendedSelection)

# 自定义输入框控件
class CustomLineEdit(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
        QLineEdit {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.INPUT_BORDER_COLOR};
            border-radius: {StyleParameters.BORDER_RADIUS};
            padding: {StyleParameters.INPUT_GROUP['PADDING']};
            background-color: {StyleParameters.BACKGROUND_COLOR};
            selection-background-color: {StyleParameters.PRIMARY_COLOR};
            selection-color: {StyleParameters.TEXT_COLOR};
        }}
        QLineEdit:focus {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.INPUT_FOCUS_COLOR};
        }}
        """)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)  # 确保只有在点击时才获得焦点

# 自定义数字输入框控件
class CustomNumberInput(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
        QLineEdit {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.INPUT_BORDER_COLOR};
            border-radius: {StyleParameters.BORDER_RADIUS};
            padding: {StyleParameters.INPUT_GROUP['PADDING']};
            background-color: {StyleParameters.BACKGROUND_COLOR};
            selection-background-color: {StyleParameters.PRIMARY_COLOR};
            selection-color: {StyleParameters.TEXT_COLOR};
        }}
        QLineEdit:focus {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.INPUT_FOCUS_COLOR};
        }}
        """)
        self.setValidator(QIntValidator(1, 999999))  # 限制只能输入数字
        self.setText("10")  # 默认值为10
        self.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.setFixedWidth(60)  # 设置固定宽度
        self.setFixedHeight(30)  # 设置固定高度，与其他输入框一致

# 自定义按钮控件（开始和终止按钮）
class CustomButton(QPushButton):
    def __init__(self, text, is_primary=True, parent=None):
        super().__init__(text, parent)
        color = StyleParameters.PRIMARY_COLOR if is_primary else StyleParameters.SECONDARY_COLOR
        hover_color = self.adjust_color(color, 20)
        pressed_color = self.adjust_color(color, -20)
        
        self.setStyleSheet(f"""
        QPushButton {{
            background-color: {color};
            border: none;
            color: {StyleParameters.TEXT_COLOR};
            padding: {StyleParameters.MAIN_BUTTON_GROUP['PADDING']};
            text-align: center;
            text-decoration: none;
            font-size: {StyleParameters.FONT_SIZE};
            margin: {StyleParameters.MAIN_BUTTON_GROUP['MARGIN']};
            border-radius: {StyleParameters.BORDER_RADIUS};
        }}
        QPushButton:hover {{
            background-color: {hover_color};
        }}
        QPushButton:pressed {{
            background-color: {pressed_color};
        }}
        QPushButton:disabled {{
            background-color: {StyleParameters.DISABLED_COLOR};
        }}
        """)

    @staticmethod
    def adjust_color(color, amount):
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        r = max(0, min(255, r + amount))
        g = max(0, min(255, g + amount))
        b = max(0, min(255, b + amount))
        return f"#{r:02x}{g:02x}{b:02x}"

# 自定义进度条控件
class CustomProgressBar(QProgressBar):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
        QProgressBar {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.BORDER_COLOR};
            border-radius: {StyleParameters.PROGRESS_GROUP['BORDER_RADIUS']};
            background-color: {StyleParameters.PROGRESS_GROUP['BACKGROUND_COLOR']};
            text-align: center;
            height: {StyleParameters.PROGRESS_GROUP['HEIGHT']};
        }}
        QProgressBar::chunk {{
            background-color: {StyleParameters.PROGRESS_GROUP['CHUNK_COLOR']};
            border-radius: {StyleParameters.PROGRESS_GROUP['CHUNK_RADIUS']};
        }}
        """)
        self.setTextVisible(False)

# 自定义小按钮控件（用于+、-、清空按钮）
class SmallButton(QPushButton):
    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
        QPushButton {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.BORDER_COLOR};
            border-radius: {StyleParameters.BORDER_RADIUS};
            padding: {StyleParameters.INPUT_GROUP['PADDING']};
            background-color: {StyleParameters.HOVER_COLOR};
            width: {StyleParameters.INPUT_GROUP['BUTTON_WIDTH']};
        }}
        QPushButton:hover {{
            background-color: {StyleParameters.PRESSED_COLOR};
        }}
        QPushButton:pressed {{
            background-color: {StyleParameters.BORDER_COLOR};
        }}
        """)

class CustomComboBox(QComboBox):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet(f"""
        QComboBox {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.BORDER_COLOR};
            border-radius: {StyleParameters.BORDER_RADIUS};
            padding: 5px;
            background-color: {StyleParameters.BACKGROUND_COLOR};
            color: black;
            font-size: {StyleParameters.FONT_SIZE};
        }}
        QComboBox:focus, QComboBox:on {{ /* 'on' state when the popup is open */
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.INPUT_FOCUS_COLOR};
        }}
        QComboBox::drop-down {{
            subcontrol-origin: padding;
            subcontrol-position: top right;
            width: 25px;
            border-left-width: 0px;
            border-top-right-radius: {StyleParameters.BORDER_RADIUS};
            border-bottom-right-radius: {StyleParameters.BORDER_RADIUS};
        }}
        QComboBox QAbstractItemView {{
            border: {StyleParameters.BORDER_WIDTH} solid {StyleParameters.INPUT_FOCUS_COLOR};
            background-color: {StyleParameters.BACKGROUND_COLOR};
            selection-background-color: {StyleParameters.PRIMARY_COLOR};
        }}
        QComboBox QAbstractItemView::item {{
            padding: 5px;
            border: none;
        }}
        QComboBox QAbstractItemView::item:selected {{
            background-color: {StyleParameters.PRIMARY_COLOR};
            color: {StyleParameters.TEXT_COLOR};
        }}
        QComboBox QAbstractItemView::item:hover {{
            background-color: {StyleParameters.PRIMARY_COLOR};
            color: {StyleParameters.TEXT_COLOR};
        }}
        QComboBox QAbstractItemView::item:focus {{
            border: none;
            outline: none;
        }}
        QComboBox QAbstractItemView {{
            outline: 0px;
        }}
        QComboBox QAbstractItemView::item {{
            outline: 0px;
        }}
        """)
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        
    def wheelEvent(self, event):
        # 禁用鼠标滚轮事件
        event.ignore()
