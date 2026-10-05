#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 787 汇编器 —— **第④个缺陷**：`store action 调用`也是写入

## 本批发现的是**上一批那层扫描的第④个盲区**

786 把 783 的 `crossWrites` 层重写了一遍，修了三处缺陷（prop 名当状态名 /
内联 JSX 箭头不被包裹函数正则匹配 / 状态集按文件切），组数从 2 涨到 6。
★ 但它**只认两种「写入」的语法形态**：`set<S>(` 调用、**对象字面量键**。

⟹ 而 zustand 的 **action 调用**（`startMotionPathDrawing(tool)`）**也是**写入，
**完全隐形**。本批把它接上，组数从 **6 涨到 10**。

## 四组新增（每组两行行锚定，needle 唯一）

| 组 | 写入 A（**action 调用**） | 写入 B（`set<S>`） | 含义 |
| --- | --- | --- | --- |
| `DirectorTimeline.tsx:1532` | `startMotionPathDrawing(tool)` `:1533` | `setPathMenuLeft(null)` `:1543` | 开始绘制 ⟹ 关掉路径菜单 |
| `DirectorTimeline.tsx:1574` | `createMotionPath(preset)` `:1575` | `setPathMenuLeft(null)` `:1576` | 从预设建路径 ⟹ 关掉路径菜单 |
| ★★ `DirectorViewport.tsx:2835` | `addModelLibraryObject(item)` `:2836` | `setModelLibraryOpen(false)` `:2837` | ★★ **往模型库加条目 ⟹ 杀掉正在进行的运镜绘制** |
| ★★ `DirectorViewport.tsx:2842` | `addModelLibraryObject(item)` `:2843` | `setModelLibraryOpen(false)` `:2844` | ★★ 同上（本机模型变体） |

★ 后两行是本批的重头戏：**没有任何一层普查报出过它们**。

## ★★ 这条更正限定了 786 的一处推论

786 用「`motionPathDraft` 在 31 个组里一次都没出现」支持
「它与模型库**无互斥关系**」。★ 而那个「一次都没出现」是**基于一个不完整的层**
得出的 —— 它没看见 action 调用。
⟹ **「没有交叉写入」只在「层看得见全部写入」时才成立。**

## 纪律

