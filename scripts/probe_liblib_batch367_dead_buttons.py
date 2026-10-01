#!/usr/bin/env python3
"""Batch 367 普查: 画布本体里「自称可点却没有接线, 也没自证惰性」的 button。

## 为什么要有这个工具

Batch 366 的发现: 覆盖普查用 `data-*` 标记衡量「有没有被验证过」, 但**标记
体系本身有洞** —— `StoryboardScriptEditor` 里几十个 button 只有一个带标记,
于是「标记覆盖率」会让人**低估**组件的控件数, 死控件藏在没标记的那些里。

所以补一个**不依赖标记**的判据: 直接扫源码里的 `<button>`, 看它是否
「自称可点」(有 `aria-label` / `data-testid` / `role="button"`) 却同时
满足「无 onClick / 无 disabled / 无 data-inert」。

## 判据的三个陷阱(都已踩过, 别再踩)

1. **不能只扫顶层目录**。第一版用 `COMPONENTS.glob("*.tsx")`, 那是**非递归**的,
   于是 `src/components/nodes/`(16 个 tsx, **画布本体核心**: VideoNode /
   ImageNode / AudioNode 全在这儿) 整个被跳过。
   而 batch 364 亲手修掉的「播放视频」死控件**就在 `nodes/VideoNode.tsx`** ——
   也就是说: 上一批已经证明这条线存在这类缺陷, 普查工具却对它失明。
   靠塞一个 `ZzProbeTmp` 阳性对照才抓出来(见下方「下界自检」)。
   **教训: 判据的下界必须在「你以为覆盖的每个目录」上分别验证, 不能只在顶层验一次。**
   -> 改成 `rglob`, 并按**相对路径**判定跨线, 而不是只看文件名。

2. **不能用固定行数窗口扫属性**。第一版用「从 `<button` 那一行往后 3 行」
   判断有没有 onClick, 结果把 `TopNavBar` 的「积分余额」误报成死控件 ——
   它的 `data-inert` / `title` 写在**标签内部**、跨了好几行, 窗口没覆盖到。
   而它其实在 batch 358 就已经被正确处理过。**误报已处理的控件, 会导致
   重复改动或撞上既有门禁钉住的约定**, 危害比漏报大得多。
   -> 改成解析**完整标签**(`<button` 到配对的 `>`), 逐个属性判。

3. **读数类不是控件**。「积分余额」是个只读显示, 不是承诺可点的操作。
   它已被 batch358 正确处理(`data-inert` + title), 本工具也会认出来 ——
   但真要新增判据, 必须先问「它是不是在承诺一个动作」。

## 下界自检(必须双向, 见 scripts/verify-liblib-batch367.py)

- **下界**: 往 `src/components/nodes/` 塞一个明知死掉的按钮, 工具必须报出来。
  修复前的版本**报不出来** —— 这正是递归缺失的证据。
- **上界**: 同一文件里的「已接线 / 已 inert / 已禁用」三个阴性对照必须都不报。

## 输出

只报告**源码层面**的候选。是否可触达、是否真的骗人, 要用浏览器实测确认 ——
本工具不越权下结论。
"""

from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ROOT / "src" / "components"
OUT = ROOT / "docs" / "research" / "liblib-batch367-2026-10-01" / "dead-button-census.json"

# 跨线: 有并行 session 未提交 WIP, 不普查(只记录, 不动)
CROSS_LINE = ("Director", "Jimeng")

# 自称可点的信号
SELF_CLAIM = re.compile(r'aria-label\s*=|data-testid\s*=|role\s*=\s*"button"')
WIRED = re.compile(r'\bon[A-Z]\w*\s*=|disabled\b')

# 解析一个 JSX 开标签: 从 `<button` 到配对的 `>`(跳过属性值里的 `>`)
#
# **必须先剥掉 JSX 注释**, 否则判据会误报: 本线代码里大量属性带中文注释,
# 而注释里常有反引号(`hover:bg-[#333]`)、`<button>` 之类的尖括号, 会让
# 正则把标签截断在注释中间 —— 于是「积分余额」(batch 358 已正确处理, 带
# data-inert)被误报成死控件。**误报已处理的控件危害大于漏报**: 它会让人
# 重复改动, 或撞上既有门禁钉住的约定。
TAG = re.compile(r'<button\b((?:[^>"]|"[^"]*"|\'[^\']*\'|\{[^{}]*\})*?)(/?)>', re.S)
JSX_COMMENT = re.compile(r'\{/\*.*?\*/\}', re.S)
# Batch 368: **无花括号**的块注释 `/* ... */` 也得剥。
# 起因是我自己踩的: 给 `SegmentReshootPanel` 写修复说明时用了
#   return (
#     /* Batch 368: …按「<button> 即控件」的口径… */
#     <button ... />
#   )
# 这是**表达式位置**的 JS 块注释, 外面**没有花括号** —— 于是 `JSX_COMMENT`
# (`\{/\*.*?\*/\}`) 匹配不到它, 注释里那句字面量 `<button>` 被当成真标签扫了出来,
# 凭空多出一个候选。
# > **给修复写的说明文档, 反过来制造了一个新的误报。** 判据必须能扛住
# > 源码里出现「关于判据本身的文字」, 否则每修一次就多一个假零/假阳。
# 顺序: 先剥带花括号那种(JSX children 位置), 再剥裸的那种。
BARE_BLOCK_COMMENT = re.compile(r'/\*.*?\*/', re.S)
LINE_COMMENT = re.compile(r'//[^\n]*')


