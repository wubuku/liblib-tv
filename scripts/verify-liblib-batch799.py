#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 799 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

799 改的是「组框写回时用哪个坐标系」：`nextPosition` 是 kids 的**绝对**包围盒，
799 之前被原样写进组的 `position`，而 `position` 的语义是**相对直接父节点**。
单层组没有父节点，两者恰好相等 ⟹ 793–798 六批造的组全都没有父节点，碰不到它。

- ★★ **判据不能预设坐标系**。若断言写成「`position == 绝对框`」或
  「`position == 绝对框 - 父绝对`」，就只是在测实现，不是测行为。
  ⟹ S1–S11 全部用**绝对几何**表述：成员必须落在父组的绝对框内（B 不变量）。
- ★★ **必须有阴性对照臂**（`nestedOrigin`）：外层组在原点时 `parentAbs == 0`，
  旧写法与新写法**完全等价** ⟹ 它全绿**证明不了修复有效**，只证明探针没坏。
  ⟹ S2 额外断言该臂的 `g-outer` 相对位置确实是 `(0,0)`，把「阴性」钉死。
- ★★ **发散的中间态不可逐位复刻**：同一份代码两次跑，t=700 读数不同
  （`g-inner rel` 分别是 `(8840,23190)` 与 `(9040,23740)`）⟹ 反馈趟数依赖
  DOM 测量的**时序**。S10 只判**稳定态**与**性质**，S9 如实记录「逐位复刻不了」。
- ★ **padding 不写死**：S12 从 raw 反推，16 个候选里必须唯一。
- ★ **不要用「恰好 N 处」这类断言**（797 修过 793 的同类过时断言）。
- ★ **end-to-end 证据天然存在**：`raw/vb799a-pre.json` 是变异前跑的，
  `raw/vb799a-post.json` 是修复后跑的 ⟹ 差异只能来自 `src/`。
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch799-2026-10-01"
PRE = OUTDIR / "raw/vb799a-pre.json"
POST = OUTDIR / "raw/vb799a-post.json"
DIAG_PRE = OUTDIR / "raw/vb799diag-pre.json"
DIAG_POST = OUTDIR / "raw/vb799diag-post.json"
AUDIT = OUTDIR / "audit-799.json"
REPORT = OUTDIR / "verify-report.json"
CS = "src/store/canvasStore.ts"

EPS = 0.01
PAD_CANDIDATES = (0, 4, 8, 10, 12, 16, 20, 24, 28, 32, 36, 40, 44, 48, 56, 64)
NEST_ARMS = ("nestedOrigin", "nestedOffsetOnce", "nestedOffsetTwice")


# ============================================================ 独立几何实现
def abs_pos(all_nodes, node):
    """沿 `parentId` 链把相对坐标累加成绝对坐标（防环、上限 32）。"""
    index = dict((n["id"], n) for n in all_nodes)
    x, y = node["position"]["x"], node["position"]["y"]
    pid, hops, seen = node.get("parentId"), 0, set([node["id"]])
    while pid and pid not in seen and hops < 32:
        seen.add(pid)
        hops += 1
        up = index.get(pid)
        if up is None:
            break
        x += up["position"]["x"]
        y += up["position"]["y"]
        pid = up.get("parentId")
    return x, y


def node_size(node, key, fallback):
    val = node.get(key)
    if not val:
        val = (node.get("style") or {}).get(key)
    return val if val else fallback


