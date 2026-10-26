import os
import json
import time
import shutil
import exiftool
import matplotlib.pyplot as plt

from utils.logging_utils import getLogger

logger = getLogger(__name__)

def timeTestExtractMetadatasBatchSize(dir_path, exiftool_exe_path):
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as eh:
        from utils.metadata import extractMetadatas
        from utils.file import iterFiles
        
        quantity = 5000
        batch_sizes = [1, 10, 100, 200, 500, 1000, 2000]
        file_iter = iterFiles(dir_path)
        files = list(file_iter)[:quantity]
        results = []
        for batch_size in batch_sizes:
            print(f'Process {batch_size}')
            start = time.perf_counter()
            extractMetadatas(files, eh, verbose=True, batch_size=batch_size)
            end = time.perf_counter() - start
            results.append(end)
            
        fig = plt.figure(figsize=(12, 8))
        plt.plot(batch_sizes, results)
        plt.legend()
        plt.xscale('log')
        plt.xlabel("Batch size")
        plt.ylabel("Execution time (seconds)")
        plt.title("Metadata extraction performance")
        plt.grid(True)
        plt.show()
def timeTestExtractInfosVsMetadatas(dir_path, exiftool_exe_path):
    from utils.stat import countMetadatas
    from utils.metadata import extractMetadatas
    from utils.file import iterFiles
    import time
    from format_song_files.utils import extractInformation
    from tqdm import tqdm
    
    with exiftool.ExifToolHelper(executable=exiftool_exe_path, encoding="utf-8") as eh:
        results = {'old':[], 'new':[]}
        quantities = [1, 10, 100, 1000, 2000, 5000, 10000]
        for quantity in quantities:
            print(f'Process {quantity}')
            start = time.perf_counter()
            for i, file_path in tqdm(enumerate(iterFiles(dir_path)), mininterval=1, total=quantity):
                extractInformation(file_path, exiftool_helper=eh)
                if i >= quantity - 1:
                    break
            end = time.perf_counter() - start
            results['old'].append(end)
            
            start = time.perf_counter()
            file_iter = iterFiles(dir_path)
            files = list(file_iter)[:quantity]
            extractMetadatas(files, eh, verbose=True, batch_size=100)
            end = time.perf_counter() - start
            results['new'].append(end)
            
        fig = plt.figure(figsize=(12, 8))
        for key, y in results.items():
            plt.plot(quantities, y, label=key)
        plt.legend()
        plt.xscale('log')
        plt.xlabel("Number of files")
        plt.ylabel("Execution time (seconds)")
        plt.title("Metadata extraction performance")
        plt.grid(True)
        plt.show()

def fileWithNonLatinCharFromServerToTodo(music_path: str, todo_path:str, exiftool_exe_path:str):
    from utils.metadata import extractMetadatas
    from utils.file import iterFiles
    from utils.constant import PLEX_METADATA_KEYS_MODIF, METADATA_KEYS
    from utils.language import isNotLatin
    
    keys = list(set(PLEX_METADATA_KEYS_MODIF) | set(METADATA_KEYS))
    
    iterator = list(iterFiles(music_path))
    metadatas = extractMetadatas(iterator, exiftool_exe_path, verbose=True)
    for file_metadatas in metadatas:
        for key in keys:
            if key not in file_metadatas:
                continue
            if not isinstance(file_metadatas[key], list):
                file_metadatas[key] = [str(file_metadatas[key])]
            
            content = ', '.join(file_metadatas[key])
            
            is_not_latin = isNotLatin(content)
            
            if is_not_latin:
                #logger.info(f'{os.path.basename(file_metadatas["SourceFile"])} - {key}: {content}')
                
                file_dir, file_name = os.path.split(file_metadatas["SourceFile"])
                destination = os.path.join(todo_path, file_name)
                
                if os.path.exists(destination):
                    logger.error(f'Already exist: {destination}')
                else:
                    shutil.move(file_metadatas["SourceFile"], destination)
                break
                

        

if __name__ == '__main__':
    from utils.config import readConfig
    import re
    
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    music_path = r'E:\music'
    todo_path = r'E:\music utils\todo'
    
    
    #fileWithNonLatinCharFromServerToTodo(music_path, todo_path, exiftool_exe_path)
    
            
