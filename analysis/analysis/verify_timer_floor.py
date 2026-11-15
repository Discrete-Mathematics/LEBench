#!/usr/bin/env python3
"""Verify the numbers published in docs/timer-floor.md against results/.

`scripts/verify_report_numbers.py` checks the numbers in the *report*. This
script does the same job for the timer-floor note in `docs/`, so that a reader
(or the TA) can re-derive every claim in it with one command and get a
pass/fail, not a paragraph.

It recomputes, from `results/kernel_summary.csv` alone:

  * the number of measurements and how many clear the timer floor (K = 3)
  * the median relative latency and the share of clearly slower rows
  * the range of the empty-syscall floor across boots
  * the pure-CPU control in the 4.16-4.18 window that exposes the artifact

and compares each with the value quoted in the note. Any drift fails the run,
which is what should happen if the sweep or the note is edited.

Usage:
    python3 analysis/verify_timer_floor.py [--csv results/kernel_summary.csv]

Exit code 0 when every check passes, 1 otherwise.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

BASELINE = "4.0.5"
K = 3.0

# Every constant below is quoted in docs/timer-floor.md.
EXPECTED = {
    "measurements": 1152,
    "usable_at_k3": 1096,
    "timer_bound": 56,
    "median_ratio": 1.032,
    "clearly_slower_share": 0.271,
    "floor_max_ns": 305.3,          # 3.7.9, 305.333 ns
    "spearman_floor_cpu": 0.457,
}


def spearman(a: np.ndarray, b: np.ndarray) -> float:
    ra = pd.Series(a).rank().to_numpy()
    rb = pd.Series(b).rank().to_numpy()
    ra = ra - ra.mean()
    rb = rb - rb.mean()
    den = np.sqrt((ra**2).sum() * (rb**2).sum())
    return float((ra * rb).sum() / den) if den else float("nan")


def compute(csv_path: Path) -> dict:
    df = pd.read_csv(csv_path).dropna(subset=["mean_ns", "stdev_ns"])

    floor = (
        df[df["test"] == "ref"][["kernel", "mean_ns"]]
        .rename(columns={"mean_ns": "floor_ns"})
        .set_index("kernel")["floor_ns"]
    )
    df["floor_ns"] = df["kernel"].map(floor)
    base_rows = df[df["kernel"].str.startswith(BASELINE)].set_index("test")

    rows = []
    for _, r in df.iterrows():
        if r["test"] == "ref" or r["test"] not in base_rows.index:
            continue
        bm = float(base_rows.loc[r["test"], "mean_ns"])
        bs = float(base_rows.loc[r["test"], "stdev_ns"])
        if bm <= 0:
            continue
        f = float(r["floor_ns"]) if pd.notna(r["floor_ns"]) else np.nan
        rtf = float(r["mean_ns"]) / f if f and f > 0 else np.nan
        rows.append(dict(
            kernel=r["kernel"], test=r["test"], mean_ns=float(r["mean_ns"]),
            floor_ns=f, ratio_to_floor=rtf, ratio=float(r["mean_ns"]) / bm,
            measurable=bool(np.isfinite(rtf)),
            clearly_slower=(float(r["mean_ns"]) - float(r["stdev_ns"])) > (bm + bs),
        ))
    long = pd.DataFrame(rows)
    long.loc[long["mean_ns"] <= 0, "measurable"] = False
    long["usable"] = (long["ratio_to_floor"] >= K) & long["measurable"]

    later = long[~long["kernel"].str.startswith(BASELINE)]

    cpu = df[df["test"] == "cpu"][["kernel", "mean_ns"]].rename(columns={"mean_ns": "cpu_ns"})
    kern = (long.groupby("kernel").agg(floor_ns=("floor_ns", "first")).reset_index()
            .merge(cpu, on="kernel", how="left"))
    kern = kern[kern["floor_ns"].notna() & (kern["floor_ns"] >= 0)]

    hot = kern["kernel"].str.contains(r"4\.1[678]")
    cpu_hot = kern.loc[hot, "cpu_ns"].median()
    cpu_rest = kern.loc[~hot, "cpu_ns"].median()

    return {
        "measurements": len(long),
        "usable_at_k3": int(long["usable"].sum()),
        "timer_bound": int((~long["usable"]).sum()),
        "median_ratio": float(later.loc[later["usable"], "ratio"].median()),
        "clearly_slower_share": float(later.loc[later["usable"], "clearly_slower"].mean()),
        "floor_min_ns": float(kern["floor_ns"].min()),
        "floor_max_ns": float(kern["floor_ns"].max()),
        "spearman_floor_cpu": spearman(kern["floor_ns"].to_numpy(), kern["cpu_ns"].to_numpy()),
        "cpu_hot_ms": float(cpu_hot) / 1e6,
        "cpu_rest_ms": float(cpu_rest) / 1e6,
        "floor_3_6_10": float(kern.loc[kern["kernel"].str.startswith("3.6.10"), "floor_ns"].iloc[0]),
    }


def close(actual: float, expected: float, tol: float) -> bool:
    return abs(actual - expected) <= tol


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--csv", default="results/kernel_summary.csv")
    args = ap.parse_args()

    path = Path(args.csv)
    if not path.exists():
        print(f"[FAIL] input not found: {path}", file=sys.stderr)
        return 1

    m = compute(path)

    checks = [
        ("measurements in docs/timer-floor.md", m["measurements"],
         EXPECTED["measurements"], 0),
        ("rows usable at K=3", m["usable_at_k3"], EXPECTED["usable_at_k3"], 0),
        ("timer-bound or invalid rows", m["timer_bound"], EXPECTED["timer_bound"], 0),
        ("median relative latency", m["median_ratio"], EXPECTED["median_ratio"], 0.005),
        ("share of clearly-slower rows", m["clearly_slower_share"],
         EXPECTED["clearly_slower_share"], 0.005),
        ("largest empty-syscall floor (ns)", m["floor_max_ns"],
         EXPECTED["floor_max_ns"], 0.6),
        ("Spearman(floor, pure-CPU test)", m["spearman_floor_cpu"],
         EXPECTED["spearman_floor_cpu"], 0.02),
    ]

    failed = 0
    for name, actual, expected, tol in checks:
        ok = close(actual, expected, tol)
        failed += 0 if ok else 1
        flag = "PASS" if ok else "FAIL"
        if isinstance(expected, int):
            print(f"[{flag}] {name:38s} {actual} (expected {expected})")
        else:
            print(f"[{flag}] {name:38s} {actual:.3f} (expected {expected:.3f})")

    # structural checks that do not need a tolerance
    struct = [
        ("3.6.10 boot has a zero floor", m["floor_3_6_10"] == 0.0),
        ("pure-CPU control halves in 4.16-4.18",
         m["cpu_hot_ms"] < 0.6 * m["cpu_rest_ms"]),
    ]
    for name, ok in struct:
        failed += 0 if ok else 1
        print(f"[{'PASS' if ok else 'FAIL'}] {name:38s} "
              f"hot={m['cpu_hot_ms']:.2f} ms, rest={m['cpu_rest_ms']:.2f} ms"
              if name.startswith("pure-CPU") else
              f"[{'PASS' if ok else 'FAIL'}] {name:38s} floor={m['floor_3_6_10']:.0f} ns")

    total = len(checks) + len(struct)
    print(f"\n{total - failed} checked, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

