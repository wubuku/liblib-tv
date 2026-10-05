#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 792 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

792 改了 `src/store/canvasStore.ts` 的 `groupSelectedNodes`，结论是
「跨分组多选不再静默掏空已有分组」。

- ★ 这是一个**静默数据丢失**类结论，所以「没人被掏空」必须由**结构**判定
  （每个旧组的 children 逐组比对），不能只看「新组成功了」（S4/S6）。
- ★ 最容易的糊弄是「少收一点就说不破坏」。所以新组的 children 数量
  **必须**被钉住：pre 8 / post 7（S4）⟹ 否则一个「干脆不组」也能过 S4。
- ★ **两个阳性对照**缺一不可（S5）：
  「组 + 自己成员」= 零变化；「两个散节点」= children 2。
  少了后者，一个「让 `G` 什么都不做」的修复能同时满足 S4 与 S6。
- ★ **基线陷阱**（756 的原话）：「本来就空」的组不能被算成受害者（S6）。
- ★ 选区是 store 摆的 ⟹ 必须读回 `selectedNodeIds` 长度，否则
  「我以为我选中了」和「我真的选中了」无法区分（S3）。
- ★ 源码变异必须能翻掉结论（N1），且**字节级复原**（S11）。

## 静态层为什么算「独立」

汇编器用**行锚定**找三处源码并硬编码 `ARMS`；
本验收器用**正则**在整份源码里**自行定位**两处判据，并从 raw 的
`before`/`after` 的 groups 结构**重新算**谁被掏空 ⟹ 两边写错会互相抓出来。
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch792-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb792a-pre.json"
POST = OUTDIR / "raw/vb792a-post.json"

CS = "src/store/canvasStore.ts"
PAGE = "src/app/page.tsx"

