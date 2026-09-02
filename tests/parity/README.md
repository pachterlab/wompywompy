# R / Python parity harness

Two harnesses:

* `run_parity.py` -- the **W\_POMP crossing objective** `L` (below).
* `run_color_parity.py` -- the **W\_LOMP colouring**: for the same random case,
  compares R `get_lode_clusters()` with Python `find_colors_advanced()` /
  `find_colors_reference()` as partitions of the (column, value) nodes, up to
  community relabelling. The deterministic methods (`left`, `right`, named
  column) must match exactly; `advanced` uses Leiden, whose RNG differs between
  the R and Python igraph bindings, so it is reported as adjusted Rand index.
  `PARITY_RSCRIPT=... python run_color_parity.py --n 200 --seed 0` --
  needs `wompwomp` installed (`R CMD INSTALL`), not just on the source path.

---

Checks that `wompwomp` (R) and `wompywompy` (Python) compute the **same**
W\_POMP crossing objective `L` when handed the **same** block ordering.

The two packages each fix the order of alluvia *within* a stratum before
counting crossings (R: `make_lode_df`, Python: `_plot_alluvium`). For `m >= 3`
that order affects `L`, so the two implementations only agree if they use an
identical, fully-specified rule. This harness is the regression test for that.

## What it does

For each random case (`gen_case`):

1. build a collapsed weighted data frame with `m` categorical layers,
2. draw one random block permutation per layer -- imposed on **both** packages,
3. compute `L` with `wompywompy.determine_crossing_edges`,
4. compute `L` with `wompwomp::compute_crossing_objective` (via `r_objective.R`),
5. independently recount crossings with an O(n^2) brute force on the exact
   layout each package produced.

`R == Python` should be 100%. `Fenwick == brute force` on each side catches a
sweep bug as opposed to a layout difference.

## Run

```bash
PARITY_RSCRIPT=/path/to/Rscript \
python run_parity.py --n 300 --seed 0 --min-layers 2 --max-layers 5
```

Needs an R (>= 4.1) that can `pkgload::load_all()` the sibling `wompwomp`
checkout -- `--wompwomp /path/to/wompwomp` if it is not at `../../../wompwomp`.
`r_objective.R` sources only `src/fenwick.cpp`, `R/utils.R` and
`R/objective_calculation.R`, none of which touch igraph, so a stale igraph in
the R install does not matter.

Exit code is non-zero if any case disagrees.
