# Final-week checklist

Last update: 2026-11-26. This file is the group's single source of truth for the
final submission week (presentation on 1 December 2026).

## Deadlines

| Milestone | Date | Status |
|---|---|---|
| Weekly Git check (last one) | Sunday 29 November, 23:59 | upcoming |
| Presentation | Tuesday 1 December | upcoming |
| Final report / final repository deadline | per *Presentation Instruction* or TA (not stated in the assignment PDF) | **confirm with TA** |
| `v1.0` tag | after the very last commit before the final deadline | to do |

TA: 2250025281@student.must.edu.mo — group form:
<https://v.wjx.cn/vm/rZCQLSE.aspx>

## Still open (with owner)

| # | Item | Owner |
|---|---|---|
| 1 | Add 孙东旭's line to the contribution statement in both reports, rebuild the PDFs (`make report`) | group |
| 2 | 邹涵锋 (1240020460) needs at least one substantive commit this week (message with ID + name) | 邹涵锋 |
| 3 | Obtain the *Presentation Instruction* and check slide format/length against it | group |
| 4 | Rehearse the 5-minute talk (`docs/talk-script.md`, `report/qa-card.pdf`) | group |
| 5 | Confirm the exact final submission deadline with the TA | group |

## Before the final deadline, in order

1. `make verify && make test` — all seven checks must pass (CI does this on every push).
2. `make report` — regenerate both PDFs if any `.tex` changed (requires `tectonic` on PATH).
3. Confirm the report PDF contains the final contribution statement for all four members.
4. `git tag -a v1.0 -m "CS340 final submission" && git push origin v1.0`
5. Re-check the group form has the correct repository link.

## What is already done

Documented in `docs/audit.md`: the 34-kernel sweep, four root-cause toggles
(KPTI, Retpoline, transparent hugepages, fault-around), the two-host
macrobenchmark, the batched-`getpid` and hugepage extensions, the full-iteration
protocol comparison (`results/fulliter/`), the reports and slides in English and
Chinese, and the CI that recomputes every published number.
