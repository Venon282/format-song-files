import os
import json
import mutagen
import traceback
import pandas as pd 
from dataclasses import asdict

import special_tag_reorganisation

from utils.audio_quality import rankAudioQuality
from utils.file import getDestination, fileToOpus, renameFile
from utils.metadata import deleteTags, setTags
from utils.logging_utils import getLogger
from utils.config import readConfig

logger = getLogger(__name__)
    
def insertInformations(
    music_path:str,
    exiftool_exe_path: str| None=None,
    load_path:str='./extracted_infos.json',
    separator: str = '; ',
    tag_reorganisation: str | None = None,
    deplace_to_path: str | None = None,
) -> None:
    # Load metadatas
    with open(load_path, 'r', encoding='utf-8') as f:
        entries = json.load(f)
    
    # reorganise tags depending of a defined method
    if tag_reorganisation is not None:
        getattr(special_tag_reorganisation, tag_reorganisation)(entries, exclude_tags = ('title', 'artist', 'album_artist', 'year', 'album')) # inplace
        
    # Handle metadatas
    files_error = {}
    for entry in entries:
        source_file = entry['SourceFile']
        try:
            source_file = fileToOpus(source_file)
            audio = mutagen.File(source_file, easy=True)

            deleteTags(audio, entry['TagsToDelete'] + list(entry['TagsToSet'].keys()))
            setTags(audio, entry['TagsToSet'])
            
            audio.save()
            
            # Get extension from converted file
            new_ext = os.path.splitext(source_file)[1]

            # Update entry['NewFileName'] extension
            base_name = os.path.splitext(entry['NewFileName'])[0]
            entry['NewFileName'] = base_name + new_ext
            
            source_file = renameFile(entry['NewFileName'], source_file)
            
            if deplace_to_path is not None:
                
                dest_file = getDestination(music_root=deplace_to_path, file_path=source_file, file_metadatas=entry['TagsToSet'])
                
                if os.path.exists(dest_file):
                    ranking, decisive = rankAudioQuality([source_file, dest_file], keep_order=True)
                    
                    if ranking[0] == ranking[1]:
                        os.remove(source_file)
                        logger.warning(f'File removed as same than destination one: {source_file}')
                        continue
                        
                    ranking = [asdict(x) for x in ranking]
                    for rank in ranking:
                        rank['notes'] = '' #'\n'.join(rank['notes'])
                    df = pd.DataFrame(
                        ranking,
                        index=["File 1", "File 2"],
                    ).T
                    print(df.to_string())
                    
                    files_error[source_file] = [f"File already exist in destination.", entry]
                    continue
                
                os.makedirs(os.path.dirname(dest_file), exist_ok=True)
                os.rename(source_file, dest_file)
        except:
            files_error[source_file] = [traceback.format_exc(), entry]
            continue
        
    for source_file, [error, entry] in files_error.items():
        print(f'{source_file}: {error}')   # \n{entry}\n
             
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", required=False, help="Path to the config file")
    args = parser.parse_args()
    config_path = args.config if args.config is not None else './config.toml'
        
    config = readConfig(config_path)
    insertInformations(**config['global'], **config['insertion'])