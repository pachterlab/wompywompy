#!/usr/bin/env python
"""Parity harness -- orchestrator.

Feeds *identical* block orderings to the R (wompwomp) and Python (wompywompy)
implementations of the W_POMP crossing objective and checks they agree.

For each random case we also compute an independent O(n^2) brute-force crossing
count on the exact layout each package produced, so a mismatch can be pinned to
(a) the two packages laying alluvia out differently, or (b) a Fenwick bug.

Usage:
    python run_parity.py [--n 300] [--seed 0] [--min-layers 2] [--max-layers 4]
                         [--rscript Rscript] [--wompwomp ../../../wompwomp]

Exit code is non-zero if any case disagrees (outside floating tolerance).
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

from wompywompy.wompwomp import _plot_alluvium, determine_crossing_edges  # noqa: E402


def gen_case(rng: np.random.Generator, case_id: int, n_layers: int) -> dict:
    ks = rng.integers(2, 6, size=n_layers)
    cols = [f"col_{i + 1}" for i in range(n_layers)]

    # Every (block) combination that occurs, with a random positive weight.
    # Draw a random subset of the full grid so n_alluvia varies.
    grid = list(itertools.product(*[range(k) for k in ks]))
    n_take = rng.integers(max(2, len(grid) // 4), len(grid) + 1)
    idx = rng.choice(len(grid), size=min(n_take, len(grid)), replace=False)
    rows = []
    for gi in idx:
        combo = grid[gi]
        row = {cols[i]: f"L{i}_{combo[i]}" for i in range(n_layers)}
        row["value"] = int(rng.integers(1, 20))
        rows.append(row)

    # A random block order per layer -- the ordering imposed on BOTH packages.
    levels = {}
    for i, k in enumerate(ks):
        vals = [f"L{i}_{b}" for b in range(k)]
        rng.shuffle(vals)
        levels[cols[i]] = vals

    return {"case_id": case_id, "cols": cols, "levels": levels, "rows": rows}


def brute_force(lode: pd.DataFrame, cols: list[str]) -> float:
    total = 0.0
    w = lode["value"].to_numpy(dtype=float)
    n = len(w)
    for h in range(len(cols) - 1):
        yl = lode[f"y_{cols[h]}"].rank(method="min").to_numpy()
        yr = lode[f"y_{cols[h + 1]}"].rank(method="min").to_numpy()
        for i in range(n - 1):
            for j in range(i + 1, n):
                dl = np.sign(yl[i] - yl[j])
                dr = np.sign(yr[i] - yr[j])
                if dl != 0 and dr != 0 and dl != dr:
                    total += w[i] * w[j]
    return total


def py_objective(case: dict) -> tuple[float, float]:
    cols = case["cols"]
    df = pd.DataFrame(case["rows"])
    order_dict = {c: list(case["levels"][c]) for c in cols}

    obj = determine_crossing_edges(
        df.copy(), graphing_columns=list(cols), order_dict=order_dict, col_weights="value"
    )
    lode = _plot_alluvium(
        df.copy(), list(cols), "value", order_dict=order_dict, objective_calc=True
    )
    return float(obj), brute_force(lode, cols)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=300)
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
        cases.append(gen_case(rng, cid, nl))

    py = {}
    for case in cases:
        py[case["case_id"]] = py_objective(case)

    tmpdir = tempfile.mkdtemp(prefix="parity_")
    cases_path = os.path.join(tmpdir, "cases.json")
    out_path = os.path.join(tmpdir, "r_out.json")
    with open(cases_path, "w") as fh:
        json.dump(cases, fh)

    r_script = os.path.join(HERE, "r_objective.R")
    proc = subprocess.run(
        [args.rscript, r_script, cases_path, out_path, args.wompwomp],
        capture_output=True, text=True,
    )
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr + "\n")
        return 2
    with open(out_path) as fh:
        r_rows = {r["case_id"]: r for r in json.load(fh)}

    if not args.keep:
        os.remove(cases_path)
        os.remove(out_path)
        os.rmdir(tmpdir)

    tol = 1e-6
    by_layers: dict[int, list[bool]] = {}
    rp_by_layers: dict[int, list[bool]] = {}
    worst = []
    for case in cases:
        cid = case["case_id"]
        nl = len(case["cols"])
        py_obj, py_bf = py[cid]
        r_obj = float(r_rows[cid]["r_objective"])
        r_bf = float(r_rows[cid]["r_bruteforce"])

        rp_match = abs(py_obj - r_obj) <= tol
        self_ok = abs(py_obj - py_bf) <= tol and abs(r_obj - r_bf) <= tol
        rp_by_layers.setdefault(nl, []).append(rp_match)
        by_layers.setdefault(nl, []).append(self_ok)
        if not rp_match:
            worst.append((abs(py_obj - r_obj), cid, nl, py_obj, r_obj, py_bf, r_bf))

    print(f"{'layers':>7} {'R==Py':>12} {'Fenwick==brute':>16}")
    for nl in sorted(rp_by_layers):
        rp = rp_by_layers[nl]
        sc = by_layers[nl]
        print(f"{nl:>7} {sum(rp):>5}/{len(rp):<6} {sum(sc):>7}/{len(sc):<8}")
    total_rp = sum(sum(v) for v in rp_by_layers.values())
    total_n = sum(len(v) for v in rp_by_layers.values())
    print(f"{'all':>7} {total_rp:>5}/{total_n:<6}")

    if worst:
        worst.sort(reverse=True)
        print("\nworst mismatches (|Py-R|, case, layers, py_obj, r_obj, py_bf, r_bf):")
        for row in worst[:10]:
            print("  ", "  ".join(f"{x:g}" if isinstance(x, float) else str(x) for x in row))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
