# Questions they will ask

Sixteen answers, thirty seconds each, in the order they are likely to arrive.
Every answer names the file that backs it. If an answer is not here, the right
response is "we did not measure that".

Compiled by 孙东旭 (5260000073).

---

**Q1. Why a virtual machine and not a server?**
We do not have the paper's HP DL160 G9, and the effect we are testing is a
*kernel* property, so the machine is held fixed across kernels instead of matched
to the paper's. The cost is that absolute latencies are not comparable; that is
why every gap we report is a ratio.
*Evidence:* `report/report.tex` §Deviations; `docs/REPRODUCTION.md`.
*Answered by:* 邹浩宇.

**Q2. Is 43% just noise?**
No: noise is measured, not assumed. The median run-to-run coefficient of
variation is 10.9%, and we only call a difference real when the two
`mean ± stdev` intervals are disjoint. On that rule 27.1% of the usable rows are
clearly slower and 15.3% clearly faster — a ratio of about 1.8, not the paper's
picture of "most".
*Evidence:* `docs/timer-floor.md` F1; `analysis/suspect_rows.csv`.
*Answered by:* 孙东旭.

**Q3. What happened at 4.16, 4.17 and 4.18?**
Every test looks about twice as fast on those three boots, including the pure-CPU
loop, which never enters the kernel. A kernel cannot halve a fixed instruction
loop, so the boots had a shifted time base or frequency, not a faster kernel. We
exclude them from cross-kernel statements and say so in the limitations.
*Evidence:* `docs/timer-floor.md` F3 and its table; `analysis/fig_timer_floor.png`
panel D.
*Answered by:* 孙东旭.

**Q4. How do you know the CPU is not affected by Meltdown?**
The kernel says so. `/sys/devices/system/cpu/vulnerabilities/meltdown` reads "Not
affected" on every boot, and it is recorded in each `environment.txt`. KPTI is
therefore never engaged, which is why `nopti` cannot remove a cost that is not
being paid.
*Evidence:* `results/thp/*/environment.txt`; `results/kernels/4.4.0-210-nopti/`.
*Answered by:* 邹浩宇.

**Q5. Why only one kernel for claim 3?**
Because claim 3 needs eleven causes off, and on a fixed kernel we can toggle one
runtime switch. Running the other ten means rebuilding the kernel ten times; the
guest cannot afford it, so we report what one switch does and label the rest a
scope limit rather than a result.
*Evidence:* `results/macro/`; `docs/audit.md` §3 item 6.
*Answered by:* 张澄心.

**Q6. Why not rebuild the kernel with the causes disabled?**
Two of them are not runtime switches and one (`CONFIG_CONTEXT_TRACKING_FORCE`)
does not even exist in this kernel line any more. A rebuild per cause is 20–40
minutes each on this guest and changes the toolchain too, which would confound
the comparison.
*Evidence:* `docs/REPRODUCTION.md` §Scope.
*Answered by:* 邹浩宇.

**Q7. Why 34 of 41 kernels?**
3.0.7 through 3.5.4 install, reach a login prompt and never answer sshd, so there
is no way to log in and run anything; 4.19.11 needs a `linux-modules` package
that Ubuntu no longer publishes at that URL. Both are recorded as boot failures
with no latency, not as zeros.
*Evidence:* `results/kernels/boot-failures.txt`, `results/kernels/progress.log`.
*Answered by:* 邹浩宇.

**Q8. Isn't `BASE_ITER` 40 instead of 10,000 cheating?**
It changes precision, not the direction of the comparison, and it is stated in
the report and in the deviation table. What it does cost is sensitivity: with
three runs and a 10.9% median CV, differences below about 10% are not measurable
here. We say that in the limitations rather than claiming them.
*Evidence:* `report/report.tex` §Deviations; `docs/timer-floor.md` F1.
*Answered by:* 邹浩宇.

**Q9. What is the K-best rule?**
The authors' own statistic: take five samples that are within 5% of each other
and report the fastest. It rejects interference. We keep it inside each process
run and then report the mean and sample standard deviation of three runs, which
is the cross-run statistic the course asks for.
*Evidence:* `docs/REPRODUCTION.md`; `scripts/summarize_runs.py`.
*Answered by:* 邹浩宇.

**Q10. Can I re-derive your numbers?**
Yes — that is what the two verifiers are for. `scripts/verify_report_numbers.py`
recomputes the claim-1, claim-3 and extension numbers from `results/` and
compares them with the generated tables; `analysis/verify_timer_floor.py` does
the same for the timer-floor figures. Both run in CI on every push, so a number
that drifts breaks the build.
*Evidence:* `scripts/verify_report_numbers.py`, `analysis/verify_timer_floor.py`,
`.github/workflows/verify.yml`.
*Answered by:* 孙东旭.

**Q11. Why "not supported" and not "the paper is wrong"?**
Because absence of evidence on one 2-vCPU guest is not a refutation of a
measurement on a Xeon server. We can say the effect did not appear here, and for
KPTI we can say why it could not appear. Saying more than that would be
overclaiming.
*Evidence:* `docs/verdicts.md` §"What we cannot claim".
*Answered by:* 孙东旭.

**Q12. What would change your verdict?**
Bare metal with a CPU affected by Meltdown would give claim 2a a fair test;
kernels 3.0–3.5 that actually boot would give claim 1 its 3.0 baseline; and a
kernel rebuild per cause would give the eleven-cause ablation. Any one of those
would move a verdict; none of them is available on this guest.
*Evidence:* `docs/audit.md` §4.
*Answered by:* 孙东旭.

**Q13. How much of this was AI-assisted?**
Disclosed in the report. An assistant in Cursor drafted the runner, the reboot
script, the report and the slides; a second assistant supported the independent
re-analysis and the timer audit. Neither produced a measurement — every number
comes from `results/` and is recomputed by the verifiers.
*Evidence:* `report/report.tex` §AI usage statement.
*Answered by:* 邹浩宇.

**Q14. Did you modify the authors' benchmark?**
`TEST_DIR/OS_Eval.c` is untouched. We generate a reduced copy
(`course/OS_Eval_reduced.c`) that keeps the same clock calls and K-best rule and
compiles out three cases that either block or dominate runtime; the extension
binary differs by one changed test. Both are listed in the report.
*Evidence:* `course/make_reduced_eval.py`; `report/report.tex` §Starting code.
*Answered by:* 邹浩宇.

**Q15. Why is the TSC-based rewrite not used?**
Because on this guest the TSC is not a stable offset from the host, and the
rewrite did not serialise the instruction stream. The authors' `clock_gettime`
path is the one that survives virtualisation.
*Evidence:* `report/report.tex` §The other implementation.
*Answered by:* 邹浩宇.

**Q16. With more time, what is the first thing you would do?**
Boot patches for 3.0.7–3.5.4, because that single missing baseline is the only
thing standing between our claim-1 verdict and the paper's "75% slower than 3.0".
*Evidence:* `docs/audit.md` §4, P2.
*Answered by:* 邹浩宇.

---

## If you do not know

Three sentences that always work:

1. "We did not measure that." (then stop — do not fill the silence)
2. "That number is in `docs/verdicts.md`, and the file behind it is named there."
3. "I can check and come back to you after the session."

Never guess a number. The verifiers exist so that the printed numbers are the
only ones anyone has to defend.
