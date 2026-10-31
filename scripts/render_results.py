#!/usr/bin/env python3
"""Turn results/kernel_summary.csv into LaTeX tables and a relative-latency figure."""

import csv
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUMMARY = ROOT / "results" / "kernel_summary.csv"
OUT_DIR = ROOT / "report" / "generated"
BASELINE = "4.0.5-040005-generic"
FOCUS = [
    "getpid",
    "context siwtch",
    "send",
    "recv",
    "fork",
    "small read",
    "small write",
    "big write",
    "big munmap",
    "select",
    "poll",
    "epoll",
]


def version_key(name):
    head = name.split("-")[0]
    parts = []
    for piece in head.split("."):
        if piece.isdigit():
            parts.append(int(piece))
        else:
            parts.append(0)
    return tuple(parts)


def load():
    grouped = defaultdict(dict)
    if not SUMMARY.is_file():
        return grouped
    for row in csv.DictReader(SUMMARY.open(encoding="utf-8")):
        grouped[row["kernel"]][row["test"]] = (float(row["mean_ns"]), float(row["stdev_ns"]))
    return grouped


def tex_num(value):
    if value >= 1_000_000:
        return "%.2f" % (value / 1_000_000)
    if value >= 1_000:
        return "%.1f" % (value / 1_000)
    return "%.0f" % value


def scaled(value, reference):
    if reference >= 1_000_000:
        return "%.2f" % (value / 1_000_000)
    if reference >= 1_000:
        return "%.1f" % (value / 1_000)
    return "%.0f" % value


def unit(value):
    if value >= 1_000_000:
        return "ms"
    if value >= 1_000:
        return "us"
    return "ns"


def write_extension(grouped):
    default = grouped.get("4.4.0-210-generic", {})
    nopti = grouped.get("4.4.0-210-nopti", {})
    lines = [
        r"\begin{tabular}{@{}lrrrr@{}}",
        r"\toprule",
        r"Test & Default & $nopti$ & Change & Intervals overlap? \\",
        r"\midrule",
    ]
    for name in FOCUS:
        if name not in default or name not in nopti:
            continue
        mean_a, stdev_a = default[name]
        mean_b, stdev_b = nopti[name]
        change = (mean_b / mean_a - 1.0) * 100.0
        overlap = (mean_a - stdev_a) <= (mean_b + stdev_b) and (mean_b - stdev_b) <= (mean_a + stdev_a)
        lines.append(
            "%s & %s %s & %s %s & %+.0f\\%% & %s \\\\"
            % (name.replace("_", r"\_"), tex_num(mean_a), unit(mean_a), tex_num(mean_b), unit(mean_b), change, "yes" if overlap else "no")
        )
    lines += [r"\bottomrule", r"\end{tabular}", ""]
    (OUT_DIR / "extension_table.tex").write_text("\n".join(lines), encoding="utf-8")


def write_kernel_table(grouped):
    kernels = sorted(
        (name for name in grouped if name not in ("4.4.0-210-generic", "4.4.0-210-nopti")),
        key=version_key,
    )
    columns = ("getpid", "big write", "big munmap")
    lines = [
        r"\begin{longtable}{@{}lrrr@{}}",
        r"\caption{Mean $\pm$ sample standard deviation of three K-best runs.}\label{tab:kernels}\\",
        r"\toprule",
        r"Kernel & getpid & big write & big munmap \\",
        r"\midrule",
        r"\endfirsthead",
        r"\toprule",
        r"Kernel & getpid & big write & big munmap \\",
        r"\midrule",
        r"\endhead",
        r"\bottomrule",
        r"\endfoot",
    ]
    for kernel in kernels:
        cells = [kernel.split("-")[0]]
        for name in columns:
            if name not in grouped[kernel]:
                cells.append("---")
                continue
            mean, stdev = grouped[kernel][name]
            cells.append("%s$\\pm$%s %s" % (scaled(mean, mean), scaled(stdev, mean), unit(mean)))
        lines.append(" & ".join(cells) + r" \\")
    if len(kernels) == 0:
        lines.append(r"\multicolumn{4}{l}{No paper-kernel run has three complete CSVs yet.} \\")
    lines += [r"\end{longtable}", ""]
    (OUT_DIR / "kernel_table.tex").write_text("\n".join(lines), encoding="utf-8")


def write_claim(grouped):
    base = grouped.get(BASELINE)
    lines = []
    if not base:
        lines.append("Linux 4.0.5 did not produce three complete runs, so the Figure~1 percentage is not computed.")
    else:
        later = [
            name for name in grouped
            if name not in ("4.4.0-210-generic", "4.4.0-210-nopti")
            and version_key(name) > version_key(BASELINE)
        ]
        slower = 0
        much = 0
        clear = 0
        total = 0
        for kernel in later:
            for test, (mean, stdev) in grouped[kernel].items():
                if test not in base or base[test][0] <= 0:
                    continue
                base_mean, base_stdev = base[test]
                total += 1
                ratio = mean / base_mean - 1.0
                if ratio > 0:
                    slower += 1
                if ratio >= 0.5:
                    much += 1
                if mean - stdev > base_mean + base_stdev:
                    clear += 1
        if total:
            lines.append(
                "Across %d later-kernel measurements, %d (%.0f\\%%) have a higher mean than the same test on 4.0.5 and %d (%.0f\\%%) have a mean at least 50\\%% higher. %d of those measurements have non-overlapping mean$\\pm$stdev intervals and a higher mean, which is the bar used in the analysis."
                % (total, slower, 100.0 * slower / total, much, 100.0 * much / total, clear)
            )
        else:
            lines.append("No kernel newer than 4.0.5 has a complete three-run summary yet.")
    (OUT_DIR / "claim_summary.tex").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_figure(grouped):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        return
    base = grouped.get(BASELINE)
    if not base:
        return
    kernels = sorted(
        (name for name in grouped if name not in ("4.4.0-210-generic", "4.4.0-210-nopti")),
        key=version_key,
    )
    tests = [name for name in ("getpid", "small read", "select", "big write", "big munmap") if name in base]
    if not kernels or not tests:
        return
    fig, ax = plt.subplots(figsize=(10, 4.5))
    for test in tests:
        xs, ys = [], []
        for index, kernel in enumerate(kernels):
            if test not in grouped[kernel]:
                continue
            xs.append(index)
            ys.append(grouped[kernel][test][0] / base[test][0])
        ax.plot(xs, ys, marker="o", label=test)
    ax.axhline(1.0, color="black", linewidth=0.8)
    ax.set_xticks(range(len(kernels)))
    ax.set_xticklabels([name.split("-")[0] for name in kernels], rotation=90, fontsize=7)
    ax.set_ylabel("Latency / 4.0.5")
    ax.set_title("Reduced LEBench, mean of three runs")
    ax.legend(fontsize=8, ncol=3)
    fig.tight_layout()
    fig.savefig(OUT_DIR / "relative_latency.pdf")
    plt.close(fig)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    grouped = load()
    write_extension(grouped)
    write_kernel_table(grouped)
    write_claim(grouped)
    write_figure(grouped)
    print("rendered %d kernels" % len(grouped))


if __name__ == "__main__":
    main()
