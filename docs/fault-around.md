# Fault-around experiment (paper section 4.2.1, root cause #5)

Fault-around pre-establishes page-table mappings for the pages surrounding a
faulting page when those pages are resident in the page cache. The paper reports
a 54% slowdown of `big-pagefault` from this feature (Table 3 lists up to 167%).

## Design

One factor changes: `fault_around_bytes` in debugfs, on 4.4.0-210-generic.

| Config | `fault_around_bytes` | Meaning |
|---|---|---|
| `default` | 65536 | the kernel default (16-page window, fault-around on) |
| `off` | 4096 | one-page window, fault-around effectively disabled |

Everything else stays fixed: the reduced `OS_Eval` binary (`course/`), the
command line, 2 vCPUs, the same guest, and three runs per configuration. The six
runs were interleaved (default, off, default, off, default, off) so that slow
drift over the session does not load onto one configuration. The knob was
restored to 65536 afterwards; `environment.txt` records the value read back
after each write.

## Result

Mean ± sample standard deviation of the three K-best runs (ns). The full table
is `results/fault-around/summary.csv`; the page-fault rows the paper's claim is
about:

| Test | default | off (4096) | ratio |
|---|---|---|---|
| small page fault | 10500 ± 520 | 11200 ± 1967 | 1.07 |
| mid page fault | 11200 ± 436 | 11567 ± 1650 | 1.03 |
| big page fault | 11733 ± 723 | 12000 ± 954 | 1.02 |

Every row moves by less than its run-to-run spread, and the control rows move
the same amount. The paper's 54% `big-pagefault` slowdown does not appear.

## Verdict

**Not supported** on this guest. Two reasons, both documented as deviations:

1. The reduced suite maps a 1{,}000-page file for `big page fault` (the
   10{,}000-page case is compiled out) and touches one byte, so the surrounding
   pages fault-around would pre-map are not faulted in this test anyway.
2. Fault-around only pays off when the neighbouring pages are resident in the
   page cache; the reduced test's file is read fresh, so there is nothing to
   pre-map.

The experiment still does what a one-factor ablation should: it changes exactly
one kernel setting, records it, and shows that the effect is inside the noise on
this guest. Raw logs: `results/fault-around/<config>/run{1,2,3}.csv`.
