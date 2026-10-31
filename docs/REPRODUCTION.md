# Reproduction plan

Paper: Xiang (Jenny) Ren, Kirk Rodrigues, Luyuan Chen, Camilo Vega, Michael Stumm, and Ding Yuan. *An Analysis of Performance Evolution of Linux’s Core Operations.* SOSP 2019. <https://doi.org/10.1145/3341301.3359640>

Course: CS340 Operating Systems, academic year 2026–2027. The week of 2026-10-26 set the plan. The week of 2026-10-31 runs that plan on the VirtualBox guest. Measurements are the CSVs under `results/kernels/`. The report is `report/report.tex`.

## Starting code

| Item | Value |
| --- | --- |
| Upstream repository | <https://github.com/LinuxPerfStudy/LEBench> |
| Starting commit | `6aa7801` (`Merge pull request #9 from purplewall1206/master`) |
| License | Apache License 2.0, copyright 2019 University of Toronto (`LICENSE`) |
| Files modified from that commit | `README.md` |
| Files added | `.gitignore`, `Makefile`, `docs/REPRODUCTION.md`, `docs/CONTRIBUTIONS.md`, `results/README.md`, `scripts/run_current_kernel.py`, `scripts/summarize_runs.py`, `setup/Dockerfile` |

`run.py`, `get_kern.py`, `EXPERIMENTS.md`, `template/`, `grub`, and `TEST_DIR/` are the upstream sources and have not been edited. `run.py` and `get_kern.py` are Python 2, as published. The new runner is Python 3 and does not reboot the machine.

## Claims to test

1. **Figure 1(a).** Relative to Linux 4.0, the core operations measured by LEBench are slower on later kernels through 4.20, except big-write and big-munmap. The majority (75%) are also slower than on Linux 3.0, and many slow by at least 50%. The metric is the percentage change in latency of each LEBench test against the same test on 4.0.
2. **Table 3 and Figure 2.** Eleven changes — four security enhancements, four new features, and three configuration changes — account for the large fluctuations. Disabling the change that the paper names removes the corresponding spike. The metric is the latency change of the affected LEBench test with that one cause disabled.
3. **Section 5.** With those eleven changes disabled, Redis, Apache, and Nginx speed up by as much as 56%, 33%, and 34%. The metric is benchmark throughput or latency relative to the configured kernel the paper starts from.

Claim 1 is the main experiment. Claims 2 and 3 are the follow-on experiments. A smaller kernel set is acceptable for the course if the reduction is stated here and in the final report.

## Scope for the reduced reproduction

The paper runs all 36 Ubuntu kernels from 3.0.7 through 4.20.13 on one HP server, then rebuilds kernels with individual causes disabled. This repository cannot assume that server or those prebuilt kernels.

Planned scale:

- Run the unchanged `TEST_DIR/OS_Eval` suite on the kernels we can actually boot.
- Include Linux 4.0 (the paper’s baseline), one kernel before the 4.15 KPTI change, 4.15 or the first booted kernel where KPTI is present, and one later kernel. That is enough to test the direction of Claim 1, not the full heatmap.
- For Claim 2, toggle one cause at a time on a single kernel version, starting with a build-time switch the paper lists (`CONFIG_PAGE_TABLE_ISOLATION`, `CONFIG_RETPOLINE`, `CONFIG_SLAB_FREELIST_RANDOM`, `CONFIG_HARDENED_USERCOPY`, `CONFIG_MEMCG`, `CONFIG_USERFAULTFD`, or `CONFIG_CONTEXT_TRACKING_FORCE`).
- For Claim 3, keep the same kernel pair (causes on versus causes off) and run one of Redis, Apache, or Nginx rather than all three, unless time allows the full trio.
- Repeat every reported condition in at least three separate process invocations and publish mean ± sample standard deviation. The benchmark’s own K-best filter (K = 5, 5% tolerance) stays as published inside each invocation.

## Workloads

The microbenchmarks are the tests compiled from `TEST_DIR/OS_Eval.c`. Table 2 of the paper describes them: context switch, thread create, fork, read/write, mmap/munmap, page fault, send/recv, and select/poll/epoll, each at the sizes hard-coded in `main`. No external trace is downloaded. Application workloads, when we reach Claim 3, will be pinned by version in a later script (the paper uses Redis 4.0.8, Apache as in Section 5, and Nginx).

## Environment

Recorded for every batch in `results/<kernel>/<timestamp>/environment.txt`:

- `/etc/os-release`
- `uname` kernel release
- `gcc --version`, `make --version`, `python3 --version`

The paper’s reference machine is an HP DL160 G9, Xeon E5-2630 v3 at 2.40 GHz, 128 GB DDR4-1866, and a 960 GB SSD, running Ubuntu 16.04.6. The image in `setup/Dockerfile` pins the userspace toolchain to Ubuntu 22.04 with `build-essential` and Python 3. It does not pin the kernel, because the latency under test is the kernel’s.

## Deviations

| Item | Paper | Setting used | Reason |
| --- | --- | --- | --- |
| Hardware | HP DL160 G9, Xeon E5-2630 v3, 128 GB, 960 GB SSD | Whatever machine boots the kernel under test; model recorded in `environment.txt` | The paper’s server is not available. Absolute latencies will differ; comparisons use the same machine across kernels. |
| Kernel set | 36 versions in the paper; 41 releases in `EXPERIMENTS.md` | Every release in `EXPERIMENTS.md`, on the VirtualBox guest | The released list is the one that can be downloaded. Kernels that do not reach sshd are logged and skipped. |
| Userspace | Ubuntu 16.04.6 | Ubuntu 16.04.6 in VirtualBox (the Dockerfile is an unused alternate toolchain) | The guest matches the paper's distribution. Kernels older than 3.6 often reach a login prompt and never answer sshd. |
| Cross-run statistics | K-best inside one process; the paper does not report a cross-run standard deviation | At least three process runs, then mean ± sample standard deviation of the published K-best value | The course requires mean ± standard deviation across at least three runs. |
| Multi-kernel driver | `run.py` reboots through GRUB and runs `grub-install` on `/dev/sda1` | `scripts/vm_kernel_sweep.py` uses `grub-reboot` for one boot and always returns to 4.4.0-210 | Installing GRUB onto a partition can overwrite the host disk. One-shot reboot keeps a known-good kernel. |
| Application suite | Redis, Apache, and Nginx | Not run this week | The microbenchmark path has to exist before the macrobenchmarks. |

## What the measurements are

Logs from the guest are under `results/kernels/`. `results/kernel_summary.csv` is the mean and sample standard deviation of the K-best value over three runs. The English report is `report/report.tex` and the slides are `report/slides.tex`. Application benchmarks from Section 5 of the paper are still not run.
