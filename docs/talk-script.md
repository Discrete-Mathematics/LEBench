# Five-minute talk — the script, the timing, and who says what

The deck is `report/slides.tex`: eight slides, five minutes, four speakers. The
`\note{}` fields already carry the time budget; this file turns them into words
you can rehearse.

Compiled by 孙东旭 (5260000073), 19 November 2026.

---

## The shape of the five minutes

| # | Slide | Time | Speaker | The one job of this slide |
|---|---|---|---|---|
| 1 | Title | 0:00–0:10 | 邹涵锋 | Name the paper and the four speakers. Nothing else. |
| 2 | What the paper claims | 0:10–1:00 | 邹涵锋 | Four claims, no numbers, no verdicts. |
| 3 | What actually runs | 1:00–2:00 | 邹浩宇 | The pipeline: guest → one `grub-reboot` → three runs → mean ± stdev. |
| 4 | Across kernels | 2:00–2:25 | 邹浩宇 | Two numbers (43%, 12%) and "not supported". |
| 5 | Two switches | 2:25–2:50 | 邹浩宇 | `nopti` and hugepages, both not supported. |
| 6 | Claim 3 | 2:50–3:30 | 张澄心 | One switch: Apache slower, Nginx faster, Redis flat. |
| 7 | What this guest cannot show | 3:30–4:30 | **孙东旭** | Hardware, missing 3.0 baseline, the clock. Stop at 4:30. |
| 8 | For someone running this CPU | 4:30–5:00 | 邹浩宇 | One sentence and stop. |

**Word budget:** about 140 spoken words per minute. Anything over 720 words for
the whole talk will run long. Slide 7 is 60 s ≈ 150 words; slide 4 is 25 s ≈ 60
words.

---

## Slide 7 — your 60 seconds (孙东旭)

This is the only slide you speak on, and it is the longest single block after
slide 3. Learn it as three beats: hardware, baseline, clock.

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

**Delivery notes**

* Say "pure-CPU loop" slowly — it is the whole argument in three words. If a
  listener remembers one thing from your minute, it should be that sentence.
* Do not say "4.16 to 4.18 look faster, but actually…". Say "look twice as fast",
  then "a kernel cannot do that". The contrast is the point.
* You have 60 seconds and roughly 150 words. If you are past 45 s at "We
  exclude them", drop the last sentence and just say "one machine, one clock".
* Do not look at the audience during the clock sentence; look at the slide. The
  argument is about the slide, not about you.

**If the question comes back to you later** ("so were your numbers wrong?"), the
answer is in `docs/qa-bank.md` Q3 and Q12. The one-liner: *"No — the numbers are
what the machine produced; we removed the boots where the clock itself moved."*

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
number you will see is the mean and the sample standard deviation of three runs.
The K-best rule and the clock are the authors' — `clock_gettime`, five samples
within five per cent. `BASE_ITER` is forty instead of ten thousand, because a
full pass takes hours on this guest."

## Slide 4 — 邹浩宇 (25 s)

"Here is the claim against our logs. Relative to our 4.0.5, two hundred and
seventy-one of six hundred and twenty-seven later measurements have a higher
mean — forty-three per cent. Seventy-six, twelve per cent, are at least fifty per
cent higher. That is not 'most tests, many by half'. Claim one is not supported
on this guest."

## Slide 5 — 邹浩宇 (25 s)

"Two switches, same kernel. `nopti`: getpid is 314 against 295 nanoseconds, the
intervals overlap, and fork moves the wrong way. This CPU is not affected by
Meltdown. Hugepages: `always`, `madvise`, `never` — big munmap is around three
hundred microseconds in all three, intervals overlapping. The closest pair still
overlaps. Neither factor is supported here."

## Slide 6 — 张澄心 (40 s)

"Claim three, one switch. The sysfs line moves from Enhanced IBRS to Vulnerable,
so the switch took effect. Apache goes from 1580 to 1308 requests per second —
slower, intervals disjoint. Nginx goes from 5725 to 7314 — faster, intervals
disjoint. Redis means rise and every interval still overlaps. One switch does not
reproduce eleven causes. Claim three is not supported."

## Slide 8 — 邹浩宇 (30 s)

"On this virtual machine the paper's slowdown and these switches were not
reproduced. This i7 is not affected by Meltdown, so a mitigation that matters on
an older server is not evidence on this hardware. Thank you — questions welcome."

---

## Rehearsal plan (three passes)

| Pass | When | What to do | Target |
|---|---|---|---|
| 1 | two weeks out | Read your own part aloud with a stopwatch, alone | your part within ±5 s |
| 2 | one week out | Full run with all four, slides clicked live, no stopping | total ≤ 5:00 |
| 3 | two days out | Full run in the room, one person in the audience holding a phone timer | total 4:45–5:00 |

Rules that save the talk:

* **A hard stop at 5:00.** Slide 8 is the last thing said; there is no "and
  finally".
* If you are over at slide 4, cut slide 5's third bullet (the closest pair), not
  slide 7 — slide 7 is where the honest limits live.
* If the figure on slide 4 is missing, the slide falls back to text; say the two
  numbers and move on. Do not apologise.
* Never read the slide aloud. The deck is sparse on purpose; the words are here.

---

## Question handoff

| Topic | Who answers |
|---|---|
| What the paper actually claims, page numbers | 邹涵锋 |
| Hardware, kernels, the driver, `BASE_ITER`, K-best | 邹浩宇 |
| Claim 3, applications, macrobenchmark design | 张澄心 |
| The clock, the 4.16–4.18 boots, noise, verifiers, what is traceable | 孙东旭 |
| Anything nobody measured | whoever measured it, or: "we did not measure that" |

The last row matters more than it looks: **"we did not measure that" is a
complete answer.** Guessing loses points that honesty does not.
