import os
import json
import exiftool

from utils.config import readConfig
from utils.metadata import extractMetadatas

    
def extractInformations(
    music_path:str,
    exiftool_exe_path: str| None=None,
    save_path:str='./extracted_infos.json',
    main_keys_to_excluse:list[str]=[]
) -> None:
    # Get metadatas
    metadatas = extractMetadatas(
        files_paths         = music_path,
        exiftool_exe_path   = exiftool_exe_path,
    )
    # with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
    #     entries = []
    #     for entry in os.scandir(music_path):
    #         if not entry.is_file():
    #             continue
            
    #         path = entry.path       
    #         try:
    #             raw_bytes = et.execute("-a", path, raw_bytes=True)
    #             raw_output = raw_bytes.decode("utf-8", errors="replace")
    #         except Exception as e:
    #             print(f"\n[ERROR] ExifTool failed for: {path}")
    #             print(f"Exception: {e}")
    #             print(f"args: {e.args}")
    #             print(f"dict: {vars(e)}")
    #             continue
            
    #         entry = {"SourceFile": path}
    #         for line in raw_output.splitlines():
    #             if not " : " in line:
    #                 continue
                
    #             left, value = line.split(" : ", 1)
    #             left = left.strip()
    #             value = value.strip()
                

    #             if value.isdigit():
    #                 value = int(value)
                    
    #             if left.startswith('[') and ']' in left:
    #                 group_end = left.index(']')
    #                 group = left[1:group_end].strip()
                    
    #                 if group in main_keys_to_excluse:
    #                     continue
                    
    #                 tag = left[group_end+1:].strip()
    #                 key = f'{group}:{tag}'
                    
    #                 if key in entry:
    #                     if isinstance(entry[key], list):
    #                         entry[key].append(value)
    #                     else:
    #                         entry[key] = [entry[key], value]
    #                 else:
    #                     entry[key] = value
    #         entries.append(entry)

    # Save metadatas
    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(metadatas, f, indent=4)
    
    
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=False, help="Path to the config file")
    args = parser.parse_args()
    config_path = args.config if args.config is not None else './config.toml'
    
    config = readConfig(config_path)
    extractInformations(
        **config['global'], 
        **config['extraction']
    )