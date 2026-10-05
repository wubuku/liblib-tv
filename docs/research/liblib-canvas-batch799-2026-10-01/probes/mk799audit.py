#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 799 汇编器 —— 嵌套分组：`fitStoryboardGroupsToChildren` 的写回坐标系

## 判据：两条**与坐标系语义无关**的客观不变量

`position` 到底该写绝对还是相对，是**实现细节**。所以判据不去猜实现，
只判**用户看得见的绝对几何**：

★ 不变量 A（793 的核心承诺）：每个**有父组**的节点，它的**绝对**位置必须落在
  父组的**绝对**框内。（对**子组**同样成立 —— 内层组也是外层的子节点。）

★ 不变量 B（贴合）：每个**有直接子节点**的组，其**绝对**框 =
  直接子节点绝对包围盒 ⊕ `GROUP_PADDING`。

★ 两条都用绝对坐标表述 ⟹ 不预设 `position` 语义 ⟹ 改对改错都判得出来。

## 「多趟」不是实现细节，是被 raw 记录的事实

`dbg799diag.py` 实测：注入后同一 tick 内读是 `w=10`（`setNodes` 同步态），
30ms 后已贴合 ⟹ fit 在此期间跑过；而且 fit 会改 `style.width` ⟹ DOM 重排
⟹ react-flow 再量 ⟹ `onNodesChange` ⟹ `routeReactFlowChanges` 再跑一次
（`canvasStore.ts:3819`）⟹ **正反馈**。

⟹ 所以「注入后」读到的状态 = **跑到不动点**的状态，不是单趟。
本汇编器的独立重算因此照此模拟，并要求与 raw **逐位吻合**。

## 独立重算

