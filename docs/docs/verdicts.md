# Claim verdicts — one page

Every verdict this project can defend, in one table. If a number is not here, we
do not quote it in the talk. Each row names the file a reader can open.

Compiled by 孙东旭 (5260000073). Revised 24 November 2026 to cover the
fault-around ablation and the second-host macrobenchmark.

| # | Claim as the paper states it | Metric | Ours | Verdict | Evidence |
|---|---|---|---|---|---|
| C1 | Most operations slower on later kernels, many by ≥50% (Fig. 1a) | 627 paired measurements on the 19 later kernels vs 4.0.5 | 271 (43%) higher; 76 (12%) ≥50% higher; 117 with disjoint intervals | **not supported** | `report/generated/claim_summary.tex` |
| C1′ | C1 excluding timer-bound rows | median ratio; clearly-slower share | median 1.032; 27.1% clearly slower; 56/1152 rows dropped (4.9%) | **not supported**, unchanged | `docs/timer-floor.md`, `analysis/suspect_rows.csv` |
| C2a | KPTI costs per syscall (§4.1.1) | `getpid`, `fork` with and without `nopti` | getpid 314 vs 295 ns (overlap); fork 93 → 254 µs (disjoint, wrong direction) | **inconclusive**: CPU reports Meltdown "Not affected", KPTI never engages | `results/kernels/4.4.0-210-nopti/` |
| C2b | Disabled hugepages are a config cause (§4.2.3) | `big munmap`, page faults under `always`/`madvise`/`never` | every pair of intervals overlaps | **not supported** | `results/thp/`, `report/generated/thp_table.tex` |
| C2c | Fault-around (§4.2.1) | page faults with `fault_around_bytes` 65536 vs 4096, six interleaved runs | every page-fault row stays inside the run-to-run spread | **not supported**: the reduced suite maps 1000 pages and touches one byte, so it cannot exercise the feature | `results/fault-around/`, `docs/fault-around.md` |
| C2d | Retpoline (§4.1.2) | `select`/`poll`/`epoll` with `spectre_v2=off` on the micro suite | not yet run; the guest reports `Enhanced IBRS`, and a zero `__x86_indirect_thunk` count would mean there is nothing to switch off | **pending** (planned, pre-registered in `docs/claim2-plan.md`) | `results/toggles/` (to be created) |
| C2e | **Coverage of the eleven causes** | causes actually toggled | **4 of 11 tested** (1, 5, 6*, 7); **6 are testable on this guest**; 5 cannot be tested (3 and 4 need a kernel rebuild; 9, 10 and 11 no longer exist in this kernel line) | **partial by construction**, stated as a limit | `docs/claim2-plan.md` §1 |
| C3 | Disabling the causes speeds Redis/Apache/Nginx (§5) | throughput, one kernel, one switch, host 1 | Apache 1580 ± 139 → 1308 ± 24 (slower, disjoint); Nginx 5725 ± 966 → 7314 ± 208 (faster, disjoint); Redis means up, intervals overlap | **not supported** | `results/macro/`, `report/generated/macro_table.tex` |
| C3′ | Same, second host | same harness, i9-14900HX | the switch speeds Redis on host 1 and slows it on host 2 | **not supported**, and the effect does not transfer | `results/macro-host2/`, `docs/cross-host.md` |
| EXT | The single-shot `getpid` row measures the clock | per-call ns, 1 vs 1000 calls per sample | 4.0.5: 245 → 129 ns; 4.4.0-210: 314 → 127 ns | **supported** | `results/batching/` |

\* cause 6 (cgroup memory controller) is testable but not yet run; see
`docs/claim2-plan.md` E2.

## What the verdicts rest on

* **Disjoint intervals.** "Slower" means the two `mean ± stdev` intervals do not
  touch. A difference smaller than one standard deviation is not called a
  difference.
* **Relative, never absolute.** The guest's latencies are not the paper's.
* **Traceability.** `scripts/verify_report_numbers.py` (six checks) and
  `analysis/verify_timer_floor.py` (nine checks) recompute the published numbers
  from `results/`; both run in CI.

## What we cannot claim

1. That the paper is wrong — only that this guest did not show its effect, and
   for KPTI why it could not.
2. Anything about Linux 3.0: 3.0.7–3.5.4 never reached sshd.
3. The eleven-cause ablation as a whole: four causes tested, five untestable
   here, two (Retpoline, cgroup) planned.
4. Anything about a server-class machine: 2 vCPU, 4 GB, VirtualBox, and one
   second host for claim 3 only.

## One-line answers for the talk

* C1 → "43% of the paired measurements are higher, 12% by at least half."
* C2a → "This CPU is not affected by Meltdown, so there is no KPTI cost to remove."
* C2b/c → "Hugepages and fault-around both leave every interval overlapping."
* C3 → "Apache got slower and Nginx faster; on a second host Redis flips direction."
* EXT → "Batching a thousand calls halves the number, which is what a
  timer-dominated row looks like."
* C2e → "Four of eleven causes tested, six testable here, five impossible on this
  kernel — and we say which is which."
