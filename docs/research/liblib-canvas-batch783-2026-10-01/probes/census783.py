#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 783 普查器 —— 11 个 `Escape` 主人：**门** 与 **打开者里的交叉写入**

## 782 数出了 11 个主人，但只数了**形态**（相位 / 有没有 `sIP`），
没数**它们能不能同时活着**。而这才决定 Escape 的真实行为。

## ★★ 本批第一版走错了路，而且错了两次 —— 记在最前面

**第一次**：想给每个主人标一个「激活门」，规则是「在 `useEffect` 体里找
`if (COND) return;`，提到 `event.key` 的是键守卫、其余是激活门」。两处都错：

1. **正则吃不下条件里的 `)`** —— `if (!resolveLibTVBlockingForegroundSurface
   (uiState)) return;` 里 `uiState)` 先把 `[^)]*` 截断 ⟹ `page.tsx:1400`
   的门**整条丢失**，而输出里仍有另一条门的标识符，**看起来像个正常结果**。
2. **「激活门」这个分类学本身站不住** —— 它把桌的 `:487`
   `if (isEditable) return;` 也算成激活门，而那是**分发守卫**
   （它筛修饰键，不是「我是否活着」）。

**第二次**：改成一两两判「A 的条件有没有提到 B 的状态」，结果被
`Escape` / `key` / `target` / `Node` 淹没 —— 45 对「互相牵制」，全是噪声。

⟹ **两次的共同教训：普查器不该做语义判断。**
⟹ 本版只**采集**（每条 `if` 的条件用**括号配对**取、记行号与标识符），
**结论由汇编器用行锚定的字面量断言下**（782 验收器已验证这条路）。

## ★★ 本批真正的发现：互斥不变量**藏在主人普查看不见的地方**

`DirectorTimeline` 的两个 Escape 主人（`:570` / `:594`），
从普查看是**两个门状态互不相关**的主人 ⟹ 看起来「可能同时活着」。
★ 而真正让它们互斥的是**两个「打开者」里各一行的显式交叉写入**：

- `togglePathMenu`（`:601-614`）第 3 行：`setPresetPanelLeft(null);`
- `togglePresetPanel`（`:695-709`）第 10 行：`setPathMenuLeft(null);`

⟹ **「主人的门互相独立」≠「主人可以同时活着」** ——
不变量写在**打开者**里，而任何「键盘主人普查」都不会去看打开者。
⟹ 本普查因此**加一层 `crossWrites` 扫描**：找每个主人自己的 `set<S>(…)`
在**别的函数**里的落点，并看那个函数是否**顺手写了另一个主人的状态**。

## 不覆盖的（显式列出）

- 门的**可满足性**静态不可判 ⟹ 运行时的事
- 键守卫 / 分发守卫 / 输入过滤器**不分类** ⟹ 本普查只采集，不下语义结论
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
C782 = REPO / ("docs/research/liblib-canvas-batch782-2026-10-01"
               "/raw/census782.json")
OUT = REPO / ("docs/research/liblib-canvas-batch783-2026-10-01"
              "/raw/census783.json")

SURFACE_PRED = "resolveLibTVBlockingForegroundSurface"
#: 条件里**不是状态**的东西（只用于展示；**不参与**任何结论）
NOISE = {"if", "return", "true", "false", "null", "undefined", "event",
         "isComposing", "isLibTVEditableCommandTarget", "querySelector",
         "getState", "activeElement", "contains", "length", "includes",
         "key", "code", "target", "currentTarget", "Node", "instanceof",
         "Escape", "Enter", "Tab", "Delete", "Backspace", "Space"}


def blank_comments(line):
    i = line.find("//")
    return line if i < 0 else line[:i]


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


def effect_span(lines, reg_line):
    for n in range(reg_line, 0, -1):
        if "useEffect(" in blank_comments(lines[n - 1]):
            text = "\n".join(lines[n - 1:])
            op = text.index("(", text.index("useEffect") + 9)
            cb = text.index("{", op)
            end = match(text, "{", "}", cb)
            return n, (text[:end + 1] if end > 0 else text)
    return None, ""


