#!/usr/bin/env python3
"""Aggregate LEBench CSVs into mean and sample standard deviation.

Each OS_Eval CSV has one K-best latency and one average latency per
test, in seconds. This script reads every run*/output.*.csv under a
batch directory and writes summary.csv with the cross-run mean and
sample standard deviation (n - 1). Numbers in the report should cite
that file together with the raw CSVs.
"""

import argparse
import csv
import math
import statistics
import sys
import tempfile
from pathlib import Path


def parse_latency_csv(path):
    """Return {test_name: {"kbest": float, "average": float}}."""
    parsed = {}
    text = path.read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines():
        kind = None
        if "kbest:" in line:
            kind = "kbest"
        elif "average:" in line:
            kind = "average"
        else:
            continue
        left, value, _rest = (line.split(",", 2) + ["", ""])[:3]
        name = left.split(kind + ":")[0].strip()
        if not name:
            raise ValueError("missing test name in %s: %r" % (path, line))
        parsed.setdefault(name, {})[kind] = float(value.strip())
    if not parsed:
        raise ValueError("no latency rows in %s" % path)
    return parsed


def aggregate(runs):
    """runs is a list of parse_latency_csv() results, in run order."""
    names = []
    for run in runs:
        for name in run:
            if name not in names:
                names.append(name)

    rows = []
    for name in names:
        row = {"test": name, "runs": len(runs)}
        for kind in ("kbest", "average"):
            values = []
            for run in runs:
                if kind not in run.get(name, {}):
                    raise ValueError("run is missing %s %s" % (name, kind))
                values.append(run[name][kind])
            mean = statistics.fmean(values)
            # One observation has no sample standard deviation.
            stdev = statistics.stdev(values) if len(values) >= 2 else math.nan
            row["%s_mean_sec" % kind] = mean
            row["%s_stdev_sec" % kind] = stdev
            row["%s_values_sec" % kind] = " ".join("%.9f" % value for value in values)
        rows.append(row)
    return rows


def write_summary(batch, rows):
    destination = Path(batch) / "summary.csv"
    fieldnames = [
        "test",
        "runs",
        "kbest_mean_sec",
        "kbest_stdev_sec",
        "kbest_values_sec",
        "average_mean_sec",
        "average_stdev_sec",
        "average_values_sec",
    ]
    with destination.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            formatted = dict(row)
            for key in (
                "kbest_mean_sec",
                "kbest_stdev_sec",
                "average_mean_sec",
                "average_stdev_sec",
            ):
                formatted[key] = "%.9f" % formatted[key]
            writer.writerow(formatted)
    return destination


def collect_runs(batch):
    batch = Path(batch)
    csv_paths = sorted(batch.glob("run*/output.*.csv"))
    if not csv_paths:
        raise SystemExit("no run*/output.*.csv files under %s" % batch)
    return [parse_latency_csv(path) for path in csv_paths]


def self_test():
    """Check parsing and the mean/stdev arithmetic on synthetic CSVs."""
    sample = (
        "OS Benchmark experiment\n"
        "Test Name:,6.8.0-sample,\n"
        "       ref          kbest:,0.000000100,\n"
        "       ref        average:,0.000000120,\n"
        " small read          kbest:,0.000001000,\n"
        " small read        average:,0.000001500,\n"
    )
    other = sample.replace("0.000000100", "0.000000300").replace(
        "0.000001000", "0.000003000"
    )
    with tempfile.TemporaryDirectory() as tmp:
        batch = Path(tmp)
        for index, body in enumerate((sample, other), start=1):
            run_dir = batch / ("run%d" % index)
            run_dir.mkdir()
            (run_dir / "output.sample.csv").write_text(body, encoding="utf-8")
        rows = aggregate(collect_runs(batch))
        by_name = {row["test"]: row for row in rows}
        ref = by_name["ref"]
        if abs(ref["kbest_mean_sec"] - 0.0000002) > 1e-15:
            raise SystemExit("ref mean mismatch: %s" % ref["kbest_mean_sec"])
        expected_stdev = statistics.stdev([0.0000001, 0.0000003])
        if abs(ref["kbest_stdev_sec"] - expected_stdev) > 1e-15:
            raise SystemExit("ref stdev mismatch: %s" % ref["kbest_stdev_sec"])
        destination = write_summary(batch, rows)
        text = destination.read_text(encoding="utf-8")
        if "small read" not in text or "kbest_mean_sec" not in text:
            raise SystemExit("summary.csv missing expected columns")
    print("summarize_runs self-test passed")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "batch",
        nargs="?",
        help="results/<kernel>/<timestamp> directory containing run*/",
    )
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.batch:
        raise SystemExit("pass a batch directory, or --self-test")
    rows = aggregate(collect_runs(args.batch))
    destination = write_summary(args.batch, rows)
    print("wrote %s" % destination)


if __name__ == "__main__":
    sys.exit(main() or 0)
