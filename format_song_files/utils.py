import os
import toml
import subprocess
from pathlib import Path

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