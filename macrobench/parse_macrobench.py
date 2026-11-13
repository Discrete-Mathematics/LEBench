#!/usr/bin/env python3
"""Aggregate macrobenchmark results into mean +/- std and ratios against `default`.

Reads every ``results/macro/<config>/results.csv`` under the given root and writes
``summary.csv`` / ``summary.txt`` at that root.

Python 3.5 compatible: the Ubuntu 16.04.6 guest ships python3.5 (no f-strings).
"""

import argparse
import csv
import os
import statistics
from collections import defaultdict


def load_rows(root):
    rows = []
    for dirpath, _dirnames, filenames in os.walk(root):
        if "results.csv" not in filenames:
            continue
        path = os.path.join(dirpath, "results.csv")
        with open(path, newline="", encoding="utf-8") as handle:
            for row in csv.DictReader(handle):
                try:
                    value = float(row["value"])
                except (KeyError, TypeError, ValueError):
                    continue
                rows.append(
                    {
                        "config": row.get("config", ""),
                        "app": row.get("app", ""),
                        "test": row.get("test", ""),
                        "metric": row.get("metric", ""),
                        "unit": row.get("unit", ""),
                        "value": value,
                    }
                )
    return rows


def aggregate(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[(row["config"], row["app"], row["test"], row["metric"])].append(row["value"])

    stats = {}
    for key, values in groups.items():
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.0
        stats[key] = {
            "n": len(values),
            "mean": mean,
            "std": std,
            "min": min(values),
            "max": max(values),
            "unit": next(r["unit"] for r in rows if (r["config"], r["app"], r["test"], r["metric"]) == key),
        }
    return stats


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("root", help="results/macro directory")
    args = parser.parse_args(argv)

    rows = load_rows(args.root)
    if not rows:
        raise SystemExit("no results.csv rows found under " + args.root)

    stats = aggregate(rows)

    # baseline per (app, test, metric)
    baseline = {}
    for (config, app, test, metric), values in stats.items():
        if config == "default":
            baseline[(app, test, metric)] = values["mean"]

    out_csv = os.path.join(args.root, "summary.csv")
    out_txt = os.path.join(args.root, "summary.txt")
    lines = []
    with open(out_csv, "w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            ["config", "app", "test", "metric", "n", "mean", "std", "min", "max", "unit", "ratio_vs_default"]
        )
        for key in sorted(stats):
            config, app, test, metric = key
            values = stats[key]
            base = baseline.get((app, test, metric))
            ratio = ""
            if base:
                ratio = "%.4f" % (values["mean"] / base)
            writer.writerow(
                [
                    config,
                    app,
                    test,
                    metric,
                    values["n"],
                    "%.6g" % values["mean"],
                    "%.6g" % values["std"],
                    "%.6g" % values["min"],
                    "%.6g" % values["max"],
                    values["unit"],
                    ratio,
                ]
            )
            lines.append(
                "%-12s %-7s %-8s %-12s n=%d  %10.4g +/- %8.3g %-8s ratio=%s"
                % (
                    config,
                    app,
                    test,
                    metric,
                    values["n"],
                    values["mean"],
                    values["std"],
                    values["unit"],
                    ratio if ratio else "-",
                )
            )

    with open(out_txt, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines) + "\n")

    print("\n".join(lines))
    print("\nwrote %s and %s" % (out_csv, out_txt))


if __name__ == "__main__":
    main()
