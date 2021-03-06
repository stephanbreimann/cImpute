"""
cImpute (conditional Imputation) is a hybrid imputation algorithm for missing values (MVs) in (prote)omics data.
Missing values can be distinguished into three categories as described by Lazar et al., 2016 and Wei et al., 2018
for proteomic data sets as follows:

    a) Missing Completely At Random (MCAR): MVs due to random errors and stochastic fluctuations during process of
        data acquisition. Since MCAR MVs can not be explained by measured intensities, they are uniformly distributed.
    b) Missing At Random (MAR): MVs due to suboptimal data processing and conditional dependencies. MAR is a more
        general class than MCAR, where all MCAR MVs are MAR MVs. The distribution of MAR MVs can just be speculated
        and likely differs highly between experiments.
    c) Missing Not At Random (MNAR): MVs due to experimental bias (i.e., the detection limit in mass-spectrometry
        experiments). Commonly, MNAR MVs are described by a left-censored Gaussian distribution (i.e., the Gaussian
        distribution is truncated on the region of lower abundances, which is the left side of the distribution).

cImpute aims to impute only MVs matching well-defined confidence criteria and consists of following four steps:

    1. Definition of upper bound for MNAR MVs to distinguish between MNAR and MCAR
    2. Classification of MVs for detected proteins in an experimental group
    3. Computation of confidence score (CS)
    4. Group-wise imputation for proteins with CS higher than given threshold

For more details look into the README

"""
import pandas as pd
import numpy as np


from scipy.stats import truncnorm
from sklearn.impute import KNNImputer

# TODO a) add check functions for interface
# TODO b) generalize (e.g., lfq -> intensities, test with other input)
# TODO c) optimize (e.g., optimize of clusters for KNN via Silhouette score)
# TODO d) testing
# TODO e) extend documentation & create google colab
# TODO f) benchmarking (ring trail, standards (Tenzer Lab), existing artificial benchmark sets (c.f. publication)
# TODO g) Extend to other omics data
# TODO h) Extend to peptide level

# Settings
pd.set_option('expand_frame_repr', False)  # Single line print for pd.Dataframe

# Constants
STR_MCAR = "MCAR"
STR_MNAR = "MNAR"
STR_MAR = "MAR"
STR_NM = "NM"
LIST_MV_CLASSES = [STR_MCAR, STR_MNAR, STR_MAR, STR_NM]
STR_CS = "CS"
STR_MV_LABELS = "labels"


# I Helper Functions
def _compute_cs(vals=None, mv_class=None, n=None):
    """Compute confidence score (CS) depending on missing value category and
    proportion of missing values"""
    count_nan = lambda val: len([x for x in val if str(x) == "nan"])
    if mv_class == STR_NM:
        return 1
    elif mv_class == STR_MAR:
        return 0
    elif mv_class == STR_MCAR:
        return round((n - count_nan(vals)) / n, 2)
    elif mv_class == STR_MNAR:
        return round(count_nan(vals) / n, 2)


def _impute_mnr(df=None, std_factor=0.5, d_min=None, up_mnar=None):
    """MinProb imputation as suggested by Lazar et al., 2016

    Arguments
    --------
    df: DataFrame
        DataFrame with missing values just classified as MNAR
    std_factor: int, default = 0.5
        Factor to control size of standard deviation of distribution relative to distance of upMNAR and Dmin.

    Notes
    -----
    std = (up_mnar - d_min) * std_factor

    See also
    --------
    https://www.rdocumentation.org/packages/imputeLCMD/versions/2.0/topics/impute.MinProb
    https://bioconductor.org/packages/release/bioc/vignettes/DEP/inst/doc/MissingValues.html
    """
    df = df.copy()
    d1, d2 = df.shape
    std = (up_mnar - d_min) * std_factor   # Standard deviation (spread, scale, or "width")
    # Generate random numbers using truncated (left-censored) normal distribution
    vals = truncnorm.rvs(a=0, b=1, size=d1*d2, loc=d_min, scale=std).reshape((d1, d2))
    mask = df.isnull()
    df[mask] = vals
    return df


def _impute_mcar(df=None, n_neighbors=6):
    """KNN imputation via sklearn implementation

    Arguments
    ---------
    df: DataFrame
        DataFrame with missing values just classified as MNAR
    n neighbors: int, default=6 (Liu and Dongre, 2020)
        Number of neighboring samples to use for imputation
    """
    imputer = KNNImputer(n_neighbors=n_neighbors)
    X = np.array(df)
    index, cols = df.index, df.columns
    X = imputer.fit_transform(X)
    df = pd.DataFrame(X, columns=cols, index=index)
    return df


