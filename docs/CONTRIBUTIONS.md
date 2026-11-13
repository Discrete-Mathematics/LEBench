# Contributions

| Name | Student ID | Work so far |
| --- | --- | --- |
| 邹浩宇 | 5260000157 | Week of 2026-10-26: imported LEBench at upstream commit `6aa7801`, wrote the reproduction plan, and added the single-kernel runner. Week of 2026-10-31: built the Ubuntu 16.04.6 guest, ran the reduced LEBench suite three times per booted kernel, compared `nopti` on 4.4.0-210, and wrote the report and slides. Week of 2026-11-09: ran Redis 4.0.8, Apache, and Nginx on 4.4.0-210 with and without `spectre_v2=off`, and recorded the logs under `results/macro/`. |
| 张澄心 | 1240016541 | Week of 2026-11-07: Claim 3 macrobenchmark harness (`macrobench/`), pre-registered design and verdict rules (`macrobench/plan.md`), results layout and aggregation script. Week of 2026-11-13: independent verification of every published number from `results/` (`scripts/verify_report_numbers.py`) and the rubric-by-rubric project audit (`docs/audit.md`). |
| 孙东旭 | 5260000073 | Week of 2026-11-01: independent re-analysis of the sweep (`analysis/`, `docs/analysis-note.md`). Week of 2026-11-08: timer-resolution audit (`analysis/timer_floor.py`, `docs/timer-floor.md`). |
