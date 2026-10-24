import argparse
import os

from utils.logging_utils import getLogger
from utils.constant import METADATA_KEYS, PLEX_METADATA_KEYS_MODIF, METADATA_KEYS_CATEGORIES
from utils.stat import countMetadatas
from utils.chart import barChart

logger = getLogger(__name__)

def getbarCharts(args):
    os.makedirs(args.output, exist_ok=True)
    
    plex_keys_not_in_keys = [key for key in PLEX_METADATA_KEYS_MODIF.keys() if key not in METADATA_KEYS]
    plex_keys_in_keys = [key for key in PLEX_METADATA_KEYS_MODIF.keys() if key in METADATA_KEYS]
    keys = METADATA_KEYS + plex_keys_not_in_keys
    
    counter = countMetadatas(args.path, keys=keys, exiftool_exe_path=args.exiftool_exe_path, verbose=args.verbose)
    
    categories_key = [k for k in METADATA_KEYS_CATEGORIES if k not in set(plex_keys_in_keys)] + plex_keys_not_in_keys # all categories that have a key plex modify + all new plex keys
    for key in categories_key:
        barChart(key, counter[key], save=os.path.join(args.output, key + '_bar_cat.png'))

    top_n_key = [k for k in METADATA_KEYS if k not in set(METADATA_KEYS_CATEGORIES)]
    for key in top_n_key:
        barChart(f'{key} (top {args.top_n})', counter[key], top_n=args.top_n, save=os.path.join(args.output, key + '_bar_top.png'))
        
    
        
if __name__ == "__main__":
    """ 
    Exemple:
        py scripts/get_charts.py E:/music -v --exiftool_exe_path 'E:\code\format_song_files\exiftool-13.59_64\exiftool.exe'
    """
    parser = argparse.ArgumentParser(description='Convert all musics of a directory or a single file to .opus recursively.')
    
    parser.add_argument("path", type=str, help="Directory or file to process.")
    parser.add_argument("-o", "--output", default="./outputs", help="Directory or file to process.")
    parser.add_argument("-eep", "--exiftool_exe_path", default=None, help="Exiftool executable path.")
    parser.add_argument("-v", "--verbose", action='store_true', help="Verbose come back.")
    parser.add_argument('-tn', '--top_n', default=10, help='For list without quantity or too long display the top n only')
    
    args = parser.parse_args()
    
    getbarCharts(args)