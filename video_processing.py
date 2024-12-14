import subprocess
from tqdm import tqdm
import os
import time

def should_process_video(file_path, min_size_mb):
    """检查视频文件是否需要处理"""
    try:
        file_size = os.path.getsize(file_path) / (1024 * 1024)  # 转换为MB
        return file_size >= min_size_mb
    except Exception as e:
        print(f"获取文件大小失败: {e}")
        return True  # 如果无法获取文件大小，默认处理该文件

def process_video(input_path, output_path, update_progress, check_if_running, ffmpeg_path, rotation="0", min_size_mb=10):
    # 检查文件大小
    if not should_process_video(input_path, min_size_mb):
        print(f"跳过小于 {min_size_mb}MB 的文件: {input_path}")
        return None  # 返回 None 表示文件被跳过
        
    command = [
        ffmpeg_path,
        '-i', input_path,
        '-c:v', 'libx264',
        '-preset', 'veryslow',
        '-crf', '21',
        '-g', '120',
        '-sc_threshold', '60',
        '-x264-params', 'ref=1:qcomp=0.5:psy-rd=0.3,0:aq-mode=2:aq-strength=0.8',
        '-c:a', 'aac',
        '-b:a', '256k'
    ]

    # 添加旋转参数
    if rotation != "0":
        if rotation == "90":
            command.extend(['-vf', 'transpose=1'])
        elif rotation == "180":
            command.extend(['-vf', 'transpose=1,transpose=1'])
        elif rotation == "270":
            command.extend(['-vf', 'transpose=2'])

    command.append(output_path)
    
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, encoding='utf-8', errors='replace')
    except Exception as e:
        print(f"启动 ffmpeg 时出错: {e}")
        return False
    
    duration = None
    for line in process.stderr:
        if "Duration" in line:
            try:
                time_str = line.split("Duration: ")[1].split(",")[0].strip()
                if time_str != "N/A":
                    h, m, s = map(float, time_str.split(':'))
                    duration = h * 3600 + m * 60 + s
                else:
                    print("无法确定视频时长，将不显示进度")
            except Exception as e:
                print(f"解析视频时长时出错: {e}")
            break
    
    # 使用 emit 方法来发送信号
    update_progress.emit(os.path.basename(input_path), 0)  # 确保进度条从0%开始
    
    if duration:
        for line in process.stderr:
            if not check_if_running():
                process.terminate()
                time.sleep(1)  # 给进程一些时间来终止
                return None  # 返回 None 表示处理被终止
            if "time=" in line:
                try:
                    time_str = line.split("time=")[1].split()[0].strip()
                    if time_str != "N/A":
                        h, m, s = map(float, time_str.split(':'))
                        current_time = h * 3600 + m * 60 + s
                        progress = int((current_time / duration) * 100)
                        update_progress.emit(os.path.basename(input_path), progress)
                except Exception as e:
                    print(f"解析当前时间时出错: {e}")
    else:
        for line in process.stderr:
            if not check_if_running():
                process.terminate()
                time.sleep(1)  # 给进程一些时间来终止
                return None  # 返回 None 表示处理被终止
    
    return_code = process.wait()
    if return_code != 0:
        print(f"ffmpeg 处理失败，返回代码: {return_code}")
        return False
    return True
