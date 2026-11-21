# Fault-around results (claim 2, root cause #5)

One directory per configuration (`default` = 65536-byte fault-around window,
`off` = 4096-byte window), three interleaved runs each:

```
results/fault-around/<config>/
├── environment.txt   # knob value read back, kernel, CPU, date
├── run{1,2,3}.csv    # OS_Eval output, K-best and average per test
├── run{1,2,3}.stdout.txt / .stderr.txt
└── summary.csv       # mean ± std per test, and the off/default ratio
```

Design, verdict and the comparison with the paper's §4.2.1 are in
`docs/fault-around.md`.
