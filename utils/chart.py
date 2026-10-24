import matplotlib.pyplot as plt
import matplotlib


def barChart(
        name:str,
        datas:dict, 
        top_n:int=None,
        x_log:bool=True, 
        show:bool=False,
        save:str|None=None,
    ):
    if show is False:
        matplotlib.use("Agg")
        
    datas = {k:v for k, v in sorted(datas.items(), key= lambda item: item[1], reverse=True)}
    keys, values = [str(k) for k in datas.keys()], list(datas.values())
            
    if top_n is not None:
        keys, values = keys[:top_n], values[:top_n]

        
    
    # Hight adapt depending of the number of categories
    fig_height = max(5, len(keys) * 0.4)
    
    fig, ax = plt.subplots(figsize=(12, fig_height))
    
    bars = ax.barh(keys, values, align='center')
    ax.yaxis.set_inverted(True)  # arrange data from top to bottom
    ax.margins(y=0)
    ax.set_xlabel('Number of files')
    ax.set_title(f'Repartition of {name!r} on the server', pad=5, fontsize=15, fontweight="bold")

    ax.grid(
        axis="x",
        linestyle="--",
        alpha=0.3,
    )
    
    # Porcentage on the right of bar
    total = sum(values)
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