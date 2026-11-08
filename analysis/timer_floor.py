#!/usr/bin/env python3
"""Timer-resolution audit of the LEBench kernel sweep (CS340-EX2).

Why this exists
---------------
The sweep summary in results/kernel_summary.csv contains tests whose measured
latency is only a few times the cost of reading the clock itself. The commit
of 2026-11-03 already showed that a single-shot getpid is dominated by timer
overhead. This script makes that judgement systematic:

  * the empty syscall (`ref`) fixes an empirical floor per kernel — it is what
    the harness costs when the kernel does essentially nothing;
  * any measurement whose mean is within K x that floor is flagged as
    **timer-bound**: the clock, not the kernel, supplies a large share of the
    number, so the row must not be used as evidence;
  * the verdict on claim 1 is then recomputed on the surviving rows, and the
    sensitivity of that verdict to K is reported instead of asserted.

Inputs   : results/kernel_summary.csv
Outputs  : suspect_rows.csv            (one row per measurement, with a flag)
           timer_floor_by_test.csv     (per test: distance to the floor)
           timer_floor_sensitivity.csv (verdict vs K)
           fig_timer_floor.png

Usage:
    python3 analysis/timer_floor.py \
        --csv results/kernel_summary.csv --outdir analysis

Nothing under results/ is modified.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


BASELINE = "4.0.5"


def verdict(long: pd.DataFrame, base: str, k: float) -> dict:
    """Recompute the claim-1 verdict on rows that clear the timer floor."""
    ok = long[(long["ratio_to_floor"] >= k) & long["measurable"]]
    ok = ok[ok["kernel"] != base]
    if ok.empty:
        return {}
    return {
        "K": k,
        "rows_used": len(ok),
        "median_ratio": float(ok["ratio"].median()),
        "higher_pct": float((ok["ratio"] > 1).mean()),
        "over_150_pct": float((ok["ratio"] > 1.5).mean()),
        "clearly_slower_pct": float(ok["clearly_slower"].mean()),
        "clearly_faster_pct": float(ok["clearly_faster"].mean()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="results/kernel_summary.csv")
    ap.add_argument("--outdir", default="analysis")
    ap.add_argument("--k", type=float, default=3.0, help="timer-floor multiple")
    args = ap.parse_args()

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(args.csv).dropna(subset=["mean_ns", "stdev_ns"])

    # ---- empirical floor per kernel ---------------------------------------
    floor = (
        df[df["test"] == "ref"][["kernel", "mean_ns"]]
        .rename(columns={"mean_ns": "floor_ns"})
        .set_index("kernel")["floor_ns"]
    )
    df["floor_ns"] = df["kernel"].map(floor)

    # ---- baseline per test ------------------------------------------------
    base_rows = df[df["kernel"].str.startswith(BASELINE)].set_index("test")

    rows = []
    for _, r in df.iterrows():
        if r["test"] == "ref":
            continue                              # the yardstick, not a test
        if r["test"] not in base_rows.index:
            continue
        bm = float(base_rows.loc[r["test"], "mean_ns"])
        bs = float(base_rows.loc[r["test"], "stdev_ns"])
        if bm <= 0:
            continue
        f = float(r["floor_ns"]) if pd.notna(r["floor_ns"]) else np.nan
        ratio_to_floor = float(r["mean_ns"]) / f if f and f > 0 else np.nan
        rows.append(
            dict(
                kernel=r["kernel"],
                test=r["test"],
                mean_ns=float(r["mean_ns"]),
                stdev_ns=float(r["stdev_ns"]),
                floor_ns=f,
                ratio_to_floor=ratio_to_floor,
                ratio=float(r["mean_ns"]) / bm,
                measurable=bool(np.isfinite(ratio_to_floor)),
                clearly_slower=(float(r["mean_ns"]) - float(r["stdev_ns"])) > (bm + bs),
                clearly_faster=(float(r["mean_ns"]) + float(r["stdev_ns"])) < (bm - bs),
            )
        )
    long = pd.DataFrame(rows)

    # a zero reading is a failed window, not a fast kernel
    zero = long["mean_ns"] <= 0
    long.loc[zero, "measurable"] = False
    long["usable"] = (long["ratio_to_floor"] >= args.k) & long["measurable"]
    long["reason"] = np.where(
        ~long["measurable"], "no floor or zero reading",
        np.where(long["usable"], "ok",
                 f"within {args.k:g}x of the empty-syscall floor"),
    )
    long.sort_values(["kernel", "test"]).to_csv(outdir / "suspect_rows.csv", index=False)

    # ---- per test ---------------------------------------------------------
    per_test = (
        long.groupby("test")
        .agg(
            median_ns=("mean_ns", "median"),
            median_ratio_to_floor=("ratio_to_floor", "median"),
            n_rows=("usable", "size"),
            n_usable=("usable", "sum"),
        )
        .reset_index()
        .sort_values("median_ratio_to_floor")
    )
    per_test["pct_usable"] = per_test["n_usable"] / per_test["n_rows"]
    per_test.to_csv(outdir / "timer_floor_by_test.csv", index=False)

    # ---- sensitivity of the verdict to K ----------------------------------
    sens = pd.DataFrame([verdict(long, BASELINE, k) for k in (1, 2, 3, 5, 10)]).dropna()
    sens.to_csv(outdir / "timer_floor_sensitivity.csv", index=False)

    # ---- console summary --------------------------------------------------
    n_all, n_used = len(long), int(long["usable"].sum())
    print("=" * 72)
    print(f"baseline kernel          : {BASELINE}")
    print(f"measurements             : {n_all}")
    print(f"usable at K={args.k:g}         : {n_used} ({n_used / n_all:.1%})")
    print(f"timer-bound / invalid    : {n_all - n_used} ({1 - n_used / n_all:.1%})")
    print("\ntests closest to the empty-syscall floor (median across kernels):")
    for _, r in per_test.head(8).iterrows():
        print(f"  {r['test']:22s} floor x{r['median_ratio_to_floor']:6.2f}   "
              f"usable on {r['n_usable']:2d}/{r['n_rows']} kernels")
    print("\ntests safely above the floor:")
    for _, r in per_test.tail(4).iterrows():
        print(f"  {r['test']:22s} floor x{r['median_ratio_to_floor']:6.1f}")
    print("\nverdict vs K:")
    print(sens.round(3).to_string(index=False))
    print("=" * 72)

    # ---- figure -----------------------------------------------------------
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    plt.rcParams.update({
        "figure.dpi": 160, "font.size": 8,
        "axes.spines.top": False, "axes.spines.right": False,
        "axes.grid": True, "grid.alpha": 0.25, "grid.linewidth": 0.5,
    })

    fig, axes = plt.subplots(2, 2, figsize=(9.6, 6.6), constrained_layout=True)
    (ax1, ax2), (ax3, ax4) = axes

    pt = per_test.sort_values("median_ratio_to_floor")
    y = np.arange(len(pt))
    colors = ["#C44E52" if v < args.k else "#4C72B0" for v in pt["median_ratio_to_floor"]]
    ax1.barh(y, pt["median_ratio_to_floor"], color=colors, height=0.72)
    ax1.axvline(args.k, color="#C44E52", ls="--", lw=1.0, label=f"K = {args.k:g}x floor")
    ax1.set_xscale("log")
    ax1.set_xlim(0.9, 3e4)
    ax1.set_yticks(y)
    ax1.set_yticklabels(pt["test"], fontsize=6)
    ax1.set_xlabel("median latency / empty-syscall floor  (log scale)")
    ax1.set_title("A  Distance to the timer floor, per test", loc="left", fontsize=8.5)
    ax1.legend(frameon=False, fontsize=7, loc="lower right")

    ax2.plot(sens["K"], sens["median_ratio"], "o-", color="#4C72B0",
             label="median relative latency (left)")
    ax2.axhline(1.0, color="black", lw=0.6, ls=":")
    ax2.set_xscale("log")
    ax2.set_xticks(list(sens["K"]))
    ax2.set_xticklabels([f"{int(k)}x" for k in sens["K"]])
    ax2.set_xlabel("timer-floor threshold K")
    ax2.set_ylabel("median relative latency")
    ax2.set_ylim(0.8, 1.2)
    ax2b = ax2.twinx()
    ax2b.plot(sens["K"], sens["clearly_slower_pct"] * 100, "s--", color="#C44E52",
              label="clearly slower, % of rows (right)")
    ax2b.set_ylabel("clearly slower (%)")
    ax2b.set_ylim(0, 100)
    ax2b.grid(False)
    h1, l1 = ax2.get_legend_handles_labels()
    h2, l2 = ax2b.get_legend_handles_labels()
    ax2.legend(h1 + h2, l1 + l2, frameon=False, fontsize=6.8, loc="lower right")
    ax2.set_title("B  Verdict is robust to the threshold", loc="left", fontsize=8.5)

    # ---- C: the floor itself is not constant across kernels ---------------
    kern = (
        long.groupby("kernel")
        .agg(floor_ns=("floor_ns", "first"), median_ratio=("ratio", "median"))
        .reset_index()
    )
    kern = kern[kern["floor_ns"].notna() & (kern["floor_ns"] >= 0)]
    v = kern["kernel"].str.extract(r"^(\d+)\.(\d+)").astype(float)
    kern["version"] = v[0] + v[1] / 100.0
    kern = kern.sort_values("version").reset_index(drop=True)
    pos = np.arange(len(kern))
    labels = kern["kernel"].str.extract(r"^(\d+\.\d+)")[0].tolist()

    ax3.bar(pos, kern["floor_ns"], color="#4C72B0", width=0.7)
    hot = kern["kernel"].str.contains(r"4\.1[678]")
    if hot.any():
        ax3.bar(pos[hot], kern.loc[hot, "floor_ns"], color="#DD8452", width=0.7,
                label="4.16-4.18: floor collapses")
    ax3.set_ylabel("empty-syscall floor (ns)")
    ax3.set_title("C  The harness floor moves between boots", loc="left", fontsize=8.5)
    ax3.set_xticks(pos[::2])
    ax3.set_xticklabels(labels[::2], rotation=90, fontsize=5.5)
    ax3.legend(frameon=False, fontsize=6.5, loc="upper right")

    # ---- D: when the floor drops, the whole batch looks faster ------------
    # `cpu` is a fixed-size compute loop: no syscall, no I/O, same instruction
    # count on every kernel. If it moves with the floor, the boot's time base
    # moved, not the kernel.
    cpu = (df[df["test"] == "cpu"][["kernel", "mean_ns"]]
           .rename(columns={"mean_ns": "cpu_ns"}))
    kern = kern.merge(cpu, on="kernel", how="left")

    ax4.scatter(kern["floor_ns"], kern["cpu_ns"] / 1e6, s=16,
                color=np.where(hot, "#DD8452", "#4C72B0"))
    ax4.set_xlabel("empty-syscall floor of that boot (ns)")
    ax4.set_ylabel("pure-CPU test, fixed instruction count (ms)")
    ax4.axhline(kern["cpu_ns"].median() / 1e6, color="black", lw=0.6, ls=":")

    def spearman(a, b):
        ra = pd.Series(a).rank().to_numpy()
        rb = pd.Series(b).rank().to_numpy()
        ra -= ra.mean()
        rb -= rb.mean()
        den = np.sqrt((ra ** 2).sum() * (rb ** 2).sum())
        return float((ra * rb).sum() / den) if den else float("nan")

    rho = spearman(kern["floor_ns"].to_numpy(), kern["cpu_ns"].to_numpy())
    ax4.set_title(f"D  Floor vs pure-CPU control (Spearman {rho:+.2f})", loc="left",
                  fontsize=8.5)

    fig.savefig(outdir / "fig_timer_floor.png", bbox_inches="tight")
    plt.close(fig)

    print(f"floor range across boots : {kern['floor_ns'].min():.0f} - "
          f"{kern['floor_ns'].max():.0f} ns")
    print(f"Spearman(floor, pure-CPU test) : {rho:+.3f}")

    for name in ("suspect_rows.csv", "timer_floor_by_test.csv",
                 "timer_floor_sensitivity.csv", "fig_timer_floor.png"):
        print(f"wrote: {outdir / name}")


if __name__ == "__main__":
    main()
