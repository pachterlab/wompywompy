# wompywompy benchmarks

Timing/resource harness for `wompywompy.plot_alluvial`, meant to run on atlas
(48 cores / 377G RAM, no job scheduler -- launch long sweeps under `tmux` or
`nohup`).

## Setup

```
ssh atlas
conda activate wompwomp_env
cd ~/wompywompy/benchmarks
```

## Resource etiquette

atlas is a shared, unscheduled box (no SLURM/qsub) -- other people's jobs run
there too. `run_benchmark.py` caps BLAS/OpenMP thread pools to 1
(`OMP_NUM_THREADS`, `OPENBLAS_NUM_THREADS`, `MKL_NUM_THREADS`,
`NUMEXPR_NUM_THREADS`, `VECLIB_MAXIMUM_THREADS`) *before* numpy/pandas/igraph
get imported, so each config runs single-threaded by default and won't grab
cores away from anyone else's running work. This also makes wall-clock
numbers comparable across runs instead of varying with how busy the box is.

To measure realistic multi-threaded throughput instead (only do this if you've
checked `htop`/`free -h` and the box has headroom), export a higher value
before invoking the script -- `setdefault()` in the harness won't override an
already-exported value:
```
export OMP_NUM_THREADS=8 OPENBLAS_NUM_THREADS=8
python run_benchmark.py sweep --which default --out results/default_mt.csv
```

## What's being measured

Each config runs `plot_alluvial` end-to-end (synthetic data generation +
sorting/column-ordering + coloring + plotting, no display/savefig I/O) in its
own subprocess, isolated so a hung or crashing config can't take down the
whole sweep. Recorded per run: wall time, user/sys CPU time, peak RSS
(`resource.getrusage`), and the number of unique alluvia actually plotted.

Cost drivers (see `generate_data.py` docstring for detail):
- `n_categories` -- distinct values per column; sets distance-matrix size.
  `sorting_algorithm="tsp"` is an *exact* exponential-time DP solver -- only
  include it with `n_categories <= ~15` (see `TSP_SWEEP` in `sweep_config.py`).
- `n_columns` -- multiplies column-order-optimization cost.
- `n_rows` -- mainly controls how much of the `n_categories**n_columns`
  combinatorial space gets populated (more unique alluvia to draw).
- `optimize_column_order` / `optimize_column_order_per_cycle` -- each adds a
  nested pass of edge-crossing calculations.

## Running

Smoke test first (~seconds):
```
python run_benchmark.py sweep --which smoke --out results/smoke.csv
```

Check grid size before committing to a long run:
```
python run_benchmark.py sweep --which default --out results/default.csv --dry-run
```

Full sweep, under tmux so it survives disconnects:
```
tmux new -s wompy-bench
conda activate wompwomp_env
python run_benchmark.py sweep --which default --out results/default.csv
# detach: Ctrl-b d
```

Resume after an interruption (skips rows already marked "ok"):
```
python run_benchmark.py sweep --which default --out results/default.csv --resume
```

One-off config:
```
python run_benchmark.py single --n-rows 50000 --n-columns 3 --n-categories 10 \
    --sorting-algorithm neighbornet --optimize-column-order
```

## Files

- `generate_data.py` -- synthetic wide-format categorical dataframe generator.
- `bench_utils.py` -- subprocess isolation + timing/memory capture.
- `sweep_config.py` -- parameter grids (`default`, `tsp`, `smoke`) and fixed params.
- `run_benchmark.py` -- CLI entry point.
- `results/` -- CSV output (gitignored).
