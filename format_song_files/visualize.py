from collections import defaultdict
import matplotlib.pyplot as plt
import matplotlib
from tqdm import tqdm
import numpy as np
import exiftool
import os

# internal
from format_song_files.utils import extractInformation

def barChart(
        root:str, 
        key:str, 
        x_log:bool=True, 
        strict:bool=False, 
        exiftool_exe_path: str | None = None, 
        verbose=1,
        show:bool=False,
        save:str|None=None,
        include_unknow:bool=True,
    ):
    if show is False:
        matplotlib.use("Agg")
    # 'Title', 'Artist', 'Album', 'Year', 'Genre', 'Style', 'Mood', 'Language', 'Country', 'Decade', 'RealGenre'
    counter = defaultdict(int)
    
    with exiftool.ExifToolHelper(
            executable=exiftool_exe_path,
            encoding="utf-8",
        ) as et:
        for file_root, _, files in tqdm(os.walk(root), disable=verbose<1, leave=False, mininterval=1):
            for file in tqdm(files, disable=verbose<2, mininterval=1):
                infos = extractInformation(os.path.join(file_root, file), et)

                values = infos.get(key, None)
                
                if values is None:
                    if strict:
                        raise Exception(f'{key!r} not present in {os.path.join(file_root, file)}')
                    elif include_unknow:
                        values = 'Unknow'
                    else:
                        continue
                
                if isinstance(values, list):
                    for value in values:
                        counter[value] +=1
                else:
                    counter[values] +=1
 
    counter = {k: v for k, v in sorted(counter.items(), key=lambda item: item[1], reverse=True)}

    # Hight adapt depending of the number of categories
    keys, values = [str(k) for k in counter.keys()], list(counter.values())
    fig_height = max(5, len(keys) * 0.4)
    fig, ax = plt.subplots(figsize=(12, fig_height))
    
    
    bars = ax.barh(keys, values, align='center')
    ax.yaxis.set_inverted(True)  # arrange data from top to bottom
    ax.margins(y=0)
    ax.set_xlabel('Number of files')
    ax.set_title(f'Repartition of {key!r} on the server', pad=5, fontsize=15, fontweight="bold")

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.3,
    )
    
    
    # Porcentage on the right of bar
    total = sum(counter.values())
    labels_text = [
        f"{v} ({v / total:.1%})"
        for v in values
    ]
    ax.bar_label(
        bars,
        labels=labels_text,
        padding=5,
        fontsize=9,
    )

    if x_log:
        ax.set_xscale('log')
        
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=10)
    ax.tick_params(axis="x", labelsize=9)
    fig.tight_layout()

        
    if save is not None:
        plt.savefig(save)
        
    if show:
        plt.show()
        
    
    
    return fig