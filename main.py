import os
import sys
import time
import subprocess
import shutil
import re
from file_utils import is_video, is_photo, count_files, get_input_paths
from video_processing import process_video
from photo_processing import move_photo
from date_utils import rename_file, modify_file_dates
from PyQt6.QtWidgets import QMessageBox
from gui_dialogs import DownloadDialog

def get_executable_path(executable_name):
    if getattr(sys, 'frozen', False):
        # 如果是打包后的可执行文件
        base_path = sys._MEIPASS
    else:
        # 如果是直接运行的脚本
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    executable_path = os.path.join(base_path, executable_name)
    
    if os.path.exists(executable_path):
        return executable_path
    else:
        # 尝试从系统路径中查找
        try:
            subprocess.run([executable_name, "-version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return executable_name
        except FileNotFoundError:
            return None

# 在文件开头附近添加这些全局变量
FFMPEG_PATH = get_executable_path('ffmpeg.exe')
EXIFTOOL_PATH = get_executable_path('exiftool.exe')

def check_dependencies(parent_window=None):
    missing_deps = []
    if FFMPEG_PATH is None:
        missing_deps.append("FFmpeg")
    if EXIFTOOL_PATH is None:
        missing_deps.append("ExifTool")
    
    if missing_deps:
        msg = f"缺少以下依赖项：{', '.join(missing_deps)}。是否下载？"
        if parent_window:
            reply = QMessageBox.question(parent_window, '缺少依赖项', msg, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.Yes)
            
            if reply == QMessageBox.StandardButton.Yes:
                download_dialog = DownloadDialog(parent_window)
                download_dialog.exec()
        else:
            print(msg)
        return False
    return True

def check_existing_files(input_paths):
    existing_files = set()
    for input_path in input_paths:
        if os.path.isdir(input_path):
            h264_folder = os.path.join(input_path, 'H264')
            if os.path.exists(h264_folder):
                for root, _, files in os.walk(h264_folder):
                    for file in files:
                        existing_files.add(os.path.join(root, file).lower())
        elif os.path.isfile(input_path):
            h264_folder = os.path.join(os.path.dirname(input_path), 'H264')
            if os.path.exists(h264_folder):
                existing_file = os.path.join(h264_folder, os.path.basename(input_path))
                if os.path.exists(existing_file):
                    existing_files.add(existing_file.lower())
    return existing_files

def process_files(input_paths, update_current_progress, update_total_progress, check_if_running, existing_files, output_folder, min_size_mb=10):
    if not check_dependencies():
        return set()

    start_time = time.time()
    
    total_files = sum(count_files(path) for path in input_paths)
    processed_files = 0
    error_paths = set()
    processed_file_paths = []  # 新增：用于存储处理后的文件路径
    
    update_total_progress.emit(processed_files, total_files)
    
    for input_path in input_paths:
        if not check_if_running():
            break
        
        print(f"处理路径: {input_path}")
        
        if os.path.exists(input_path):
            if os.path.isfile(input_path):
                output_path = os.path.join(os.path.dirname(input_path), output_folder, os.path.basename(input_path))
                if output_path.lower() not in existing_files:
                    result = process_single_file(input_path, update_current_progress, check_if_running, output_folder, min_size_mb)
                    if result is True:  # 处理成功
                        processed_file_paths.append(output_path)  # 添加处理后的文件路径
                    elif result is False:  # 处理失败
                        error_paths.add(input_path)
                    processed_files += 1
                    update_total_progress.emit(processed_files, total_files)
                else:
                    print(f"跳过已存在的文件: {os.path.basename(input_path)}")
                    processed_files += 1
                    update_total_progress.emit(processed_files, total_files)
            elif os.path.isdir(input_path):
                for root, _, files in os.walk(input_path):
                    for file in files:
                        if not check_if_running():
                            return error_paths
                        if is_video(file) or is_photo(file):
                            file_path = os.path.join(root, file)
                            output_path = os.path.join(os.path.dirname(file_path), output_folder, file)
                            if output_path.lower() not in existing_files:
                                result = process_single_file(file_path, update_current_progress, check_if_running, output_folder, min_size_mb)
                                if result is True:  # 处理成功
                                    processed_file_paths.append(output_path)  # 添加处理后的文件路径
                                elif result is False:  # 处理失败
                                    error_paths.add(file_path)
                                processed_files += 1
                                update_total_progress.emit(processed_files, total_files)
                            else:
                                print(f"跳过已存在的文件: {file}")
                                processed_files += 1
                                update_total_progress.emit(processed_files, total_files)
            else:
                print(f"无效的输入路径: {input_path}")
                error_paths.add(input_path)
        else:
            print(f"路径不存在: {input_path}")
            error_paths.add(input_path)

    # 在所有文件处理完成后，进行文件整理
    if processed_file_paths and check_if_running():
        print("开始整理文件...")
        for file_path in processed_file_paths:
            if not check_if_running():
                break
            
            filename = os.path.basename(file_path)
            if not is_valid_filename(filename):
                print(f"文件名格式错误，跳过整理: {filename}")
                continue

            # 从文件名中提取年份和月份
            year = filename[:4]
            month = filename[5:7]
            
            # 在输出文件夹中创建年份和月份文件夹
            base_dir = os.path.dirname(file_path)
            year_dir = os.path.join(base_dir, year)
            month_dir = os.path.join(year_dir, f"{year}-{month}")

            try:
                # 创建文件夹
                os.makedirs(month_dir, exist_ok=True)
                
                # 移动文件
                new_path = os.path.join(month_dir, filename)
                if os.path.exists(new_path):
                    print(f"目标位置已存在同名文件，跳过移动: {filename}")
                    continue
                    
                shutil.move(file_path, new_path)
                print(f"已整理文件: {filename}")
            except Exception as e:
                print(f"整理文件失败 {filename}: {str(e)}")
                error_paths.add(file_path)
    
    end_time = time.time()
    total_time = end_time - start_time
    hours, rem = divmod(total_time, 3600)
    minutes, seconds = divmod(rem, 60)
    print(f"总处理时间: {int(hours):02d}:{int(minutes):02d}:{int(seconds):02d}")
    
    return error_paths

def is_valid_filename(filename):
    pattern = r'^\d{4}_\d{2}_\d{2} \d{2}_\d{2}_\d{2}'
    return bool(re.match(pattern, filename))

def process_single_file(file_path, update_current_progress, check_if_running, output_folder, min_size_mb=10):
    # 重命名文件
    new_file_path = rename_file(file_path, EXIFTOOL_PATH)
    
    if new_file_path is None:
        print(f"重命名文件失败: {file_path}")
        return False
    
    # 创建输出文件夹
    output_dir = os.path.join(os.path.dirname(new_file_path), output_folder)
    os.makedirs(output_dir, exist_ok=True)
    
    if is_video(new_file_path):
        # 处理视频
        output_path = os.path.join(output_dir, os.path.basename(new_file_path))
        print(f"正在处理视频: {os.path.basename(new_file_path)}")
        processing_result = process_video(new_file_path, output_path, update_current_progress, 
                                       check_if_running, FFMPEG_PATH, rotation="0", 
                                       min_size_mb=min_size_mb)
        if processing_result is True:  # 处理成功
            print(f"处理视频 {os.path.basename(new_file_path)} 成功")
            modify_file_dates(output_path, EXIFTOOL_PATH)
            return True
        elif processing_result is False:  # 处理失败
            print(f"处理视频 {os.path.basename(new_file_path)} 失败")
            cleanup_failed_process(new_file_path, output_path, move_to_error=True)
            return False
        elif processing_result is None:  # 文件被跳过或处理被终止
            print(f"跳过视频 {os.path.basename(new_file_path)}")
            return None
    elif is_photo(new_file_path):
        try:
            # 移动照片
            moved_path = move_photo(new_file_path, output_dir)
            modify_file_dates(moved_path, EXIFTOOL_PATH)
            update_current_progress.emit(os.path.basename(new_file_path), 100)
            return True
        except Exception as e:
            print(f"处理照片 {os.path.basename(new_file_path)} 失败: {e}")
            cleanup_failed_process(new_file_path, os.path.join(output_dir, os.path.basename(new_file_path)), move_to_error=True)
            return False

    return False

def cleanup_failed_process(input_path, output_path, move_to_error=False):
    try:
        subprocess.run(["taskkill", "/F", "/IM", "ffmpeg.exe"], check=False, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(1)
        if os.path.exists(output_path):
            os.remove(output_path)
            print(f"已删除未完成的输出文件: {output_path}")
    except Exception as e:
        print(f"无法删除文件 {output_path}: {e}")
    
    if move_to_error:
        # 移动到 ERROR 文件夹
        error_dir = os.path.join(os.path.dirname(input_path), 'ERROR')
        os.makedirs(error_dir, exist_ok=True)
        error_path = os.path.join(error_dir, os.path.basename(input_path))
        os.rename(input_path, error_path)
        print(f"已将文件 {os.path.basename(input_path)} 移动到 ERROR 文件夹")

if __name__ == "__main__":
    input_paths = get_input_paths()
    existing_files = check_existing_files(input_paths)
    process_files(input_paths, None, None, lambda: True, existing_files, "H264")

