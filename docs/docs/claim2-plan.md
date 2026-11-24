# Claim 2: which of the eleven causes can this guest actually test?

**Author:** 孙东旭 (5260000073), 24 November 2026
**Status:** plan and pre-registration. Nothing in this file is a result.
**Why it exists:** the report currently tests 4 of the paper's 11 causes. A reader
is entitled to ask "and the other seven?". This file answers that question cause
by cause, before any new data exists, so that the answer cannot be shaped after
the fact.

---

## 1. The eleven causes and their switch mechanism

The numbering follows the paper's Table 3, as listed in `report/report.tex`.

| # | Cause (paper) | Mechanism in the kernel | Switch available here |
|---|---|---|---|
| 1 | KPTI — remove kernel mappings from user page tables | separate page tables, `CR3` switch per entry | **runtime**: `pti=off` |
| 2 | Avoid indirect branch speculation (Retpoline) | `__x86_indirect_thunk_*` replacing indirect jumps | **runtime**: `spectre_v2=off` |
| 3 | SLAB freelist randomization | build option `CONFIG_SLAB_FREELIST_RANDOM` | none (rebuild) |
| 4 | Hardened usercopy | build option `CONFIG_HARDENED_USERCOPY` | none (rebuild) |
| 5 | Fault-around | mmap readahead of neighbouring pages, `fault_around_bytes` | **runtime**: debugfs |
| 6 | cgroup memory controller | per-page charge/uncharge in the mm path | **runtime**: `cgroup_disable=memory` |
| 7 | Transparent huge pages | sysfs `enabled` = `always`/`madvise`/`never` | **runtime**: sysfs |
| 8 | Userspace page fault handling (userfaultfd) | `vm.unprivileged_userfaultfd` | runtime, but **the tests never fault a uffd region** |
| 9 | Forced context tracking | `CONFIG_CONTEXT_TRACKING_FORCE` | none — the option is gone in 4.4+ |
| 10 | TLB layout change | merged into mainline | none — no toggle exists |
| 11 | CPU idle power states | merged into mainline, `intel_idle` | none — hardware/kernel generation |

**Consequence:** six causes have a switch that can be flipped on the installed
kernel (1, 2, 5, 6, 7, and 8 in principle). The other five need a kernel rebuild
(3, 4) or no longer exist in this kernel line (9, 10, 11).

That is the honest ceiling on this guest: **6 of 11**, not 11 of 11.

---

## 2. What is already done

| Cause | Experiment | Verdict | Where |
|---|---|---|---|
| 1 KPTI | `nopti` vs default on 4.4.0-210 | inconclusive — this CPU reports Meltdown "Not affected", so KPTI is never engaged | `report/generated/extension_table.tex` |
| 5 fault-around | `fault_around_bytes` 65536 vs 4096, six interleaved runs | not supported — reduced suite maps 1000 pages and touches one byte | `results/fault-around/`, `docs/fault-around.md` |
| 7 THP | `always` / `madvise` / `never` | not supported — every interval overlaps | `results/thp/`, `report/generated/thp_table.tex` |
| 2 Retpoline | only on the **macro** benchmark (`spectre_v2=off`) | not supported for the applications; **never run on the micro suite** | `results/macro/` |

So the real coverage today is **3 of 6 testable**, not 4 of 11. This plan covers
the remaining three testable ones: 2 (micro), 6, and the check for 8.

---

## 3. The two experiments to run, pre-registered

### E1 — Retpoline on the micro suite (cause 2)

**Design.** One kernel (4.4.0-210-generic), one binary (reduced suite), three
runs each with `spectre_v2=off` and with the default, interleaved A/B/A/B/A/B.

**First, a one-line question that decides everything.** The guest's
`environment.txt` records `spectre_v2: Mitigation: Enhanced IBRS`. If the kernel
uses Enhanced IBRS it does not emit retpoline thunks at all, and there is nothing
to switch off. Check before running:

```bash
grep -c __x86_indirect_thunk /proc/kallsyms   # 0 means no retpolines
```

**Pre-registered expectations**

| If the count is | Expectation |
| --- | --- |
| 0 (no thunks) | no measurable change on `select`, `poll`, `epoll`, `select big`, `poll big`, `epoll big`; verdict will be **inconclusive for the paper's mechanism**, and the paper's 68/89/72% cannot be reproduced on this hardware |
| > 0 (thunks exist) | the paper's direction: those six tests get slower with the mitigation on; expect 20–70% |

**Verdict rule.** `supported` only if the six tests move in the paper's direction
with disjoint intervals; `partially supported` if the direction matches but some
intervals overlap; `not supported` if they overlap entirely or move the wrong
way; `inconclusive` if the thunk count is zero.

### E2 — cgroup memory controller (cause 6)

**Design.** One kernel, one binary, three runs each with `cgroup_disable=memory`
and default, interleaved.

**Pre-registered expectation.** The paper reports `big munmap` 81% slower before
3.17 and 9% after, because uncharge was batched. On this kernel the batching
already exists, so the expected effect is *small* — a few percent at most — and
`munmap` is the only test that should move. `getpid` is the control and must not
move.

**Verdict rule.** As above. A large `big munmap` effect would be surprising and
should be treated as a measurement problem first, not a finding.

### E3 — userfaultfd (cause 8): a check, not an experiment

The reduced suite never registers a userfaultfd region, so the sysctl
(`vm.unprivileged_userfaultfd`) cannot change any row. Record it as
**structurally untestable** with the evidence that no test opens a uffd.
Cost: one line in the report, no guest time.

---

## 4. What the runner has to capture

For every batch, `environment.txt` must record the state that makes the switch
real, not just the command line:

| Toggle | Evidence the switch took effect |
| --- | --- |
| `pti=off` | `/sys/devices/system/cpu/vulnerabilities/meltdown` |
| `spectre_v2=off` | same file for spectre_v2 **and** `grep -c __x86_indirect_thunk /proc/kallsyms` |
| `cgroup_disable=memory` | `grep cgroup /proc/cmdline` and `/proc/cgroups` |
| THP | `cat /sys/kernel/mm/transparent_hugepage/enabled` (bracket) |
| fault-around | `cat /sys/kernel/debug/fault_around_bytes` |

`course/run_toggle.py` writes exactly this block; a run without the evidence line
is a failed run, not a null result.

---

## 5. Cost and order

| Order | Experiment | Guest time | Blocks |
| --- | --- | --- | --- |
| 1 | E1 thunk check only | 1 minute | tells us whether E1 is worth 30 minutes |
| 2 | E2 cgroup (3+3 runs) | ~40 min | — |
| 3 | E1 micro (3+3 runs) | ~40 min | the thunk check |
| 4 | E3 sentence | 0 | — |

If only one is affordable: **E2**, because the paper's number for it (81% → 9%)
is the most specific claim in Table 3 and either outcome is publishable.

---

## 6. How the result enters the report

One sentence per cause in the claim-2 subsection, plus one row in
`docs/verdicts.md`. The Limitations paragraph then changes from "4 of 11" to
"6 of 11 tested; 5 structurally untestable here (3, 4 need a rebuild; 9, 10, 11
no longer exist in this kernel line)". That sentence is the whole point of this
plan.
