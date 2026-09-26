import os
from format_song_files.utils import convertToOpus

def renamconvertAll(dir_path:str):
    for entry in os.scandir(dir_path):
        if not entry.is_file() or entry.path.endswith('.opus'):
            continue
        path = entry.path
        new_path = convertToOpus(entry.path)
        print(f'{os.path.basename(path)} -> {os.path.basename(new_path)}')
        
        

if __name__ == "__main__":
    renamconvertAll(r"E:\music")