# Macrobenchmark results (Claim 3)

One directory per kernel configuration:

```
results/macro/<config>/
├── environment.txt   # kernel cmdline, CPU, vulnerability status, tool versions
├── results.csv       # long-form observations, one row per measurement
├── raw/              # unmodified redis-benchmark / ab output
└── summary.csv       # mean +/- std per config and the ratio against `default`
```

Configurations currently used:

| Config | Kernel command line | What it isolates |
|---|---|---|
| `default` | as installed | baseline |
| `spectre-off` | `spectre_v2=off` | Retpoline (Spectre v2) mitigation cost |

Every number in the report's Claim 3 section must point at a row in one of these
`results.csv` files and at the raw log next to it.
