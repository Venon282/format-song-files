from scipy.ndimage import gaussian_filter1d
import matplotlib.pyplot as plt
import numpy as np
import matplotlib
import math

""" TODO

Histogramme des durée des morceaux
Matrice de corelations
Graph de réseau des artistes
Histograme des années et décénis plustot que bar chart
heatmap taille par minute vs duréer du morceau (couleur nb de track dans la région exagone)
"""

TITLE_SIZE = 22
SUB_TITLE_SIZE = 18
LABEL_SIZE = 16
LEGEND_SIZE = 16
TICK_SIZE = 12


def _save(fig, show:bool=False, save:str|None=None, close:bool=True):
    fig.tight_layout()
    
    if save is not None:
        plt.savefig(save)
        
    if show:
        plt.show()
        
    if close:
        plt.close(fig)
        return None
    
    return fig

def barVertChart(
        name:str,
        datas:dict, 
        top_n:int=None,
        x_log:bool=True, 
        show:bool=False,
        save:str|None=None,
        close:bool=True,
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
    ax.set_xlabel('Number of files', fontsize=LABEL_SIZE)
    fig.suptitle(f'Repartition of {name!r} on the server', fontweight="bold", fontsize=TITLE_SIZE)

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
        fontsize=LABEL_SIZE,
    )

    if x_log:
        ax.set_xscale('log')
        
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_visible(False)
    ax.spines["bottom"].set_visible(False)
    ax.tick_params(axis="y", length=0, labelsize=TICK_SIZE)
    ax.tick_params(axis="x", labelsize=TICK_SIZE)
    

    return _save(fig, show, save, close)


def barHoriChart(
    name: str,
    datas: dict,
    y_log:bool=True, 
    show: bool = False,
    save: str | None = None,
    close: bool = True,
    sort: bool = True,
    smoothing_window: int | None = 5,
    bar_width: float | None = None,
    categorical: bool = False,
) -> None:
    """
    Plot a bar chart with optional Gaussian smoothing.

    Numeric keys are used as actual X coordinates. Non-numeric keys
    are displayed as equally spaced categorical positions.

    Parameters
    ----------
    name : str
        X-axis label.
    datas : dict
        Mapping of X coordinates/categories to their quantities.
    show : bool, default=False
        Display the figure.
    save : str | None, default=None
        Path where the figure should be saved.
    close : bool, default=True
        Close the figure after processing.
    sort : bool, default=True
        Sort numeric keys numerically, or categorical keys alphabetically.
        If False, preserve dictionary insertion order.
    smoothing_window : int | None, default=5
        Approximate number of consecutive observations included in
        the Gaussian smoothing kernel. None or 1 disables smoothing.
    bar_width : float | None, default=None
        Bar width in X-axis units. If None, automatically determined
        from the minimum distance between numeric coordinates.
        For categorical data, bars fill their positions.

    Returns
    -------
    None
        Delegates figure handling to _save().
    """
    if smoothing_window is not None and (
        not isinstance(smoothing_window, int) or smoothing_window < 1
    ):
        raise ValueError("smoothing_window must be a positive integer or None")

    if bar_width is not None and bar_width <= 0:
        raise ValueError("bar_width must be positive")

    fig, ax = plt.subplots(figsize=(max(12, len(datas)//5), 8))

    if not datas:
        ax.text(
            0.5, 0.5, "No data available",
            ha="center", va="center",
            transform=ax.transAxes,
        )
    else:
        labels = list(datas.keys())
        values = np.asarray(list(datas.values()), dtype=float)

        if not np.all(np.isfinite(values)):
            raise ValueError("All data values must be finite numbers")

        # Determine whether keys represent numeric coordinates
        try:
            x = np.asarray(labels, dtype=float)
            numeric = np.all(np.isfinite(x))
        except (ValueError, TypeError):
            numeric = False

        # Sort while preserving key/value associations
        if sort:
            order = (
                np.argsort(x, kind="stable")
                if numeric
                else np.argsort([str(k) for k in labels], kind="stable")
            )

            labels = [labels[i] for i in order]
            values = values[order]

            if numeric:
                x = x[order]

        # Categorical coordinates
        if categorical or not numeric:
            x = np.arange(len(values), dtype=float)

        # Numeric coordinates must be unique
        if numeric and len(np.unique(x)) != len(x):
            raise ValueError("Numeric X coordinates must be unique")

        # Determine bar width
        if bar_width is None:
             width = 1.0 if categorical or not numeric else (
                np.min(np.diff(np.sort(x))) if len(x) > 1 else 1.0
            )
        else:
            width = bar_width
        # ax.set_xlim(np.min(x) - width / 2, np.max(x) + width / 2)
        ax.margins(x=0)

        # Bars
        ax.bar(
            x,
            values,
            width=width,
            edgecolor="black",
            zorder=2,
        )

        # Gaussian smoothing
        if smoothing_window is not None and smoothing_window > 1:
            radius = max(1, (smoothing_window - 1) // 2)
            sigma = radius / 2

            smoothed = gaussian_filter1d(
                values,
                sigma=sigma,
                radius=radius,
                mode="nearest",
            )

            ax.plot(
                x,
                smoothed,
                linewidth=2,
                label=f"Gaussian smoothing ({smoothing_window} points)",
                zorder=3,
            )
            ax.legend(fontsize=LEGEND_SIZE)

        # X-axis labels
        ax.set_xticks(x)
        ax.set_xticklabels(
            [str(label) for label in labels],
            rotation=90,
            ha="center",
        )
        
    ax.grid(
        axis="y",
        linestyle="--",
        alpha=0.3,
    )

    ax.tick_params(axis="both", labelsize=TICK_SIZE)
    if y_log:
        from matplotlib.ticker import FuncFormatter
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(
            FuncFormatter(lambda y, _: f"{int(y):,}".replace(",", " "))
        )
    ax.set_xlabel(name, fontsize=LABEL_SIZE)
    ax.set_ylabel("Quantity", fontsize=LABEL_SIZE)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    fig.suptitle(
        f"Histogram of {name!r} on the server",
        fontweight="bold",
        fontsize=TITLE_SIZE,
    )
    
    return _save(fig, show, save, close)