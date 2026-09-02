#!/usr/bin/env python
"""Summary figure for a sweep CSV produced by run_benchmark.py, matching the
format of wompwomp (R)'s benchmarks/plot_results.R: wall time and peak
memory each plotted against n_columns / n_categories / n_unique_alluvia,
points colored/shaped by algorithm, with a short tick marking each x-group's
mean, panels lettered A-F, title only (no subtitle).

Usage: python plot_results.py results/default.csv results/sweep_report.png
"""
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

IN_PATH = sys.argv[1] if len(sys.argv) > 1 else "results/default.csv"
OUT_PATH = sys.argv[2] if len(sys.argv) > 2 else "results/sweep_report.png"

df = pd.read_csv(IN_PATH)
df = df[df.status == "ok"]
if len(df) == 0:
    raise SystemExit(f"no 'ok' rows in {IN_PATH}")

methods = sorted(df.sorting_algorithm.unique())
# Same palette/marker assignment as wompwomp's plot_results.R (alphabetical
# method order against the same Okabe-Ito-derived colors), so the two
# figures read as one system.
PALETTE = ["#0072B2", "#D55E00", "#009E73", "#CC79A7"]
MARKERS = ["o", "^", "s", "D"]
col_for = {m: PALETTE[i] for i, m in enumerate(methods)}
mk_for = {m: MARKERS[i] for i, m in enumerate(methods)}


def group_means(x, y, method):
    key = pd.Series(list(zip(method, x)))
    gx = pd.Series(x).groupby(key).first()
    gy = pd.Series(y).groupby(key).mean()
    gm = pd.Series(method).groupby(key).first()
    return pd.DataFrame({"x": gx, "y": gy, "method": gm})


def panel(ax, x, y, method, xlab, ylab, logx=False, logy=False):
    x = np.asarray(x, dtype=float)
    y = np.asarray(y, dtype=float)
    method = np.asarray(method)
    ok = np.isfinite(x) & np.isfinite(y)
    if logx:
        ok &= x > 0
    if logy:
        ok &= y > 0
    x, y, method = x[ok], y[ok], method[ok]

    for m in methods:
        sel = method == m
        ax.scatter(x[sel], y[sel], c=col_for[m], marker=mk_for[m], s=45, alpha=0.85, edgecolors="none")

    gm = group_means(x, y, method)
    if logx:
        halfwidth = (np.log10(x.max()) - np.log10(x.min())) * 0.015
    else:
        halfwidth = (x.max() - x.min()) * 0.015 if x.max() > x.min() else 0.05
    for _, row in gm.iterrows():
        if logx:
            x0, x1 = row.x * 10 ** (-halfwidth), row.x * 10 ** halfwidth
        else:
            x0, x1 = row.x - halfwidth, row.x + halfwidth
        ax.plot([x0, x1], [row.y, row.y], color=col_for[row.method], lw=3, solid_capstyle="butt")

    if logx:
        ax.set_xscale("log")
    if logy:
        ax.set_yscale("log")
    ax.set_xlabel(xlab)
    ax.set_ylabel(ylab)


fig, axes = plt.subplots(2, 3, figsize=(16, 10.2))
fig.subplots_adjust(top=0.87, bottom=0.07, hspace=0.4, wspace=0.3, left=0.06, right=0.98)

fig.text(0.01, 0.965, "wompywompy benchmark sweep — results", fontsize=18, fontweight="bold")

handles = [
    plt.Line2D([0], [0], marker=mk_for[m], color="w", markerfacecolor=col_for[m], markersize=9, label=m)
    for m in methods
]
fig.legend(handles=handles, loc="upper right", bbox_to_anchor=(0.99, 0.97), ncol=1, frameon=False, fontsize=11)

panel(axes[0, 0], df.n_columns, df.wall_time_s, df.sorting_algorithm, "n_columns", "wall time (s)", logy=True)
axes[0, 0].set_title("A  wall time vs n_columns", loc="left", fontsize=11, fontweight="bold")

panel(axes[0, 1], df.n_categories, df.wall_time_s, df.sorting_algorithm, "n_categories", "wall time (s)", logx=True, logy=True)
axes[0, 1].set_title("B  wall time vs n_categories", loc="left", fontsize=11, fontweight="bold")

panel(axes[0, 2], df.n_unique_alluvia, df.wall_time_s, df.sorting_algorithm, "n_unique_alluvia", "wall time (s)", logx=True, logy=True)
axes[0, 2].set_title("C  wall time vs n_unique_alluvia", loc="left", fontsize=11, fontweight="bold")

panel(axes[1, 0], df.n_columns, df.peak_rss_mb, df.sorting_algorithm, "n_columns", "peak RSS (MB)")
axes[1, 0].set_title("D  memory vs n_columns", loc="left", fontsize=11, fontweight="bold")

panel(axes[1, 1], df.n_categories, df.peak_rss_mb, df.sorting_algorithm, "n_categories", "peak RSS (MB)", logx=True)
axes[1, 1].set_title("E  memory vs n_categories", loc="left", fontsize=11, fontweight="bold")

panel(axes[1, 2], df.n_unique_alluvia, df.peak_rss_mb, df.sorting_algorithm, "n_unique_alluvia", "peak RSS (MB)", logx=True)
axes[1, 2].set_title("F  memory vs n_unique_alluvia", loc="left", fontsize=11, fontweight="bold")

fig.savefig(OUT_PATH, dpi=150, facecolor="white")
print(f"wrote {OUT_PATH} ({len(df)} ok rows of {len(pd.read_csv(IN_PATH))} total)")
