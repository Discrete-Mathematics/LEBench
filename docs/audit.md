# Project audit — what is done, what is missing

Date: 2026-11-21. Scope: repository `Discrete-Mathematics/LEBench` against the CS340
assignment (Final Report, Final Presentation, Git History Check). Every statement below
points at a file that exists in this repository.

## 1. What exists

| Area | Evidence | State |
|---|---|---|
| Kernel sweep (claim 1) | `results/kernels/` (34 kernels × 3 runs), `results/kernel_summary.csv`, `analysis/`, `docs/timer-floor.md` | done, verdict *not supported* |
| Root causes (claim 2) | `results/kernels/4.4.0-210-nopti/` (KPTI), `results/macro/{default,spectre-off}/` (Retpoline), `results/thp/` (transparent hugepages, 3 modes × 3 runs), `results/fault-around/` (fault-around window) | four of eleven causes, verdict *not supported* on this CPU/guest |
| Applications (claim 3) | `results/macro/`, `report/generated/macro_table.tex` | done for one kernel and one switch, verdict *not supported* |
| Applications, cross-host (claim 3) | `results/macro-host2/`, `docs/cross-host.md` | same experiment on a second host; the switch's direction reverses, so the negative verdict is robust |
| Extensions | `results/batching/` (batched `getpid`), `results/thp/` (hugepage modes) | both done, single-factor designs |
| Report | `report/report.tex` + `report.pdf`, `report/report_zh.tex` + `report_zh.pdf` | drafted, needs the fixes in §3 |
| Slides and talk | `report/slides.{tex,pdf}`, `slides_zh.*`, 5-minute cut, `report/qa-card.pdf`, `docs/talk-script.md`, `docs/qa-bank.md` | drafted |
| Reproduction notes | `docs/REPRODUCTION.md`, deviations table in the report | done |
| Numbers traceable | `scripts/verify_report_numbers.py`, unit tests, CI (`.github/workflows/verify.yml`) | **passes** (see §2) |

## 2. Traceability check

`scripts/verify_report_numbers.py` recomputes every published number from the result
files and compares it with the generated LaTeX. Current output:

```
[PASS] claim 1 (kernel sweep)
[PASS] claim 3 (macrobenchmark)
[PASS] claim 3 (cross-host)
[PASS] extension (batched getpid)
[PASS] extension (transparent hugepages)
[PASS] claim 2 (fault-around)

6 checked, 0 failed
```

Claim 1 recomputes 627 measurements on the 19 later kernels, 271 with a higher mean,
76 at least 50% higher, 117 with disjoint intervals — exactly the numbers in
`report/generated/claim_summary.tex`. The same checks run in CI on every push and
`make verify` / `make test` run them locally. Re-run after any table is edited.

## 3. Gaps against the assignment

Ordered by what the rubric penalises.

1. **Contribution statement covers one member only.** `report/report.tex` credits only
   邹浩宇, although 孙东旭 (`analysis/`, `docs/timer-floor.md`) and 张澄心 (`macrobench/`,
   `scripts/verify_report_numbers.py`, tests and CI) also have commits and files. The
   rubric grades *individual* contributions (10% of the Git history check) and the
   report must carry a contribution statement. *Fix:* add one line per member with the
   work their commits record, then rebuild the PDF.

2. **No dedicated Limitations section.** Limitations are scattered through the analysis.
   The rubric's structure asks for one. *Fix:* one short section listing: one machine,
   reduced iteration count, 34 of 41 kernels, three of eleven causes, timer floor, CPU
   not subject to Meltdown, one kernel for claim 3.

3. **Discrepancy gaps are relative only.** The report gives percentages but not absolute
   differences. Defensible (the guest's absolute latencies are not comparable), but it
   should be stated explicitly rather than implied.

4. **AI usage statement names one assistant.** It should describe the assistance
   actually used (more than one assistant contributed across the term).

5. **No `v1.0` tag.** The final deadline requires the repository to be tagged `v1.0`
   after the last commit.

6. **The eleven-cause ablation is not reproduced.** Four of the eleven causes were
   toggled (`nopti`, `spectre_v2=off`, hugepage modes, fault-around). This is a scope
   decision, not an oversight; it must stay in the Limitations section.

7. **Linux 3.0 baseline missing.** 3.0.7–3.5.4 never reached sshd, so the paper's
   "75% slower than 3.0" cannot be tested. Recorded in `results/kernels/boot-failures.txt`.

8. **Duplicate directories.** `analysis/analysis/` and `docs/docs/` were created by two
   "add files via upload" commits and duplicate `timer_floor.py` and `timer-floor.md`.
   Nothing references the nested copies; they can be removed in a cleanup commit.

## 4. Next steps

| Priority | Action | Where |
|---|---|---|
| P0 | Add the missing members to the contribution statement; add a Limitations section; update the AI usage statement; rebuild `report.pdf` and `report_zh.pdf` | `report/*.tex` |
| P0 | After the last commit before the deadline: `git tag -a v1.0 -m "CS340 final" && git push origin v1.0` | repository |
| P1 | Add one sentence on absolute versus relative gaps | `report/report.tex` |
| P1 | Rehearse the 5-minute talk against `docs/talk-script.md` and the separate Presentation Instruction | `report/slides.tex` |
| P2 | Remove the duplicated `analysis/analysis/` and `docs/docs/` trees | repository |
| P2 | Optional: boot patches for 3.0–3.5 to recover the 3.0 baseline | `results/kernels/` |

## 5. Weekly commit hygiene

Every member needs at least one meaningful commit per week, with the student ID and name
in the message. Current recorded authors: 邹浩宇 (`5260000157`), 张澄心 (`1240016541`),
孙东旭 (`5260000073`). 邹涵锋 (`1240020460`) has no commit in the history — either add one
or state the contribution explicitly.
