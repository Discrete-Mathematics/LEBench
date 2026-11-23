#!/usr/bin/env python3
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def kbest(path):
    vals = {}
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if "kbest" not in line:
            continue
        name = line.split("kbest")[0].strip()
        nums = [p for p in line.split(",") if p.strip()[:1].isdigit()]
        if nums:
            vals[name] = float(nums[-1]) * 1e9
    return vals


def stats(directory):
    runs = [kbest(directory / ("run%d.csv" % i)) for i in (1, 2, 3)]
    out = {}
    for name in runs[0]:
        samples = [run[name] for run in runs]
        out[name] = (statistics.mean(samples), statistics.stdev(samples))
    return out


def nearest(value):
    return int(value + 0.5) if value >= 0 else int(value - 0.5)


def main():
    reduced = stats(ROOT / "results" / "kernels" / "4.4.0-210-generic")
    full = stats(ROOT / "results" / "fulliter" / "4.4.0-210-generic")
    names = [
        "ref",
        "getpid",
        "context siwtch",
        "fork",
        "small read",
        "big write",
        "big munmap",
        "select",
    ]
    for name in names:
        rm, rs = reduced[name]
        fm, fs = full[name]
        overlap = not (rm - rs > fm + fs or fm - fs > rm + rs)
        print(
            "%-16s reduced %6d +/- %6d   full %6d +/- %6d   %s"
            % (name, nearest(rm), nearest(rs), nearest(fm), nearest(fs), "overlap" if overlap else "SEPARATE")
        )


if __name__ == "__main__":
    main()
