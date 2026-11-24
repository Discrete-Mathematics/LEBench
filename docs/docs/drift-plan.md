# Drift control: can this guest tell a kernel change from a machine change?

**Author:** 孙东旭 (5260000073), 24 November 2026
**Status:** plan. No drift data exists yet.
**Analysis code:** `analysis/analyze_drift.py`

---

## The problem, stated plainly

The sweep in `results/kernels/` boots 34 kernels **once each, in order**. That
design has a hole: if the machine itself changes during the campaign — thermal
throttling, another VM on the host, a fan curve, a Windows update — the later
kernels inherit the change and the difference gets attributed to the kernel.

We already have a candidate case. Boots of 4.16.13, 4.17.14 and 4.18.16 come out
"about twice as fast" on every test, including `cpu`, a fixed instruction loop
that never enters the kernel (`docs/timer-floor.md` §F3). A kernel cannot halve a
fixed loop, so either those boots hit a different time base, or something about
the machine differed. **We inferred that; we never measured it.**

This plan measures it, in about an hour of guest time.

---

## The design

Boot each kernel **twice**, and break the order so that a monotone drift and a
kernel effect cannot both explain the same pattern:

```
A B C A B C        A = 4.15.15, B = 4.16.13, C = 4.20.13
```

* Same binary, same reduced suite, three runs per boot, as everywhere else.
* Between boots, nothing else changes: no package upgrades, no new VM, same
  host session if possible.
* Record the clock evidence in each `environment.txt`: `scaling_cur_freq`,
  `cpufreq` governor, the `cpu` test itself.

If drift is monotone in time, the A/B/C ordering makes it visible: the second
visit to each kernel lands at a different place in the sequence than the first.

---

## What the analysis reports

`analysis/analyze_drift.py` takes the boots in the order they happened and
prints, per boot, the median latency ratio (relative to the first boot) and the
pure-CPU control, then:

| Statistic | Reads as |
| --- | --- |
| Spearman(boot order, `cpu`) ≥ 0.7 | the machine drifts during the campaign |
| Spearman(boot order, `cpu`) < 0.7 | no drift detected |
| within-kernel spread < between-kernel spread | the kernel effect is real and survives the check |
| within-kernel spread ≥ between-kernel spread | the kernel effect is not separable from noise here |

Self-test on synthetic data (interleaved, drift-free) gives
`Spearman = +0.31`, within-kernel spread `0.010`, between-kernel spread `0.741`,
verdict "the kernel effect survives the drift check" — which is the shape we
want for the real run.

---

## The three possible outcomes, pre-registered

| Outcome | Meaning for the report | Where it goes |
| --- | --- | --- |
| `cpu` follows boot order, and the 4.16–4.18 dip follows `cpu` | the dip is a machine artifact, **confirmed by experiment** rather than inferred | Analysis section, and one line in the talk's slide 7 |
| `cpu` does not follow boot order, and the dip reproduces on all three 4.16–4.18 boots | the dip is reproducible and unexplained — a stronger, more uncomfortable finding | Analysis section, and an honest "we do not know" |
| the dip does not reproduce at all | our sweep row for those kernels is noise; the artifact claim is withdrawn | correction note in `docs/timer-floor.md` |

All three are writeable. That is why this experiment is worth an hour: **it can
only improve the honesty of the report**, never embarrass us.

---

## Cost

| Step | Guest time |
| --- | --- |
| 6 boots × (install check + 3 runs × ~20 s + reboot) | 50–70 min |
| analysis | seconds |

Boots go through the existing `scripts/vm_kernel_sweep.py` machinery; the only
change is the kernel order and the destination directory
(`results/drift/<kernel>-<visit>/`).

---

## What to add to every `environment.txt` from now on

Two lines that would have settled F3 immediately:

```
scaling_cur_freq: <cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_cur_freq>
cpufreq_governor: <cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor>
```

`course/run_toggle.py` already records the pure-CPU control implicitly (it runs
the whole suite); this plan asks for the frequency lines as well.
