# LEBench reproduction (CS340)

This repository reproduces Ren et al., *An Analysis of Performance Evolution of Linux’s Core Operations* (SOSP 2019), using the authors’ [LEBench](https://github.com/LinuxPerfStudy/LEBench) microbenchmarks. The study asks whether the latency of core kernel operations (system calls, page faults, context switching, and related paths) got slower as Linux went from 3.0 to 4.20, and which kernel changes caused the regressions.

The course write-up and the claims under test are in [docs/REPRODUCTION.md](docs/REPRODUCTION.md). Who committed what is in [docs/CONTRIBUTIONS.md](docs/CONTRIBUTIONS.md).

## Credit and starting point

- Upstream: <https://github.com/LinuxPerfStudy/LEBench>
- Starting commit: `6aa7801` (`Merge pull request #9 from purplewall1206/master`)
- License: Apache License 2.0, copyright 2019 University of Toronto. See `LICENSE`.
- Unmodified upstream sources: `run.py`, `get_kern.py`, `EXPERIMENTS.md`, `template/`, `grub`, `TEST_DIR/OS_Eval.c`, `TEST_DIR/makefile`
- Files changed or added for the course are listed in [docs/REPRODUCTION.md](docs/REPRODUCTION.md)

The upstream experiment notes are in [EXPERIMENTS.md](EXPERIMENTS.md). They describe the original HP DL160 G9 server, Ubuntu 16.04.6, and the 36 kernels from 3.0.7 to 4.20.13.

## Setup

The benchmark calls Linux system calls directly. Build and run it on Linux. A Windows checkout can hold the sources, but `OS_Eval` will not compile or run there.

Host packages:

```bash
sudo apt-get update
sudo apt-get install -y build-essential python3
```

The same packages are pinned for the userspace toolchain in `setup/Dockerfile` (`ubuntu:22.04`, `build-essential`, `python3`). That image does not select the kernel. LEBench measures the kernel that is running, so kernel comparisons have to boot each kernel.

```bash
docker build -f setup/Dockerfile -t lebench-toolchain .
```

Set `LEBENCH_DIR` to this repository with a trailing slash. `OS_Eval` concatenates that prefix onto its output names and its socket path.

```bash
export LEBENCH_DIR="$(pwd)/"
```

`scripts/run_current_kernel.py` sets this itself. The upstream `run.py` harness does not; export it before using `run.py`.

## Build and run

Single kernel, three repetitions (the course asks for mean ± standard deviation across at least three runs):

```bash
python3 scripts/run_current_kernel.py --runs 3
```

The same command is `make bench`. Context-switch tests raise their scheduling priority and are less noisy as root:

```bash
sudo -E python3 scripts/run_current_kernel.py --runs 3
```

Check the summary arithmetic without a machine measurement:

```bash
python3 scripts/summarize_runs.py --self-test
```

Multi-kernel sweep on the course VM (Python 3). It installs the Ubuntu image debs listed in `EXPERIMENTS.md`, boots each one with `grub-reboot`, and stores three reduced runs under `results/kernels/`. A kernel that never reaches sshd is appended to `results/kernels/boot-failures.txt` and is not retried.

```bash
python scripts/vm_kernel_sweep.py
python scripts/summarize_kernel_sweep.py
python scripts/render_results.py
```

The reduced binary uses `BASE_ITER` 40 and omits the three long cases named in `course/make_reduced_eval.py`. Thirty-four of the 41 listed kernels have three runs under `results/kernels/`. `course/make_batched_eval.py` changes only `getpid`: 1,000 calls per sample, then divide. `scripts/run_batched_extension.py` runs that binary three times; logs are `results/batching/`.

```bash
python3 course/make_batched_eval.py
gcc -O0 -pthread -o course/batched_bench course/OS_Eval_batched.c
```

The password is read from `LEBENCH_VM_PASSWORD` or from a local `Password:` line. It is not stored in this repository. Do not point the upstream `run.py` harness at a machine you cannot reboot, and do not let it run `grub-install` against the Windows disk. Details are in the upstream section below.

## Expected outputs and runtime

Each invocation creates `results/<kernel-release>/<UTC-timestamp>/`:

| File | Contents |
| --- | --- |
| `environment.txt` | OS, kernel release, gcc, make, Python |
| `run<N>/stdout.txt` | Progress lines, including `Test took:` |
| `run<N>/stderr.txt` | Errors from `OS_Eval` |
| `run<N>/exit_code.txt` | Process exit status |
| `run<N>/output.<kernel>.csv` | Per-test K-best and average latency, in seconds |
| `summary.csv` | Mean and sample standard deviation across the runs |

The directory layout is also described in [results/README.md](results/README.md). The virtual-machine sweep is checked in under `results/kernels/`, and the batched-`getpid` runs under `results/batching/`.

`OS_Eval` sleeps 60 seconds at startup, then runs on the order of 10^5 to 10^6 iterations of each microbenchmark (fork, page fault, select, send/recv, and the rest of Table 2 in the paper). On the class of server used in the paper, plan on roughly one to a few hours per pass. Three passes is the default, so leave the machine otherwise idle for that long. The script stops if a pass exits non-zero and leaves the logs in place.

## Group

| Name | Student ID |
| --- | --- |
| 邹浩宇 | 5260000157 |
| 孙东旭 | 5260000073 |
| 张澄心 | 1240016541 |
| 邹涵锋 | 1240020460 |

## Upstream instructions

The remainder of this file is the original LEBench run instructions, kept so the multi-kernel harness can still be followed.

Run `crontab -e` and add the following entries:

```
LEBENCH_DIR=<path>/LEBench/
PATH=/bin:/usr/local/bin:/usr/bin:/usr/local/sbin:/usr/sbin
@reboot python <path>/LEBench/run.py >> <path>/LEBench.out 2>&1
```

Run `python get_kern.py` to generate the kernel list.

Run `sudo python run.py`.

Results will be saved in .csv files in the LEBench folder.

Detailed instructions for reproducing the main results in the original study are in [EXPERIMENTS.md](EXPERIMENTS.md).
