#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 784 普查器 —— 只采一件机械可靠的事：**哪些 Escape 主人的浮层有外点关闭**

## 783 留下的缺口

783 发现「主人的门互相独立」≠「主人可以同时活着」，真机制是**打开者里的
交叉写入**。但 783 **只查了 `DirectorTimeline` 内部**，其余 9 个主人之间
有没有同类机制，**从来没查过**。

⟹ 而 774 那个悬着的问题（「层内 Escape 只关层」全族只有 2/6 做对）背后是：
**可靠机制总共只有两种** ——

| 机制 | 能挡住什么 |
| --- | --- |
| **外点关闭** | 产生那个 pointer 事件的激活方式（**键盘不产生** ⟹ 只挡鼠标） |
| **打开者里的交叉写入** | 任何激活方式（783 已证，双向） |

本普查把**外点关闭**这一种在**全仓**清点一遍。

## ★★ 两版都踩的坑（第三版才对），记下来

**第一版**：用「取门状态 `ids` 的第一个」⟹ 给 `DirectorDesk:570` 算出
`state=capture`（它真正的门是「桌开着」）⟹ **783 明令禁止的语义判断，
换个形式又犯了一次**。

**第二版**：判据是「这条 pointer 监听**所在的 `useEffect` 体**里有没有
`set<S>(null)`」⟹ 抓到一个**假阳性** `DirectorTimeline.tsx:771`
（`pointerup` / `handleUp`）—— 那是一段**拖拽结束**的清理逻辑，
而且 `handleUp` 是**一跳间接**调 `cleanup()` → `setPresetPanelLeft(null)`，
它根本不是「点外面关掉面板」。

⟹ **第三版的判据**（机械、无歧义）：

> 对每条 `mousedown`/`pointerdown`/`click` 监听，
> 取它注册的**处理器函数体**，要求 `set<S>(null)` **直接出现在那个函数体里**。

⟹ 「直接出现」这条同时排掉两件事：**不在 effect 里的代码**（第一、二版的
假阳性来源）与**一跳间接调用**（拖拽清理）。

## 不覆盖的（显式列出）

- **谁的门状态是哪个** —— 由汇编器逐条行锚定，不在这里判
- **键盘可达性** —— 静态不可判，运行时的事
- 交叉写入（783 已用行锚定字面量钉死）—— 本普查**不重复扫**
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUT = REPO / ("docs/research/liblib-canvas-batch784-2026-10-01"
              "/raw/census784.json")
SRC = REPO / "src"

#: 这 10 个门状态由**汇编器**逐条行锚定钉死，这里只拿来扫描
STATES = ["viewerCaptureId", "contextMenu", "open", "pathMenuLeft",
          "presetPanelLeft", "motionPathDraft", "modelLibraryOpen",
          "activeDirectorNodeId", "exportPanelOpen", "followTargetId"]

LISTEN_RX = re.compile(
    r"(window|document|[\w.]+)\s*\.\s*addEventListener\(\s*"
    r"[\"']([a-z]+)[\"']\s*,\s*([A-Za-z_$][\w$]*|)")
POINTER_EVENTS = ("mousedown", "pointerdown", "click", "touchstart")
DECL_RX = "(?:const|let|var|function)\\s+%s\\b"


def match(text, op, cl, idx):
    depth = 0
    for i in range(idx, len(text)):
        if text[i] == op:
            depth += 1
        elif text[i] == cl:
            depth -= 1
            if depth == 0:
                return i
    return -1


def setter(state):
    return "set" + state[0].upper() + state[1:]


def handler_body(text, name, from_idx):
    """取处理器**自己的**函数体（括号配对）。找不到就返回 None。"""
    if name == "":                       # 内联箭头：`(event) => {`
        cb = text.find("=>", from_idx)
        cb = text.find("{", cb) if cb > 0 else -1
    else:
        rx = re.compile(DECL_RX % re.escape(name))
        best = None
        for m in rx.finditer(text):
            if m.start() >= from_idx:
                break
            best = m
        if best is None:
            return None
        cb = text.find("{", best.end())
        if cb < 0:                       # `const f = (e) => expr` 形态
            arrow = text.find("=>", best.end())
            cb = text.find("{", arrow) if arrow > 0 else -1
    if cb < 0:
        return None
    cl = match(text, "{", "}", cb)
    return text[cb:cl + 1] if cl > 0 else None


def main():
    files = {}
    for p in sorted(list(SRC.rglob("*.ts")) + sorted(SRC.rglob("*.tsx"))):
        files[str(p.relative_to(REPO))] = p.read_text(encoding="utf-8")
    outside = {s: [] for s in STATES}
    scanned = 0
    for rel, text in files.items():
        for m in LISTEN_RX.finditer(text):
            ev, handler = m.group(2), m.group(3)
            if ev not in POINTER_EVENTS:
                continue
            scanned += 1
            body = handler_body(text, handler, m.start())
            if not body:
                continue
            for s in STATES:
                # ★ **直接**出现在处理器自己的函数体里（排除一跳间接）
                if re.search(r"\b%s\s*\(\s*null" % setter(s), body):
                    outside[s].append({
                        "event": ev, "target": m.group(1), "handler": handler,
                        "file": rel,
                        "line": text[:m.start()].count("\n") + 1})
    for s in outside:
        seen, uniq = set(), []
        for o in outside[s]:
            k = (o["event"], o["handler"], o["file"], o["line"])
            if k not in seen:
                seen.add(k)
                uniq.append(o)
        outside[s] = uniq
    withAny = sorted(s for s in STATES if outside[s])
    without = sorted(s for s in STATES if not outside[s])
    out = {
        "batch": 784, "states": STATES, "outsideClose": outside,
        "statesWithOutsideClose": withAny,
        "statesWithoutOutsideClose": without,
        "pointerListenersScanned": scanned,
        "method": "★ 判据：每条 `mousedown`/`pointerdown`/`click` 监听，"
                  "取它注册的**处理器函数体**，要求 `set<S>(null)` "
                  "**直接**出现在里面 ⟹ 同时排掉「不在 effect 里的代码」"
                  "与「一跳间接调用」（`DirectorTimeline:771` 的 "
                  "`pointerup`/`handleUp` → `cleanup()` 就是后者）。"
                  "★ **不做任何归类**（前两版用「`ids` 第一个」猜门状态、"
                  "用「所在 effect」判外点，都错了）。",
        "notCovered": [
            "**谁的门状态是哪个** —— 由汇编器逐条行锚定",
            "**键盘可达性** —— 静态不可判，运行时的事",
            "交叉写入（783 已用行锚定字面量钉死）—— 本普查不重复扫",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("扫了 %d 个文件、%d 条 pointer/mouse 监听"
          % (len(files), scanned))
    print("\n★ **有**外点关闭的门状态（%d 个）：" % len(withAny))
    for s in withAny:
        for o in outside[s]:
            print("   %-20s ← %-12s handler=%-14s %s:%d"
                  % (s, o["event"], o["handler"],
                     o["file"].split("src/")[-1], o["line"]))
    print("\n★ **没有**任何外点关闭的门状态（%d 个）：%r" % (len(without),
                                                          without))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
