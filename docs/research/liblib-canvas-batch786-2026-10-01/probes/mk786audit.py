#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 786 汇编器 —— 把「三向互斥」这个结构用**行锚定字面量**钉死

## 承重预测（从源码逐行推出，可 falsify）

**P786-1**：783 的 `crossWrites` 层有**三处**缺陷（prop 名当状态名 /
内联 JSX 箭头不被包裹函数正则匹配 / 状态集按文件切）⟹ **修好之后报出来的
交叉写入组**应该**多于** 783 报的那一个文件里的两组。

**P786-2**：`{modelLibraryOpen, crowdPanelOpen, phoneVcamOpen}` 构成
**三向**互斥（783 那对是**双向**）⟹ 每个打开者都**先关掉另外两个、再打开自己**。

**P786-3**：「能不能共活」静态不可判 ⟹ 留给运行时（本批只钉**事实**）。

## ★ 但「先关掉另外两个」不是无条件的 —— 有一处带门

vcam 触发器 `:3537` 写着 `if (phoneVcamRecording) return;` ⟹ **录制中点它
什么都不会发生**。这条要单独钉住，否则「无条件」这个说法就是假的。

## 纪律

- 每条结论 = 一个**行锚定字面量**（file:line + 精确 needle），从**源码**断言
- 普查器只采集 ⟹ 与普查输出**对账**，不一致就记成发现
- ★ needle 要**唯一**：`setPhoneVcamOpen(false);` 这种整行字面量，
  而不是 `setPhoneVcamOpen(`（783 那种粒度会撞名）
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch786-2026-10-01"
CENSUS = REPO / (B + "/raw/census786.json")
C783 = REPO / ("docs/research/liblib-canvas-batch783-2026-10-01"
               "/raw/census783.json")
OUT = REPO / (B + "/runtime-audit.json")

DV = "src/components/director/DirectorViewport.tsx"
DD = "src/components/director/DirectorDesk.tsx"
DVP = "src/components/director/DirectorPhoneVcamPanel.tsx"
DT = "src/components/director/DirectorTimeline.tsx"

#: ★ 5 组交叉写入：`(名字, 文件, 组起始行, [(行, 精确 needle), …])`
CROSS_GROUPS = [
    ("togglePathMenu", DT, 601, [
        (602, "if (cameraFollowActive) return;"),
        (603, "setPresetPanelLeft(null);"),
        (605, "setPathMenuLeft(null);"),
        (611, "setPathMenuLeft("),
    ]),
    ("togglePresetPanel", DT, 695, [
        (696, 'if (selectedTrack?.kind !== "camera" || cameraFollowActive) return;'),
        (698, "setPresetPanelLeft(null);"),
        (704, "setPathMenuLeft(null);"),
        (705, "setPresetPanelLeft("),
    ]),
    ("toggleModelLibrary", DV, 2825, [
        (2826, "setPhoneVcamOpen(false);"),
        (2827, "setCrowdPanelOpen(false);"),
        (2828, "setModelLibraryOpen((value) => !value);"),
    ]),
    ("vcamTriggerOnClick", DV, 3536, [
        (3537, "if (phoneVcamRecording) return;"),
        (3538, "setModelLibraryOpen(false);"),
        (3539, "setCrowdPanelOpen(false);"),
        (3540, "setPhoneVcamOpen((value) => !value);"),
    ]),
    ("crowdTriggerOnClick", DV, 3556, [
        (3557, "setModelLibraryOpen(false);"),
        (3558, "setPhoneVcamOpen(false);"),
        (3559, "setCrowdPanelOpen((value) => !value);"),
    ]),
]

#: ★ C786-3：`DirectorDesk.tsx` 的 Escape 阶梯写 ≥2 个门状态，但**每一档都
#:   `return`** ⟹ 一次按键最多走一档 ⟹ 它们**互相排斥**，**不是**交叉写入。
#:   ★ 而第一版普查器用「以 `;` 结尾」当类型标注判据，把 `:565` 那条**真的**
#:   `followTargetId` 写入也杀了 ⟹ 组数**恰好**对上了，**理由却是错的**。
EARLY_RETURN_LADDER = ("handleKeyDown", DD, 473, [
    (557, "if (exportPanelOpen) {"),
    (558, "setExportPanelOpen(false);"),
    (559, "return;"),
    (564, "if (followTargetId) {"),
    (565, "if (activeCameraId) updateCamera(activeCameraId, { followTargetId: null });"),
    (566, "return;"),
])

