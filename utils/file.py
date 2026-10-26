import os
import re
import shutil
import itertools
import subprocess
from collections.abc import Generator, Iterable

# internal
from utils.logging_utils import getLogger

logger = getLogger(__name__)

def iterFiles(path:str) -> Generator[str]:
    for root, _, files in os.walk(path):
        for file in files:
            yield os.path.join(root, file)
            
def batchFiles(path:str, batch_size: int) -> Generator[list[str], None, None]:
    if batch_size < 1:
        raise ValueError(f'batch_size must be at least 1, got {batch_size}.')

    it = iterFiles(path)

    while True:
        batch = list(itertools.islice(it, batch_size))

        if not batch:
            break

        yield batch
            

def fileToOpus(file_path: str, bitrate: str = "160k") -> str:
    """
    Converts an audio file to Opus format if it isn't already .opus.
    Returns the path to the .opus file.
    """
    # Skip if it is already an Opus file
    if os.path.splitext(file_path)[1].lower() == ".opus":
        return file_path

    output_path = os.path.splitext(file_path)[0] + '.opus'

    # Command to convert via FFmpeg
    cmd = [
        "ffmpeg",
        "-y",                   # Overwrite output file if it exists
        "-i", file_path,        # Input file
        "-c:a", "libopus",      # Audio codec
        "-b:a", bitrate,        # Target bitrate (120k-160k is near transparent for music)
        "-v", "quiet",          # Suppress standard logging
        "-stats",               # Keep progress output clean
        output_path
    ]

    try:
        subprocess.run(cmd, check=True)
        
        # Remove the old file (e.g., .m4a or .mp3) after successful conversion
        os.remove(file_path)
        return output_path
        
    except subprocess.CalledProcessError as e:
        logger.error(f"Error converting {os.path.basename(file_path)}: {e}")
        # Cleanup output file if conversion failed
        if output_path.exists():
            os.remove(output_path)
        raise


def deleteEmptyFolders(root):
    deleted = set()
    
    for current_dir, subdirs, files in os.walk(root, topdown=False):
        still_has_subdirs = False
        for subdir in subdirs:
            if os.path.join(current_dir, subdir) not in deleted:
                still_has_subdirs = True
                break
    
        if not any(files) and not still_has_subdirs:
            os.rmdir(current_dir)
            deleted.add(current_dir)

    return deleted

def flattenDir(path: str):
    path = os.path.abspath(os.path.normpath(path))
    
    for file_path in iterFiles(path):
        file_path = os.path.abspath(os.path.normpath(file_path))
        file_dir, file_name = os.path.split(file_path)
        
        # Already at the root
        if file_dir == path:
            continue
        
        destination = os.path.join(path, file_name)
        
        # Avoid overwriting an existing file
        if os.path.exists(destination):
            logger.warning(
                f"Cannot move {file_name}: destination already exists"
            )
            continue
        
        try:
            shutil.move(file_path, os.path.join(path, file_name))
        except PermissionError as e:
            logger.error(f'Impossible to move {file_name}: {e}')
            continue
    
    deleteEmptyFolders(path)
    
def sanitizeComponent(name: str, default: str = "Unknown") -> str:
    """Removes forbidden Windows characters and strips trailing dots/spaces."""
    if not name:
        return default
    
    # Remove Windows forbidden characters: < > : " / \ | ? *
    clean = re.sub(r'[<>:"/\\|?*]', '', str(name))
    
    # Windows strictly forbids folder/file names ending with spaces or dots
    clean = clean.rstrip('. ')
    
    return clean if clean else default
    
def sanitizeFullPath(path: str) -> str:
    """Safely sanitizes every folder and file name in a full path string."""
    drive, path_tail = os.path.splitdrive(path)
    
    # Split path by any slashes
    parts = re.split(r'[/\\]+', path_tail)
    
    # Sanitize each segment independently
    cleaned_parts = [sanitizeComponent(p) for p in parts if p]
    return drive + os.sep + os.sep.join(cleaned_parts)
    
def getDestination(music_root:str, file_path: str, file_metadatas: dict):
    """
    Path is main artist/album/file
    """
    def _helper(keys:list, default: str='Unknow'):
        # Get the element
        element = None
        for key in keys:
            element = file_metadatas.get(key, None)
            if element is not None:
                break
        else:
            element = default
        
        # If more than one, select the first. Suppose to be the main one
        if isinstance(element, list):
            element = element[0]
            
        return re.sub(r'[<>:"/\\|?*]', "", str(element)) 
            
    artist = _helper(['album_artist', 'AlbumArtist', 'artist', 'Artist'])    
    album = _helper(['album', 'Album'])
    
    return sanitizeFullPath(os.path.join(music_root, artist, album, os.path.basename(file_path)))
        
    