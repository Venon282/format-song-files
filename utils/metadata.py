import os
import exiftool
from tqdm import tqdm
from typing import Iterable
from contextlib import contextmanager

from utils.file import batchFiles, iterFiles

# @contextmanager
# def _exiftoolHelper(exiftool_helper:exiftool.ExifToolHelper|None=None, exiftool_exe_path: str| None=None):
#     try:
#         _exiftool_helper = None
#         if exiftool_helper is not None:
#             _exiftool_helper = exiftool_helper  
#         else :
#             _exiftool_helper = exiftool.ExifToolHelper(
#                 executable=exiftool_exe_path,
#                 encoding="utf-8"
#             )
#             _exiftool_helper.run()
#         yield _exiftool_helper
#     finally:
#         if _exiftool_helper is not None and exiftool_helper is None:
#             _exiftool_helper.close()
            
 
# def _parseVerboseOutput(
#     raw_output: str,
#     fallback_paths: list[str],
# ) -> list[dict]:
#     MARKER = "======== "
#     SEPARATOR = " = "
    
#     sections = []
#     current_path = None
#     current_lines = []
#     has_markers = False

#     if len(fallback_paths) > 1:
#         for line in raw_output.splitlines():
#             if line.startswith(MARKER):
#                 has_markers = True

#                 if current_path is not None:
#                     sections.append((current_path, current_lines))

#                 current_path = line[len(MARKER):].strip()
#                 current_lines = []

#             elif current_path is not None:
#                 current_lines.append(line)

#         if current_path is not None:
#             sections.append((current_path, current_lines))

#     # Some single-file outputs may omit the section marker.
#     if not has_markers:
#         if len(fallback_paths) != 1:
#             raise RuntimeError(
#                 "Cannot separate multi-file verbose output."
#             )
#         sections = [(fallback_paths[0], raw_output.splitlines())]

#     results = []

#     for file_path, lines in sections:
#         entry = {"SourceFile": file_path}

#         for line in lines:
#             if SEPARATOR not in line:
#                 continue

#             key, value = line.split(SEPARATOR, 1)
#             key = key.strip().split()[-1]
#             value = value.strip()

#             if value.isdigit():
#                 value = int(value)
#             else:
#                 try:
#                     value = float(value)
#                 except ValueError:
#                     pass

#             if key in entry:
#                 if isinstance(entry[key], list):
#                     entry[key].append(value)
#                 else:
#                     entry[key] = [entry[key], value]
#             else:
#                 entry[key] = value
                
#         results.append(entry)

#     return results
    
# def extractMetadatas(
#     files_paths:Iterable[str] | str,
#     exiftool_helper:exiftool.ExifToolHelper|None=None,
#     exiftool_exe_path: str| None=None, 
#     batch_size: int = 100,
#     verbose:bool=False
# ) -> None:
#     """ 
#     exiftool_exe_path if exiftool_helper is None but not obligate
#     """
    
#     if isinstance(files_paths, str):
#         files_paths = [files_paths]
#     else:
#         files_paths = list(files_paths)
        
#     results = []
#     with _exiftoolHelper(exiftool_helper, exiftool_exe_path) as eh:
#         for start in tqdm(range(0, len(files_paths), batch_size), desc='Extract metadatas:', unit='batch', mininterval=1, disable=not verbose):
#             batch = files_paths[start:start + batch_size]    
            
#             # Get metadatas
#             raw_output = eh.execute(
#                             "-a",
#                             "-v1",
#                             "-ec",
#                             *batch
#                         )
            
#             print(raw_output)
            
#             results.extend(
#                 _parseVerboseOutput(raw_output, batch)
#             )
    
#     return results
    
import re
from collections.abc import Iterable

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


def extractMetadatas(
    files_paths: Iterable[str] | str,
    exiftool_exe_path: str | None = None,
    batch_size: int = 100,
    verbose: bool = False,
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
    with exiftool.ExifToolHelper(
        executable=exiftool_exe_path, 
        encoding="utf-8", 
        common_args=[]
    ) as eh: # can't pass it directly has previous version because need to be sure to overwrite common args
        
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

    return results
