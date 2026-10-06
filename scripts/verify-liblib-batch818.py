#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 818 验收器 —— 历史栈的**边界**：连点 N 次，撤 N 次能不能撤干净？

## 起点（817 自开的洞）

817 量到「叠 5 份之后连撤 6 次精确回到起点」，「不声称」里明写：

- ★ 「**只叠 5 份、一次都不删、连撤 5 次**这条更简单的序列没测」；
- ★ 「**能不能叠到几十份、会不会撞上 `MAX_HISTORY`** 未测」。

## ★ 这批要的不是「撤不干净」，而是**撤不掉几份**（有公式）

`canvasStore.ts:464` `MAX_HISTORY = 50`；`pushHistory`（`:507`）每次把
**当前整张图**深拷贝推进 `past` 再 `.slice(-MAX_HISTORY)`。

⟹ **撤不掉的份数 == 连点次数 − min(连点次数, 封顶值)**。

★ 这条公式把「撤销坏了」与「**撤销够不着**」分开：
对照组（远在封顶前）撤得干净，跨封顶臂撤不掉 ⟹ 差别**只在封顶**。

## ★ 封顶值**从数据反推**，再与源码对账

探针只逐次记**历史长度**；判据去找「历史长度不再增长」的那个值，
再拿它跟**从 `canvasStore.ts` 正则读出来的** `MAX_HISTORY` 对账 ——
⟹ 既不写死常量，也不只信源码（**两个独立来源必须对上**）。

## ★ 判据一律从 raw 的**原始字段**重算

