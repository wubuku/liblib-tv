#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十四道闸：取证基线自洽（Batch 175 新增）。

**这道闸看守的是「手册照哪个版本取证」这件事本身**，而不是手册里的任何一个数字。

**为什么需要它（Batch 175 的实测，不是假想问题）**：

在此之前，8 道读上游源码的闸门各自把 ref 写死成 **`origin/main`**（浮动的），
而手册正文声明「适用 v1.6.16」、正文是照 v1.6.16 写的。上游从 v1.6.16 走到
v1.6.22（**27 个提交、223 个文件有差异**）之后，两边静悄悄地分家了：

  · 实测 8 道闸对着两个 ref 各跑一遍，**2 道结论不一致**：
    `web/src/pages/canvas` 行数（17009 → 17122）与「选择镜头模板」文案
    （`canvas-director-template-modal.tsx` 在 v1.6.22 已被整个删除）。
  · **这两条在 v1.6.16 上都是绿的**——手册没写错，是上游走了。

**为什么这个混淆危险**：红灯只有一种修法（改正文），于是人会去改正文，
把照 v1.6.16 写的内容改成 v1.6.22 的样子——手册从此不对应任何真实版本。
**「上游走了」该做的是升版并重做增量对账，「手册错了」才是改正文，两者修法相反。**
把两种情况压进同一个 `rc=1`，就等于把「该升版」伪装成「该改字」。

**本闸的四个方向**：

  方向一：基线声明**可解析**且**可解析出两条字段**——没有它，8 道闸全部退化为「未能核对」。
  方向二：基线声明的**提交在上游真实存在**——写错提交号会让 8 道闸一起读空。
  方向三：**基线版本与 README「适用版本」一致**——手册两处各说一个版本是最难发现的错。
  方向四（**本闸最要紧的一处**）：**没有任何闸门把 ref 写死成浮动的 `origin/main`**。
    这是防止 Batch 175 那个缺陷被下一个人不小心改回去。
    只看「基线声明对不对」是不够的——**声明对了但脚本没读它，等于没声明**，
    这正是纪律 107「判据锚的必须是事实、不能是誊抄副本」的翻版。

**方向四为什么不能只 grep 字面量**：脚本里出现 `origin/main` 有两种正当理由——
文档字符串（解释「这里以前写的是什么」）和注释（历史说明）。只有**真正参与
ref 解析的代码**才算违规，所以判据沿用 Batch 170 的**引号感知剥注释**，
并额外排除 docstring。**跨行块注释明确不处理**（Batch 170 同款限制，如实说明）。

退出码：0 全部自洽；1 有不自洽；2 未能核对（找不到手册 / 找不到上游源码 / 解析不出基线）。
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import (  # noqa: E402
    REFERENCE, ROOT, SRC, BaselineError, commit_exists, declared_baseline, upstream_tip,
)

README = os.path.join(ROOT, "README.md")
SCRIPTS = os.path.join(ROOT, "scripts")

# 允许出现 origin/main 的例外文件：本闸自己、共享基线模块。
SELF = {"verify-baseline.py", "baseline.py"}


def strip_comments_and_docstrings(src):
    """引号感知地剥掉注释与 docstring，只留**会被执行的代码**。

    为什么要剥 docstring：闸门脚本的开头大段说明里会写「这里以前是 origin/main」
    这样的历史交代，那是**给人看的**，不是 ref 解析。若不剥，方向四会永远红，
    而一条永远红的判据等于没有判据（Batch 155 方向五的教训）。

    **反验用例 5/6 上线首跑就抓到这个函数的一个真实 bug**（Batch 175）：
    最初把**所有**三引号串都当 docstring 剥掉，于是
    `REF = "origin/main"` 里的字符串字面量也被剥了——
    **判据把自己的论据一起删了**，方向四对真实的浮动 ref 完全无感（用例 5 漏报），
    同时把 docstring 之外的行判断也搅乱（用例 6 误伤）。
    修法是**只剥行首（允许空白）开头的三引号串**，也就是真正的 docstring；
    行内出现的三引号串按普通字面量保留。
    """
    out = []
    i, n = 0, len(src)
    # **反验用例 5 漏报抓到的就是这个**（Batch 175）：最初的实现剥完 docstring 后
    # 拿 **src 的下标**去回填 out，而剥注释时 src 字符已被丢弃，两套下标早已错位——
    # 结果是真正的 `REF = "origin/main"` 被判成「干净」，方向四对真实违规完全无感。
    # 修法：**docstring 在写入时就用等长空格占位**，全程只维护 out 一套坐标。
    while i < n:
        c = src[i]
        if c == '"' or c == "'":
            q = src[i:i + 3]
            if q in ('"""', "'''"):
                j = src.find(q, i + 3)
                if j < 0:
                    break
                # 前缀判断：行首（允许空白）才是 docstring，否则是普通字符串字面量
                line_start = src.rfind("\n", 0, i) + 1
                if src[line_start:i].strip() == "":
                    # docstring 整段不写入内容，只用等长空格占位
                    out.append(" " * (j + 3 - i))
                    i = j + 3
                    continue
                out.append(src[i:j + 3])
                i = j + 3
                continue
            j = i + 1
            while j < n and src[j] != c:
                if src[j] == "\\":
                    j += 1
                j += 1
            out.append(src[i:j + 1])
            i = j + 1
            continue
        if c == "#":
            # Python 的行注释。**这一分支是被反验抓出来的**（Batch 175 用例 5/6 首跑失败）：
            # 本函数最初照搬闸 7 处理 TypeScript 的那套，只认 `//` 与 `/* */`，
            # 于是 Python 里满地的 `# 注释` 原样留在结果里，
            # 方向四把「只是注释里提到 origin/main」误判成违规（用例 6 误伤）。
            # `//` 分支保留，是为了同一份判据将来若要扫 `.ts` 也不会静悄悄失效。
            j = src.find("\n", i)
            i = n if j < 0 else j
            continue
        if c == "/" and i + 1 < n:
            if src[i + 1] == "/":
                j = src.find("\n", i)
                i = n if j < 0 else j
                continue
            if src[i + 1] == "*":
                # 跨行块注释：**不处理**（嵌套块注释在本仓未使用，如实说明做不到）
                j = src.find("*/", i + 2)
                i = n if j < 0 else j + 2
                continue
        out.append(c)
        i += 1
    # docstring 已在写入时就以等长空格占位，这里直接拼接即可——
    # **不再做「按区间回填」**：那一步正是下标错位的来源（见上方 doc_ranges 注释）。
    return "".join(out)


