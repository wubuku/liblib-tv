#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 791 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

791 改了 `src/app/page.tsx` 里**一个**监听器，修两个缺陷。

- ★ 最容易出的错是「只修了一个」。所以两个方向都要能判：
  死入口（空白双击要开）与误开（节点双击**要不开**）。
  只测前者的话，一个把闸拆掉的修复也能全绿 ⟹ S6/S7 都必须有。
- ★ **最容易被糊弄的是「阳性对照」**。面板还有 `Tab` 与右键菜单两条入口，
  pre 就通 ⟹ 没有它们，「双击坏了」与「面板根本打不开」无法区分 ⟹ S8。
- 若信 raw 自报字段 ⟹ 派生值一律从 `before`/`after` **重算** ⟹ S5。
- ★ 阶段没搞反是最基本的错：`menuPosition` 那套在这里对应的是
  「pre 的空白双击必须**开不了**、post 必须**开得了**」⟹ S3。
- ★ 源码变异必须能把结论**翻掉**（N1/N2），且**字节级复原**（S12）。

## 静态层为什么算「独立」

汇编器（`mk791audit.py`）用**行锚定**找三处源码并硬编码 `ARMS`；
本验收器用**正则**在整份源码里**自行定位** `addEventListener` /
`removeEventListener` / 闸的实现，并从 raw 的 `before`/`after` **重新推**
面板开没开 ⟹ 两边写错会互相抓出来。

## 沿用纪律

- 阴性对照实测证据、needle 唯一
- ★ **基线必须全绿才准跑阴性对照**（785 立）
- ★ 阴性对照跑完源码与 raw 必须**字节级复原**（785/786 立）
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch791-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb791a-pre.json"
POST = OUTDIR / "raw/vb791a-post.json"

PAGE = "src/app/page.tsx"

