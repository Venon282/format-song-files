import json
import exiftool
import time
import matplotlib.pyplot as plt

import utils

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

if __name__ == '__main__':
    from utils.config import readConfig
    
    config = readConfig()
    exiftool_exe_path = config['global']['exiftool_exe_path']
    dir_path = r'E:\music'
    
    from utils.stat import countMetadatas
    from utils.constant import METADATA_KEYS
    
    keys = []
    # counter = countMetadatas(dir_path, exiftool_exe_path=exiftool_exe_path, max_files=100, verbose=True)
        
    # print(counter.keys())
        
    counter = countMetadatas(dir_path, keys=METADATA_KEYS, exiftool_exe_path=exiftool_exe_path, sort='asc', verbose=True)
    
    print(json.dumps(counter, indent=2))
    
    counter = countMetadatas(dir_path, keys=METADATA_KEYS, exiftool_exe_path=exiftool_exe_path, sort='desc', verbose=True)
        
    print(json.dumps(counter, indent=2))
    
            
