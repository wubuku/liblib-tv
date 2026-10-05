#!/usr/bin/env python3
"""校验行内强调（`**加粗**`）的写法不会让 VitePress 渲染失败。

**为什么需要这道检查（M90 实测）**：CommonMark 的 flanking 规则规定，
`**` 定界符能不能开/闭，取决于**它左右紧邻的字符**。写不好就会在产物里
**留下字面量 `**`**，加粗彻底失效，而源文件看上去完全正常。

**精确判据**（不是"跨度首尾是标点就错"——M90 第一版就是这么写的，
结果 **146 条假阳性**，因为表格单元格里 `**` 两侧有空格，条件自动成立）：

- **开定界符**能开（left-flanking），当且仅当：后面**不是空白**，且
  ① 后面**不是标点**，**或者** ② 后面是标点但**前面是空白或标点**。
- **闭定界符**能闭（right-flanking），当且仅当：前面**不是空白**，且
  ① 前面**不是标点**，**或者** ② 前面是标点但**后面是空白或标点**。

所以**表格里永远不会中招**（`| **加粗** |` 两侧有空格，② 兜住了），
**正文散文里才会**——`但它的**读屏提示（…）**是` 两侧都是实义字，①② 都不成立。

M90 实测：全站扫产物才发现 **7 处，跨 6 个页面**，而 `check-tables` /
`check-anchors` / `check-claims` / `check-dist-links` **全部报 ok**。
这是继 M84（单元格内未转义竖线导致内容被丢弃）之后**第二类"源文件没事、
产物坏了"**的缺陷。

**本脚本现在管两件事**，因为它们是同一族——markdown/Vue 构造在源文件里看着
正常、渲染时才失效：

1. `**加粗**` 的 flanking（M90）
2. `{{ }}` 被 Vue 当插值吞掉（M91）——见下方 `check_vue_interpolation`

退出码 0 表示全部写法正确，1 表示存在会渲染失效的写法。
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

# ★ **M240：排除名单不再自己抄，改为读 `.vitepress/config.mjs` 的 `srcExclude`。**
# 读法、匹配语义与「读不到就判失败」的取舍都写在共享模块里。
sys.path.insert(0, str(Path(__file__).resolve().parent))
from _site_exclude import is_excluded, read_src_exclude  # noqa: E402

# Unicode 标点类 + ASCII 常用标点（会触发 flanking 判定）
PUNCT = set(
    "，。、；：？！「」『』（）《》〈〉【】〔〕…—～·"
    "，．、；：？！＂＇｀～"
    ",.;:?!()<>[]{}'\"`~|"
)
# 空白（含全角空格与不换行空格——中文排版里都可能出现）
WS = set(" \t　 ")

SPAN_RE = re.compile(r"\*\*(?P<body>[^*\n]+?)\*\*")
SKIP_DIRS = {"node_modules", ".vitepress", "dist", ".git", "screenshots"}
FENCE_RE = re.compile(r"^\s*(```|~~~)")

# ★ **M240：这里原先有一份手抄的 `INTERNAL` 名单，现在没有了。**
# 排除哪些页面**不是本脚本该决定的事**——那是 `.vitepress/config.mjs` 的
# `srcExclude` 说了算（见 `read_src_exclude`）。
# **手抄一份的代价，本批已经付过一次**：
# 那份名单把 `README.md` 当内部资料，而它其实是被发布的首页，
# 于是本脚本跳过了首页与 `10-tasks/README.md`，
# 注入一个必定违规的跨度进去，**构建 exit=0、产物里留着字面量 `**`，门禁却报「均成立」**。
# **「不扫哪些文件」这种名单，永远要从事实推导，而不是另抄一份。**


def left_flanking(prev: str, nxt: str) -> bool:
    """`nxt` 是 body 首字符、`prev` 是开定界符前紧邻的字符。开定界符能开吗？"""
    if nxt in WS:
        return False
    if nxt not in PUNCT:
        return True
    return prev in WS or prev in PUNCT


def right_flanking(prev: str, nxt: str) -> bool:
    """`prev` 是 body 尾字符、`nxt` 是闭定界符后紧邻的字符。闭定界符能闭吗？"""
    if prev in WS:
        return False
    if prev not in PUNCT:
        return True
    return nxt in WS or nxt in PUNCT


def fenced_lines(lines: list[str]) -> set[int]:
    inside: set[int] = set()
    fence: str | None = None
    for i, line in enumerate(lines):
        stripped = line.strip()
        if fence is None:
            if FENCE_RE.match(line):
                fence = stripped[:3]
                inside.add(i)
            continue
        inside.add(i)
        if stripped.startswith(fence):
            fence = None
    return inside


# 行内代码的占位字符。**必须是"普通字符"（既非空白也非标点）**——
# M90 第二版曾用空格填充，结果把行内代码结尾的反引号（属标点）换成了空白，
# flanking 上下文被改写，`**…传 \`undefined\`**` 这类**本来就正常**的写法被误报。
# 换成 `X` 之后，代码段对 flanking 的影响与真实解析一致。
_CODE_FILLER = "X"


def strip_inline_code(text: str) -> str:
    """把行内代码换成等长的普通字符，避免 ``**x**`` 里的记号被当成强调。"""
    return re.sub(r"`[^`\n]*`", lambda m: _CODE_FILLER * len(m.group(0)), text)


def check_vue_interpolation(
    lines: list[str], rel: str, code: set[int]
) -> list[str]:
    """`{{ }}` 会被 Vue 当成插值求值，变量不存在时**渲染成空字符串**。

    **M91 实测**：VitePress 把 markdown 编译成 Vue 组件，所以正文里的
    `{{count}}` **不是字面量，而是插值**。写手册经常要引用 i18n 的占位符语法，
    源文件读起来完全正常，产物里却**已经被吞掉了**：

        源：  | 占位符（`{{count}}` 等） |     ← 行内代码段
        产物：| 占位符（<code></code> 等） |  ← 空的 code，读者看不到 count

        源：  「已导入 {{count}} 个画布」
        产物：「已导入  个画布」            ← 正文里直接少了一段

    第一种还能被 `check-render.py` 的"空标签"判据捞到；**第二种什么都测不出来**
    ——它不产生任何异常标签，只是内容消失了。**所以只能在源侧拦。**

    **正确写法**：`<span v-pre>{{count}}</span>`（M91 实测有效；要保留行内代码段
    就把反引号放进 span：``<span v-pre>`{{count}}`</span>``）。
    **HTML 实体 `&#123;` 在行内代码段里无效**——代码段会转义实体，读者会看到
    字面的 `&amp;#123;`（这条也是 M91 实测排除的）。
    """
    problems: list[str] = []
    for number, line in enumerate(lines, 1):
        if number - 1 in code or "{{" not in line:
            continue
        guarded = re.sub(r"<span v-pre>.*?</span>", "", line)
        for match in re.finditer(r"\{\{[^{}\n]*\}\}", guarded):
            token = match.group(0)
            problems.append(
                f"{rel}:{number}: 正文里的 `{token}` 会被 Vue 当插值吞掉，"
                f"产物里这段会消失——用 `<span v-pre>{token}</span>` 包起来"
            )
    return problems


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    excluded_patterns = read_src_exclude(root)
    if excluded_patterns is None:
        print("  [渲染陷阱] 读不到 .vitepress/config.mjs 里的 srcExclude —— "
              "**判据不知道哪些页面会被发布**，不敢扫（扫全库会重现 M90 的 382 条假阳性），"
              "也不敢按旧名单硬扫（那正是 M240 抓到的假阴性）。请先修 config.mjs。")
        return 1
    all_md = sorted(
        p for p in root.rglob("*.md")
        if not SKIP_DIRS.intersection(p.relative_to(root).parts)
    )
    md_files = [
        p for p in all_md
        if not is_excluded(p.relative_to(root).as_posix(), excluded_patterns)
    ]
    if not md_files:
        print("  [渲染陷阱] 没有找到任何待检查的 .md 页面")
        return 1

    problems: list[str] = []
    span_count = 0
    for path in md_files:
        rel = path.relative_to(root).as_posix()
        lines = path.read_text(encoding="utf-8").splitlines()
        code = fenced_lines(lines)
        problems.extend(check_vue_interpolation(lines, rel, code))
        for number, raw in enumerate(lines, 1):
            if number - 1 in code:
                continue
            text = strip_inline_code(raw)
            for match in SPAN_RE.finditer(text):
                body = match.group("body")
                span_count += 1
                # 行首/行尾对 flanking 而言等同空白（CommonMark 把行尾当空白），
                # M90 第二版用空串表示，导致"段落最后一行以 `**…**。` 收尾"被误报
                prev = text[match.start() - 1] if match.start() > 0 else " "
                nxt = text[match.end()] if match.end() < len(text) else " "
                bad = []
                if not left_flanking(prev, body[0]):
                    bad.append(
                        f"开定界符前是「{prev}」后是「{body[0]}」，不满足 left-flanking"
                    )
                if not right_flanking(body[-1], nxt):
                    bad.append(
                        f"闭定界符前是「{body[-1]}」后是「{nxt}」，不满足 right-flanking"
                    )
                if bad:
                    problems.append(
                        f"{rel}:{number}: {'；'.join(bad)}，产物里会留下字面量 ** ：**{body[:28]}**"
                    )

    for problem in problems:
        print(f"  [渲染陷阱] {problem}")
    if problems:
        print(f"渲染陷阱校验失败：{len(problems)} 项")
        return 1
    print(
        f"  [ ok ] 渲染陷阱校验：{span_count} 个 `**…**` 跨度 flanking 均成立，"
        "且无会被 Vue 吞掉的裸双花括号插值"
    )
    # ★ **F41 纪律：报「通过」必须同时报「看到了多少」**（M240）。
    # 旧判据只报跨度数——**而跨度数与「扫了哪些页面」没有对应关系**：
    # 少扫一个页面，跨度数只会少几十，**看上去仍是「均成立」**。
    # 本次假阴性正是这样藏住的：产物首页里留着字面量 `**`，报读却一切正常。
    # ★ **所以这里必须点名页面数，并把被排除的名单原样打出来**——
    # **排除名单一旦与 `srcExclude` 脱节，这一行就会露馅。**
    excluded_names = sorted(
        {p.relative_to(root).as_posix() for p in all_md}
        - {p.relative_to(root).as_posix() for p in md_files}
    )
    print(
        f"         覆盖面：扫了 {len(md_files)} 个已发布页面"
        f"（另有 {len(excluded_names)} 个按 .vitepress/config.mjs 的 srcExclude 排除："
        f"{'、'.join(Path(n).name for n in excluded_names)}）"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
