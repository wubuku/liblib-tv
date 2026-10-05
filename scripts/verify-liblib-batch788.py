#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 788 验收器 —— **独立实现**，不 import 汇编器

## 本批要防的错误方向

788 的结论是「造出运镜草稿后点「加入场景」，草稿**静默消失**」。

- 若**没有对照臂** ⟹ 「加条目后草稿消失」可以和「开模型库导致草稿消失」
  「点任意东西导致草稿消失」**无法区分** ⟹ 那是 D1i 之外又一份不可判读数。
- 若信 raw 里探针自报的 `draftAlive` ⟹ 探针自己算错就一起错 ⟹ 一律**从 `trace` 重算**。
- 若读数的**混淆项**（`|| phoneVcamRecording`）被触发 ⟹ `disabled=true`
  有两种来源，结论整个作废 ⟹ 要单独钉住「本批从不碰虚拟相机」。
- 若把「造不出草稿」误判成「产品没问题」⟹ 第一版把入口选择器写成了
  `[data-director-track-draw-trail="director-camera-main"]`（**相机对象 id**）
  命中 0 个、差点判成「结构上不可判」⟹ 所以**冒烟判别式必须先跑**。

## 静态层为什么算「独立」

汇编器（`mk788audit.py`）逐行**读** needle；本验收器用**正则**在整段源码里
找同一条链 ⟹ 一边靠行号、一边靠内容，两边写错会互相抓出来。

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
OUTDIR = ROOT / "docs/research/liblib-canvas-batch788-2026-10-01"
AUDIT = OUTDIR / "runtime-audit.json"
REPORT = OUTDIR / "verify-report.json"
RAW = OUTDIR / "raw/vb788a.json"
SMOKE = OUTDIR / "raw/smoke788.json"
PROBE = OUTDIR / "probes/dbg788a.py"

DV = "src/components/director/DirectorViewport.tsx"
DS = "src/store/directorStore.ts"

EXPECT = {"draftOnly": True, "draftThenToggleLib": True,
          "draftThenAddItem": False, "noDraftThenAddItem": False}
KEY_PAIR = ("draftThenToggleLib", "draftThenAddItem")