def conditions(body, off):
    """★ `if (…)` 的条件用**括号配对**取 —— 吃得下 `f(uiState)` 这种嵌套。"""
    out = []
    for m in re.finditer(r"\bif\s*\(", body):
        op = body.index("(", m.end() - 1)
        cl = match(body, "(", ")", op)
        if cl < 0:
            continue
        out.append({"line": off + body[:m.start()].count("\n") + 1,
                    "cond": " ".join(body[op + 1:cl].split()),
                    "returns": body[cl + 1:cl + 40].lstrip()
                    .startswith("return")})
    return out


def ids_in(cond):
    return sorted({m.group(1) for m in
                   re.finditer(r"\b([A-Za-z_$][\w$]*)\b", cond)
                   if m.group(1) not in NOISE})


def cross_writes(lines, states):
    """★ 每个状态 `S` 的**写入点**在哪个函数里，那个函数**有没有顺手写别的状态**。"""
    text = "\n".join(lines)
    out = []
    for s in states:
        setter = "set" + s[0].upper() + s[1:]
        for m in re.finditer(r"\b%s\s*\(" % setter, text):
            ln = text[:m.start()].count("\n") + 1
            # 往上找包裹这个调用的最近一层 `const NAME = (…) => {` / `function`
            fn, fnLine = None, None
            for n in range(ln, 0, -1):
                code = blank_comments(lines[n - 1])
                fm = re.search(r"(?:const|function)\s+([A-Za-z_$][\w$]*)\s*"
                               r"(?:=\s*)?(?:\([^)]*\)|[A-Za-z_$][\w$]*)\s*"
                               r"(?:=>\s*)?\{", code)
                if fm:
                    fn, fnLine = fm.group(1), n
                    break
            if not fn:
                continue
            # 该函数体内还写了谁？
            start = "\n".join(lines[fnLine - 1:])
            cb = start.index("{")
            cl = match(start, "{", "}", cb)
            body = start[:cl + 1] if cl > 0 else start
            others = sorted({o for o in states if o != s
                            and re.search(r"\bset%s\s*\(" % (
                                o[0].upper() + o[1:]), body)})
            out.append({"state": s, "setterLine": ln, "fn": fn,
                        "fnLine": fnLine, "alsoWrites": others,
                        "inEffect": "useEffect(" in "\n".join(
                            lines[max(0, fnLine - 3):fnLine])})
    return out


