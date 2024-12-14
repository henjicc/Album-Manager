import shutil
import os

def move_photo(input_path, output_dir):
    os.makedirs(output_dir, exist_ok=True)
    shutil.move(input_path, output_dir)
    moved_path = os.path.join(output_dir, os.path.basename(input_path))
    print(f"已移动照片: {os.path.basename(input_path)}")
    return moved_path
