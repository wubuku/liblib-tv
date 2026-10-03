#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""方向十一之二的反验注入（Batch 237 新增，用例 42）：**删掉一份「被引用但不是驱动」
的反验的认领行** → 期望报出方向十一之二那条。

**这条为什么必须存在**：方向十一之二（`verify-meta.py`）**在 Batch 212 写下时明确记了
「这条没有自动反验用例」**，理由是「验这个洞需要**两处**改动（新建一份被引用的反验
+ 不登记它），而 `selftest-meta.sh` 的注入机制只能改**一个**文件」。

**那个理由是错的，而且错在一个具体的地方：它只想到了一种验法。**
方向十一之二要抓的是「**非夹具反验没有被认领**」，而**驱动**只是非夹具的一个子集。
现场恰好有 **7 份反验「被别的反验在字符串里提到过、因而不是驱动、但仍是真入口」**
（`selftest-endpoints.py` / `feature-flags` / `label-drift` / `line-counts` /
`meta.sh` / `shot-version` / `tables.sh`）——**它们全都被登记了**，
所以**只要把其中一行的认领删掉，就是一个单文件注入**，
**两处改动的说法不成立**。

**本夹具照用例 33 的做法「现场算」，不写死任何具体文件名**：
从 `verify-meta` 问出当前的「非夹具但非驱动」集合，再挑一行确实认领了其中一份的表行删掉。
**为什么不写死**：那 7 份的「是不是驱动」会随别的反验增删而变
（用例 33 就因为 Batch 198 修好驱动判定而从「作废」变成「失败」——
**写死具体名字的夹具，本批就是它的第二个实例**）。

**断言三道**（少一道都可能空转）：
  1. 现场问出的集合非空；
  2. 被删的那一行**恰好**认领其中一份（不多不少）；
  3. 删完之后表里**确实没有行再认领它**。
"""
import importlib.util
import re
import sys

_spec = importlib.util.spec_from_file_location("vm", "scripts/verify-meta.py")
_vm = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_vm)

_entries = set(_vm.selftest_entries("."))
_drivers = set(_vm.selftest_drivers(".")[0])
#: **方向十一之二的靶子：非夹具、但不是驱动**（被别的反验在字符串里提到过）
_refs = sorted(_entries - _drivers)
assert _refs, ("锚点未命中：现场没有「非夹具但非驱动」的反验了"
               "（非夹具 %d / 驱动 %d）——**这个夹具的前提已失效**，"
               "要么方向十一之二已经不需要这条用例，要么驱动判定变了"
               % (len(_entries), len(_drivers)))

s = sys.stdin.read()
lines = s.split("\n")

idx = [i for i, ln in enumerate(lines)
       if ln.startswith("|") and re.match(r"^\|\s*\d", ln)
       and any(("%s" % r) in ln for r in _refs)]
assert idx, ("锚点未命中：表里没有一行认领了任何一份「非夹具但非驱动」的反验"
             "（这类共 %d 份：%s）" % (len(_refs), "、".join(_refs)))
i = idx[0]
assert lines[i].strip().endswith("|"), "锚点未命中：不是表格行"

_dropped = [r for r in _refs if ("%s" % r) in lines[i]]
assert len(_dropped) == 1, ("被删的那一行应恰好认领 1 份「非驱动」反验，实得 %d：%s"
                            % (len(_dropped), _dropped))
_name = _dropped[0]

out = lines[:i] + lines[i + 1:]


def _claims(rows, name):
    return [r for r in rows if r.startswith("|") and name in r
            and re.match(r"^\|\s*\d", r)]


assert not _claims(out, _name), "空转：表里还有行认领这一份"
#: **不要求这个名字在整个文件里都不许出现**（用例 33 在这里栽过：
#: 慢反验实测耗时那段散文里早就写着这些名字）——**只核表行**。
sys.stdout.write("\n".join(out))
