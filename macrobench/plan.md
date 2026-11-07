# Claim 3 pre-registration — macrobenchmark speed-up

Written before any macrobenchmark number was collected, so that the verdict cannot be
chosen after seeing the data.

## Question

The paper (§5, Figure 7) says that disabling the 11 root causes speeds up Redis, Apache
and Nginx by up to 56%, 33% and 34%, and 19%, 6.5% and 10% on average across kernels.
Can a single runtime-togglable cause produce a measurable speed-up on this guest, in the
same direction and of a plausible magnitude?

## Hypotheses

- **H1 (direction).** With `spectre_v2=off`, Redis throughput rises by at least the
  run-to-run noise floor (one standard deviation), and Apache/Nginx show the same sign.
- **H2 (magnitude).** The Redis speed-up is smaller than the paper’s 56% maximum,
  because the paper disables all 11 causes while we disable one.
- **H3 (mechanism).** The effect is larger for syscall-dense workloads (Redis, 41% system
  time in the paper’s Table 1) than for the web servers.

## Design

- Machine: the CS340 VirtualBox guest, Ubuntu 16.04.6, 2 vCPU, 4 GB — identical to the
  kernel sweep, so the comparison stays within one machine.
- Kernel: 4.4.0-210-generic (the guest’s known-good kernel). One factor changes between
  batches: the kernel command line.
- Configurations:
  - `default` — no extra parameters (mitigations as configured by the distribution).
  - `spectre-off` — adds `spectre_v2=off`; `nopti` added only if the guest reports a
    Meltdown-affected CPU.
- Repetitions: 3 independent runs per configuration; the unit of analysis is the mean of
  the three runs, and the report quotes mean ± sample standard deviation.
- Workloads (fixed, from the paper):
  - Redis: `redis-benchmark -n 100000 -c 50 -t rpush,spop,rpop,get,lrange`
  - Apache: `ab -n 100000 -c 100 http://127.0.0.1/`
  - Nginx: `ab -n 100000 -c 100 http://127.0.0.1:8080/`
- Order: interleave configurations per run where possible (default, spectre-off, default,
  …) so that a slow drift in the machine does not load onto one configuration. If a
  reboot is required between configurations, note it in `environment.txt` and run the
  configurations on the same day.

## Verdict rules

- **supported** — same sign on all three applications, Redis speed-up ≥ 2× the pooled
  standard deviation, and magnitude within a factor of two of the paper’s average.
- **partially supported** — same sign, but magnitude clearly below the paper’s average.
- **not supported** — sign reversed, or the effect is inside the noise.
- **inconclusive** — the toggle did not take effect (check
  `/sys/devices/system/cpu/vulnerabilities/spectre_v2`), or the services did not answer
  identically across configurations.

## Known limitations (to state in the report)

1. One cause out of eleven; the paper’s 56% is a sum over causes.
2. One kernel, not the paper’s 36–41.
3. Virtualized network and disk; `ab` measures loopback HTTP, so syscall overhead is
   diluted by the virtual NIC.
4. Redis 4.0.8 is the paper’s version, but Apache/Nginx are Ubuntu 16.04 packages, not
   the paper’s builds.