def _impute(df=None, mv_class=None, d_min=None, up_mnar=None, std_factor=0.5, n_neighbors=6):
    """Wrapper for imputation methods applied on an experimental group"""
    if mv_class == STR_NM:
        return df
    elif mv_class == STR_MAR:
        return df
    elif mv_class == STR_MCAR:
        return _impute_mcar(df=df, n_neighbors=n_neighbors)
    elif mv_class == STR_MNAR:
        return _impute_mnr(df=df, d_min=d_min, std_factor=std_factor, up_mnar=up_mnar)


# II Main Functions
def get_up_mnar(df=None, loc_up_mnar=0.1):
    """Get upper bound for MNAR MVs for whole data set"""
    d_min = df.min().min()  # Detection limit
    d_max = df.max().max()  # Largest detected value
    dr = d_max - d_min      # Detection range
    up_mnar = d_min + loc_up_mnar * dr   # Upper MNAR border
    return d_min, up_mnar


def classify_of_mvs(df_group=None, up_mnar=None):
    """Classification of missing values for given protein intensities of an experimental group"""
    n_groups = len(list(df_group))
    mv_classes = []     # NaN Classes
    for i, row in df_group.iterrows():
        n_nan = row.isnull().sum()
        n_higher_up_mnar = np.array((row > up_mnar)).sum()
        n_lower_or_equal_up_mnar = np.array((row <= up_mnar)).sum()
        # MNAR (Missing Not At Random)
        if n_lower_or_equal_up_mnar + n_nan == n_groups:
            mv_classes.append(STR_MNAR)
        # MCAR (Missing Completely At Random)
        elif n_higher_up_mnar + n_nan == n_groups:
            mv_classes.append(STR_MCAR)
        # NM (No Missing values)
        elif n_higher_up_mnar + n_lower_or_equal_up_mnar == n_groups:
            mv_classes.append(STR_NM)
        # MAR (Missing At Random)
        else:
            mv_classes.append(STR_MAR)
    return mv_classes


def compute_cs(df_group=None, mv_classes=None):
    """Computation of confidence scores depending on missing value classification and proportion of missing values"""
    n = len(list(df_group))
    dict_prot_cs = {}
    for mv_class in LIST_MV_CLASSES:
        mask = [True if l == mv_class else False for l in mv_classes]
        df = df_group[mask]
        for entry, row in df.iterrows():
            cs = _compute_cs(vals=list(row), mv_class=mv_class, n=n)
            dict_prot_cs[entry] = cs
    list_cs = [dict_prot_cs[entry] for entry in df_group.index]
    return list_cs


def impute(df_group=None, mv_classes=None, list_cs=None, min_cs=0.5, d_min=None, up_mnar=None,
           n_neighbors=5, std_factor=0.5):
    """Group-wise imputation over whole data set"""
    df_group = df_group.copy()
    args = dict(n_neighbors=n_neighbors, std_factor=std_factor, d_min=d_min, up_mnar=up_mnar)
    for mv_class in LIST_MV_CLASSES:
        mask = np.array([True if (l == mv_class and cs >= min_cs) else False
                         for l, cs in zip(mv_classes, list_cs)])
        df_group[mask] = _impute(df=df_group[mask], mv_class=mv_class, **args)
    return df_group


