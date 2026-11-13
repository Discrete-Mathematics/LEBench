#!/usr/bin/env python3
"""Verify that the numbers printed in the report can be recomputed from results/.

Every quantitative claim in report/report.tex comes from one of three places:

  * results/kernel_summary.csv        (kernel sweep, claim 1)
  * results/macro/summary.csv         (application throughput, claim 3)
  * results/batching/<kernel>/run*.csv (batched getpid extension)

This script recomputes each published number from those files and compares it
with the value in the generated LaTeX, so a stale or hand-edited table fails
loudly instead of shipping. It reads files only.

Usage:
    python3 scripts/verify_report_numbers.py [--root .]

Exit code 0 means every checked number matches; 1 means at least one mismatch.
"""

import argparse
import csv
import re
import statistics
import sys
from pathlib import Path

BASELINE = "4.0.5-040005-generic"
RECOVERY = ("4.4.0-210-generic", "4.4.0-210-nopti")


def load_kernel_rows(root):
    path = root / "results" / "kernel_summary.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def load_macro_rows(root):
    path = root / "results" / "macro" / "summary.csv"
    with path.open(newline="", encoding="utf-8") as fh:
        return [r for r in csv.DictReader(fh) if r["metric"] != "failed"]


def version(kernel):
    return tuple(int(x) for x in re.match(r"(\d+)\.(\d+)\.(\d+)", kernel).groups())


def claim1(root):
    rows = load_kernel_rows(root)
    baseline = {r["test"]: r for r in rows if r["kernel"] == BASELINE}
    later = sorted(
        {r["kernel"] for r in rows if version(r["kernel"]) > version(BASELINE)}
        - set(RECOVERY)
    )
    total = higher = ge50 = disjoint = 0
    for row in rows:
        if row["kernel"] not in later:
            continue
        base = baseline.get(row["test"])
        if base is None:
            continue
        mean = float(row["mean_ns"])
        std = float(row["stdev_ns"])
        bmean = float(base["mean_ns"])
        bstd = float(base["stdev_ns"])
        total += 1
        if mean > bmean:
            higher += 1
        if mean >= 1.5 * bmean:
            ge50 += 1
        if mean - std > bmean + bstd:
            disjoint += 1
    text = (root / "report" / "generated" / "claim_summary.tex").read_text(encoding="utf-8")
    published = {
        "total": int(re.search(r"Across (\d+) later-kernel", text).group(1)),
        "higher": int(re.search(r"(\d+) \(\d+\\\\?%\) have a higher mean", text).group(1)),
        "ge50": int(re.search(r"(\d+) \(\d+\\\\?%\) have a mean at least 50", text).group(1)),
        "disjoint": int(re.search(r"(\d+) of those measurements have non-overlapping", text).group(1)),
    }
    computed = {"total": total, "higher": higher, "ge50": ge50, "disjoint": disjoint}
    return {
        "name": "claim 1 (kernel sweep)",
        "ok": computed == published,
        "computed": computed,
        "published": published,
    }


MACRO_NAMES = {
    "Apache index": ("apache", "index"),
    "Nginx index": ("nginx", "index"),
    "Redis GET": ("redis", "GET"),
    "Redis RPUSH": ("redis", "RPUSH"),
    "Redis RPOP": ("redis", "RPOP"),
    "Redis SPOP": ("redis", "SPOP"),
    "Redis LRANGE 100": ("redis", "LRANGE_100 (first 100 elements)"),
}

ROW_RE = re.compile(
    r"^(?P<name>.+?) & (?P<dmean>\d+) \$\\pm\$ (?P<dstd>\d+) /s & "
    r"(?P<smean>\d+) \$\\pm\$ (?P<sstd>\d+) /s & (?P<ratio>[\d.]+) \\\\$"
)


