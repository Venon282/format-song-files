import os
import argparse

from utils.file import iterFiles, fileToOpus
from utils.logging_utils import getLogger

logger = getLogger(__name__)

def convertAllToOpus(path:str):
    file_iterator = [path] if os.path.isfile(path) else iterFiles(path) # pass one file to convert is allow
    
    for i, file_path in enumerate(file_iterator):
        new_path = fileToOpus(file_path)
        
        if new_path != file_path:
            logger.info(f'{i} - {os.path.basename(file_path)} -> {os.path.basename(new_path)}')
        
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert all musics of a directory or a single file to .opus recursively.')
    
    parser.add_argument("path", type=str, help="Directory or file to process.")
    
    args = parser.parse_args()
    
    convertAllToOpus(args.path)