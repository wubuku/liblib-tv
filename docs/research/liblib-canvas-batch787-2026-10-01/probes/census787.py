#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 786 普查器 —— **重建 783 的 `crossWrites` 层**

## 783 那层为什么不能直接用

783 的结论（「`pathMenuLeft` 与 `presetPanelLeft` 因**打开者里的双向交叉写入**
而永不共活」）是对的，但它**得出结论的那层扫描**有三处缺陷 ——
本批把那三处逐条修掉，看**修好之后报出来的东西**是什么。

| 编号 | 缺陷 | 症状 |
| --- | --- | --- |
| ✗ 第①道 | **prop 名当状态名** | 783 把 `PhoneVcamPanel` 的门记成 `open` ⟹ 真状态 `phoneVcamOpen` **不在**喂给这层的 `states` 里 ⟹ 它跟谁交叉都看不见 |
| ✗ 第②道 | **内联 JSX 箭头不被包裹函数正则匹配** | 正则只认 `const NAME = (…) => {`；JSX 的 `onClick={() => {` 没有 `const` ⟹ 回溯**越过整个箭头**、落到更外层一个不相干的具名函数上。★ 症状实测：783 把 `setModelLibraryOpen` 的 `:3538` 记成 `fn: "openLocalModelLibraryImport", fnLine: 2859`，而那个函数体只有一行 `localModelLibraryInputRef.current?.click();`、**一个 setter 都没有** ⟹ `alsoWrites: []` 是在**错误的函数体**上算出来的 |
| ✗ 第③道 | **状态集按文件切** | 783 的 `states` 是「**同一个文件里**的门状态」⟹ 跨文件的写入者（`DirectorViewport` 关掉 `PhoneVcamPanel` 的 prop）看不见对面 |

## 本批的修法（只采集，不下语义结论）

- **状态集**：785 已更正过的 **11 个可写门状态**（含 `crowdPanelOpen` ——
  它**有门却没有 Escape 主人**，774 记过）；域 = 挂载域组件
  （`src/components/director/**` + `src/app/page.tsx`）。
- **写入点**：两种形态都要 —— `set<S>(` 调用、**对象字面量键**写入
  （`activeDirectorNodeId` / `followTargetId` / `motionPathDraft` 是 zustand 字段）。
- ★ **同一个函数体怎么定**：改用**括号链**（从写入点向上取最近未配对的 `{`）
  + 「这个 `{` 前面是不是 `=>`」⟹ 这就**天然**认得出 JSX 内联箭头；
  再补一条**简写箭头体**（`() => set({...})` 没有块体）的路径。
- **交叉写入**：同一个函数体里写了**几个**门状态、分别是什么。

## 不覆盖的（显式列出）