`_sim_fit` 是本文件自己写的 fit 模拟（相对化 + 先外后内 + 多趟到不动点），
**不 import 任何 `src/` 代码**，只吃 raw 里的 `position/parentId/width/height`。
要求：`_sim_fit` 的输出与 raw 读数**逐位相同** ⟹ 模拟复刻了实现。
"""
import copy
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
RAW_PRE = ROOT / "raw" / "vb799a-pre.json"
RAW_POST = ROOT / "raw" / "vb799a-post.json"
OUT = ROOT / "audit-799.json"

EPS = 0.01
NEAR = lambda a, b: abs(a - b) <= EPS   # noqa: E731

#: ★ 候选 padding（不写死 40 —— 让它变成被验证出来的量，见 P1）
PAD_CANDIDATES = (0, 4, 8, 10, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 56, 64)

SRC_FIT = "src/store/canvasStore.ts:fitStoryboardGroupsToChildren"


# ---------------------------------------------------------------- 独立重算
def _abs(nodes, node):
    """沿 `parentId` 链求和（与 `getAbsoluteNodePosition` 同语义）。"""
    by_id = {n["id"]: n for n in nodes}
    x, y = node["position"]["x"], node["position"]["y"]
    pid, seen, d = node.get("parentId"), {node["id"]}, 0
    while pid and pid not in seen:
        seen.add(pid)
        d += 1
        parent = by_id.get(pid)
        if parent is None:
            break
        x += parent["position"]["x"]
        y += parent["position"]["y"]
        pid = parent.get("parentId")
    return x, y


def _sim_pass(nodes, pad, relativize=True):
    """单趟：顺序 = **先外后内**（depth 升序），每组用**当前**状态重算绝对位置。

    ★ `relativize=False` 复刻 **799 之前**的写法：把绝对坐标原样写进 `position`。
    有了这个开关，同一个模拟器就能**同时**解释修复前后的读数 ——
    否则「模拟吻合实测」只能证明模拟很橡皮章。
    """
    out = copy.deepcopy(nodes)
    by_id = {n["id"]: n for n in out}

    def depth(n):
        d, pid, seen = 0, n.get("parentId"), {n["id"]}
        while pid and pid not in seen:
            seen.add(pid)
            d += 1
            n = by_id.get(pid) or {}
            pid = n.get("parentId")
        return d

    groups = sorted((n for n in out
                     if n["type"] == "storyboard-group"),
                    key=depth)
    changed_any = False
    for g in groups:
        kids = [n for n in out if n.get("parentId") == g["id"]]
        if not kids:
            continue                                   # 边界 1：空组不动
        abs_pos = {k["id"]: _abs(out, k) for k in kids}
        min_x = min(abs_pos[k["id"]][0] for k in kids)
        min_y = min(abs_pos[k["id"]][1] for k in kids)
        max_x = max(abs_pos[k["id"]][0] + (k.get("w") or 350) for k in kids)
        max_y = max(abs_pos[k["id"]][1] + (k.get("h") or 180) for k in kids)
        # ★★ 799 修复：组的 `position` 是**相对直接父节点**
        pid = g.get("parentId")
        pabs = _abs(out, by_id[pid]) if pid in by_id else (0, 0)
        new_abs = (min_x - pad, min_y - pad)
        new_rel = ((new_abs[0] - pabs[0], new_abs[1] - pabs[1])
                   if relativize else new_abs)
        w = max_x - min_x + pad * 2
        h = max_y - min_y + pad * 2
        if (NEAR(g["position"]["x"], new_rel[0]) and NEAR(g["position"]["y"], new_rel[1])
                and NEAR(g.get("w"), w) and NEAR(g.get("h"), h)):
            continue                                   # 已经贴合 ⟹ no-op
        changed_any = True
        for n in out:
            if n["id"] == g["id"]:
                n["position"] = {"x": new_rel[0], "y": new_rel[1]}
                n["w"], n["h"] = w, h
            elif n.get("parentId") == g["id"]:
                a = abs_pos[n["id"]]
                n["position"] = {"x": a[0] - new_abs[0], "y": a[1] - new_abs[1]}
        by_id = {n["id"]: n for n in out}
    return out, changed_any


def _sim_settle(nodes, pad, relativize=True, max_passes=16):
    """跑到不动点（模拟 `routeReactFlowChanges` 的 `dimensions` 反馈）。"""
    cur = copy.deepcopy(nodes)
    passes = 0
    for _ in range(max_passes):
        cur, changed = _sim_pass(cur, pad, relativize)
        passes += 1
        if not changed:
            break
    return cur, passes


def _sim_n(nodes, pad, n, relativize=True):
    """**恰好**跑 `n` 趟（发散时不会收敛，只能这样定位）。"""
    cur = copy.deepcopy(nodes)
    for _ in range(n):
        cur, _ = _sim_pass(cur, pad, relativize)
    return cur


def _as_diag_node(n):
    """`dbg799diag.py` 的读数（字段名是 `rel`）⟹ 独立重算用的形状。"""
    return {"id": n["id"], "type": n["type"], "parentId": n.get("parentId"),
            "position": {"x": n["rel"]["x"], "y": n["rel"]["y"]},
            "w": n["w"], "h": n["h"]}


def _shape(nodes):
    """独立重算结果 ⟹ 探针 `MEASURE` 的读数形状（供 `_same` 逐位比对）。"""
    return [{"id": n["id"], "type": n["type"], "parentId": n["parentId"],
             "pos": n["position"],
             "abs": dict(zip(("x", "y"), _abs(nodes, n))),
             "w": n["w"], "h": n["h"]} for n in nodes]


# ---------------------------------------------------------------- 读数工具
def _as_node(n):
    """把探针的 MEASURE 读数转成独立重算用的形状（`w/h` 与 `position`）。"""
    return {
        "id": n["id"], "type": n["type"], "parentId": n["parentId"],
        "position": {"x": n["pos"]["x"], "y": n["pos"]["y"]},
        "w": n["w"], "h": n["h"],
    }


def _violations(nodes, pad):
    """返回 (不变量A违规, 不变量B违规) 的可读描述列表。"""
    by_id = {n["id"]: n for n in nodes}
    a_bad, b_bad = [], []
    for n in nodes:
        pid = n.get("parentId")
        if not pid or pid not in by_id:
            continue
        g = by_id[pid]
        gx, gy = _abs(nodes, g)
        nx, ny = _abs(nodes, n)
        gw, gh = g.get("w") or 0, g.get("h") or 0
        nw, nh = n.get("w") or 0, n.get("h") or 0
        if (nx < gx - EPS or ny < gy - EPS
                or nx + nw > gx + gw + EPS or ny + nh > gy + gh + EPS):
            over = []
            if nx < gx - EPS:
                over.append("左溢出%s" % (gx - nx))
            if ny < gy - EPS:
                over.append("上溢出%s" % (gy - ny))
            if nx + nw > gx + gw + EPS:
                over.append("右溢出%s" % (nx + nw - gx - gw))
            if ny + nh > gy + gh + EPS:
                over.append("下溢出%s" % (ny + nh - gy - gh))
            a_bad.append("%s 超出 %s：%s" % (n["id"], pid, "、".join(over)))
    for g in nodes:
        if g["type"] != "storyboard-group":
            continue
        kids = [n for n in nodes if n.get("parentId") == g["id"]]
        if not kids:
            continue
        abs_pos = {k["id"]: _abs(nodes, k) for k in kids}
        min_x = min(abs_pos[k["id"]][0] for k in kids)
        min_y = min(abs_pos[k["id"]][1] for k in kids)
        max_x = max(abs_pos[k["id"]][0] + (k.get("w") or 350) for k in kids)
        max_y = max(abs_pos[k["id"]][1] + (k.get("h") or 180) for k in kids)
        gx, gy = _abs(nodes, g)
        want = (min_x - pad, min_y - pad,
                max_x - min_x + pad * 2, max_y - min_y + pad * 2)
        got = (gx, gy, g.get("w") or 0, g.get("h") or 0)
        if not all(NEAR(a, b) for a, b in zip(want, got)):
            b_bad.append("%s 期望(abs %s,%s %sx%s) 实得(abs %s,%s %sx%s)"
                         % ((g["id"],) + want + got))
    return a_bad, b_bad


def _same(a, b, pos_key="pos"):
    """逐位比较两个读数（相对位置 / 绝对位置 / 宽高 全都要）。"""
    ia = {n["id"]: n for n in a}
    ib = {n["id"]: n for n in b}
    if set(ia) != set(ib):
        return False, "节点集合不同"
    for k in sorted(ia):
        x, y = ia[k], ib[k]
        for f in (pos_key, "abs"):
            for c in ("x", "y"):
                if x[f][c] != y[f][c]:
                    return False, "%s.%s.%s %r != %r" % (k, f, c, x[f][c], y[f][c])
        for c in ("w", "h"):
            if x[c] != y[c]:
                return False, "%s.%s %r != %r" % (k, c, x[c], y[c])
    return True, ""


def _shape_diag(nodes):
    """独立重算结果 ⟹ `dbg799diag.py` 读数的形状（该探针把相对位置叫 `rel`）。"""
    return [{"id": n["id"], "type": n["type"], "parentId": n["parentId"],
             "rel": n["position"],
             "abs": dict(zip(("x", "y"), _abs(nodes, n))),
             "w": n["w"], "h": n["h"]} for n in nodes]


def _diag_at(rows, tag, t):
    for r in rows:
        if r["tag"] == tag:
            for s in r["seq"]:
                if s["t"] == t:
                    return s["nodes"]
    return None


def _rows(raw):
    """两轮 × 四臂，展平成 (round, arm) -> row。"""
    out = {}
    for rnd in raw["rounds"]:
        for row in rnd["rows"]:
            out[(rnd["round"], row["arm"])] = row
    return out


# ---------------------------------------------------------------- 反推 padding
def infer_pad(row):
    """★ 用 `nestedOrigin` 的最终态反推 padding：哪个候选能让不变量 B 成立？

    选 `nestedOrigin` 是因为它在 pre 里**本来就对**（`parentAbs == 0` 的特例），
    所以反推出来的值不依赖修复后的实现 ⟹ 不是循环论证。
    """
    hits = []
    for pad in PAD_CANDIDATES:
        nodes = [_as_node(n) for n in row["seq"][-1]["state"]["nodes"]]
        _, bad_b = _violations(nodes, pad)
        if not bad_b:
            hits.append(pad)
    return hits


# ---------------------------------------------------------------- 主流程
def main():
    pre = json.loads(RAW_PRE.read_text(encoding="utf-8"))
    post = json.loads(RAW_POST.read_text(encoding="utf-8"))
    prows, porows = _rows(pre), _rows(post)
    checks = []

    def add(cid, title, ok, detail, anchors):
        checks.append({"id": cid, "title": title, "pass": bool(ok),
                       "detail": detail, "anchors": anchors})

    # --- P1 反推 padding（pre 的 nestedOrigin 上做，两轮都要唯一）
    pad_sets = []
    for rd in (1, 2):
        row = prows.get((rd, "nestedOrigin"))
        if row and not row.get("FAILED"):
            pad_sets.append((rd, infer_pad(row)))
    uniq = sorted({p for _, s in pad_sets for p in s})
    add("P1", "GROUP_PADDING 由 raw 反推得出（不写死常量）",
        len(pad_sets) == 2 and all(len(s) == 1 for _, s in pad_sets)
        and len({s[0] for _, s in pad_sets}) == 1,
        "两轮反推结果：%s；候选域 %s" % (pad_sets, list(PAD_CANDIDATES)),
        ["probes/dbg799a.py:ARMS[nestedOrigin]", SRC_FIT])
    pad = uniq[0] if len(uniq) == 1 else None

    # --- P2 阴性对照前提：nestedOrigin 确实落在 parentAbs==0 的特例上
    origin_ok = []
    for rd in (1, 2):
        row = prows.get((rd, "nestedOrigin"))
        if not row or row.get("FAILED"):
            origin_ok.append((rd, "读数缺失"))
            continue
        g = [n for n in row["seq"][0]["state"]["nodes"] if n["id"] == "g-outer"]
        origin_ok.append((rd, None if g and (g[0]["pos"]["x"] == 0
                                             and g[0]["pos"]["y"] == 0)
                          else "g-outer 相对位置不是 (0,0)：%r" % (g[0]["pos"] if g else None)))
    add("P2", "★ 阴性对照前提：nestedOrigin 的外层组**确实**在原点（parentAbs==0）",
        all(err is None for _, err in origin_ok),
        "逐轮核对：%s" % (origin_ok,),
        ["probes/dbg799a.py:MAKE_GRAPH(outer@spec.ox,spec.oy)"])

    # --- P3 阳性对照：单层臂 pre 全对（机制本身没坏）
    pos_ok, pos_detail = [], []
    for rd in (1, 2):
        row = prows.get((rd, "singleNudge"))
        if not row or row.get("FAILED"):
            pos_ok.append(False)
            pos_detail.append("r%d 读数缺失" % rd)
            continue
        nodes = [_as_node(n) for n in row["seq"][-1]["state"]["nodes"]]
        a, b = _violations(nodes, pad if pad is not None else 40)
        pos_ok.append(not a and not b)
        pos_detail.append("r%d A=%s B=%s" % (rd, a or "无", b or "无"))
    add("P3", "阳性对照：单层组（无父节点）pre 已全对",
        all(pos_ok), "；".join(pos_detail),
        ["probes/dbg799a.py:ARMS[singleNudge]", SRC_FIT])

    # --- B1 缺陷复现：pre 的偏移臂违反不变量 A
    bug_rows, bug_detail = [], []
    for arm in ("nestedOffsetOnce", "nestedOffsetTwice"):
        for rd in (1, 2):
            row = prows.get((rd, arm))
            if not row or row.get("FAILED"):
                bug_rows.append(False)
                bug_detail.append("%s r%d 读数缺失" % (arm, rd))
                continue
            nodes = [_as_node(n) for n in row["seq"][-1]["state"]["nodes"]]
            a, _ = _violations(nodes, pad if pad is not None else 40)
            bug_rows.append(bool(a))
            bug_detail.append("%s r%d 末步 A违规 %d 条" % (arm, rd, len(a)))
    add("B1", "★ 缺陷复现：pre 的「外层有偏移」臂违反不变量 A（成员/子组在框外）",
        all(bug_rows), "；".join(bug_detail),
        ["probes/dbg799a.py:ARMS[nestedOffsetOnce/Twice]"])

    # --- B2 缺陷不需要用户动作：`setNodes` 之后的自动 fit 就已引爆
    #   （`dbg799diag.py` 实测 t=0 还是 w=10，t=30 已贴合 ⟹ 期间跑过 fit）
    first_bad = []
    for arm in ("nestedOffsetOnce", "nestedOffsetTwice"):
        for rd in (1, 2):
            row = prows.get((rd, arm))
            if not row or row.get("FAILED"):
                first_bad.append((arm, rd, None))
                continue
            t0 = [_as_node(n) for n in row["seq"][0]["state"]["nodes"]]
            a0, _ = _violations(t0, pad if pad is not None else 40)
            first_bad.append((arm, rd, len(a0)))
    add("B2", "★ 缺陷不必等用户动作：**注入后的首读**就已越界（自动 fit 就够）",
        all(v is not None and v > 0 for _, _, v in first_bad),
        "注入后首读的不变量 A 违规条数（臂, 轮, 条数）：%s" % (first_bad,),
        ["probes/dbg799diag.py:t=0 vs t=30", "src/store/canvasStore.ts:3819"])

    # --- F1 修复生效：post 的偏移臂两条不变量都成立
    fix_rows, fix_detail = [], []
    for arm in ("nestedOrigin", "nestedOffsetOnce", "nestedOffsetTwice"):
        for rd in (1, 2):
            row = porows.get((rd, arm))
            if not row or row.get("FAILED"):
                fix_rows.append(False)
                fix_detail.append("%s r%d 读数缺失" % (arm, rd))
                continue
            bad = []
            for st in row["seq"]:
                nodes = [_as_node(n) for n in st["state"]["nodes"]]
                a, b = _violations(nodes, pad if pad is not None else 40)
                bad += ["步%d A:%s" % (st["step"], x) for x in a]
                bad += ["步%d B:%s" % (st["step"], x) for x in b]
            fix_rows.append(not bad)
            fix_detail.append("%s r%d 违规 %d 条" % (arm, rd, len(bad)))
    add("F1", "★ 修复生效：post 的全部嵌套臂（含偏移）两条不变量全程成立",
        all(fix_rows), "；".join(fix_detail),
        ["src/store/canvasStore.ts:parentAbs", SRC_FIT])

    # --- R1 无回归：修复对 parentAbs==0 的情形是**逐位 no-op**
    same_rows, same_detail = [], []
    for arm in ("singleNudge", "nestedOrigin"):
        for rd in (1, 2):
            a_row, b_row = prows.get((rd, arm)), porows.get((rd, arm))
            if not a_row or not b_row or a_row.get("FAILED") or b_row.get("FAILED"):
                same_rows.append(False)
                same_detail.append("%s r%d 读数缺失" % (arm, rd))
                continue
            for i, (x, y) in enumerate(zip(a_row["seq"], b_row["seq"])):
                ok, why = _same(x["state"]["nodes"], y["state"]["nodes"])
                same_rows.append(ok)
                if not ok:
                    same_detail.append("%s r%d 步%d: %s" % (arm, rd, i, why))
    add("R1", "★ 无回归：单层臂与 nestedOrigin 的 pre/post **逐位相同**",
        all(same_rows), "共比对 %d 组读数；差异：%s"
        % (len(same_rows), same_detail or "无"),
        ["src/store/canvasStore.ts:parentAbs（parentAbs==0 时为恒等）"])

    # --- C1 独立重算逐位吻合（post）
    sim_rows, sim_detail = [], []
    for arm in ("nestedOrigin", "nestedOffsetOnce", "nestedOffsetTwice"):
        row = porows.get((1, arm))
        if not row or row.get("FAILED") or pad is None:
            sim_rows.append(False)
            sim_detail.append("%s 缺前置" % arm)
            continue
        t0 = [_as_node(n) for n in row["seq"][0]["state"]["nodes"]]
        sim0, passes = _sim_settle(t0, pad)
        want = [{"id": n["id"], "type": n["type"], "parentId": n["parentId"],
                 "pos": n["position"], "abs": dict(zip(("x", "y"), _abs(sim0, n))),
                 "w": n["w"], "h": n["h"]} for n in sim0]
        got = row["seq"][0]["state"]["nodes"]
        ok, why = _same(want, got)
        sim_rows.append(ok)
        sim_detail.append("%s 收敛用了 %d 趟；逐位比对 %s"
                          % (arm, passes, "相同" if ok else why))
    add("C1", "★ 独立重算逐位吻合：本文件自写的 fit 模拟复刻了 post 的实测",
        all(sim_rows), "；".join(sim_detail),
        ["probes/mk799audit.py:_sim_settle"])

    # --- C2 pre 侧独立重算：模拟**修复后**算法去解释 **pre** 的读数 ⟹ 必须对不上
    mismatch = []
    for arm in ("nestedOrigin", "nestedOffsetOnce"):
        row = prows.get((1, arm))
        if not row or row.get("FAILED") or pad is None:
            continue
        t0 = [_as_node(n) for n in row["seq"][0]["state"]["nodes"]]
        sim0, _ = _sim_settle(t0, pad)
        want = [{"id": n["id"], "type": n["type"], "parentId": n["parentId"],
                 "pos": n["position"], "abs": dict(zip(("x", "y"), _abs(sim0, n))),
                 "w": n["w"], "h": n["h"]} for n in sim0]
        ok, _ = _same(want, row["seq"][0]["state"]["nodes"])
        mismatch.append((arm, ok))
    add("C2", "★ 同一模拟对 pre 的偏移臂**对不上**（证明模拟抓的是真缺陷，不是口径差异）",
        dict(mismatch).get("nestedOrigin") is True
        and dict(mismatch).get("nestedOffsetOnce") is False,
        "「模拟 == pre 实测」逐臂结果：%s" % (mismatch,),
        ["probes/mk799audit.py:_sim_settle"])

    # --- 下面三条用 `dbg799diag.py` 的读数：那里才有**原始注入态**（w=10），
    #     所以能从「注入」一路验到「稳定」，而不只是验不动点。
    diag_post = json.loads((ROOT / "raw" / "vb799diag-post.json")
                           .read_text(encoding="utf-8"))
    diag_pre = json.loads((ROOT / "raw" / "vb799diag-pre.json")
                          .read_text(encoding="utf-8"))

    # --- C3 完整路径（post）：原始注入态 → 自动多趟 → 稳定态，逐位吻合
    c3, c3d = [], []
    for tag in ("origin", "offset"):
        t0, t700 = _diag_at(diag_post, tag, 0), _diag_at(diag_post, tag, 700)
        if t0 is None or t700 is None or pad is None:
            c3.append(False)
            c3d.append("%s 缺读数" % tag)
            continue
        sim, passes = _sim_settle([_as_diag_node(n) for n in t0], pad, True)
        ok, why = _same(_shape_diag(sim), t700, "rel")
        c3.append(ok)
        c3d.append("%s 收敛于第 %d 趟；逐位%s" % (tag, passes,
                                                "相同" if ok else why))
    add("C3", "★ 完整路径：原始注入态 →（自动多趟）→ 稳定态，post 侧逐位吻合",
        all(c3), "；".join(c3d),
        ["probes/dbg799diag.py:t=0 → t=700", "probes/mk799audit.py:_sim_settle"])

    # --- C4 旧实现的**稳定态**被复刻（origin 臂）
    #     ★ 只要求稳定态吻合，**不**要求发散中间态吻合 —— 理由见 C4b。
    def _levels(nodes):
        by = {n["id"]: n for n in nodes}

        def d(n):
            k, pid, seen = 0, n.get("parentId"), {n["id"]}
            while pid and pid in by and pid not in seen:
                seen.add(pid)
                k += 1
                pid = by[pid].get("parentId")
            return k
        return max((d(n) for n in nodes
                    if n["type"] == "storyboard-group"), default=0) + 1

    c4, c4d = {}, []
    for tag in ("origin", "offset"):
        t0, t700 = _diag_at(diag_pre, tag, 0), _diag_at(diag_pre, tag, 700)
        if t0 is None or t700 is None or pad is None:
            c4[tag] = None
            c4d.append("%s 缺读数" % tag)
            continue
        base = [_as_diag_node(n) for n in t0]
        c4[tag] = {"levels": _levels(base),
                   "hits": [k for k in range(1, 41)
                            if _same(_shape_diag(_sim_n(base, pad, k,
                                                         relativize=False)),
                                     t700, "rel")[0]]}
        c4d.append("%s 嵌套层数 %d；不相对化模拟的命中趟数 %s"
                   % (tag, c4[tag]["levels"],
                      (c4[tag]["hits"][:3] + ["…"] + c4[tag]["hits"][-1:])
                      if len(c4[tag]["hits"]) > 4 else c4[tag]["hits"]))
    org = c4.get("origin") or {}
    hits = org.get("hits") or []
    add("C4", "★ 旧实现的稳定态被复刻：origin 臂的稳定趟数 == 嵌套层数",
        bool(hits) and len(hits) == 40 - hits[0] + 1 and hits[0] == org.get("levels"),
        "；".join(c4d),
        ["probes/mk799audit.py:_sim_n(relativize=False)"])

    # --- C4b 发散的**中间态**不唯一：如实记账，不假装能逐位复刻
    #     证据：同一份 pre 代码、同一个探针，两次运行的 t=700 读数不同
    #     （第一次 `g-inner rel(8840,23190)`、第二次 `rel(9040,23740)`）。
    #     ⟹ 反馈趟数取决于 DOM 测量回调的**时序**，不是确定函数。
    off_hits = (c4.get("offset") or {}).get("hits") or []
    add("C4b", "★ 如实记账：发散中间态**不可逐位复刻**（时序依赖），只判性质",
        off_hits == [],
        "不相对化模拟对 pre 偏移臂的命中趟数：%s（空=逐位复刻不了）。"
        "两次 pre diag 实测 t=700 的 g-inner rel 分别是 (8840,23190) 与 "
        "(9040,23740) ⟹ 中间态随 DOM 测量时序变化。"
        % (off_hits or "空",),
        ["probes/dbg799diag.py:两次 pre 运行"])

    # --- C4c 但**性质**必须一致：旧实现的模拟态同样越界
    c4c = None
    if pad is not None:
        t0 = _diag_at(diag_pre, "offset", 0)
        if t0 is not None:
            base = [_as_diag_node(n) for n in t0]
            bad = []
            for k in range(1, 41):
                a, _ = _violations(_sim_n(base, pad, k, relativize=False), pad)
                if a:
                    bad.append(k)
            c4c = bad
    add("C4c", "★ 性质一致：旧实现模拟出的态**也**违反不变量 A（越界）",
        bool(c4c),
        "不相对化模拟中越界的趟数：%s" % (c4c,),
        ["probes/mk799audit.py:_violations"])

    # --- C5 阴性对照：修复版的模拟对 pre 的偏移臂**不该**命中
    #     （origin 臂本来就对，两种写法等价，会命中 —— 所以只查 offset）
    c5 = None
    if pad is not None:
        t0, t700 = _diag_at(diag_pre, "offset", 0), _diag_at(diag_pre, "offset", 700)
        if t0 is not None and t700 is not None:
            base = [_as_diag_node(n) for n in t0]
            c5 = [k for k in range(1, 41)
                  if _same(_shape_diag(_sim_n(base, pad, k, relativize=True)),
                           t700, "rel")[0]]
    add("C5", "★ 阴性对照：相对化的模拟对 pre 偏移臂**一趟都不该命中**",
        c5 == [],
        "相对化模拟命中 pre 偏移臂的趟数：%s" % (c5,),
        ["probes/mk799audit.py:_sim_n(relativize=True)"])

    report = {"batch": 799,
              "inferredGroupPadding": pad,
              "inferredFromCandidates": list(PAD_CANDIDATES),
              "checks": checks,
              "passed": sum(1 for c in checks if c["pass"]),
              "total": len(checks)}
    OUT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    for c in checks:
        print("  %-4s %s %s" % (c["id"], "PASS" if c["pass"] else "FAIL", c["title"]))
        print("       %s" % c["detail"])
    print("  %d/%d ｜ 反推 padding = %s" % (report["passed"], report["total"], pad))
    print("wrote %s" % OUT)
    return 0 if all(c["pass"] for c in checks) else 1


if __name__ == "__main__":
    raise SystemExit(main())
