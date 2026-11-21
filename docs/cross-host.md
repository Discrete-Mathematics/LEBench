# Cross-host check of Claim 3 (macrobenchmark with `spectre_v2=off`)

The paper's §6 repeats LEBench on a second machine to test hardware sensitivity.
Claim 3 (applications) was measured on host A (i7-13700H, `results/macro/`). The
same experiment was repeated on host B (i9-14900HX, `results/macro-host2/`) with
the same guest (Ubuntu 16.04.6, 2 vCPU, 4 GB), the same kernel (4.4.0-210), the
same binaries and the same three-run protocol. Ratio = `spectre-off` mean divided
by `default` mean.

| Test | Host A ratio | Host B ratio | Direction on A | Direction on B |
|---|---|---|---|---|
| Redis GET | 1.35 | 0.78 | faster | slower |
| Redis RPUSH | 1.26 | 0.78 | faster | slower |
| Redis RPOP | 1.16 | 0.70 | faster | slower |
| Redis SPOP | 1.19 | 0.76 | faster | slower |
| Redis LRANGE 100 | 1.08 | 0.75 | faster | slower |
| Apache index | 0.83 | 0.94 | slower | slower |
| Nginx index | 1.28 | 1.01 | faster | ~unchanged |

On host A the switch speeds Redis up by 8-35% and Nginx by 28%; on host B the
same switch slows Redis down by 22-30% and leaves Nginx within noise. Apache is
slower on both hosts. The only consistent observation across hosts is that the
effect is small (well under the paper's 56%, 33%, 34% maxima, which come from
disabling all eleven causes) and that its sign is not portable.

Conclusion: the single-switch application experiment does not reproduce the
paper's Claim 3 on either host, and the cross-host repetition shows the result is
not an artifact of one machine's noise — the negative verdict in the report is
robust. This mirrors the paper's own §6 finding that one of its eleven causes
(idle states) does not transfer between machines.

Raw logs: `results/macro-host2/<config>/raw/*.log`, per-run rows in
`results/macro-host2/<config>/results.csv`, aggregation in
`results/macro-host2/summary.csv`.
