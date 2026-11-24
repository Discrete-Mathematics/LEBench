# Questions they will ask

Nineteen answers, thirty seconds each. Every answer names the file behind it. If
an answer is not here, the right response is "we did not measure that".

Compiled by 孙东旭 (5260000073). Updated 24 November 2026 with the fault-around
ablation and the second-host macrobenchmark.

---

**Q1. Why a virtual machine and not a server?**
We do not have the paper's HP DL160 G9, and the effect is a kernel property, so
the machine is held fixed across kernels instead of matched to the paper's. The
cost is that absolute latencies are not comparable, which is why every gap we
report is a ratio. *Evidence:* `report/report.tex` §Deviations.

**Q2. Is 43% just noise?**
No — noise is measured. The median run-to-run coefficient of variation is 10.9%,
and a difference counts only when the two `mean ± stdev` intervals are disjoint.
On that rule 27.1% of usable rows are clearly slower and 15.3% clearly faster:
about 1.8 to 1, not "most". *Evidence:* `docs/timer-floor.md` §F1.

**Q3. What happened at 4.16, 4.17 and 4.18?**
Every test looks about twice as fast, including the pure-CPU loop that never
enters the kernel. A kernel cannot halve a fixed instruction loop, so those boots
had a shifted time base or frequency. We exclude them from cross-kernel
statements and say so. *Evidence:* `docs/timer-floor.md` §F3.

**Q3b. And you never re-ran those boots to prove it?**
Correct, and that is the honest gap. `docs/drift-plan.md` specifies exactly that
re-run: each kernel booted twice, interleaved, with the pure-CPU control and the
frequency recorded. Analysis code is already written
(`analysis/analyze_drift.py`); the guest time is about an hour.

**Q4. How do you know the CPU is not affected by Meltdown?**
The kernel says so: `/sys/devices/system/cpu/vulnerabilities/meltdown` reads "Not
affected" on every boot, and it is in each `environment.txt`. KPTI is therefore
never engaged. *Evidence:* `results/thp/*/environment.txt`.

**Q5. Why only one kernel for claim 3?**
Claim 3 needs eleven causes off; on a fixed kernel we can toggle one runtime
switch, and the other ten need kernel rebuilds. We report what one switch does —
and we repeated it on a second host, which is the more informative result:
the switch speeds Redis on the first host and slows it on the second.
*Evidence:* `results/macro/`, `results/macro-host2/`, `docs/cross-host.md`.

**Q5b. Why do the two hosts disagree?**
Because the switch removes an IBRS-style mitigation whose cost depends on the
microarchitecture, and the two hosts are different generations (i7-13700H and
i9-14900HX). The disagreement is itself the finding: a single-machine
"disabling X speeds things up 30%" generalises to nothing.
*Evidence:* `docs/cross-host.md`.

**Q5c. What about fault-around?**
We toggled `fault_around_bytes` between 65536 and 4096 with six interleaved runs.
Every page-fault row stays inside the run-to-run spread, and the reason is in the
benchmark: the reduced suite maps a thousand pages and touches one byte, so it
cannot exercise the feature. That is a negative result about *our* workload, not
about Linux. *Evidence:* `results/fault-around/`, `docs/fault-around.md`.

**Q5d. Then how much of the eleven causes did you actually test?**
Four of eleven: KPTI, fault-around, hugepages, and the Spectre switch on the
application benchmark. Six are testable on this guest — the other two are the
cgroup memory controller and the Spectre switch on the micro suite. Five cannot
be tested here at all: two need a kernel rebuild, three no longer exist in this
kernel line. *Evidence:* `docs/claim2-plan.md` §1.

**Q6. Why not rebuild the kernel with the causes disabled?**
Two of them are build options and one (`CONFIG_CONTEXT_TRACKING_FORCE`) is gone
from this kernel line. A rebuild per cause is 20–40 minutes on this guest and
changes the toolchain too. We attempted a seven-kernel rebuild campaign; two
kernels built and validated, then the guest disk was corrupted when the host
drive filled. It is documented as incomplete with a ready-to-run build plan.
*Evidence:* the campaign status commit, `docs/audit.md`.

**Q7. Why 34 of 41 kernels?**
3.0.7 through 3.5.4 install, reach a login prompt and never answer sshd;
4.19.11 needs a `linux-modules` package Ubuntu no longer publishes. Both are
recorded as boot failures with no latency, not as zeros.
*Evidence:* `results/kernels/boot-failures.txt`.

**Q8. Isn't `BASE_ITER` 40 instead of 10,000 cheating?**
It changes precision, not direction, and it is in the deviation table. What it
costs is sensitivity: with three runs and 10.9% median CV, differences below
about 10% are not measurable here. We say that rather than claim them.

**Q9. What is the K-best rule?**
The authors' own: five samples within 5% of each other, report the fastest. It
rejects interference. We keep it inside each process run, then report mean and
sample standard deviation across three runs.

**Q10. Can I re-derive your numbers?**
Yes — that is what the verifiers are for. `scripts/verify_report_numbers.py` runs
six checks over the sweep, the THP table, the two macro hosts and the fault-around
summary; `analysis/verify_timer_floor.py` runs nine over the timer-floor figures.
A number that drifts breaks CI.
*Evidence:* `.github/workflows/verify.yml`.

**Q11. Why "not supported" and not "the paper is wrong"?**
Absence of evidence on a 2-vCPU guest is not a refutation of a measurement on a
Xeon server. *Evidence:* `docs/verdicts.md` §"What we cannot claim".

**Q12. What would change your verdict?**
Bare metal with a CPU affected by Meltdown for C2a; bootable 3.0–3.5 for C1's
3.0 baseline; a kernel rebuild per cause for the full ablation.
*Evidence:* `docs/audit.md` §4.

**Q13. How much of this was AI-assisted?**
Disclosed in the report: one assistant drafted the runner, the reboot script, the
report and the slides; a second supported the independent re-analysis and the
timer audit. Neither produced a measurement — every number is recomputed by the
verifiers. *Evidence:* `report/report.tex` §AI usage statement.

**Q14. Did you modify the authors' benchmark?**
`TEST_DIR/OS_Eval.c` is untouched. We generate a reduced copy that keeps the same
clock calls and K-best rule and compiles out three blocking or dominant cases;
the extension binary differs by one test.
*Evidence:* `course/make_reduced_eval.py`.

**Q15. Why is the TSC-based rewrite not used?**
On this guest the TSC is not a stable offset from the host, and the rewrite did
not serialise the instruction stream. *Evidence:* report §The other implementation.

**Q16. With more time, what is the first thing you would do?**
Boot patches for 3.0.7–3.5.4 — that single missing baseline is the only thing
between our claim-1 verdict and the paper's "75% slower than 3.0".
*Evidence:* `docs/audit.md` §4.

---

## If you do not know

1. "We did not measure that." Then stop — do not fill the silence.
2. "That number is in `docs/verdicts.md`, and the file behind it is named there."
3. "I can check and come back to you after the session."

Never guess a number. The verifiers exist so that only the printed numbers ever
need defending.