#: ★ 类型标注判据的两个方向（第一版用「以 `;` 结尾」⟹ 误杀 `:565`）
TYPE_DISCRIMINATOR = [
    (DVP, 99, "open: boolean;", "type"),
    (DD, 565,
     "if (activeCameraId) updateCamera(activeCameraId, { followTargetId: null });",
     "write"),
]

#: ★ 三向互斥：每个打开者「关掉另外两个」的**顺序**必须排在「打开自己」之前
TRIANGLE = [
    # (组名, 自己的行, 关掉 A 的行, 关掉 B 的行)
    ("toggleModelLibrary", 2828, 2826, 2827),
    ("vcamTriggerOnClick", 3540, 3538, 3539),
    ("crowdTriggerOnClick", 3559, 3557, 3558),
]

def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def anchors(specs):
    out, ok = [], True
    for rel, n, needle in specs:
        code = line_of(rel, n)
        good = needle in code
        ok = ok and good
        out.append({"file": rel, "line": n, "needle": needle, "ok": good,
                    "code": code.strip()[:110]})
    return ok, out


def main():
    cen = json.loads(CENSUS.read_text(encoding="utf-8"))
    c783 = json.loads(C783.read_text(encoding="utf-8"))
    checks = []

    # ── A：5 组交叉写入，每组逐行锚定 ──
    for name, rel, start, specs in CROSS_GROUPS:
        ok, det = anchors([(rel, n, nd) for n, nd in specs])
        c = {"id": "A:" + name, "file": rel, "startLine": start,
             "ok": ok, "n": len(specs), "anchors": det}
        assert ok, "★ 行锚定失败：%s\n%r" % (name, det)
        checks.append(c)

    # ── B：三向互斥的**顺序**（关掉另外两个排在打开自己之前）──
    b_ok, b_det = True, []
    for gname, self_line, a_line, b_line in TRIANGLE:
        good = a_line < self_line and b_line < self_line
        b_ok = b_ok and good
        b_det.append({"group": gname, "closes": [a_line, b_line],
                      "opensSelf": self_line, "ok": good})
    c = {"id": "B:三向互斥的顺序", "ok": b_ok, "n": len(TRIANGLE),
         "anchors": b_det,
         "claim": "★ 每个打开者**先关掉另外两个、再打开自己** ⟹ 三向互斥"}
    assert b_ok, "★ 顺序不成立：%r" % b_det
    checks.append(c)

    # ── C：★「无条件」这个说法**不成立** —— vcam 打开者带一道门 ──
    ok, det = anchors([
        (DV, 3536, "onClick={() => {"),
        (DV, 3537, "if (phoneVcamRecording) return;"),
    ])
    c = {"id": "C:vcam 打开者带门", "ok": ok, "n": 2, "anchors": det,
         "claim": "★ vcam 触发器 `:3537` 有 `if (phoneVcamRecording) return;` "
                  "⟹ **录制中点它什么都不会发生**，所以「无条件」只对另外两个成立"}
    assert ok, "★ 行锚定失败：%r" % det
    checks.append(c)

    # ── F：★ Timeline 那两个打开者**也**带门，而且是**不对称**的 ──
    #   `togglePathMenu:603` 的 `setPresetPanelLeft(null)` 排在 `:604` 的早退
    #   **之前** ⟹ **关掉**路径菜单也会顺手关掉预设面板；
    #   而 `togglePresetPanel:704` 的 `setPathMenuLeft(null)` 排在 `:697` 早退
    #   **之后** ⟹ **关掉**预设面板**不会**关掉路径菜单。
    f_ok, f_det = anchors([
        (DT, 603, "setPresetPanelLeft(null);"),
        (DT, 604, "if (pathMenuLeft !== null) {"),
        (DT, 697, "if (presetPanelLeft !== null) {"),
        (DT, 698, "setPresetPanelLeft(null);"),
        (DT, 704, "setPathMenuLeft(null);"),
    ])
    c = {"id": "F:Timeline 两个打开者不对称", "ok": f_ok, "n": 5,
         "anchors": f_det,
         "claim": "★ 783 说的「双向」在**写入对方状态**这件事上成立，"
                  "但**关闭方向不对称**：`togglePathMenu:603` 在早退**之前** ⟹ "
                  "关路径菜单会连带关掉预设面板；`togglePresetPanel:704` 在早退"
                  "**之后** ⟹ 关预设面板**不会**关掉路径菜单。"
                  "★ 两个打开者都带 `cameraFollowActive` 门（`:602` / `:696`）"}
    assert f_ok, "★ 行锚定失败：%r" % f_det
    assert 603 < 604 and 704 > 698, "★ 不对称的顺序不成立"
    checks.append(c)

    # ── D：P786-1 —— 783 只在 **1 个文件**里报出交叉写入，另两个文件它一个都没报 ──
    c783_cwf = c783["crossWriteFiles"]
    files_783 = sorted({x["file"].split("/")[-1] for x in c783_cwf})
    misattributed = [w for o in c783["escapeOwners"]
                     for w in (o.get("crossWrites") or [])
                     if w["fn"] == "openLocalModelLibraryImport"
                     and w["state"] == "modelLibraryOpen"]
    files_786 = sorted({g["file"].split("/")[-1] for g in cen["crossWrites"]})
    d = {
        "id": "D:P786-1 修好后报得更多", "ok": True, "n": 1,
        "detail": {
            "c783_crossWriteFiles": files_783,
            "c783_pairs": [p for x in c783_cwf for p in x["pairs"]
                           if p[1]],
            "c786_crossWriteGroups": cen["crossWriteGroups"],
            "c786_files": files_786,
            "misattributedSetts": misattributed,
        },
        "claim": "★ 783 的层只在 %d 个文件（%s）里报出交叉写入；"
                 "786 修好三处缺陷后报出 %d 组、跨 %d 个文件（%s）"
                 % (len(files_783), "、".join(files_783),
                    cen["crossWriteGroups"], len(files_786),
                    "、".join(files_786)),
    }
    assert files_783 == ["DirectorTimeline.tsx"], \
        "★ 783 的 crossWriteFiles 不是预期的 Timeline ⟹ P786-1 的对照要重算：%r" % files_783
    assert cen["crossWriteGroups"] > 2, \
        "★ 786 报出的组数没有多于 783 在 Timeline 里那 2 组 ⟹ P786-1 被否"
    assert len(files_786) > len(files_783), \
        "★ 786 报出的**文件数**没有多于 783 ⟹ P786-1 被否"
    assert misattributed, "★ 没在 783 raw 里找到误归的证据 ⟹ P786-1 的对照要重算"
    checks.append(d)

    # ── E：与普查器对账 ──
    mine = sorted({g[0] for g in CROSS_GROUPS})
    theirs = sorted({g["name"] or ("line%d" % g["startLine"])
                     for g in cen["crossWrites"]})
    e = {"id": "E:与普查器对账", "ok": True, "n": 1,
         "detail": {"assemblerGroups": mine, "censusGroups": theirs,
                    "censusCount": cen["crossWriteGroups"]},
         "claim": "★ 组数与所属文件必须一致（**名字**可能因内联箭头而无名 ⟹ "
                 "对账只比「文件 + 组数」，名字不比）"}
    files_assembler = sorted({g[1].split("/")[-1] for g in CROSS_GROUPS}
                             | {EARLY_RETURN_LADDER[1].split("/")[-1]})
    files_census = sorted({g["file"].split("/")[-1] for g in cen["crossWrites"]})
    e["detail"]["filesAssembler"] = files_assembler
    e["detail"]["filesCensus"] = files_census
    e["ok"] = (files_assembler == files_census
               and cen["crossWriteGroups"] == len(CROSS_GROUPS) + 1)
    assert e["ok"], "★ 对账失败：%r" % e["detail"]
    checks.append(e)

    # ── H：★ C786-3 早退阶梯 —— 机制是**早退**不是**交叉写入** ──
    gname, grel, gstart, gspecs = EARLY_RETURN_LADDER
    ok, det = anchors([(grel, n, nd) for n, nd in gspecs])
    c = {"id": "H:早退阶梯（不是交叉写入）", "ok": ok, "n": len(gspecs),
         "file": grel, "startLine": gstart, "name": gname, "anchors": det,
         "claim": "★ `DirectorDesk.tsx:473` 的 `handleKeyDown`（Escape 阶梯）写了 "
                  "`exportPanelOpen`(`:558`) 与 `followTargetId`(`:565`) 两个门状态，"
                  "但**每一档后面都 `return`**（`:559` / `:566`）⟹ 一次按键最多走一档 ⟹ "
                  "两者**互相排斥**、**不是**交叉写入。"
                  "★ 第一版普查器用「以 `;` 结尾」判类型注解，把 `:565` 那条**真的**"
                  "写入也杀了 ⟹ 组数**恰好**对上了、**理由却是错的**"}
    assert ok, "★ 行锚定失败：%r" % det
    checks.append(c)

    # ── I：类型标注判据的两个方向 ──
    ok, det = anchors([(rel, n, nd) for rel, n, nd, _ in TYPE_DISCRIMINATOR])
    ends_semi = [line_of(rel, n).rstrip().endswith(";")
                 for rel, n, _, _ in TYPE_DISCRIMINATOR]
    c = {"id": "I:类型标注判据（第一版会误杀）", "ok": ok, "n": 2,
         "anchors": det, "bothEndWithSemicolon": ends_semi,
         "claim": "★ `open: boolean;` 与 `…{ followTargetId: null });` **都以 `;` 结尾**"
                  "⟹ 「以 `;` 结尾」这个判据**分不开**它们；真正的分界是"
                  "「类型标注里不会出现 `(` 或 `=>`」"}
    assert ok, "★ 行锚定失败：%r" % det
    assert all(ends_semi), (
        "★ 两行不再都以 `;` 结尾 ⟹ 本条断言的前提没了，要重写判据")
    checks.append(c)

    out = {
        "batch": 786,
        "claims": {
            "P786-1": d["claim"],
            "P786-2": "★ `{modelLibraryOpen, crowdPanelOpen, phoneVcamOpen}` "
                      "构成**三向**互斥（783 那对是**双向**）",
            "P786-3": "「能不能共活」静态不可判 ⟹ 运行时（`raw/vb786a.json`）",
            "caveat": "★ 「无条件」只对 `toggleModelLibrary` 与 crowd 触发器成立；"
                      "vcam 触发器 `:3537` 有 `if (phoneVcamRecording) return;`",
        },
        "crossWriteGroups": [
            {"name": n, "file": f, "startLine": s, "mechanism": "cross-write",
             "members": [{"line": ln, "needle": nd} for ln, nd in sp]}
            for n, f, s, sp in CROSS_GROUPS] + [
            {"name": gname, "file": grel, "startLine": gstart,
             "mechanism": "early-return-ladder",
             "members": [{"line": ln, "needle": nd} for ln, nd in gspecs]}],
        "triangle": [{"group": g, "opensSelf": sl, "closes": [al, bl]}
                     for g, sl, al, bl in TRIANGLE],
        "runtime": {"probe": "raw/vb786a.json",
                    "arms": cen.get("arms"),
                    "note": "本汇编器**不**读运行时 raw；运行时结论由 "
                            "`verify-liblib-batch786.py` 从 raw **重算**"},
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(c.get("n", 0) for c in checks),
                   "failed": sum(0 if c["ok"] else 1 for c in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ P786-1：783 只在 %s 里报出 ⟹ 786 报出 %d 组、跨 %s"
          % ("、".join(files_783), cen["crossWriteGroups"],
             "、".join(files_census)))
    print("★ P786-2：三向互斥的顺序成立（3 个打开者都是「先关另外两个再开自己」）")
    print("★ 但 vcam 触发器带门 `:3537 if (phoneVcamRecording) return;`")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
