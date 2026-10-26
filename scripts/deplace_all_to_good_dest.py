import os
import shutil
import argparse
from dataclasses import asdict
import pandas as pd
from tqdm import tqdm

from utils.file import getDestination, deleteEmptyFolders
from utils.metadata import extractMetadatas
from utils.logging_utils import getLogger
from utils.audio_quality import rankAudioQuality

logger = getLogger(__name__)

def deplaceAllToGoodDest(args):
    metadatas = extractMetadatas(args.path, exiftool_exe_path=args.exiftool_exe_path, verbose=args.verbose)
    
    verbose = args.verbose and not args.dry_run
    for file_metadatas in tqdm(metadatas, disable=not verbose, unit=' file', mininterval=1):
        file_path = file_metadatas['SourceFile']
        new_file_path = getDestination(args.path, file_path, file_metadatas)
        
        # case same files: silently continue
        file_path_normalized = os.path.normcase(os.path.abspath(file_path))
        new_file_path_normalized = os.path.normcase(os.path.abspath(new_file_path))
        if file_path_normalized == new_file_path_normalized:
            continue
        
        # case new path exist: log error, continue
        if os.path.exists(new_file_path):
            logger.error(f'New file path already exist: {file_path} -> {new_file_path}')
            ranking, decisive = rankAudioQuality([file_path, new_file_path], keep_order=True)
            ranking = [asdict(x) for x in ranking]
            for rank in ranking:
                rank['notes'] = ', '.join(rank['notes'])
            df = pd.DataFrame(
                ranking,
                index=["File 1", "File 2"],
            ).T
            print(df.to_string())
            continue
        
        # case dry run: log plan, continue
        if args.dry_run:
            print(f'{file_path} -> {new_file_path}')
            continue
        
        os.makedirs(os.path.split(new_file_path)[0], exist_ok=True)
        shutil.move(file_path, new_file_path)
    
    if not args.dry_run:
        deleteEmptyFolders(args.path)
        
    

if __name__ == '__main__':
    """ 
    Exemple:
           py scripts/deplace_all_to_good_dest.py E:/music -v --dry_run --exiftool_exe_path 'E:\code\format_song_files\exiftool-13.59_64\exiftool.exe'
    """
    parser = argparse.ArgumentParser(description='Deplace all tracks to their corresponding destination. Then delete empty folders.')
        
    parser.add_argument("path", help="Directory or file to process.")
    parser.add_argument("-eep", "--exiftool_exe_path", default=None, help="Exiftool executable path.")
    parser.add_argument("-dr", "--dry_run", action="store_true", help="Display the deplacements instead to do it.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Progress bar.")
    
    args = parser.parse_args()
    
    deplaceAllToGoodDest(args)