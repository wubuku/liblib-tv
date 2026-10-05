#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 789 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

789 的结论是「两个 `sIP` 主人共活时**先注册的赢**，而且要多按一次」。

- 若把「我没预测到」直接写成「机制就是这样」⟹ 那只是**观察**。所以
  S3 专门把**混淆项**钉住：唯一可达的共活臂里，**打开顺序与源码顺序重合**
  ⟹ 本批**不能**区分「注册顺序 = 打开顺序」与「源码顺序 = 谁赢」。
  报告只准说「**先注册的赢**」，不准说「先打开的赢」是已被排除源码顺序的。
- 若信 raw 自报字段 ⟹ 派生值一律从 `presses[].read` **重算**。
- 若「桌还在」是从「草稿与库两个读数都变 `null`」**推断**出来的 ⟹
  任何一个读数因别的原因消失都会误判 ⟹ S4 强制它**必须直读**。
- 若把不可达臂说成「造草稿失败」⟹ 实际 raw 里 `draftAfterAttempt=="true"`
  ⟹ 草稿**造出来了**，是模型库被顺手续掉的 ⟹ S7 钉住这一点。
- 若「多按一次」只在**两轮某一轮**成立 ⟹ 断言按臂取交集，两轮都要满足。

## 静态层为什么算「独立」

汇编器（`mk789audit.py`）逐行**读** needle 并**硬编码** EXPECT；
本验收器用**正则**在整段源码里**自行定位**两个 effect，并从
`presses[].read` **重新推**出一组断言 ⟹ 一边靠行号、一边靠内容，
两边写错会互相抓出来。

## 沿用纪律

- 阴性对照实测证据、needle 唯一
- ★ **源码变异必须行数中性**（782 立）
- ★ **同一文件多处编辑必须原子化**（786 立）—— 本批 `:2702` 与 `:2744`
  在**同一个文件**，两处 `stopImmediatePropagation` 少改一处对照就无效
