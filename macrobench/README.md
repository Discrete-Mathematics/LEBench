# Claim 3 — macrobenchmark harness

The report currently leaves Claim 3 (“disabling the kernel changes speeds up Redis,
Apache and Nginx by up to 56%, 33% and 34%”) as *not tested*. This directory runs a
reduced but honest version of that experiment on the same Ubuntu 16.04.6 guest that
produced `results/kernels/`.

What we can and cannot reproduce:

| Paper | Here |
|---|---|
| Disables all 11 root causes | Disables one runtime-togglable cause at a time (`spectre_v2=off`, optionally `pti=off`) |
| Redis 4.0.8, Apache, Nginx | Redis 4.0.8 built from source (falls back to the distro build), Apache 2.4, Nginx 1.10 |
| 100,000 requests, 50/100 connections | Same parameters |
| max and average speed-up over all kernels | Speed-up on one kernel, mean ± std over 3 runs |

Because the guest CPU reports Meltdown as “Not affected”, `pti=off` is a no-op there.
Retpoline (Spectre v2) is still active on 4.4.0-210, so `spectre_v2=off` is the toggle
that can actually move the numbers.

## Layout

```
macrobench/
├── install_guest.sh      # one-time: redis 4.0.8, apache2, nginx (port 8080), ab
├── run_macrobench.sh     # runs the three benchmarks N times, writes raw logs + results.csv
├── parse_macrobench.py   # raw results.csv -> summary.csv / summary.txt (mean ± std, ratios)
├── plan.md               # pre-registered design, hypotheses and verdict rules
└── README.md
results/macro/<config>/   # environment.txt, raw/*.log, results.csv, summary.csv
```

## Usage

Inside the guest (Ubuntu 16.04.6), as a user with sudo:

```bash
bash macrobench/install_guest.sh          # once per VM
bash macrobench/run_macrobench.sh --config default --runs 3
# reboot with the kernel parameter under test, then:
bash macrobench/run_macrobench.sh --config spectre-off --runs 3
python3 macrobench/parse_macrobench.py results/macro
```

The runner refuses to start if a service is not answering, and records the command
line plus `/sys/devices/system/cpu/vulnerabilities/*` in every batch so a toggle that
did not take effect is visible in the logs.

## Runtime

- Redis: 100,000 requests over 5 command types at 50 connections — about 1 minute.
- Apache/Nginx: `ab -n 100000 -c 100`, 2 runs of `ab` per app — a few minutes.
- Three repetitions per configuration: roughly 15–25 minutes per boot.

## Results format

`results.csv` is long-form, one row per observation:

```
config,run,app,test,metric,value,unit
default,1,redis,RPUSH,throughput,412345.67,req_per_s
default,1,apache,index,throughput,8123.45,req_per_s
default,1,apache,index,latency_mean,12.31,ms
```

`parse_macrobench.py` turns it into mean ± std per (config, app, test, metric) and, when
a `default` batch exists, the ratio of every other configuration against it.
