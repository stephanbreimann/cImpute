"""
This is a script for ...
"""
import time
import pandas as pd
import matplotlib.pyplot as plt
from c_impute import cImpute

import c_impute.utils as ut
from c_impute.plotting import plot_settings, plot_hist, plot_scatter


# Settings
pd.set_option('expand_frame_repr', False)  # Single line print for pd.Dataframe


# I Helper Functions


# II Main Functions
def dev():
    """"""

    # Settings
    plot_settings()
    groups = ["A", "B", "C", "D", "E", "F"]
    str_lfq = "log2 LFQ "
    str_ids = "Protein IDs"

    # Creat imputation object
    cimp = cImpute(str_id=str_ids, str_lfq=str_lfq)
    # Load data
    file = "raw_data_proteomics_lfq.xlsx"
    df_raw = pd.read_excel(ut.FOLDER_DATA + file)
    dict_group_cols = cimp.get_dict_groups(df=df_raw, groups=groups)
    all_groups_col = cimp.get_all_group_cols(dict_group_cols=dict_group_cols)

    # Imputation
    loc_up_mnar = 0.2
    d_min, up_mnar, d_max = cimp.get_limits(df=df_raw.copy(),
                                            dict_group_cols=dict_group_cols,
                                            loc_up_mnar=loc_up_mnar)

    df_imputed = cimp.run(df=df_raw.copy(),
                          dict_group_cols=dict_group_cols,
                          min_cs=0.5,
                          loc_up_mnar=loc_up_mnar,
                          std_factor=0.8,
                          n_neigbhors=6)
    df_imputed.to_excel(ut.FOLDER_RESULTS + "cImpute_data_proteomics_lfq.xlsx")
    # Plot histogram
    plot_hist(df_raw=df_raw,
              df_imputed=df_imputed,
              cols=all_groups_col,
              d_min=d_min,
              up_mnar=up_mnar)
    plt.savefig(ut.FOLDER_RESULTS + "cImpute_histogram_proteomics_lfq.png")
    plt.show()
    plt.close()
    # Plot scatter plot for each group
    df_raw_plot = df_raw.set_index(str_ids)
    df_raw_plot = df_raw_plot.sort_index()
    for group in dict_group_cols:
        cols = dict_group_cols[group]
        plot_scatter(df_raw=df_raw_plot, df_imputed=df_imputed, cols=cols, group=group)
        plt.tight_layout()
        plt.savefig(ut.FOLDER_RESULTS + f"cImpute_scatter{group}_proteomics_lfq.png")
        plt.show()
        plt.close()

# III Test/Caller Functions


# IV Main
def main():
    t0 = time.time()
    dev()
    t1 = time.time()
    print("Time:", t1 - t0)


if __name__ == "__main__":
    main()
