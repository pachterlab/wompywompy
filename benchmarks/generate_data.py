"""Synthetic wide-format categorical data for wompywompy benchmarks.

wompywompy's sorting/coloring cost is driven mainly by:
  - n_categories: distinct values per graphing column. Sets the distance-matrix
    size for neighbornet/tsp. The "tsp" sorting_algorithm is an *exact* DP
    solver (exponential in node count) -- keep n_categories small (~15) when
    including it in a sweep.
  - n_columns: number of graphing columns. Multiplies column-order-optimization
    cost (each column pair gets its own edge-crossing calculation).
  - n_rows: raw observation count. plot_alluvial() collapses rows to unique
    column-combinations before sorting/plotting, so n_rows mainly controls how
    much of the n_categories**n_columns combinatorial space is populated (and
    thus how many alluvia matplotlib ends up drawing).
"""

import numpy as np
import pandas as pd


def make_synthetic_df(n_rows, n_columns, n_categories, seed=0):
    """Generate a random wide-format categorical dataframe.

    Parameters
    ----------
    n_rows : int
        Number of individual observations (rows).
    n_columns : int
        Number of graphing columns to generate (named col_0, col_1, ...).
    n_categories : int
        Number of distinct category values per column.
    seed : int
        RNG seed for reproducibility.

    Returns
    -------
    df : pandas.DataFrame
    graphing_columns : list of str
    """
    rng = np.random.default_rng(seed)
    graphing_columns = [f"col_{i}" for i in range(n_columns)]
    data = {
        col: rng.integers(0, n_categories, size=n_rows).astype(str)
        for col in graphing_columns
    }
    return pd.DataFrame(data), graphing_columns
