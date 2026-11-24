# Five-minute talk — the script, the timing, and who says what

The deck is `report/slides.tex`: eight slides, five minutes, four speakers. This
file turns the `\note{}` budgets into words you can rehearse.

Compiled by 孙东旭 (5260000073). Updated 24 November 2026: slides 5 and 6 gain
half a sentence each for the fault-around ablation and the second host. **No new
slides** — the five-minute budget does not allow one.

---

## The shape of the five minutes

| # | Slide | Time | Speaker | The one job |
|---|---|---|---|---|
| 1 | Title | 0:00–0:10 | 邹涵锋 | Paper and four speakers. |
| 2 | What the paper claims | 0:10–1:00 | 邹涵锋 | Four claims, no numbers, no verdicts. |
| 3 | What actually runs | 1:00–2:00 | 邹浩宇 | guest → one `grub-reboot` → three runs → mean ± stdev |
| 4 | Across kernels | 2:00–2:25 | 邹浩宇 | 43%, 12%, "not supported". |
| 5 | Two switches (+ fault-around clause) | 2:25–2:55 | 邹浩宇 | `nopti`, hugepages, fault-around: all not supported. |
| 6 | Claim 3 (+ second host) | 2:55–3:30 | 张澄心 | Apache slower, Nginx faster, Redis flat; second host flips Redis. |
| 7 | What this guest cannot show | 3:30–4:30 | **孙东旭** | hardware, missing 3.0 baseline, the clock. |
| 8 | For someone running this CPU | 4:30–5:00 | 邹浩宇 | one sentence, stop. |

Word budget: ~140 words per minute, so ≤ 720 words for the whole talk.
Slide 7 is 60 s ≈ 150 words; slide 4 is 25 s ≈ 60 words.

---

## Slide 7 — your 60 seconds (孙东旭)

Three beats: hardware, baseline, clock.

> **0:00–0:05** "Three things this guest cannot show."
>
> **0:05–0:20** "First, the hardware. Two virtual CPUs, four gigabytes, a laptop
> chip. The paper measured a Xeon with a hundred and twenty-eight. Absolute
> numbers are not comparable, so we only ever compare ratios on the same
> machine."
>
> **0:20–0:35** "Second, the baseline. Kernels three-point-zero-point-seven
> through three-point-five-point-four install, reach a login prompt, and never
> answer sshd. Without 3.0 there is no way to test the paper's 'seventy-five per
> cent slower than 3.0'."
>
> **0:35–0:55** "Third — and this one is mine — the clock. A wrong timer still
> prints a number. Three boots, 4.16 through 4.18, look about twice as fast. So
> does the pure-CPU loop, which never enters the kernel at all. A kernel cannot
> make a fixed loop twice as fast, so those boots have a shifted time base, not a
> faster kernel. We exclude them instead of averaging them in."
>
> **0:55–1:00** "That is the honest limit: one machine, and one of its clocks was
> not constant."

**Delivery.** Say "pure-CPU loop" slowly — it is the whole argument in three
words. Do not hedge ("look faster, but actually…"): state the observation, then
"A kernel cannot do that". If you are past 45 s at "We exclude them", drop the
last sentence.

**If someone pushes back later** ("so were your numbers wrong?"): "No — the
numbers are what the machine produced; we removed the boots where the clock
itself moved. And we wrote the re-run that proves it: `docs/drift-plan.md`."

---

## Slide 2 — 邹涵锋 (50 s)

"Ren and colleagues measured the latency of core Linux operations from 3.0 to
4.20 and argued the kernel got slower. Four claims. One: most operations are
slower on later kernels, apart from big write and big munmap. Two: eleven
changes explain the jumps — security work, new features, and configuration
mistakes. Three: turning those eleven off speeds up Redis, Apache and Nginx.
Four: the effect is large — up to fifty-six per cent."

*No numbers beyond the paper's own, no verdicts. Stop at one minute.*

## Slide 3 — 邹浩宇 (60 s)

"We rebuilt nothing. The functions are the authors'. One guest, two virtual CPUs,
four gigabytes. For each kernel the driver writes one boot entry, reboots once,
runs the reduced suite three times, and returns to a known-good kernel. Each
number is the mean and sample standard deviation of three runs. The K-best rule
and the clock are the authors' — `clock_gettime`, five samples within five per
cent. `BASE_ITER` is forty instead of ten thousand, because a full pass takes
hours here."

## Slide 4 — 邹浩宇 (25 s)

"Here is the claim against our logs. Relative to our 4.0.5, two hundred and
seventy-one of six hundred and twenty-seven later measurements have a higher
mean — forty-three per cent. Seventy-six, twelve per cent, are at least fifty per
cent higher. That is not 'most tests, many by half'. Claim one is not supported."

## Slide 5 — 邹浩宇 (30 s, was 25)

"Three switches, same kernel. `nopti`: getpid 314 against 295 nanoseconds,
intervals overlap, fork moves the wrong way. Hugepages, three modes: every pair
overlaps. Fault-around, two window sizes, six interleaved runs: the page-fault
rows stay inside the noise — the suite maps a thousand pages and touches one
byte, so it cannot exercise the feature. No cause survives."

## Slide 6 — 张澄心 (35 s, was 40)

"Claim three, one switch, and then the same switch on a second host. On the
first: the sysfs line moves from Enhanced IBRS to Vulnerable, so it took effect.
Apache 1580 to 1308 requests per second, slower, intervals disjoint. Nginx 5725
to 7314, faster, disjoint. Redis means rise, intervals overlap. On the second
host the Redis direction flips. One switch does not reproduce eleven causes, and
what it does reproduce does not transfer between machines."

## Slide 8 — 邹浩宇 (30 s)

"On this virtual machine the paper's slowdown and these switches were not
reproduced. This i7 is not affected by Meltdown, so a mitigation that matters on
an older server is not evidence on this hardware. Thank you — questions welcome."

---

## Rehearsal plan

| Pass | When | What | Target |
|---|---|---|---|
| 1 | 26 Nov | each speaker alone with a stopwatch | own part ±5 s |
| 2 | 28 Nov | full run, slides clicked live | total ≤ 5:00 |
| 3 | 30 Nov | full run in the room, phone timer | total 4:45–5:00 |

* **Hard stop at 5:00.** Slide 8 is the last thing said; there is no "and
  finally".
* If over at slide 4, cut slide 5's fault-around clause first (the weakest new
  one), then slide 6's second-host clause. **Never cut slide 7.**
* If the figure on slide 4 is missing, the slide falls back to text — say the two
  numbers and move on. Do not apologise.
* Never read the slide aloud. The deck is sparse on purpose; the words are here.

---

## Question handoff

| Topic | Who |
|---|---|
| What the paper claims | 邹涵锋 |
| Hardware, kernels, driver, `BASE_ITER`, K-best | 邹浩宇 |
| Claim 3, applications, cross-host | 张澄心 |
| Timer, 4.16–4.18, noise, verifiers, traceability | **孙东旭** |
| Anything unmeasured | whoever measured it, or "we did not measure that" |

The last row matters most: **"we did not measure that" is a complete answer.**
