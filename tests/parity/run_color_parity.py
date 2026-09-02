#!/usr/bin/env python
"""Colour parity harness: R get_lode_clusters() vs Python find_colors_*().

For each random case, compares the colour partitions of the (column, value)
nodes, up to community relabelling. The deterministic reference-propagation
methods (left / right / a named column) are expected to match exactly; the
`advanced` method uses Leiden, whose RNG differs between the R and Python
igraph bindings, so it is reported as adjusted Rand index rather than required
to match.

    PARITY_RSCRIPT=/path/to/Rscript python run_color_parity.py --n 200 --seed 0
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
import tempfile

import numpy as np
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", ".."))

from run_parity import gen_case  # noqa: E402
from wompywompy.wompwomp import find_colors_advanced, find_colors_reference  # noqa: E402


def canon(part):
    """Canonical form of {col: {value: community}} -> frozenset of frozenset((col,value))."""
    if part is None:
        return None
    groups = {}
    for col, d in part.items():
        for val, comm in d.items():
            groups.setdefault(comm, set()).add((str(col), str(val)))
    return frozenset(frozenset(g) for g in groups.values())


def labels_vector(part, nodes):
    return [part_lookup(part, n) for n in nodes]


def part_lookup(part, node):
    col, val = node
    return part.get(col, {}).get(val)


def adjusted_rand(a, b):
    # a, b: label lists over the same node order
    from math import comb
    n = len(a)
    if n < 2:
        return 1.0
    ai = {v: i for i, v in enumerate(sorted(set(a)))}
    bi = {v: i for i, v in enumerate(sorted(set(b)))}
    cont = np.zeros((len(ai), len(bi)), dtype=int)
    for x, y in zip(a, b):
        cont[ai[x], bi[y]] += 1
    sum_comb_c = sum(comb(v, 2) for v in cont.flatten())
    sum_a = sum(comb(v, 2) for v in cont.sum(axis=1))
    sum_b = sum(comb(v, 2) for v in cont.sum(axis=0))
    exp = sum_a * sum_b / comb(n, 2)
    mx = (sum_a + sum_b) / 2
    return 1.0 if mx == exp else (sum_comb_c - exp) / (mx - exp)


def py_partitions(case):
    cols = case["cols"]
    df = pd.DataFrame(case["rows"])
    g = df.groupby(cols, as_index=False)["value"].sum()
    return {
        "left": find_colors_reference(g, cols, reference="left"),
        "right": find_colors_reference(g, cols, reference="right"),
        "named": find_colors_reference(g, cols, reference=cols[0]),
        "advanced": find_colors_advanced(g, cols, resolution=1),
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=200)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--min-layers", type=int, default=2)
    ap.add_argument("--max-layers", type=int, default=4)
    ap.add_argument("--rscript", default=os.environ.get("PARITY_RSCRIPT", "Rscript"))
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    cases = [gen_case(rng, i, int(rng.integers(args.min_layers, args.max_layers + 1)))
             for i in range(args.n)]

    pyres = {c["case_id"]: py_partitions(c) for c in cases}

    tmp = tempfile.mkdtemp(prefix="colorparity_")
    cj, oj = os.path.join(tmp, "c.json"), os.path.join(tmp, "o.json")
    json.dump(cases, open(cj, "w"))
    r_script = os.path.join(HERE, "r_colors.R")
    proc = subprocess.run([args.rscript, r_script, cj, oj], capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout + "\n" + proc.stderr + "\n")
        return 2
    rres = {r["case_id"]: r["partitions"] for r in json.load(open(oj))}

    det = {"left": [0, 0], "right": [0, 0], "named": [0, 0]}
    adv_ari = []
    mism = []
    for c in cases:
        cid = c["case_id"]
        nodes = [(col, str(v)) for col in c["cols"] for v in c["levels"][col]]
        for m in ("left", "right", "named"):
            det[m][1] += 1
            rp, pp = canon(rres[cid].get(m)), canon(pyres[cid][m])
            if rp == pp:
                det[m][0] += 1
            else:
                mism.append((cid, m))
        rp, pp = rres[cid].get("advanced"), pyres[cid]["advanced"]
        if rp is not None:
            common = [n for n in nodes
                      if part_lookup(rp, n) is not None and part_lookup(pp, n) is not None]
            if len(common) >= 2:
                adv_ari.append(adjusted_rand(labels_vector(rp, common), labels_vector(pp, common)))

    print(f"{'method':10} {'R == Py (exact, up to relabel)':>32}")
    for m in ("left", "right", "named"):
        print(f"{m:10} {det[m][0]:>15}/{det[m][1]:<16}")
    if adv_ari:
        a = np.array(adv_ari)
        print(f"\nadvanced: Leiden RNG differs across bindings; partition ARI "
              f"mean={a.mean():.3f} min={a.min():.3f} (n={len(a)})")
    if mism:
        print("\nfirst deterministic mismatches (case, method):", mism[:10])
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
