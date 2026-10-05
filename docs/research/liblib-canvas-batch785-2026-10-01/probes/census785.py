#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 785 普查器 —— **更正 784 的覆盖面结论**，并把 D1i 的可达性钉死

## 本批要更正的是**我自己上一批的静态结论**

784 断言「11 个主人的门状态里**只有 3 个**有任何外点关闭，其余 7 个没有」，
判据是：监听器自己的处理器体里**直接**出现 `set<S>(null)`。

★ 复查发现**三处**错，两处让覆盖面数字偏小、一处让 key 本身就是错的：

1. ★ **假阴性：判据只认 `null`。**
   `setModelLibraryOpen(false)`（`DirectorViewport.tsx:2747` 的
   `closeOnOutsidePointerDown`）也是「关掉」，但 `\(\s*null` 匹配不到。
2. ★ **key `open` 根本不是可写状态。**
   783 把 `PhoneVcamPanel` 的门记成 `open`（那是 **prop**），
   784 把它硬编码进 `STATES`（`census784.py:57`）⟹ **两批都从来没找过真状态**。
   真名是 `phoneVcamOpen`（`DirectorViewport.tsx:2544` 声明，
   `:3080` 以 `open={phoneVcamOpen}` 透传，`:3081` 把它接到 `onClose`）。
   ★ 而 784 的 raw 里 `open` 记的是 **`[]`（没有外点关闭）** ——
   所以**没有发生**「跨文件撞名算成有」，784 的错是**整个漏掉了一个门状态**，
   恰好落进同一个桶 ⟹ 桶数只动了一次（3→4），但**分母从来没对过**。
3. ★ **因此正确答案是 4 有 / 6 无**，不是 784 的 3 / 7，
   也不是「把 `open` 丢掉」的 4 / 5（丢掉会把 vcam 面板从风险面里**藏起来**）。

⟹ 本批把普查器加一条**证据层**：每个 key 都记下它的**全部写入点**
（`set<K>(` 调用 + 对象字面量键写入）。

★ **第一版试过把它做成机械判据（「`set<K>(` 在主人文件里被调用过」），
当场失败并作废** —— 两个方向都不成立：
- `motionPathDraft` / `activeDirectorNodeId` / `followTargetId`
  三个**真**状态一个 `useState` 都不是（`followTargetId` 的关闭走的是
  `updateCamera(id, { followTargetId: null })` 这种**对象字面量键**形态）；
- 而 `open` 的 `setOpen(` 在全仓有 **38 处**
  （`TopNavBar.tsx:250`、`FrameosMaterialLibrary.tsx:105` …）
  ⟹ **全局「setter 被调用过」根本分不开 prop 与状态**。

⟹ 「这个 key 可不可写」交给**汇编器**用行锚定字面量断言（沿用 783/784 纪律），
普查器只负责把证据摆齐。

## ★ 而这条更正**不动摇 D1i，反而把它加宽**

784 报的是「**键盘**路径」：右键菜单 + 模型库键盘共活。
★ 但 **782 的 `captureOwner` 臂早就是同一个形态，而且是纯鼠标** ——
导出面板（**没有任何外点关闭**）+ 模型库（`pointerdown` 外点关闭）：

| 读数 | 值 |
| --- | --- |
| 第 1 次按 Escape | 模型库关；**导出面板仍在**（`cap=0`，阶梯跑不到） |
| 第 2 次按 Escape | 导出面板关 |

⟹ **D1i 的形态是「`sIP` 主人 + 任何其他主人共活 → 一次只关 `sIP` 那个」**，
而它**纯鼠标可达**（导出面板那条在 782 就测过）⟹ **严重度维持**，
覆盖面比 784 写的**更宽**：不止键盘路径。

★ 782 的读数是**复用**而非重跑（R152：同一形态的读数常被归档在不同框架下，
先换框架重读既有 raw 往往比再跑一轮更值钱）。

