# analysis/ — independent re-analysis of the kernel sweep

One script, one input, three figures. It reads the sweep summary that
`scripts/summarize_kernel_sweep.py` already produced and asks a different
question from the one the report asks: **is the paper's claim 1 visible in our
logs once run-to-run noise is taken into account, or is the "slowdown" mostly
the noise floor?**

It does not touch `results/`; it only reads `results/kernel_summary.csv`.

## Run

```bash
python3 analysis/analyze_kernel_summary.py \
    --csv results/kernel_summary.csv \
    --outdir analysis
```

Requires Python 3 with `pandas`, `numpy`, and `matplotlib`.

## Outputs

| File | What it is |
| --- | --- |
| `relative_latency_by_kernel.csv` | per kernel: median/IQR ratio vs 4.0.5, share of tests clearly slower / clearly faster, median CV |
| `relative_latency_by_test.csv` | per test: median ratio, how many kernels are clearly slower / faster |
| `noise_by_test.csv` | per test: median and 90th-percentile coefficient of variation |
| `fig_trend.png` | A: median relative latency per kernel; B: share of tests that clear the noise |
| `fig_tests.png` | per-test median over the sweep |
| `fig_noise.png` | distribution of run-to-run variation |

## Definitions

* **ratio** — `mean_ns(kernel, test) / mean_ns(4.0.5, test)`.
* **clearly slower / faster** — the two `mean ± stdev` intervals are disjoint.
  This is deliberately conservative: a difference smaller than one standard
  deviation is not counted as evidence.

The interpretations and the numbers quoted in `docs/analysis-note.md` come out
of the run above.
