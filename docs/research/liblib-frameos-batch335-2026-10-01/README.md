# Batch 335（2026-10-01）：全仓验证器「空断言 / 恒真断言」审计

## 结论一句话

Batch 208 证明了**绿色断言可能锁着缺陷**。本批把这条教训推广到全仓：
扫描所有 `scripts/verify-*.py`，找出**恒真**（vacuous）的断言 ——
它们无论功能好坏都会通过，却在账本上显示为「已覆盖」。
**共 5 处，全部修正。**

## 扫描方法

正则匹配恒真模式：

| 模式 | 含义 | 命中 |
|---|---|---|
| `count() >= 0` | 计数不可能为负 | 5（其中 1 处在 frameos221） |
| `... >= 0 or True` | 显式或真，**整条断言失效** | 1（liblib200） |
| `== []` | 断言「空」 | 30+ 处 —— **多数合法**（确实在断言空态） |

`== []` 那一类经抽查全部是「断言某集合确实为空」的真实断言（如
`after_delete["edges"] == []`），**不是**空断言，不动。

## 修正的 5 处

| 文件 | 原断言 | 修正为 | 性质 |
|---|---|---|---|
| `verify-frameos-batch221.py` | `toolbar.count() >= 0` | `== 1`，并补 `node.selected == 1` | 恒真 |
| `verify-liblib-batch200.py` | `... .count() >= 0 or True` | `== 1` | **显式或真，整条死掉** |
| `verify-liblib-batch528.py` | `node.count() >= 0 and is_visible()` | `== 1 and is_visible()` | 恒真 |
| `verify-liblib-batch562.py` | `... .count() >= 0`（or 分支） | `== 1` | 恒真，且是 `or` 短路分支 |
| `verify-liblib-batch586.py` | `gallery.count() >= 0` | `== 1` | 恒真 |

全部修正后复跑：frameos221 13/13 PASS；liblib200/528/562 PASS；
liblib586 18/18 PASS。

## 为什么空断言比「没有断言」更危险

`check("card:selected", X >= 0 or True)` 在覆盖矩阵里显示为
**「card:selected ✅」** —— 读账本的人会认为该行为已被验证。
实际上它对任何实现都通过，包括功能完全损坏的实现。
这比不写断言更糟：不写断言至少在矩阵里是空缺，会引人去补。

## 与 Batch 208 的关系

- **Batch 208**：断言**方向反了**（把「内容丢失」当通过条件）—— 会锁定缺陷；
- **Batch 335**：断言**恒真**（什么都不验证）—— 制造虚假的覆盖感。

两者都是「绿色但无意义」。208 已修正，本批处理恒真这一类。

## 顺延 / 候选

- 源站采样队列仍阻塞（见 `SOURCE_ACCESS_BLOCKED_2026-10-01.md`）。
- 候选 Batch 336：把「恒真断言」检查做成**脚本门禁**
  （类似 `verify-docs.py` 的角色），对 `scripts/verify-*.py` 扫描
  `>= 0` / `or True` 等模式并让 `run-frameos-verifiers.sh` 前置运行，
  避免同类问题再次混入。