def strip_comments(text: str) -> str:
    """剥掉 JSX 块注释、裸块注释与行注释, 但**保留换行**以维持行号。"""
    text = JSX_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    text = BARE_BLOCK_COMMENT.sub(lambda m: re.sub(r"[^\n]", " ", m.group(0)), text)
    text = LINE_COMMENT.sub(lambda m: " " * len(m.group(0)), text)
    return text


def classify_hover_target(src: str, tag_start: int) -> bool:
    """这个按钮是不是**hover 目标**而不是点击动作?

    ## 为什么需要这一条

    `SubtitleErasePanel.tsx:472` 的「查看框选去字幕说明」没有 onClick, 看着是
    标准死控件。但浏览器实测: 悬停它, 旁边的使用说明浮层 `opacity` 变 1、
    `visibility` 变 visible、文案完整 —— **它是有行为的 hover 目标**。
    按「无 handler = 死控件」去改它, 会把一个好控件改坏。

    ## 判据

    按钮自己带 `group-hover:` 不算(那只是它自己的悬停样式); 要看**它后面
    紧邻的元素**里有没有靠 `group-hover:` + `group-focus-within:` 显现的
    浮层 —— 那是「悬停这个按钮会弹出东西」的结构证据。

    ## 为什么是「分类」而不是「过滤」

    过滤掉会让下次普查**看不见**这一类, 学不到东西。所以只打 `hoverTarget`
    标签照常上报, 由浏览器实测来定性。这与本工具的定位一致: 只报候选。
    """
    window = src[tag_start : tag_start + 2000]
    return bool(
        re.search(r"group-hover:visib", window)
        and re.search(r"group-focus-within:visib", window)
    )


def scan(path: Path) -> list[dict[str, object]]:
    raw = path.read_text(encoding="utf-8", errors="replace")
    # 判据跑在剥掉注释的文本上(行号保持不变), 但 snippet 用原文, 便于人工核实
    src = strip_comments(raw)
    found: list[dict[str, object]] = []
    for m in TAG.finditer(src):
        attrs = m.group(1)
        if WIRED.search(attrs):
            continue
        if "data-inert" in attrs:
            continue
        line = raw[: m.start()].count("\n") + 1
        aria = re.search(r'aria-label\s*=\s*"([^"]*)"', attrs) or \
            re.search(r"aria-label\s*=\s*\{`([^`]*)`\}", attrs)
        raw_attrs = raw[m.start(1):m.end(1)]
        found.append({
            "line": line,
            "aria": aria.group(1) if aria else None,
            "hasHover": "hover:" in attrs,
            "hoverTarget": classify_hover_target(src, m.end()),
            # Batch 368: 判据**上界**又一个洞。第一版要求「自称可点」
            # (aria-label / data-testid / role=button) 才收, 理由是想避开
            # 纯展示元素。但 `SegmentReshootPanel` 的「参考」「标记」「角色库」
            # 三颗 pill **连 aria-label 都没有**, 却和同一行右侧**真能用的**
            # 「展开/收起」长得一模一样 —— 于是 367 一个都没抓到, 是 368 的
            # 运行时扫描按「<button> 即控件」的口径才报出来的。
            # 与其猜「有没有自称」, 不如**全都收**, 把「自称」降级成一个标签:
            # `selfClaim: false` 的候选**更值得看**(它连自己是个控件都没说清楚)。
            "selfClaim": bool(SELF_CLAIM.search(attrs)),
            "selfClosing": m.group(2) == "/",
            "snippet": " ".join(raw_attrs.split())[:160],
        })
    return found


def is_cross_line(rel: Path) -> bool:
    """跨线判定看**相对路径的每一段**, 且**大小写无关**。

    两个都踩过:
    - 只看 `path.stem` 时, 子目录里的跨线词判断会漏;
    - 只看 `path.parts[0]` 时, 目录名是**小写** `jimeng/`, 而 CROSS_LINE 写的是
      `Jimeng` —— `startswith` 不匹配, 于是把 42 个 jimeng 文件全当成本线候选报了出来。
      跨线一旦被误扫, 就会把别人的 WIP 报成候选、诱导后续去改, **比漏报更糟**。
    """
    return any(part.casefold().startswith(tuple(x.casefold() for x in CROSS_LINE)) for part in rel.parts[:-1])


def main() -> int:
    census: dict[str, object] = {"components": {}, "summary": {}}
    total = 0
    # **必须 rglob**: 画布本体的核心组件(nodes/ 16 个、frameos/ 26 个)在子目录里,
    # glob 只扫顶层会把它们整片漏掉 —— 已用阳性对照证实过这个漏报。
    for path in sorted(COMPONENTS.rglob("*.tsx")):
        rel = path.relative_to(COMPONENTS)
        if is_cross_line(rel):
            continue
        hits = scan(path)
        if hits:
            census["components"][str(rel)] = hits
            total += len(hits)
    census["summary"] = {
        "totalCandidates": total,
        "components": sorted(census["components"]),
        "note": "源码层面候选; 可触达性与是否骗人需浏览器实测确认",
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(census, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    for name, hits in census["components"].items():
        print(f"{name}:")
        for h in hits:
            tag = "  <- hover 目标, 大概率是误报, 需浏览器定性" if h["hoverTarget"] else ""
            print(f"  L{h['line']:<4} aria={h['aria']!r} hover={h['hasHover']}{tag}")
    print(f"总计 {total} 个候选, 分布 {len(census['components'])} 个组件")
    print(f"wrote {OUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
