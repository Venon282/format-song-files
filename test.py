import os
import json
import time
import shutil
import exiftool
import matplotlib.pyplot as plt

from utils.logging_utils import getLogger

logger = getLogger(__name__)

def timeTestExtractMetadatasBatchSize(dir_path, exiftool_exe_path):
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
            extractMetadatas(files, exiftool_exe_path, verbose=True, batch_size=batch_size)
            end = time.perf_counter() - start
            results.append(end)
            
        fig = plt.figure(figsize=(12, 8))
        plt.plot(batch_sizes, results, marker='o')
        plt.legend()
        plt.xscale('log')
        plt.xlabel("Batch size")
        plt.ylabel("Execution time (seconds)")
        plt.title("Metadata extraction performance")
        plt.grid(True)
        plt.show()
        
def timeTestExtractMetadatasWithWorkers(dir_path, exiftool_exe_path):
        from utils.metadata import extractMetadatas
        from utils.file import iterFiles
        
        quantity = 5000
        workers = [0, 2, 4, 6, 8, 10, 12]
        file_iter = iterFiles(dir_path)
        files = list(file_iter)[:quantity]
        results = []
        for worker in workers:
            print(f'Process {worker} workers')
            start = time.perf_counter()
            extractMetadatas(files, exiftool_exe_path, verbose=True, batch_size=100, max_workers=worker)
            end = time.perf_counter() - start
            results.append(end)
            
            
        fig = plt.figure(figsize=(12, 8))
        plt.plot(workers, results, marker='o')
        plt.legend()
        plt.xlabel("Max workers")
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
    
    # timeTestExtractMetadatasWithWorkers(music_path, exiftool_exe_path)
    
    from utils.string import generateKeyVariants
    print(generateKeyVariants('PictureMIMEType'))
    
    #fileWithNonLatinCharFromServerToTodo(music_path, todo_path, exiftool_exe_path)

            