def read(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return fh.read()
    except OSError as exc:
        return None if exc.__class__ is FileNotFoundError else None


def direction_one_and_two():
    """基线声明可解析 + 提交真实存在。"""
    problems = []
    try:
        version, commit = declared_baseline()
    except BaselineError as exc:
        return [f"方向一/二：{exc}"], None, None

    if not re.match(r"^v\d+\.\d+\.\d+$", version):
        problems.append(f"方向一：基线版本 {version!r} 不是 v主.次.修订 形态")
    if not re.match(r"^[0-9a-f]{7,40}$", commit):
        problems.append(f"方向二：基线提交 {commit!r} 不是 git 短提交号形态")
        return problems, version, commit
    if not commit_exists(commit):
        problems.append(
            f"方向二：基线提交 {commit} 在上游 {SRC} 里不存在"
            "（写错提交号会让 8 道闸一起读空，且它们会报 rc=2 而不是报错）")
    return problems, version, commit


def direction_three(version):
    """基线版本 == README 的「适用版本」。"""
    text = read(README)
    if text is None:
        return [f"方向三：读不到 {os.path.basename(README)}"]
    m = re.search(r"适用版本[：:]\s*BeefTV\s*`?(v\d+\.\d+\.\d+)`?", text)
    if not m:
        return ["方向三：README.md 里找不到「适用版本：BeefTV vX.Y.Z」那一行"]
    if m.group(1) != version:
        return [f"方向三：README 适用版本 {m.group(1)} ≠ 取证基线 {version}"
                "——手册两处各说一个版本，读者按哪一处都无法判断正文写的是哪版"]
    return []


def direction_four():
    """没有任何闸门把 ref 写死成浮动的 origin/main。"""
    problems = []
    checked = 0
    for fn in sorted(os.listdir(SCRIPTS)):
        if not fn.startswith("verify-") or not fn.endswith(".py"):
            continue
        if fn in SELF:
            continue
        raw = read(os.path.join(SCRIPTS, fn))
        if raw is None:
            problems.append(f"方向四：读不到 scripts/{fn}")
            continue
        code = strip_comments_and_docstrings(raw)
        checked += 1
        # **判据刻意检测字符串字面量**：ref 的值本来就写在引号里
        # （`REF = "origin/main"`），所以「排除引号」恰恰会漏掉唯一的真证据。
        # 剥注释与 docstring 之后仍能看到的 origin/main，一定是被代码引用的。
        for lineno, line in enumerate(code.splitlines(), 1):
            if "origin/main" in line:
                problems.append(
                    f"方向四：scripts/{fn} 第 {lineno} 行仍在**代码**里引用 origin/main"
                    "　→ 改用 baseline.resolve_ref()，否则这道闸会把「上游走了」"
                    "报成「手册错了」")
    if checked == 0:
        return [f"方向四：在 {SCRIPTS} 下没找到任何 verify-*.py（闸门清单表也会因此对不上）"]
    return problems


def main():
    if not os.path.isdir(SRC):
        print(f"[skip] 未找到 BeefTV 源码（{SRC}），跳过取证基线核对")
        return 2
    if not os.path.isfile(REFERENCE):
        print(f"[skip] 未找到 {os.path.basename(REFERENCE)}，跳过取证基线核对")
        return 2

    problems, version, commit = direction_one_and_two()
    if version:
        problems += direction_three(version)
    problems += direction_four()

    if problems:
        print("取证基线核对：%d 处不自洽" % len(problems))
        for p in problems:
            print("  ✗ " + p)
        print("→ 基线是**升版时唯一要改的地方**；改完请重跑本闸，"
              "并确认它是升版而不是把旧结论悄悄改掉")
        return 1

    tip = upstream_tip()
    print("取证基线核对：一致（%d 个闸门脚本均按声明的基线取证，无浮动 ref）" % direction_four_count())
    print("  基线：%s" % version)
    print("  提交：%s" % commit)
    if tip and tip[:7] != commit[:7]:
        behind = subprocess.run(
            ["git", "-C", SRC, "rev-list", "--count", f"{commit}..{tip}"],
            capture_output=True, text=True)
        n = behind.stdout.strip() if behind.returncode == 0 else "?"
        print("  ℹ 上游 origin/main 已领先本基线 %s 个提交（顶端 %s）——"
              "**这不是错误**：基线锁定的是正文照哪版写的。"
              "要跟上游就该升版并重做增量对账，而不是改判据。" % (n, tip[:7]))
    return 0


def direction_four_count():
    return sum(1 for fn in os.listdir(SCRIPTS)
               if fn.startswith("verify-") and fn.endswith(".py") and fn not in SELF)


if __name__ == "__main__":
    sys.exit(main())
