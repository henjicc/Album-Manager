import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton, QLabel, QFileDialog, QProgressBar, QMessageBox, QTabWidget, QGridLayout
from PyQt6.QtGui import QIcon, QDragEnterEvent, QDropEvent
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from gui_widgets import CustomListWidget, CustomLineEdit, CustomButton, CustomProgressBar, SmallButton, CustomNumberInput, CustomCheckBox, CustomSlider, AdvancedSettingsGroup, CustomComboBox
from gui_dialogs import InfoDialog
from gui_worker import WorkerThread
from main import check_existing_files

# 导入新的选项卡模块
from tab_rename import RenameTab
from tab_transcode import TranscodeTab
from tab_fix_time import FixTimeTab
from tab_organize import OrganizeTab

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CC相册整理")
        self.setAcceptDrops(True)
        self.initUI()
        self.error_paths = set()  # 添加这行来初始化 error_paths
        self.processing_terminated = False  # 添加这行来跟踪处理是否被终止
        self.success_paths = set()  # 添加这行来跟踪成功处理的路径

    def initUI(self):
        icon = QIcon('icon.png')
        self.setWindowIcon(icon)
        app = QApplication.instance()
        app.setWindowIcon(icon)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        # 创建选项卡控件
        self.tab_widget = QTabWidget()
        layout.addWidget(self.tab_widget)

        # 添加"一条龙"选项卡
        self.all_in_one_tab = QWidget()
        self.tab_widget.addTab(self.all_in_one_tab, "一条龙")
        self.setup_all_in_one_tab()

        # 添加"按日期重命名"选项卡
        self.rename_tab = RenameTab()
        self.tab_widget.addTab(self.rename_tab, "按日期重命名")

        # 添加"视频转码"选项卡
        self.transcode_tab = TranscodeTab()
        self.tab_widget.addTab(self.transcode_tab, "视频转码")

        # 添加"修复时间属性"选项卡
        self.fix_time_tab = FixTimeTab()
        self.tab_widget.addTab(self.fix_time_tab, "修复时间属性")

        # 添加"整理"选项卡
        self.organize_tab = OrganizeTab()
        self.tab_widget.addTab(self.organize_tab, "整理")

        self.resize(600, 400)

        # 在 initUI 方法中，添加以下代码来连接选项卡切换信号
        self.tab_widget.currentChanged.connect(self.clear_focus_on_tab_change)

    def setup_all_in_one_tab(self):
        layout = QVBoxLayout(self.all_in_one_tab)

        # 路径输入框和按钮
        path_layout = QHBoxLayout()
        self.path_input = CustomLineEdit()
        self.path_input.setPlaceholderText("拖放文件/文件夹到下方或点击+添加")
        path_layout.addWidget(self.path_input)

        self.add_button = SmallButton("+")
        self.add_button.clicked.connect(self.add_path)
        path_layout.addWidget(self.add_button)

        self.remove_button = SmallButton("-")
        self.remove_button.clicked.connect(self.remove_path)
        path_layout.addWidget(self.remove_button)

        self.clear_button = SmallButton("清空")
        self.clear_button.clicked.connect(self.clear_paths)
        self.clear_button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.clear_button.customContextMenuRequested.connect(self.show_info_dialog)
        path_layout.addWidget(self.clear_button)

        layout.addLayout(path_layout)

        # 路径列表
        self.path_list = CustomListWidget()
        layout.addWidget(self.path_list)

        # 合并输出文件夹设置和文件大小过滤到同一行
        output_settings_layout = QHBoxLayout()
        
        # 输出文件夹设置
        output_label = QLabel("输出文件夹：")
        self.output_folder_input = CustomLineEdit()
        self.output_folder_input.setText("H264")
        self.output_folder_input.setPlaceholderText("输入输出文件夹名称")
        output_settings_layout.addWidget(output_label)
        output_settings_layout.addWidget(self.output_folder_input)
        
        # 添加一些间距
        output_settings_layout.addSpacing(20)
        
        # 文件大小过滤设置
        size_filter_label = QLabel("跳过小于：")
        self.size_filter_input = CustomNumberInput()
        size_filter_unit = QLabel("MB 的视频文件")
        output_settings_layout.addWidget(size_filter_label)
        output_settings_layout.addWidget(self.size_filter_input)
        output_settings_layout.addWidget(size_filter_unit)
        
        # 添加弹性空间
        output_settings_layout.addStretch()
        
        layout.addLayout(output_settings_layout)

        # 创建高级设置组
        self.advanced_group = AdvancedSettingsGroup()
        advanced_layout = QGridLayout()
        self.advanced_group.setLayout(advanced_layout)

        # 编码速度设置
        preset_label = QLabel("编码速度：")
        self.preset_combo = CustomComboBox()
        self.preset_combo.addItems(["ultrafast", "superfast", "veryfast", "faster", 
                                   "fast", "medium", "slow", "slower", "veryslow"])
        self.preset_combo.setCurrentText("veryslow")
        advanced_layout.addWidget(preset_label, 0, 0)
        advanced_layout.addWidget(self.preset_combo, 0, 1)

        # 视频质量设置
        crf_label = QLabel("视频质量(CRF)：")
        self.crf_slider = CustomSlider(Qt.Orientation.Horizontal)
        self.crf_slider.setRange(0, 51)
        self.crf_slider.setValue(21)
        self.crf_value_label = QLabel("21")
        self.crf_slider.valueChanged.connect(lambda v: self.crf_value_label.setText(str(v)))
        advanced_layout.addWidget(crf_label, 1, 0)
        advanced_layout.addWidget(self.crf_slider, 1, 1)
        advanced_layout.addWidget(self.crf_value_label, 1, 2)

        # GOP设置
        gop_label = QLabel("关键帧间隔：")
        self.gop_input = CustomNumberInput()
        self.gop_input.setText("120")
        advanced_layout.addWidget(gop_label, 2, 0)
        advanced_layout.addWidget(self.gop_input, 2, 1)

        # 场景切换阈值设置
        sc_label = QLabel("场景切换阈值：")
        self.sc_input = CustomNumberInput()
        self.sc_input.setText("60")
        advanced_layout.addWidget(sc_label, 3, 0)
        advanced_layout.addWidget(self.sc_input, 3, 1)

        # 音频码率设置
        audio_label = QLabel("音频码率：")
        self.audio_combo = CustomComboBox()
        self.audio_combo.addItems(["128k", "192k", "256k", "320k"])
        self.audio_combo.setCurrentText("256k")
        advanced_layout.addWidget(audio_label, 4, 0)
        advanced_layout.addWidget(self.audio_combo, 4, 1)

        layout.addWidget(self.advanced_group)

        # 开始和终止按钮
        button_layout = QHBoxLayout()
        self.start_button = CustomButton("开始", is_primary=True)
        self.start_button.clicked.connect(self.start_processing)
        button_layout.addWidget(self.start_button)

        self.stop_button = CustomButton("终止", is_primary=False)
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_processing)
        button_layout.addWidget(self.stop_button)

        layout.addLayout(button_layout)

        # 进度条
        self.current_file_label = QLabel("当前文件：")
        layout.addWidget(self.current_file_label)
        self.current_progress = CustomProgressBar()
        self.current_progress.setValue(0)  # 初始化为0%
        layout.addWidget(self.current_progress)

        self.total_progress_label = QLabel("总进度：0/0")
        layout.addWidget(self.total_progress_label)
        self.total_progress = CustomProgressBar()
        self.total_progress.setValue(0)  # 初始化为0%
        layout.addWidget(self.total_progress)

    def show_info_dialog(self):
        info_dialog = InfoDialog(self)
        info_dialog.show()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        current_tab = self.tab_widget.currentWidget()
        for url in event.mimeData().urls():
            if isinstance(current_tab, (RenameTab, TranscodeTab, FixTimeTab, OrganizeTab)):
                current_tab.add_path_to_list(url.toLocalFile())
            elif current_tab == self.all_in_one_tab:
                self.add_path_to_list(url.toLocalFile())

    def add_path(self):
        if self.path_input.text():
            self.add_path_to_list(self.path_input.text())
            self.path_input.clear()
        else:
            path = QFileDialog.getExistingDirectory(self, "选择文件夹")
            if path:
                self.add_path_to_list(path)

    def add_path_to_list(self, path):
        if path not in [self.path_list.item(i).text() for i in range(self.path_list.count())]:
            self.path_list.addItem(path)

    def remove_path(self):
        selected_items = self.path_list.selectedItems()
        if selected_items:
            for item in selected_items:
                self.path_list.takeItem(self.path_list.row(item))

    def clear_paths(self):
        self.path_list.clear()
        self.reset_progress()  # 添加这行来重置进度条

    def reset_progress(self):
        self.current_file_label.setText("当前文件：")
        self.current_progress.setValue(0)
        self.total_progress_label.setText("总进度：0/0")
        self.total_progress.setValue(0)

    def start_processing(self):
        paths = [self.path_list.item(i).text() for i in range(self.path_list.count())]
        if not paths:
            return

        output_folder = self.output_folder_input.text()
        if not output_folder:
            output_folder = "H264"

        min_size_mb = float(self.size_filter_input.text())  # 获取文件大小过滤阈值

        self.reset_progress()  # 添加这行来重置进度条

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.add_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.path_input.setEnabled(False)

        self.success_paths = set()  # 重置成功路径
        self.error_paths = set()  # 重置错误路径
        self.worker = WorkerThread(paths, output_folder)
        self.worker.min_size_mb = min_size_mb  # 添加文件大小过滤阈值
        self.worker.update_current_progress.connect(self.update_current_progress)
        self.worker.update_total_progress.connect(self.update_total_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error_paths.connect(self.update_error_paths)
        self.worker.success_paths.connect(self.update_success_paths)

        # 获取编码参数
        preset = self.preset_combo.currentText()
        crf = str(self.crf_slider.value())
        gop = self.gop_input.text()
        sc_threshold = self.sc_input.text()
        audio_bitrate = self.audio_combo.currentText()

        # 添加编码参数
        self.worker.preset = preset
        self.worker.crf = crf
        self.worker.gop = gop
        self.worker.sc_threshold = sc_threshold
        self.worker.audio_bitrate = audio_bitrate

        self.worker.start()

        self.processing_terminated = False  # 重置终止标志

    def stop_processing(self):
        if hasattr(self, 'worker'):
            self.processing_terminated = True  # 设置标志表示处理被终止
            self.worker.stop()
            self.worker.wait()
            self.processing_finished()
            QMessageBox.information(self, "已终止", "处理已被终止")

    def processing_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.add_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.path_input.setEnabled(True)

        if not self.processing_terminated:  # 只有在处理没有被终止的情况下才显示这些消息
            if self.error_paths:
                error_message = "\n".join(self.error_paths)
                QMessageBox.warning(self, "处理完成", f"部分文件未被正确处理，请留意 ERROR 文件夹:\n{error_message}", QMessageBox.StandardButton.Ok)
            elif self.worker.is_running:  # 添加这个条件，确保只有在正常完成时才显示成功消息
                QMessageBox.information(self, "处理完成", "所有文件处理已完成！", QMessageBox.StandardButton.Ok)

        self.processing_terminated = False  # 重置终止标志
        self.error_paths.clear()  # 清空错误路径列表

    def update_current_progress(self, file_name, progress):
        self.current_file_label.setText(f"当前文件：{file_name}")
        self.current_progress.setValue(progress)

    def update_total_progress(self, processed, total):
        self.total_progress_label.setText(f"总进度：{processed}/{total}")
        self.total_progress.setValue(int(processed / total * 100))

    def update_error_paths(self, error_paths):
        if not self.processing_terminated:  # 只有在处理没有被终止时才更新
            self.error_paths = error_paths
            # 移除所有成功处理的路径
            for i in range(self.path_list.count() - 1, -1, -1):
                path = self.path_list.item(i).text()
                # 如果路径不在错误路径集合中，说明处理成功，移除它
                if path not in error_paths:
                    self.path_list.takeItem(i)

    def update_success_paths(self, success_paths):
        if not self.processing_terminated:
            self.success_paths = success_paths
            self.update_path_list()

    def update_path_list(self):
        # 移除所有成功处理的路径
        for i in range(self.path_list.count() - 1, -1, -1):
            path = self.path_list.item(i).text()
            if path in self.success_paths:
                self.path_list.takeItem(i)

    def clear_focus_on_tab_change(self, index):
        # 获取当前选中的选项卡
        current_tab = self.tab_widget.widget(index)
        
        # 清除当前选项卡中所有 CustomLineEdit 的焦点
        for child in current_tab.findChildren(CustomLineEdit):
            child.clearFocus()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