def check_invariants(nodes, pad):
    """返回 (越界描述列表, 不贴合描述列表)。两个判据都只用**绝对**几何。"""
    index = dict((n["id"], n) for n in nodes)
    outside, loose = [], []
    # ── 不变量 A：任何有父组的节点，其绝对矩形必须**被**父组的绝对矩形包含
    for node in nodes:
        pid = node.get("parentId")
        group = index.get(pid) if pid else None
        if group is None:
            continue
        gx, gy = abs_pos(nodes, group)
        nx, ny = abs_pos(nodes, node)
        gw, gh = node_size(group, "w", 0), node_size(group, "h", 0)
        nw, nh = node_size(node, "w", 350), node_size(node, "h", 180)
        if (nx >= gx - EPS and ny >= gy - EPS
                and nx + nw <= gx + gw + EPS and ny + nh <= gy + gh + EPS):
            continue
        why = []
        if nx < gx - EPS:
            why.append("左超 %g" % (gx - nx))
        if ny < gy - EPS:
            why.append("上超 %g" % (gy - ny))
        if nx + nw > gx + gw + EPS:
            why.append("右超 %g" % (nx + nw - gx - gw))
        if ny + nh > gy + gh + EPS:
            why.append("下超 %g" % (ny + nh - gy - gh))
        outside.append("%s 越出 %s（%s）" % (node["id"], pid, "、".join(why)))
    # ── 不变量 B：组的绝对框 == 直接子节点绝对包围盒 ⊕ pad
    for group in nodes:
        if group["type"] != "storyboard-group":
            continue
        kids = [n for n in nodes if n.get("parentId") == group["id"]]
        if not kids:
            continue
        pts = [abs_pos(nodes, k) for k in kids]
        left = min(p[0] for p in pts)
        top = min(p[1] for p in pts)
        right = max(p[0] + node_size(k, "w", 350) for k, p in zip(kids, pts))
        bottom = max(p[1] + node_size(k, "h", 180) for k, p in zip(kids, pts))
        gx, gy = abs_pos(nodes, group)
        want = (left - pad, top - pad, right - left + 2 * pad, bottom - top + 2 * pad)
        got = (gx, gy, node_size(group, "w", 0), node_size(group, "h", 0))
        if not all(abs(a - b) <= EPS for a, b in zip(want, got)):
            loose.append("%s 应为 (%g,%g,%g,%g) 实为 (%g,%g,%g,%g)"
                         % ((group["id"],) + want + got))
    return outside, loose


def sim_round(nodes, pad, relativize):
    """fit 的一趟：先外后内；`relativize=False` 复刻 799 之前的写回。"""
    work = [dict(n, position=dict(n["position"])) for n in nodes]
    index = dict((n["id"], n) for n in work)

    def depth(n):
        d, pid, seen = 0, n.get("parentId"), set([n["id"]])
        while pid and pid in index and pid not in seen and d < 32:
            seen.add(pid)
            d += 1
            pid = index[pid].get("parentId")
        return d

    order = sorted([n for n in work if n["type"] == "storyboard-group"],
                   key=depth)
    touched = False
    for group in order:
        kids = [n for n in work if n.get("parentId") == group["id"]]
        if not kids:
            continue
        pts = dict((k["id"], abs_pos(work, k)) for k in kids)
        left = min(pts[k["id"]][0] for k in kids)
        top = min(pts[k["id"]][1] for k in kids)
        right = max(pts[k["id"]][0] + node_size(k, "w", 350) for k in kids)
        bottom = max(pts[k["id"]][1] + node_size(k, "h", 180) for k in kids)
        up = index.get(group.get("parentId"))
        ux, uy = abs_pos(work, up) if up is not None else (0, 0)
        want_abs = (left - pad, top - pad)
        want_rel = ((want_abs[0] - ux, want_abs[1] - uy) if relativize
                    else want_abs)
        want_w = right - left + 2 * pad
        want_h = bottom - top + 2 * pad
        if (abs(group["position"]["x"] - want_rel[0]) <= EPS
                and abs(group["position"]["y"] - want_rel[1]) <= EPS
                and abs(node_size(group, "w", 0) - want_w) <= EPS
                and abs(node_size(group, "h", 0) - want_h) <= EPS):
            continue
        touched = True
        for n in work:
            if n["id"] == group["id"]:
                n["position"] = {"x": want_rel[0], "y": want_rel[1]}
                n["w"], n["h"] = want_w, want_h
            elif n.get("parentId") == group["id"]:
                p = pts[n["id"]]
                n["position"] = {"x": p[0] - want_abs[0], "y": p[1] - want_abs[1]}
        index = dict((n["id"], n) for n in work)
    return work, touched


