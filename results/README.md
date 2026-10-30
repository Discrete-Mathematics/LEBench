# Result logs

`scripts/run_current_kernel.py` writes one directory per batch:

```
results/<kernel-release>/<UTC-timestamp>/environment.txt
results/<kernel-release>/<UTC-timestamp>/run<N>/stdout.txt
results/<kernel-release>/<UTC-timestamp>/run<N>/stderr.txt
results/<kernel-release>/<UTC-timestamp>/run<N>/exit_code.txt
results/<kernel-release>/<UTC-timestamp>/run<N>/output.<kernel-release>.csv
results/<kernel-release>/<UTC-timestamp>/summary.csv
```

`environment.txt` records the operating system, kernel release, compiler, and Python version for that batch. `summary.csv` is the mean and sample standard deviation of the K-best and average latencies across the runs in the batch. Every number quoted in the report should point at one of these files.

No measurements are stored yet. The first batch is produced by running the suite on Linux (see the repository README).
