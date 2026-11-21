# Macrobenchmark results on a second host (Claim 3 cross-host check)

These logs are the same experiment as `results/macro/`, run on a **different
host**: a Windows 11 laptop with an Intel i9-14900HX (24 cores) hosting the
Ubuntu 16.04.6 guest with 2 vCPUs and 4 GB, collected on 7-8 November 2026 with
the `macrobench/` harness (`run_macrobench.sh`, three runs per configuration).

| Host | results/ dir | CPU | Guest | Date |
|---|---|---|---|---|
| A (primary, used by the report) | `results/macro/` | i7-13700H | Ubuntu 16.04.6, 2 vCPU, 4 GB | 9 Nov 2026 |
| B (this directory) | `results/macro-host2/` | i9-14900HX | Ubuntu 16.04.6, 2 vCPU, 4 GB | 7-8 Nov 2026 |

The configurations are identical to host A: `default` versus `spectre_v2=off`
on 4.4.0-210-generic, with the vulnerability file moving from
`Mitigation: Enhanced IBRS` to `Vulnerable` between the boots. An interrupted
control batch (three further `default` runs started on 8 November) was cut short
when the host slept and is not committed.

The cross-host comparison lives in `docs/cross-host.md`.