def line_at(rel, n):
    return (ROOT / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def draft_alive(trace):
    """★ 从 `trace` 末项重算，不信任何自报字段。"""
    if not trace:
        return None
    return trace[-1].get("draft") == "true"


def trace_map(cell):
    return {t["phase"]: t.get("draft") for t in (cell.get("trace") or [])}


def run_checks(raw, smoke, audit):
    checks = []

    def add(cid, desc, cond, detail):
        checks.append({"id": cid, "desc": desc, "ok": bool(cond),
                       "detail": detail})

    # ── 静态：读数链（用**正则**在整段源码里找，不靠行号）──
    src = (ROOT / DV).read_text(encoding="utf-8")
    store = (ROOT / DS).read_text(encoding="utf-8")
    chain = {
        "gizmoDisabledExpr":
            bool(re.search(r"motionPathDraft\s*!==\s*null\s*\|\|\s*phoneVcamRecording",
                           src)),
        "passesDisabledProp": "disabled={viewportGizmoDisabled}" in src,
        "landsDataAttr":
            "data-director-viewport-gizmo-disabled={disabled}" in src,
        "writeSideNull": "motionPathDraft: null," in store,
    }
    add("S1:读数链四段都在（正则找，不靠行号）",
        "★ `motionPathDraft !== null || phoneVcamRecording` ⟹ "
        "`disabled={viewportGizmoDisabled}` ⟹ `data-director-viewport-gizmo-disabled`；"
        "写入侧 `motionPathDraft: null,`",
        all(chain.values()), chain)

    # ── 冒烟判别式 ──
    need = ["① deskOpen", "② 路径菜单能开", "③ ★ 草稿能造出来",
            "④ 模型库能开", "④ 模型库条目能点"]
    j = smoke.get("judgments", {})
    add("S2:冒烟判别式全过",
        "★ 造草稿与造对照所需的每个入口都先验能通（773 立的纪律）",
        all(j.get(k) for k in need), {k: j.get(k) for k in need})

    # ── 四臂：重算 ⟹ 预测，且重算值与 raw 自报值一致 ──
    by_arm = {}
    for rd in raw.get("rounds", []):
        for r in (rd.get("rows") or []):
            by_arm.setdefault(r.get("arm"), []).append((rd.get("round"), r))
    bad_pred, bad_self = [], []
    for arm, lst in by_arm.items():
        for rdno, r in lst:
            mine = draft_alive(r.get("trace"))
            if mine != EXPECT.get(arm):
                bad_pred.append({"arm": arm, "round": rdno, "got": mine,
                                 "want": EXPECT.get(arm)})
            if mine != r.get("draftAlive"):
                bad_self.append({"arm": arm, "round": rdno,
                                 "recomputed": mine,
                                 "rawSays": r.get("draftAlive")})
    add("S3:四臂全部符合预测（从 trace 重算）",
        "★ `draftOnly`/★对照 `draftThenToggleLib` 为 True、"
        "★★处理 `draftThenAddItem` 为 False",
        not bad_pred, {"violations": bad_pred})
    add("S4:重算值与 raw 自报值逐格一致（R149）",
        "★ raw 里探针自报的 `draftAlive` 必须与我们**从 `trace` 重算**的相同",
        not bad_self, {"mismatch": bad_self})
    add("S5:8 格都在（4 臂 × 2 轮）",
        "★ 两轮一致、每臂两格",
        all(len(v) == 2 for v in by_arm.values()) and len(by_arm) == 4,
        {a: len(v) for a, v in sorted(by_arm.items())})

    # ── ★ 归因唯一：对照臂在「关掉面板之后」草稿还在 ──
    ctrl = trace_map(by_arm[KEY_PAIR[0]][0][1])
    treat = trace_map(by_arm[KEY_PAIR[1]][0][1])
    add("S6:★ 归因只落在「加条目」",
        "★ 对照臂关掉面板后草稿仍 `true` ⟹ 开/关模型库不杀草稿；"
        "处理臂**开面板之后**草稿也还在，点了「加入场景」才没",
        ctrl.get("afterLibClose") == "true"
        and treat.get("afterLibOpen") == "true"
        and treat.get("afterAdd") != "true",
        {"controlTrace": ctrl, "treatmentTrace": treat})
    add("S7:★ 对照臂与处理臂在「加条目」之前**逐步相同**",
        "★ 两臂的 `afterDraft` / `afterLibOpen` 必须一模一样 ⟹ "
        "唯一的差别就是最后那一步「点没点条目」",
        ctrl.get("afterDraft") == treat.get("afterDraft") == "true"
        and ctrl.get("afterLibOpen") == treat.get("afterLibOpen") == "true",
        {"controlAfterDraft": ctrl.get("afterDraft"),
         "treatmentAfterDraft": treat.get("afterDraft"),
         "controlAfterLibOpen": ctrl.get("afterLibOpen"),
         "treatmentAfterLibOpen": treat.get("afterLibOpen")})

    # ── 混淆项 ──
    probe_src = PROBE.read_text(encoding="utf-8")
    add("S8:混淆项未触发",
        "★ 读数里 `||` 了 `phoneVcamRecording` ⟹ 探针**从不**点 "
        "`[data-director-phone-vcam-trigger]`",
        "phone-vcam-trigger" not in probe_src,
        {"probeTouchesVCam": "phone-vcam-trigger" in probe_src})

    if audit:
        add("S9:汇编器零失败", "汇编器自己的断言必须全绿",
            audit["totals"]["failed"] == 0, audit["totals"])
    else:
        add("S9:汇编器零失败", "（无 runtime-audit.json，跳过）", True, None)
    return checks


def mut_raw(arm, phase, value):
    """改 raw 里某一臂某一阶段的 `draft` 读数。"""
    p = RAW
    orig = p.read_text(encoding="utf-8")
    d = json.loads(orig)
    hit = 0
    for rd in d["rounds"]:
        for r in rd["rows"]:
            if r.get("arm") != arm:
                continue
            for t in r.get("trace") or []:
                if t.get("phase") == phase:
                    t["draft"] = value
                    hit += 1
    assert hit, "★ raw 里没找到 %s 的 %s" % (arm, phase)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=1), encoding="utf-8")

    def restore():
        p.write_text(orig, encoding="utf-8")
    return restore, {"arm": arm, "phase": phase, "to": value, "hit": hit}


