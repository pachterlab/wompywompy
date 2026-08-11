"""Parameter grids for run_benchmark.py sweep mode.

DEFAULT_SWEEP covers the axes that actually move wompywompy's cost (see
generate_data.py docstring). "tsp" is deliberately excluded from the default
grid since it's an exact exponential-time solver -- add it explicitly with a
small n_categories cap (<=15) if you want it, e.g. via TSP_SWEEP below.
"""

DEFAULT_SWEEP = {
    "n_rows": [1_000, 10_000, 100_000],
    "n_columns": [2, 3, 4],
    "n_categories": [4, 8, 16],
    "sorting_algorithm": ["neighbornet", "greedy_wblf"],
    "optimize_column_order": [True, False],
}

TSP_SWEEP = {
    "n_rows": [10_000],
    "n_columns": [2, 3],
    "n_categories": [4, 8, 12, 15],
    "sorting_algorithm": ["tsp"],
    "optimize_column_order": [False],
}

SMOKE_SWEEP = {
    "n_rows": [500],
    "n_columns": [2],
    "n_categories": [4],
    "sorting_algorithm": ["neighbornet", "greedy_wblf"],
    "optimize_column_order": [False],
}

SWEEPS = {
    "default": DEFAULT_SWEEP,
    "tsp": TSP_SWEEP,
    "smoke": SMOKE_SWEEP,
}

# Held fixed across every row in a sweep (override with --fixed key=value).
FIXED_PARAMS = {
    "optimize_column_order_per_cycle": False,
    "coloring_algorithm": "advanced",
    "match_colors": True,
    "seed": 0,
}

DEFAULT_TIMEOUT_S = 600
