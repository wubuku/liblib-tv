#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 794 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

794 改了 `src/store/canvasStore.ts`，把 `fitStoryboardGroupsToChildren` 挂到
**两个删除写点**上。结论是「删掉一个成员之后分组框收拢」。

- ★ **只测「框动了」不够**：一个「删成员后把框硬塞成幸存者尺寸、无视真实位置」
  的实现也能全绿 ⟹ 必须有**从 raw 独立重算**的贴合值对照（S5）。
- ★ **只测「两个写点都挂了」也不够**：两处 needle **完全相同**
  （`nodes: fitStoryboardGroupsToChildren(` + 下一行
  `canvas.nodes.filter((node) => !removedIds.has(node.id))`）
  ⟹ 任何按**子串**做的「唯一命中」断言都会数成 2 或 0，
  且源码变异若用 `replace_all` 会**一次改掉两处** ⟹ 阴性对照直接作废。
  ⟹ 本验收器一律**按行号定位**，且逐行校验原文后才替换。
- ★ **「pre 不等、post 等」必须双向判**（S5）：只判 post 会让「两阶段都等于贴合值」
  这种「造组那一步本来就贴好了、修复没做任何事」的实现混过去。
- ★ **撤销臂要同时验成员与框**（S6）：756 的教训是「用户最自然的补救动作无效，
  唯一出路是撤销」⟹ 框没跟着回来，撤销就是半个修复。
- ★ **前置对照**（S7）：没有它，「处理臂的框变了」可能只是造组那一步本来就错。
- ★ 源码变异必须能翻掉结论，且**字节级复原**（N1/S10）。

## 静态层为什么算「独立」

