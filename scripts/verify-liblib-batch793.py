#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 793 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

793 改了 `src/store/canvasStore.ts`，加了 `fitStoryboardGroupsToChildren`
并挂在 `routeReactFlowChanges` 的写点。结论是「分组框跟随成员」。

- ★ **只测「子节点拖出去框跟着走」不够**：一个「凡是拖动就把**所有**组
  都重算一遍」的粗糙实现也能全绿 ⟹ 对照一（拖非成员组不得动）必须独立判（S4）。
- ★ **只测「框动了」也不够**：拖组本身时组**本来就会动** ⟹ 真正的不变量是
  「拖组时**尺寸**不得变、成员要跟着走」⟹ S5。
- ★ 「在不在框里」必须用 **DOM rect** 判定（pre/post 同页同 zoom，zoom 自己约掉），
  不能用 store 坐标反推 ⟹ S3。
- ★ 基线框被归位这件事是**可见变化**，必须由一个**独立重算**的检查兜住
  （用 raw 里的子节点读数 + 32×padding，不依赖源码公式）⟹ S6。
- ★ 两轮一致只能比**行为签名**，不能比像素（拖拽起点是扫描出来的）⟹ S7。
- ★ 源码变异必须能翻掉结论，且**字节级复原**（S11）。

## 静态层为什么算「独立」

汇编器用**行锚定**找四处源码；本验收器用**正则**在整份源码里**自行定位**，
并从 raw 的 before/after **重新推**行为签名 ⟹ 两边写错会互相抓出来。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch793-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb793a-pre.json"
POST = OUTDIR / "raw/vb793a-post.json"

