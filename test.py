from format_song_files.utils import *
import json
from insert_informations import deleteTags, setTags
import mutagen

"""
{
    "SourceFile": "E:\\music\\1994 (Nightcore) - Alec Benjamin (2018).opus",
    "ExifTool:ExifTool Version Number": "13.59",
    "File:File Name": "1994 (Nightcore) - Alec Benjamin (2018).opus",
    "File:Directory": "E:/music",
    "File:File Size": 3278356,
    "File:File Modification Date/Time": "2026:08:16 21:44:27+02:00",
    "File:File Access Date/Time": "2026:08:20 09:37:52+02:00",
    "File:File Creation Date/Time": "2026:08:16 21:23:31+02:00",
    "File:File Permissions": 100666,
    "File:File Type": "OPUS",
    "File:File Type Extension": "OPUS",
    "File:MIME Type": "audio/ogg",
    "Opus:Opus Version": 1,
    "Opus:Audio Channels": 2,
    "Opus:Sample Rate": 48000,
    "Opus:Output Gain": 1,
    "Vorbis:Vendor": "Lavf63.5.101",
    "Vorbis:Encoder": "Lavf63.5.101",
    "Vorbis:Title": "1994 (Nightcore)",
    "Vorbis:Artist": "Alec Benjamin",
    "Vorbis:Year": 2018,
    "Vorbis:Genre": [
        "1994 (Nightcore)",
        "Alec Benjamin",
        2018,
        "Pop",
        "Singer-Songwriter",
        "Nightcore",
        "Nightcore",
        "Remix",
        "Sped Up",
        "Nostalgic",
        "Reflective",
        "Bittersweet",
        "Coming-of-age",
        "English",
        "USA",
        "2010s",
        "Fan art featuring My Hero Academia's Izuku Midoriya",
        "Original by Alec Benjamin"
    ],
    "Vorbis:Style": [
        "Nightcore",
        "Remix",
        "Sped Up"
    ],
    "Vorbis:Mood": [
        "Nostalgic",
        "Reflective",
        "Bittersweet",
        "Coming-of-age"
    ],
    "Vorbis:Language": "English",
    "Vorbis:Country": "USA",
    "Vorbis:Decade": "2010s",
    "Vorbis:Comment": [
        "Fan art featuring My Hero Academia's Izuku Midoriya",
        "Original by Alec Benjamin"
    ],
    "Vorbis:Real Genre": [
        "Pop",
        "Singer-Songwriter",
        "Nightcore"
    ],
    "FLAC:Picture Type": 3,
    "FLAC:Picture MIME Type": "image/png",
    "FLAC:Picture Description": "",
    "FLAC:Picture Width": 1280,
    "FLAC:Picture Height": 720,
    "FLAC:Picture Bits Per Pixel": 0,
    "FLAC:Picture Indexed Colors": 0,
    "FLAC:Picture Length": 422669,
    "FLAC:Picture": "(Binary data 422669 bytes, use -b option to extract)"
}
"""


def getAllNightCoreTitles():
    # wait to have handle all nightcore before so they have the tags
    config = readConfig()
    infos = extractInfosWithTags(r'E:\music', {'Vorbis:Genre':'NightCore'}, key_operator='or', exiftool_exe_path=config['global']['exiftool_exe_path'])
    source_files = infosSingleFilter(infos, key='SourceFile')
    print(source_files)
    
def getAllGenres():
    config = readConfig()
    tags = getAllTags(r'E:\music', keys='Vorbis:Genre', exiftool_exe_path=config['global']['exiftool_exe_path'])
    print(tags)
    
def updateAllTags():
    config = readConfig()
    styles = getAllTags(r'E:\music', keys='Vorbis:Style', exiftool_exe_path=config['global']['exiftool_exe_path'])
    moods = getAllTags(r'E:\music', keys='Vorbis:Mood', exiftool_exe_path=config['global']['exiftool_exe_path'])
    genres = getAllTags(r'E:\music', keys='Vorbis:Real Genre', exiftool_exe_path=config['global']['exiftool_exe_path'])
    
    obj = {
        "style"    : list(styles   ),
        "mood"     : list(moods    ),
        "genre"    : list(genres   )
    }
    
    with open("all_tags.json", "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=4)
        
def correctSemicolonTags():
    
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    keys = ["Vorbis:Genre", "Vorbis:Style", "Vorbis:Mood", "Vorbis:Comment", "Vorbis:Real Genre"]
    
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
        for entry in os.scandir(dir_path):
            if not entry.is_file():
                continue
            
            infos = extractInformation(entry.path, et)

            for key in keys:
                if key not in infos:
                    logger.warning(
                        "Key %s is not present in %s",
                        key,
                        os.path.basename(entry.path)
                    )
                    continue
                
                raw_values = infos[key] if isinstance(infos[key], list) else [infos[key]]
                
                # verify if an element have a semicolon
                has_semicolon = any(isinstance(v, str) and ';' in v for v in raw_values)
                if not has_semicolon:
                    continue

                # reconstruct the list, split ; and convert all to str
                clean_values = []
                for v in raw_values:
                    v_str = str(v)
                    if ';' in v_str:
                        clean_values.extend([part.strip() for part in v_str.split(';') if part.strip()])
                    else:
                        clean_values.append(v_str.strip())

                # Use SourceFile or current path
                target_path = infos.get('SourceFile', entry.path)
                audio = mutagen.File(target_path, easy=True)
                
                simple_key = key.split(':')[1].lower().strip().replace(' ','_')
                deleteTags(audio, simple_key)
                setTags(audio, {simple_key: list(set(clean_values))})
                
                audio.save()
                
def restartDeleteAllTags():
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    keys = ["Vorbis:Genre", "Vorbis:Style", "Vorbis:Mood", "Vorbis:Comment", "Vorbis:Real Genre"]
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as et:
        for entry in os.scandir(dir_path):
            if not entry.is_file():
                continue
                
            audio = mutagen.File(entry.path, easy=True)
            deleteTags(audio, [key.split(':')[1].lower().strip().replace(' ','_') for key in keys])
            
            audio.save()
            
def sortAllPossibleTags():
    path = 'all_possible_tags.json'
    with open(path, 'r', encoding='utf-8') as f:
        apt = json.load(f)
        
    for k, v in apt.items():
        apt[k] = sorted(apt[k])
        
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(apt, f, indent=4)
        
if __name__ == '__main__':
    sortAllPossibleTags()