from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from gui_widgets import CustomListWidget, CustomLineEdit, CustomButton, CustomProgressBar, SmallButton
from file_utils import is_video, is_photo
import os
import re
import shutil

class OrganizeWorker(QThread):
    update_total = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, paths):
        super().__init__()
        self.paths = paths
        self.is_running = True
        self.total_files = self.count_files()

    def count_files(self):
        total = 0
        for path in self.paths:
            if os.path.isfile(path):
                if is_video(path) or is_photo(path):
                    total += 1
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    total += sum(1 for file in files if is_video(file) or is_photo(file))
        return total

    def is_valid_filename(self, filename):
        pattern = r'^\d{4}_\d{2}_\d{2} \d{2}_\d{2}_\d{2}'
        return bool(re.match(pattern, filename))

    def organize_file(self, file_path):
        filename = os.path.basename(file_path)
        if not self.is_valid_filename(filename):
            self.error.emit(f"文件名格式错误: {filename}")
            return False

        # 从文件名中提取年份和月份
        year = filename[:4]
        month = filename[5:7]
        
        # 在原始文件所在目录创建年份和月份文件夹
        base_dir = os.path.dirname(file_path)
        year_dir = os.path.join(base_dir, year)
        month_dir = os.path.join(year_dir, f"{year}-{month}")

        try:
            # 创建文件夹
            os.makedirs(month_dir, exist_ok=True)
            
            # 移动文件
            new_path = os.path.join(month_dir, filename)
            if os.path.exists(new_path):
                self.error.emit(f"目标位置已存在同名文件: {filename}")
                return False
                
            shutil.move(file_path, new_path)
            return True
        except Exception as e:
            self.error.emit(f"移动文件失败 {filename}: {str(e)}")
            return False

    def run(self):
        self.update_total.emit(0, self.total_files)
        processed_files = 0

        for path in self.paths:
            if not self.is_running:
                break
            if os.path.isfile(path):
                if is_video(path) or is_photo(path):
                    if self.organize_file(path):
                        processed_files += 1
                        self.update_total.emit(processed_files, self.total_files)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if not self.is_running:
                            return
                        if is_video(file) or is_photo(file):
                            file_path = os.path.join(root, file)
                            if self.organize_file(file_path):
                                processed_files += 1
                                self.update_total.emit(processed_files, self.total_files)

        self.finished.emit()

    def stop(self):
        self.is_running = False

class OrganizeTab(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()
        self.error_files = []

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
        self.reset_progress()

    def reset_progress(self):
        self.total_progress_label.setText("总进度：0/0")
        self.total_progress.setValue(0)

    def start_processing(self):
        paths = [self.path_list.item(i).text() for i in range(self.path_list.count())]
        if not paths:
            return

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.add_button.setEnabled(False)
        self.remove_button.setEnabled(False)
        self.clear_button.setEnabled(False)
        self.path_input.setEnabled(False)

        self.error_files = []
        self.worker = OrganizeWorker(paths)
        self.worker.update_total.connect(self.update_total_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.add_error_file)
        self.worker.start()

    def stop_processing(self):
        if hasattr(self, 'worker'):
            self.worker.stop()
            self.worker.wait()
            self.processing_finished()

    def add_error_file(self, error_message):
        self.error_files.append(error_message)

    def processing_finished(self):
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.add_button.setEnabled(True)
        self.remove_button.setEnabled(True)
        self.clear_button.setEnabled(True)
        self.path_input.setEnabled(True)

        if self.error_files:
            error_message = "\n".join(self.error_files)
            QMessageBox.warning(self, "处理完成", f"部分文件整理失败:\n{error_message}", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "处理完成", "所有文件整理成功！", QMessageBox.StandardButton.Ok)

        self.path_list.clear()

    def update_total_progress(self, processed, total):
        self.total_progress_label.setText(f"总进度：{processed}/{total}")
        if total > 0:
            self.total_progress.setValue(int(processed / total * 100))
        else:
            self.total_progress.setValue(0)
