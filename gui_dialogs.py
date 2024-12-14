from PyQt6.QtWidgets import QDialog, QVBoxLayout, QTextBrowser, QPushButton, QHBoxLayout
from PyQt6.QtCore import Qt, QUrl
from PyQt6.QtGui import QDesktopServices

class InfoDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("关于CC相册整理")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)
        info = QTextBrowser(self)
        info.setOpenExternalLinks(True)
        info.setHtml("""
        本软件主要用于相册整理<br>
        会自动按照文件日期重命名文件<br>
        对于视频文件，会进行转码，确保小体积高画质<br>
        作者：痕继痕迹 & AI<br>
        主页：<a href="https://space.bilibili.com/39337803">https://space.bilibili.com/39337803</a>
        """)
        layout.addWidget(info)
        self.resize(300, 200)  # 设置对话框大小

    def focusOutEvent(self, event):
        self.close()

class DownloadDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("下载依赖项")
        self.setWindowFlags(Qt.WindowType.Window | Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout(self)
        
        info = QTextBrowser(self)
        info.setHtml("""
        请下载并安装以下依赖项：<br><br>
        1. FFmpeg<br>
        2. ExifTool<br><br>
        安装完成后，请重新启动程序。
        """)
        layout.addWidget(info)
        
        button_layout = QHBoxLayout()
        ffmpeg_button = QPushButton("下载 FFmpeg")
        ffmpeg_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://ffmpeg.org/download.html")))
        button_layout.addWidget(ffmpeg_button)
        
        exiftool_button = QPushButton("下载 ExifTool")
        exiftool_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl("https://exiftool.org/")))
        button_layout.addWidget(exiftool_button)
        
        layout.addLayout(button_layout)
        
        self.resize(400, 200)