# Wrapper
class cImpute:
    """Hybrid imputation algorithm for missing values (MVs) in (prote)omics data.

    Arguments
    ---------
    str_id: str, default = "Protein IDs"
        Column name of entry ids of input DataFrame for associated methods
    str_lfq: str, default = "log2 LFQ"
        Common substring of intensity columns of input DataFrame for associated methods

    """
    def __init__(self, str_id="Protein IDs", str_lfq="log2 LFQ"):
        self.list_mv_classes = LIST_MV_CLASSES
        self.str_id = str_id
        self.str_lfq = str_lfq

    def get_dict_groups(self, df=None, groups=None, group_to_col=True):
        """Get dictionary with groups from df based on lfq_str and given groups

        Arguments
        --------
        df: DataFrame
            DataFrame containing quantified features including missing values
        groups: list of str
            List with group names
        group_to_col: bool, default = True
            Decide whether group columns (values) should be returned as list

        Return
        ------
        dict_col_group: dict
            Dictionary assigning column names (keys) to group names (values) if group_to_col=False
        dict_group_cols: dict
            Dictionary assigning groups (keys) to list of column names (values) if group_to_col=True
        """
        dict_col_group = {}
        for col in list(df):
            if self.str_lfq in col:
                col_wo_lfq_str = col.replace(self.str_lfq, "")
                for group in groups:
                    if group in col_wo_lfq_str:
                        dict_col_group[col] = group
        if group_to_col:
            dict_group_cols = {g: [k for k, v in dict_col_group.items() if v == g] for g in groups}
            return dict_group_cols
        return dict_col_group

    @staticmethod
    def get_all_group_cols(dict_group_cols=None):
        """Retrieve all columns from group dictionary

        Arguments
        ---------
        dict_group_cols: dict
            Dictionary assigning groups (keys) to list of column names (values)

        Return
        ------
        all_group_cols: list
            List with all columns of input Data Frame from cImpute.get_dict_groups containing intensity values.
        """
        all_group_cols = []
        for group in dict_group_cols:
            all_group_cols.extend(dict_group_cols[group])
        return all_group_cols

    def get_limits(self, df=None, loc_up_mnar=0.1, dict_group_cols=None):
        """Get minimum of detected values (d_min, i.e., detection limit), upper bound of MNAR MVs (up_mnar),
        and maximum of detected values (d_max).

        Arguments
        ---------
        df: DataFrame
            DataFrame containing quantified features including missing values
        loc_up_mnar: int, default=0.1, [0-1]
            Location factor for the upMNAR given as relative proportion of the detection range
        dict_group_cols: dict
            Dictionary assigning groups (keys) to list of column names (values)

        Return
        ------
        d_min: int
            Minimum of detected values
        up_mnar: int
            upper bound of MNAR MVs
        d_max: int
            Maximum of detected values
        """
        df = df.copy()
        all_group_cols = self.get_all_group_cols(dict_group_cols=dict_group_cols)
        d_min, up_mnar = get_up_mnar(df=df[all_group_cols], loc_up_mnar=loc_up_mnar)
        d_max = df[all_group_cols].max().max()
        return d_min, up_mnar, d_max

    def run(self, df=None, dict_group_cols=None, loc_up_mnar=0.2, min_cs=0.5, std_factor=0.8, n_neigbhors=6):
        """Hybrid method for imputation of omics data called conditional imputation (cImpute)
        using MinProb for MNAR (Missing Not at Random) missing values and KNN imputation for
        MCAR (Missing completely at Random) missing values.

        Arguments
        --------
        df: DataFrame
            DataFrame containing quantified features including missing values
        dict_group_cols: dict
            Dictionary for groups to list of columns containing intensity values for group.
        min_cs: int, default 0.5 [0-1]
            Minimum of confidence score used for selecting values for protein in groups to apply imputation on.
        loc_up_mnar: int, default 0.25 [0-1]
            Factor to determine the location of the upper detection limit bound. In percent of total value range.
        std_factor: int, default = 0.5 (MinProb parameter)
            Factor to control size of standard deviation of left-censored distribution
            relative to distance of upMNAR and Dmin.
        n_neigbhors: int, default=6 (KNN imputation parameter)
            Number of neighboring samples to use for imputation.

        Return
        ------
        df_imputed: DataFrame
            DataFrame with (a) imputed intensities values and (b) group-wise confidence score and NaN classification.
        """
        df = df.copy()
        all_group_cols = self.get_all_group_cols(dict_group_cols=dict_group_cols)
        d_min, up_mnar = get_up_mnar(df=df[all_group_cols], loc_up_mnar=loc_up_mnar)
        # TODO change to numpy Arrays & compute summary statistic (n MVs per class and group)
        list_df_groups = []
        list_mv_classes = []
        cs_vals = []
        for group in dict_group_cols:
            cols = dict_group_cols[group]
            df_group = df[cols]
            mv_classes = classify_of_mvs(df_group=df_group, up_mnar=up_mnar)
            list_cs = compute_cs(df_group=df_group, mv_classes=mv_classes)
            df_group = impute(df_group=df_group, mv_classes=mv_classes, list_cs=list_cs,
                              min_cs=min_cs,
                              d_min=d_min, up_mnar=up_mnar,
                              std_factor=std_factor,
                              n_neighbors=n_neigbhors)
            list_df_groups.append(df_group)
            list_mv_classes.append(mv_classes)
            cs_vals.append(list_cs)
        # Merge imputation for all groups
        df_imputed = pd.concat(list_df_groups, axis=1)
        # Add aggregated CS values (mean and std)
        cs_means = np.array(cs_vals).mean(axis=0).round(2)
        cs_stds = np.array(cs_vals).std(axis=0).round(2)
        df_imputed.insert(len(list(df_imputed)), "CS_MEAN", cs_means)
        df_imputed.insert(len(list(df_imputed)), "CS_STD", cs_stds)
        # Add  CS values per group
        df_cs = pd.DataFrame(cs_vals).T
        df_cs.columns = [f"CS_{group}" for group in dict_group_cols]
        df_cs.index = df.index
        df_nan = pd.DataFrame(list_mv_classes).T
        df_nan.columns = [f"NaN_{group}" for group in dict_group_cols]
        df_nan.index = df.index
        df_imputed = pd.concat([df_imputed, df_cs, df_nan], axis=1)
        return df_imputed
