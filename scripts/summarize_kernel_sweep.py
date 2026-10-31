#!/usr/bin/env python3
"""Summarize reduced-sweep CSVs as mean ± sample standard deviation.

Each run CSV is the upstream OS_Eval layout: a kbest row and an average row
per test, with the latency written as seconds.nanoseconds. The published
comparison uses the kbest row. Three run files are required.
"""

import argparse
import csv
import math
import re
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ROW = re.compile(r"^(.*?)\s+(kbest|average):,(\d+)\.(\d+),$")


def parse_run(path):
    values = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        match = ROW.match(line.strip())
        if not match or match.group(2) != "kbest":
            continue
        name = match.group(1).strip()
        seconds = int(match.group(3))
        fraction = match.group(4)
        nanos = seconds * 1_000_000_000 + int(fraction.ljust(9, "0")[:9])
        values[name] = nanos
    return values


def mean_stdev(samples):
    mean = statistics.fmean(samples)
    stdev = statistics.stdev(samples) if len(samples) > 1 else 0.0
    return mean, stdev


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--kernels", type=Path, default=ROOT / "results" / "kernels")
    parser.add_argument("--out", type=Path, default=ROOT / "results" / "kernel_summary.csv")
    args = parser.parse_args()

    rows = []
    for directory in sorted(path for path in args.kernels.iterdir() if path.is_dir()):
        runs = []
        for index in (1, 2, 3):
            csv_path = directory / ("run%d.csv" % index)
            if not csv_path.is_file():
                runs = []
                break
            runs.append(parse_run(csv_path))
        if len(runs) != 3:
            continue
        names = list(runs[0])
        for name in names:
            if any(name not in run for run in runs):
                continue
            samples = [run[name] for run in runs]
            mean, stdev = mean_stdev(samples)
            rows.append(
                {
                    "kernel": directory.name,
                    "test": name,
                    "mean_ns": "%.3f" % mean,
                    "stdev_ns": "%.3f" % stdev,
                    "run1_ns": samples[0],
                    "run2_ns": samples[1],
                    "run3_ns": samples[2],
                }
            )

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=["kernel", "test", "mean_ns", "stdev_ns", "run1_ns", "run2_ns", "run3_ns"],
        )
        writer.writeheader()
        writer.writerows(rows)
    print("wrote %d rows to %s" % (len(rows), args.out))


if __name__ == "__main__":
    main()