def main():
    cen = json.loads(C782.read_text(encoding="utf-8"))
    owners = [o for o in cen["owners"] if "Escape" in o["keys"]]
    rows, allStates = [], {}
    for o in owners:
        p = REPO / o["file"]
        lines = p.read_text(encoding="utf-8").split("\n")
        short = "%s:%d" % (o["file"].split("src/")[-1], o["regLine"])
        if o["handler"] == "inline":
            rows.append({
                "short": short, "file": o["file"], "regLine": o["regLine"],
                "scope": o["scope"], "kind": "prop",
                "conds": [{"line": o["regLine"], "cond": "(React prop)",
                           "returns": False}],
                "ids": [], "sIP": o["stopsImmediate"],
                "capture": o["capture"], "crossWrites": [],
            })
            continue
        start, body = effect_span(lines, o["regLine"])
        conds = conditions(body, (start - 1) if start else 0)
        # ★ 只把**门**（`if … return;`）里的标识符当状态；键守卫不算
        ids = sorted({i for c in conds if c["returns"] and "event" not in c["cond"]
                      for i in ids_in(c["cond"])})
        for i in ids:
            allStates.setdefault(i, []).append(short)
        rows.append({
            "short": short, "file": o["file"], "regLine": o["regLine"],
            "scope": o["scope"], "kind": "effect",
            "conds": conds, "ids": ids, "sIP": o["stopsImmediate"],
            "capture": o["capture"], "crossWrites": [],
        })
    # ── 交叉写入：只在**同一文件内**、且写入点在**别的函数**（非自己的 effect）──
    byFile = {}
    for r in rows:
        byFile.setdefault(r["file"], []).append(r)
    for f, rs in byFile.items():
        lines = (REPO / f).read_text(encoding="utf-8").split("\n")
        states = sorted({i for r in rs for i in r["ids"]})
        if len(states) < 2:
            continue
        for r in rs:
            # ★ 必须传**同文件全部**门状态：`others` 是「这个函数顺手写了谁」，
            #   只传自己的 ids 的话 `others` 恒为空，扫描静默返回空集
            r["crossWrites"] = [w for w in cross_writes(lines, states)
                                if not w["inEffect"] and w["state"] in r["ids"]]
    shared = {s: v for s, v in allStates.items() if len(v) > 1}
    xw = [{"file": f,
           "pairs": sorted({(r["ids"][0] if r["ids"] else None,
                             tuple(w["alsoWrites"]), w["fn"], w["fnLine"])
                            for r in rs for w in r["crossWrites"]})}
          for f, rs in byFile.items()
          if any(w["alsoWrites"] for r in rs for w in r["crossWrites"])]
    out = {
        "batch": 783, "escapeOwners": rows,
        "gateStates": allStates, "sharedGateStates": shared,
        "crossWriteFiles": xw,
        "surfaceGated": [r["short"] for r in rows
                         if any(SURFACE_PRED in c["cond"] for c in r["conds"])],
        # ★ `page.tsx:1400` 与 `:1401` 注册在**同一个 `useEffect`** 里
        #   ⟹ 逐主人的「门归属」在那一处是**歧义**的（普查器只能看到整个
        #   effect 的全部守卫）。这不影响结论（782 已分别用字面量钉死两道门），
        #   但**必须写明**，不能让产物看起来像两个主人各有各的门。
        "sharedEffectOwners": sorted(
            r["short"] for r in rows
            if sum(1 for q in rows
                   if q["file"] == r["file"]
                   and q["conds"] and r["conds"]
                   and q["conds"][0]["line"] == r["conds"][0]["line"]) > 1),
        "method": "★ 只**采集**：每条 `if (…)` 的条件用**括号配对**取、记行号；"
                  "**不做门分类**（第一版分类学与两两判据都因噪声失败）。"
                  "★ 另加一层 `crossWrites`：找每个门状态的写入点落在哪个函数、"
                  "那个函数**有没有顺手写另一个门状态** —— 不变量就藏在这里。",
        "notCovered": [
            "门的**可满足性**静态不可判 ⟹ 运行时的事",
            "键守卫 / 分发守卫 / 输入过滤器**不分类**",
            "本普查**只扫同一个文件内**的交叉写入",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("Escape 主人 %d 个" % len(rows))
    for r in rows:
        g = [c for c in r["conds"] if c["returns"] and "event" not in c["cond"]]
        print("%-42s %-6s %-4s 门状态=%-30s"
              % (r["short"], "capture" if r["capture"] else "bubble",
                 "sIP" if r["sIP"] else "-", ",".join(r["ids"]) or "—"))
        for c in g:
            print("%44s 门@%d: if (%s) return;" % ("", c["line"], c["cond"][:60]))
    print("\n★ 门状态 %d 个；**被两个以上主人共用**的：%r" % (len(allStates), shared))
    print("★ 交叉写入（同文件、写在别的函数里）：")
    for f in xw:
        for p in f["pairs"]:
            print("   %s  写 %s 时**顺手写** %s  （%s:%d）"
                  % (f["file"].split("src/")[-1], p[0], list(p[1]), p[2], p[3]))
    print("★ 被 `%s` 门控：%r" % (SURFACE_PRED, out["surfaceGated"]))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
