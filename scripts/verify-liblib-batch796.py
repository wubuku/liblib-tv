#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 796 验收器 —— **独立实现**，不 import 汇编器

## 本批的性质：★ **没改 `src/`**，结论是「撤销本来就正确」

796 只做测量。所以验收的重点不是「修复有没有生效」，而是
**「这批读数真的支撑那个结论吗」** ⟹ 阴性对照必须能逐条把结论**打掉**。

- ★ **A（pre≡post）是最容易被糊弄的一条**：没改源码却要求两阶段逐格相同，
  如果断言只比「成员数」这类粗量，A 会永远绿 ⟹ 必须比**含亚像素的完整几何**。
- ★ **B 的判据不能是「撤销后 == 拖动前」**：撤销键没反应时这个也成立
  ⟹ 必须配 E 的阳性对照（造组后立刻撤销 ⟹ 组真的消失）。
- ★ **C 的判据必须双向**：「快照 == 拖动前」不够，还要「快照 **≠** 现值」
  —— 两者相同时反而说明快照被现值覆盖了，那才是污染。
- ★ **F 不能靠源码公式**：贴合值必须由 raw 的成员读数 + `32×2` 独立重算。
- ★ **G 是本批最容易写错的一条**：脏值是**拖拽落点的亚像素**，不是缺陷。
  若把它当缺陷去「修」，就会去改一个浏览器固有行为。⟹ 判据是
  「两阶段逐位相同」（确定性），不是「值不漂亮」。

## 静态层为什么算「独立」

汇编器用正则数源码锚点；本验收器用**块结构**找 `onNodeDragStart` / `onNodeDragStop`
两段并分别判定，并从 raw 重算 Δ ⟹ 两边写错互相抓。
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch796-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb796a-pre.json"
POST = OUTDIR / "raw/vb796a-post.json"
PAGE = "src/app/page.tsx"
CS = "src/store/canvasStore.ts"

ARMS = ["dragThenUndo", "snapshotPurity", "noopDrag", "positiveUndo"]
EPS = 0.01
PADDING = 32


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def bx(m):
    """★ 完整几何（**不取整**）：脏值必须原样参与比较。"""
    g = (m or {}).get("groupStore")
    if not g:
        return None
    return [g["pos"]["x"], g["pos"]["y"], g["w"], g["h"]]


def close(a, b):
    return (a is not None and b is not None
            and len(a) == len(b)
            and all(abs(x - y) <= EPS for x, y in zip(a, b)))


def fit_of(m):
    ms = [x for x in (m or {}).get("members", []) if isinstance(x, dict)]
    if not ms:
        return None
    x0 = min(x["abs"]["x"] for x in ms)
    y0 = min(x["abs"]["y"] for x in ms)
    x1 = max(x["abs"]["x"] + (x.get("w") or 0) for x in ms)
    y1 = max(x["abs"]["y"] + (x.get("h") or 0) for x in ms)
    return [x0 - PADDING, y0 - PADDING, x1 - x0 + PADDING * 2,
            y1 - y0 + PADDING * 2]


def cell_sig(c, undo_key="after"):
    b, a = c.get("before"), c.get(undo_key)
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    return {"box": bx(a), "undoBox": bx(c.get("after")) if undo_key != "after"
            else None,
            "past": [b.get("past"), a.get("past")],
            "snap": bx({"groupStore": a.get("snapGroup")}) if a.get("snapGroup")
            else None}


