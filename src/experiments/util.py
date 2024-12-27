import os
import shutil


def clean_working_dir():
    """カレントワーキングディレクトリ以下の全ファイル・フォルダを削除"""
    current_dir = os.getcwd()

    for item in os.listdir(current_dir):
        item_path = os.path.join(current_dir, item)
        try:
            shutil.rmtree(item_path)
        except NotADirectoryError:
            os.unlink(item_path)