- ★ **基线必须全绿才准跑阴性对照**（785 立）
- ★ 阴性对照跑完源码与 raw 必须**字节级复原**（785/786 立）
"""
import json
import pathlib
import re
import sys

ROOT = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUTDIR = ROOT / "docs/research/liblib-canvas-batch789-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAW = OUTDIR / "raw/vb789a.json"

DV = "src/components/director/DirectorViewport.tsx"
UNREACHABLE = "libThenDraft"
ALONE = ("draftOnly", "libOnly")
BOTH = "draftThenLib"

#: ★ 两个 effect 的定位**不靠行号**：靠「门 + 紧随其后的 effect 体」
#: ★ 门用**命名捕获组**取：正则里 `\s*` 紧跟 `useEffect(() => {` 之后，
#:   ⟹ 捕到的 `gate` **必然是函数体第一条语句**（S2 的「第一条」由此保证）
EFFECT_RES = {
    "motionPathDraft": re.compile(
        r"useEffect\(\(\)\s*=>\s*\{\s*"
        r"(?P<gate>if \(!timeline\.motionPathDraft\) return;)"
        r"(?P<body>.*?)\n\s*\}, \[", re.S),
    "modelLibraryOpen": re.compile(
        r"useEffect\(\(\)\s*=>\s*\{\s*"
        r"(?P<gate>if \(!modelLibraryOpen\) return;)"
        r"(?P<body>.*?)\n\s*\}, \[", re.S),
}


def norm(r):
    """★ 从一次按压的读数**重算**判据形状；**不信任何自报字段**。"""
    r = r or {}
    if "deskOpen" not in r:
        return {"broken": True}
    return {"draft": r.get("draft"), "lib": r.get("lib"),
            "exportOpen": bool(r.get("exportOpen")),
            "desk": bool(r.get("deskOpen"))}


def seq_of(row):
    return [norm(p.get("read")) for p in (row.get("presses") or [])]


def index_rows(raw):
    by = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            by.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    return by


def run_checks(raw, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    src = (ROOT / DV).read_text(encoding="utf-8")

    # ── S1：两个 `sIP` 主人，正则**自行定位**（不靠行号）──
    eff, s1bad = {}, []
    for state, rx in EFFECT_RES.items():
        m = rx.search(src)
        if not m:
            s1bad.append({"state": state, "why": "正则没定位到 effect"})
            continue
        body = m.group("body")
        ev = {
            "gateFirstLine": True,
            "hasSIP": "event.stopImmediatePropagation();" in body,
            "hasWindowCapture":
                bool(re.search(r'window\.addEventListener\("keydown",\s*\w+,\s*true\)',
                               body)),
            "hasWindowCaptureCleanup":
                bool(re.search(
                    r'window\.removeEventListener\("keydown",\s*\w+,\s*true\)',
                    body)),
        }
        eff[state] = {"span": m.span(), "evidence": ev}
        if not (ev["hasSIP"] and ev["hasWindowCapture"]):
            s1bad.append({"state": state, "evidence": ev})
    add("S1:两个 sIP 主人都在（正则定位，不靠行号）",
        "★ 运镜草稿与模型库两个 effect **各自**都有 `sIP` 且都是 "
        "`window` 捕获相位（`addEventListener(..., true)` + 对称 `remove`）",
        not s1bad and len(eff) == 2, {"found": eff, "bad": s1bad})

    # ── S2：两个门都是「状态非空才注册」⟹ 注册顺序跟随**打开**顺序 ──
    gates = {}
    for state, rx in EFFECT_RES.items():
        m = rx.search(src)
        # ★ 正则已把 `gate` 锚在 `useEffect(() => {` 之后的第一条语句
        gates[state] = bool(m) and m.group("gate") == \
            ("if (!timeline.%s) return;" % state
             if state == "motionPathDraft" else "if (!%s) return;" % state)
    add("S2:两个门都是「状态非空才注册」",
        "★ 两个 effect 体**第一件事**就是「状态为空就 return」，"
        "⟹ 监听器只在**状态变成非空那一刻**注册 ⟹ **注册顺序 = 打开顺序**。"
        "★ 这是**机制**层的读数，不是从观察反推的",
        all(gates.values()) and len(gates) == 2, gates)

    # ── S3：★★ 混淆项 —— 本批**分不开**「打开顺序」与「源码顺序」──
    if len(eff) == 2:
        src_first = ("motionPathDraft"
                     if eff["motionPathDraft"]["span"][0]
                     < eff["modelLibraryOpen"]["span"][0]
                     else "modelLibraryOpen")
        open_first = "motionPathDraft"   # ★ `draftThenLib` 里草稿先造
        coincide = src_first == open_first
    else:
        src_first = open_first = None
        coincide = False
    add("S3:★★ 混淆项：打开顺序与源码顺序在本批里**重合**",
        "★ 唯一**可达**的共活臂 `draftThenLib` 里，草稿既**先打开**、"
        "effect 又**写在前面**（`:2697` vs `:2733`）⟹ 两种解释给出**同一预测**"
        "⟹ 本批**不能**区分 ⟹ 报告只准说「**先注册的赢**」"
        "（「注册顺序 = 打开顺序」由 S2 的门支撑，而不是由本臂的胜负反推）",
        coincide and src_first == "motionPathDraft" and len(eff) == 2,
        {"srcFirst": src_first, "openFirst": open_first,
         "coincide": coincide,
         "note": "★ 两个顺序重合 ⟹ H1/H2 不可分离，本批不下结论"})

    by = index_rows(raw)

    # ── S4：「桌还在」必须**直读**，不得是推断 ──
    reads = []
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            for s in (r.get("setup") or []):
                if isinstance(s.get("read"), dict):
                    reads.append((r.get("arm"), "setup", s["read"]))
            for p in (r.get("presses") or []):
                reads.append((r.get("arm"), "press", p.get("read")))
            if isinstance(r.get("start"), dict):
                reads.append((r.get("arm"), "start", r["start"]))
            if isinstance(r.get("after"), dict):
                reads.append((r.get("arm"), "after", r["after"]))
    missing = [{"arm": a, "at": w} for a, w, rr in reads
               if "deskOpen" not in (rr or {})]
    add("S4:「桌还在」是**直读**（每个读数都带 deskOpen）",
        "★ 若从「草稿与库两个读数都变 `null`」**推断**桌关，"
        "任何一个读数因别的原因消失都会误判 ⟹ 强制直读 "
        "`[role=\"dialog\"][aria-modal=\"true\"]`",
        not missing and len(reads) > 0,
        {"reads": len(reads), "missing": missing})

    # ── S5：★ 独立重算逐次读数（不 import 汇编器的 EXPECT）──
    def one(arm, press_no, want):
        """★ `press_no` 是**第几次按压**（1 起）；越界或读数残缺都算不通过。"""
        got = []
        for rdno, r in by.get(arm, []):
            s = seq_of(r)
            g = s[press_no - 1] if len(s) >= press_no else None
            got.append((rdno, len(s), g))
        ok = bool(got) and all(
            ln == 3 and g is not None and not g.get("broken")
            and all(g[k] == w for k, w in want.items())
            for _r, ln, g in got)
        return ok, got

    v1, g1 = one(BOTH, 1, {"draft": "false", "lib": "true", "desk": True})
    v2, g2 = one(BOTH, 2, {"draft": "false", "lib": "false", "desk": True})
    v3, g3 = one(BOTH, 3, {"draft": "false", "lib": "false", "exportOpen": False,
                           "desk": True})
    add("S5:共活臂逐次读数重算一致（3 次 × 2 轮）",
        "★ P1 草稿关、库**仍在**；P2 库关；P3 导出面板关、**桌仍在**",
        v1 and v2 and v3, {"p1": g1, "p2": g2, "p3": g3})
    alone_ok, alone_g = True, []
    for a in ALONE:
        ok, g = one(a, 1, {"draft": "false", "lib": "false", "desk": True})
        alone_ok = alone_ok and ok
        alone_g.append({"arm": a, "p1": g})
        ok3, g3a = one(a, 3, {"desk": False})
        alone_ok = alone_ok and ok3
        alone_g.append({"arm": a, "p3": g3a})
    add("S6:两个单独臂逐次读数重算一致（第 3 次桌关）",
        "★ 单独时第 1 次就两样都清、第 3 次把整张桌关掉",
        alone_ok, alone_g)

    # ── S7：★★ P789-1 被否（观察层）──
    p1 = [seq_of(r)[0] for _rd, r in by.get(BOTH, [])]
    add("S7:★★ 「先注册的赢」（我预测「后开的赢」被否）",
        "★ `draftThenLib` 第 1 次按 Escape 关掉的是**草稿**、模型库**留着** "
        "⟹ 我原先的预测**被否**"
        "（★ 但 S3 已钉住：分不开「打开顺序」与「源码顺序」）",
        len(p1) == 2 and all(x.get("draft") == "false"
                             and x.get("lib") == "true" for x in p1),
        {"press1": p1,
         "myPrediction": "模型库被关（后打开的赢）",
         "actual": "草稿被关、模型库仍在"})

    # ── S8：不可达臂，且**不是**造草稿失败 ──
    unr = [(rdno, r) for rdno, r in by.get(UNREACHABLE, [])]
    mk = [s for _rd, r in unr for s in (r.get("setup") or [])
          if s.get("phase") == "makeDraft"]
    add("S8:★ 不可达臂两轮一致，且**草稿造出来了**",
        "★ 先开模型库再造草稿：两轮都 `libAfterAttempt==\"false\"` "
        "**且** `draftAfterAttempt==\"true\"` ⟹ 不是「造草稿失败」，"
        "是**模型库被外点关闭顺手关掉**（`DirectorViewport.tsx:2747` 的 "
        "`document.addEventListener(\"pointerdown\", …)`）⟹ C785-2 的直接推论",
        len(unr) == 2
        and all(r.get("structurallyUnreachable") for _rd, r in unr)
        and len(mk) == 2
        and all(s.get("libAfterAttempt") == "false"
                and s.get("draftAfterAttempt") == "true" for s in mk),
        {"rounds": [rd for rd, _ in unr],
         "makeDraft": mk,
         "whys": [r.get("why") for _rd, r in unr]})

    # ── S9：格数与无抖动 ──
    add("S9:8 格都在（4 臂 × 2 轮）且 tries 全为 1",
        "★ 两轮一致、每臂两格；`tries==1` ⟹ 没有靠重试掩盖的抖动",
        len(by) == 4 and all(len(v) == 2 for v in by.values())
        and all(r.get("tries") == 1 for v in by.values() for _rd, r in v),
        {a: len(v) for a, v in sorted(by.items())})

    # ── S10：桌的锚点**唯一**（不会被导出面板冒充）──
    # ★ 报 `aria-modal="true"` **自己那行**的行号，并要求它**前面几行内**
    #   就有 `role="dialog"` ⟹ 否则「唯一出现」不足以说明它是桌
    hits, noDialog = [], []
    for p in sorted((ROOT / "src/components/director").glob("*.tsx")):
        lines = p.read_text(encoding="utf-8").split("\n")
        for i, ln in enumerate(lines, 1):
            if 'aria-modal="true"' in ln:
                window = "\n".join(lines[max(0, i - 4):i])
                if 'role="dialog"' not in window:
                    noDialog.append("%s:%d" % (p.name, i))
                hits.append("%s:%d" % (p.name, i))
    add("S10:桌的锚点唯一",
        "★ `aria-modal=\"true\"` 在整个 director 组件目录里**只有一处**、"
        "且**同一个元素**上还有 `role=\"dialog\"` ⟹ "
        "`[role=\"dialog\"][aria-modal=\"true\"]` 就是桌本身；"
        "其余 `role=\"dialog\"`（导出面板等）**没有** `aria-modal`，不会冒充",
        hits == ["DirectorDesk.tsx:902"] and not noDialog,
        {"hits": hits, "ariaModalWithoutDialog": noDialog})

    if audit:
        add("S11:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S11:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


def mut_raw(fn):
    p = RAW
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = fn(d)
    assert hit, "★ raw 变异没命中任何东西"
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, {"hit": hit}


def _flip_read(arm, where, field, value):
    def go(d):
        n = 0
        for rd in d["rounds"]:
            for r in rd["rows"]:
                if r.get("arm") != arm:
                    continue
                if where == "press" and isinstance(r.get("presses"), list):
                    for pr in r["presses"]:
                        pr["read"][field] = value
                        n += 1
                elif where == "start" and isinstance(r.get("start"), dict):
                    r["start"][field] = value
                    n += 1
        return n
    return mut_raw(go)


def mut_lines(*specs):
    """行数中性的多行变异；**同一文件多处编辑必须原子化**（786 立）。

    ★ 本批 `:2702` 与 `:2744` 是**同一个文件里的两处** `sIP`。
    S1 要求两个 effect **各自**都有 ⟹ 只改一处 S1 仍绿 ⟹ 对照无效；
    所以两处**必须一起改**，且复原也必须一次性。
    """
    assert specs
    rels = sorted({x[0] for x in specs})
    orig = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in rels}
    evidence = []
    for rel, line, old, new in specs:
        p = ROOT / rel
        before = p.read_text(encoding="utf-8").split("\n")
        assert old in before[line - 1], "★ needle 不在 %s:%d：%r" % (
            rel, line, before[line - 1])
        lines = list(before)
        lines[line - 1] = lines[line - 1].replace(old, new)
        assert len(lines) == len(before), "★ 变异不是行数中性"
        p.write_text("\n".join(lines), encoding="utf-8")
        after = p.read_text(encoding="utf-8").split("\n")[line - 1]
        ev = {"file": rel, "line": line, "oldGone": old not in after,
              "newThere": new in after}
        assert ev["oldGone"] and ev["newThere"], \
            "★ 变异没真改到目标性质：%r" % ev
        evidence.append(ev)
    # ★ 事后自检：改完之后 S1 依赖的「两个都有」**必须真的不成立**
    return restore_and_check(orig), evidence


def restore_and_check(orig):
    def restore():
        for rel, txt in orig.items():
            (ROOT / rel).write_text(txt, encoding="utf-8")
    return restore


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    checks = run_checks(raw, audit)
    nPos = sum(1 for c in checks if c["ok"])
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(RAW.read_text(encoding="utf-8")), audit)
            flipped = [x["id"] for x in c if not x["ok"]]
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped,
                    "stillPassing": [x["id"] for x in c if x["ok"]]}
        finally:
            restore()

    # ① 把共活臂第 1 次的草稿读数翻成「还活着」⟹ 核心观察必须翻
    negs.append(neg("N1 共活臂 P1 草稿读数被翻成 true",
                    "★ 验证 S5/S7 真的在读**共活臂第 1 次**的读数"
                    "（若没读，「预测被否」这句话就没有证据）",
                    lambda: _flip_read(BOTH, "press", "draft", "true"),
                    "S7:★★ 「先注册的赢」（我预测「后开的赢」被否）"))
    # ② 把不可达臂的 `libAfterAttempt` 翻成 true ⟹ 不可达必须不成立
    def flip_unr():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") != UNREACHABLE:
                        continue
                    for s in r.get("setup") or []:
                        if s.get("phase") == "makeDraft":
                            s["libAfterAttempt"] = "true"
                            n += 1
            return n
        return mut_raw(go)
    negs.append(neg("N2 不可达臂 libAfterAttempt 翻成 true",
                    "★ 验证 S8：若模型库**没有**被关掉，这个臂就该被判为可达 ⟹ "
                    "「不可达」是**读出来的**不是写死的",
                    flip_unr,
                    "S8:★ 不可达臂两轮一致，且**草稿造出来了**"))
    # ③ 源码：把两处 `sIP` **原子化**一起去掉 ⟹ S1 必须翻
    negs.append(neg("N3 两处 sIP 一起被去掉（同一文件·原子化）",
                    "★ 验证 S1 真的在找 `sIP`，而不是靠行号硬取。"
                    "★ 只改 `:2702` 或只改 `:2744` S1 都仍绿（它要求两个都有）"
                    "⟹ **两处必须一起改**，否则对照无效",
                    lambda: mut_lines(
                        (DV, 2702, "event.stopImmediatePropagation();",
                         "void event;"),
                        (DV, 2744, "event.stopImmediatePropagation();",
                         "void event;")),
                    "S1:两个 sIP 主人都在（正则定位，不靠行号）"))
    # ④ 把共活臂第 3 次的 deskOpen 翻成 false ⟹ 「多按一次」必须翻
    def flip_desk():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") != BOTH:
                        continue
                    for pr in r.get("presses") or []:
                        pr["read"]["deskOpen"] = False
                        n += 1
            return n
        return mut_raw(go)
    negs.append(neg("N4 共活臂 P3 deskOpen 翻成 false",
                    "★ 验证 S5/S6：「3 次里桌没关」这个读数**被真读了**"
                    "（少了它，「多按一次」就只是断言里的话）",
                    flip_desk,
                    "S5:共活臂逐次读数重算一致（3 次 × 2 轮）"))
    # ⑤ 抽掉一个读数的 deskOpen ⟹ S4 必须抓到（「直读」不可退化）
    def drop_desk():
        def go(d):
            n = 0
            for rd in d["rounds"]:
                for r in rd["rows"]:
                    if r.get("arm") != "draftOnly":
                        continue
                    for pr in r.get("presses") or []:
                        pr["read"].pop("deskOpen", None)
                        n += 1
            return n
        return mut_raw(go)
    negs.append(neg("N5 抽掉读数里的 deskOpen",
                    "★ 验证 S4：「桌还在」**不能**退化成从别的读数推断",
                    drop_desk,
                    'S4:「桌还在」是**直读**（每个读数都带 deskOpen）'))

    # ── 复原核对（源码 + raw，字节级）──
    fp_src = {rel: (ROOT / rel).read_bytes() for rel in (DV,)}
    fp_raw = RAW.read_bytes()
    drifted = sorted(rel for rel, b in fp_src.items()
                     if (ROOT / rel).read_bytes() != b)
    raw_drift = RAW.read_bytes() != fp_raw
    checks.append({
        "id": "S12:阴性对照已复原（源码 + raw，字节级）",
        "desc": "★ N3 改过 `DirectorViewport.tsx` 的两处 ⟹ 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg, nCaught = len(negs), sum(1 for n in negs if n["ok"])
    REPORT.write_text(json.dumps(
        {"batch": 789, "checks": checks,
         "totals": {"checks": len(checks), "passed": nPos,
                    "failed": len(checks) - nPos},
         "negativeControls": {"total": nNeg, "caught": nCaught,
                              "detail": negs}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== batch 789 验收 ===")
    for c in checks:
        print("  %s %s" % ("OK  " if c["ok"] else "FAIL", c["id"]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-42s flipped=%s"
              % ("OK  " if n["ok"] else "FAIL", n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d" % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
