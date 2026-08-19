import os
import json
import toml
import logging
import exiftool
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

def convertToOpus(file_path: str, bitrate: str = "160k") -> str:
    """
    Converts an audio file to Opus format if it isn't already .opus.
    Returns the path to the .opus file.
    """
    path = Path(file_path)
    
    # Skip if it is already an Opus file
    if path.suffix.lower() == ".opus":
        return str(path)

    output_path = path.with_suffix(".opus")

    # Command to convert via FFmpeg
    cmd = [
        "ffmpeg",
        "-y",                   # Overwrite output file if it exists
        "-i", str(path),        # Input file
        "-c:a", "libopus",     # Audio codec
        "-b:a", bitrate,        # Target bitrate (120k-160k is near transparent for music)
        "-v", "quiet",          # Suppress standard logging
        "-stats",               # Keep progress output clean
        str(output_path)
    ]

    try:
        subprocess.run(cmd, check=True)
        
        # Remove the old file (e.g., .m4a or .mp3) after successful conversion
        os.remove(path)
        print(f"Converted: {path.name} -> {output_path.name}")
        return str(output_path)
        
    except subprocess.CalledProcessError as e:
        print(f"Error converting {path.name}: {e}")
        # Cleanup output file if conversion failed
        if output_path.exists():
            os.remove(output_path)
        raise

def readConfig(path:str = './config.toml') -> dict:
    with open(path, 'r', encoding='utf-8') as f:
        return toml.load(f)
    
def extractInformation(
    file_path:str,
    exiftool_helper:exiftool.ExifToolHelper|None=None,
    exiftool_exe_path: str| None=None, 
) -> None:
    """ 
    exiftool_exe_path if exiftool_helper is None but not obligate
    """
    _exiftool_helper = None
    try:
        if exiftool_helper is not None:
            _exiftool_helper = exiftool_helper  
        else :
            _exiftool_helper = exiftool.ExifToolHelper(
                executable=exiftool_exe_path,
                encoding="utf-8"
            )
            _exiftool_helper.run()
            
        # Get metadatas
        raw_output = _exiftool_helper.execute("-a", file_path)
        
        entry = {"SourceFile": file_path}
        for line in raw_output.splitlines():
            if not " : " in line:
                continue
            
            left, value = line.split(" : ", 1)
            left = left.strip()
            value = value.strip()
            
            if value.isdigit():
                value = int(value)
                
            if left.startswith('[') and ']' in left:
                group_end = left.index(']')
                group = left[1:group_end].strip()
                tag = left[group_end+1:].strip()
                key = f'{group}:{tag}'
                
                if key in entry:
                    if isinstance(entry[key], list):
                        entry[key].append(value)
                    else:
                        entry[key] = [entry[key], value]
                else:
                    entry[key] = value
        return entry
    finally:
        if _exiftool_helper is not None and exiftool_helper is None:
            _exiftool_helper.close()
            
            
def findValuesInDict(
    data: dict,
    target_key: str,
) -> list:
    """
    Recursively searches for target_key inside a nested dictionary.

    It also searches dictionaries contained inside lists.

    Example:

        {
            "metadata": {
                "audio": {
                    "genre": "NightCore"
                }
            }
        }

    Searching for "genre" returns:

        ["NightCore"]
    """

    results = []

    for current_key, value in data.items():

        # Current key matches
        if current_key == target_key:
            results.append(value)

        # Nested dictionary
        if isinstance(value, dict):
            results.extend(
                findValuesInDict(
                    value,
                    target_key
                )
            )

        # List containing dictionaries
        elif isinstance(value, list):

            for item in value:
                if isinstance(item, dict):
                    results.extend(
                        findValuesInDict(
                            item,
                            target_key
                        )
                    )

    return results