- 每条结论 = 一个**行锚定字面量**（file:line + 精确 needle），从**源码**断言
- ★ needle 要**唯一**：`addModelLibraryObject(item);` 这种整行字面量
- 与普查器输出**对账**；顺带断言**上一批那层确实不认识 action**（缺陷本身要被钉住）
"""
import json
import pathlib

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
B = "docs/research/liblib-canvas-batch787-2026-10-01"
CENSUS = REPO / (B + "/raw/census787.json")
C786_SRC = REPO / ("docs/research/liblib-canvas-batch786-2026-10-01"
                   "/probes/census786.py")
OUT = REPO / (B + "/runtime-audit.json")

DV = "src/components/director/DirectorViewport.tsx"
DT = "src/components/director/DirectorTimeline.tsx"
DS = "src/store/directorStore.ts"

#: ★ 四组新增：`(组名, 文件, **表头行**, [(行, needle, 期望状态), …])`
#:   ★ 表头行 = 普查记的 `startLine`（**不是**成员首行）—— 第一版记成成员首行，
#:   于是和普查的清单对不上（`1532` vs `1533`）。
NEW_GROUPS = [
    ("timeline-draw-tool", DT, 1532, [
        (1533, "startMotionPathDrawing(tool);", "motionPathDraft"),
        (1543, "setPathMenuLeft(null);", "pathMenuLeft"),
    ]),
    ("timeline-create-from-preset", DT, 1574, [
        (1575, "createMotionPath(preset);", "motionPathDraft"),
        (1576, "setPathMenuLeft(null);", "pathMenuLeft"),
    ]),
    ("★ add-model-library-item", DV, 2835, [
        (2836, "addModelLibraryObject(item);", "motionPathDraft"),
        (2837, "setModelLibraryOpen(false);", "modelLibraryOpen"),
    ]),
    ("★ add-local-model-library-item", DV, 2842, [
        (2843, "addModelLibraryObject(item);", "motionPathDraft"),
        (2844, "setModelLibraryOpen(false);", "modelLibraryOpen"),
    ]),
]

#: ★ action 侧的行锚定：这些 action 真的写了那些门状态
ACTION_ANCHORS = [
    ("startMotionPathDrawing", DS, 7753,
     "startMotionPathDrawing: (tool, requestedTrackId) =>"),
    ("createMotionPath", DS, 7703,
     "createMotionPath: (preset, requestedTrackId) =>"),
    ("addModelLibraryObject", DS, 5152, "addModelLibraryObject: (item) => {"),
    # ★★ 关键那一行：模型库加条目把草稿**置空**
    ("addModelLibraryObject", DS, 5190, "motionPathDraft: null,"),
]


def line_of(rel, n):
    return (REPO / rel).read_text(encoding="utf-8").split("\n")[n - 1]


def anchors(specs):
    out, ok = [], True
    for spec in specs:
        rel, n, needle = spec[0], spec[1], spec[2]
        code = line_of(rel, n)
        good = needle in code
        ok = ok and good
        out.append({"file": rel, "line": n, "needle": needle, "ok": good,
                    "code": code.strip()[:110]})
    return ok, out


def main():
    cen = json.loads(CENSUS.read_text(encoding="utf-8"))
    checks = []

    # ── A：四组新增，每组两行行锚定 ──
    for name, rel, hdr, specs in NEW_GROUPS:
        ok, det = anchors([(rel, n, nd) for n, nd, _ in specs])
        c = {"id": "A:" + name, "file": rel, "startLine": hdr,
             "ok": ok, "n": len(specs),
             "members": [{"line": n, "needle": nd, "state": st}
                         for n, nd, st in specs],
             "anchors": det}
        assert ok, "★ 行锚定失败：%s\n%r" % (name, det)
        checks.append(c)

    # ── B：action 侧的行锚定 ──
    ok, det = anchors([(f, n, nd) for _a, f, n, nd in ACTION_ANCHORS])
    c = {"id": "B:action 侧行锚定", "ok": ok, "n": len(ACTION_ANCHORS),
         "anchors": det,
         "claim": "★ `addModelLibraryObject` 在 `directorStore.ts:5190` "
                  "把 `motionPathDraft` **置空** ⟹ 「往模型库加条目」"
                  "这个操作会**取消正在进行的运镜绘制**"}
    assert ok, "★ 行锚定失败：%r" % det
    checks.append(c)

    # ── C：组数 6 ⟹ 10 ──
    c = {"id": "C:组数 6 ⟹ 10", "ok": True, "n": 1,
         "detail": {"c787_groups": cen["crossWriteGroups"],
                    "c787_touching": cen["groupsTouchingGates"],
                    "c787_actions": cen["storeActionsWritingGates"]},
         "claim": "★ 接上 action 调用之后，组数从 **6** 涨到 **%d**、"
                  "触到门状态的函数体从 **31** 涨到 **%d**"
                  % (cen["crossWriteGroups"], cen["groupsTouchingGates"])}
    assert cen["crossWriteGroups"] == 10, (
        "★ 组数不是 10（实为 %d）⟹ 四组里有哪组没被发现，要重查"
        % cen["crossWriteGroups"])
    checks.append(c)

    # ── D：★ 缺陷本身要被钉住 —— 786 那层**确实**不认识 action ──
    src786 = C786_SRC.read_text(encoding="utf-8")
    has_action = "store_action_writes" in src786 or '"action"' in src786
    d = {"id": "D:786 那层不认识 action（缺陷被钉住）", "ok": True, "n": 1,
         "detail": {"census786HasActionRecognition": has_action},
         "claim": "★ `census786.py` 里**没有**任何 action 识别（无 "
                  "`store_action_writes`、无 `\"action\"` 形态）⟹ "
                  "四组新增在 786 里是**结构性不可见**，不是「没找到」"}
    assert not has_action, (
        "★ census786.py 里已经有 action 识别了 ⟹ 786 那版的 raw 也要重算，D 的前提变了")
    checks.append(d)

    # ── E：与普查器对账（四组必须在 raw 里）──
    raw_keys = {"%s:%d" % (g["file"], g["startLine"]) for g in cen["crossWrites"]}
    expect = {"%s:%d" % (DT, 1532), "%s:%d" % (DT, 1574),
              "%s:%d" % (DV, 2835), "%s:%d" % (DV, 2842)}
    e = {"id": "E:四组都在 raw 里", "ok": True, "n": 1,
         "detail": {"rawKeys": sorted(raw_keys), "missing":
                    sorted(expect - raw_keys)},
         "claim": "★ 四组新增必须真的出现在普查产物里"}
    assert not (expect - raw_keys), "★ raw 里缺：%r" % sorted(expect - raw_keys)
    checks.append(e)

    out = {
        "batch": 787,
        "claims": {
            "C787-1": "★ `store action 调用`也是写入，而 786 那层只认 "
                      "`set<S>(` 与对象字面量键 ⟹ 组数 6 ⟹ **10**",
            "C787-2": "★★ **往模型库加条目会取消正在进行的运镜绘制**"
                      "（`DirectorViewport.tsx:2836-2837` / `:2843-2844`）——"
                      "两层普查都没报出过",
            "C787-3": "★ 这条限定了 786 的一处推论：「没有交叉写入」"
                      "**只在「层看得见全部写入」时才成立**"
        },
        "newGroups": [{"name": n, "file": f, "startLine": h,
                       "members": [{"line": ln, "needle": nd, "state": st}
                                   for ln, nd, st in sp]}
                      for n, f, h, sp in NEW_GROUPS],
        "actionAnchors": [{"action": a, "file": f, "line": ln, "needle": nd}
                          for a, f, ln, nd in ACTION_ANCHORS],
        "checks": checks,
        "totals": {"checks": len(checks),
                   "assertedAnchors": sum(c.get("n", 0) for c in checks),
                   "failed": sum(0 if c["ok"] else 1 for c in checks)},
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ C787-1：组数 6 ⟹ %d（触到门状态的函数体 31 ⟹ %d，"
          "识别出 %d 个写门状态的 store action）"
          % (cen["crossWriteGroups"], cen["groupsTouchingGates"],
             cen["storeActionsWritingGates"]))
    for n, f, h, sp in NEW_GROUPS:
        print("   %-32s %s:%d ⟹ %s"
              % (n, f.split("src/")[-1], h,
                 "、".join(x[2] for x in sp)))
    print("★ C787-2：★ 往模型库加条目 ⟹ 杀掉正在进行的运镜绘制")
    print("★ 断言 %d 条 / 锚点 %d 个 / 失败 %d"
          % (out["totals"]["checks"], out["totals"]["assertedAnchors"],
             out["totals"]["failed"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
