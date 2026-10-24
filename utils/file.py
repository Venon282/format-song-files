import os
import subprocess

# internal
from utils.logging_utils import getLogger

logger = getLogger(__name__)

def iterFiles(path:str):
    for root, _, files in os.walk(path):
        for file in files:
            yield os.path.join(root, file)
            

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