def flattenValues(values: list) -> list:
    """
    Recursively flattens lists.

    Example:

        [
            "Rock",
            ["Electronic", "NightCore"],
            [["Dance"]]
        ]

    becomes:

        [
            "Rock",
            "Electronic",
            "NightCore",
            "Dance"
        ]
    """

    result = []

    for value in values:
        if isinstance(value, list):
            result.extend(
                flattenValues(value)
            )

        else:
            result.append(value)

    return result


def valueMatchesTags(
    values: list,
    tags: list[str],
    operator: str,
) -> bool:
    """
    Checks whether values match the requested tags.
    """

    values = flattenValues(values)

    if operator == "or":
        return any(
            tag in values
            for tag in tags
        )

    if operator == "and":
        return all(
            tag in values
            for tag in tags
        )

    raise ValueError(
        f"Unknown tag operator: {operator}"
    )


def extractInfosWithTags(
    dir_path: str,
    key_value: dict[str, str | list[str]],
    key: str | None = None,
    tag_operator: str = "or",
    key_operator: str = "and",
    recursive: bool = False,
    exiftool_exe_path: str | None = None,
    verbose: bool = True,
) -> list[dict]:
    """
    Searches for files whose information matches the specified tags.

    key_value:
        {
            "Key1": "value",
            "Key2": ["value1", "value2"],
        }

    key:
        If None, all keys from key_value are used.
        Otherwise, only the specified key is used.

    tag_operator:
        Operator between tags within the same key:
            "or"
            "and"

    key_operator:
        Operator between different keys:
            "or"
            "and"

    recursive:
        If True, searches recursively inside subdirectories.

    The key search itself is also recursive inside nested dictionaries
    returned by extractInformation().
    """

    
    # Normalize key values
    normalized_key_value = {
        k: [v] if isinstance(v, str) else v
        for k, v in key_value.items()
    }

    
    # Restrict to one key if requested
    if key is not None:

        if key not in normalized_key_value:
            raise KeyError(
                f"Unknown key: {key}"
            )

        normalized_key_value = {
            key: normalized_key_value[key]
        }

    
    # Validate operators
    if tag_operator not in ("or", "and"):
        raise ValueError(
            f"Unknown tag operator: {tag_operator}"
        )

    if key_operator not in ("or", "and"):
        raise ValueError(
            f"Unknown key operator: {key_operator}"
        )

    
    # Prepare file iterator
    if recursive:
        entries = (
            os.path.join(root, filename)
            for root, _, filenames in os.walk(dir_path)
            for filename in filenames
        )
    else:
        entries = (
            entry.path
            for entry in os.scandir(dir_path)
            if entry.is_file()
        )

    
    # Search
    files_infos = []

    with exiftool.ExifToolHelper(
        executable=exiftool_exe_path,
        encoding="utf-8"
    ) as et:

        for file_path in entries:

            # Extract metadata
            try:
                infos = extractInformation(
                    file_path,
                    exiftool_helper=et
                )

            except Exception as e:
                logger.error(
                    "Unable to extract information from %s: %s",
                    file_path,
                    e
                )
                continue

            # Check every requested key
            key_results = []

            for info_key, tags in normalized_key_value.items():

                # Recursively search the key inside infos
                found_values = findValuesInDict(
                    infos,
                    info_key
                )

                # Key does not exist anywhere
                if not found_values:
                    print(json.dumps(infos, indent=4))
                    raise
                    if verbose:
                        logger.warning(
                            "Key %s is not present in %s",
                            info_key,
                            os.path.basename(file_path)
                        )

                    key_results.append(False)
                    continue

                
                # Check tags
                key_match = valueMatchesTags(
                    found_values,
                    tags,
                    tag_operator
                )

                key_results.append(
                    key_match
                )

            # Combine keys
            if key_operator == "or":

                file_match = any(
                    key_results
                )
            else:
                file_match = all(
                    key_results
                )

            # Keep file
            if file_match:
                files_infos.append(
                    infos
                )

    return files_infos

def infosSingleFilter(infos:list[dict], key:str) -> list:
    result = []
    for info in infos:
        value = info.get(key, None)
        
        if value:
            result.append(value)
            
    return result
   
        
        
    