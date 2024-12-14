import os
import platform
import sys
import shlex

def is_video(file):
    return file.lower().endswith(('.mp4', '.mov', '.mkv'))

def is_photo(file):
    return file.lower().endswith(('.jpg', '.png', '.heic', '.heif'))

def get_input_paths():
    if platform.system() == "Windows":
        print("请输入路径，多个路径请用引号包裹并用空格分隔：", end='', flush=True)
    else:
        print("请输入路径，多个路径请用引号包裹并用空格分隔：", end='', flush=True)
    
    input_line = sys.stdin.readline().strip()
    paths = shlex.split(input_line)  # 使用 shlex.split() 来正确处理带引号的路径
    return [os.path.abspath(os.path.expanduser(path)) for path in paths]

def count_files(input_path):
    total_files = 0
    if os.path.isfile(input_path):
        return 1
    for root, _, files in os.walk(input_path):
        for file in files:
            if is_video(file) or is_photo(file):
                total_files += 1
    return total_files
