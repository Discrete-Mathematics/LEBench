# What is under `results/`

Six result trees, three of them written by experiments that answer a specific
cause from the paper's Table 3. This page says which tree answers which
question, so nobody has to guess and nobody re-runs what already exists.

Compiled by 孙东旭 (5260000073), 24 November 2026.

| Tree | Produced by | Kernels × runs | Question it answers | Verdict |
| --- | --- | --- | --- | --- |
| `results/kernels/` | `scripts/vm_kernel_sweep.py` | 34 kernels × 3 | claim 1: are later kernels slower than 4.0.5? | not supported |
| `results/kernel_summary.csv` | `scripts/summarize_kernel_sweep.py` | — | the mean ± stdev table every claim-1 number comes from | — |
| `results/kernels/4.4.0-210-nopti/` | `course/boot_nopti.sh` | 1 kernel × 3 | cause 1 (KPTI) | inconclusive: this CPU is not affected by Meltdown |
| `results/thp/{always,madvise,never}/` | `scripts/run_nopti_extension.py` re-used for THP | 1 kernel × 3 × 3 | cause 7 (transparent huge pages) | not supported |
| `results/fault-around/` | six interleaved runs, `fault_around_bytes` 65536 vs 4096 | 1 kernel × 6 | cause 5 (fault-around) | not supported: the reduced suite maps 1000 pages and touches one byte |
| `results/macro/` | `macrobench/run_macrobench.sh` | 1 kernel, 1 switch, 3 runs per app | claim 3 on the first host | not supported (Apache slower, Nginx faster, Redis flat) |
| `results/macro-host2/` | same harness, second host | 1 kernel, 1 switch, 3 runs per app | claim 3 on a second machine | not supported — and the effect does not transfer between hosts |
| `results/batching/` | `course/OS_Eval_batched.c` | 2 kernels × 3 | our extension: is `getpid` measuring the clock? | supported: 245 → 129 ns on 4.0.5 |
| `results/toggles/<label>/` | `course/run_toggle.py` (new) | 1 kernel × N | any runtime cause, one parameter per directory | to be filled by the claim-2 campaign |
| `results/drift/<kernel>-<visit>/` | sweep machinery, interleaved order (new) | 3 kernels × 2 visits × 3 | is the 4.16–4.18 dip a machine artifact? | to be filled by the drift campaign |

## Conventions every tree follows

* `environment.txt` in each batch: kernel release, `/proc/cmdline`, compiler,
  CPU model, and the vulnerability strings that show which mitigation is active.
  A batch without it is a failed batch, not a null result.
* `run<N>/` holds `stdout.txt`, `stderr.txt`, `exit_code.txt` and the LEBench
  CSV for that run.
* `summary.csv` holds one row per test: mean, sample standard deviation, n, and
  the individual K-best values.
* Every number in `report/` and `docs/` is supposed to be recomputable from one
  of these files. `scripts/verify_report_numbers.py` and
  `analysis/verify_timer_floor.py` are the checks that say so.

## The two trees that do not exist yet

`results/toggles/` and `results/drift/` are created by this week's scripts:

```bash
# one runtime cause, two arms
sudo sh course/boot_toggle.sh --add cgroup_disable=memory
sudo python3 course/run_toggle.py --label cgroup-off --runs 3
sudo sh course/boot_toggle.sh --restore     # reboot, then the second arm

python3 analysis/analyze_toggle.py \
    --baseline results/toggles/cgroup-on --variant results/toggles/cgroup-off \
    --cause 6 --toggle cgroup_disable=memory
```

```bash
# interleaved drift check
python3 analysis/analyze_drift.py \
    --run 4.15=results/drift/4.15-1 --run 4.16=results/drift/4.16-1 \
    --run 4.20=results/drift/4.20-1 --run 4.15=results/drift/4.15-2 \
    --run 4.16=results/drift/4.16-2 --run 4.20=results/drift/4.20-2
```
