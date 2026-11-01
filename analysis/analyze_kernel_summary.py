#!/usr/bin/env python3
"""Independent re-analysis of results/kernel_summary.csv  (CS340-EX2).

Question we answer here, independently of the report's prose:

1. Claim 1 of the paper says core operations got slower after Linux 4.0.
   Is that visible in our own logs once run-to-run noise is taken into
   account, or is the signal buried in the noise?
2. How much of the observed variation is noise (stdev/mean) rather than a
   kernel-version effect?
3. Which tests are too noisy to support any verdict at all?

Input  : results/kernel_summary.csv
         columns: kernel, test, mean_ns, stdev_ns, run1_ns, run2_ns, run3_ns
Output : relative_latency_by_kernel.csv
         noise_by_test.csv
         fig_trend.png
         fig_noise.png
         (all written under --outdir)

Usage:
    python3 analyze_kernel_summary.py \
        --csv results/kernel_summary.csv --outdir analysis

The script only reads; it never edits results/.  Numbers quoted in
docs/analysis-note.md are printed by this script, so the note stays
traceable to one command.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------
# helpers
# --------------------------------------------------------------------------
def parse_version(release: str) -> float | None:
    """'4.14.15-041415-generic' -> 4.14 ; '4.20.13-042013-generic' -> 4.20.

    Encoded as major + minor / 100 so that 4.2 (-> 4.02) and 4.20 (-> 4.20)
    sort correctly; a plain float('4.20') would collide with float('4.2').
    """
    m = re.match(r"^(\d+)\.(\d+)", release)
    if not m:
        return None
    return int(m.group(1)) + int(m.group(2)) / 100.0


def pick_baseline(kernels: list[str], wanted: str = "4.0") -> str:
    for k in kernels:
        if k.startswith(wanted):
            return k
    raise SystemExit(f"baseline kernel {wanted!r} not found in {kernels[:5]}...")


def spearman(x: np.ndarray, y: np.ndarray) -> float:
    """Rank correlation without scipy."""
    rx = pd.Series(x).rank().to_numpy()
    ry = pd.Series(y).rank().to_numpy()
    rx = rx - rx.mean()
    ry = ry - ry.mean()
    denom = np.sqrt((rx**2).sum() * (ry**2).sum())
    return float((rx * ry).sum() / denom) if denom else float("nan")


# --------------------------------------------------------------------------
# main
# --------------------------------------------------------------------------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="results/kernel_summary.csv")
    ap.add_argument("--outdir", default="analysis")
    ap.add_argument("--baseline", default="4.0")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv)
    df = df.dropna(subset=["mean_ns", "stdev_ns"])
    kernels = sorted(df["kernel"].unique(), key=lambda k: (parse_version(k) or 0, k))
    base = pick_baseline(kernels, args.baseline)

    # ---- per-test baseline ------------------------------------------------
    b = df[df["kernel"] == base].set_index("test")
    keep = [t for t in b.index]  # every test the baseline measured

    # ---- join every kernel against the baseline ---------------------------
    rows = []
    for k in kernels:
        sub = df[(df["kernel"] == k) & (df["test"].isin(keep))]
        for _, r in sub.iterrows():
            bm = float(b.loc[r["test"], "mean_ns"])
            bs = float(b.loc[r["test"], "stdev_ns"])
            if bm <= 0:
                continue
            rows.append(
                dict(
                    kernel=k,
                    version=parse_version(k),
                    is_extension=("4.4.0-210" in k),
                    test=r["test"],
                    mean_ns=float(r["mean_ns"]),
                    stdev_ns=float(r["stdev_ns"]),
                    base_mean_ns=bm,
                    base_stdev_ns=bs,
                    ratio=float(r["mean_ns"]) / bm,
                    cv=float(r["stdev_ns"]) / float(r["mean_ns"]) if r["mean_ns"] else np.nan,
                    # conservative "clearly slower": the whole kernel interval
                    # sits above the whole baseline interval
                    clearly_slower=(float(r["mean_ns"]) - float(r["stdev_ns"]))
                    > (bm + bs),
                    clearly_faster=(float(r["mean_ns"]) + float(r["stdev_ns"]))
                    < (bm - bs),
                )
            )
    long = pd.DataFrame(rows)

    # ---- per-kernel aggregate --------------------------------------------
    agg = (
        long.groupby(["kernel", "version"])
        .agg(
            n_tests=("test", "nunique"),
            median_ratio=("ratio", "median"),
            p25_ratio=("ratio", lambda s: s.quantile(0.25)),
            p75_ratio=("ratio", lambda s: s.quantile(0.75)),
            frac_higher=("ratio", lambda s: (s > 1.0).mean()),
            frac_clearly_slower=("clearly_slower", "mean"),
            frac_clearly_faster=("clearly_faster", "mean"),
            frac_over_150=("ratio", lambda s: (s > 1.5).mean()),
            median_cv=("cv", "median"),
        )
        .reset_index()
        .sort_values("version")
    )
    agg.to_csv(outdir / "relative_latency_by_kernel.csv", index=False)

    # ---- per-test noise ---------------------------------------------------
    noise = (
        long.groupby("test")
        .agg(median_cv=("cv", "median"), p90_cv=("cv", lambda s: s.quantile(0.90)))
        .reset_index()
        .sort_values("median_cv", ascending=False)
    )
    noise.to_csv(outdir / "noise_by_test.csv", index=False)

    # ---- headline numbers -------------------------------------------------
    # the sweep is the 34 kernels that are part of the paper's release list;
    # 4.4.0-210 (and its nopti twin) is the recovery kernel used for the
    # extension experiment, so it is counted separately.
    later = long[(long["kernel"] != base) & (~long["is_extension"])]
    n = len(later)
    print("=" * 72)
    print(f"baseline kernel            : {base}")
    print(f"sweep kernels compared     : {later['kernel'].nunique()} (excluding baseline and extension)")
    print(f"measurements vs baseline   : {n}")
    print(f"  higher mean              : {int((later['ratio'] > 1).sum())} "
          f"({(later['ratio'] > 1).mean():.1%})")
    print(f"  mean >= 50% higher       : {int((later['ratio'] > 1.5).sum())} "
          f"({(later['ratio'] > 1.5).mean():.1%})")
    print(f"  clearly slower (no overlap): {int(later['clearly_slower'].sum())} "
          f"({later['clearly_slower'].mean():.1%})")
    print(f"  clearly faster (no overlap): {int(later['clearly_faster'].sum())} "
          f"({later['clearly_faster'].mean():.1%})")
    print(f"median ratio, all later     : {later['ratio'].median():.3f}")
    print(f"median CV (stdev/mean)      : {long['cv'].median():.1%}")
    print(f"tests whose median CV > 20% : {int((noise['median_cv'] > 0.20).sum())} / {len(noise)}")

    # ---- per-test verdict (sweep only) ------------------------------------
    per_test = (
        later.groupby("test")
        .agg(
            median_ratio=("ratio", "median"),
            frac_clearly_slower=("clearly_slower", "mean"),
            frac_clearly_slower_n=("clearly_slower", "sum"),
            frac_clearly_faster=("clearly_faster", "mean"),
            frac_clearly_faster_n=("clearly_faster", "sum"),
            n=("ratio", "size"),
        )
        .reset_index()
        .sort_values("median_ratio", ascending=False)
    )
    per_test.to_csv(outdir / "relative_latency_by_test.csv", index=False)
    print("\nmost-slowed tests (median ratio over the sweep):")
    for _, r in per_test.head(5).iterrows():
        print(f"  {r['test']:22s} {r['median_ratio']:.2f}x   "
              f"clearly slower on {int(r['frac_clearly_slower_n'])}/{int(r['n'])} kernels")
    print("fastest tests:")
    for _, r in per_test.tail(3).iloc[::-1].iterrows():
        print(f"  {r['test']:22s} {r['median_ratio']:.2f}x")

    # trend vs kernel version (sweep only)
    sweep_agg = agg[~agg["kernel"].str.contains("4.4.0-210")]
    xs = sweep_agg[sweep_agg["kernel"] != base]["version"].to_numpy(dtype=float)
    ys = sweep_agg[sweep_agg["kernel"] != base]["median_ratio"].to_numpy(dtype=float)
    slope = np.polyfit(xs, ys, 1)[0] if len(xs) > 2 else float("nan")
    print(f"Spearman(version, median ratio) : {spearman(xs, ys):+.3f}")
    print(f"slope of median ratio per minor version : {slope:+.4f}")

    # the two tests the paper calls exceptions
    for t in ("big write", "big munmap"):
        s = later[later["test"] == t]["ratio"]
        if len(s):
            print(f"{t:12s} median ratio {s.median():.3f}   n={len(s)}")

    print("=" * 72)

    # ---- figures ----------------------------------------------------------
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 160,
            "font.size": 8,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": True,
            "grid.alpha": 0.25,
            "grid.linewidth": 0.5,
        }
    )

    sweep_plot = (
        agg[~agg["kernel"].str.contains("4.4.0-210")]
        .sort_values("version")
        .reset_index(drop=True)
    )
    pos = np.arange(len(sweep_plot))
    labels = [re.match(r"^(\d+\.\d+)", k).group(1) for k in sweep_plot["kernel"]]
    base_pos = int(sweep_plot.index[sweep_plot["kernel"] == base][0])

    def span(ax, lo, hi, color, text):
        m = (sweep_plot["version"] >= lo) & (sweep_plot["version"] <= hi)
        if not m.any():
            return
        i0, i1 = pos[m].min() - 0.5, pos[m].max() + 0.5
        ax.axvspan(i0, i1, color=color, alpha=0.12, lw=0)
        ax.annotate(
            text, xy=((i0 + i1) / 2, 0.97), xycoords=("data", "axes fraction"),
            ha="center", va="top", fontsize=6.2, color=color,
        )

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(7.2, 5.0), sharex=True, constrained_layout=True
    )

    ax1.fill_between(
        pos, sweep_plot["p25_ratio"], sweep_plot["p75_ratio"], color="#4C72B0",
        alpha=0.18, lw=0, label="inter-quartile range across 33 tests",
    )
    ax1.plot(pos, sweep_plot["median_ratio"], "o-", color="#4C72B0", lw=1.3, ms=3.2,
             label="median relative latency")
    ax1.axhline(1.0, color="#C44E52", lw=1.0, ls="--", label="Linux 4.0.5 baseline")
    ax1.axvline(base_pos, color="#C44E52", lw=0.6, ls=":", alpha=0.7)
    span(ax1, 3.10, 3.15, "#8172B3", "3.10-3.15\nsustained slowdown")
    span(ax1, 4.16, 4.18, "#DD8452", "4.16-4.18\nstep change (unexplained)")
    ax1.set_yscale("log")
    ax1.set_ylim(0.4, 2.2)
    ax1.minorticks_off()
    ax1.set_yticks([0.5, 0.75, 1.0, 1.5, 2.0])
    ax1.set_yticklabels(["0.5x", "0.75x", "1x", "1.5x", "2x"])
    ax1.set_ylabel("latency / 4.0.5 latency  (log scale)")
    ax1.set_title(
        "A  Median relative latency of the 33 LEBench tests, one point per kernel",
        loc="left", fontsize=8.5,
    )
    ax1.legend(frameon=False, fontsize=6.8, loc="lower left")

    ax2.bar(pos, sweep_plot["frac_clearly_slower"] * 100, width=0.62, color="#C44E52",
            label="clearly slower (mean$\\pm$stdev intervals disjoint)")
    ax2.bar(pos, -sweep_plot["frac_clearly_faster"] * 100, width=0.62, color="#55A868",
            label="clearly faster")
    ax2.axhline(0, color="black", lw=0.6)
    ax2.set_ylim(-100, 100)
    ax2.set_ylabel("% of the 33 tests")
    ax2.set_title("B  Tests that clear the noise floor", loc="left", fontsize=8.5)
    ax2.legend(frameon=False, fontsize=6.8, loc="upper left")

    step = 2
    ax2.set_xticks(pos[::step])
    ax2.set_xticklabels(labels[::step], rotation=90, fontsize=6.5)
    ax2.set_xlabel("kernel release, in boot order (ordinal axis)")

    fig.savefig(outdir / "fig_trend.png", bbox_inches="tight")
    plt.close(fig)

    fig2, ax = plt.subplots(figsize=(6.4, 2.8), constrained_layout=True)
    ax.hist(long["cv"].dropna() * 100, bins=40, color="#4C72B0", alpha=0.85)
    ax.axvline(20, color="#C44E52", ls="--", lw=1.0)
    ax.set_xlabel("run-to-run coefficient of variation, stdev / mean  (%)")
    ax.set_ylabel("measurements")
    ax.set_title(
        "Noise floor: variation that is not a kernel-version effect",
        loc="left", fontsize=8.5,
    )
    fig2.savefig(outdir / "fig_noise.png", bbox_inches="tight")
    plt.close(fig2)

    fig3, ax = plt.subplots(figsize=(6.4, 4.4), constrained_layout=True)
    pt = per_test.sort_values("median_ratio")
    colors = ["#C44E52" if v > 1 else "#55A868" for v in pt["median_ratio"]]
    ax.barh(np.arange(len(pt)), pt["median_ratio"] - 1.0, left=1.0, color=colors,
            height=0.72)
    ax.axvline(1.0, color="black", lw=0.7)
    ax.set_yticks(np.arange(len(pt)))
    ax.set_yticklabels(pt["test"], fontsize=6)
    ax.set_xlabel("median latency ratio vs 4.0.5   (> 1 = slower)")
    ax.set_title("Per-test median across the 33 sweep kernels", loc="left", fontsize=8.5)
    fig3.savefig(outdir / "fig_tests.png", bbox_inches="tight")
    plt.close(fig3)

    for name in (
        "relative_latency_by_kernel.csv",
        "relative_latency_by_test.csv",
        "noise_by_test.csv",
        "fig_trend.png",
        "fig_noise.png",
        "fig_tests.png",
    ):
        print(f"wrote: {outdir / name}")


if __name__ == "__main__":
    main()
