#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 797 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

797 改了一个常量：`GROUP_PADDING` 32 → 40（= 2×20），让「组被吸附时成员被带离网格」
消失。结论是「吸附开着时拖组，成员仍留在网格上」。

- ★★ **判据必须是「倍数」而不是「40」**：若把断言写成「padding == 40」，
  将来有人改成 60（也是 20 的倍数、功能仍对）会被误判红。
  ⟹ H 判 `v % 20 == 0`。
- ★★ **核心臂有前提**：必须先把成员摆到网格上再拖组，否则「结果不在网格」
  不能证明什么。⟹ B 先判「拖前成员在网格」，不成立直接判红。
- ★★ **必须显式作废 `dragGroupSnapOn` 那条臂**（G）：它拖之前成员就不在网格，
  「结果不在网格」**不构成缺陷证据」。不做这件事，后人会读成「post 也没修好」。
- ★ **阳性对照不可省**（E）：吸附关时成员也必须不在网格，否则「成员在网格上」
  可能只是「本来就在」，post 的结论就没有意义。
- ★ 修 793 验收器的**过时断言**（`len(fn_call) == 1`）：794/795 合法加了写点后
  它永久变红 ⟹ 验收器红着就不能再信它。
"""
import ast
import hashlib
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch797-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
PRE = OUTDIR / "raw/vb797a-pre.json"
POST = OUTDIR / "raw/vb797a-post.json"
CS = "src/store/canvasStore.ts"
PAGE = "src/app/page.tsx"
TOOLBAR = "src/components/BottomToolbar.tsx"

ARMS = ["dragSnapOn", "dragSnapOff", "snapToggleOnly", "dragGroupSnapOn",
        "groupDragAfterMembersSnapped"]
GRID = 20
CORE = "groupDragAfterMembersSnapped"
INVALID = "dragGroupSnapOn"


def index(raw):
    out = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            out.setdefault(r.get("arm"), []).append(r)
    return out


def on_grid(v):
    return (v % GRID) == 0


def all_grid(members):
    ms = [m for m in (members or []) if isinstance(m, dict)]
    return bool(ms) and all(
        on_grid(m["abs"]["x"]) and on_grid(m["abs"]["y"]) for m in ms)


def rel_of(members):
    """★ 相对偏移（组坐标系）—— 排序后比较，避开成员顺序不确定性。"""
    return sorted(tuple(sorted(m["pos"].items())) for m in (members or []))


def xy(m):
    g = (m or {}).get("groupStore")
    return None if not g else (g["pos"]["x"], g["pos"]["y"])


def run_checks(pre_raw, post_raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / CS).read_text(encoding="utf-8")
    page = (ROOT / PAGE).read_text(encoding="utf-8")
    toolbar = (ROOT / TOOLBAR).read_text(encoding="utf-8")
    pre, post = index(pre_raw), index(post_raw)

    # ── S1：★★ 前提：吸附**真的存在** ──
    add("S1:★★ 网格吸附真的存在（传参 + 网格值 + UI 入口）",
        "★ 若吸附还不存在，整批的立论（「吸附开着却把成员拖下网格」）就塌了",
        len(re.findall(r"snapToGrid=\{snapToGrid\}", page)) == 1
        and len(re.findall(r"snapGrid=\{\[20, 20\]\}", page)) == 1
        and len(re.findall(r'label="网格吸附"', toolbar)) == 1,
        {"snapToGrid": len(re.findall(r"snapToGrid=\{snapToGrid\}", page)),
         "snapGrid": len(re.findall(r"snapGrid=\{\[20, 20\]\}", page)),
         "UI入口": len(re.findall(r'label="网格吸附"', toolbar))})

    # ── S2：★★ 核心臂：前提成立 + pre 掉出、post 仍在 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get(CORE, []):
            b, a = c.get("before"), c.get("after")
            if not isinstance(b, dict) or not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            bg, ag = all_grid(b.get("members")), all_grid(a.get("members"))
            rel_same = rel_of(b.get("members")) == rel_of(a.get("members"))
            ev.append({"phase": name, "拖前在网格": bg, "拖后在网格": ag,
                       "相对偏移未变": rel_same,
                       "组": (xy(b), xy(a))})
            if not bg:
                bad.append(dict(ev[-1], why="★ 前提不成立：拖前成员就不在网格"))
            elif (name == "pre") == ag:
                bad.append(dict(ev[-1], why="pre 应掉出、post 应留在网格"))
            if not rel_same:
                bad.append(dict(ev[-1], why="相对偏移变了 ⟹ 机理不成立"))
    add("S2:★★ 核心臂：前提成立，拖组后 pre **掉出**网格、post **仍在**",
        "★ 先判「拖前成员在网格」这个前提，不成立直接判红 ⟹ 否则"
        "「结果不在网格」什么都不能证明。★ 相对偏移两阶段必须**未变**",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S3：★★ 相对偏移与组位置**自洽**（把机理钉死）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get(CORE, []):
            b, a = c.get("before"), c.get("after")
            if not isinstance(b, dict) or not isinstance(a, dict):
                continue
            r0, r1 = rel_of(b.get("members")), rel_of(a.get("members"))
            g0, g1 = xy(b), xy(a)
            # ★ 「相对偏移在网格上」与「组位置在网格上」必须**同时**成立
            #   （两者都在 ⟹ 成员绝对必然在）
            rel0 = all(on_grid(v) for m in b.get("members", [])
                       for v in m["pos"].values())
            rel1 = all(on_grid(v) for m in a.get("members", [])
                       for v in m["pos"].values())
            g0_ok = g0 is not None and all(on_grid(v) for v in g0)
            g1_ok = g1 is not None and all(on_grid(v) for v in g1)
            ev.append({"phase": name, "rel未变": r0 == r1,
                       "rel拖前在网格": rel0, "rel拖后在网格": rel1,
                       "组拖前在网格": g0_ok, "组拖后在网格": g1_ok})
            if r0 != r1:
                bad.append(dict(ev[-1], why="相对偏移变了"))
            if (name == "pre") != (not rel0):
                bad.append(dict(ev[-1], why="rel 的网格状态与阶段相反"))
            if (name == "post") != rel1:
                bad.append(dict(ev[-1], why="post 的 rel 应在网格上"))
            if not g1_ok:
                bad.append(dict(ev[-1], why="拖组后组位置不在网格（吸附的正是组）"))
    add("S3:★★ 相对偏移未变；rel 与组位置的网格状态自洽",
        "★ 「rel = 成员绝对 − 组位置」⟹ rel 在网格 + 组在网格 ⟹ 成员绝对必然在。"
        "★ 这条把「唯一来源是 PADDING」钉死，而不是只观测结果",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S4：★★ 阳性对照：吸附**关**时成员不在网格 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("dragSnapOff", []):
            a = c.get("after")
            if not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            snap = a.get("snapToGrid")
            on = all_grid(a.get("members"))
            ev.append({"phase": name, "snap": snap, "成员在网格": on})
            if snap is not False:
                bad.append(dict(ev[-1], why="吸附读数不是 False"))
            if on:
                bad.append(dict(ev[-1], why="★ 对照失效：吸附关却在网格上"))
    add("S4:★★ 阳性对照：吸附**关**时 `snapToGrid=False` 且成员**不在**网格",
        "★ 没有它，「成员在网格上」可能只是「本来就在」⟹ S2 的 post 无意义",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S5：★ 前置对照：只切开关不改几何 ──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get("snapToggleOnly", []):
            b, a = c.get("before"), c.get("after")
            if not isinstance(b, dict) or not isinstance(a, dict):
                bad.append({"phase": name, "why": "空读数"})
                continue
            same = xy(b) == xy(a) and \
                [m["abs"] for m in b["members"]] == \
                [m["abs"] for m in a["members"]]
            ev.append({"phase": name, "snap": a.get("snapToGrid"),
                       "几何未变": same})
            if not same or a.get("snapToGrid") is not True:
                bad.append(dict(ev[-1], why="切开关本身改了几何"))
    add("S5:★ 前置对照：只切吸附开关**不改变任何几何**",
        "★ 若切开关就动几何，S2 的变化可能来自开关而不是拖动",
        not bad and len(ev) == 4, {"bad": bad, "evidence": ev})

    # ── S6：★★ 显式作废 `dragGroupSnapOn`（前提不满足）──
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        for c in idx.get(INVALID, []):
            b = c.get("before")
            if not isinstance(b, dict):
                continue
            bg = all_grid(b.get("members"))
            ev.append({"phase": name, "拖前成员在网格": bg})
            if bg:
                bad.append({"phase": name,
                            "why": "★ 成员拖前已在网格 ⟹ 本臂应当也能判缺陷"})
    add("S6:★★ 显式作废 `dragGroupSnapOn`（它的成员**拖前就不在网格**）",
        "★ 它「拖后不在网格」**不构成缺陷证据** ⟹ 必须显式作废，"
        "否则会被读成「post 也没修好」",
        not bad and len(ev) == 4 and all(not x["拖前成员在网格"]
                                         for x in ev),
        {"bad": bad, "evidence": ev,
         "★ 该臂的定位": "前提不满足，仅作参考读数"})

    # ── S7：★★ 判据是「倍数」而不是「40」 ──
    m = re.findall(r"const GROUP_PADDING = (\d+);", src)
    v = int(m[0]) if m else None
    add("S7:★★ `GROUP_PADDING` 是网格（20）的**整数倍**",
        "★ 本批**唯一**的改动点。★ 判据写成「== 40」的话，将来有人改成 60"
        "（同样是 20 的倍数、功能仍对）会被误判红",
        v is not None and v % GRID == 0,
        {"GROUP_PADDING": v, "网格": GRID, "v % 20": (v % GRID) if v else None})

    # ── S8：★ 仍满足 793 的贴合不变量（组 = 恰好包住成员 + padding）──
    # ★★ 坑：`pre` 采于 padding=**32** 时、`post` 采于 padding=**40** 时。
    #   用**当前源码**的 padding 去算 `pre` 的贴合值必然对不上 ⟹
    #   这里按阶段各用**自己的** padding（32 / 40），从 raw 的历史推出来，
    #   而不是从源码读「现在的值」。
    PAD = {"pre": 32, "post": 40}
    bad, ev = [], []
    for name, idx in (("pre", pre), ("post", post)):
        pad = PAD[name]
        for c in idx.get(CORE, []):
            for key in ("before", "after"):
                m2 = c.get(key)
                if not isinstance(m2, dict):
                    continue
                g = (m2.get("groupStore") or {})
                ms = m2.get("members") or []
                if not g or not ms:
                    continue
                x0 = min(mm["abs"]["x"] for mm in ms)
                y0 = min(mm["abs"]["y"] for mm in ms)
                x1 = max(mm["abs"]["x"] + (mm.get("w") or 0) for mm in ms)
                y1 = max(mm["abs"]["y"] + (mm.get("h") or 0) for mm in ms)
                want = (x0 - pad, y0 - pad, x1 - x0 + pad * 2,
                        y1 - y0 + pad * 2)
                got = (g["pos"]["x"], g["pos"]["y"], g["w"], g["h"])
                ok = all(abs(a - b) <= 0.01 for a, b in zip(want, got))
                ev.append({"phase": name, "when": key, "用padding": pad,
                           "贴合值": want, "实际": got, "ok": ok})
                if not ok:
                    bad.append(ev[-1])
    add("S8:★ 仍满足 793 的贴合不变量（组 = 恰好包住成员 + padding）",
        "★ 改 padding 不许顺手破坏 793 ⟹ 贴合值用**读数 + 该阶段自己的 padding**"
        "独立重算，不依赖源码公式。★ pre 用 32、post 用 40",
        not bad and len(ev) == 8, {"bad": bad, "evidence": ev})

    # ── S9：★ 修 793 验收器的过时断言 ──
    # ★★★ 判据必须用 **ast 真正解析**、看有没有**表达式**用到那个写法。
    #   前两版都栽在「字符串匹配」上：
    #     ① 全文找子串 ⟹ 注释里「说明原来写的是什么」被判红（第一版）
    #     ② 只跳过 `#` 开头的行 ⟹ dict 的**字符串字面量**里那句仍被判红（第二版）
    #   ⟹ 只有「它出现在一段**可执行表达式**里」才算真的还在用。
    p793 = ROOT / "scripts/verify-liblib-batch793.py"
    code_old, where = False, None
    if p793.exists():
        try:
            tree = ast.parse(p793.read_text(encoding="utf-8"))
        except SyntaxError as e:
            code_old, where = True, "parse error: %s" % e
        else:
            for node in ast.walk(tree):
                if isinstance(node, ast.Compare):
                    src = ast.dump(node)
                    if "fn_call" in src and any(
                            isinstance(c, ast.Eq) for c in node.ops):
                        code_old = True
                        where = "line %d" % node.lineno
                        break
    add("S9:★★ 793 验收器的**过时断言**已修（不再写死「调用点恰好 1 处」）",
        "★ 794/795 合法加了写点后 `len(fn_call) == 1` 永久变红 ⟹ "
        "验收器红着就不能再信它。★ 判据用 **ast** 看有没有**表达式**在用它"
        "（注释与字符串字面量里的提及不算）",
        not code_old, {"793 里仍有**表达式**用 fn_call == 1": code_old,
                       "位置": where})

    # ── S10：格数与无 FAILED ──
    bad = []
    for name, idx in (("pre", pre), ("post", post)):
        if set(idx) != set(ARMS):
            bad.append({"phase": name, "arms": sorted(idx)})
        for arm, lst in idx.items():
            if len(lst) != 2:
                bad.append({"phase": name, "arm": arm, "rounds": len(lst)})
            for c in lst:
                if c.get("FAILED"):
                    bad.append({"phase": name, "arm": arm,
                                "FAILED": c.get("FAILED")})
    add("S10:两阶段各 5 臂 × 2 轮且无 FAILED",
        "★ 探针 FAILED 就是**空读数**", not bad, {"bad": bad})

    if audit:
        add("S11:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S11:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)

    add("S12:★★ 记账：本批**改了一个常量**且**有可见副作用**",
        "★ 吸附**关**时 padding 只是视觉留白，32→40 会让框**宽 8 像素** ⟹ "
        "这是**取舍**不是零成本，必须显式记下来",
        True, {"改动": "GROUP_PADDING 32 → 40", "改动点数": 1,
               "可见副作用": "吸附关时框宽 +8 像素",
               "为何选 40": "2×20，是网格整数倍；仍是整齐偶数、更贴近 8pt 栅格",
               "源站对照": "★ 未做（源站需登录）⟹ 40 是工程判断，不是源站实测值"})
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


def mut_pad(new_val):
    """★ 变异 `GROUP_PADDING` 的值（行数中性）。"""
    p = ROOT / CS
    orig = p.read_text(encoding="utf-8")
    m = re.search(r"const GROUP_PADDING = \d+;", orig)
    assert m, "★ 找不到 GROUP_PADDING"
    before = orig[:m.start()] + "const GROUP_PADDING = %d;" % new_val + \
        orig[m.end():]
    assert len(before.split("\n")) == len(orig.split("\n")), "★ 变异不是行数中性"
    p.write_text(before, encoding="utf-8")
    after = p.read_text(encoding="utf-8")
    ev = {"新值": new_val,
          "真的改了": ("const GROUP_PADDING = %d;" % new_val) in after,
          "行数中性": len(after.split("\n")) == len(orig.split("\n"))}
    assert ev["真的改了"] and ev["行数中性"], "★ 变异没真改到目标性质：%r" % ev

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, ev


def mut_text(path, old, new, label=""):
    p = ROOT / path
    orig = p.read_text(encoding="utf-8")
    assert orig.count(old) == 1, "★ needle 不唯一：%r" % old
    new_txt = orig.replace(old, new)
    assert len(new_txt.split("\n")) == len(orig.split("\n")), "★ 非行数中性"
    p.write_text(new_txt, encoding="utf-8")
    after = p.read_text(encoding="utf-8")
    ev = {"新的在": new in after, "旧的不在": old not in after, "label": label}
    assert ev["新的在"] and ev["旧的不在"], "★ 变异没真改到目标性质：%r" % ev

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
    src0, pre0, post0 = sha(ROOT / CS), sha(PRE), sha(POST)

    checks = run_checks(pre_raw, post_raw, audit)
    nPos = sum(1 for c in checks if c["ok"])
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        """★ `expect` 传 `__NO_FLIP__` 表示**反向对照**：期望**不**翻。"""
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(PRE.read_text(encoding="utf-8")),
                           json.loads(POST.read_text(encoding="utf-8")), audit)
            flipped = [x["id"] for x in c if not x["ok"]]
            if expect == "__NO_FLIP__":
                # ★ 反向对照：判据是「**没有**任何断言翻红」，
                #   否则说明把判据写死成了「必须等于 40」
                return {"name": name, "why": why, "evidence": ev,
                        "expectFlipped": "（反向对照：期望不翻）",
                        "flipped": flipped, "ok": not flipped,
                        "stillPassing": [x["id"] for x in c if x["ok"]]}
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped,
                    "stillPassing": [x["id"] for x in c if x["ok"]]}
        finally:
            restore()

    # ① ★★ padding 改回 32（**不是** 20 的倍数）⟹ S7 必须翻
    negs.append(neg("N1 ★★ `GROUP_PADDING` 改回 32",
                    "★ 验证 S7：32 **不是** 20 的倍数 ⟹ 缺陷会回来",
                    lambda: mut_pad(32),
                    "S7:★★ `GROUP_PADDING` 是网格（20）的**整数倍**"))
    # ② ★★ padding 改成 35（同样不是倍数）⟹ S7 也必须翻
    #   ★ 证明判据不是「== 40」也不是「偶数」
    negs.append(neg("N2 ★★ `GROUP_PADDING` 改成 35（奇数、非倍数）",
                    "★ 验证 S7 的判据确实是「倍数」：35 是奇数也不是 20 的倍数 ⟹ "
                    "若断言写成「偶数」就会被放过",
                    lambda: mut_pad(35),
                    "S7:★★ `GROUP_PADDING` 是网格（20）的**整数倍**"))
    # ③ ★★ padding 改成 60（**是**倍数，修复应仍成立）⟹ S7 必须仍绿
    negs.append(neg("N3 ★★ `GROUP_PADDING` 改成 60（仍是 20 的倍数）",
                    "★ 反向对照：60 是 3×20，功能上仍应成立 ⟹ "
                    "S7 **不该**翻。这一条证明判据没被写死成 40",
                    lambda: mut_pad(60), "__NO_FLIP__"))
    # ④ ★★ post 的「成员留在网格上」被翻成「掉出去了」⟹ S2 必须翻
    def members_off():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == CORE:
                        for m in r["after"]["members"]:
                            m["abs"] = {"x": m["abs"]["x"] + 8,
                                        "y": m["abs"]["y"] - 8}
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N4 ★★ post 的「成员留在网格上」被翻成「掉出去了」",
                    "★ 验证 S2 的核心半边：post 的结论必须靠这条撑着",
                    members_off,
                    "S2:★★ 核心臂：前提成立，拖组后 pre **掉出**网格、post **仍在**"))
    # ⑤ ★★ 把核心臂的**前提**破坏（拖前成员就不在网格）⟹ S2 必须翻
    def break_premise():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == CORE:
                        for m in r["before"]["members"]:
                            m["abs"] = {"x": m["abs"]["x"] + 3,
                                        "y": m["abs"]["y"] + 7}
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N5 ★★ 破坏核心臂的**前提**（拖前成员就不在网格）",
                    "★ 验证 S2 的前提守卫：若不判「拖前在网格」，"
                    "「结果不在网格」什么都不能证明",
                    break_premise,
                    "S2:★★ 核心臂：前提成立，拖组后 pre **掉出**网格、post **仍在**"))
    # ⑥ ★★ 阳性对照翻成「吸附关也在网格」⟹ S4 必须翻
    def control_fake():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") == "dragSnapOff":
                        for m in r["after"]["members"]:
                            m["abs"] = {"x": 20 * round(m["abs"]["x"] / 20),
                                        "y": 20 * round(m["abs"]["y"] / 20)}
                        n += 1
            return n
        return mut_raw("post", go)
    negs.append(neg("N6 ★★ 阳性对照被翻成「吸附关也在网格」",
                    "★ 验证 S4：若对照能假绿，post 的「在网格上」就失去对照",
                    control_fake,
                    "S4:★★ 阳性对照：吸附**关**时 `snapToGrid=False` 且成员**不在**网格"))
    # ⑦ ★★ 破坏吸附的**存在性** ⟹ S1 必须翻
    #   ★ 删掉整行会**破坏行数中性**（782 立的纪律）⟹ 改成把网格值换掉，
    #   断言 S1 的两个条件（传参 + `snapGrid=[20,20]`）随之不成立。
    negs.append(neg("N7 ★★ 把 `snapGrid` 换成别的值",
                    "★ 验证 S1：整批的立论是「吸附开着、网格是 20」⟹ "
                    "换成别的网格后 S1 必须翻",
                    lambda: mut_text(PAGE, "snapGrid={[20, 20]}",
                                     "snapGrid={[13, 13]}", label="换网格"),
                    "S1:★★ 网格吸附真的存在（传参 + 网格值 + UI 入口）"))
    # ⑧ ★★ 把 793 验收器里那个**过时写法**作为代码行放回去 ⟹ S9 必须翻
    p793 = ROOT / "scripts/verify-liblib-batch793.py"
    p793_orig = p793.read_text(encoding="utf-8")
    # ★ 必须插成**真实代码行**（不是注释）⟹ S9 判据跳过注释，只看代码
    p793.write_text(
        p793_orig + "\nif len(fn_call) == 1:\n    pass\n",
        encoding="utf-8")
    try:
        c = run_checks(json.loads(PRE.read_text(encoding="utf-8")),
                       json.loads(POST.read_text(encoding="utf-8")), audit)
        flipped = [x["id"] for x in c if not x["ok"]]
        negs.append({"name": "N8 ★★ 把 793 的过时写法放回去",
                     "why": "★ 验证 S9：验收器红着就不能再信它",
                     "evidence": {"放回": "len(fn_call) == 1"},
                     "expectFlipped": "S9:★★ 793 验收器的**过时断言**已修"
                                      "（不再写死「调用点恰好 1 处」）",
                     "flipped": flipped,
                     "ok": "S9:★★ 793 验收器的**过时断言**已修"
                            "（不再写死「调用点恰好 1 处」）" in flipped,
                     "stillPassing": [x["id"] for x in c if x["ok"]]})
    finally:
        p793.write_text(p793_orig, encoding="utf-8")

    restored = {"cs": sha(ROOT / CS) == src0, "pre": sha(PRE) == pre0,
                "post": sha(POST) == post0,
                "793verifier": sha(p793) == hashlib.sha256(
                    p793_orig.encode("utf-8")).hexdigest()}
    assert all(restored.values()), "★ 阴性对照后文件没复原：%r" % restored

    # ★ `neg()` 已把反向对照的判定收进 `n["ok"]` ⟹ 这里直接汇总
    negs_ok = sum(1 for n in negs if n["ok"])
    ok = all(n["ok"] for n in negs)
    out = {
        "batch": 797, "verdict": "PASS" if ok else "FAIL",
        "baseline": {"checks": checks, "passed": nPos,
                     "failed": len(checks) - nPos},
        "negative": negs,
        "negativeSummary": {"total": len(negs), "passed": negs_ok},
        "restoreSha": {"cs": src0, "pre": pre0, "post": post0,
                       "ok": restored},
    }
    REPORT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                      encoding="utf-8")
    print("★ 797 验收：%d/%d 断言通过" % (nPos, len(checks)))
    for c in checks:
        print("   %s %s" % ("OK " if c["ok"] else "FAIL", c["id"]))
    print("★ 阴性对照 %d/%d" % (negs_ok, len(negs)))
    for n in negs:
        print("   %s %s → 翻了 %r"
              % ("OK " if n["ok"] else "FAIL", n["name"], n["flipped"]))
    print("★ 阴性对照后字节级复原：%r" % restored)
    print("wrote %s" % REPORT)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