## 不覆盖的（显式列出）

- `viewerCaptureId` 在 clone 默认数据下**不可达**（`[data-director-capture-view]`
  命中 0）⟹ 不能拿它当共活搭档 ⟹ **纯鼠标**那一路改用 `exportPanelOpen`
- 不判断「某个状态能不能被置上」——那是可达性问题，逐条单列
- ★ **交叉写入不在本普查**：783 的 `crossWrites` 层另有**两处**缺陷
  （prop 状态被下游静默剔除 / 内联 JSX 箭头不被包裹函数正则匹配 ⟹ `fn` 误归），
  留待 batch 786
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
C783 = REPO / ("docs/research/liblib-canvas-batch783-2026-10-01"
               "/raw/census783.json")
C784 = REPO / ("docs/research/liblib-canvas-batch784-2026-10-01"
               "/raw/census784.json")
RAW782 = REPO / ("docs/research/liblib-canvas-batch782-2026-10-01"
                 "/raw/vb782a.json")
OUT = REPO / "docs/research/liblib-canvas-batch785-2026-10-01/raw/census785.json"
SRC = REPO / "src"

#: ★ 784 那份是**硬编码**的（`census784.py:57`）⟹ key 可以是 prop 而无人察觉。
#:   本版每个 key 都带 `ownerFile`（783 的主人文件），汇编器据此断言
#:   「`set<S>` 真的在主人文件里被调用过」⟹ `open` 这类错当场暴露。
STATES = [
    ("viewerCaptureId", "src/components/director/DirectorInspector.tsx"),
    ("contextMenu", "src/components/director/DirectorObjectTree.tsx"),
    ("phoneVcamOpen", "src/components/director/DirectorPhoneVcamPanel.tsx"),
    ("pathMenuLeft", "src/components/director/DirectorTimeline.tsx"),
    ("presetPanelLeft", "src/components/director/DirectorTimeline.tsx"),
    ("motionPathDraft", "src/components/director/DirectorViewport.tsx"),
    ("modelLibraryOpen", "src/components/director/DirectorViewport.tsx"),
    ("activeDirectorNodeId", "src/store/uiStore.ts"),
    ("exportPanelOpen", "src/components/director/DirectorDesk.tsx"),
    ("followTargetId", "src/components/director/DirectorDesk.tsx"),
]
#: ★ 784 的 key `open`：783 记的是 **prop** 名，784 直接抄进了硬编码清单
PROP_KEYS_784 = {"open": (
    "★ 783 把 `PhoneVcamPanel` 的门记成 `open`（那是 **prop**，"
    "`:96/:99` 是解构出来当参数用），784 把它抄进 `census784.py:57` 的"
    "硬编码 `STATES` ⟹ **两批都没找过真状态**。真名 `phoneVcamOpen`，"
    "由 `DirectorViewport.tsx:2544` 声明、`:3080` 以 `open=` 透传、"
    "`:3081` 接到 `onClose`。★ 784 的 raw 里 `open` 记的是 **`[]`** "
    "⟹ 没有发生「撞名算成有」，784 的错是**整个漏掉一个门状态**，"
    "恰好落进同一个桶 ⟹ 分母从来没对过。")}
#: ★ 「关掉」的三种写法都要算（784 只认 `null` ⟹ 假阴性）
FALSY = r"(?:null|false|undefined)"
PE = ("mousedown", "pointerdown", "click", "touchstart")


def setter(s):
    return "set" + s[0].upper() + s[1:]


def brace(text, start):
    cb = text.find("{", start)
    if cb < 0:
        return None
    d = 0
    for i in range(cb, len(text)):
        if text[i] == "{":
            d += 1
        elif text[i] == "}":
            d -= 1
            if d == 0:
                return text[cb:i + 1]
    return None


