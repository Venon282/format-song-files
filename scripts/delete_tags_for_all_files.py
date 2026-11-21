import os
import mutagen
import argparse
from tqdm import tqdm

from utils.file import iterFiles
from utils.metadata import deleteTags
from utils.logging_utils import getLogger

logger = getLogger(__name__)

def deleteTagsForAllFiles(
    root:str,
    tags:list[str] | str, 
    variants:bool=False,
    dry_run:bool=False,
):
    # pass single tag to list
    if isinstance(tags, str):
        tags = [tags]
        
    # does we add variants to be stronger deletion ?
    if variants:
        from utils.string import generateKeyVariants, stringWithSpaceAroundsCase
        for tag in tags.copy():
            variant_keys = generateKeyVariants(tag)
            tags.extend(variant_keys)
            tags.extend(item for variant_key in variant_keys for item in stringWithSpaceAroundsCase(variant_key))
        
        tags = list(set(tags))
        
    # Verify that the user is okay with what will be deleted
    is_valid = ''
    new_line = "\n"
    while is_valid.lower() not in ('y', 'n'):
        print(f'{new_line.join([repr(tag) for tag in tags])}\n\n')
        if dry_run:
            print('Dry run is activate so no worries.')
        is_valid = input('Above tags will be deleted in all files. Ok [Y/N] ? ').lower()
        
        if is_valid == 'y':
            break
        if is_valid == 'n':
            import sys
            logger.info('Abort, no process occured.')
            sys.exit()
            
    # Deletion part
    for file_path in tqdm(iterFiles(root), mininterval=1, disable=dry_run, desc='File process:', unit='file'):
        try:
            audio = mutagen.File(file_path, easy=True)
        except Exception as e:
            logger.error(f'{file_path}: {e}')
            continue
        
        if audio is None:
            logger.error(f'Reading {file_path}')
            continue
        
        if dry_run:
            tags_delete = [repr(tag) for tag in tags if tag in audio]
            if tags_delete:
                logger.info(f'{os.path.splitext(os.path.basename(file_path))[0]} del: {", ".join(tags_delete)}')
            continue
        
        deleteTags(audio, tags, variants=False)
        
        audio.save()
        
    

if __name__ == '__main__':
    """ 
    py .\scripts\delete_tags_for_all_files.py E:/music <tags> --dry_run --variants
    """
    
    parser = argparse.ArgumentParser(description='Delete tags from the song collection.')
    parser.add_argument("path", type=str, help="Directory or file to process.")
    parser.add_argument("tags", nargs='+', help="Tags to delete.")
    parser.add_argument("-d", "--dry_run", action='store_true', help="Process without deleting any file.")
    parser.add_argument("--variants", action='store_true', help="Add the variants of define tags.")
    
    args = parser.parse_args()
        
        
    deleteTagsForAllFiles(
        root = args.path,
        tags = args.tags, 
        variants=args.variants,
        dry_run = args.dry_run,
    )