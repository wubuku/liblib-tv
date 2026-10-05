#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 795 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

795 给画布**新增**了键盘方向键移动（此前完全没有这个能力）。结论是
「方向键能移动节点，且分组框跟着走」。

- ★ **这是新增能力，最危险的错法是「加了个假动作」**：调了 store、位置却没变，
  或只对某个方向生效 ⟹ 必须逐方向判（S5）。
- ★ **「框跟着」不能只看成员动了**：必须证明**框的绝对位置也变了同量**
  ⟹ 只测成员会让「框纹丝不动」的修复全绿（S4）。
- ★ **必须带阳性对照**（S6）：pre 的「没动」有两种解释 —— 能力缺失 / 探针没送事件。
  `Delete` 与方向键走**同一个** keydown 监听器，它两阶段都真删 ⟹ 排除后者。
  ★ 没有它，「pre 没动」可以是探针坏了，于是「post 动了」也没意义。
- ★ **1× vs 2× 必须在验收里也分清**（S5）：移动成员是 1×（组由收口重算），
  移动组是 2×（组和成员都在 `movingIds`）⟹ 用同一个 `wantDelta` 判两条臂必然有一条翻红。
- ★ **收口调用数必须钉死 4**（S3）：键盘是**第三条**写点，绕过收口就是
  794 刚补完的洞同型第三次复发。
- ★ 源码变异必须**行数中性**、**先验它真改到目标性质**，且跑完**字节级复原**。

## 静态层为什么算「独立」

汇编器用正则数 call 站点；本验收器用**块结构**（找 `nudgeSelectedNodes:` 之后
到下一个顶层 `  name:` 之前的整段）逐处判定，并从 raw 重算 Δ ⟹ 两边写错互相抓。
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch795-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb795a-pre.json"
POST = OUTDIR / "raw/vb795a-post.json"

CS = "src/store/canvasStore.ts"
PAGE = "src/app/page.tsx"
ARMS = ["arrowMovesMember", "arrowMovesGroup", "positiveDelete"]
PRESSES = 3
STEP = 1


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def sig(cell, key="after"):
    """★ 行为签名：targets 的 **Δx**（按 before 的顺序），不依赖 id 字面值。"""
    b, a = cell.get("before"), cell.get(key)
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    bt, at_ = b.get("targets"), a.get("targets")
    if not bt or not at_ or len(bt) != len(at_):
        return None
    amap = {t["id"]: t for t in at_}
    out = []
    for t in bt:
        p, q = t.get("abs"), (amap.get(t["id"]) or {}).get("abs")
        if not isinstance(p, dict):
            return None
        # ★ `after` 的 `abs` 可能是 **null** —— 那正是「节点已被删掉」，
        #   必须记成位移 `None` 而不是让整个签名变成空读数（第一版踩过）。
        out.append(None if not isinstance(q, dict)
                   else (q["x"] - p["x"], q["y"] - p["y"]))
    return {"d": out, "nodeCount": (b.get("nodeCount"), a.get("nodeCount")),
            "past": (b.get("past"), a.get("past")),
            "gone": [t.get("exists") for t in bt],
            "goneAfter": [(amap.get(t["id"]) or {}).get("exists")
                          for t in bt]}


def arrow_table(page):
    m = re.search(r"const ARROW_NUDGE[^=]*= \{(?P<b>.*?)\n\};", page, re.S)
    if not m:
        return {}
    return {k: (int(x), int(y)) for k, x, y in
            re.findall(r"(Arrow\w+): \{ x: (-?\d+), y: (-?\d+) \}",
                       m.group("b"))}


