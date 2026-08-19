import os
import json
import exiftool
from format_song_files.utils import readConfig

    
def extractInformations(
    music_path:str,
    exiftool_exe_path: str| None=None,
    save_path:str='./extracted_infos.json'
) -> None:
    # Get metadatas
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
        entries = []
        for entry in os.scandir(music_path):
            if not entry.is_file():
                continue
            
            path = entry.path       
            raw_output = et.execute("-a", path)
            
            entry = {"SourceFile": path}
            for line in raw_output.splitlines():
                if not " : " in line:
                    continue
                
                left, value = line.split(" : ", 1)
                left = left.strip()
                value = value.strip()
                
                if value.isdigit():
                    value = int(value)
                    
                if left.startswith('[') and ']' in left:
                    group_end = left.index(']')
                    group = left[1:group_end].strip()
                    tag = left[group_end+1:].strip()
                    key = f'{group}:{tag}'
                    
                    if key in entry:
                        if isinstance(entry[key], list):
                            entry[key].append(value)
                        else:
                            entry[key] = [entry[key], value]
                    else:
                        entry[key] = value
            entries.append(entry)

    # Save metadatas
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, indent=4)
    
    
if __name__ == "__main__":
    config = readConfig()
    extractInformations(**config['global'], **config['extraction'])