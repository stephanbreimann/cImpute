"""
This is a script for plotting value distributions to compare raw and imputed data
"""
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import seaborn as sns


# Settings
pd.set_option('expand_frame_repr', False)  # Single line print for pd.Dataframe


# I Helper Functions
def plot_settings(fig_format="pdf", verbose=False, grid=False, grid_axis="y"):
    """General plot settings"""
    if verbose:
        print(plt.rcParams.keys)  # Print all plot settings that can be modified in general
    sns.set_context("talk", font_scale=0.7)
    # plt.style.use("Solarize_Light2") # https://matplotlib.org/stable/gallery/style_sheets/style_sheets_reference.html
    # Font settings https://matplotlib.org/3.1.1/tutorials/text/text_props.html
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = "Arial"
    plt.rcParams["axes.labelweight"] = "bold"
    plt.rcParams["axes.titleweight"] = "bold"
    plt.rcParams["axes.labelsize"] = 17  # 13.5
    plt.rcParams["axes.titlesize"] = 16.5  # 15
    if fig_format == "pdf":
        mpl.rcParams['pdf.fonttype'] = 42
    elif "svg" in fig_format:
        mpl.rcParams['svg.fonttype'] = 'none'
    font = {'family': 'Arial',
            "weight": "bold"}
    mpl.rc('font', **font)
    # Error bars
    plt.rcParams["errorbar.capsize"] = 10  # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.errorbar.html
    # Grid
    plt.rcParams["axes.grid.axis"] = grid_axis  # 'y', 'x', 'both'
    plt.rcParams["axes.grid"] = grid
    # Legend
    #plt.rcParams["legend.frameon"] = False
    #plt.rcParams["legend.fontsize"] = "medium"  # "x-small"
    plt.rcParams[
        "legend.loc"] = 'upper right'  # https://matplotlib.org/stable/api/_as_gen/matplotlib.pyplot.legend.html


# II Main Functions
def _plot_scatter(ax=None, df_plot=None, df_imputed=None, cols=None, legend=False, title=None, hue=None):
    """"""
    df = df_plot[cols].T.describe().T
    df.index = df_imputed.index
    df[hue] = df_imputed[hue]
    ax = sns.scatterplot(ax=ax, data=df, x="std", y="mean",
                         hue=hue, size="count", palette="RdBu", alpha=0.75, legend=legend)
    ax.set_xlim(0, 8)
    ax.set_ylim(10, 35)
    ax.set_title(title)
    return ax


def plot_scatter(df_raw=None, df_imputed=None, cols=None, group=None):
    """"""
    args = dict(df_imputed=df_imputed.copy(), cols=cols, hue=f"CS_{group}")
    plt.figure(figsize=(6, 7))
    fig, ax = plt.subplots(1, 2)
    _plot_scatter(ax=ax[0], df_plot=df_raw.copy(), title="Raw", **args)
    sns.despine()
    _plot_scatter(ax=ax[1], df_plot=df_imputed.copy(), title="Imputed", **args, legend=True)
    plt.tight_layout()
    plt.legend(bbox_to_anchor=(1.05, 1), loc=2, borderaxespad=0.)
    fig.suptitle(f"log2 LFQ group {group}", weight="bold", y=1)


def plot_hist(df_raw=None, df_imputed=None, cols=None, d_min=None, up_mnar=None):
    """"""
    plt.figure(figsize=(6, 5))
    sns.histplot(df_imputed[cols].to_numpy().flatten())
    sns.histplot(df_raw[cols].to_numpy().flatten(), color="tab:orange")
    plt.xlabel("log2 LFQ")
    plt.legend(labels=['Imputed', 'Raw'])
    plt.axvline(d_min, color='black', ls="--")
    plt.text(d_min * 1.01, plt.ylim()[1] * 0.95, "Dmin")
    plt.axvline(up_mnar, color='black', ls="--")
    plt.text(up_mnar * 1.01, plt.ylim()[1] * 0.95, "upMNAR")
    sns.despine()
    plt.tight_layout()

