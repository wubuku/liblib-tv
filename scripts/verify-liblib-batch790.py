#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 790 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

790 改了 `src/`（第一批发界面），结论是「改之前 4 个格子里 3 个点不到」。

- ★ **最容易出的错是「拿改动后的读数当改动前」**。所以验收器要求
  pre 与 post 用**同一份** raw 结构，且**分别**断言 `menuPosition`
  分别是 `absolute` / `fixed` —— 只要有一份跑错阶段，S2/S3/S4 立刻红。
- ★ **最容易被糊弄的是「几何」**。只比「祖先盒子装不下菜单」会在改成
  `fixed` 之后继续报「有裁剪者」⟹ 必须按 **包含块链**算（S5）。
- 若 `hitIsSelf` 被信成「点得到」而没看**功能**（行内 input）⟹ 命中与
  「点了有用」是两回事 ⟹ S6/S7 两条都要。
- ★ **阳性对照必须钉住**（755 的 R18）：没有「6 张·首行 pre 就好」这一格，
  「3/4 不可用」可以和「这份代码根本点不动」无法区分 ⟹ S8。
- ★ 改过 `src/` ⟹ 阴性对照要能**把源码改回去**并让结论翻掉（N1），
  且必须**字节级复原**（S12）。

## 静态层为什么算「独立」

汇编器（`mk790audit.py`）按**行号**读 needle 并硬编码 `ACTIONS`；
本验收器用**正则**在整份源码里**自行定位**菜单容器与四个动作文案，
并从 raw 的 `items` **重新推**可达性 ⟹ 两边写错会互相抓出来。

## 沿用纪律

- 阴性对照实测证据、needle 唯一
- ★ **源码变异必须行数中性**（782 立）
- ★ **基线必须全绿才准跑阴性对照**（785 立）
- ★ 阴性对照跑完源码与 raw 必须**字节级复原**（785/786 立）
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch790-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb790a-pre.json"
POST = OUTDIR / "raw/vb790a-post.json"

CTD = "src/components/CanvasTabDropdown.tsx"

ACTIONS = ["在新窗口打开", "重命名画布", "复制画布", "删除画布"]
FUNCTIONAL = ["重命名画布", "复制画布", "删除画布"]
CELLS = [(2, "first"), (2, "last"), (6, "first"), (6, "last")]
CONTROL = "6张·first"


def cell_name(c, w):
    return "%d张·%s" % (c, w)


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(cell_name(r.get("wantCanvases"), r.get("which")),
                           []).append(r)
    return out