def block(page, start_re, end_re):
    m = re.search(start_re, page)
    if not m:
        return None
    rest = page[m.end():]
    e = re.search(end_re, rest)
    return rest[:e.start()] if e else rest


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    page = (ROOT / PAGE).read_text(encoding="utf-8")
    cs = (ROOT / CS).read_text(encoding="utf-8")
    pre, post = index(pre_raw), index(post_raw)

    # ── S1：★★ pre ≡ post（比**完整几何**，含亚像素）──
    def sigmap(idx):
        out = {}
        for arm in ARMS:
            out[arm] = []
            for c in idx.get(arm, []):
                s = cell_sig(c, "afterDrag") if arm == "dragThenUndo" \
                    else cell_sig(c)
                out[arm].append(None if not s else [
                    s["box"], s["undoBox"], s["past"], s["snap"]])
        return out

    a1, a2 = sigmap(pre), sigmap(post)
    diff = [arm for arm in ARMS if a1.get(arm) != a2.get(arm)]
    # ★ 退化守卫：确实读到了**带小数**的几何，否则「逐格相同」毫无意义
    has_dirty = any(
        isinstance(x, list) and x and any(
            isinstance(v, float) and abs(v - round(v)) > 1e-9
            for v in (x[0] or []))
        for arm in ARMS for x in a1.get(arm, []))
    add("S1:★★ pre ≡ post（比**含亚像素的完整几何**）",
        "★ 本批没改 `src/` ⟹ 两阶段必须逐格相同；这同时证明读数可复现、"
        "探针不依赖运行状态。★ 必须比完整几何：只比成员数的话这条永远绿",
        not diff and has_dirty,
        {"不同的臂": diff, "读到带小数几何": has_dirty,
         "pre": a1.get("snapshotPurity"), "post": a2.get("snapshotPurity")})

    # ── S2：★★ 撤销臂：框复原 + past 退一格 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("dragThenUndo", []):
            s = cell_sig(c, "afterDrag")
            u = cell_sig(c)
            if not (s and u):
                bad.append({"phase": name, "why": "空读数"})
                continue
            ok = (close(u["box"], bx(c["before"]))
                  and s["past"][1] == s["past"][0] + 1
                  and u["past"][1] == s["past"][1] - 1)
            ev.append({"phase": name, "拖动前": bx(c["before"]),
                       "拖后": s["box"], "撤销后": u["box"],
                       "past": [c["before"]["past"], s["past"][1],
                                u["past"][1]], "ok": ok})
            if not ok:
                bad.append(ev[-1])
    add("S2:★★ 撤销臂：组**与框**复原到拖动前，且 `past` 真退一格",
        "★ 判据是「撤销后 == 拖动前」**且**「历史深度退一格」"
        "（不是「有东西被恢复」就算）",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S3：★★ 快照未被污染（**双向**判据）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("snapshotPurity", []):
            s = cell_sig(c)
            if not s or s["snap"] is None:
                bad.append({"phase": name, "why": "快照缺失"})
                continue
            ok = close(s["snap"], bx(c["before"])) and not close(s["snap"],
                                                                 s["box"])
            ev.append({"phase": name, "快照": s["snap"], "现值": s["box"],
                       "拖动前": bx(c["before"]),
                       "等于拖动前": close(s["snap"], bx(c["before"])),
                       "≠现值": not close(s["snap"], s["box"])})
            if not ok:
                bad.append(ev[-1])
    add("S3:★★ 快照**未被污染**：等于拖动前 **且** ≠ 现值",
        "★ `snapshot.nodes` 是**引用**不是深拷贝 ⟹ 写入原地改它，"
        "撤销就会回到「已被改过」的世界。★ 只判「等于拖动前」不够——"
        "**两者相同时反而说明被现值覆盖了**，那才是污染",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S4：★ 空拖不记历史 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("noopDrag", []):
            s = cell_sig(c)
            if not s:
                bad.append({"phase": name, "why": "空读数"})
                continue
            ok = s["past"][0] == s["past"][1] and close(s["box"], bx(c["before"]))
            ev.append({"phase": name, "past": s["past"], "box": s["box"],
                       "ok": ok})
            if not ok:
                bad.append(ev[-1])
    add("S4:★ 空拖臂：零位移**不记历史**、几何不变",
        "★ `moved` 判据真的看了 `position` ⟹ 无意义的空操作不会填满撤销栈",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S5：★★ 阳性对照：`Cmd+Z` 接上了画布 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("positiveUndo", []):
            b, a = c.get("before"), c.get("after")
            if not isinstance(b, dict) or not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            ok = (bx(b) is not None and bx(a) is None
                  and a.get("past") == b.get("past") - 1)
            ev.append({"phase": name, "before": bx(b), "after": bx(a),
                       "past": [b.get("past"), a.get("past")], "ok": ok})
            if not ok:
                bad.append(ev[-1])
    add("S5:★★ 阳性对照：造组后 `Cmd+Z` ⟹ 组消失、`past` 退一格",
        "★ 没有它，S2 的「复原」可以是「撤销键根本没反应、什么都没变」"
        "——那种情况框也恰好等于拖动前 ⟹ 假绿",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S6：★★ 拖后框 = 独立重算的贴合值 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("snapshotPurity", []):
            a = c.get("after")
            if not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            want, got = fit_of(a), bx(a)
            ev.append({"phase": name, "拖后框": got, "独立重算": want,
                       "相等": close(got, want)})
            if not close(got, want):
                bad.append(ev[-1])
    add("S6:★★ 拖后框**精确等于**按 padding 独立重算的贴合值",
        "★ 用 raw 的成员读数 + `32×2` 重算，**不依赖**源码公式 ⟹ 公式写错也抓得出",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S7：★★ 脏值：两阶段**逐位相同**（确定性），且**不当缺陷** ──
    vals = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm in ("snapshotPurity", "dragThenUndo"):
            for c in idx.get(arm, []):
                for m in (c.get("after"), c.get("afterDrag")):
                    w = (m or {}).get("groupStore", {}).get("w")
                    if isinstance(w, float) and abs(w - round(w)) > 1e-9:
                        vals.append(w)
    uniq = sorted(set(vals))
    add("S7:★★ 脏值两阶段**逐位相同**，且**判为非缺陷**",
        "★ 脏值来自**拖拽落点的亚像素**，框只是忠实跟随 ⟹ 把它当缺陷去「修」"
        "就会去改浏览器固有行为。★ 正判据是「可复现（确定性）」，"
        "不是「值不漂亮」⟹ 顺带证明 793 的 `EPS` no-op 判定稳定",
        len(uniq) == 1 and len(vals) >= 4,
        {"脏值": uniq, "出现次数": len(vals), "判为缺陷": False,
         "理由": "算术自洽：891.34+350-132+64=1173.34"})

    # ── S8：★ 源码侧前提：按**块结构**分别判两段 ──
    start = block(page, r"onNodeDragStart=\{[^}]*?\{",
                  r"onNodeDragStop=\{")
    stop = block(page, r"onNodeDragStop=\{[^}]*?\{", r"nodeTypes=")
    in_start = bool(start) and "currentCanvas.nodes" in start
    in_stop = (bool(stop) and "historySnapshot: transaction.snapshot" in stop
               and "recordHistory: true" in stop)
    moved_ok = bool(stop) and "before.position.x !== after.position.x" in stop
    add("S8:★ 源码侧前提：快照取自拖动前、提交时带上它、`moved` 判位置",
        "★ 用**块结构**分别找 `onNodeDragStart` / `onNodeDragStop` 两段 ⟹ "
        "不会因为两段里各有一个关键词就算「都在同一处」。"
        "★ 依据必须**从源码重读**，不能凭上一批记忆",
        in_start and in_stop and moved_ok,
        {"onNodeDragStart 含 currentCanvas.nodes": in_start,
         "onNodeDragStop 含 historySnapshot+recordHistory": in_stop,
         "onNodeDragStop 的 moved 判位置": moved_ok})

    if audit:
        add("S9:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S9:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)

    add("S10:★ 记账：★ 本批**没改 `src/`**",
        "★ 结论是「撤销本来就正确」⟹ 不许被记成「修好了什么」。"
        "★ 这条把「结论类型」钉住，防止后人误读台账",
        True, {"是否改 src": False, "结论类型": "测量（无缺陷）",
               "被测对象": "onNodeDragStart/onNodeDragStop 的历史快照语义"})
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


def mut_text(path, old, new, label=""):
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    n = orig.count(old)
    assert n == 1, "★ needle 命中 %d 行（须唯一）：%r" % (n, old)
    new_txt = orig.replace(old, new)
    assert len(new_txt.split("\n")) == len(orig.split("\n")), "★ 变异不是行数中性"
    p.write_text(new_txt, encoding="utf-8")
    after = p.read_text(encoding="utf-8")
    ev = {"旧的在": old in after, "新的在": new in after,
          "行数中性": len(after.split("\n")) == len(orig.split("\n")),
          "label": label}
    assert ev["新的在"] and not ev["旧的在"], "★ 变异没真改到目标性质：%r" % ev

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
    pre0, post0 = sha(PRE), sha(POST)
    src0 = {p: sha(ROOT / p) for p in (PAGE, CS)}

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

    # ① ★★ 把 post 的「撤销后」改成「没复原」⟹ S2 必须翻
    def undo_broken():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dragThenUndo":
                        r["after"] = json.loads(json.dumps(r["afterDrag"]))
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N1 ★★ post 的「撤销后复原」被翻成「没复原」",
                    "★ 验证 S2：这是本批的**主结论** ⟹ 必须能被打掉",
                    undo_broken,
                    "S2:★★ 撤销臂：组**与框**复原到拖动前，且 `past` 真退一格"))
    # ② ★★ 把「快照 == 现值」（= 被污染）⟹ S3 必须翻
    def snap_polluted():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "snapshotPurity":
                        r["after"]["snapGroup"] = json.loads(
                            json.dumps(r["after"]["groupStore"]))
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N2 ★★ 快照被改成「等于现值」（= 被污染）",
                    "★ 验证 S3 的**双向**半边：只判「等于拖动前」的话，"
                    "「快照被现值覆盖」这种真污染反而能过",
                    snap_polluted,
                    "S3:★★ 快照**未被污染**：等于拖动前 **且** ≠ 现值"))
    # ③ ★★ 把空拖的 past 翻成「记了历史」⟹ S4 必须翻
    def noop_records():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "noopDrag":
                        r["after"]["past"] = r["before"]["past"] + 1
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N3 ★★ 空拖的 `past` 被翻成「记了历史」",
                    "★ 验证 S4：`moved` 判据若失效（无条件记历史），"
                    "撤销栈会被无意义的空操作填满",
                    noop_records,
                    "S4:★ 空拖臂：零位移**不记历史**、几何不变"))
    # ④ ★★ 阳性对照被翻成「撤销没反应」⟹ S5 必须翻
    def undo_dead():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "positiveUndo":
                        # ★ 翻成「撤销什么都没发生」⟹ 这正是会让 S2 假绿的那种世界
                        r["after"]["groupStore"] = json.loads(
                            json.dumps(r["before"]["groupStore"]))
                        r["after"]["past"] = r["before"]["past"]
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 ★★ 阳性对照被翻成「`Cmd+Z` 没反应」",
                    "★ 验证 S5：若撤销键没反应，S2 的「撤销后 == 拖动前」"
                    "会**恰好成立**（什么都没变）⟹ 那是假绿",
                    undo_dead,
                    "S5:★★ 阳性对照：造组后 `Cmd+Z` ⟹ 组消失、`past` 退一格"))
    # ⑤ ★★ 拖后框被改成「不是贴合值」⟹ S6 必须翻
    def frame_wrong():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "snapshotPurity":
                        r["after"]["groupStore"]["h"] += 9
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 ★★ 拖后框被改成「不是贴合值」",
                    "★ 验证 S6：贴合值由 raw 独立重算 ⟹ 不依赖源码公式",
                    frame_wrong,
                    "S6:★★ 拖后框**精确等于**按 padding 独立重算的贴合值"))
    # ⑥ ★★ 破坏 pre≡post ⟹ S1 必须翻（证明「没改源码」这条被真盯着）
    def break_equiv():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "snapshotPurity":
                        r["after"]["groupStore"]["w"] += 0.5
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N6 ★★ 破坏 pre≡post（给 post 的框宽 +0.5）",
                    "★ 验证 S1：本批没改 `src/` ⟹ 两阶段必须逐格相同。"
                    "★ 若只比成员数，这条会永远绿",
                    break_equiv,
                    "S1:★★ pre ≡ post（比**含亚像素的完整几何**）"))
    # ⑦ ★★ 让脏值变得不可复现 ⟹ S7 必须翻
    def dirty_unstable():
        def go(d):
            n = 0
            for rd in d["rounds"][1:]:
                for r in rd["rows"]:
                    if r.get("arm") in ("snapshotPurity", "dragThenUndo"):
                        for m in (r.get("after"), r.get("afterDrag")):
                            g = (m or {}).get("groupStore")
                            if isinstance(g, dict):
                                g["w"] = g["w"] + 1e-7
                                n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N7 ★★ 让脏值变得**不可复现**",
                    "★ 验证 S7：判据是「两阶段逐位相同」（确定性）⟹ "
                    "打掉这一点就说明这条断言真的在看可复现性",
                    dirty_unstable,
                    "S7:★★ 脏值两阶段**逐位相同**，且**判为非缺陷**"))
    # ⑧ ★★ 把源码里的快照改成取自**拖动后** ⟹ S8 必须翻
    negs.append(neg("N8 ★★ 把 `onNodeDragStart` 的快照来源改掉",
                    "★ 验证 S8：本批结论的机制依据在源码里 ⟹ "
                    "源码被改后这条必须翻，防止结论与代码脱节",
                    lambda: mut_text(PAGE,
                                     "snapshot: { nodes: currentCanvas.nodes, "
                                     "edges: currentCanvas.edges },",
                                     "snapshot: { nodes: currentNodes, "
                                     "edges: currentCanvas.edges },",
                                     label="快照取自拖动后"),
                    "S8:★ 源码侧前提：快照取自拖动前、提交时带上它、`moved` 判位置"))

    restored = {"pre": sha(PRE) == pre0, "post": sha(POST) == post0,
                **{p: sha(ROOT / p) == h for p, h in src0.items()}}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    ok = all(n["ok"] for n in negs)
    out = {
        "batch": 796, "verdict": "PASS" if ok else "FAIL",
        "baseline": {"checks": checks, "passed": nPos,
                     "failed": len(checks) - nPos},
        "negative": negs,
        "negativeSummary": {"total": len(negs),
                            "passed": sum(1 for n in negs if n["ok"])},
        "restoreSha": {"pre": pre0, "post": post0, "src": src0, "ok": restored},
    }
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("★ 796 验收：%d/%d 断言通过" % (nPos, len(checks)))
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