def sim_rounds(nodes, pad, times, relativize):
    cur = [dict(n, position=dict(n["position"])) for n in nodes]
    for _ in range(times):
        cur, _ = sim_round(cur, pad, relativize)
    return cur


def sim_until_stable(nodes, pad, relativize, cap=16):
    cur = [dict(n, position=dict(n["position"])) for n in nodes]
    used = 0
    for _ in range(cap):
        cur, touched = sim_round(cur, pad, relativize)
        used += 1
        if not touched:
            break
    return cur, used


# ============================================================ 读数归一
def to_sim(state_nodes):
    out = []
    for n in state_nodes:
        out.append({"id": n["id"], "type": n["type"],
                    "parentId": n.get("parentId") or n.get("parentId"),
                    "position": dict(n.get("pos") or n.get("rel")),
                    "w": n["w"], "h": n["h"]})
    return out


def to_shape(nodes, key):
    return [{"id": n["id"], "type": n["type"],
             "parentId": n.get("parentId"),
             key: dict(n["position"]),
             "abs": dict(zip(("x", "y"), abs_pos(nodes, n))),
             "w": n["w"], "h": n["h"]} for n in nodes]


def bit_equal(a, b, key):
    ia = dict((n["id"], n) for n in a)
    ib = dict((n["id"], n) for n in b)
    if set(ia) != set(ib):
        return False, "节点集合不同"
    for k in sorted(ia):
        for field in (key, "abs"):
            for c in ("x", "y"):
                if ia[k][field][c] != ib[k][field][c]:
                    return False, "%s.%s.%s %r≠%r" % (k, field, c,
                                                      ia[k][field][c], ib[k][field][c])
        for c in ("w", "h"):
            if ia[k][c] != ib[k][c]:
                return False, "%s.%s %r≠%r" % (k, c, ia[k][c], ib[k][c])
    return True, ""