ARMS = ["selectAllThenG", "groupPlusMember", "twoLoose"]
WANT_SEL = {"selectAllThenG": 10, "groupPlusMember": 2}


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def drained(cell):
    """★ 从 before/after 的 groups **重算**哪些旧组的成员变少了。"""
    b, a = cell.get("before"), cell.get("after")
    if not isinstance(b, dict) or not isinstance(a, dict):
        return None
    bk = {g["id"]: len(g.get("kids") or []) for g in b.get("groups", [])}
    ak = {g["id"]: len(g.get("kids") or []) for g in a.get("groups", [])}
    lost = sorted(k for k in bk if k in ak and ak[k] < bk[k])
    newg = sorted(k for k in ak if k not in bk)
    return {"lost": lost,
            "newKids": [ak[k] for k in newg],
            "nodeDelta": a.get("nodeCount", 0) - b.get("nodeCount", 0),
            "emptyBefore": sorted(k for k, v in bk.items() if v == 0),
            "sel": cell.get("selectedBeforeG"),
            "toast": cell.get("toastCount")}


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / CS).read_text(encoding="utf-8")
    lines = src.split("\n")

    def hits(needle):
        return [i + 1 for i, l in enumerate(lines) if needle in l]

    # ── S1：新增的那条闸在，且旧过滤仍在 ──
    guard = hits('!selectedGroupIds.has(node.parentId ?? "")')
    old = hits('node.type !== "storyboard-group"')
    collect = hits("const selectedGroupIds = new Set(")
    add("S1:新增闸在、既有过滤仍在（正则定位）",
        "★ 修法是「**只**堵破坏」：既有的「分组不参与组合」必须**保留**",
        len(guard) == 1 and len(old) == 1 and len(collect) == 1,
        {"guard": guard, "typeFilter": old, "collect": collect})

    # ── S2：★ 修复点必须在 `groupSelectedNodes` 里面，不是别处 ──
    #   同一个文件里有 `ungroupSelectedNodes` 等多个函数 ⟹ 光「文件里有一行」
    #   不够，要证明它落在**组合**这个函数体内。
    # ★ R25：`src.find(...)` 返回的是**字符偏移**，不是行号 ⟹ 第一版拿它
    #   直接和行号比，量纲都不同，判据恒假。
    fn = src.find("groupSelectedNodes: (nodeIds) => {")
    fn_line = whole_line(src, fn) if fn > 0 else -1
    guard_line = guard[0] if guard else -1
    add("S2:★ 修复点落在 `groupSelectedNodes` 函数体内",
        "★ 同一个文件里有多个 `…SelectedNodes` 实现，只断言「文件里有一行」"
        "会把别处的同名行也算进来（750 立过的「同一模式出现多次先数清有几处」）；"
        "★ 两边都必须换算成**行号**再比",
        fn_line > 0 and guard_line > fn_line
        and guard_line - fn_line < 60,
        {"fnLine": fn_line, "guardLine": guard_line,
         "delta": (guard_line - fn_line) if fn_line > 0 and guard_line > 0
                  else None})

    # ── S3：★ 选区前置条件被读到 ──
    pre, post = index(pre_raw), index(post_raw)
    sel_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, want in WANT_SEL.items():
            for c in idx.get(arm, []):
                d = drained(c)
                if not d or d["sel"] != want:
                    sel_bad.append({"phase": name, "arm": arm,
                                    "sel": d and d["sel"], "want": want})
    add("S3:★ 选区前置条件被读到",
        "★ 选区是 `selectNodes` 摆的 ⟹ 必须读回长度；"
        "「我以为我选中了」和「我真的选中了」不是一回事",
        not sel_bad, {"bad": sel_bad, "want": WANT_SEL})

    # ── S4：★ pre 掏空 / post 不掏空，且新组 children 钉死 8 → 7 ──
    p = [drained(c) for c in pre.get("selectAllThenG", [])]
    q = [drained(c) for c in post.get("selectAllThenG", [])]
    add("S4:★ pre 掏空 1 个组、post 零个，且新组 children 8 → 7",
        "★ 「少收一点就说不破坏」是最容易的糊弄 ⟹ 新组 children 数量"
        "**必须**钉住（pre 8 / post 7）",
        len(p) == 2 and len(q) == 2
        and all(x and len(x["lost"]) == 1 and x["newKids"] == [8] for x in p)
        and all(x and not x["lost"] and x["newKids"] == [7] for x in q),
        {"pre": p, "post": q})

    # ── S5：★★ 两个阳性对照前后都不变 ──
    ctrl_bad = []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("groupPlusMember", []):
            d = drained(c)
            if not (d and not d["lost"] and not d["newKids"]
                    and d["nodeDelta"] == 0):
                ctrl_bad.append({"phase": name, "arm": "groupPlusMember",
                                 "got": d})
        for c in idx.get("twoLoose", []):
            d = drained(c)
            if not (d and not d["lost"] and d["newKids"] == [2]
                    and d["nodeDelta"] == 1):
                ctrl_bad.append({"phase": name, "arm": "twoLoose", "got": d})
    add("S5:★★ 两个阳性对照前后都不变",
        "★ 「组 + 自己成员」= 零变化；「两个散节点」= 节点 +1、新组 children 2。"
        "★ 少了后者，一个「让 `G` 什么都不做」的修复能同时满足 S4 与 S6",
        not ctrl_bad, {"bad": ctrl_bad})

    # ── S6：★★ 基线里「本来就空」的组没被算成受害者 ──
    base_bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("selectAllThenG", []):
            d = drained(c)
            if not d:
                base_bad.append({"phase": name, "why": "读数缺失"})
                continue
            mis = [k for k in d["lost"] if k in d["emptyBefore"]]
            ev.append({"phase": name, "lost": d["lost"],
                       "emptyBefore": d["emptyBefore"], "misread": mis})
            if mis:
                base_bad.append({"phase": name, "misread": mis})
            if (name == "pre" and len(d["lost"]) != 1) or \
                    (name == "post" and d["lost"]):
                base_bad.append({"phase": name, "lost": d["lost"]})
    add("S6:★★ 基线里「本来就空」的组没被算成受害者",
        "★ 756 的原话：「如果只看操作后的快照，会把『本来就空』"
        "误读成『被操作掏空』」⟹ 种子里 2 个组有 1 个本来就 0 成员",
        not base_bad, {"bad": base_bad, "evidence": ev})

    # ── S7：★ 零提示这件事**没有**被改变（遗留项要如实记账）──
    toasts = {}
    for name, idx in (("pre", pre), ("post", post)):
        toasts[name] = [drained(c).get("toast") if drained(c) else None
                        for c in idx.get("selectAllThenG", [])]
    add("S7:★ 零提示**没有**被改变（如实记账）",
        "★ 本批修的是「不再破坏」，**没有**加任何提示 ⟹ "
        "「选中里有分组时用户仍然得不到告知」是**遗留**项，不能被本批的绿盖住",
        toasts.get("pre") == [0, 0] and toasts.get("post") == [0, 0],
        toasts)

    # ── S8：选区确实是 store 摆的（不是框选）──
    pg = (ROOT / PAGE).read_text(encoding="utf-8")
    add("S8:★ 画布是 `selectionOnDrag={false}`（所以框选不可用）",
        "★ 这是选区**必须**用 store 摆的依据：第一版探针照 756 的手势拖，"
        "三条臂全读成空读数（选区 0 / 1 / 节点Δ 0）",
        "selectionOnDrag={false}" in pg, None)

    # ── S9：两轮一致 ──
    same = []
    for name, idx in (("pre", pre), ("post", post)):
        for arm, lst in idx.items():
            ds = [drained(c) for c in lst]
            same.append(len(ds) == 2 and ds[0] == ds[1])
    add("S9:两轮逐臂完全一致", "★ 6 格每格两轮读数相同 ⟹ 不是抖动",
        len(same) == 6 and all(same), {"perCell": len(same),
                                       "allSame": all(same)})

    if audit:
        add("S10:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S10:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


def whole_line(src, idx):
    return src[:idx].count("\n") + 1


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

    # ① 源码：把新增的闸拆掉 ⟹ S1/S2 必须翻
    negs.append(neg("N1 新增的闸被拆掉",
                    "★ 验证 S1/S2：闸是**唯一**的改动点，拆掉它源码侧必须判红",
                    lambda: mut_src(
                        '&& !selectedGroupIds.has(node.parentId ?? ""),',
                        '&& true,'),
                    "S1:新增闸在、既有过滤仍在（正则定位）"))
    # ② pre 的受害者被抹平 ⟹ S4/S6 必须翻
    def pre_no_loss():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "selectAllThenG":
                        b = {(g["id"]): g for g in r["before"]["groups"]}
                        for g in r["after"]["groups"]:
                            if g["id"] in b:
                                g["kids"] = list(b[g["id"]]["kids"])
                        n += 1
            return n
        return mut_raw("pre", go)
    negs.append(neg("N2 pre 的受害者被抹平",
                    "★ 验证 S4/S6：「pre 确实有人被掏空」这个读数**被真读了**"
                    "（抹平之后 pre 与 post 就没区别，修复等于没发生）",
                    pre_no_loss,
                    "S4:★ pre 掏空 1 个组、post 零个，且新组 children 8 → 7"))
    # ③ post 的「两个散节点」被翻坏 ⟹ S5 必须翻
    def break_two_loose():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "twoLoose":
                        for g in r["after"]["groups"]:
                            g["kids"] = g["kids"][:1]
                        r["after"]["nodeCount"] = r["before"]["nodeCount"]
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N3 post 的「两个散节点」被翻坏",
                    "★ 验证 S5：正常组合**仍能成**这件事必须**真的**在读，"
                    "否则一个「让 `G` 什么都不做」的修复也能全绿",
                    break_two_loose,
                    "S5:★★ 两个阳性对照前后都不变"))
    # ④ 选区长度被改 ⟹ S3 必须翻
    def sel_flip():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "selectAllThenG":
                        r["selectedBeforeG"] = 1
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 选区长度被改成 1",
                    "★ 验证 S3：选区是 store 摆的，必须读回长度，"
                    "否则「我以为我选中了」和「我真的选中了」分不开",
                    sel_flip,
                    "S3:★ 选区前置条件被读到"))
    # ⑤ 基线里「本来就空」的组被改成一个有成员的组 ⟹ S6 必须翻
    def empty_baseline_lie():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "selectAllThenG" and r.get("baseline"):
                        for g in r["baseline"]["groups"]:
                            if not g["kids"]:
                                g["kids"] = ["fake-kid"]
                                n += 1
                        r["before"] = r["baseline"]
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 基线里「本来就空」的组被改成有成员",
                    "★ 验证 S6：受害者必须与基线**对照**才算数，"
                    "否则「本来就空」的组会被算成受害者",
                    empty_baseline_lie,
                    "S6:★★ 基线里「本来就空」的组没被算成受害者"))

    fp_src = (ROOT / CS).read_bytes()
    fp = {p: p.read_bytes() for p in (PRE, POST)}
    drifted = (ROOT / CS).read_bytes() != fp_src
    raw_drift = sorted(p.name for p, b in fp.items() if p.read_bytes() != b)
    checks.append({
        "id": "S11:阴性对照已复原（源码 + raw，字节级）",
        "desc": "★ N1 改过 `src/store/canvasStore.ts` ⟹ 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg, nCaught = len(negs), sum(1 for n in negs if n["ok"])
    REPORT.write_text(json.dumps(
        {"batch": 792, "checks": checks,
         "totals": {"checks": len(checks), "passed": nPos,
                    "failed": len(checks) - nPos},
         "negativeControls": {"total": nNeg, "caught": nCaught,
                              "detail": negs}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== batch 792 验收 ===")
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
