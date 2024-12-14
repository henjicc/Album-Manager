from PyQt6.QtCore import QThread, pyqtSignal
from main import process_files, check_existing_files, check_dependencies, count_files
from PyQt6.QtWidgets import QApplication

class WorkerThread(QThread):
    update_current_progress = pyqtSignal(str, int)
    update_total_progress = pyqtSignal(int, int)
    finished = pyqtSignal()
    error_paths = pyqtSignal(set)
    success_paths = pyqtSignal(set)  # 新增：发送成功处理的路径

    def __init__(self, input_paths, output_folder):
        super().__init__()
        self.input_paths = input_paths
        self.output_folder = output_folder
        self.is_running = True
        self.min_size_mb = 10  # 添加默认的文件大小过滤阈值
        self.existing_files = set()

    def run(self):
        # 获取主窗口
        main_window = QApplication.activeWindow()
        
        # 检查依赖
        if not check_dependencies(main_window):
            self.finished.emit()
            return

        self.existing_files = check_existing_files(self.input_paths)
        
        # 计算总文件数并立即更新进度
        total_files = sum(count_files(path) for path in self.input_paths)
        self.update_total_progress.emit(0, total_files)
        
        error_paths = process_files(self.input_paths, self.update_current_progress, 
                                  self.update_total_progress, self.check_if_running, 
                                  self.existing_files, self.output_folder,
                                  min_size_mb=self.min_size_mb)  # 添加文件大小过滤参数
        
        if self.is_running:  # 只有在没有被终止的情况下才发送路径
            # 计算成功处理的路径
            success_paths = set(self.input_paths) - error_paths
            self.success_paths.emit(success_paths)  # 发送成功路径
            self.error_paths.emit(error_paths)  # 发送错误路径
        
        self.finished.emit()

    def stop(self):
        self.is_running = False

    def check_if_running(self):
        return self.is_running
