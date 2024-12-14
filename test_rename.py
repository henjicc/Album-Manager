import os
from date_utils import rename_file
from file_utils import get_input_path, is_video, is_photo

def test_rename():
    input_path = get_input_path()
    
    if os.path.isfile(input_path):
        if is_video(input_path) or is_photo(input_path):
            new_path = rename_file(input_path)
            if new_path:
                print(f"文件已重命名: {os.path.basename(input_path)} -> {os.path.basename(new_path)}")
            else:
                print(f"文件重命名失败: {os.path.basename(input_path)}")
        else:
            print(f"不支持的文件类型: {os.path.basename(input_path)}")
    elif os.path.isdir(input_path):
        for root, _, files in os.walk(input_path):
            for file in files:
                if is_video(file) or is_photo(file):
                    file_path = os.path.join(root, file)
                    new_path = rename_file(file_path)
                    if new_path:
                        print(f"文件已重命名: {file} -> {os.path.basename(new_path)}")
                    else:
                        print(f"文件重命名失败: {file}")
    else:
        print(f"无效的输入路径: {input_path}")

if __name__ == "__main__":
    test_rename()
