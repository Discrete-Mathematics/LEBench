# Claims Under Test — SOSP'19 "An Analysis of Performance Evolution of Linux's Core Operations"

> 课程要求：*One to three claims, each linked to a table or figure in the paper.*
> 每条 claim 都必须能对应论文里的一张图/表，并且能用仓库 `results/` 里的日志判定
> `supported` / `partially supported` / `not supported` / `inconclusive`。

| # | Claim（待验证的论断） | 论文出处 | 论文给出的数字 |
|---|---|---|---|
| C1 | 内核页表隔离（KPTI，Meltdown 缓解）显著拖慢核心系统调用；关闭它后延迟明显下降 | Fig. 2、§4.1.1 | 微基准平均 +22%；`recv` 63%、`read` 59%；常数开销 400–500 cycles |
| C2 | 间接跳转推测的规避（Retpoline，Spectre v2 缓解）使 `select`/`poll`/`epoll` 显著变慢；改为直接分支可大幅消除 | Fig. 2、§4.1.2 | `select` 68%、`poll` 89%、`epoll` 72%（平均 66%）；改 `switch` 后降到 5.7% / 2.5% |
| C3 | 关闭上述根因后，真实应用吞吐显著提升 | Fig. 8、§5 | Redis 最高 +56%、Apache +33%、Nginx +34% |

---

## 判定规则（写报告时照这个填）

- **supported**：我们的方向与量级都和论文一致（例如慢 50% 以上 vs 论文 68%）。
- **partially supported**：方向一致，但量级明显偏小（例如只有 10%–20%）。
- **not supported**：方向相反或量级差一个数量级。
- **inconclusive**：结果在噪声范围内，或环境条件无法保证（如 guest 中 mitigation 是否真正启用无法确认）。

---

## C1 的实施细节

- 方法：同一 guest、同一 LEBench 版本、同一 CPU 绑定；
  对比启动参数 `pti=off` 与默认（`pti=on`）。
- 必采证据：
  - `dmesg | grep -i "page tables isolation"`（确认是否真的启用/关闭）
  - `cat /sys/devices/system/cpu/vulnerabilities/meltdown`
  - `uname -a`、`lscpu`
- 测试集：`big-select`、`small-read`、`small-recv`（与论文对比口径一致）
- 重复：≥3 次运行，报告 mean ± std，同时记录 k-best（最慢 5 个且相邻差 ≤5%）

## C2 的实施细节

- 方法：对比 `spectre_v2=off` 与默认（retpoline）。
- 必采证据：`cat /sys/devices/system/cpu/vulnerabilities/spectre_v2`、`dmesg | grep -i retpoline`
- 测试集：`big-select`、`big-poll`、`big-epoll`
- 加分项：按论文 §4.1.2 的思路把一处间接调用改成 `switch`，观察降幅

## C3 的实施细节

- 方法：`redis-benchmark`（RPUSH / GET / LRANGE），50 并发、100,000 请求
- 对比：mitigation 全开 vs 全关（`pti=off spectre_v2=off`）
- 记录：吞吐（ops/sec）与 p99 延迟

---

## 当前状态（每次跑完更新）

| Claim | 已跑测试 | 运行次数 | 日志路径 | 初步判定 |
|---|---|---|---|---|
| C1 | TODO | 0 | TODO | inconclusive |
| C2 | TODO | 0 | TODO | inconclusive |
| C3 | TODO | 0 | TODO | inconclusive |
