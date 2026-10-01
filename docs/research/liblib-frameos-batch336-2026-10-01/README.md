# Batch 336（2026-10-01）：断言质量门禁（verify-assertions.py）

## 结论一句话

Batch 335 清掉了 5 处恒真断言，但**没有防复发机制**。本批把这类检查固化成
门禁脚本 `scripts/verify-assertions.py`，并接入 `npm run assertions:check`。
**门禁上线当场又查出 2 处此前漏掉的恒真断言**（batch437 / batch448）。

## 为什么需要门禁

Batch 208（方向反了）和 Batch 335（恒真）都证明：**绿色断言 ≠ 已验证**。
一次性清理只能治存量，治不了增量。人工 review 靠不住 —— 这两批的问题都是在
写测试/写文档时**顺手**留下的，没人会特意去造一个恒真断言。

## 门禁检查项

| 规则 | 匹配 | 说明 |
|---|---|---|
| `VACUOUS_COUNT` | `.count() >= 0` | 计数不可能为负，恒真 |
| `OR_TRUE` | `... or True` | 显式或真，整条断言失效 |
| `COMPARE_TO_NONE` | `x == None` / `x != None` | 应写 `is None`（smell 级） |

**刻意不检查** `== []` —— Batch 335 已确认那 30+ 处都是在真实断言「某集合为空」，
不是空断言。误报比漏报更消耗信任，门禁必须精准。

## 门禁上线即抓出 2 处新问题

这正是门禁的价值 —— 一次性清理总会漏：

| 文件 | 原断言 | 修正为 |
|---|---|---|
| `verify-liblib-batch437.py` | `after_target["nodeCount"] == 0 or True  # canvas-2 has fixture nodes` | `set(before).isdisjoint(after)` —— 断言**节点集合不重叠** |
| `verify-liblib-batch448.py` | `"请选择字幕擦除区域" in generate.get_attribute("title") or True` | 去掉 `or True`，真实断言 |

两处都不是随手写错的：作者当时大概遇到了断言失败，用 `or True`「解决」了 ——
于是那个断言从此再也不会失败，**它要检查的东西变成了无人看管**。
437 那条尤其隐蔽：注释「canvas-2 has fixture nodes」说明了为什么 `count()==0`
不成立，但正确做法是断言**集合不重叠**，而不是放弃断言。

## 门禁有效性自检

不验证门禁本身的门禁等于没有门禁。已做**注入测试**：

```
注入 `.count() >= 0` → Found 1 vacuous assertion(s) ... EXIT=1
还原                  → passed: 0 vacuous assertions in 452 verifier scripts. EXIT=0
```

覆盖 **452 个验证器脚本**。另排除本脚本自身（docstring 里必然引用这些模式，
否则自我误报）。

## 使用

```bash
python3 scripts/verify-assertions.py           # 全量
python3 scripts/verify-assertions.py --quiet   # 只输出结论
npm run assertions:check                      # package.json 入口
```

退出码 0 = 干净，1 = 发现恒真断言。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 337：
  - 把 `assertions:check` 接入 `npm run check` 或 CI（目前只是独立脚本，
    不强制执行 —— 门禁不进流水线等于软性建议）；
  - 扩展规则：目前只查恒真，未查 Batch 208 那类**方向反了**的断言
    （`== nodes_before` 该不该等于操作前），后者需要语义分析，正则难覆盖。
