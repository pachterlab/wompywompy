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
def test_plot_alluvial_greedy_wolf(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="greedy_wolf",
        match_colors=False,
        color_alluvium=False
    )
    fig = fig[0]  # tuple --> figure

    assert fig is not None

    return fig

@pytest.mark.mpl_image_compare
def test_plot_alluvial_greedy_wblf(clus_df_gather):
    graphing_columns=["tissue", "cluster"]
    fig = plot_alluvial(
        df=clus_df_gather,
        graphing_columns=graphing_columns,
        column_weights="value",
        sorting_algorithm="greedy_wblf",
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

    assert num == 96