CS = "src/store/canvasStore.ts"
ARMS = ["dragChildOut", "dragNonMember", "dragGroupItself"]
PADDING = 32


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def sig(cell):
    """★ 从 raw 重算「行为签名」；返回 None 表示**空读数**。"""
    b, a = cell.get("before"), cell.get("after")
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    gb, ga = b.get("groupStore"), a.get("groupStore")
    kb = (b.get("kids") or [None])[0]
    ka = (a.get("kids") or [None])[0]
    if not (gb and ga and kb and ka):
        return None
    return {
        "groupMoved": [gb["pos"]["x"], gb["pos"]["y"]]
        != [ga["pos"]["x"], ga["pos"]["y"]],
        "groupSizeChanged": [gb["w"], gb["h"]] != [ga["w"], ga["h"]],
        "childInside": [kb.get("inside"), ka.get("inside")],
        "childMoved": kb.get("abs") != ka.get("abs"),
        "beforeGroup": gb, "beforeKid": kb,
    }


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / CS).read_text(encoding="utf-8")
    pre, post = index(pre_raw), index(post_raw)

    # ── S1：纯函数存在，且挂在**唯一收口**上 ──
    fn_def = re.findall(r"function fitStoryboardGroupsToChildren\(", src)
    fn_call = re.findall(r"nodes: fitStoryboardGroupsToChildren\(", src)
    writer = re.findall(r"nodes: plan\.nextNodes\.map\(withoutStoredNodeSelection\)",
                        src)
    add("S1:纯函数存在，且**替换**了原写点",
        "★ 位置变更落库的唯一收口是 `nodes: plan.nextNodes.map(...)` "
        "（`page.tsx:600` 全部经 `routeReactFlowChanges` 进来）",
        len(fn_def) == 1 and len(fn_call) == 1 and len(writer) == 0,
        {"fnDef": len(fn_def), "fnCall": len(fn_call),
         "旧写点还在": len(writer)})

    # ── S2：★ 两条刻意边界都在源码里 ──
    empty_guard = re.findall(r"if \(kids\.length === 0\) continue;", src)
    eps = re.findall(r"const EPS = 0\.01;", src)
    add("S2:★ 两条刻意边界都在（空组不动 + 容差 no-op）",
        "★ 空组不动 = 757 待拍板 ②（源站未采样）；容差 = 浮点噪声会让"
        "精确相等的 no-op 分支永不成立（实测 414 → 414.00000000000006）",
        len(empty_guard) == 1 and len(eps) == 1,
        {"emptyGuard": len(empty_guard), "eps": len(eps)})

    # ── S3：★★ 处理臂两个方向都要判 ──
    p = [sig(c) for c in pre.get("dragChildOut", [])]
    q = [sig(c) for c in post.get("dragChildOut", [])]
    add("S3:★★ 处理臂：pre 框不动且子节点出框，post 框跟上且子节点在框内",
        "★ `childInside` 来自 **DOM rect** 的包含关系（pre/post 同页同 zoom，"
        "zoom 自己约掉），不是拿 store 坐标反推",
        len(p) == 2 and len(q) == 2
        and all(x and not x["groupMoved"] and x["childInside"] == [True, False]
                for x in p)
        and all(x and x["groupMoved"] and x["childInside"] == [True, True]
                for x in q),
        {"pre": p, "post": q})

    # ── S4：★ 对照一：拖非成员组不得动 ──
    d4 = [sig(c) for c in pre.get("dragNonMember", [])] + \
         [sig(c) for c in post.get("dragNonMember", [])]
    add("S4:★ 对照一：拖非成员，两阶段组都不动",
        "★ 缺了它，一个「凡是拖动就把**所有**组都重算一遍」的粗糙实现"
        "也能让 S3 通过",
        len(d4) == 4
        and all(x and not x["groupMoved"] and not x["groupSizeChanged"]
                and x["childInside"] == [True, True] for x in d4),
        d4)

    # ── S5：★ 对照二：拖组本身尺寸不得变、成员跟着走 ──
    d5 = [sig(c) for c in pre.get("dragGroupItself", [])] + \
         [sig(c) for c in post.get("dragGroupItself", [])]
    add("S5:★ 对照二：拖组本身，尺寸不变、成员跟着走、仍在框内",
        "★ 组「移动」不等于组「重算」⟹ 拖组时成员绝对位置没变，"
        "整段必须是 no-op（否则说明重算在误伤）",
        len(d5) == 4
        and all(x and x["groupMoved"] and not x["groupSizeChanged"]
                and x["childMoved"] and x["childInside"] == [True, True]
                for x in d5),
        d5)

    # ── S6：★★ 基线框归位，且精确等于按 padding **独立重算**的贴合值 ──
    ev, bad6 = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("dragChildOut", []):
            s = sig(c)
            if not s:
                bad6.append({"phase": name, "why": "空读数"})
                continue
            k, g = s["beforeKid"], s["beforeGroup"]
            want = {"x": k["abs"]["x"] - PADDING, "y": k["abs"]["y"] - PADDING,
                    "w": (k.get("w") or 0) + PADDING * 2,
                    "h": (k.get("h") or 0) + PADDING * 2}
            got = {"x": g["pos"]["x"], "y": g["pos"]["y"],
                   "w": g["w"], "h": g["h"]}
            same = got == want
            ev.append({"phase": name, "group": got, "tightFit": want,
                       "equals": same})
            if name == "post" and not same:
                bad6.append(ev[-1])
    add("S6:★★ post 基线框精确等于按 padding 独立重算的贴合值",
        "★ 用 raw 里的子节点读数重算，**不依赖**源码里的公式 ⟹ "
        "公式写错也会被抓出来。★ 种子里 722×460 并不贴合它唯一那个 622×350 的成员",
        not bad6, {"bad": bad6, "evidence": ev})

    # ── S7：★ 两轮一致只比**行为签名** ──
    bad7 = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, lst in idx.items():
            s = [sig(c) for c in lst]
            if len(s) != 2 or s[0] != s[1]:
                bad7.append({"phase": name, "arm": arm, "sigs": s})
    add("S7:★ 两轮的行为签名一致",
        "★ 拖拽起点是扫描出来的、每轮差几个像素 ⟹ 拿像素判「一致」会误报",
        len(bad7) == 0 and len(ev) == 4, {"bad": bad7})

    # ── S8：格数与无 FAILED ──
    bad8 = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad8.append({"phase": name, "arms": sorted(idx)})
        for k, v in idx.items():
            if len(v) != 2:
                bad8.append({"phase": name, "arm": k, "rounds": len(v)})
            if any(c.get("FAILED") or sig(c) is None for c in v):
                bad8.append({"phase": name, "arm": k, "FAILED": "有 FAILED/空读数"})
    add("S8:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 或读数缺失就是**空读数**", not bad8, {"bad": bad8})

    if audit:
        add("S9:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S9:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


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


def mut_src(old, new):
    """行数中性的源码变异（782 立的纪律；R24：必须按子串统计）。"""
    p = ROOT / CS
    orig = p.read_text(encoding="utf-8")
    before = orig.split("\n")
    n = sum(1 for l in before if old in l)
    assert n == 1, "★ needle 命中 %d 行，必须**唯一**一行：%r" % (n, old)
    lines = [l.replace(old, new) for l in before]
    assert len(lines) == len(before), "★ 变异不是行数中性"
    p.write_text("\n".join(lines), encoding="utf-8")
    after = p.read_text(encoding="utf-8").split("\n")
    ev = {"oldGone": not any(old in l for l in after),
          "newThere": any(new in l for l in after)}
    assert ev["oldGone"] and ev["newThere"], \
        "★ 变异没真改到目标性质：%r" % ev

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, ev


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
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

    # ① 把「空组不动」那条拆掉 ⟹ S1/S2 必须翻
    negs.append(neg("N1 「空组不动」的边界被拆掉",
                    "★ 验证 S2：空组处理是 757 待拍板 ② 的边界，"
                    "拆掉它源码侧必须判红（它会把空组也收缩掉）",
                    lambda: mut_src("if (kids.length === 0) continue;",
                                    "if (false) continue;"),
                    "S2:★ 两条刻意边界都在（空组不动 + 容差 no-op）"))
    # ② pre 的「子节点出框」被翻成「在框内」⟹ S3/S7 必须翻
    def pre_inside():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dragChildOut":
                        r["after"]["kids"][0]["inside"] = True
                        n += 1
            return n
        return mut_raw("pre", go)
    negs.append(neg("N2 pre 的「子节点出框」被翻成「在框内」",
                    "★ 验证 S3：「框不动导致子节点出框」这个读数**被真读了**"
                    "（翻平之后 pre 与 post 就没区别，修复等于没发生）",
                    pre_inside,
                    "S3:★★ 处理臂：pre 框不动且子节点出框，post 框跟上且子节点在框内"))
    # ③ post 的「拖非成员」被翻成「组动了」⟹ S4 必须翻
    def nonmember_moves():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dragNonMember":
                        g = r["after"]["groupStore"]
                        g["pos"]["x"] = g["pos"]["x"] + 7
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N3 post 的「拖非成员」被翻成「组动了」",
                    "★ 验证 S4：必须能抓住「凡是拖动就把**所有**组都重算一遍」"
                    "这种粗糙实现",
                    nonmember_moves, "S4:★ 对照一：拖非成员，两阶段组都不动"))
    # ④ post 的「拖组」被翻成「尺寸变了」⟹ S5 必须翻
    def group_resized():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dragGroupItself":
                        r["after"]["groupStore"]["w"] = \
                            r["after"]["groupStore"]["w"] + 5
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 post 的「拖组本身」被翻成「尺寸变了」",
                    "★ 验证 S5：组「移动」不等于组「重算」⟹ 尺寸不变才是真不变量",
                    group_resized,
                    "S5:★ 对照二：拖组本身，尺寸不变、成员跟着走、仍在框内"))
    # ⑤ 源码：把写点接回旧写法（不挂重算）⟹ S1 必须翻
    negs.append(neg("N5 写点接回 `plan.nextNodes.map(...)`（不挂重算）",
                    "★ 验证 S1：修复必须挂在**唯一收口**上；"
                    "只在别处补一个监听或只读一次不算修好",
                    lambda: mut_src(
                        "nodes: fitStoryboardGroupsToChildren(",
                        "nodes: plan.nextNodes.map("),
                    "S1:纯函数存在，且**替换**了原写点"))

    fp_src = (ROOT / CS).read_bytes()
    fp = {p: p.read_bytes() for p in (PRE, POST)}
    drifted = (ROOT / CS).read_bytes() != fp_src
    raw_drift = sorted(p.name for p, b in fp.items() if p.read_bytes() != b)
    checks.append({
        "id": "S10:阴性对照已复原（源码 + raw，字节级）",
        "desc": "★ N1/N5 改过 `src/store/canvasStore.ts` ⟹ 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg, nCaught = len(negs), sum(1 for n in negs if n["ok"])
    REPORT.write_text(json.dumps(
        {"batch": 793, "checks": checks,
         "totals": {"checks": len(checks), "passed": nPos,
                    "failed": len(checks) - nPos},
         "negativeControls": {"total": nNeg, "caught": nCaught,
                              "detail": negs}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== batch 793 验收 ===")
    for c in checks:
        print("  %s %s" % ("OK  " if c["ok"] else "FAIL", c["id"]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-44s flipped=%s"
              % ("OK  " if n["ok"] else "FAIL", n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d" % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
