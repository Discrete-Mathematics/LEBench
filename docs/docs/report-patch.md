# Report patch — the three P0 text fixes

**Author:** 孙东旭 (5260000073)
**Target:** `report/report.tex` (and `report/report_zh.tex` if it carries the same sections)
**Why:** `docs/audit.md` §3 lists four P0 gaps; three of them are text-only and are
written out below, ready to paste. The fourth (the `v1.0` tag) is a git action.

Paste, rebuild, done — the person pasting does **not** need to rewrite anything.

---

## How to apply

1. Open `report/report.tex` in the GitHub editor (or locally).
2. **Block A** replaces the current `\section*{Contribution statement}` paragraph.
3. **Block B** replaces the current `\section*{AI usage statement}` paragraph.
4. **Block C** is inserted as a new section immediately **before** `\section{Conclusion}`.
5. **Block D** is one optional sentence for the Analysis section (the audit's P1).
6. Rebuild twice: `pdflatex report.tex && pdflatex report.tex`, then the same for
   `report_zh.tex` if it has the same sections.
7. Sanity check after rebuilding:

```bash
python3 scripts/verify_report_numbers.py     # 3 checks, must still pass
python3 analysis/verify_timer_floor.py       # 9 checks, must still pass
```

Nothing in these blocks introduces a new number, so both verifiers must keep
passing unchanged.

---

## Block A — Contribution statement (replaces the current one)

```latex
\section*{Contribution statement}

Four students carried this reproduction. \textbf{Haoyu Zou (5260000157)} imported
LEBench at \texttt{6aa7801}, built the Ubuntu 16.04.6 guest, wrote the reduced
runner and the reboot driver, collected the logs under \texttt{results/kernels/},
measured the batched-\texttt{getpid} variant under \texttt{results/batching/},
ran the Redis, Apache, and Nginx comparison under \texttt{results/macro/}, and
drafted the report and the slides.
\textbf{Dongxu Sun (5260000073)} analysed the sweep independently
(\texttt{analysis/}, \texttt{docs/analysis-note.md}), audited the timer
resolution of every measurement (\texttt{analysis/timer\_floor.py},
\texttt{docs/timer-floor.md}), and added the verifier that pins those numbers to
the logs (\texttt{analysis/verify\_timer\_floor.py}).
\textbf{Chengxin Zhang (1240016541)} built the claim-3 harness
(\texttt{macrobench/}) and fixed its hypotheses and verdict rules before any data
existed, verified every published number against the logs
(\texttt{scripts/verify\_report\_numbers.py}), audited the repository against the
assignment (\texttt{docs/audit.md}), and added the unit tests and the CI job.
\textbf{Hanfeng Zou (1240020460)} [TODO --- one sentence naming this member's
work; no commit is recorded under this student ID yet, so the group must confirm
what to write].
Commits for each piece of work carry the student ID and name of the member who
did it.
```

> **Note on the last member.** `docs/audit.md` §5 records that 1240020460 has no
> commit in the history. Either that member commits something before the
> deadline (any of the P1/P2 items in the audit), or the group replaces the TODO
> with a sentence describing work done offline (for example reading the paper,
> preparing the Chinese translation, or checking the slides). Do not submit the
> paragraph with a TODO in it.

---

## Block B — AI usage statement (replaces the current one)

```latex
\section*{AI usage statement}

AI assistants were used, and are disclosed here in full. An AI coding assistant
in Cursor drafted the runner, the reboot script, this report and the slides, and
operated the virtual machine. A second assistant supported the independent
re-analysis and the timer-resolution audit (\texttt{analysis/},
\texttt{docs/timer-floor.md}), including the statistics correction recorded in
that note's revision section. Neither assistant produced a measurement: every
latency in this report comes from the guest logs under \texttt{results/}, and
every published number is recomputed from those logs by
\texttt{scripts/verify\_report\_numbers.py} and
\texttt{analysis/verify\_timer\_floor.py}, both of which run in CI on every push.
```

---

## Block C — Limitations section (new section, insert before `\section{Conclusion}`)

```latex
\section{Limitations}

\paragraph{One machine.} Every measurement comes from a single VirtualBox guest
on an i7-13700H host. The paper used an HP DL160 G9 and repeated the sweep on a
laptop; we did neither. No absolute latency here is comparable with the paper's,
which is why every gap we report is quoted as a ratio or a percentage and never
as an absolute nanosecond difference.

\paragraph{Reduced workload.} \texttt{BASE\_ITER} is 40 rather than 10{,}000, the
60-second settle is omitted, and three cases are compiled out (the 96\,KB
send/recv pair, the 12{,}000-page fork, and the 10{,}000-page file tests). A
shorter window makes the K-best rule more sensitive to a single outlier: the
median coefficient of variation is 10.9\%, so differences below roughly 10\% are
not measurable on this guest.

\paragraph{Kernel coverage.} 34 of the 41 releases in \texttt{EXPERIMENTS.md}
booted far enough to be measured. Kernels 3.0.7--3.5.4 install and then never
answer sshd, so the paper's ``75\% of tests are slower than 3.0'' cannot be
tested at all, and 4.19.11 was not installable from the published packages.

\paragraph{Timer resolution.} The empty-syscall floor of a boot ranges from 0 to
305\,ns across the 36 boots. We drop the 56 of 1152 rows (4.9\%) that sit within
3$\times$ the floor of their own boot; \texttt{getpid} is the only test affected
systematically. The verdict is unchanged for any threshold between 1$\times$ and
10$\times$ (median relative latency 1.032--1.044, clearly-slower share
27.1--27.9\%).

\paragraph{CPU not subject to Meltdown.} The host reports Meltdown as ``Not
affected'', so page-table isolation is not engaged on any boot and
\texttt{nopti} cannot reproduce the paper's KPTI cost. The claim-2 experiment is
therefore \emph{inconclusive} with respect to the paper's mechanism; it does not
refute it.

\paragraph{No eleven-cause ablation.} We toggle two runtime switches
(\texttt{nopti} and \texttt{spectre\_v2=off}). The other nine causes in the
paper's Table~3 need kernel rebuilds, which this guest cannot afford.

\paragraph{Claim 3 on one kernel.} The application comparison uses one kernel and
one switch, not eleven causes across many kernels, and the paper's percentages
are not attainable under that design.

\paragraph{Boot-level artifacts.} Three boots (4.16.13--4.18.16) show a shifted
time base: the pure-CPU control, which never enters the kernel, is twice as fast
there. Those rows are excluded from every cross-kernel statement rather than
averaged in.
```

---

## Block D — optional P1 sentence

The audit asks for the relative-versus-absolute point to be explicit. Block C's
first paragraph now says it; if you also want it in the Analysis section, append
this sentence to the first paragraph of `\section{Analysis}`:

```latex
Every gap in this report is relative by construction: the guest's absolute
latencies are not the paper's, so we never quote an absolute difference against
the paper.
```

---

## After the patch

| Item | Where | Who |
| --- | --- | --- |
| Rebuild `report.pdf` and `report_zh.pdf` | local TeX or Overleaf | whoever has the toolchain |
| Re-run both verifiers | `scripts/` and `analysis/` | anyone, 10 s |
| Fill the TODO in Block A | `report/report.tex` | 邹涵锋 or the group |
| `git tag -a v1.0 -m "CS340 final" && git push origin v1.0` | after the last commit | 邹浩宇 |