汇编器用**行锚定 + 向上找 owner** 判归属；本验收器用**行号 + 逐行原文校验**，
并从 raw 的 before/afterDelete/after **重新推**行为签名 ⟹ 两边写错会互相抓出来。
"""
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch794-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb794a-pre.json"
POST = OUTDIR / "raw/vb794a-post.json"

CS = "src/store/canvasStore.ts"
ARMS = ["groupTwoDeleteOne", "groupTwoDeleteOneUndo", "groupTwoNoDelete"]
PADDING = 32

#: ★ 两个删除写点的**逐行原文**（与 `fitStoryboardGroupsToChildren` 的实参一起）。
#: 两处 needle 完全相同 ⟹ 只能靠行号区分，substring 断言在这里是**错的**。
DEL_SITE_BODY = [
    "                nodes: fitStoryboardGroupsToChildren(",
    "                  canvas.nodes.filter((node) => !removedIds.has(node.id)),",
    "                ),",
]
#: 变异后：把其中一处接回原形（去掉包裹），行数保持 3 ⟹ 行数中性
DEL_SITE_MUT = [
    "                nodes:",
    "                  canvas.nodes.filter((node) => !removedIds.has(node.id)),",
    "                ),",
]


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def box(g):
    if not g:
        return None
    return (g["pos"]["x"], g["pos"]["y"], g["w"], g["h"])


def fit_of(members):
    """★ 从 raw 的成员读数**独立重算**贴合框（不读源码公式）。"""
    ms = [m for m in (members or []) if isinstance(m, dict) and m.get("abs")]
    if not ms:
        return None
    x0 = min(m["abs"]["x"] for m in ms)
    y0 = min(m["abs"]["y"] for m in ms)
    x1 = max(m["abs"]["x"] + (m.get("w") or 0) for m in ms)
    y1 = max(m["abs"]["y"] + (m.get("h") or 0) for m in ms)
    return (x0 - PADDING, y0 - PADDING, x1 - x0 + PADDING * 2, y1 - y0 + PADDING * 2)


def sig(cell, key="after"):
    """★ 行为签名；None = **空读数**（探针 FAILED / 字段缺失）。"""
    b, a = cell.get("before"), cell.get(key)
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    if not (b.get("groupStore") and a.get("groupStore")):
        return None
    return {
        "memberCount": (b.get("memberCount"), a.get("memberCount")),
        "box": (box(b["groupStore"]), box(a["groupStore"])),
        "frameMoved": box(b["groupStore"]) != box(a["groupStore"]),
        "inside": [[m.get("inside") for m in b.get("members", [])],
                   [m.get("inside") for m in a.get("members", [])]],
        "past": (b.get("past"), a.get("past")),
        "fit": fit_of(a.get("members", [])),
    }


def front(cell):
    """前置对照臂的签名（只有一个 state 快照，没有 before/after）。"""
    s = cell.get("state")
    if not isinstance(s, dict) or not s.get("groupStore"):
        return None
    return {"memberCount": s.get("memberCount"),
            "box": box(s["groupStore"]),
            "fit": fit_of(s.get("members", [])),
            "inside": [m.get("inside") for m in s.get("members", [])]}


def del_sites(lines):
    """★ 按行号找出两个删除写点；每处**逐行校验原文**，只认真匹配。"""
    hits = []
    for i, l in enumerate(lines):
        if l.strip() == "nodes: fitStoryboardGroupsToChildren(":
            block = lines[i:i + 3]
            if block == DEL_SITE_BODY:
                hits.append({"line": i + 1, "block": block})
    return hits


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / CS).read_text(encoding="utf-8")
    lines = src.split("\n")
    pre, post = index(pre_raw), index(post_raw)
    sites = del_sites(lines)

    # ── S1：★ 两个删除写点都在，且**逐行原文校验**过 ──
    add("S1:★★ 两个删除写点都在（逐行原文校验，不是子串计数）",
        "★ 两处 needle 完全相同 ⟹ 子串计数必然数错；"
        "且源码变异若按子串替换会一次改掉两处，阴性对照直接作废",
        len(sites) == 2,
        {"命中行": [s["line"] for s in sites],
         "原文": sites[0]["block"] if sites else None})

    # ── S2：★ 拖拽收口那处**仍然**挂着（本批没把 793 的半边改坏）──
    drag = re.findall(r"nodes: fitStoryboardGroupsToChildren\(\n"
                      r"\s*plan\.nextNodes\.map\(withoutStoredNodeSelection\),", src)
    add("S2:★ 793 的拖拽收口那处仍然挂着",
        "★ 同一文件多处编辑必须原子化（782 立的纪律）⟹ "
        "本批加了两处删除路径，**不能**顺手把 793 那处弄坏",
        len(drag) == 1 and len(sites) == 2,
        {"拖拽写点": len(drag), "删除写点": len(sites)})

    # ── S3：★ 纯函数仍只有一个定义（本批复用 793 的，不另造一个）──
    add("S3:纯函数仍是**一个**定义",
        "★ 另造一个等价实现会绕过 793 的两条刻意边界（空组不动 / EPS）",
        len(re.findall(r"function fitStoryboardGroupsToChildren\(", src)) == 1,
        {"定义数": len(re.findall(
            r"function fitStoryboardGroupsToChildren\(", src))})

    # ── S4：★ 两个删除写点分属两个不同函数 ──
    def owner(ln):
        j = next(i for i, l in enumerate(lines)
                 if re.match(r"\s*export const useCanvasStore = create", l))
        for k in range(ln - 1, j, -1):
            m = re.match(r"  ([A-Za-z_]\w*):\s*\(", lines[k])
            if m:
                return m.group(1)
        return None

    owners = sorted({owner(s["line"]) for s in sites})
    add("S4:★★ 两个删除写点分属**两个不同的函数**",
        "★ 同名函数里数出两处可能只是同一处写了两遍 ⟹ "
        "必须确认是 `removeNode` 与 `removeSelectedNodes`",
        owners == ["removeNode", "removeSelectedNodes"],
        {"函数": owners})

    # ── S5：★★ 处理臂：pre 框不动、post 框收拢，且 post **精确等于**独立重算值 ──
    p = [sig(c) for c in pre.get("groupTwoDeleteOne", [])]
    q = [sig(c) for c in post.get("groupTwoDeleteOne", [])]
    bad5 = []
    for name, lst in (("pre", p), ("post", q)):
        for s in lst:
            if not s or s["memberCount"] != (2, 1) or s["inside"][1] != [True]:
                bad5.append({"phase": name, "sig": s, "why": "读数不合预期"})
                continue
            same = s["box"][1] == s["fit"]
            if (name == "post") != same:      # pre 应**不等**，post 应**相等**
                bad5.append({"phase": name, "box": s["box"][1],
                             "fit": s["fit"], "equals": same})
    add("S5:★★ pre 框不动、post 框收拢，且 post 精确等于独立重算的贴合值",
        "★ 贴合值由 raw 里的幸存者读数 + 32×2 重算，**不依赖**源码公式 ⟹ "
        "公式写错也会被抓出来。★ 双向判：只判 post 会让「造组那步本来就贴好、"
        "修复没做任何事」混过去",
        not bad5, {"bad": bad5, "pre": p, "post": q})

    # ── S6：★★ 撤销臂：成员与**框**都回来，且 past 退了一格 ──
    bad6, ev6 = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("groupTwoDeleteOneUndo", []):
            b, m, a = sig(c, "before"), sig(c, "afterDelete"), sig(c, "after")
            if not (b and m and a):
                bad6.append({"phase": name, "why": "空读数"})
                continue
            ok = (a["memberCount"][1] == 2
                  and a["box"][1] == b["box"][0]
                  and a["inside"][1] == [True, True]
                  and a["past"][1] < a["past"][0] + 1)
            ev6.append({"phase": name, "before": b["box"][0],
                        "afterDelete": m["box"][1], "afterUndo": a["box"][1],
                        "members": a["memberCount"], "past": a["past"],
                        "frameRestored": a["box"][1] == b["box"][0]})
            if not ok:
                bad6.append(ev6[-1])
    add("S6:★★ 撤销臂：成员与**框**都回来，且 past 真的退了一格",
        "★ 756 的教训：「用户最自然的补救动作无效，唯一出路是撤销」⟹ "
        "框没跟着回来，撤销就是半个修复",
        not bad6, {"bad": bad6, "evidence": ev6})

    # ── S7：★ 前置对照：造出的两成员框就是贴合值，且两阶段一致 ──
    bad7, ev7 = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("groupTwoNoDelete", []):
            f = front(c)
            if not f or f["memberCount"] != 2:
                bad7.append({"phase": name, "front": f, "why": "不是两成员"})
                continue
            ok = f["box"] == f["fit"] and f["inside"] == [True, True]
            ev7.append({"phase": name, "box": f["box"], "fit": f["fit"],
                        "equals": f["box"] == f["fit"], "inside": f["inside"]})
            if not ok:
                bad7.append(ev7[-1])
    add("S7:★ 前置对照：造出的两成员框就是贴合值，两阶段一致",
        "★ 没有它，「处理臂的框变了」可能只是造组那一步本来就错",
        not bad7, {"bad": bad7, "evidence": ev7})

    # ── S8：★ 两轮只比**行为签名**（不比的像素）──
    bad8 = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm in ARMS:
            lst = idx.get(arm, [])
            sigs = [front(c) for c in lst] if arm == "groupTwoNoDelete" \
                else [sig(c) for c in lst]
            if len(sigs) != 2 or sigs[0] != sigs[1]:
                bad8.append({"phase": name, "arm": arm, "sigs": sigs})
    add("S8:★ 两轮的行为签名一致",
        "★ 节点 id 每轮新造 ⟹ 拿 id / 像素判「一致」会误报",
        not bad8, {"bad": bad8})

    # ── S9：格数与无 FAILED ──
    bad9 = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad9.append({"phase": name, "arms": sorted(idx)})
        for arm, lst in idx.items():
            if len(lst) != 2:
                bad9.append({"phase": name, "arm": arm, "rounds": len(lst)})
            for c in lst:
                if c.get("FAILED") or not isinstance(c, dict):
                    bad9.append({"phase": name, "arm": arm, "FAILED": "有 FAILED"})
    add("S9:两阶段各 3 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 或读数缺失就是**空读数**，不能当结论", not bad9, {"bad": bad9})

    if audit:
        add("S10:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S10:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)

    # ── S11：★★ 限定：探针的 Delete 键只走 `removeSelectedNodes` ──
    # ★ 这是本批**最重要的一条限定**：raw 里的行为读数只支撑**一个**写点。
    #   `removeNode` 在画布 UI 上**零调用者**（见 detail 里的调用者普查）⟹
    #   它的修复**只有静态证据**（S1/S4），**没有行为证据**。
    #   把它说成「两处都验过了」就是越界。
    page = (ROOT / "src/app/page.tsx").read_text(encoding="utf-8")
    hit_removeSelected = len(re.findall(r"removeSelectedNodes\(", page))
    hit_removeNode = len(re.findall(r"(?<!Selected)removeNode\(", page))
    # ★ Delete 键的**真实**调用行（从源码读出，不写死）
    del_line = next((i for i, l in enumerate(page.split("\n"), 1)
                     if re.match(r'\s*removeSelectedNodes\(', l)), None)
    zero_ui = hit_removeNode == 0
    add("S11:★★ 限定：Delete 键只走 `removeSelectedNodes`，"
        "`removeNode` 在画布 UI 上零调用者",
        "★ raw 的行为读数**只支撑一个写点**。`removeNode` 那处只有静态证据"
        "（S1/S4），**没有行为证据** ⟹ 报告不许说「两处都验过了」",
        hit_removeSelected > 0 and zero_ui and del_line is not None,
        {"page.tsx 里 removeSelectedNodes 调用数": hit_removeSelected,
         "page.tsx 里 removeNode 调用数": hit_removeNode,
         "Delete 键实际调用行": del_line,
         "删除键走的函数": "removeSelectedNodes",
         "removeNode 的证据等级": "★ 仅静态（S1/S4），无行为证据",
         "结論": "本批只证明了 `removeSelectedNodes` 那处的行为；"
                 "`removeNode` 那处按「同一条路径两个半边一起改」处理，"
                 "是**一致性**修法，不是被测出来的行为"})
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


def mut_site(which_site):
    """★ 把**指定那一个**删除写点接回原形。

    783 立的纪律：行数中性 + 先验它真改到目标性质。
    ★ 这里**必须按行号**（两处 needle 完全相同），且逐行校验原文后才替换。
    """
    p = ROOT / CS
    orig = p.read_text(encoding="utf-8")
    before = orig.split("\n")
    sites = del_sites(before)
    assert len(sites) == 2, "★ 找不到两个删除写点（实得 %d）" % len(sites)
    s = sites[which_site]
    at = s["line"] - 1
    assert before[at:at + 3] == DEL_SITE_BODY, \
        "★ 第 %d 行不是预期的删除写点" % s["line"]
    after = before[:at] + DEL_SITE_MUT + before[at + 3:]
    assert len(after) == len(before), "★ 变异不是行数中性"
    p.write_text("\n".join(after), encoding="utf-8")

    # ★ 先验：变异真把「这一个」改掉了，且**另一个没被动**
    now = del_sites(after)
    ev = {"改前命中": [x["line"] for x in sites],
          "改后命中": [x["line"] for x in now],
          "行数中性": len(after) == len(before),
          "只掉一处": len(now) == 1}
    assert ev["只掉一处"] and ev["行数中性"], "★ 变异没真改到目标性质：%r" % ev
    untouched = [x["line"] for x in now]
    assert untouched != [s["line"]], "★ 被改的不是指定那一处：%r" % untouched

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

    src0, page0 = sha(ROOT / CS), sha(ROOT / "src/app/page.tsx")
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

    # ① ★★ 只把 `removeNode` 那处接回原形 ⟹ S1 必须翻（「另一个还在」是半个修复）
    # ★ 如实记账：N1/N2 会**连带**翻掉 S2 与 S4 —— 因为 S2 的条件是
    #   `len(drag)==1 and len(sites)==2`、S4 的判据是「两个不同函数」，
    #   两者都以「两处都在」为前提。这不是误报，是**同源断言的连带**。
    #   真正说明「没波及行为层」的是：S5/S6/S7/S8 仍绿（它们只读 raw）⟹
    #   raw 里**没有任何一条读数**因为源码少了半边而变化。
    negs.append(neg("N1 ★★ 只把 removeNode 那处接回原形",
                    "★ 验证 S1：同一条路径的两个半边只修一个 ⟹ 断言必须翻。"
                    "★ 本变异按**行号**定位，所以 `removeSelectedNodes` 那处"
                    "**保持已修**状态 ⟹ S5/S6/S7 仍绿（那几条只读 raw），"
                    "连带翻掉的 S2/S4 是「两处都在」这个前提的连带",
                    lambda: mut_site(0),
                    "S1:★★ 两个删除写点都在（逐行原文校验，不是子串计数）"))
    # ② ★ 另一个半边单独接回原形 ⟹ S1 也必须翻（两次变异抓的是**两处不同**的）
    negs.append(neg("N2 ★ 另一个半边（removeSelectedNodes）单独接回原形",
                    "★ 验证 S1 的另一半：N1 与 N2 分别打掉不同的那一处，"
                    "两次都必须翻 ⟹ 说明断言盯的是**两处**而不是某一处",
                    lambda: mut_site(1),
                    "S1:★★ 两个删除写点都在（逐行原文校验，不是子串计数）"))
    # ③ ★ 打断 793 的拖拽收口 ⟹ S2 必须翻（同一文件多处编辑的原子性）
    negs.append(neg("N3 ★ 打断 793 的拖拽收口那处",
                    "★ 验证 S2：两处删除路径加进来时**不能**把 793 那半边弄坏",
                    mut_drag_site, "S2:★ 793 的拖拽收口那处仍然挂着"))

    # ④ post 的「框收拢了」被翻成「框没动」⟹ S5 必须翻
    def post_no_move():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "groupTwoDeleteOne":
                        r["after"]["groupStore"] = dict(r["before"]["groupStore"])
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 ★ post 的「框收拢了」被翻成「框没动」",
                    "★ 验证 S5：post 的框变化这个读数**被真读了**"
                    "（翻平之后 pre 与 post 就没区别，修复等于没发生）",
                    post_no_move,
                    "S5:★★ pre 框不动、post 框收拢，且 post 精确等于独立重算的贴合值"))

    # ⑤ ★ post 的框被改成「不是贴合值」（但仍然 ≠ 旧框）⟹ S5 的**贴合值**半边翻
    def post_wrong_fit():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "groupTwoDeleteOne":
                        g = r["after"]["groupStore"]
                        g["w"] = g["w"] + 40      # 动了，但不是贴合值
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 ★★ post 的框被改成「动了但不是贴合值」",
                    "★ 验证 S5 的**独立重算**半边：只判「框变了」的话，"
                    "一个把框硬塞成任意尺寸的实现也能过",
                    post_wrong_fit,
                    "S5:★★ pre 框不动、post 框收拢，且 post 精确等于独立重算的贴合值"))

    # ⑥ ★ 撤销臂的「框复原了」被翻成「框没复原」⟹ S6 必须翻
    def undo_no_frame():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "groupTwoDeleteOneUndo":
                        r["after"]["groupStore"] = dict(
                            r["afterDelete"]["groupStore"])
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N6 ★ 撤销臂的「框复原了」被翻成「框没复原」",
                    "★ 验证 S6：撤销必须把**框**也带回来，只带成员是半个修复",
                    undo_no_frame,
                    "S6:★★ 撤销臂：成员与**框**都回来，且 past 真的退了一格"))

    # ⑦ ★ 撤销臂的 past 被翻成「没退」⟹ S6 必须翻（撤销没真的发生）
    def undo_no_past():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "groupTwoDeleteOneUndo":
                        r["after"]["past"] = r["afterDelete"]["past"]
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N7 ★ 撤销臂的 past 被翻成「没退」",
                    "★ 验证 S6 的历史半边：撤销臂不能只靠「框复原了」"
                    "蒙混过关，history 必须真的退了一格",
                    undo_no_past,
                    "S6:★★ 撤销臂：成员与**框**都回来，且 past 真的退了一格"))

    # ⑧ ★ 前置对照被翻成「造出来的框本来就不贴合」⟹ S7 必须翻
    def front_bad():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "groupTwoNoDelete":
                        r["state"]["groupStore"]["h"] = \
                            r["state"]["groupStore"]["h"] + 11
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N8 ★ 前置对照的「造出的框本来就贴合」被翻掉",
                    "★ 验证 S7：若造组那一步本身就不贴合，"
                    "「处理臂的框变了」就不能归因给本批的修复",
                    front_bad, "S7:★ 前置对照：造出的两成员框就是贴合值，两阶段一致"))

    # ⑨ ★★ 给 `removeNode` 造一个 UI 调用者 ⟹ S11 必须翻（「零调用者」要真被盯着）
    # ★ S11 只读 `page.tsx`，raw 变异翻不动它 ⟹ 必须有一条**作用于源码**的对照。
    def add_remove_node_caller():
        p = ROOT / "src/app/page.tsx"
        orig = p.read_text(encoding="utf-8")
        # ★ 用正则定位、不手写缩进（手写缩进踩过一次：真实是 10 空格不是 12）
        ms = list(re.finditer(r"^(\s*)removeSelectedNodes\(selection\.nodeIds\);$",
                              orig, re.M))
        assert len(ms) == 1, "★ needle 命中 %d 行" % len(ms)
        # ★ 接在**同一行**末尾（不新起一行）⟹ 行数天然中性
        at = ms[0].end() - 1
        new = (orig[:at] +
               " void useCanvasStore.getState().removeNode(selection.nodeIds[0]);"
               + orig[at:])
        assert len(new.split("\n")) == len(orig.split("\n")), "★ 变异不是行数中性"
        p.write_text(new, encoding="utf-8")
        txt = p.read_text(encoding="utf-8")
        ev = {"行数中性": len(txt.split("\n")) == len(orig.split("\n")),
              "removeNode 调用数": len(re.findall(
                  r"(?<!Selected)removeNode\(", txt))}
        assert ev["removeNode 调用数"] == 1, \
            "★ 变异没真改到目标性质：%r" % ev

        def restore():
            p.write_text(orig, encoding="utf-8")
        return restore, ev

    negs.append(neg("N9 ★★ 给 `removeNode` 造一个 UI 调用者",
                    "★ 验证 S11：「`removeNode` 零调用者」这个限定必须被**真盯着**。"
                    "★ 它只读 page.tsx，raw 变异翻不动 ⟹ 这条对照是唯一能翻它的",
                    add_remove_node_caller,
                    "S11:★★ 限定：Delete 键只走 `removeSelectedNodes`，"
                    "`removeNode` 在画布 UI 上零调用者"))

    # ★ 阴性对照跑完，源码 / raw 必须**字节级**复原
    restored = {"src": sha(ROOT / CS) == src0,
                "page": sha(ROOT / "src/app/page.tsx") == page0,
                "pre": sha(PRE) == pre0, "post": sha(POST) == post0}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    ok = all(n["ok"] for n in negs)
    out = {
        "batch": 794,
        "verdict": "PASS" if ok else "FAIL",
        "baseline": {"checks": checks,
                     "passed": nPos, "failed": len(checks) - nPos},
        "negative": negs,
        "negativeSummary": {"total": len(negs),
                            "passed": sum(1 for n in negs if n["ok"])},
        "restoreSha": {"src": src0, "page": page0, "pre": pre0, "post": post0,
                       "ok": restored},
    }
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                      encoding="utf-8")

    print("★ 794 验收：%d/%d 断言通过" % (nPos, len(checks)))
    for c in checks:
        print("   %s %s" % ("OK " if c["ok"] else "FAIL", c["id"]))
    print("★ 阴性对照 %d/%d" % (sum(1 for n in negs if n["ok"]), len(negs)))
    for n in negs:
        print("   %s %s → 翻了 %r"
              % ("OK " if n["ok"] else "FAIL", n["name"], n["flipped"]))
    print("★ 阴性对照后字节级复原：%r" % restored)
    print("wrote %s" % REPORT)
    return 0 if ok else 1


def mut_drag_site():
    """★ 打断 793 的**拖拽收口**那处（按实参定位，不写死行号）。

    行数中性：只把调用处的函数名改掉一个字符 ⟹ 行数天然不变。
    ★ 判据用 `fitStoryboardGroupsToChildren\\(` （名字后紧跟左括号），
    所以 `...ToChildrenNoOp(` **不会**被误判成「还在」——这一点很关键，
    否则这个阴性对照会假绿。
    """
    p = ROOT / CS
    orig = p.read_text(encoding="utf-8")
    before = orig.split("\n")
    at = None
    for i, l in enumerate(before):
        if (l.strip() == "nodes: fitStoryboardGroupsToChildren("
                and "plan.nextNodes" in before[i + 1]):
            at = i
            break
    assert at is not None, "★ 找不到拖拽收口那处"
    assert len(before[at + 1]) > 0, "★ 第 %d 行后无实参" % (at + 1)
    after = list(before)
    after[at] = after[at].replace("fitStoryboardGroupsToChildren(",
                                 "fitStoryboardGroupsToChildrenNoOp(")
    assert len(after) == len(before), "★ 变异不是行数中性"
    joined = "\n".join(after)
    p.write_text(joined, encoding="utf-8")
    ev = {"行": at + 1,
          "行数中性": len(after) == len(before),
          "拖拽收口还在": len(re.findall(
              r"nodes: fitStoryboardGroupsToChildren\(\n"
              r"\s*plan\.nextNodes\.map\(withoutStoredNodeSelection\),",
              joined)) == 1,
          "删除写点数": len(del_sites(after))}
    assert not ev["拖拽收口还在"] and ev["删除写点数"] == 2, \
        "★ 变异没真改到目标性质：%r" % ev

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, ev


if __name__ == "__main__":
    sys.exit(main())
