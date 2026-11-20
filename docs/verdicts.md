# Claim verdicts — one page

Every verdict this project can defend, in one table. If a number is not here, we
do not quote it in the talk. Each row names the file a reader can open to check
it.

Compiled by 孙东旭 (5260000073) from `report/report.tex`, `docs/audit.md`,
`docs/timer-floor.md` and `results/`.

| # | Claim as the paper states it | Metric | Paper | Ours | Verdict | Evidence |
|---|---|---|---|---|---|---|
| C1 | Most core operations are slower on later kernels, many by ≥50% (Fig. 1a) | share of 627 paired measurements on the 19 kernels newer than 4.0.5 | "most tests slower, many ≥50%" | 271 (43%) higher; 76 (12%) ≥50% higher; 117 with disjoint intervals | **not supported** | `report/generated/claim_summary.tex`, `results/kernel_summary.csv` |
| C1′ | Same claim, excluding timer-bound rows | median ratio, clearly-slower share | — | median 1.032; 27.1% clearly slower; 56/1152 rows (4.9%) dropped | **not supported** (verdict unchanged) | `docs/timer-floor.md`, `analysis/suspect_rows.csv` |
| C2a | KPTI costs a measurable amount per syscall (§4.1.1) | getpid, fork on 4.4.0-210 with and without `nopti` | KPTI costs 400–500 cycles; recv +63% | getpid 314 vs 295 ns (overlap); fork 93 → 254 µs (disjoint, wrong direction) | **inconclusive** — the CPU reports Meltdown "Not affected", so KPTI is never engaged | `results/kernels/4.4.0-210-nopti/`, `report/generated/extension_table.tex` |
| C2b | Disabled transparent hugepages are a configuration cause (§4.2.3) | big munmap, page fault under `always`/`madvise`/`never` | THP disabled is a listed mistake | big munmap 302857 ± 36653 / 307558 ± 14605 / 306336 ± 15523 ns; all pairs overlap | **not supported** | `results/thp/`, `report/generated/thp_table.tex` |
| C2c | Eleven causes explain the jumps (Table 3, Fig. 2) | causes actually toggled | 11 | 3 of 11 (nopti, `spectre_v2=off`, THP) | **not reproduced** (scope) | `docs/audit.md` §3 item 6 |
| C3 | Disabling the causes speeds Redis 56%, Apache 33%, Nginx 34% (§5) | throughput, one kernel, one switch | +56/+33/+34% | Apache 1580 ± 139 → 1308 ± 24 req/s (slower, disjoint); Nginx 5725 ± 966 → 7314 ± 208 (faster, disjoint); Redis means up, intervals overlap | **not supported** | `results/macro/`, `report/generated/macro_table.tex` |
| EXT | The single-shot `getpid` row measures the clock, not the syscall | per-call ns, 1 vs 1000 calls per sample | — (our own extension) | 4.0.5: 245 → 129 ns; 4.4.0-210: 314 → 127 ns; intervals separate before, overlap after | **supported** | `results/batching/`, `report/generated/batch_table.tex` |

## What the verdicts rest on

* **Disjoint intervals.** "Slower" means the two `mean ± stdev` intervals do not
  touch. Anything smaller than one standard deviation is not called a
  difference. This is the conservative reading and it is stated in the report.
* **Relative, never absolute.** The guest's absolute latencies are not the
  paper's, so every gap is quoted as a ratio or a percentage.
* **Traceability.** `scripts/verify_report_numbers.py` recomputes the C1, C3 and
  extension numbers from `results/` and compares them with the generated LaTeX;
  `analysis/verify_timer_floor.py` does the same for the timer-floor figures.
  Both run in CI.

## What we cannot claim

1. That the paper is wrong. We can only say **this guest did not show its
   effect**, and in C2a we can say why (a CPU that does not pay for KPTI).
2. Anything about Linux 3.0: 3.0.7–3.5.4 never reached sshd.
3. Anything about the eleven-cause ablation as a whole: 8 of the 11 were never
   toggled.
4. Anything about a server-class machine: 2 vCPU, 4 GB, VirtualBox.

## One-line answers for the talk

* C1 → "43% of our paired measurements are higher, 12% by at least half; that is
  not the paper's picture."
* C2a → "This CPU is not affected by Meltdown, so there is no KPTI cost to
  remove."
* C2b → "Switching hugepages across three modes leaves every interval
  overlapping."
* C3 → "Apache got slower and Nginx faster, so one switch does not reproduce
  eleven causes."
* EXT → "Batching a thousand calls per sample halves the number, which is what a
  timer-dominated row looks like."