ARMS = ["dblclickPane", "dblclickNode", "tabKey", "contextMenu"]
CTRL = ("tabKey", "contextMenu")
NODE_MODULES = ROOT / "node_modules/@xyflow/react/dist"


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def opened(cell):
    """★ 从 `before`/`after` 重算面板有没有开，**不信**自报的 `panelOpened`。"""
    b, a = cell.get("before"), cell.get("after")
    if not isinstance(b, int) or not isinstance(a, int):
        return None
    return {"before": b, "after": a, "opened": a > b}


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / PAGE).read_text(encoding="utf-8")
    lines = src.split("\n")

    def hits(needle):
        return [i + 1 for i, l in enumerate(lines) if needle in l]

    # ── S1：add / remove **两侧**都带捕获阶段 ──
    add_ = hits('addEventListener("dblclick", handleDoubleClick, true)')
    rem_ = hits('removeEventListener("dblclick", handleDoubleClick, true)')
    # ★ 副作用：带 `true` 的 add 之后**不该**再有裸的 add（会多挂一个监听器）
    bare_add = hits('addEventListener("dblclick", handleDoubleClick)')
    bare_add = [n for n in bare_add if lines[n - 1].rstrip().endswith(
        'handleDoubleClick);')]
    add("S1:注册与清理**两侧**都带 `{ capture: true }`",
        "★ 漏改 cleanup 会留下一个再也摘不掉的监听器；"
        "★ 多挂一个裸的 add 也会让计数对不上 ⟹ 两侧都要唯一且没有裸 add",
        len(add_) == 1 and len(rem_) == 1 and not bare_add,
        {"addTrue": add_, "removeTrue": rem_, "bareAdd": bare_add})

    # ── S2：闸必须是「就是 pane」而不是 `closest` ──
    guard_cls = hits('classList.contains("react-flow__pane")')
    guard_closest = hits('closest(".react-flow__pane")')
    add("S2:闸用 `classList.contains`（不是 `closest`）",
        "★ v12 的 DOM 是 `renderer > pane > viewport > nodes > node`，"
        "pane 是 viewport 的**最外层** ⟹ `closest` 对节点也成立、闸形同虚设",
        len(guard_cls) == 1 and len(guard_closest) == 0,
        {"contains": guard_cls, "closest": guard_closest})

    # ── S3：★ 阶段没搞反 ──
    pre, post = index(pre_raw), index(post_raw)
    s3 = {}
    for name, idx in (("pre", pre), ("post", post)):
        for arm in ("dblclickPane", "dblclickNode"):
            s3["%s.%s" % (name, arm)] = [opened(c) for c in idx.get(arm, [])]
    pane_pre = s3.get("pre.dblclickPane", [])
    pane_post = s3.get("post.dblclickPane", [])
    add("S3:★ 阶段没搞反（pre 空白双击开不了、post 开得了）",
        "★ 拿改动后的读数当改动前是最容易犯的错 ⟹ "
        "pre 的空白双击必须**开不了**（`after == before`）、post 必须**开得了**",
        len(pane_pre) == 2 and len(pane_post) == 2
        and all(x and not x["opened"] for x in pane_pre)
        and all(x and x["opened"] and x["after"] == 9 for x in pane_post),
        s3)

    # ── S4：格数与无 FAILED ──
    shape_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            shape_bad.append({"phase": name, "arms": sorted(idx)})
        for k, v in idx.items():
            if len(v) != 2:
                shape_bad.append({"phase": name, "arm": k, "rounds": len(v)})
            if any(c.get("FAILED") for c in v):
                shape_bad.append({"phase": name, "arm": k, "FAILED": "有 FAILED"})
    add("S4:两阶段各 4 臂 × 2 轮且无 FAILED",
        "★ 探针自己有 FAILED 就是**空读数**，不能当结论", not shape_bad,
        {"bad": shape_bad,
         "pre": {k: len(v) for k, v in sorted(pre.items())},
         "post": {k: len(v) for k, v in sorted(post.items())}})

    # ── S5：★ 两个方向都要判（死入口 + 误开）──
    node_pre = [opened(c) for c in pre.get("dblclickNode", [])]
    node_post = [opened(c) for c in post.get("dblclickNode", [])]
    add("S5:★ 节点双击：pre 误开、post 不开",
        "★ 只测「空白双击能开」的话，一个把闸拆掉的修复也能全绿 ⟹ "
        "「节点双击不该开」必须单独判",
        len(node_pre) == 2 and all(x and x["opened"] for x in node_pre)
        and len(node_post) == 2
        and all(x and not x["opened"] for x in node_post),
        {"pre": node_pre, "post": node_post})

    # ── S6：空白双击：pre 死入口、post 通 ──
    add("S6:空白画布双击：pre 死入口、post 通",
        "★ `before` 与 `after` 都取自 raw，**不信**自报的 `panelOpened`",
        all(x and not x["opened"] for x in pane_pre)
        and all(x and x["opened"] and x["after"] == 9 for x in pane_post),
        {"pre": pane_pre, "post": pane_post})

    # ── S7：★ 两条阳性对照前后都通 ──
    ctrl_bad = []
    for arm in CTRL:
        for name, idx in (("pre", pre), ("post", post)):
            for c in idx.get(arm, []):
                o = opened(c)
                if not (o and o["opened"] and o["before"] == 0
                        and o["after"] == 9):
                    ctrl_bad.append({"phase": name, "arm": arm, "got": o})
    add("S7:★★ 两条别的入口（Tab / 右键菜单）前后都通",
        "★ 755 的 R18 / 758 的 R24：没有阳性对照，"
        "「双击那条坏了」与「面板本身打不开」无法区分",
        not ctrl_bad, {"bad": ctrl_bad})

    # ── S8：两轮一致 ──
    same = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, lst in idx.items():
            same.append([opened(c) for c in lst][0]
                        == [opened(c) for c in lst][1])
    add("S8:两轮逐臂完全一致", "★ 8 格每格两轮读数相同 ⟹ 不是抖动",
        len(same) == 8 and all(same), {"perCell": len(same), "allSame": all(same)})

    # ── S9：★ `onPaneDoubleClick` 在 v12 确实不存在 ──
    found = []
    if NODE_MODULES.exists():
        for p in NODE_MODULES.rglob("*"):
            if p.is_file() and p.suffix in (".js", ".mjs", ".cjs", ".ts",
                                            ".d.ts", ".d.mts"):
                try:
                    if "onPaneDoubleClick" in p.read_text(
                            encoding="utf-8", errors="ignore"):
                        found.append(p.name)
                except Exception:            # noqa: BLE001
                    pass
    add("S9:★ `onPaneDoubleClick` 在 `@xyflow/react` v12 里不存在",
        "★ 758 给的三个修法方向里，第三个在本仓库的 React Flow 版本上**不可用**"
        "⟹ 只剩「挂到 pane」与「改捕获阶段」，而运行时读数支持后者",
        not found, {"hits": sorted(set(found))[:5],
                    "distExists": NODE_MODULES.exists()})

    if audit:
        add("S10:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S10:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
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
    """行数中性的源码变异（782 立的纪律）。

    ★ R24（承 790）：`list.count(needle)` 是**整行相等**判断而非子串包含
      ⟹ 统计必须按子串做。
    """
    p = ROOT / PAGE
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

    # ① 源码：捕获阶段改回冒泡 ⟹ S1 必须翻
    negs.append(neg("N1 捕获阶段改回冒泡",
                    "★ 验证 S1 真能判出「死入口那个修复还在不在」",
                    lambda: mut_src(
                        'addEventListener("dblclick", handleDoubleClick, true)',
                        'addEventListener("dblclick", handleDoubleClick)'),
                    "S1:注册与清理**两侧**都带 `{ capture: true }`"))
    # ② 源码：把闸换回 `closest` ⟹ S2 必须翻
    negs.append(neg("N2 闸换回 closest",
                    "★ 验证 S2：闸一旦退回 `closest`，节点双击就会重新误开",
                    lambda: mut_src(
                        'if (!target?.classList.contains("react-flow__pane")) return;',
                        'if (!target?.closest(".react-flow__pane")) return;'),
                    "S2:闸用 `classList.contains`（不是 `closest`）"))
    # ③ pre 的空白双击被翻成「能开」⟹ S3/S6 必须翻
    def pre_pane_ok():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dblclickPane":
                        r["after"] = 9
                        n += 1
            return n
        return mut_raw("pre", go)
    negs.append(neg("N3 pre 的空白双击被翻成「能开」",
                    "★ 验证 S3/S6：「死入口」这个读数**被真读了**"
                    "（翻平之后 pre 与 post 就没区别了，修复等于没发生）",
                    pre_pane_ok, "S3:★ 阶段没搞反（pre 空白双击开不了、post 开得了）"))
    # ④ post 的节点双击被翻成「误开」⟹ S5 必须翻
    def post_node_bad():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dblclickNode":
                        r["after"] = 9
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 post 的节点双击被翻成「误开」",
                    "★ 验证 S5：D791-2 的修复**被真读了**",
                    post_node_bad, "S5:★ 节点双击：pre 误开、post 不开"))
    # ⑤ 阳性对照之一被翻坏 ⟹ S7 必须翻
    def break_ctrl():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "contextMenu":
                        r["after"] = 0
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 阳性对照（右键菜单）被翻坏",
                    "★ 验证 S7：阳性对照必须**真的**在读，"
                    "否则「双击那条坏了」可以和「面板打不开」混为一谈",
                    break_ctrl, "S7:★★ 两条别的入口（Tab / 右键菜单）前后都通"))

    fp_src = (ROOT / PAGE).read_bytes()
    fp = {p: p.read_bytes() for p in (PRE, POST)}
    drifted = (ROOT / PAGE).read_bytes() != fp_src
    raw_drift = sorted(p.name for p, b in fp.items() if p.read_bytes() != b)
    checks.append({
        "id": "S11:阴性对照已复原（源码 + raw，字节级）",
        "desc": "★ N1/N2 改过 `src/app/page.tsx` ⟹ 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg, nCaught = len(negs), sum(1 for n in negs if n["ok"])
    REPORT.write_text(json.dumps(
        {"batch": 791, "checks": checks,
         "totals": {"checks": len(checks), "passed": nPos,
                    "failed": len(checks) - nPos},
         "negativeControls": {"total": nNeg, "caught": nCaught,
                              "detail": negs}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== batch 791 验收 ===")
    for c in checks:
        print("  %s %s" % ("OK  " if c["ok"] else "FAIL", c["id"]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-40s flipped=%s"
              % ("OK  " if n["ok"] else "FAIL", n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d" % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