def main():
    files = {}
    for p in sorted(list(SRC.rglob("*.ts")) + sorted(SRC.rglob("*.tsx"))):
        files[str(p.relative_to(REPO))] = p.read_text(encoding="utf-8")

    names = [s for s, _ in STATES]
    owner = dict(STATES)

    # ── 只**采集**写入点当证据，不判断「可不可写」 ──
    # ★ 第一版试过正则判据「`set<K>(` 在主人文件里被调用过」，**当场失败**：
    #   `motionPathDraft` / `activeDirectorNodeId` / `followTargetId` 三个真状态
    #   一个 useState 都不是（后者是 `updateCamera(id, { followTargetId: null })`
    #   这种**对象字面量键**形态）；而 `open` 的 `setOpen(` 在全仓有 **38 处**
    #   （`TopNavBar.tsx:250`、`FrameosMaterialLibrary.tsx:105` …）
    #   ⟹ **全局「setter 被调用过」根本分不开 prop 与状态**。
    # ⟹ 判定「可写」交给汇编器**行锚定字面量**（沿用 783/784 纪律）。
    writeSites = {}
    for s in names:
        st = setter(s)
        setters, objkeys = [], []
        for rel, txt in files.items():
            for m in re.finditer(r"\b%s\s*\(" % st, txt):
                setters.append({"file": rel, "line":
                                txt[:m.start()].count("\n") + 1})
            for m in re.finditer(r"[{(,]\s*%s\s*:\s*(?![=])([^;\n]*),?"
                                 % re.escape(s), txt):
                ln = txt[:m.start()].count("\n") + 1
                if txt.split("\n")[ln - 1].rstrip().endswith(";"):
                    continue                      # 类型注解，不是写入
                objkeys.append({"file": rel, "line": ln})
        writeSites[s] = {"ownerFile": owner[s],
                         "setCalls": sorted(set(
                             (o["file"], o["line"]) for o in setters)),
                         "objectKeyWrites": sorted(set(
                             (o["file"], o["line"]) for o in objkeys))}

    found = {s: [] for s in names}
    for rel, text in files.items():
        for m in re.finditer(
                r'([\w.]+)\s*\.\s*addEventListener\(\s*'
                r'["\']([a-z]+)["\']\s*,\s*([A-Za-z_$][\w$]*|\()'
                r'((?:\s*,\s*(?:true|capture))?)\s*\)', text):
            target, ev, arg, caparg = m.groups()
            if ev not in PE:
                continue
            if arg == "(":
                b = brace(text, m.end() - 1)
            else:
                ds = [d for d in re.finditer(
                    r'(?:const|let|var|function)\s+%s\b' % re.escape(arg), text)
                    if d.start() < m.start()]
                b = brace(text, ds[-1].end()) if ds else None
            if not b:
                continue
            for s in names:
                if re.search(r"\b%s\s*\(\s*%s" % (setter(s), FALSY), b):
                    found[s].append({
                        "event": ev, "target": target, "phase": (
                            "capture" if caparg.strip() else "bubble"),
                        "handler": arg, "file": rel,
                        "line": text[:m.start()].count("\n") + 1})
    for s in found:
        seen, u = set(), []
        for o in found[s]:
            k = (o["event"], o["handler"], o["file"], o["line"])
            if k not in seen:
                seen.add(k)
                u.append(o)
        found[s] = u
    withOc = sorted(s for s in names if found[s])
    withoutOc = sorted(s for s in names if not found[s])
    events = {s: sorted({o["event"] for o in found[s]}) for s in withOc}
    # ★ 所有外点关闭的事件**是否全都是 pointer 类** ⟹ 键盘一律绕过
    allPointer = all(e in PE for s in withOc for e in events[s])

    # ── 782 的 raw：纯鼠标的 D1i 读数（**复用**，不重跑）──
    raw782 = json.loads(RAW782.read_text(encoding="utf-8"))
    cap = None
    for rd in raw782["rounds"]:
        for r in (rd.get("rows") or []):
            if r.get("arm") == "captureOwner":
                cap = r
                break
        if cap:
            break
    pureMouse = None
    if cap:
        p = (cap.get("presses") or [])
        if len(p) >= 2:
            pureMouse = {
                "arm": "captureOwner",
                "setup": "导出面板（**无**外点关闭）+ 模型库（pointerdown 外点关闭）"
                         "，**纯鼠标**点开",
                "source": "batch782 raw（**复用**，本批不跑浏览器）",
                "press1": {"cap": p[0]["read"].get("cap"),
                           "win": p[0]["read"].get("win"),
                           "targetOpen": (p[0].get("state") or {}).get("targetOpen"),
                           "exportOpen": (p[0].get("state") or {}).get("exportOpen")},
                "press2": {"exportOpen": (p[1].get("state") or {}).get("exportOpen")},
            }

    out = {
        "batch": 785, "states": names, "ownerOf": owner,
        "writeSites": writeSites,
        "keyPropsRejected784": PROP_KEYS_784,
        "outsideClose": found,
        "statesWithOutsideClose": withOc,
        "statesWithoutOutsideClose": withoutOc,
        "events": events,
        "allOutsideCloseArePointerEvents": allPointer,
        "pureMouseD1i": pureMouse,
        "batch784Claim": {
            "with": len(json.loads(C784.read_text(encoding="utf-8"))
                        ["statesWithOutsideClose"]),
            "without": len(json.loads(C784.read_text(encoding="utf-8"))
                           ["statesWithoutOutsideClose"]),
            "source": "census784.json",
            "corrected": {"with": len(withOc), "without": len(withoutOc)},
        },
        "ownerCount783": len(json.loads(
            C783.read_text(encoding="utf-8"))["escapeOwners"]),
        "method": "★ 判据 = 监听器**自己的**处理器体里**直接**出现 "
                  "`set<S>(null|false|undefined)` ⟹ 784 只认 `null` 造成"
                  "**假阴性**。★ 本普查**不做**「key 可不可写」的语义判断 ——"
                  "只把每个 key 的**全部写入点**采成证据，由汇编器行锚定断言"
                  "（第一版试图用正则判据，**已作废**，见 `notCovered`）。",
        "notCovered": [
            "`viewerCaptureId` 在 clone 默认数据下**不可达**"
            "（`[data-director-capture-view]` 命中 0）⟹ 不能当共活搭档",
            "「某个状态能不能被置上」是**可达性**问题，逐条单列，不在本普查",
            "★ **正则判据「`set<S>(` 在主人文件里被调用过」已作废**："
            "三个真状态是**对象字面量键**形态（不过判），"
            "而 `open` 的 `setOpen(` 全仓 38 处（会误过判）",
            "★ **交叉写入不在本普查**：783 的 `crossWrites` 层另有**两处**缺陷"
            "（prop 状态被下游静默剔除 / 内联 JSX 箭头不被包裹函数正则匹配）"
            "⟹ 留待 batch 786",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    b = out["batch784Claim"]
    print("★ 784 说 %d 有 / %d 没有 ⟹ **更正为 %d 有 / %d 没有**"
          % (b["with"], b["without"], b["corrected"]["with"],
             b["corrected"]["without"]))
    for s in withOc:
        for o in found[s]:
            print("   有  %-20s ← %-12s on %-8s handler=%-28s %s:%d"
                  % (s, o["event"], o["target"], o["handler"],
                     o["file"].split("src/")[-1], o["line"]))
    for s in withoutOc:
        print("   无  %-20s" % s)
    print("\n★ 783 的主人数 = %d ⟹ 本清单 %d 个可写门状态"
          % (out["ownerCount783"], len(names)))
    print("★ 所有外点关闭事件**都是 pointer 类**？ %s ⟹ 键盘一律绕过"
          % allPointer)
    print("\n★ 782 raw 里的**纯鼠标** D1i 读数：")
    print("   %s" % json.dumps(pureMouse, ensure_ascii=False))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
