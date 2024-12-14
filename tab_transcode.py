from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QFileDialog, QMessageBox, QComboBox
from PyQt6.QtCore import QThread, pyqtSignal
from gui_widgets import CustomListWidget, CustomLineEdit, CustomButton, CustomProgressBar, SmallButton, CustomComboBox, CustomNumberInput
from video_processing import process_video
from file_utils import is_video
from main import get_executable_path
import os
import shutil

class TranscodeWorker(QThread):
    update_progress = pyqtSignal(str, int)
    update_total = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, paths, output_folder, rotation, min_size_mb):
        super().__init__()
        self.paths = paths
        self.output_folder = output_folder
        self.rotation = rotation
        self.min_size_mb = min_size_mb
        self.is_running = True
        self.ffmpeg_path = get_executable_path('ffmpeg.exe')
        self.total_files = self.count_files()
        self.existing_files = self.get_existing_files()
        self.current_output_path = None

    def get_existing_files(self):
        existing_files = set()
        for path in self.paths:
            if os.path.isdir(path):
                output_dir = os.path.join(path, self.output_folder)
                if os.path.exists(output_dir):
                    for root, _, files in os.walk(output_dir):
                        for file in files:
                            existing_files.add(os.path.join(root, file).lower())
            elif os.path.isfile(path):
                output_dir = os.path.join(os.path.dirname(path), self.output_folder)
                if os.path.exists(output_dir):
                    output_file = os.path.join(output_dir, os.path.basename(path))
                    if os.path.exists(output_file):
                        existing_files.add(output_file.lower())
        return existing_files

    def count_files(self):
        total = 0
        for path in self.paths:
            if os.path.isfile(path):
                if is_video(path):
                    total += 1
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    total += sum(1 for file in files if is_video(file))
        return total

    def run(self):
        self.update_total.emit(0, self.total_files)
        processed_files = 0

        for path in self.paths:
            if not self.is_running:
                break
            if os.path.isfile(path):
                if is_video(path):
                    output_path = os.path.join(os.path.dirname(path), self.output_folder, os.path.basename(path))
                    if output_path.lower() not in self.existing_files:
                        self.process_file(path)
                    else:
                        print(f"跳过已存在的文件: {os.path.basename(path)}")
                    processed_files += 1
                    self.update_total.emit(processed_files, self.total_files)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if not self.is_running:
                            return
                        if is_video(file):
                            file_path = os.path.join(root, file)
                            output_path = os.path.join(os.path.dirname(file_path), self.output_folder, file)
                            if output_path.lower() not in self.existing_files:
                                self.process_file(file_path)
                            else:
                                print(f"跳过已存在的文件: {file}")
                            processed_files += 1
                            self.update_total.emit(processed_files, self.total_files)

        if self.is_running:  # 只有在没有被终止的情下才发出完成信号
            self.finished.emit()

    def process_file(self, file_path):
        output_dir = os.path.join(os.path.dirname(file_path), self.output_folder)
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, os.path.basename(file_path))
        self.current_output_path = output_path
        success = process_video(file_path, output_path, self.update_progress, lambda: self.is_running, self.ffmpeg_path, self.rotation, self.min_size_mb)
        if success is False:  # 处理失败
            self.error.emit(f"处理文件失败: {file_path}")
            self.move_to_error_folder(file_path)
        elif success is None:  # 处理被跳过或终止
            if os.path.exists(output_path):
                self.cleanup_incomplete_file(output_path)

    def cleanup_incomplete_file(self, output_path):
        if os.path.exists(output_path):
            try:
                os.remove(output_path)
                print(f"已删除未完成的输出文件: {output_path}")
            except Exception as e:
                print(f"无法删除文件 {output_path}: {e}")

    def move_to_error_folder(self, file_path):
        error_dir = os.path.join(os.path.dirname(file_path), 'ERROR')
        os.makedirs(error_dir, exist_ok=True)
        error_path = os.path.join(error_dir, os.path.basename(file_path))
        shutil.move(file_path, error_path)
        print(f"已将文件 {os.path.basename(file_path)} 移动到 ERROR 文件夹")

    def stop(self):
        self.is_running = False
        if self.current_output_path:
            self.cleanup_incomplete_file(self.current_output_path)

class TranscodeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.worker = None
        self.error_files = []
        self.processing_terminated = False
        self.processed_paths = set()  # 添加这行来跟踪已处理的路径

    def initUI(self):
        layout = QVBoxLayout(self)

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
        path_layout.addWidget(self.clear_button)

        layout.addLayout(path_layout)

        # 路径列表
        self.path_list = CustomListWidget()
        layout.addWidget(self.path_list)

        # 合并输出文件夹、视频旋转和文件大小过滤设置到同一行
        settings_layout = QHBoxLayout()
        
        # 输出文件夹设置
        output_label = QLabel("输出文件夹：")
        self.output_folder_input = CustomLineEdit()
        self.output_folder_input.setText("H264")
        self.output_folder_input.setPlaceholderText("输入输出文件夹名称")
        settings_layout.addWidget(output_label)
        settings_layout.addWidget(self.output_folder_input)
        
        # 添加一些间距
        settings_layout.addSpacing(20)
        
        # 文件大小过滤设置
        size_filter_label = QLabel("跳过小于：")
        self.size_filter_input = CustomNumberInput()
        size_filter_unit = QLabel("MB 的视频文件")
        settings_layout.addWidget(size_filter_label)
        settings_layout.addWidget(self.size_filter_input)
        settings_layout.addWidget(size_filter_unit)
        
        # 添加一些间距
        settings_layout.addSpacing(20)
        
        # 视频旋转选项
        rotation_label = QLabel("视频旋转：")
        self.rotation_combo = CustomComboBox()
        self.rotation_combo.addItems(["0", "90", "180", "270"])
        self.rotation_combo.setFixedWidth(80)
        settings_layout.addWidget(rotation_label)
        settings_layout.addWidget(self.rotation_combo)
        
        # 添加弹性空间
        settings_layout.addStretch()
        
        layout.addLayout(settings_layout)

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
        layout.addWidget(self.current_progress)

        self.total_progress_label = QLabel("总进度：0/0")
        layout.addWidget(self.total_progress_label)
        self.total_progress = CustomProgressBar()
        layout.addWidget(self.total_progress)

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
        self.reset_progress()  # 添加这行

    def reset_progress(self):
        self.current_file_label.setText("当前文件：")
        self.current_progress.setValue(0)
        self.total_progress_label.setText("总进度：0/0")
        self.total_progress.setValue(0)

    def start_processing(self):
        paths = [self.path_list.item(i).text() for i in range(self.path_list.count())]
        if not paths:
            QMessageBox.warning(self, "警告", "请先添加要处理的文件或文件夹")
            return

        output_folder = self.output_folder_input.text()
        if not output_folder:
            output_folder = "H264"

        rotation = self.rotation_combo.currentText()
        min_size_mb = float(self.size_filter_input.text())

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.add_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.path_input.setEnabled(False)
        self.rotation_combo.setEnabled(False)

        self.processing_terminated = False
        self.error_files = []
        self.processed_paths.clear()  # 清空已处理路径集合
        self.worker = TranscodeWorker(paths, output_folder, rotation, min_size_mb)
        self.worker.update_progress.connect(self.update_current_progress)
        self.worker.update_total.connect(self.update_total_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.add_error_file)
        self.worker.start()

    def add_error_file(self, error_message):
        self.error_files.append(error_message)

    def stop_processing(self):
        if self.worker and self.worker.isRunning():
            self.processing_terminated = True
            self.worker.stop()
            self.worker.wait()
            self.processing_finished()

    def processing_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.add_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.path_input.setEnabled(True)
        self.rotation_combo.setEnabled(True)

        if not self.processing_terminated:
            if self.error_files:
                error_message = "\n".join(self.error_files)
                QMessageBox.warning(self, "处理完成", f"部分视频转码失败:\n{error_message}", QMessageBox.StandardButton.Ok)
            else:
                QMessageBox.information(self, "处理完成", "所有视频转码成功！", QMessageBox.StandardButton.Ok)
            
            self.remove_processed_paths()  # 只在正常完成时移除已处理的路径
        else:
            QMessageBox.information(self, "已终止", "处理已被终止")

    def remove_processed_paths(self):
        for i in range(self.path_list.count() - 1, -1, -1):
            path = self.path_list.item(i).text()
            if path in self.processed_paths:
                self.path_list.takeItem(i)

    def update_current_progress(self, file_name, progress):
        self.current_file_label.setText(f"当前文件：{file_name}")
        self.current_progress.setValue(progress)
        if progress == 100:
            # 当文件处理完成时，将其添加到已处理路径集合中
            self.processed_paths.add(os.path.dirname(file_name))

    def update_total_progress(self, processed, total):
        self.total_progress_label.setText(f"总进度：{processed}/{total}")
        if total > 0:
            self.total_progress.setValue(int(processed / total * 100))
        else:
            self.total_progress.setValue(0)

    def show_error(self, message):
        QMessageBox.warning(self, "错误", message)
