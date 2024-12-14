from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFileDialog, QMessageBox
from PyQt6.QtCore import QThread, pyqtSignal
from gui_widgets import CustomListWidget, CustomLineEdit, CustomButton, CustomProgressBar, SmallButton
from date_utils import rename_file
from file_utils import is_video, is_photo
from main import get_executable_path  # 导入获取可执行文件路径的函数
import os
import shutil

class RenameWorker(QThread):
    update_total = pyqtSignal(int, int)
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, paths):
        super().__init__()
        self.paths = paths
        self.is_running = True
        self.exiftool_path = get_executable_path('exiftool.exe')  # 获取 exiftool 路径
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

    def run(self):
        self.update_total.emit(0, self.total_files)
        processed_files = 0

        for path in self.paths:
            if not self.is_running:
                break
            if os.path.isfile(path):
                if is_video(path) or is_photo(path):
                    self.process_file(path)
                    processed_files += 1
                    self.update_total.emit(processed_files, self.total_files)
            elif os.path.isdir(path):
                for root, _, files in os.walk(path):
                    for file in files:
                        if not self.is_running:
                            return
                        if is_video(file) or is_photo(file):
                            file_path = os.path.join(root, file)
                            self.process_file(file_path)
                            processed_files += 1
                            self.update_total.emit(processed_files, self.total_files)

        self.finished.emit()

    def process_file(self, file_path):
        new_path = rename_file(file_path, self.exiftool_path)
        if new_path is None:
            self.error.emit(f"重命名失败: {file_path}")
            self.move_to_error_folder(file_path)

    def move_to_error_folder(self, file_path):
        error_dir = os.path.join(os.path.dirname(file_path), 'ERROR')
        os.makedirs(error_dir, exist_ok=True)
        error_path = os.path.join(error_dir, os.path.basename(file_path))
        shutil.move(file_path, error_path)
        print(f"已将文件 {os.path.basename(file_path)} 移动到 ERROR 文件夹")

    def stop(self):
        self.is_running = False

class RenameTab(QWidget):
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
        self.worker = RenameWorker(paths)
        self.worker.update_total.connect(self.update_total_progress)
        self.worker.finished.connect(self.processing_finished)
        self.worker.error.connect(self.add_error_file)
        self.worker.start()

    def stop_processing(self):
        if hasattr(self, 'worker'):
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

        if self.error_files:
            error_message = "\n".join(self.error_files)
            QMessageBox.warning(self, "处理完成", f"部分文件重命名失败:\n{error_message}", QMessageBox.StandardButton.Ok)
        else:
            QMessageBox.information(self, "处理完成", "所有文件重命名成功！", QMessageBox.StandardButton.Ok)

        self.remove_successful_paths()

    def remove_successful_paths(self):
        if not self.error_files:
            self.path_list.clear()
        else:
            error_paths = {os.path.dirname(error.split(":")[1].strip()) for error in self.error_files}
            for i in range(self.path_list.count() - 1, -1, -1):
                path = self.path_list.item(i).text()
                if path not in error_paths:
                    self.path_list.takeItem(i)

    def update_total_progress(self, processed, total):
        self.total_progress_label.setText(f"总进度：{processed}/{total}")
        if total > 0:
            self.total_progress.setValue(int(processed / total * 100))
        else:
            self.total_progress.setValue(0)

    def add_error_file(self, error_message):
        self.error_files.append(error_message)