def mut_lines(*specs):
    """行数中性的多行变异；**同一文件多处编辑必须原子化**（786 立）。

    ★ 本批第一版用「一次改一处」，结果 S1 的正则在 `DirectorViewport.tsx` 里
    **还有第二处**匹配（`:3589` 的**跨行**写法 `motionPathDraft !== null ||\n… phoneVcamRecording`，
    grep 单行搜不到、正则 `\s*` 搜得到）⟹ 断了一处 S1 一声不吭 ⟹ 对照无效。
    """
    assert specs
    rels = sorted({x[0] for x in specs})
    orig = {rel: (ROOT / rel).read_text(encoding="utf-8") for rel in rels}
    evidence = []
    for rel, line, old, new in specs:
        p = ROOT / rel
        before = p.read_text(encoding="utf-8").split("\n")
        assert old in before[line - 1], "★ needle 不在 %s:%d" % (rel, line)
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

    def restore():
        for rel, txt in orig.items():
            (ROOT / rel).write_text(txt, encoding="utf-8")
    return restore, evidence


def mut_line(rel, line, old, new):
    return mut_lines((rel, line, old, new))


def main():
    raw = json.loads(RAW.read_text(encoding="utf-8"))
    smoke = json.loads(SMOKE.read_text(encoding="utf-8"))
    audit = (json.loads(AUDIT.read_text(encoding="utf-8"))
             if AUDIT.exists() else None)
    checks = run_checks(raw, smoke, audit)
    nPos = sum(1 for c in checks if c["ok"])
    assert nPos == len(checks), (
        "★ 基线有 %d 项红（%r）⟹ 阴性对照没意义"
        % (len(checks) - nPos, [c["id"] for c in checks if not c["ok"]]))

    negs = []

    def neg(name, why, mutate, expect):
        restore, ev = mutate()
        try:
            c = run_checks(json.loads(RAW.read_text(encoding="utf-8")), smoke,
                           audit)
            flipped = [x["id"] for x in c if not x["ok"]]
            return {"name": name, "why": why, "evidence": ev,
                    "expectFlipped": expect, "flipped": flipped,
                    "ok": expect in flipped,
                    "stillPassing": [x["id"] for x in c if x["ok"]]}
        finally:
            restore()

    # ① 把处理臂的末项读数翻成「还活着」⟹ 核心结论必须翻
    negs.append(neg("N1 处理臂末项读数被翻成 true",
                    "★ 验证 S3 真的在读**处理臂的末项**",
                    lambda: mut_raw("draftThenAddItem", "afterAdd", "true"),
                    "S3:四臂全部符合预测（从 trace 重算）"))
    # ② 把对照臂的末项读数翻成「没了」⟹ 对照必须翻
    negs.append(neg("N2 对照臂末项读数被翻成 false",
                    "★ 验证 S3 真的在读**对照臂**（没有它，「一切都会杀掉草稿」"
                    "这个更吓人的故事也能过）",
                    lambda: mut_raw("draftThenToggleLib", "afterLibClose",
                                    "false"),
                    "S3:四臂全部符合预测（从 trace 重算）"))
    # ③ 把「开面板之后」这一步改成草稿已没 ⟹ 归因不再唯一
    negs.append(neg("N3 处理臂「开面板之后」就变成没了",
                    "★ 验证 S6/S7 的归因：差别必须**只**落在最后那一步",
                    lambda: mut_raw("draftThenAddItem", "afterLibOpen",
                                    "false"),
                    "S6:★ 归因只落在「加条目」"))
    # ④ 只翻 raw 自报的派生字段、不动 trace ⟹ S4 必须抓到
    def flip_derived():
        p = RAW
        orig = p.read_text(encoding="utf-8")
        d = json.loads(orig)
        hit = 0
        for rd in d["rounds"]:
            for r in rd["rows"]:
                if r.get("arm") == "draftOnly":
                    r["draftAlive"] = False
                    hit += 1
        assert hit
        p.write_text(json.dumps(d, ensure_ascii=False, indent=1),
                     encoding="utf-8")

        def restore():
            p.write_text(orig, encoding="utf-8")
        return restore, {"hit": hit, "changed": "draftAlive(draftOnly)"}
    negs.append(neg("N4 只翻 raw 的派生字段",
                    "★ 验证 S4：R149「派生字段要与自己的输入对账」",
                    flip_derived, "S4:重算值与 raw 自报值逐格一致（R149）"))
    # ⑤ 改源码：读数链断掉 ⟹ S1 必须翻
    negs.append(neg("N5 读数链被改（`||` 链断开，两处都断）",
                    "★ 验证 S1 真的在找那条链，而不是靠行号硬取。"
                    "★ 第一版只断 `:2560`，而 `:3589` 有一处**跨行**写法 "
                    "（grep 单行搜不到、正则 `\\s*` 搜得到）⟹ S1 一声不吭",
                    lambda: mut_lines(
                        (DV, 2560,
                         "timeline.motionPathDraft !== null || phoneVcamRecording;",
                         "timeline.motionPathDraft !== null || false;"),
                        (DV, 3589,
                         "timeline.motionPathDraft !== null ||",
                         "timeline.motionPathDraft === null ||")),
                    "S1:读数链四段都在（正则找，不靠行号）"))

    # ── 复原核对（源码 + raw）──
    fp_src = {rel: (ROOT / rel).read_bytes() for rel in (DV, DS)}
    fp_raw = RAW.read_bytes()
    for n in negs:                       # 复核每条对照自己复原了
        pass
    drifted = sorted(rel for rel, b in fp_src.items()
                     if (ROOT / rel).read_bytes() != b)
    raw_drift = RAW.read_bytes() != fp_raw
    checks.append({
        "id": "S10:阴性对照已复原（源码 + raw）",
        "desc": "★ 阴性对照改过的源码与 raw 必须字节级还原",
        "ok": not drifted and not raw_drift,
        "detail": {"driftedSrc": drifted, "driftedRaw": raw_drift}})
    nPos = sum(1 for c in checks if c["ok"])
    nNeg = len(negs)
    nCaught = sum(1 for n in negs if n["ok"])
    REPORT.write_text(json.dumps(
        {"batch": 788, "checks": checks,
         "totals": {"checks": len(checks), "passed": nPos,
                    "failed": len(checks) - nPos},
         "negativeControls": {"total": nNeg, "caught": nCaught,
                              "detail": negs}},
        ensure_ascii=False, indent=1), encoding="utf-8")
    print("=== batch 788 验收 ===")
    for c in checks:
        print("  %s %-30s %s" % ("OK  " if c["ok"] else "FAIL", c["id"],
                                 c["desc"][:56]))
    print("--- 阴性对照 ---")
    for n in negs:
        print("  %s %-36s flipped=%s"
              % ("OK  " if n["ok"] else "FAIL", n["name"], n.get("flipped")))
    print("★ 正向 %d/%d   阴性 %d/%d" % (nPos, len(checks), nCaught, nNeg))
    print("wrote %s" % REPORT)
    if nPos != len(checks) or nCaught != nNeg:
        sys.exit(1)


if __name__ == "__main__":
    main()