def rows_of(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for row in (rd.get("rows") or []):
            out.setdefault(row.get("arm"), []).append(row)
    return out


def diag_at(rows, tag, t):
    for r in rows:
        if r.get("tag") == tag:
            for s in r.get("seq", []):
                if s.get("t") == t:
                    return s.get("nodes")
    return None


# ============================================================ 检查
def run_checks(pre_raw, post_raw, diag_pre, diag_post, src):
    checks = []

    def add(cid, why, ok, ev):
        checks.append({"id": cid, "why": why, "ok": bool(ok), "evidence": ev})

    prow, pstrow = rows_of(pre_raw), rows_of(post_raw)

    # ── pad 反推：16 个候选里必须唯一，且两轮一致
    hits = []
    for row in prow.get("nestedOrigin", []):
        nodes = to_sim(row["seq"][-1]["state"]["nodes"])
        ok = [p for p in PAD_CANDIDATES
              if not check_invariants(nodes, p)[1]]
        hits.append(ok)
    pad = hits[0][0] if (hits and len(hits[0]) == 1
                         and all(h == hits[0] for h in hits)) else None
    add("S1:pad 由 raw 反推且唯一",
        "★ 不能写死 40（798 的教训）：16 个候选里必须唯一命中",
        pad is not None, {"候选域": list(PAD_CANDIDATES), "逐轮命中": hits,
                          "反推值": pad})
    PAD = pad if pad is not None else 40

    # ── S2 阴性对照前提：origin 臂的 g-outer 确实在 (0,0)
    ev = []
    for row in prow.get("nestedOrigin", []):
        g = [n for n in row["seq"][0]["state"]["nodes"] if n["id"] == "g-outer"]
        ev.append(None if (g and g[0]["pos"]["x"] == 0 and g[0]["pos"]["y"] == 0)
                  else "非原点")
    add("S2:★★ 阴性对照前提：`nestedOrigin` 的外层组在 (0,0)",
        "★ 该臂全绿**证明不了修复有效**（parentAbs==0 时新旧写法等价），"
        "只证明探针没坏 ⟹ 必须把「它落在特例上」钉死",
        ev and all(e is None for e in ev), ev)

    # ── S3 阳性对照：单层臂 pre 已全对
    ev = []
    for row in prow.get("singleNudge", []):
        a, b = check_invariants(to_sim(row["seq"][-1]["state"]["nodes"]), PAD)
        ev.append({"越界": a, "不贴合": b})
    add("S3:阳性对照：单层组 pre 全对",
        "★ 单层本来就对（没父节点）⟹ 它绿是「机制没坏」而不是「修复生效」",
        ev and all(not x["越界"] and not x["不贴合"] for x in ev), ev)

    # ── S4 缺陷复现：pre 偏移臂越界
    ev = {}
    for arm in ("nestedOffsetOnce", "nestedOffsetTwice"):
        for i, row in enumerate(prow.get(arm, [])):
            a, _ = check_invariants(to_sim(row["seq"][-1]["state"]["nodes"]), PAD)
            ev["%s#%d" % (arm, i)] = a
    add("S4:★★ 缺陷复现：pre 偏移臂成员/子组越出父组框",
        "★ 这是 793–798 六批全都测不到的那一类（它们的组都没有父节点）",
        ev and all(len(v) > 0 for v in ev.values()), ev)

    # ── S5 缺陷不必等用户动作
    ev = {}
    for arm in ("nestedOffsetOnce", "nestedOffsetTwice"):
        for i, row in enumerate(prow.get(arm, [])):
            a, _ = check_invariants(to_sim(row["seq"][0]["state"]["nodes"]), PAD)
            ev["%s#%d" % (arm, i)] = len(a)
    add("S5:★★ 缺陷在**注入后首读**就已越界（自动 fit 就够）",
        "★ `routeReactFlowChanges` 每次 react-flow 变化（含 DOM 测量）都跑 fit "
        "⟹ 不需要用户动作就会引爆",
        ev and all(v > 0 for v in ev.values()), ev)

    # ── S6 修复生效
    ev = {}
    for arm in NEST_ARMS:
        for i, row in enumerate(pstrow.get(arm, [])):
            bad = []
            for st in row["seq"]:
                a, b = check_invariants(to_sim(st["state"]["nodes"]), PAD)
                bad += ["步%d 越界 %s" % (st["step"], x) for x in a]
                bad += ["步%d 不贴合 %s" % (st["step"], x) for x in b]
            ev["%s#%d" % (arm, i)] = bad
    add("S6:★★★ 修复生效：post 全部嵌套臂两条不变量全程成立",
        "★ 判据全用绝对几何表述 ⟹ 改对改错都判得出来",
        ev and all(not v for v in ev.values()), ev)

    # ── S7 无回归：pre/post 逐位相同
    ev = []
    for arm in ("singleNudge", "nestedOrigin"):
        for i, (a, b) in enumerate(zip(prow.get(arm, []), pstrow.get(arm, []))):
            for j, (x, y) in enumerate(zip(a["seq"], b["seq"])):
                same, why = bit_equal(x["state"]["nodes"], y["state"]["nodes"], "pos")
                ev.append({"臂": arm, "轮": i, "步": j, "相同": same, "差异": why})
    add("S7:★★ 无回归：单层臂与 origin 臂 pre/post **逐位相同**",
        "★ 修复对 parentAbs==0 必须是**恒等**变换 ⟹ 逐位相同是最强的证据",
        ev and all(x["相同"] for x in ev),
        {"比对组数": len(ev), "不一致": [x for x in ev if not x["相同"]]})

    # ── S8/S9 完整路径（post）：从原始注入态跑到稳定态
    ev = {}
    for tag in ("origin", "offset"):
        t0, t700 = diag_at(diag_post, tag, 0), diag_at(diag_post, tag, 700)
        if t0 is None or t700 is None:
            ev[tag] = "缺读数"
            continue
        sim, used = sim_until_stable(to_sim(t0), PAD, True)
        same, why = bit_equal(to_shape(sim, "rel"), t700, "rel")
        ev[tag] = {"稳定趟数": used, "逐位相同": same, "差异": why}
    add("S8:★★★ 完整路径：原始注入态 →自动多趟→ 稳定态（post 逐位吻合）",
        "★ `setNodes` 不同 tick 读是 w=10（原始态），30ms 后已贴合 ⟹ "
        "路径必须能从「注入」一路验到「稳定」",
        ev and all(isinstance(v, dict) and v.get("逐位相同") for v in ev.values()),
        ev)

    # ── S10 同一模拟对 pre 偏移臂对不上
    ev = {}
    for tag in ("origin", "offset"):
        t0, t700 = diag_at(diag_pre, tag, 0), diag_at(diag_pre, tag, 700)
        if t0 is None or t700 is None:
            ev[tag] = "缺读数"
            continue
        sim, _ = sim_until_stable(to_sim(t0), PAD, True)
        ev[tag] = bit_equal(to_shape(sim, "rel"), t700, "rel")[0]
    add("S9:★ 同一模拟对 pre 偏移臂**对不上**",
        "★ 证明模拟抓的是真缺陷，不是口径差异（origin 臂仍应吻合）",
        ev.get("origin") is True and ev.get("offset") is False, ev)

    # ── S10 旧实现的稳定态被复刻 + 阴性对照
    t0, t700 = diag_at(diag_pre, "origin", 0), diag_at(diag_pre, "origin", 700)
    if t0 is None or t700 is None:
        add("S10:旧实现稳定态被复刻", "缺读数", False, None)
    else:
        base = to_sim(t0)
        hits = [k for k in range(1, 41)
                if bit_equal(to_shape(sim_rounds(base, PAD, k, False), "rel"),
                             t700, "rel")[0]]
        idx = dict((n["id"], n) for n in base)

        def dep(n):
            d, pid, seen = 0, n.get("parentId"), set([n["id"]])
            while pid and pid in idx and pid not in seen:
                seen.add(pid)
                d += 1
                pid = idx[pid].get("parentId")
            return d
        levels = max(dep(n) for n in base
                     if n["type"] == "storyboard-group") + 1
        add("S10:★ 旧实现（不相对化）的稳定态被复刻",
            "★ 同一个模拟器开关 relativize 就能解释修复前后的读数 ⟹ "
            "「模拟吻合实测」不是橡皮章",
            bool(hits) and len(hits) == 40 - hits[0] + 1
            and hits[0] == levels,
            {"嵌套层数": levels, "命中趟数": "%d..40" % hits[0] if hits else []})

    t0, t700 = diag_at(diag_pre, "offset", 0), diag_at(diag_pre, "offset", 700)
    if t0 is None or t700 is None:
        add("S11:发散中间态不可逐位复刻", "缺读数", False, None)
    else:
        base = to_sim(t0)
        hit = [k for k in range(1, 41)
               if bit_equal(to_shape(sim_rounds(base, PAD, k, True), "rel"),
                            t700, "rel")[0]]
        bad = [k for k in range(1, 41)
               if check_invariants(sim_rounds(base, PAD, k, False), PAD)[0]]
        add("S11:★ 如实记账：发散中间态不可逐位复刻，但**性质**一致",
            "★ 同一份代码两次跑 t=700 读数不同（g-inner rel 分别是 (8840,23190) "
            "与 (9040,23740)）⟹ 反馈趟数依赖 DOM 测量时序，不硬凑逐位吻合",
            hit == [] and bool(bad),
            {"相对化模拟命中趟数": hit,
             "旧实现模拟中越界的趟数": "%d..40" % bad[0] if bad else [],
             "两次实测": {"第一次": "g-inner rel(8840,23190)",
                          "第二次": "g-inner rel(9040,23740)"}})

    # ── S12 静态锚点：写回处与 no-op 判定处都用上 parentAbs
    m_write = re.search(r"position: \{ x: nextPosition\.x - parentAbs\.x,"
                        r" y: nextPosition\.y - parentAbs\.y \},", src)
    m_near_x = re.search(r"near\(live\.position\.x \+ parentAbs\.x, nextPosition\.x\)",
                         src)
    m_near_y = re.search(r"near\(live\.position\.y \+ parentAbs\.y, nextPosition\.y\)",
                         src)
    m_decl = re.search(r"const parentAbs = parentNode \? getAbsoluteNodePosition\("
                       r"parentNode, byId\) : \{ x: 0, y: 0 \};", src)
    add("S12:★★ 静态锚点：`parentAbs` 在**三处**都用上",
        "★ 漏掉 no-op 判定那两处会导致「已贴合」判错、每趟白白重建对象；"
        "漏掉写回那处就是缺陷本身",
        all((m_write, m_near_x, m_near_y, m_decl)),
        {"写回": bool(m_write), "nearX": bool(m_near_x),
         "nearY": bool(m_near_y), "声明": bool(m_decl)})

    # ── S13 静态锚点：kids 重基仍用**绝对**的 nextPosition（没被误改成相对）
    m_kid = re.search(r"x: absolute\.x - nextPosition\.x,\s*\n\s*y: absolute\.y"
                      r" - nextPosition\.y,", src)
    add("S13:静态锚点：子节点重基仍以 `nextPosition`（绝对）为准",
        "★ `nextPosition` 保持绝对语义，只在**写进组自己**时才减父位置",
        bool(m_kid), {"命中": bool(m_kid)})

    # ── S14 记账：UI 仍造不出嵌套（本批**没有**顺带实现它）
    #    ★ 要抓的是**实现**（`(nodeIds) => {`），不是接口声明
    #      （`(nodeIds?: readonly string[]) => void;`）—— 否则会抓错段落。
    i0 = src.find("groupSelectedNodes: (nodeIds) => {")
    i1 = src.find("ungroupSelectedNodes: (nodeIds) => {")
    seg = src[i0:i1] if (i0 >= 0 and i1 > i0) else ""
    m_child_filter = re.search(r'node\.type !== "storyboard-group"', seg)
    add("S14:★★ 记账：792 记的「嵌套组合没实现」**今天仍然成立**",
        "★ 本批只修 fit 的坐标系，**没有**让 UI 能创建嵌套组 ⟹ "
        "799 的结论只覆盖「已有嵌套数据时的几何」，不覆盖「造得出来」",
        bool(m_child_filter),
        {"groupSelectedNodes 里仍有 `type !== 'storyboard-group'` 过滤":
         bool(m_child_filter)})

    # ── S15 记账：改了什么、没改什么
    add("S15:记账：改动面",
        "★ 单点改动（一个函数内的写回坐标系）+ 注释更正；未新增 API、未改 UI",
        True, {
            "改动文件": ["src/store/canvasStore.ts"],
            "改动函数": ["fitStoryboardGroupsToChildren"],
            "改动性质": ["写回用相对父节点的坐标", "no-op 判定补上父节点偏移"],
            "顺带更正": ["793 注释里「嵌套时内层拿到的绝对位置已经是对的」被 799 证伪"],
            "没有改": ["UI 造嵌套组的能力（792 遗留，仍未实现）",
                       "GROUP_PADDING（仍是 797 定下的 40）",
                       "组框尺寸吸附（798 拍板：不该吸）"],
            "源站对照": "★ 未做（源站需登录）⟹ 「嵌套组应当如何表现」是工程判断"})

    return checks


# ============================================================ 变异器
def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def mut_text(path, old, new, allow_superset=False):
    """行数中性地替换一段文本。

    ★★ 两个必须做对的点（第一版都踩了）：
      1. **所有校验都在写入之前**做 ⟹ 校验失败时文件一个字节都没动。
         否则 assert 抛出会把脏文件留在工作区（799 第一版就是这么把
         `// 799 修` 留在了 `canvasStore.ts` 里）。
      2. `new` 允许是 `old` 的**超集**（反向对照「只加注释」就是这个形状）⟹
         此时不能用「旧串必须消失」当校验，否则永远失败。
    """
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    assert orig.count(old) == 1, "★ needle 不唯一：%r" % old[:70]
    txt = orig.replace(old, new)
    ev = {"新的在": new in txt,
          "行数中性": len(txt.split("\n")) == len(orig.split("\n"))}
    if allow_superset:
        ev["旧串仍在（预期）"] = old in txt
    else:
        ev["旧的不在"] = old not in txt
    assert all(ev.values()), "★ 变异没真改到目标性质：%r" % ev
    p.write_text(txt, encoding="utf-8")
    assert p.read_text(encoding="utf-8") == txt, "★ 写入后读回不一致"

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, ev


def mut_raw(path, fn):
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = fn(d)
    assert hit, "★ raw 变异没命中"
    payload = json.dumps(d, ensure_ascii=False, indent=1)
    p.write_text(payload, encoding="utf-8")
    assert p.read_text(encoding="utf-8") == payload, "★ 写入后读回不一致"

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, {"file": p.name, "hit": hit}


def _find(nodes, nid):
    for n in nodes:
        if n["id"] == nid:
            return n
    return None


def main():
    pre_raw = json.loads(PRE.read_text(encoding="utf-8"))
    post_raw = json.loads(POST.read_text(encoding="utf-8"))
    diag_pre = json.loads(DIAG_PRE.read_text(encoding="utf-8"))
    diag_post = json.loads(DIAG_POST.read_text(encoding="utf-8"))
    src = (ROOT / CS).read_text(encoding="utf-8")
    audit = json.loads(AUDIT.read_text(encoding="utf-8")) if AUDIT.exists() else None

    src0, pre0, post0, dp0, dq0 = (sha(ROOT / CS), sha(PRE), sha(POST),
                                   sha(DIAG_PRE), sha(DIAG_POST))
    checks = run_checks(pre_raw, post_raw, diag_pre, diag_post, src)
    nPass = sum(1 for c in checks if c["ok"])
    assert nPass == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPass, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        """★ `mutate()` 的校验全部在写入前完成 ⟹ 这里失败也不会留下脏文件。"""
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(PRE.read_text(encoding="utf-8")),
                           json.loads(POST.read_text(encoding="utf-8")),
                           json.loads(DIAG_PRE.read_text(encoding="utf-8")),
                           json.loads(DIAG_POST.read_text(encoding="utf-8")),
                           (ROOT / CS).read_text(encoding="utf-8"))
            flipped = [x["id"] for x in c if not x["ok"]]
            if expect == "__NO_FLIP__":
                return {"name": name, "why": why, "evidence": ev,
                        "expectFlipped": "（反向对照：期望不翻）",
                        "flipped": flipped, "ok": not flipped}
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped}
        finally:
            restore()

    # ① ★★ 源码去掉相对化（回退 799 的写回）⟹ 静态锚点必须翻
    negs.append(neg(
        "N1 ★★ 源码回退：写回不再减父节点位置",
        "★ 端到端证据已在 pre/post raw 里；这条验的是**静态锚点**能抓住回退",
        lambda: mut_text(CS,
                         "position: { x: nextPosition.x - parentAbs.x,"
                         " y: nextPosition.y - parentAbs.y },",
                         "position: nextPosition,"),
        "S12:★★ 静态锚点：`parentAbs` 在**三处**都用上"))

    # ② ★★ 源码只留一半（写回改对、no-op 判定漏掉）⟹ 静态锚点必须翻
    negs.append(neg(
        "N2 ★★ 源码只改一半：漏掉 no-op 判定里的父偏移",
        "★ 漏这两处不会立刻坏掉（多重建一次对象而已）⟹ 正因如此必须由锚点守住",
        lambda: mut_text(CS,
                         "near(live.position.x + parentAbs.x, nextPosition.x)",
                         "near(live.position.x, nextPosition.x)"),
        "S12:★★ 静态锚点：`parentAbs` 在**三处**都用上"))

    # ③ ★★ 破坏 post raw 的嵌套结构（把内层组的相对位置挪走）⟹ S6/S7 必须翻
    def break_post(d):
        for rd in d["rounds"]:
            for row in rd["rows"]:
                if row.get("arm") == "nestedOffsetTwice" and "seq" in row:
                    g = _find(row["seq"][-1]["state"]["nodes"], "g-inner")
                    if g is None:
                        return False
                    g["pos"]["x"] = g["pos"]["x"] + 400
                    return True
        return False

    negs.append(neg(
        "N3 ★★ post raw：把内层组的相对位置挪 +400",
        "★ 验证 S6（修复生效）真的在看几何：几何一坏它就必须红",
        lambda: mut_raw("docs/research/liblib-canvas-batch799-2026-10-01/"
                        "raw/vb799a-post.json", break_post),
        "S6:★★★ 修复生效：post 全部嵌套臂两条不变量全程成立"))

    # ④ ★★ 把 origin 臂的外层组挪离原点 ⟹ S2（阴性对照前提）必须翻
    def break_origin(d):
        for rd in d["rounds"]:
            for row in rd["rows"]:
                if row.get("arm") == "nestedOrigin" and "seq" in row:
                    g = _find(row["seq"][0]["state"]["nodes"], "g-outer")
                    if g is None:
                        return False
                    g["pos"]["x"] = 200
                    g["pos"]["y"] = 150
                    return True
        return False

    negs.append(neg(
        "N4 ★★ pre raw：把 origin 臂的外层组挪到 (200,150)",
        "★ 验证 S2：这条断言就是「阴性对照真的落在特例上」的唯一保证",
        lambda: mut_raw("docs/research/liblib-canvas-batch799-2026-10-01/"
                        "raw/vb799a-pre.json", break_origin),
        "S2:★★ 阴性对照前提：`nestedOrigin` 的外层组在 (0,0)"))

    # ⑤ ★★ 反向对照：只改注释 ⟹ 一项都不该翻
    negs.append(neg(
        "N5 ★★ 反向对照：只改 `parentAbs` 那段注释的文字",
        "★ 证明 S12 锚的是**表达式**不是某段文本 —— 否则改个注释就全红",
        lambda: mut_text(CS,
                         "const parentAbs = parentNode ? getAbsoluteNodePosition("
                         "parentNode, byId) : { x: 0, y: 0 };",
                         "const parentAbs = parentNode ? getAbsoluteNodePosition("
                         "parentNode, byId) : { x: 0, y: 0 };  // 799 修",
                         allow_superset=True),
        "__NO_FLIP__"))

    # ⑥ ★★ 反向对照：把 GROUP_PADDING 改成另一个 20 的倍数 ⟹ 不该翻
    #    （S1 是从 raw 反推的，不读源码 ⟹ 改源码本就不该影响它）
    negs.append(neg(
        "N6 ★★ 反向对照：`GROUP_PADDING` 改成 60（仍是 20 的倍数）",
        "★ 判据是「几何自洽」不是「== 40」⟹ 改常量不该让任何一条翻红",
        lambda: mut_text(CS, "const GROUP_PADDING = 40;",
                         "const GROUP_PADDING = 60;"),
        "__NO_FLIP__"))

    restored = {"cs": sha(ROOT / CS) == src0, "pre": sha(PRE) == pre0,
                "post": sha(POST) == post0, "diagPre": sha(DIAG_PRE) == dp0,
                "diagPost": sha(DIAG_POST) == dq0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    negs_ok = sum(1 for n in negs if n["ok"])
    report = {"batch": 799, "totals": {"passed": nPass, "total": len(checks)},
              "checks": checks, "negatives": negs,
              "negativesOk": negs_ok, "negativesTotal": len(negs),
              "auditSummary": ({"passed": audit["passed"],
                                "total": audit["total"]} if audit else None),
              "restoreSha": {"src": src0, "pre": pre0, "post": post0,
                             "diagPre": dp0, "diagPost": dq0, "ok": restored}}
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    for c in checks:
        print("  %s %s" % ("PASS" if c["ok"] else "FAIL", c["id"]))
    print("★ 主检查 %d/%d" % (nPass, len(checks)))
    for n in negs:
        print("  %s %s ｜ 翻红：%s" % ("PASS" if n["ok"] else "FAIL", n["name"],
                                      n["flipped"] or "无"))
    print("★ 阴性对照 %d/%d" % (negs_ok, len(negs)))
    print("★ 阴性对照后字节级复原：%r" % restored)
    ok = nPass == len(checks) and negs_ok == len(negs)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
