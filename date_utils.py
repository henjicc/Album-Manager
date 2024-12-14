import subprocess
from datetime import datetime, timedelta
import os
from file_utils import is_video, is_photo

def rename_file(file_path, exiftool_path):
    try:
        if is_video(file_path):
            date_cmd = [exiftool_path, '-MediaCreateDate', '-s', '-s', '-s', file_path]
            tag = 'MediaCreateDate'
        else:
            date_cmd = [exiftool_path, '-DateTimeOriginal', '-s', '-s', '-s', file_path]
            tag = 'DateTimeOriginal'
        
        creation_date = subprocess.check_output(date_cmd, universal_newlines=True).strip()
        
        if not creation_date or creation_date == '0000:00:00 00:00:00':
            date_cmd = [exiftool_path, '-FileModifyDate', '-s', '-s', '-s', file_path]
            creation_date = subprocess.check_output(date_cmd, universal_newlines=True).strip()
            tag = 'FileModifyDate'
        
        if creation_date and creation_date != '0000:00:00 00:00:00':
            if tag == 'FileModifyDate':
                # 处理 FileModifyDate 格式
                date_obj = datetime.strptime(creation_date.split('+')[0], '%Y:%m:%d %H:%M:%S')
            else:
                date_obj = datetime.strptime(creation_date, '%Y:%m:%d %H:%M:%S')
            
            # 如果是视频文件且使用的是 MediaCreateDate，加 8 小时
            if is_video(file_path) and tag == 'MediaCreateDate':
                date_obj += timedelta(hours=8)
            
            new_name = date_obj.strftime('%Y_%m_%d %H_%M_%S') + os.path.splitext(file_path)[1]
            new_path = os.path.join(os.path.dirname(file_path), new_name)
            
            # 检查是否存在同名文件，排除文件自身
            while os.path.exists(new_path) and os.path.abspath(new_path) != os.path.abspath(file_path):
                date_obj += timedelta(seconds=1)
                new_name = date_obj.strftime('%Y_%m_%d %H_%M_%S') + os.path.splitext(file_path)[1]
                new_path = os.path.join(os.path.dirname(file_path), new_name)
            
            os.rename(file_path, new_path)
            print(f"已重命名: {os.path.basename(file_path)} -> {new_name}")
            return new_path
        else:
            print(f"无法获取 {file_path} 的有效创建日期")
            return None
    except Exception as e:
        print(f"重命名 {file_path} 时出错: {e}")
        return None

def modify_file_dates(file_path, exiftool_path):
    file_name = os.path.basename(file_path)
    date_str = file_name[:19].replace('_', ':')
    
    if is_video(file_path):
        command = [
            exiftool_path, '-api', 'QuickTimeUTC',
            f'-AllDates={date_str}+08:00',
            f'-TrackCreateDate={date_str}+08:00',
            f'-TrackModifyDate={date_str}+08:00',
            f'-MediaCreateDate={date_str}+08:00',
            f'-MediaModifyDate={date_str}+08:00',
            f'-FileCreateDate={date_str}+08:00',
            f'-FileModifyDate={date_str}+08:00',
            file_path,
            '-overwrite_original'
        ]
    else:
        command = [
            exiftool_path,
            f'-AllDates={date_str}+08:00',
            f'-FileCreateDate={date_str}+08:00',
            f'-FileModifyDate={date_str}+08:00',
            file_path,
            '-overwrite_original'
        ]
    
    try:
        subprocess.run(command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"已修改 {file_name} 的时间属性")
    except subprocess.CalledProcessError as e:
        print(f"修改 {file_name} 的时间属性时出错: {e}")