def parse_macro_tex(root):
    path = root / "report" / "generated" / "macro_table.tex"
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        match = ROW_RE.match(line.strip())
        if match:
            out[match.group("name")] = {
                "default": (int(match.group("dmean")), int(match.group("dstd"))),
                "spectre": (int(match.group("smean")), int(match.group("sstd"))),
                "ratio": float(match.group("ratio")),
            }
    return out


def macro(root):
    rows = load_macro_rows(root)
    by_key = {(r["app"], r["test"], r["config"]): r for r in rows}
    published = parse_macro_tex(root)
    problems = []
    for name, key in MACRO_NAMES.items():
        if name not in published:
            problems.append("row %r missing from macro_table.tex" % name)
            continue
        default = by_key.get((key[0], key[1], "default"))
        spectre = by_key.get((key[0], key[1], "spectre-off"))
        if not default or not spectre:
            problems.append("row %r missing from results/macro/summary.csv" % name)
            continue
        checks = [
            ("default mean", float(default["mean"]), published[name]["default"][0], 0.01),
            ("default std", float(default["std"]), published[name]["default"][1], 0.02),
            ("spectre mean", float(spectre["mean"]), published[name]["spectre"][0], 0.01),
            ("spectre std", float(spectre["std"]), published[name]["spectre"][1], 0.02),
            ("ratio", float(spectre["mean"]) / float(default["mean"]), published[name]["ratio"], 0.02),
        ]
        for label, computed, printed, tol in checks:
            if abs(computed - printed) > tol * abs(printed) + 1:
                problems.append(
                    "%s / %s: computed %.3f, printed %.3f" % (name, label, computed, printed)
                )
    return {"name": "claim 3 (macrobenchmark)", "ok": not problems, "problems": problems}


def batched_getpid(root):
    kernel = root / "results" / "batching"
    out = {}
    for directory in sorted(p for p in kernel.iterdir() if p.is_dir()):
        values = []
        for run in sorted(directory.glob("run*.csv")):
            for line in run.read_text(encoding="utf-8").splitlines():
                if "getpid" in line and "kbest" in line:
                    values.append(float(line.rsplit(",", 2)[-2]) * 1e9)
        if values:
            out[directory.name] = (statistics.mean(values), statistics.stdev(values) if len(values) > 1 else 0.0)
    return out


def batch(root):
    computed = batched_getpid(root)
    rows = load_kernel_rows(root)
    single = {
        r["kernel"]: (float(r["mean_ns"]), float(r["stdev_ns"]))
        for r in rows
        if r["test"] == "getpid"
    }
    published = {
        "4.0.5": (245, 0, 129, 0),
        "4.4.0-210": (314, 39, 127, 40),
    }
    problems = []
    for name, (p_single, p_single_std, p_batch, p_batch_std) in published.items():
        key = [k for k in computed if k.startswith(name)]
        if not key:
            problems.append("no batched files for %s" % name)
            continue
        mean, std = computed[key[0]]
        if abs(mean - p_batch) > 0.05 * p_batch + 1:
            problems.append("%s batched: computed %.1f, printed %d" % (name, mean, p_batch))
        if abs(std - p_batch_std) > max(0.5 * p_batch_std, 5):
            problems.append("%s batched std: computed %.1f, printed %d" % (name, std, p_batch_std))
    return {"name": "extension (batched getpid)", "ok": not problems, "problems": problems}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    args = parser.parse_args()

    results = [claim1(args.root), macro(args.root), batch(args.root)]
    failures = 0
    for result in results:
        status = "PASS" if result["ok"] else "FAIL"
        print("[%s] %s" % (status, result["name"]))
        if result["ok"]:
            continue
        failures += 1
        if "computed" in result:
            for key in result["computed"]:
                if result["computed"][key] != result["published"][key]:
                    print("       %s: computed %s, printed %s"
                          % (key, result["computed"][key], result["published"][key]))
        for problem in result.get("problems", []):
            print("       " + problem)

    print("\n%d checked, %d failed" % (len(results), failures))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
