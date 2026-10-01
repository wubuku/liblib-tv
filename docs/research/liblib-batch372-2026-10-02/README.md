# Batch 372 — 重复辅助函数的副本漂移普查

日期: 2026-10-02
分支: `master`
产品代码改动: **零**（`src/` / `app/` / `components/` 本批一行未动）
性质: 普查 + 归因，**没有修任何东西**——下面是「为什么这批不下手」的理由。

## 起因

Batch 371 抓到一个具体缺陷: `run-liblib-verifiers.sh` 的「汇总与清单同源」早修好了，
同一份逻辑复制到 `run-frameos-verifiers.sh` 后一直带着 bug。**同一类缺陷隔着一份代码
复制到另一条线，只修了一份，而修复不会自己传播。**

那只是两个 runner。本批要回答的是: 这模式在仓库里到底有多大。

## 量到了什么

`scripts/probe_liblib_batch372_duplicate_drift.py` 扫 656 个脚本，按顶层 `def` 切函数体、
归一化后按 body 哈希分组:

```text
有 2+ 份副本的函数: 149 个，合计 2137 份副本
其中已漂移的函数:     118 个，涉及 2038 份副本
```

| 函数 | 副本 | 变体 | 最大组 | 最大组占比 |
|---|---:|---:|---:|---:|
| `main` | 617 | 584 | 2 | 0.003 |
| `attach_errors` | 343 | 25 | 92 | 0.268 |
| `run_desktop` | 310 | 310 | 1 | 0.003 |
| `assert_no_overflow` | 69 | 5 | 33 | 0.478 |
| `run_mobile` | 61 | 61 | 1 | 0.016 |
| `box` | 49 | 8 | 33 | 0.673 |
| `open_director` | 45 | 42 | 2 | 0.044 |
| `wait_for_app` | 16 | **1** | 16 | **1.0** |
| `center_x` | 14 | **1** | 14 | **1.0** |

> **一份修复要抵达 343 份副本，靠人是不可能完成的。** 这是本批唯一确定的结论。

## 方法的边界（别越读）

- 单位: 顶层 `def` 的函数体; 归一化去空行 / 整行注释 / 行首缩进 / 行尾空白; 比 sha1 前 12 位。
- **这是文本比较，不是行为比较。** 同一哈希**一定**行为等价 → 「完全一致的副本数」这个
  **下界可靠**。不同哈希**未必**行为不同（字面不同但行为等价也算漂移）→ 「漂移数」是
  **上界**。所以 118/2038 是上限，不是「已经有 2038 个 bug」。

## 关键定性: 我推翻了自己一开始的框架

我以为漂移长成「一个标准版 + 一堆落伍副本」。**实际不是。** 看 `attach_errors` 的两大组:

```python
# 92 份（verify-liblib-batch100.py 等，liblib 线）—— 装了 requestfailed
page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
page.on("requestfailed", lambda request: errors.append(
    f"requestfailed:{request.method}:{request.url}:{request.failure}"))
```

```python
# 74 份（verify-frameos-batch157.py 等，frameos 线）—— 根本没装这个监听器
page.on("pageerror", lambda error: errors.append(f"pageerror:{error}"))
return errors
```

第三大组 48 份又不一样（多一个 `dialog` 自动 dismiss）。25 个变体里还有返回 `tuple`
、带 `phase[0]` 阶段标记、过滤 `TransformControls` 噪声、抓 `error.stack` 的版本。

**这些副本本来就不该相同** —— 它们演化去服务不同的门禁。所以真正该问的不是
「哪个是标准版」，而是：**哪些副本在契约上必须一致？** 副本漂移本身**不是**缺陷。
只有契约要求一致却漂移的，才轮到 batch 371 那种处理。

## 顺带把一个长期 TODO 的方向纠正了

挂了很久的待办是「给 `is_dev_server_noise` 补 `WebSocket` / `ERR_CONNECTION_REFUSED`
过滤」。本批的跨线数据说明**这个方向是错的**:

| 线 | 脚本 | 有 `requestfailed` 监听 | 用统一噪声过滤 | import 统一模块 |
|---|---:|---:|---:|---:|
| frameos | 119 | 11 (9.2%) | 11 (9.2%) | 43 (36.1%) |
| liblib | 537 | 181 (33.7%) | 0 (0.0%) | 0 (0.0%) |

1. `scripts/frameos_verify_common.py:85` 的 `is_dev_server_noise` 是**唯一单点定义**，
   但 liblib 线**一次都没 import 过它**（两条线根本不共享这套）。
2. frameos 线里也只有 9.2% 用它——36.1% import 了统一模块，却只有 9.2% 真用上过滤器。
3. 全部 656 个脚本里，提到 `ERR_CONNECTION_REFUSED` 的**只有 1 个**；提到 WebSocket 的 23 个。
4. **而两线的诊断灵敏度差 3.7 倍**：liblib 三分之一的脚本装了 `requestfailed`，
   frameos 只有 9.2%。

所以「frameos 那边看不到连接拒绝」**不是过滤器不够宽，是那个监听器压根没装**。
再加一条 `ERR_CONNECTION_REFUSED` 白名单，一刀切下去恰好会掩盖「服务器真的死了」——
`scripts/verify-frameos-batch351.py` 正是现有过滤的反向测试，它已经用运行时 404
（`/_next/static/chunks/definitely-missing-chunk-abc123._.js`）证真「真故障仍被抓」。

> **换方向**: 不动过滤器，改用 batch 370 已经实现的「runner 能测出 dev server 抖过」
> 这一层能力去限定诊断噪声——先证明是环境抖，再谈某条 console 算不算噪声。

## 复现

```bash
~/.venvs/liblib-harness/bin/python scripts/probe_liblib_batch372_duplicate_drift.py
# → docs/research/liblib-batch372-2026-10-02/duplicate-helper-drift.json
```

产物是**树状态的快照**。实测稳定性: 隔约 10 分钟复跑，5 个汇总数（656 / 149 / 118 /
2137 / 2038）**一字未变**，唯一变化是 `jimeng_unclickable_audit.py` 与
`verify-jimeng-batch841-unclickable.py`（被并行 session 改过）两个 `count: 1` 变体的
digest。**量法对并发编辑是稳的**，变的只是被改文件自己的指纹。

## 留待下一轮

- 挑出**契约上必须一致**的副本组（`attach_errors` 是不是其中之一），再决定动不动手；
- 若要动，方向是**收敛到共享模块**（`frameos_verify_common` 已有单点定义的先例），
  不是逐份去改 343 个文件；
- 跨线诊断覆盖率的差额（9.2% vs 33.7%）值得单独一批量。
