import os
import re
import exiftool
import itertools
from tqdm import tqdm
from typing import Iterable
from collections.abc import Iterable
from contextlib import contextmanager
from concurrent.futures import ProcessPoolExecutor, as_completed

from utils.file import batchFiles, iterFiles


_COPY_RE = re.compile(r"^Copy(\d+)$")


def _parseJsonEntry(raw: dict) -> dict:
    """{'Vorbis:Copy1:Genre': 'J-Pop', 'Vorbis:Genre': 'Pop'} -> {'Genre': ['J-Pop', 'Pop']}"""
    collected: dict[str, list[tuple[float, object]]] = {}

    for full_key, value in raw.items():
        if full_key == "SourceFile":
            continue

        *groups, tag = full_key.split(":")

        copy_rank = float("inf")  # pas de "CopyN" => dernière occurrence
        for g in groups:
            m = _COPY_RE.match(g)
            if m:
                copy_rank = int(m.group(1))
                break

        collected.setdefault(tag, []).append((copy_rank, value))

    entry = {"SourceFile": raw.get("SourceFile")}

    for tag, items in collected.items():
        items.sort(key=lambda x: x[0])
        values = []
        for _, v in items:
            values.extend(v if isinstance(v, list) else [v])
        entry[tag] = values[0] if len(values) == 1 else values

    return entry

def _extractMetadatas(batch, exiftool_exe_path):
    with exiftool.ExifToolHelper(
        executable=exiftool_exe_path, 
        encoding="utf-8", 
        common_args=[]
    ) as eh:
        raw = eh.execute_json(
            "-a",
            "-G1:4",
            "-charset", "exiftool=utf8",
            *batch,
        )
        return [_parseJsonEntry(r) for r in raw]

def extractMetadatas(
    files_paths: Iterable[str] | str,
    exiftool_exe_path: str | None = None,
    batch_size: int = 100,
    verbose: bool = False,
    max_workers: int | bool = 0,
) -> list[dict]:
    if isinstance(files_paths, str):
        if os.path.isfile(files_paths):
            files_paths = [files_paths]
        elif os.path.isdir(files_paths):
            files_paths = list(iterFiles(files_paths))
        else:
            raise Exception(f'WTF is that path ??? {files_paths}')
    else:
        files_paths = list(files_paths)

    results = []
    
    
    # can't pass it directly has previous version because need to be sure to overwrite common args
    if max_workers == 0:
        with exiftool.ExifToolHelper(
            executable=exiftool_exe_path, 
            encoding="utf-8", 
            common_args=[]
        ) as eh: 
            for start in tqdm(
                range(0, len(files_paths), batch_size),
                desc="Extract metadatas:", unit="batch",
                mininterval=1, disable=not verbose,
            ):
                batch = files_paths[start:start + batch_size]
                
                raw = eh.execute_json(
                    "-a",
                    "-G1:4",
                    "-charset", "exiftool=utf8",
                    *batch,
                )

                results.extend(_parseJsonEntry(r) for r in raw)
    else:
        with ProcessPoolExecutor(max_workers=max_workers) as executor: # can't pass it directly has previous version because need to be sure to overwrite common args
                    
            futures = {
                executor.submit(_extractMetadatas, files_paths[start:start + batch_size], exiftool_exe_path): i
                for i, start in enumerate(range(0, len(files_paths), batch_size))
            }
            
            results = [None] * len(futures)
            
            for future in tqdm(as_completed(futures), total=len(futures), desc="Extract metadatas:", unit="batch",mininterval=1, disable=not verbose):
                results[futures[future]] = future.result()
        
            results = list(itertools.chain.from_iterable(results))
            
    return results