- 「两个状态能不能同时活着」是**可达性**，静态不可判 ⟹ 运行时的事（另做浏览器臂）
- 门状态的**可满足性**同上
- 本普查**只采集**，行锚定的结论由汇编器下
"""
import json
import pathlib
import re

REPO = pathlib.Path("/Users/yangjiefeng/Documents/wubuku/liblib-tv")
OUT = REPO / "docs/research/liblib-canvas-batch787-2026-10-01/raw/census787.json"

DV = "src/components/director/DirectorViewport.tsx"
DOMAIN_DIR = "src/components/director"

#: ★ 785 已更正过的可写门状态，**再加** `crowdPanelOpen`
#:   （它**有门却没有 Escape 主人** —— 774 记过「export/crowd 2/6 缺自己的主人」）
GATES = [
    "activeDirectorNodeId", "contextMenu", "crowdPanelOpen", "exportPanelOpen",
    "followTargetId", "modelLibraryOpen", "motionPathDraft", "pathMenuLeft",
    "phoneVcamOpen", "presetPanelLeft", "viewerCaptureId",
]

FALSY = r"(?:null|false|undefined)"


def is_type_annotation(line):
    """这一行是**类型标注**（`open: boolean;`）而不是真的写入？

    ★ 第一版用「以 `;` 结尾」当判据 ⟹ **误杀了真实写入**：
      `DirectorDesk.tsx:565` 的
      `if (activeCameraId) updateCamera(activeCameraId, { followTargetId: null });`
      同样以 `;` 结尾，却是一次**真的**门状态写入。
    ⟹ 换成机械判据：**类型标注里不会出现 `(` 或 `=>`**，
      真的写入则一定带着一次调用（`() =>` 或 `updateCamera(`）。
    """
    t = line.rstrip()
    return t.endswith(";") and "(" not in t and "=>" not in t


def setter(s):
    return "set" + s[0].upper() + s[1:]


def domain_files():
    out = [REPO / (DOMAIN_DIR + "/" + p.name)
           for p in sorted((REPO / DOMAIN_DIR).glob("*.tsx"))]
    out.append(REPO / "src/app/page.tsx")
    return [p for p in out if p.exists()]


def enclosing_chain(text, pos):
    """从 `pos` 往上取**最近**的未配对 `{`，一路往外（由内到外）。"""
    stack, i = [], 0
    while i < pos:
        c = text[i]
        if c == "{":
            stack.append(i)
        elif c == "}":
            if stack:
                stack.pop()
        i += 1
    out = []
    for start in reversed(stack):
        d, j = 0, start
        while j < len(text):
            if text[j] == "{":
                d += 1
            elif text[j] == "}":
                d -= 1
                if d == 0:
                    break
            j += 1
        out.append((start, j))
    return out


LABEL_PATTERNS = [
    re.compile(r"(?:const|let|var|function)\s+([A-Za-z_$][\w$]*)\s*(?:=\s*)?"
               r"(?:\([^)]*\)|[A-Za-z_$][\w$]*)?\s*=>\s*$"),
    re.compile(r"(on[A-Za-z]+)\s*=\s*\{\s*$"),
    re.compile(r"addEventListener\(\s*[\"']([a-z]+)[\"']\s*,\s*$"),
    re.compile(r"([A-Za-z_$][\w$]*)\s*:\s*(?:async\s*)?function\b[^()]*$"),
]


def label_of(head):
    """这个箭头/函数体归谁？返回 `(kind, name)`。"""
    h = head.rstrip()
    for i, pat in enumerate(LABEL_PATTERNS):
        m = pat.search(h)
        if m:
            kind = ("named-arrow" if i == 0 else
                    "jsx-handler" if i == 1 else
                    "event-listener" if i == 2 else "method")
            return kind, m.group(1)
    return "anonymous-arrow", None


def group_span(text, pos):
    """写入点所在的**函数体**跨度。返回 `(start, end, kind, name)` 或 None。"""
    chain = enclosing_chain(text, pos)
    for bstart, bend in chain:                     # 情形 A：块体箭头
        head = text[:bstart].rstrip()
        if head.endswith("=>"):
            kind, name = label_of(head)
            return bstart, bend, kind, name
    # 情形 B：简写箭头体 `() => expr`（没有 `{`）
    floor = chain[-1][0] if chain else 0
    seg = text[floor:pos]
    k = seg.rfind("=>")
    if k >= 0:
        start = floor + k + 2
        d, j = 0, start
        while j < len(text):                      # 到同深度的 `,` / `;` 为止
            c = text[j]
            if c in "([{":
                d += 1
            elif c in ")]}":
                if d == 0:
                    break
                d -= 1
            elif d == 0 and c in ",;":
                break
            j += 1
        kind, name = label_of(text[floor:start])
        return start, j, kind or "concise-arrow", name
    return None


def writes_in(text, start, end, actions):
    """这个函数体里写了哪些门状态。

    ★ **三种形态**都要：`set<S>(` 调用、**对象字面量键**、★ **store action 调用**。
    """
    body = text[start:end]
    hits = {}
    for a in sorted(actions):
        if re.search(r"(?<![\w.$])%s\s*\(" % re.escape(a), body):
            for s in actions[a]["fields"]:
                hits.setdefault(s, []).append(
                    {"line": text[:start].count("\n") + 1,
                     "form": "action", "arg": a + "("})
    for s in GATES:
        st = setter(s)
        for m in re.finditer(r"\b%s\s*\(" % re.escape(st), body):
            hits.setdefault(s, []).append(
                {"line": text[:start + m.start()].count("\n") + 1,
                 "form": "setter", "arg": m.group(0)})
        for m in re.finditer(r"[{(,]\s*%s\s*:\s*" % re.escape(s), body):
            ln = text[:start + m.start()].count("\n") + 1
            code = text.split("\n")[ln - 1]
            if is_type_annotation(code):
                continue
            hits.setdefault(s, []).append(
                {"line": ln, "form": "objectKey", "arg": s + ":"})
    return hits


def rung_count(text, start, end):
    """这个函数体里有几处「写了门状态**并且**紧接着 return」。"""
    body = text[start:end]
    lines = body.split("\n")
    n = 0
    for i, ln in enumerate(lines):
        if not re.search(r"\bset[A-Z]\w*\s*\(", ln) and \
                not re.search(r"[{(,]\s*\w+\s*:\s*(?:null|false|undefined)", ln):
            continue
        rest = "\n".join(lines[i:i + 3])
        if re.search(r"\breturn\b", rest):
            n += 1
    return n


def write_sites(text, actions):
    """本文件里所有门状态写入点（位置 + 所属函数体）。"""
    out = []
    spans = {}
    for s in GATES:
        st = setter(s)
        for m in re.finditer(r"\b%s\s*\(" % re.escape(st), text):
            out.append((m.start(), s, "setter", m.group(0)))
        for m in re.finditer(r"[{(,]\s*%s\s*:\s*(?![=])" % re.escape(s), text):
            ln = text[:m.start()].count("\n") + 1
            code = text.split("\n")[ln - 1]
            if is_type_annotation(code):
                continue
            out.append((m.start(), s, "objectKey", s + ":"))
    # ★ store **action 调用**也是写入（`startMotionPathDrawing(tool)` 写
    #   `motionPathDraft`）—— 786 只认上面两种形态 ⟹ 这类调用**完全隐形**
    for a in sorted(actions):
        for m in re.finditer(r"(?<![\w.$])%s\s*\(" % re.escape(a), text):
            ln = text[:m.start()].count("\n") + 1
            if is_type_annotation(text.split("\n")[ln - 1]):
                continue
            out.append((m.start(), actions[a]["fields"][0],
                        "action:" + a, a + "("))
    for pos, s, form, arg in sorted(out):
        g = group_span(text, pos)
        if not g:
            continue
        start, end, kind, name = g
        key = (start, end)
        if key not in spans:
            spans[key] = {
                "file": None, "startLine": text[:start].count("\n") + 1,
                "kind": kind, "name": name,
                "writes": {k: v for k, v in
                           sorted(writes_in(text, start, end, actions).items())},
                "members": [],
            }
        spans[key]["members"].append(
            {"state": s, "form": form, "line": text[:pos].count("\n") + 1,
             "arg": arg,
             "fields": (actions[form.split(":", 1)[1]]["fields"]
                        if form.startswith("action:") else [s])})
    return spans


STORE_CREATE = re.compile(r"create<[^>]*>\(\([^)]*\)\s*=>\s*\(\{")


def store_action_writes():
    """扫 store 文件 ⟹ `{action 名: 它写了哪些门状态}`。

    ★ 必须**先锚定** `create<…>((set, get) => ({` —— 只按 `^  name:` 匹配会把
    `state` / `value` / `plan` 这类局部名也当成 action（第一版就是这么脏的）。
    ★ 字段扫描必须**跨行**：`motionPathDraft` 在 `directorStore.ts:7780` 是
      对象字面体里的一行，**行内**看不到它前面那个 `,`。
    """
    out = {}
    for sp in sorted(list((REPO / "src/store").glob("*.ts"))):
        text = sp.read_text(encoding="utf-8")
        lines = text.split("\n")
        anchor = STORE_CREATE.search(text)
        if not anchor:
            continue
        keys = [(km.group(1), km.start()) for km in
                re.finditer(r"(?m)^  ([A-Za-z_$][\w$]*)\s*:", text)
                if km.start() > anchor.end()]
        for i, (name, pos) in enumerate(keys):
            end = keys[i + 1][1] if i + 1 < len(keys) else len(text)
            seg = text[pos:end]
            fields = set()
            for g in GATES:
                if re.search(r"\b%s\s*\(" % re.escape(setter(g)), seg):
                    fields.add(g)
                    continue
                for om in re.finditer(r"[{,]\s*%s\s*:" % re.escape(g), seg):
                    ln = text[:pos + om.start()].count("\n") + 1
                    if not is_type_annotation(lines[ln - 1]):
                        fields.add(g)
                        break
            if fields:
                out[name] = {"file": str(sp.relative_to(REPO)),
                             "fields": sorted(fields)}
    return out


def main():
    actions = store_action_writes()
    groups = []
    for p in domain_files():
        rel = str(p.relative_to(REPO))
        text = p.read_text(encoding="utf-8")
        for (start, end), g in sorted(write_sites(text, actions).items()):
            g["file"] = rel
            written = sorted(g["writes"])
            g["writesMulti"] = written
            g["crossWrite"] = len(written) >= 2
            # ★ 第三种互斥机制：**早退阶梯** —— 同一个函数体里写了 ≥2 个门状态，
            #   但每一档都带 `return` ⟹ 一次调用最多走一档 ⟹ 它们**不是**交叉写入。
            #   （`DirectorDesk.tsx:549-568` 的 Escape 阶梯就是这一档。）
            g["earlyReturnRungs"] = rung_count(text, start, end)
            # ★ **三种**互斥机制，分开记（第一版只有「有 / 没有」两档，
            #   于是把「早退阶梯」误当成了「交叉写入」）：
            #   `early-return-ladder` ⟹ **每一**写入后面都 return ⟹ 一次调用
            #     最多走一档，**不是**交叉写入；
            #   `cross-write+ladders` ⟹ 既有无条件的交叉写入、也有早退档；
            #   `cross-write` ⟹ 全是无条件写入。
            r = g["earlyReturnRungs"]
            g["mechanism"] = ("early-return-ladder" if r >= len(written)
                              else "cross-write+ladders" if r else "cross-write")
            # 只留「自己写了门状态、且同一个函数体里还写了别的」的
            groups.append(g)

    cross = [g for g in groups if g["crossWrite"]]
    out = {
        "batch": 787,
        "domain": {"files": len(domain_files()),
                   "dir": DOMAIN_DIR, "plus": "src/app/page.tsx"},
        "gates": GATES,
        "storeActionsWritingGates": len(actions),
        "storeActions": actions,
        "groupsTouchingGates": len(groups),
        "crossWriteGroups": len(cross),
        "crossWrites": [
            {k: g[k] for k in ("file", "startLine", "kind", "name",
                               "writesMulti", "earlyReturnRungs", "mechanism")}
            for g in cross],
        "allGroups": [
            {k: g[k] for k in ("file", "startLine", "kind", "name",
                               "writesMulti", "members", "earlyReturnRungs", "mechanism")}
            for g in groups],
        "fixesVs783": [
            "✗第①道 prop 名当状态名 ⟹ 改用 785 更正过的 `phoneVcamOpen`",
            "✗第②道 内联 JSX 箭头不被包裹函数正则匹配 ⟹ 改用**括号链 + `=>` 判定**"
            "（783 把 `:3538` 误归到 `openLocalModelLibraryImport:2859`）",
            "✗第③道 状态集按文件切 ⟹ 改成**全域** 11 个门状态",
            "＋ 补一条**简写箭头体**路径（`() => set({...})` 没有块体）",
            "★★ **第④个缺陷（batch 787）**：**store action 调用**也是写入，"
            "而 786 只认 `set<S>(` 与对象字面量键 ⟹ "
            "`DirectorTimeline.tsx:1533` 的 `startMotionPathDrawing(tool);` 隐形",
        ],
        "method": "★ **只采集**：写入点 → **括号链**定函数体（`{` 前是不是 `=>`）"
                  " ⟹ 天然认得出 JSX 内联箭头；简写箭头体单走一条路。"
                  "★ 交叉写入 = **同一个函数体**里写了 ≥2 个门状态。",
        "notCovered": [
            "「两个状态能不能同时活着」是**可达性**，静态不可判 ⟹ 运行时",
            "本普查**只采集**，行锚定的结论由汇编器下",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    print("★ 域 %d 个文件、门状态 %d 个" % (out["domain"]["files"], len(GATES)))
    print("★ 写了门状态的 store action：%d 个（786 完全不认这一形态）" % len(actions))
    print("★ 触到门状态的函数体：%d 个" % len(groups))
    print("★ 其中**交叉写入**（同一函数体写了 ≥2 个门状态）：%d 个"
          % len(cross))
    for g in cross:
        print("   %s:%d  %s %-26s ⟹ %s"
              % (g["file"].split("src/")[-1], g["startLine"], g["kind"],
                 g["name"] or "-", "、".join(g["writesMulti"])))
    print("wrote %s" % OUT)


if __name__ == "__main__":
    main()