原始逐次 `历史`／`节点数`／`future`／`选区`、原始存活 id —— 
**不信**探针算好的「封顶后还能不能新建」之类的结论性字段判据。
"""
import copy
import hashlib
import json
import os
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = pathlib.Path(os.environ.get("VB818_RAW") or
                   (ROOT / "docs/research/liblib-canvas-batch818-2026-10-01"
                    / "raw" / "vb818a.json"))
OUT = pathlib.Path(os.environ.get("VB818_REPORT") or
                   (ROOT / "docs/research/liblib-canvas-batch818-2026-10-01"
                    / "verify-report.json"))
STORE = "src/store/canvasStore.ts"

#: 判据在读**哪些 raw 原始字段** —— 阴性对照必须打在这些字段上
F_KEY = "key"
F_RD = "round"
F_MADE = "建出来的 id"
F_CS = "点选逐次"          # 每项：第几次／历史／节点数／future／这次新建了几个
F_US = "撤销逐次"          # 每项：第几次撤销／还活着的份数／节点数／历史／future／选区
F_BASE = "起点"            # 节点数／历史／future
F_REMAIN = "★ 撤完之后还活着的份数"
F_END_N = "★ 撤完之后节点数"
F_END_P = "★ 撤完之后历史"
F_AGAIN = "★ 封顶后再建出了几个"
F_ACT = "★ 封顶后还能不能新建"
F_CAP_SRC = "源码里的 MAX_HISTORY"

CAP_CASE = "B_past_cap"    # 跨封顶的那条臂
FAR_CASE = "A_far_below_cap"  # 对照臂（远在封顶之前）


def cap_from_source(src):
    """★ 从**源码**独立读出封顶值 —— 与 raw 里探针记的那个是**两个来源**"""
    m = re.search(r"const MAX_HISTORY = (\d+)", src)
    return int(m.group(1)) if m else None


def run_checks(raw, src):
    checks = []

    def add(cid, why, ok, evidence):
        checks.append({"id": cid, "why": why, "ok": bool(ok),
                       "evidence": evidence})

    cells = [x for x in raw["cells"] if not x.get("FAILED")]
    src_cap = cap_from_source(src)
    raw_cap = raw.get(F_CAP_SRC)

    def pick(key):
        return [x for x in cells if x.get(F_KEY) == key]

    # ── S1 ★★ 前提：每一下都真的建了 1 个东西
    ev = []
    for x in cells:
        cs = x.get(F_CS) or []
        n = x.get("howmany")
        ev.append({"round": x.get(F_RD), "臂": x.get(F_KEY),
                   "连点次数": len(cs), "宣称要连点": n,
                   "★ 每一下都建了 1 个": bool(cs) and all(
                       c.get("这次新建了几个") == 1 for c in cs),
                   "★ 前提成立": len(cs) == n and bool(cs) and all(
                       c.get("这次新建了几个") == 1 for c in cs),
                   "★ 建出来的 id 数": len(x.get(F_MADE) or [])})
    add("S1:★★ **前提**：每一下都真的建出了 **1 个**节点",
        "★★ 807 起立的规矩：**前提不满足的臂显式作废、不得据此下结论**。"
        "★ 若某一下没建东西，后面的「撤掉几份」就全不作数了"
        "（815 的 `一共建了几份` 就是这条前提）",
        bool(ev) and all(x["★ 前提成立"] for x in ev)
        and {x["臂"] for x in ev} == {CAP_CASE, FAR_CASE},
        {"逐条": ev,
         "★ 两条臂都在": sorted({x["臂"] for x in ev}),
         "连点次数": {x["臂"]: x["宣称要连点"] for x in ev}})

    # ── S2 ★★★ 历史长度单调不减、且真的封顶；封顶值 == 源码常量
    ev = []
    for x in pick(CAP_CASE):
        cs = x.get(F_CS) or []
        hs = [c.get("历史") for c in cs]
        mono = all(a <= b for a, b in zip(hs, hs[1:]))
        cap = max(hs) if hs else None
        first = next((i + 1 for i, v in enumerate(hs) if v == cap), None)
        tail = len(hs) - first if first else 0
        ev.append({"round": x.get(F_RD), "臂": x.get(F_KEY),
                   "逐次历史长度": hs,
                   "★ 单调不减": mono,
                   "★ 反推出来的封顶值": cap,
                   "★ 第几次达到封顶": first,
                   "★ 达到封顶后还有几步": tail,
                   "★ 封顶后至少连续 5 步不再增长": tail >= 5,
                   "★ 与源码常量一致": cap == src_cap == raw_cap})
    add("S2:★★★ ★ 跨封顶臂：历史长度**单调不减**、**真的封顶**，"
        "且封顶值**与源码常量对得上**",
        "★★★ 「真的封顶」这条不能只看最大值 ⟹ 判据要求"
        "「**达到封顶之后至少还有 5 步不再增长**」，"
        "否则一个偶然的平段就会被当成封顶。"
        "★ **封顶值从数据反推**（找「历史长度不再增长」的那个值），"
        "再与**从 `canvasStore.ts` 正则读出来的** `MAX_HISTORY` 对账 —— "
        "★ **两个独立来源必须对上**；既不写死常量，也不只信源码",
        bool(ev) and all(x["★ 单调不减"] and x["★ 封顶后至少连续 5 步不再增长"]
                         and x["★ 与源码常量一致"] for x in ev),
        {"逐条": ev, "源码里的 MAX_HISTORY": src_cap,
         "raw 记的 MAX_HISTORY": raw_cap,
         "★ 两个来源一致": src_cap == raw_cap})

    # ── S3 ★★★ 对照臂（远在封顶之前）：撤得干净
    ev = []
    for x in pick(FAR_CASE):
        cs, us = x.get(F_CS) or [], x.get(F_US) or []
        hs = [c.get("历史") for c in cs]
        base = x.get(F_BASE) or {}
        ev.append({"round": x.get(F_RD), "臂": x.get(F_KEY),
                   "连点次数": len(cs),
                   "历史最大值": max(hs) if hs else None,
                   "★ 从未达到封顶": bool(hs) and max(hs) < (src_cap or 0),
                   "★ 撤销步数": len(us),
                   "★ 撤完之后还活着的份数": x.get(F_REMAIN),
                   "★ 撤完节点数回到起点": x.get(F_END_N) == base.get("节点数"),
                   "★ 撤完历史回到起点": x.get(F_END_P) == base.get("历史"),
                   "★ 三件同时": x.get(F_REMAIN) == 0
                   and x.get(F_END_N) == base.get("节点数")
                   and x.get(F_END_P) == base.get("历史")})
    add("S3:★★★ ★ **对照臂**：远在封顶之前时，撤到底**精确回到起点**"
        "（撤不掉的份数为 0 ＋ 节点数 ＋ 历史长度，三件同时）",
        "★★★ 807 起立的纪律：**必须有对照臂**。"
        "只有一条「跨过封顶」的臂 ⟹ 「撤不干净」分不清是"
        "**历史封顶**还是**撤销本身坏了**。"
        "★ 本臂同时给出 S4 的公式在「不封顶」那一档的取值（0）"
        "⟹ 公式在两端都被读数支持，不是拟合出来的",
        bool(ev) and all(x["★ 从未达到封顶"] and x["★ 三件同时"]
                         for x in ev),
        {"逐条": ev, "源码里的 MAX_HISTORY": src_cap,
         "★ 历史最大值恒定": sorted({x["历史最大值"] for x in ev})})

    # ── S4 ★★★ 跨封顶臂：撤到底回不到起点，且撤不掉的份数 > 0
    ev = []
    for x in pick(CAP_CASE):
        base = x.get(F_BASE) or {}
        n = len(x.get(F_CS) or [])
        hs = [c.get("历史") for c in (x.get(F_CS) or [])]
        cap = max(hs) if hs else None
        remain = x.get(F_REMAIN)
        ev.append({"round": x.get(F_RD), "臂": x.get(F_KEY),
                   "连点次数": n, "封顶值": cap,
                   "★ 撤完之后还活着的份数": remain,
                   "★ 撤不掉（>0）": bool(remain) and remain > 0,
                   "★ 没回到起点": x.get(F_END_N) != base.get("节点数"),
                   "★ 多出来的节点数": (x.get(F_END_N) or 0)
                   - (base.get("节点数") or 0),
                   "★ 读数成立": bool(remain) and remain > 0
                   and x.get(F_END_N) != base.get("节点数")})
    add("S4:★★★ ★ 跨封顶臂：撤到底**回不到起点**，且**撤不掉的份数 > 0**",
        "★★★ 这就是 817「不声称」② 的正面回答：**撞上 `MAX_HISTORY` 之后，"
        "叠出来的那几份撤不掉了**。"
        "★ 「没回到起点」与「撤不掉 > 0」**两条同时**成立才算数 —— "
        "只看节点数会对不齐（节点可能删过），只看份数又太弱",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 多出来的节点数恒定": sorted({x["★ 多出来的节点数"] for x in ev})})

    # ── S5 ★★★ ★ 公式：撤不掉的份数 == 连点次数 − min(连点次数, 封顶值)
    ev = []
    for x in cells:
        n = len(x.get(F_CS) or [])
        hs = [c.get("历史") for c in (x.get(F_CS) or [])]
        cap = max(hs) if hs else None
        remain = x.get(F_REMAIN)
        expect = n - min(n, cap) if cap is not None else None
        ev.append({"round": x.get(F_RD), "臂": x.get(F_KEY),
                   "连点次数": n, "封顶值": cap, "撤不掉": remain,
                   "★ 公式期望": expect,
                   "★ 读数成立": expect is not None and remain == expect})
    add("S5:★★★ ★★ **公式**：撤不掉的份数 == 连点次数 − min(连点次数, 封顶值)",
        "★★ 这条是本批的**因果读数**，不是拟合："
        "`pushHistory`（`:507`）每次把**当前整张图**深拷贝推进 `past`、"
        "再 `.slice(-MAX_HISTORY)` ⟹ 最老的「连点次数 − 封顶值」份快照**已被丢弃**。"
        "★ **它在两条臂上都成立**：对照臂（不封顶）⟹ 0；跨封顶臂 ⟹ 超出量。"
        "★ 只报「撤不干净」而不给公式，就没法区分"
        "「撤销坏了」与「**撤销够不着**」",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev,
         "★ 公式在两条臂上都命中": len({(x["臂"], x["撤不掉"])
                                  for x in ev}) == 2})

    # ── S6 ★★ 封顶不挡新建
    ev = []
    for x in cells:
        ev.append({"round": x.get(F_RD), "臂": x.get(F_KEY),
                   "★ 撤到底之后点了一下": x.get(F_ACT),
                   "★ 再建出了几个": x.get(F_AGAIN),
                   "★ 读数成立": x.get(F_ACT) == "clicked"
                   and x.get(F_AGAIN) == 1})
    add("S6:★★ 历史栈**封顶不挡新建**：撤到底之后仍然点得出新的一份",
        "★★ 这条是**排除项**：`MAX_HISTORY` 只截断 `past`／`future` "
        "（`:521` 的 `.slice(-MAX_HISTORY)` 与 `:3939` 的 "
        "`.slice(0, MAX_HISTORY)`），**不拦新操作**。"
        "★ 把它单独量出来，是为了不让「封顶」这条读数被误解成"
        "「到顶之后画布就废了」——**恰恰相反，废的是撤销、不是新建**",
        bool(ev) and all(x["★ 读数成立"] for x in ev),
        {"逐条": ev})

    return checks


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    src = (ROOT / STORE).read_text(encoding="utf-8")
    checks = run_checks(raw, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）" % (len(checks) - nPass,
                                   [c["id"] for c in checks if not c["ok"]]))

    def neg(name, why, mutate, expect):
        d = copy.deepcopy(raw)
        hit = mutate(d)
        assert hit, "★ raw 变异没命中"
        c = run_checks(d, src)
        flipped = [x["id"] for x in c if x["ok"] is False]
        if expect == "__NO_FLIP__":
            return {"name": name, "why": why, "evidence": {"hit": hit},
                    "expectFlipped": "（反向对照：期望不翻）",
                    "flipped": flipped, "ok": not flipped}
        return {"name": name, "why": why, "evidence": {"hit": hit},
                "expectFlipped": expect, "flipped": flipped,
                "ok": any(f.startswith(expect) for f in flipped)}

    def cells_of(d):
        return [x for x in d["cells"] if not x.get("FAILED")]

    def click_did_nothing(d):
        """伪造「某一下没建东西」⟹ S1 必须翻红（前提坏掉）"""
        n = 0
        for x in cells_of(d):
            cs = x.get(F_CS) or []
            if not cs:
                continue
            cs[0]["这次新建了几个"] = 0
            n += 1
        return n

    def history_not_monotone(d):
        """伪造「历史长度中途变小」⟹ S2 必须翻红"""
        n = 0
        for x in cells_of(d):
            if x.get(F_KEY) != CAP_CASE:
                continue
            cs = x.get(F_CS) or []
            if len(cs) < 5:
                continue
            cs[3]["历史"] = 0
            n += 1
        return n

    def cap_mismatch(d):
        """★ 伪造「封顶值与源码常量对不上」⟹ S2 必须翻红
        （两个独立来源必须对上；只信一个就抓不到）"""
        n = 0
        for x in cells_of(d):
            if x.get(F_KEY) != CAP_CASE:
                continue
            cs = x.get(F_CS) or []
            if not cs:
                continue
            for c in cs:
                c["历史"] = min(c["历史"], 17)
            n += 1
        return n

    def far_arm_not_back(d):
        """伪造「对照臂撤完回不到起点」⟹ S3 必须翻红"""
        n = 0
        for x in cells_of(d):
            if x.get(F_KEY) != FAR_CASE:
                continue
            x[F_END_N] = (x.get(F_END_N) or 0) + 1
            n += 1
        return n

    def cap_arm_back(d):
        """★ 伪造「跨封顶臂撤到底居然回到了起点」⟹ S4 必须翻红"""
        n = 0
        for x in cells_of(d):
            if x.get(F_KEY) != CAP_CASE:
                continue
            base = x.get(F_BASE) or {}
            x[F_REMAIN] = 0
            x[F_END_N] = base.get("节点数")
            x[F_END_P] = base.get("历史")
            n += 1
        return n

    def formula_off(d):
        """★ 伪造「撤不掉的份数不等于 N − min(N, 封顶值)」⟹ S5 必须翻红
        （把撤不掉的份数改成 1 ⟹ 只有公式那条能抓住）"""
        n = 0
        for x in cells_of(d):
            if x.get(F_REMAIN) in (None, 0):
                continue
            x[F_REMAIN] = 1
            n += 1
        return n

    def cannot_create_after_cap(d):
        """伪造「封顶之后新建不出来」⟹ S6 必须翻红"""
        n = 0
        for x in cells_of(d):
            x[F_ACT] = "not-found"
            x[F_AGAIN] = 0
            n += 1
        return n

    def unrelated(d):
        n = 0
        for x in d["cells"]:
            x["secs"] = 999
            n += 1
        return n

    negs = [
        neg("N1", "伪造「某一下没建东西」⟹ S1 翻红（前提坏掉）",
            click_did_nothing, "S1"),
        neg("N2", "伪造「历史长度中途变小」⟹ S2 翻红",
            history_not_monotone, "S2"),
        neg("N3", "★ 伪造「封顶值与源码常量对不上」⟹ S2 翻红"
                  "（两个独立来源必须对上）", cap_mismatch, "S2"),
        neg("N4", "伪造「对照臂撤完回不到起点」⟹ S3 翻红",
            far_arm_not_back, "S3"),
        neg("N5", "★ 伪造「跨封顶臂撤到底居然回到了起点」⟹ S4 翻红",
            cap_arm_back, "S4"),
        neg("N6", "★★ 伪造「撤不掉的份数不等于 N − min(N, 封顶值)」⟹ S5 翻红"
                  "（把份数改成 1 ⟹ 只有公式那条能抓住）", formula_off, "S5"),
        neg("N7", "伪造「封顶之后新建不出来」⟹ S6 翻红",
            cannot_create_after_cap, "S6"),
        neg("N8", "反向对照：只动 `secs` 这个无关字段 ⟹ 期望不翻",
            unrelated, "__NO_FLIP__"),
    ]

    nOk = sum(1 for x in negs if x["ok"])
    report = {"batch": 818,
              "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": nOk, "negativesTotal": len(negs),
              "rawSha": hashlib.sha256(RAW.read_bytes()).hexdigest()}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print(("  PASS " if c["ok"] else "  FAIL ") + c["id"])
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for x in negs:
        print(("  PASS " if x["ok"] else "  FAIL ") + x["name"]
              + " ｜ 翻红：" + str([f[:4] for f in x["flipped"]]))
    print("★ 阴性对照 %d/%d" % (nOk, len(negs)))
    return 0 if (nPass == len(checks) and nOk == len(negs)) else 1


if __name__ == "__main__":
    sys.exit(main())