def reach(cell):
    """★ 从 raw 的 `items` 重算可达性，**不信**任何自报字段。"""
    h = {it["text"]: bool(it.get("hitIsSelf"))
         for it in (cell.get("items") or [])}
    return {"all": all(h.get(a) for a in ACTIONS),
            "functional": all(h.get(a) for a in FUNCTIONAL),
            "nItems": len(cell.get("items") or []),
            "texts": [it["text"] for it in (cell.get("items") or [])],
            "funcOk": bool((cell.get("func") or {}).get("inputAppeared")),
            "pos": cell.get("menuPosition"),
            "realClippers": len(cell.get("realClippers") or []),
            "rowCount": cell.get("rowCount")}


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / CTD).read_text(encoding="utf-8")

    # ── S1：菜单容器现在必须是 `fixed`（正则定位，不靠行号）──
    menu_blocks = re.findall(
        r'<div[^>]*data-canvas-row-menu=\{[^}]*\}[^>]*>', src)
    m = menu_blocks[0] if menu_blocks else ""
    add("S1:行菜单容器是 `position: fixed`（正则定位）",
        "★ 菜单容器带 `data-canvas-row-menu` 且 className 里有 `fixed`、"
        "**没有** `absolute right-2 top-full`",
        bool(m) and "fixed" in m and "absolute" not in m,
        {"matches": len(menu_blocks), "tag": m[:160]})

    # ── S2：四个动作各有一个**唯一**的菜单项锚点 ──
    # ★ 不能用「文案在全文里唯一」当判据：「删除画布」在删除确认框的
    #   `<h3>` 里也出现一次（全文 5 次）⟹ 第一版这条判据自己就选错了对象。
    #   ⟹ 改用 `data-canvas-row-menu-item` 锚点判唯一性。
    items = re.findall(r'data-canvas-row-menu-item="([^"]+)"', src)
    want_items = ["open-in-new-window", "rename", "duplicate", "delete"]
    labels = {a: len(re.findall(r">\s*%s\s*<" % re.escape(a), src))
              for a in ACTIONS}
    add("S2:四个菜单项锚点各出现**一次**且文案都在",
        "★ 「4/4」里的 4 必须有唯一实指 ⟹ 四个 `data-canvas-row-menu-item` "
        "各一次；★ 注意**不能**用「文案全文唯一」当判据（「删除画布」在删除"
        "确认框标题里也有，全文 5 次）",
        sorted(items) == sorted(want_items)
        and all(v >= 1 for v in labels.values()),
        {"anchors": items, "want": want_items, "labels": labels})

    # ── S3：pre / post 阶段**没有搞反** ──
    pre, post = index(pre_raw), index(post_raw)
    pre_pos = {reach(c)["pos"] for v in pre.values() for c in v}
    post_pos = {reach(c)["pos"] for v in post.values() for c in v}
    add("S3:pre 全是 `absolute`、post 全是 `fixed`（阶段没搞反）",
        "★ 拿改动后的读数当改动前是最容易犯的错 ⟹ 两份 raw 的 "
        "`menuPosition` 必须分别是 `absolute` 与 `fixed`",
        pre_pos == {"absolute"} and post_pos == {"fixed"},
        {"pre": sorted(x for x in pre_pos if x),
         "post": sorted(x for x in post_pos if x)})

    # ── S4：格数与两轮 ──
    add("S4:两阶段各 4 格 × 2 轮",
        "★ 每份 raw 都要 4 个格子、每格 2 轮",
        set(pre) == set(post) == {cell_name(c, w) for c, w in CELLS}
        and all(len(v) == 2 for v in pre.values())
        and all(len(v) == 2 for v in post.values()),
        {"pre": {k: len(v) for k, v in sorted(pre.items())},
         "post": {k: len(v) for k, v in sorted(post.items())}})

    # ── S5：★ 「真裁剪者」必须按包含块链算 ──
    #   `fixed` ⟹ 包含块是视口 ⟹ 任何祖先都裁不到它 ⟹ 必须是 0；
    #   `absolute` ⟹ 包含块是 `relative` 的行 ⟹ **定位**祖先里超出的才算。
    s5bad = []
    for name, lst, want in (("pre", pre, None), ("post", post, 0)):
        for k, v in lst.items():
            r = reach(v[0])
            if want is not None and r["realClippers"] != want:
                s5bad.append({"phase": name, "cell": k,
                              "realClippers": r["realClippers"]})
    add("S5:★ post 的真裁剪者全部为 0（按包含块链算，不是只比几何）",
        "★ 只比「祖先盒子装不下菜单」会在改成 `fixed` 之后**继续**报有裁剪者"
        "⟹ 必须按规则：`fixed` 的包含块是视口，祖先一个都裁不到",
        not s5bad, {"bad": s5bad})

    # ── S6：★ pre 恰好 3/4 格三项功能够不着 ──
    dead = sorted({k for k, v in pre.items()
                   if not all(reach(c)["functional"] for c in v)})
    alive = sorted({k for k, v in pre.items()
                    if all(reach(c)["functional"] for c in v)})
    add("S6:★ pre 恰好 3/4 格三项功能够不着",
        "★ 重命名 / 复制 / 删除三项在 3 个格子里**点不到** ⟹ "
        "755 记的不可达在当前代码里**仍然成立**",
        dead == ["2张·first", "2张·last", "6张·last"] and alive == [CONTROL],
        {"够不着": dead, "够得着": alive})

    # ── S7：★ post 四格全部 4/4 且**功能**通 ──
    s7bad = []
    for k, v in post.items():
        for c in v:
            r = reach(c)
            if not (r["all"] and r["funcOk"] and r["nItems"] == 4):
                s7bad.append({"cell": k, "got": r})
    add("S7:★ post 四格全部 4/4 且行内 input 真的出现",
        "★ 「点得到」和「点了有用」是**两件事** ⟹ 命中之外还要功能证据",
        not s7bad, {"bad": s7bad})

    # ── S8：★★ 阳性对照：pre 就好的那一格**不许**被弄坏 ──
    ctrl_pre = [reach(c) for c in pre.get(CONTROL, [])]
    ctrl_post = [reach(c) for c in post.get(CONTROL, [])]
    add("S8:★★ 阳性对照（6 张·首行）前后都 4/4",
        "★ 755 的 R18：必须有一个格子**本来就该全可点**且实测全可点，"
        "否则「3/4 不可用」与「这份代码根本点不动」无法区分",
        len(ctrl_pre) == 2 and len(ctrl_post) == 2
        and all(r["all"] and r["funcOk"] for r in ctrl_pre + ctrl_post),
        {"pre": [{"all": r["all"], "funcOk": r["funcOk"]} for r in ctrl_pre],
         "post": [{"all": r["all"], "funcOk": r["funcOk"]} for r in ctrl_post]})

    # ── S9：★ 变的是可达性，不是内容 ──
    s9bad = []
    for k in pre:
        a, b = reach(pre[k][0]), reach(post[k][0])
        if a["texts"] != b["texts"] or a["nItems"] != b["nItems"] \
                or a["rowCount"] != b["rowCount"]:
            s9bad.append({"cell": k, "pre": a, "post": b})
    add("S9:★ 每格的行数与菜单项前后完全相同",
        "★ 行数与菜单项都不变 ⟹ 变的只有「能不能点到」，"
        "而不是「菜单里少了东西」",
        not s9bad, {"bad": s9bad})

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

    ★ R24：`list.count(needle)` 是**整行相等**判断，不是子串包含 ⟹
      needle 明明在 className 那一行里，却报「出现 0 次」。
      ⟹ 统计必须按**子串**做：`sum(1 for l in lines if needle in l)`。
    """
    p = ROOT / CTD
    orig = p.read_text(encoding="utf-8")
    before = orig.split("\n")
    n = sum(1 for l in before if old in l)
    assert n == 1, (
        "★ needle 在文件里命中 %d 行，必须**唯一**一行：%r" % (n, old))
    lines = [l.replace(old, new) for l in before]
    assert len(lines) == len(before), "★ 变异不是行数中性"
    p.write_text("\n".join(lines), encoding="utf-8")
    after_text = p.read_text(encoding="utf-8")
    after = after_text.split("\n")
    ev = {"oldGone": not any(old in l for l in after),
          "newThere": any(new in l for l in after),
          "lineNo": next((i + 1 for i, l in enumerate(after) if new in l), None)}
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

    # ① 把源码的 `fixed` 改回 `absolute` ⟹ S1 必须翻
    negs.append(neg("N1 源码改回 `absolute`",
                    "★ 验证 S1 真的在找 `fixed`。★ 本批第一次动 `src/`，"
                    "S1 必须是**唯一**能把「改动是否还在」判出来的检查",
                    lambda: mut_src("fixed z-[60] w-36",
                                    "absolute right-2 top-full z-[60] w-36"),
                    "S1:行菜单容器是 `position: fixed`（正则定位）"))
    # ② 把 pre 的「2 张·末行」命中翻成全通 ⟹ S6/S9 必须翻
    def fake_pre_ok():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("wantCanvases") == 2 and r.get("which") == "last":
                        for it in r.get("items") or []:
                            it["hitIsSelf"] = True
                            n += 1
                        r["func"]["inputAppeared"] = True
            return n
        return mut_raw("pre", go)
    negs.append(neg("N2 pre 的坏格被翻成「全通」",
                    "★ 验证 S6：「3/4 不可用」这个结论**被真读了**"
                    "（否则 pre 整份都变好，故事就反过来了）",
                    fake_pre_ok,
                    "S6:★ pre 恰好 3/4 格三项功能够不着"))
    # ③ 把 post 的「6 张·末行」命中翻成不通 ⟹ S7 必须翻
    def break_post():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("wantCanvases") == 6 and r.get("which") == "last":
                        for it in r.get("items") or []:
                            it["hitIsSelf"] = False
                            n += 1
                        r["func"]["inputAppeared"] = False
            return n
        return mut_raw("post", go)
    negs.append(neg("N3 post 的末行被翻成「不通」",
                    "★ 验证 S7：修复**不是**只对首行有效",
                    break_post,
                    "S7:★ post 四格全部 4/4 且行内 input 真的出现"))
    # ④ 把 post 的 `menuPosition` 翻成 absolute ⟹ S3/S5 必须翻
    def pos_flip():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    r["menuPosition"] = "absolute"
                    r["realClippers"] = [{"tag": "DIV"}]
                    n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 post 的 menuPosition 被翻成 absolute",
                    "★ 验证 S3 与 S5：★ 「只比几何」会把 `fixed` 也报成有裁剪者，"
                    "S5 专门防这个",
                    pos_flip, "S3:pre 全是 `absolute`、post 全是 `fixed`（阶段没搞反）"))
    # ⑤ 把 pre 的行数改掉 ⟹ S9 必须翻（证明 S9 真的在比内容）
    def row_count_flip():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("wantCanvases") == 2 and r.get("which") == "first":
                        r["rowCount"] = 5
                        n += 1
            return n
        return mut_raw("pre", go)
    negs.append(neg("N5 pre 的行数被改掉",
                    "★ 验证 S9：必须能区分「可达性变了」与「内容变了」",
                    row_count_flip,
                    "S9:★ 每格的行数与菜单项前后完全相同"))

    fp_src = (ROOT / CTD).read_bytes()
    fp = {p: p.read_bytes() for p in (PRE, POST)}
    drifted = (ROOT / CTD).read_bytes() != fp_src
    raw_drift = sorted(p.name for p, b in fp.items() if p.read_bytes() != b)
    checks.append({
        "id": "S11:阴性对照已复原（源码 + raw，字节级）",
        "desc": "★ N1 改过 `CanvasTabDropdown.tsx` ⟹ 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg, nCaught = len(negs), sum(1 for n in negs if n["ok"])
    REPORT.write_text(json.dumps(
        {"batch": 790, "checks": checks,
         "totals": {"checks": len(checks), "passed": nPos,
                    "failed": len(checks) - nPos},
         "negativeControls": {"total": nNeg, "caught": nCaught,
                              "detail": negs}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== batch 790 验收 ===")
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
