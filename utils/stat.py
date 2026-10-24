from collections import defaultdict
from typing import Literal
from tqdm import tqdm
import exiftool
import os

from utils.file import iterFiles, fileToOpus
from utils.metadata import extractMetadatas


def countMetadatas(
        root:str,
        keys: list[str] | None = None,
        exiftool_exe_path: str | None = None, 
        sort: Literal['asc', 'desc'] | None = None,
        verbose: bool = False,
        max_files: int | None = None,
    ):
    if not os.path.isdir(root):
        raise ValueError('root must be a directory')
    
    counter = defaultdict(lambda: defaultdict(int))
        
    with exiftool.ExifToolHelper(
            executable=exiftool_exe_path,
            encoding="utf-8",
        ) as et:
        
        files = iterFiles(root)
        if max_files is not None:
            files = list(files)[:max_files
                                ]
        files_metadatas = extractMetadatas(files, et, verbose=verbose)
        for metadatas in tqdm(files_metadatas, desc='Count metadatas:', unit='file', mininterval=1, disable=not verbose):
            for key, values in metadatas.items():
                if keys is not None and key not in keys:
                    continue
                if not isinstance(values, list):
                    values = [values]
                    
                for value in values:
                    counter[key][value] +=1
        
    
    if sort in ("asc", "desc"):
        reverse = sort == "desc"
        
        return {
            key: dict(sorted(sub_dict.items(), key=lambda item: item[1], reverse=reverse))
            for key, sub_dict in sorted(counter.items(), key=lambda item: sum(item[1].values()), reverse=reverse)
        }
    return counter
        
    