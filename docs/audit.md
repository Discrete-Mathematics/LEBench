# Project audit — what is done, what is missing

Date: 2026-11-13. Scope: repository `Discrete-Mathematics/LEBench` against the CS340
assignment (Final Report, Final Presentation, Git History Check). Every statement below
points at a file that exists in this repository.

## 1. What exists

| Area | Evidence | State |
|---|---|---|
| Kernel sweep (claim 1) | `results/kernels/` (34 kernels × 3 runs), `results/kernel_summary.csv`, `analysis/`, `docs/timer-floor.md` | done, verdict *not supported* |
| Root cause, one factor (claim 2) | `results/kernels/4.4.0-210-nopti/`, `report/generated/extension_table.tex` | partial, verdict *not supported* on a CPU without Meltdown |
| Applications (claim 3) | `results/macro/{default,spectre-off}/`, `results/macro/summary.csv`, `report/generated/macro_table.tex` | done for one kernel and one switch, verdict *not supported* |
| Extension | `results/batching/`, `course/OS_Eval_batched.c`, `report/generated/batch_table.tex` | done (batched `getpid`) |
| Report | `report/report.tex` + `report.pdf`, `report/report_zh.tex` + `report_zh.pdf` | drafted, needs the fixes in §3 |
| Slides | `report/slides.tex`, `slides.pdf`, `slides_zh.*` | drafted |
| Reproduction notes | `docs/REPRODUCTION.md`, deviations table in the report | done |
| Numbers traceable | `scripts/verify_report_numbers.py` | **passes** (see §2) |

## 2. Traceability check

`scripts/verify_report_numbers.py` recomputes every published number from the result
files and compares it with the generated LaTeX. Current output:

```
[PASS] claim 1 (kernel sweep)
[PASS] claim 3 (macrobenchmark)
[PASS] extension (batched getpid)

3 checked, 0 failed
```

Claim 1 recomputes 627 measurements on the 19 later kernels, 271 with a higher mean,
76 at least 50% higher, 117 with disjoint intervals — exactly the numbers in
`report/generated/claim_summary.tex`. Re-run this script after any table is edited.

## 3. Gaps against the assignment

Ordered by what the rubric penalises.

1. **Contribution statement covers one member only.** `report/report.tex` line ~195
   credits only 邹浩宇. 孙东旭 (`analysis/`, `docs/timer-floor.md`) and 张澄心
   (`macrobench/`, `scripts/verify_report_numbers.py`) have commits and files but are not
   in the statement. The rubric grades *individual* contributions (10% of the Git
   history check) and the report must carry a contribution statement.
   *Fix:* add one line per member with the work their commits record, then rebuild the PDF.

2. **No dedicated Limitations section.** Limitations are scattered (lines 146, 155, 157 of
   the report). The rubric's structure asks for one. *Fix:* one short section listing: one
   machine, reduced iteration count, 34 of 41 kernels, no eleven-cause ablation, timer
   floor, CPU not subject to Meltdown, single kernel for claim 3.

3. **Discrepancy gaps are relative only.** The report gives percentages but not absolute
   differences. This is defensible because the guest's absolute latencies are not
   comparable, but it should be stated explicitly rather than implied.

4. **AI usage statement names one assistant.** It should describe the assistance actually
   used (more than one assistant contributed across the term).

5. **No `v1.0` tag.** The final deadline requires the repository to be tagged `v1.0`
   after the last commit.

6. **The eleven-cause ablation is not reproduced.** Only two runtime toggles were used
   (`nopti`, `spectre_v2=off`). This is a scope decision, not an oversight; it must stay
   in the Limitations section.

7. **Linux 3.0 baseline missing.** 3.0.7–3.5.4 never reached sshd, so the paper's
   "75% slower than 3.0" cannot be tested. Recorded in `results/kernels/boot-failures.txt`.

## 4. Next steps

| Priority | Action | Where |
|---|---|---|
| P0 | Rewrite the contribution statement for all four members; add a Limitations section; rebuild `report.pdf` and `report_zh.pdf` | `report/*.tex` |
| P0 | Update the AI usage statement | `report/report.tex` |
| P0 | After the last commit before the deadline: `git tag -a v1.0 -m "CS340 final" && git push origin v1.0` | repository |
| P1 | Add one sentence on absolute versus relative gaps | `report/report.tex` |
| P1 | Rehearse the 12–15 minute talk; confirm against the separate Presentation Instruction | `report/slides.tex` |
| P2 | Optional: two more runtime toggles (THP, idle states) for claim 2 | `results/kernels/` |
| P2 | Optional: boot patches for 3.0–3.5 to recover the 3.0 baseline | `results/kernels/` |

## 5. Weekly commit hygiene

Every member needs at least one meaningful commit per week, with the student ID and name
in the message. Current recorded authors: 邹浩宇 (`5260000157`), 张澄心 (`1240016541`),
孙东旭 (`5260000073`). 邹涵锋 (`1240020460`) has no commit in the history — either add one
or state the contribution explicitly.
