import os
import json
import shutil
import mutagen

import special_tag_reorganisation
from utils import readConfig
    
def renameFile(new_name: str, file_path: str):
    new_file_path = os.path.join(os.path.dirname(file_path), new_name)
    os.rename(file_path, new_file_path)
    return new_file_path
    
def deleteTags(audio:mutagen.File, tags_to_delete: list[str]):
    if not tags_to_delete:
        return
    
    for tag in tags_to_delete:
        audio.pop(tag, None)
    
def setTags(audio:mutagen.File, tags_to_set: dict[str, str]):
    if not tags_to_set:
        return

    for tag, value in tags_to_set.items():
        audio[tag] = value
    
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
        
    all_files = [entry.path for entry in os.scandir(music_path) if entry.is_file()]
    if len(all_files) != len(entries):
        raise ValueError(f'Found {len(all_files)} files for {len(entries)} entries')
    
    if tag_reorganisation is not None:
        getattr(special_tag_reorganisation, tag_reorganisation)(entries, separator) # inplace
        
    # Handle metadatas
    for entry in entries:
        source_file = entry['SourceFile']
        audio = mutagen.File(source_file, easy=True)
        
        deleteTags(audio, entry['TagsToDelete'])
        setTags(audio, entry['TagsToSet'])
        
        audio.save()
        
        source_file = renameFile(entry['NewFileName'], source_file)
        
        if deplace_to_path is not None:
            shutil.move(source_file, os.path.join(deplace_to_path, os.path.basename(source_file)))
        
        
            
    
    
    
if __name__ == "__main__":
    config = readConfig()
    insertInformations(**config['global'], **config['insertion'])