import pytest
import pandas as pd
import numpy as np
import random
import matplotlib.pyplot as plt
from wompywompy import plot_alluvial
from wompywompy.wompwomp import data_sort, determine_crossing_edges

# establish baseline (starting in project root): pytest --mpl-generate-path=tests/baseline
# compare against baseline: pytest --mpl --mpl-results-path=tests/results --mpl-generate-summary=html

@pytest.fixture(autouse=True)
def set_global_random_seed():
    random.seed(42)
    np.random.seed(42)

@pytest.fixture
def ungrouped_df():
    df = pd.DataFrame({
        "tissue": [
            "BRAIN", "BRAIN", "BRAIN",
            "STOMACH", "STOMACH", "STOMACH", "STOMACH", "STOMACH", "STOMACH",
            "HEART", "HEART", "HEART", "HEART", "HEART", "HEART", "HEART",
            "T CELL", "T CELL",
            "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL",
        ],
        "cluster": [
            1, 1, 2,
            1, 2, 2, 2, 2, 2,
            1, 3, 3, 3, 3, 3, 3,
            4, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4,
        ]
    })

    # Convert numeric columns to pandas Categorical with sorted levels
    for col in df.select_dtypes(include=["int", "float"]).columns:
        levels = sorted(df[col].unique())
        df[col] = pd.Categorical(df[col], categories=levels, ordered=True)

    return df

@pytest.fixture
def clus_df_gather(ungrouped_df):
    clus_df_gather = (
        ungrouped_df.groupby(list(ungrouped_df.columns))
          .size()
          .reset_index(name="value")
    )

    return clus_df_gather

@pytest.mark.mpl_image_compare
def test_plot_alluvial_ungrouped_nosort_nocolor(ungrouped_df):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=ungrouped_df,
        graphing_columns=graphing_columns,
        sorting_algorithm="none",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_grouped_nosort_nocolor(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="none",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_grouped_nosort_nocolor_alluvial_colored(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="none",
        match_colors=False,
        color_alluvium=True
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_greedy_fixed_column(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="greedy",
        fixed_column="tissue",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_greedy(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="greedy",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_neighbornet(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="neighbornet",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_tsp(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="tsp",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_colormatch(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="none",
        match_colors=True,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.fixture
def more_neighbornet_2_layer_df():
    df = pd.DataFrame({
        "tissue": [
            1, 1, 1,
            2, 2, 2, 2, 2, 2,
            3, 3, 3, 3, 3, 3, 3,
            4, 4,
            5, 5, 5, 5, 5, 5, 5, 5, 5
        ],
        "cluster": [
            6, 6, 7,
            6, 7, 7, 7, 7, 7,
            6, 8, 8, 8, 8, 8, 8,
            8, 8,
            8, 8, 8, 8, 8, 8, 8, 8, 8
        ]
    })
    graphing_columns = ["tissue", "cluster"]
    return df, graphing_columns


@pytest.fixture
def more_neighbornet_3_layer_df():
    df = pd.DataFrame({
        "tissue": [
            "BRAIN", "BRAIN", "BRAIN",
            "STOMACH", "STOMACH", "STOMACH", "STOMACH", "STOMACH", "STOMACH",
            "HEART", "HEART", "HEART", "HEART", "HEART", "HEART", "HEART",
            "T CELL", "T CELL",
            "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL", "B CELL"
        ],
        "cluster": [
            1, 1, 2,
            1, 2, 2, 2, 2, 2,
            1, 3, 3, 3, 3, 3, 3,
            4, 4,
            4, 4, 4, 4, 4, 4, 4, 4, 4
        ],
        "sex": [
            "male", "female", "male",
            "female", "male", "female", "female", "male", "female",
            "male", "female", "male", "female", "male", "female", "male",
            "female", "male",
            "male", "male", "male", "male", "male", "male", "male", "male", "male"
        ]
    })
    graphing_columns = ["tissue", "cluster", "sex"]
    return df, graphing_columns

@pytest.mark.mpl_image_compare
def test_more_neighbornet_2layer_unsorted(more_neighbornet_2_layer_df):
    df, graphing_columns = more_neighbornet_2_layer_df
    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm="none",
        coloring_algorithm="left",
        color_alluvium=True,
        optimize_column_order=False
    )
    fig = fig[0]  # unpack tuple -> fig
    return fig

@pytest.mark.mpl_image_compare
def test_more_neighbornet_2layer_neighbornet(more_neighbornet_2_layer_df):
    df, graphing_columns = more_neighbornet_2_layer_df
    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm="neighbornet",
        color_alluvium=True,
        optimize_column_order=False
    )
    fig = fig[0]
    return fig

@pytest.mark.mpl_image_compare
def test_more_neighbornet_2layer_neighbornet_optcolumns(more_neighbornet_2_layer_df):
    df, graphing_columns = more_neighbornet_2_layer_df
    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm="neighbornet",
        color_alluvium=True,
        optimize_column_order=True
    )
    fig = fig[0]
    return fig


@pytest.mark.mpl_image_compare
def test_more_neighbornet_3layer_unsorted(more_neighbornet_3_layer_df):
    df, graphing_columns = more_neighbornet_3_layer_df
    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm="none",
        color_alluvium=True,
        optimize_column_order=False
    )
    fig = fig[0]
    return fig

@pytest.mark.mpl_image_compare
def test_more_neighbornet_3layer_neighbornet(more_neighbornet_3_layer_df):
    df, graphing_columns = more_neighbornet_3_layer_df
    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm="neighbornet",
        color_alluvium=True,
        optimize_column_order=False
    )
    fig = fig[0]
    return fig

@pytest.mark.mpl_image_compare
def test_more_neighbornet_3layer_neighbornet_optcolumns(more_neighbornet_3_layer_df):
    df, graphing_columns = more_neighbornet_3_layer_df
    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm="neighbornet",
        color_alluvium=True,
        optimize_column_order=True
    )
    fig = fig[0]
    return fig

def test_objective_more_tsp_3layer_unsorted(more_neighbornet_3_layer_df):
    df, graphing_columns = more_neighbornet_3_layer_df
    df = df.groupby(graphing_columns).size().reset_index(name="value")

    graphing_columns,order_dict = data_sort(
        df=df,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="none",
        optimize_column_order=False,
    )

    num = determine_crossing_edges(df, graphing_columns=graphing_columns, order_dict=order_dict, col_weights="value")

    # Was 96 before the within-stratum ordering in _plot_alluvium was made a
    # fully-specified total order (current axis, then nearest-right axes, then
    # nearest-left axes), matching make_lode_df() in the R package. See wompwomp S1.
    assert num == 77


def _clustered_df(n_cols, seed=0):
    rng = np.random.default_rng(seed)
    latent = rng.integers(0, 4, 400)
    data = {}
    for i in range(n_cols):
        labels = rng.permutation(list("ABCD"))
        noisy = np.where(rng.random(400) < 0.8, latent, rng.integers(0, 4, 400))
        data[f"method{i + 1}"] = labels[noisy]
    df = pd.DataFrame(data)
    cols = list(df.columns)
    return df.groupby(cols).size().reset_index(name="value"), cols


@pytest.mark.parametrize("n_cols", [2, 3, 4])
@pytest.mark.parametrize("sorting_algorithm", ["greedy", "barycenter", "median", "neighbornet", "tsp"])
def test_fixed_columns_keep_their_order(n_cols, sorting_algorithm):
    df, cols = _clustered_df(n_cols)
    incoming = {col: list(df[col].astype(str).unique()) for col in cols}
    fixed_sets = [[cols[0]], [cols[-1]], [cols[0], cols[-1]]] + ([[cols[1]]] if n_cols > 2 else [])
    for fixed in fixed_sets:
        _, order_dict = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=sorting_algorithm,
                                  optimize_column_order=False, fixed_column=fixed)
        for col in fixed:
            assert order_dict[col] == incoming[col]
        assert all(sorted(order_dict[col]) == sorted(incoming[col]) for col in cols)


