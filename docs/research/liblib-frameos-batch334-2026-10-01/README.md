# Batch 334（2026-10-01）：持久化落地后的验证器隔离修复（Batch 333 的连带工作）

## 结论一句话

Batch 333 让画布内容**真的**跨刷新持久化（localStorage）后，三个验证器的
「刷新 = 干净起点」假设同时失效 → batch327 刷新后节点重叠、click 被 intercept
而超时失败。新增共享助手 `goto_clean_canvas()`，并让写入方 batch333 结束时清库。

## 这不是 Batch 333 做错了，是它**暴露**了隐藏假设

内容不持久时，「刷新」天然等于「回到 fixture 初值」—— 很多验证器（自己写的、
注释里明写的）都悄悄依赖这一点。一旦持久化变真，这些假设全部失效。

全仓只有 3 个验证器会 reload，但 3 个都中招：

| 验证器 | 失效的假设 | 处理 |
|---|---|---|
| batch327 | reload 后回到初值再测键盘路径 | 改用 `goto_clean_canvas` |
| batch208 | 同上（且本批已修其断言方向） | 改用 `goto_clean_canvas` |
| batch183 | 注释明写「刷新获得干净状态」 | 改用 `goto_clean_canvas` + 更新注释 |
| batch333 | 自己是唯一写入方 | 结束时 `localStorage.clear()` 并复验 |

## 共享助手

`scripts/frameos_verify_common.py` 新增：

```python
def goto_clean_canvas(page, base_url=None) -> None:
    """打开 demo 画布并确保存储为空，使每次验证都从 fixture 初值开始。"""
```

先 `goto` 拿到同源上下文 → 清 `localStorage` → `reload` 让应用以干净状态启动。
放进既有共享模块（该模块本就是 Batch 253 为去重而抽的），而不是每个脚本各写一遍。

## batch333 为什么必须清库

它是全仓**唯一会写入持久化存储**的验证器（它测的就是持久化）。
不清库就会把造出来的节点/分组/连线留给后续所有验证器。
已在结尾加 `localStorage.clear()` + reload 复验，并新增 2 项断言
（`cleanup:storage-wiped` / `cleanup:no-groups-left`）把这条规矩锁住。

## 附带确认：batch327 的失败**不是** id 碰撞回归

batch327 是我修 id 碰撞的那个验证器，它一失败很容易误判成「我的修复坏了」。
实际堆栈显示是 `Locator.click: Timeout 30000ms exceeded`，
`subtree intercepts pointer events` —— **点击被上层节点拦截**，
与 id 唯一性断言无关。判断依据是失败发生在 `page.locator(...).first.click()`
这一步，而不是任何 `check(...)` 断言。

> 教训：验证器失败时先看**失败在哪一步**（断言 vs 交互超时），
> 再判断是功能回归还是测试环境问题。两者修法完全不同。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 335：Batch 333 提出的**「断言方向可能相反」审计** ——
  grep 形如 `== nodes_before` / `== initial` 的断言，逐个核对该等于操作前还是操作后。
  Batch 208 已证明绿色断言可能锁着缺陷，值得全仓扫一遍。
