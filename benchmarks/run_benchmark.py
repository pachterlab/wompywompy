#!/usr/bin/env python
"""Timing/resource benchmark harness for wompywompy.plot_alluvial.

Usage
-----
Quick smoke test (should finish in well under a minute):
    python run_benchmark.py sweep --which smoke --out results/smoke.csv

Full default sweep (long-running -- launch under tmux/screen/nohup):
    python run_benchmark.py sweep --which default --out results/default.csv

Resume an interrupted sweep (skips rows already marked "ok" in --out):
    python run_benchmark.py sweep --which default --out results/default.csv --resume

Single ad-hoc config:
    python run_benchmark.py single --n-rows 10000 --n-columns 3 \\
        --n-categories 8 --sorting-algorithm neighbornet

Each row runs in its own subprocess (see bench_utils.run_isolated) so a
hung or crashing config can't take down the rest of the sweep. Results are
written to --out incrementally, one row at a time, so a killed job keeps
whatever it already finished.
"""

import os

# atlas is a shared, unscheduled box -- cap BLAS/OpenMP thread pools before
# numpy/pandas/igraph get imported anywhere below, so this harness can't grab
# cores away from other users' running jobs. setdefault() lets an operator
# override by exporting these themselves before invoking the script.
for _env_var in (
    "OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS",
    "NUMEXPR_NUM_THREADS", "VECLIB_MAXIMUM_THREADS",
):
    os.environ.setdefault(_env_var, "1")

import argparse
import csv
import itertools
import time

from bench_utils import run_isolated
from generate_data import make_synthetic_df
from sweep_config import DEFAULT_TIMEOUT_S, FIXED_PARAMS, SWEEPS

RESULT_FIELDS = [
    "status", "error", "wall_time_s", "user_cpu_s", "sys_cpu_s",
    "peak_rss_mb", "n_unique_alluvia",
]
PARAM_FIELDS = [
    "n_rows", "n_columns", "n_categories", "sorting_algorithm",
    "optimize_column_order", "optimize_column_order_per_cycle",
    "coloring_algorithm", "match_colors", "seed",
]
ALL_FIELDS = PARAM_FIELDS + RESULT_FIELDS + ["timeout_s", "timestamp"]


def _run_one(params):
    """Runs inside the isolated subprocess. Must stay a top-level function
    (multiprocessing spawn needs to re-import it by name)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from wompywompy import plot_alluvial

    df, graphing_columns = make_synthetic_df(
        n_rows=params["n_rows"],
        n_columns=params["n_columns"],
        n_categories=params["n_categories"],
        seed=params["seed"],
    )
    n_unique_alluvia = len(df.groupby(graphing_columns).size())

    fig = plot_alluvial(
        df=df,
        graphing_columns=graphing_columns,
        sorting_algorithm=params["sorting_algorithm"],
        optimize_column_order=params["optimize_column_order"],
        optimize_column_order_per_cycle=params["optimize_column_order_per_cycle"],
        coloring_algorithm=params["coloring_algorithm"],
        match_colors=params["match_colors"],
        savefig=False,
    )
    fig_obj = fig[0] if isinstance(fig, tuple) else fig
    plt.close(fig_obj)

    return {"n_unique_alluvia": n_unique_alluvia}


def _param_grid(sweep_dict):
    keys = list(sweep_dict.keys())
    for values in itertools.product(*(sweep_dict[k] for k in keys)):
        row = dict(zip(keys, values))
        row.update(FIXED_PARAMS)
        yield row


def _load_completed(out_path):
    if not os.path.exists(out_path):
        return set()
    completed = set()
    with open(out_path, newline="") as f:
        for row in csv.DictReader(f):
            if row.get("status") == "ok":
                completed.add(tuple(row[k] for k in PARAM_FIELDS))
    return completed


def _signature(params):
    return tuple(str(params[k]) for k in PARAM_FIELDS)


def _run_rows(rows, out_path, timeout_s, resume):
    completed = _load_completed(out_path) if resume else set()
    write_header = not (resume and os.path.exists(out_path))
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)

    rows = list(rows)
    total = len(rows)
    with open(out_path, "a", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ALL_FIELDS)
        if write_header:
            writer.writeheader()
        for i, params in enumerate(rows, 1):
            if resume and _signature(params) in completed:
                print(f"[{i}/{total}] skip (already ok): {params}")
                continue
            print(f"[{i}/{total}] running: {params}")
            result = run_isolated(_run_one, params, timeout_s=timeout_s)
            row = {**params, **result, "timeout_s": timeout_s, "timestamp": time.time()}
            writer.writerow({k: row.get(k) for k in ALL_FIELDS})
            f.flush()
            print(f"    -> {result['status']} in {result['wall_time_s']:.2f}s, "
                  f"peak_rss={result['peak_rss_mb']}MB")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="mode", required=True)

    p_sweep = sub.add_parser("sweep", help="Run a predefined parameter grid from sweep_config.py")
    p_sweep.add_argument("--which", choices=sorted(SWEEPS.keys()), default="smoke")
    p_sweep.add_argument("--out", default="results/sweep.csv")
    p_sweep.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)
    p_sweep.add_argument("--resume", action="store_true")
    p_sweep.add_argument("--dry-run", action="store_true", help="Print the grid size and exit")

    p_single = sub.add_parser("single", help="Run one ad-hoc config")
    p_single.add_argument("--n-rows", type=int, default=10_000)
    p_single.add_argument("--n-columns", type=int, default=3)
    p_single.add_argument("--n-categories", type=int, default=8)
    p_single.add_argument("--sorting-algorithm", default="neighbornet",
                           choices=["neighbornet", "tsp", "greedy_wolf", "greedy_wblf", "none"])
    p_single.add_argument("--optimize-column-order", action="store_true")
    p_single.add_argument("--out", default="results/single.csv")
    p_single.add_argument("--timeout", type=float, default=DEFAULT_TIMEOUT_S)

    args = parser.parse_args()

    if args.mode == "sweep":
        rows = list(_param_grid(SWEEPS[args.which]))
        if args.dry_run:
            print(f"sweep '{args.which}': {len(rows)} configs, timeout={args.timeout}s each "
                  f"(worst case {len(rows) * args.timeout / 60:.1f} min)")
            return
        _run_rows(rows, args.out, args.timeout, args.resume)
    else:
        params = {
            "n_rows": args.n_rows,
            "n_columns": args.n_columns,
            "n_categories": args.n_categories,
            "sorting_algorithm": args.sorting_algorithm,
            "optimize_column_order": args.optimize_column_order,
            **FIXED_PARAMS,
        }
        _run_rows([params], args.out, args.timeout, resume=False)


if __name__ == "__main__":
    main()