@pytest.mark.parametrize("sorting_algorithm", ["greedy", "barycenter", "median"])
@pytest.mark.parametrize("n_cols", [3, 4])
def test_sweep_algorithms_sort_any_number_of_axes(n_cols, sorting_algorithm):
    df, cols = _clustered_df(n_cols)
    unsorted = determine_crossing_edges(df.copy(), cols, {col: sorted(df[col].unique()) for col in cols}, col_weights="value")
    for fixed in [None, cols[1]]:
        columns, order_dict = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=sorting_algorithm,
                                        optimize_column_order=False, fixed_column=fixed, random_initializations=3)
        assert columns == cols
        assert determine_crossing_edges(df.copy(), columns, order_dict, col_weights="value") < unsorted


@pytest.mark.parametrize("sorting_algorithm", ["greedy", "barycenter", "median"])
def test_sweep_algorithms_optimize_column_order_with_more_than_two_axes(sorting_algorithm):
    df, _ = _clustered_df(2)
    df["copy"] = df["method1"]
    columns, _ = data_sort(df, ["method1", "method2", "copy"], column_weights="value", sorting_algorithm=sorting_algorithm,
                           optimize_column_order=True)
    assert sorted(columns) == ["copy", "method1", "method2"]
    assert abs(columns.index("method1") - columns.index("copy")) == 1


def test_fixed_column_accepts_positions_and_rejects_unknown_columns():
    df, cols = _clustered_df(3)
    random.seed(1)
    by_name = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm="greedy", optimize_column_order=False, fixed_column=["method1", "method3"])
    random.seed(1)
    by_position = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm="greedy", optimize_column_order=False, fixed_column=[0, 2])
    assert by_name == by_position
    with pytest.raises(ValueError):
        data_sort(df.copy(), cols, column_weights="value", sorting_algorithm="greedy", fixed_column="value")
    with pytest.raises(ValueError):
        data_sort(df.copy(), cols, column_weights="value", sorting_algorithm="greedy", fixed_column=3)


@pytest.mark.parametrize("old, fixed", [("greedy_wolf", "method1"), ("greedy_wblf", None)])
def test_deprecated_greedy_names_warn_and_map_to_greedy(old, fixed):
    df, cols = _clustered_df(2)
    random.seed(3)
    with pytest.warns(FutureWarning, match="deprecated"):
        old_result = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=old)
    random.seed(3)
    new_result = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm="greedy", fixed_column=fixed)
    assert old_result == new_result


@pytest.mark.parametrize("sorting_algorithm", ["greedy", "barycenter", "median"])
def test_first_initialization_is_deterministic(sorting_algorithm):
    df, cols = _clustered_df(3)
    random.seed(1)
    first = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=sorting_algorithm, optimize_column_order=False)
    random.seed(99)
    second = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=sorting_algorithm, optimize_column_order=False)
    assert first == second


@pytest.mark.parametrize("sorting_algorithm", ["greedy", "barycenter", "median"])
def test_random_initializations_never_do_worse(sorting_algorithm):
    df, cols = _clustered_df(3, seed=2)
    _, single = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=sorting_algorithm, optimize_column_order=False)
    random.seed(5)
    _, several = data_sort(df.copy(), cols, column_weights="value", sorting_algorithm=sorting_algorithm,
                           optimize_column_order=False, random_initializations=5)
    assert (determine_crossing_edges(df.copy(), cols, several, col_weights="value")
            <= determine_crossing_edges(df.copy(), cols, single, col_weights="value"))