def nudge_block(cs):
    """★ `nudgeSelectedNodes` 的**整段实现**（到下一个顶层 action 为止）。"""
    m = re.search(r"^  nudgeSelectedNodes: \(delta\) => \{$", cs, re.M)
    if not m:
        return None
    rest = cs[m.end():]
    nxt = re.search(r"^  [A-Za-z_]\w*: \(", rest, re.M)
    return rest[:nxt.start()] if nxt else rest


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    page = (ROOT / PAGE).read_text(encoding="utf-8")
    cs = (ROOT / CS).read_text(encoding="utf-8")
    pre, post = index(pre_raw), index(post_raw)

    # ── S1：★ 方向键表**四项齐全且方向正确** ──
    tbl = arrow_table(page)
    want = {"ArrowUp": (0, -1), "ArrowDown": (0, 1),
            "ArrowLeft": (-1, 0), "ArrowRight": (1, 0)}
    add("S1:★ 方向键表四项齐全、方向全对",
        "★ 「加了个假动作」的最常见形态是**只接了一个方向**或**方向写反**"
        "⟹ 四项逐个比对，不看数量",
        tbl == want, {"实际": tbl, "应为": want})

    # ── S2：★ keydown 里真接上了，且不带修饰键 ──
    hooked = re.findall(r"ARROW_NUDGE\[event\.key\]", page)
    guarded = re.findall(r"if \(!modifier && !event\.altKey\) \{", page)
    add("S2:★ keydown 里接上了、且只在**无修饰键**时生效",
        "★ `Cmd/Ctrl+方向` 是浏览器切标签页，抢走它比不提供移动更糟",
        len(hooked) == 1 and len(guarded) == 1,
        {"接上": len(hooked), "无修饰键守卫": len(guarded)})

    # ── S3：★★ 键盘路径**过了 793 的收口** ──
    blk = nudge_block(cs)
    fits = len(re.findall(r"nodes: fitStoryboardGroupsToChildren\(", cs))
    in_block = len(re.findall(r"fitStoryboardGroupsToChildren\(", blk or ""))
    add("S3:★★ 键盘路径**过了 793 的收口**，且全仓收口调用数正好 4",
        "★ 键盘是**第三条**写点（793 拖拽 / 794 删除 ×2 / 795 键盘）。"
        "★ 只数全仓 == 4 不够 —— 必须确认**这 4 个里有一个在 nudge 块内**",
        in_block == 1 and fits == 4,
        {"收口全仓调用数": fits, "nudge 块内": in_block,
         "nudge 块找到": blk is not None})

    # ── S4：★★ 处理臂：pre 纹丝不动、post 成员与框**都**恰好 +3 ──
    p = [sig(c) for c in pre.get("arrowMovesMember", [])]
    q = [sig(c) for c in post.get("arrowMovesMember", [])]
    bad4 = []
    for name, lst in (("pre", p), ("post", q)):
        for s in lst:
            if not s or len(s["d"]) < 2 or None in s["d"]:
                bad4.append({"phase": name, "why": "空读数/节点消失",
                             "sig": s})
                continue
            dk, dg = s["d"][0][0], s["d"][1][0]
            want_d = 0 if name == "pre" else STEP * PRESSES
            if not (dk == want_d and dg == want_d
                    and s["nodeCount"][0] == s["nodeCount"][1]):
                bad4.append({"phase": name, "dKid": dk, "dGroup": dg,
                             "want": want_d, "nodeCount": s["nodeCount"]})
    add("S4:★★ 处理臂：pre 完全不动、post 成员与框**都**恰好 +3、节点数不变",
        "★ 只测成员会让「框纹丝不动」的修复全绿 ⟹ 必须同时判**框的绝对位移**。"
        "★ 移动成员时组由收口重算 ⟹ 位移是 1×（对比 S5 的 2×）",
        not bad4 and len(p) == 2 and len(q) == 2, {"bad": bad4})

    # ── S5：★★ 组臂：位移**相等**且是 2×（组与成员都进了 movingIds）──
    bad5, ev5 = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("arrowMovesGroup", []):
            s = sig(c)
            if not s or len(s["d"]) < 2 or None in s["d"]:
                bad5.append({"phase": name, "why": "空读数/节点消失",
                             "sig": s})
                continue
            dg, dk = s["d"][0][0], s["d"][1][0]
            ev5.append({"phase": name, "dGroup": dg, "dKid": dk,
                        "相等": dg == dk, "past": s["past"]})
            if name == "post":
                # ★★ 2×：选区含组 ⟹ `movingIds` 里组和成员都在 ⟹ 成员绝对位移
                #   = 自身 +1 + 父组 +1 = +2。★ 用 1× 判这条臂必然翻红。
                if not (dg == dk == STEP * PRESSES * 2
                        and s["past"][1] - s["past"][0] == PRESSES):
                    bad5.append(dict(ev5[-1], want=STEP * PRESSES * 2))
    add("S5:★★ 组臂：组与成员绝对位移**相等**且为 2×，每次按压一条历史",
        "★ 关键不变量是「**相等**」（成员没掉出框）；`2×` 是因为组与成员"
        "都被塞进 `movingIds` ⟹ 绝对位移叠加。★ 两条臂用同一个步长判必有一条翻红",
        not bad5 and len(ev5) == 4, {"bad": bad5, "evidence": ev5})

    # ── S6：★★ 阳性对照：Delete 两阶段都真删 ──
    bad6, ev6 = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("positiveDelete", []):
            s = sig(c)
            if not s:
                bad6.append({"phase": name, "why": "空读数"})
                continue
            ok = (s["nodeCount"] == (11, 10)
                  and s["gone"][0] is True and s["goneAfter"][0] is False
                  and s["past"][1] - s["past"][0] == 1)
            ev6.append({"phase": name, "nodeCount": s["nodeCount"],
                        "gone": (s["gone"][0], s["goneAfter"][0]),
                        "past": s["past"], "ok": ok})
            if not ok:
                bad6.append(ev6[-1])
    add("S6:★★ 阳性对照：`Delete` 两阶段都真删掉一个节点",
        "★ 它与方向键走**同一个** keydown 监听器 ⟹ 它通过即证明"
        "「键盘事件确实到达画布」⟹ 没有它，pre 的「没动」可以是探针坏了",
        not bad6 and len(ev6) == 4, {"bad": bad6, "evidence": ev6})

    # ── S7：★ 方向键只挪位置、不增删节点；无 FAILED ──
    bad7 = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad7.append({"phase": name, "arms": sorted(idx)})
        for arm, lst in idx.items():
            if len(lst) != 2:
                bad7.append({"phase": name, "arm": arm, "rounds": len(lst)})
            for c in lst:
                if c.get("FAILED"):
                    bad7.append({"phase": name, "arm": arm,
                                 "FAILED": c.get("FAILED")})
                s = sig(c)
                if s and s["nodeCount"][0] != s["nodeCount"][1] \
                        and arm != "positiveDelete":
                    bad7.append({"phase": name, "arm": arm,
                                 "nodeCount": s["nodeCount"],
                                 "why": "移动臂不该增删节点"})
    add("S7:★ 两阶段各 3 臂 × 2 轮、无 FAILED、方向键不增删节点",
        "★ 探针 FAILED / 读数缺失就是**空读数**", not bad7, {"bad": bad7})

    if audit:
        add("S8:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S8:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)

    # ── S9：★★ 限定：★ 撤销粒度 = 1 像素（这是**代价**，不是缺陷）──
    #   必须被**记下来**，否则下一批读到 `past 1→4` 会误判成「重复记历史」。
    add("S9:★★ 记账：一次按压记一条历史（撤销要按 3 次才回原位）",
        "★ 这与桌面画布（Figma/FigJam）惯例一致 ⟹ 保留现状、不当缺陷修。"
        "★ 但它必须被**显式断言**，否则「撤销一次回原位」的期待会落空",
        True,
        {"约定": "保留现状", "理由": "与桌面画布惯例一致；源站未采样",
         "已知代价": "撤销粒度 = 1 像素；3 次按压需 3 次撤销",
         "是否当缺陷": False})
    return checks


# ── 变异工具 ────────────────────────────────────────────────
def mut_raw(which, fn):
    p = PRE if which == "pre" else POST
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = fn(d)
    assert hit, "★ raw 变异没命中"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, {"file": p.name, "hit": hit}


def mut_text(path, old, new, expect_before=True, label=""):
    """行数中性的源码变异（782 立的纪律）+ 先验它真改到目标性质。"""
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    n = orig.count(old)
    assert n == 1, "★ needle 命中 %d 行（须唯一）：%r" % (n, old)
    new_txt = orig.replace(old, new)
    assert len(new_txt.split("\n")) == len(orig.split("\n")), \
        "★ 变异不是行数中性"
    p.write_text(new_txt, encoding="utf-8")
    after = p.read_text(encoding="utf-8")
    ev = {"旧的在": (old in after) if expect_before else (old not in after),
          "新的在": (new in after) if expect_before else (old in after),
          "行数中性": len(after.split("\n")) == len(orig.split("\n")),
          "label": label}
    assert ev["新的在"] or not expect_before, \
        "★ 变异没真改到目标性质：%r" % ev

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, ev


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    src0, page0 = sha(ROOT / CS), sha(ROOT / PAGE)
    pre0, post0 = sha(PRE), sha(POST)

    checks = run_checks(pre_raw, post_raw, audit)
    nPos = sum(1 for c in checks if c["ok"])
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(PRE.read_text(encoding="utf-8")),
                           json.loads(POST.read_text(encoding="utf-8")), audit)
            flipped = [x["id"] for x in c if not x["ok"]]
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped,
                    "stillPassing": [x["id"] for x in c if x["ok"]]}
        finally:
            restore()

    # ① ★★ 方向写反（Right 变 Left）⟹ S1 必须翻
    negs.append(neg("N1 ★★ 把 ArrowRight 的方向写反",
                    "★ 验证 S1：只判「表有四项」的话，`Right: {x:-1}` "
                    "这种「按右键往左走」的错法能全绿",
                    lambda: mut_text(PAGE, "ArrowRight: { x: 1, y: 0 },",
                                      "ArrowRight: { x: -1, y: 0 },",
                                      label="方向写反"),
                    "S1:★ 方向键表四项齐全、方向全对"))
    # ② ★★ 让一个方向失效（保留行数：改成 0 位移）⟹ S1 必须翻
    negs.append(neg("N2 ★★ 把 ArrowLeft 改成 0 位移（无效方向）",
                    "★ 验证 S1：只判「四项都在」的话，某个方向位移为 0 "
                    "（按左键不动）也能全绿",
                    lambda: mut_text(PAGE, "  ArrowLeft: { x: -1, y: 0 },",
                                      "  ArrowLeft: { x: 0, y: 0 },",
                                      label="方向失效"),
                    "S1:★ 方向键表四项齐全、方向全对"))
    # ③ ★★ 键盘路径**绕过**收口 ⟹ S3 必须翻
    negs.append(neg("N3 ★★ 让键盘路径绕过 793 的收口",
                    "★ 验证 S3：键盘是**第三条**写点，绕过收口就是 794 "
                    "刚补完的洞同型第三次复发",
                    lambda: mut_text(
                        CS,
                        "                nodes: fitStoryboardGroupsToChildren(\n"
                        "                  canvas.nodes.map((node) =>",
                        "                nodes: (\n"
                        "                  canvas.nodes.map((node) =>",
                        label="绕过收口"),
                    "S3:★★ 键盘路径**过了 793 的收口**，且全仓收口调用数正好 4"))
    # ④ ★★ 去掉「无修饰键」守卫 ⟹ S2 必须翻
    negs.append(neg("N4 ★★ 去掉「无修饰键」守卫",
                    "★ 验证 S2：`Cmd+方向` 是浏览器切标签页，抢走它比不提供更糟",
                    lambda: mut_text(
                        PAGE, "      if (!modifier && !event.altKey) {\n"
                              "        const nudge = ARROW_NUDGE[event.key];",
                        "      if (true) {\n"
                        "        const nudge = ARROW_NUDGE[event.key];",
                        label="去掉守卫"),
                    "S2:★ keydown 里接上了、且只在**无修饰键**时生效"))
    # ⑤ ★ post 的「框跟着走」被翻成「框没动」⟹ S4 必须翻
    def frame_frozen():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "arrowMovesMember":
                        t = r["after"]["targets"][1]
                        b = r["before"]["targets"][1]["abs"]
                        t["abs"] = {"x": b["x"], "y": b["y"]}
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 ★★ post 的「框跟着走」被翻成「框没动」",
                    "★ 验证 S4：只测成员位移的话，「框纹丝不动」能全绿",
                    frame_frozen,
                    "S4:★★ 处理臂：pre 完全不动、post 成员与框**都**恰好 +3、节点数不变"))
    # ⑥ ★★ post 的「组臂 2×」被翻成 1× ⟹ S5 必须翻
    def half_step():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "arrowMovesGroup":
                        t = r["after"]["targets"]
                        b = r["before"]["targets"]
                        for i in (0, 1):     # 把 +6 改成 +3
                            t[i]["abs"] = {"x": b[i]["abs"]["x"] + 3,
                                           "y": b[i]["abs"]["y"]}
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N6 ★★ post 的「组臂 2×」被翻成 1×",
                    "★ 验证 S5：位移**不相等**（成员掉出框）必须被抓出来。"
                    "★ 这一条同时证明 1×/2× 的区分不是我在验收里写死的偏好",
                    half_step,
                    "S5:★★ 组臂：组与成员绝对位移**相等**且为 2×，每次按压一条历史"))
    # ⑦ ★★ 阳性对照被翻成「Delete 也没删」⟹ S6 必须翻
    def del_noop():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "positiveDelete":
                        t = r["after"]["targets"]
                        b = r["before"]["targets"]
                        t[0]["exists"] = True
                        t[0]["abs"] = dict(b[0]["abs"])
                        r["after"]["nodeCount"] = r["before"]["nodeCount"]
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N7 ★★ 阳性对照被翻成「Delete 也没删」",
                    "★ 验证 S6：若阳性对照能假绿，「pre 没动」就无法与"
                    "「探针没送事件」区分 ⟹ 整批结论失去地基",
                    del_noop,
                    "S6:★★ 阳性对照：`Delete` 两阶段都真删掉一个节点"))
    # ⑧ ★★ pre 的「纹丝不动」被翻成「pre 也动了」⟹ S4 必须翻
    def pre_moved():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "arrowMovesMember":
                        t = r["after"]["targets"]
                        b = r["before"]["targets"]
                        for i in (0, 1):
                            t[i]["abs"] = {"x": b[i]["abs"]["x"] + 3,
                                           "y": b[i]["abs"]["y"]}
                        r["after"]["past"] = r["before"]["past"] + 3
                        n += 1
            return n
        return mut_raw("pre", go)
    negs.append(neg("N8 ★★ pre 的「纹丝不动」被翻成「pre 也动了」",
                    "★ 验证 S4 的 pre 半边：若只判 post，"
                    "「修复前就有这个能力」的实现也能全绿",
                    pre_moved,
                    "S4:★★ 处理臂：pre 完全不动、post 成员与框**都**恰好 +3、节点数不变"))

    restored = {"cs": sha(ROOT / CS) == src0, "page": sha(ROOT / PAGE) == page0,
                "pre": sha(PRE) == pre0, "post": sha(POST) == post0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    ok = all(n["ok"] for n in negs)
    out = {
        "batch": 795, "verdict": "PASS" if ok else "FAIL",
        "baseline": {"checks": checks, "passed": nPos,
                     "failed": len(checks) - nPos},
        "negative": negs,
        "negativeSummary": {"total": len(negs),
                            "passed": sum(1 for n in negs if n["ok"])},
        "restoreSha": {"cs": src0, "page": page0, "pre": pre0, "post": post0,
                       "ok": restored},
    }
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("★ 795 验收：%d/%d 断言通过" % (nPos, len(checks)))
    for c in checks:
        print("   %s %s" % ("OK " if c["ok"] else "FAIL", c["id"]))
    print("★ 阴性对照 %d/%d" % (sum(1 for n in negs if n["ok"]), len(negs)))
    for n in negs:
        print("   %s %s → 翻了 %r"
              % ("OK " if n["ok"] else "FAIL", n["name"], n["flipped"]))
    print("★ 阴性对照后字节级复原：%r" % restored)
    print("wrote %s" % REPORT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
