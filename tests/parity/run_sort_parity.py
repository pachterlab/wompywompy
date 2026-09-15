#!/usr/bin/env python
"""Sorting parity harness -- orchestrator.

Feeds *identical* data to the R (wompwomp) and Python (wompywompy) sweep
sorters -- `greedy`, `barycenter` and `median`, with and without fixed axes --
and checks that both put the blocks of every axis in the same order.

Only the deterministic path is compared: one initialization (the two packages
draw their random restarts from different RNGs) and no axis-order optimization
(R's TSP solver and python_tsp are different heuristics).

Usage:
    PARITY_RSCRIPT=/path/to/Rscript python run_sort_parity.py [--n 200] [--seed 0]
                                        [--min-layers 2] [--max-layers 4]

Exit code is non-zero if any case disagrees.
"""
from __future__ import annotations

import argparse
import itertools
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))

from wompywompy.wompwomp import data_sort  # noqa: E402

METHODS = ("greedy", "barycenter", "median")


def gen_case(rng: np.random.Generator, case_id: int, n_layers: int, method: str) -> dict:
    ks = rng.integers(2, 6, size=n_layers)
    cols = [f"col_{i + 1}" for i in range(n_layers)]

    grid = list(itertools.product(*[range(k) for k in ks]))
    n_take = rng.integers(max(2, len(grid) // 4), len(grid) + 1)
    idx = rng.choice(len(grid), size=min(n_take, len(grid)), replace=False)
    rows = []
    for gi in idx:
        combo = grid[gi]
        row = {cols[i]: f"L{i}_{combo[i]}" for i in range(n_layers)}
        row["value"] = int(rng.integers(1, 20))
        rows.append(row)

    # No fixed axis, one at either end, one in the middle, or both ends.
    choices = [[], [cols[0]], [cols[-1]], [cols[0], cols[-1]]]
    if n_layers > 2:
        choices.append([cols[1]])
    fixed = choices[int(rng.integers(0, len(choices)))]

    return {"case_id": case_id, "cols": cols, "rows": rows, "fixed": fixed, "method": method}


def py_order(case: dict) -> dict:
    df = pd.DataFrame(case["rows"])
    _, order_dict = data_sort(
        df, list(case["cols"]), column_weights="value",
        sorting_algorithm=case["method"], optimize_column_order=False,
        fixed_column=case["fixed"] or None,
    )
    return {col: list(order_dict[col]) for col in case["cols"]}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-layers", type=int, default=2)
    ap.add_argument("--max-layers", type=int, default=4)
    ap.add_argument("--rscript", default=os.environ.get("PARITY_RSCRIPT", "Rscript"))
    ap.add_argument("--wompwomp", default=os.path.normpath(os.path.join(HERE, "..", "..", "..", "wompwomp")))
    ap.add_argument("--keep", action="store_true", help="keep the temp JSON files")
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    cases = []
    for cid in range(args.n):
        nl = int(rng.integers(args.min_layers, args.max_layers + 1))
        cases.append(gen_case(rng, cid, nl, METHODS[cid % len(METHODS)]))

    py = {case["case_id"]: py_order(case) for case in cases}

    tmpdir = tempfile.mkdtemp(prefix="sortparity_")
    cases_path = os.path.join(tmpdir, "cases.json")
    out_path = os.path.join(tmpdir, "r_out.json")
    with open(cases_path, "w") as fh:
        json.dump(cases, fh)

    proc = subprocess.run(
        [args.rscript, os.path.join(HERE, "r_sort.R"), cases_path, out_path, args.wompwomp],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr + "\n")
        return 2
    with open(out_path) as fh:
        r_rows = {r["case_id"]: r["order"] for r in json.load(fh)}

    if not args.keep:
        os.remove(cases_path)
        os.remove(out_path)
        os.rmdir(tmpdir)

    by_method: dict[str, list[bool]] = {}
    mismatches = []
    for case in cases:
        cid = case["case_id"]
        # a one-block axis comes back from jsonlite as a bare string, not a list
        r_order = {col: ([r_rows[cid][col]] if isinstance(r_rows[cid][col], str) else list(r_rows[cid][col]))
                   for col in case["cols"]}
        match = all(r_order[col] == py[cid][col] for col in case["cols"])
        by_method.setdefault(case["method"], []).append(match)
        if not match:
            mismatches.append((cid, case["method"], len(case["cols"]), case["fixed"], r_order, py[cid]))

    print(f"{'method':>12} {'R==Py':>12}")
    for method in sorted(by_method):
        hits = by_method[method]
        print(f"{method:>12} {sum(hits):>5}/{len(hits):<6}")
    total = sum(sum(v) for v in by_method.values())
    n_total = sum(len(v) for v in by_method.values())
    print(f"{'all':>12} {total:>5}/{n_total:<6}")

    if mismatches:
        print("\nmismatches (case, method, layers, fixed):")
        for cid, method, nl, fixed, r_order, p_order in mismatches[:10]:
            print(f"   case {cid}  {method}  {nl} layers  fixed={fixed}")
            for col in r_order:
                if r_order[col] != p_order[col]:
                    print(f"      {col}: R  {r_order[col]}")
                    print(f"      {' ' * len(col)}  Py {p_order[col]}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
