#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十七道闸：手册让读者**手敲**的 URL 查询参数，逐个对账上游。

背景（Batch 230）：手册有一节专门写「只能手敲、界面上没有入口的查询参数」。
这一节的风险和其他节不同——**别处的文字写错了，读者读错就过去了；
而这里的参数名写错了，读者会照着敲进地址栏，然后什么也不会发生**，
且没有任何报错。`?readonly=1` 敲成 `?readonly=true`、`?tab=history` 敲成 `?tabs=history`，
在产品里都是**静默失效**。

本批在这条线上抓到一处真缺陷（`20-reference.md` 把 `?apiKey=…` 说成
「会写进你的配置」，而上游 `client-root-init.tsx:113` 那个变量就叫
`ignoredApiKey`，密钥**根本不会被写入**，只弹一句「出于安全考虑…已忽略」——
**手册把上游的安全设计讲成了功能**）。
**那一处靠逐句读源码抓到，判据抓不到**（它核的是「参数名存不存在」，
而 `apiKey` 是存在的）。本闸因此**不宣称能核「作用描述对不对」**，
只守两件机械的事：

  1. **手册里出现的每个参数名，上游必须有读点**
     （`searchParams.get("名")` 或 `searchParams.has("名")`）。
     实测：手册 10 个参数名 / 30 处，上游 20 个参数 / 45 处读点，**10 个全部存在**。
     它现在抓不到东西，**但它守的是「参数名被上游改名后手册不跟」**——
     而那正是上面那类静默失效的入口。
  2. **手册若声明某参数有 N 种取值（如 `fixture=<10 种>`），
     N 必须等于上游与它比较的字面量个数。**
     实测 `fixture` 上游正好 10 个，手册写 10 种，一致。

**第 2 条有一个必须说清的边界**：它靠「与该参数比较的字符串字面量」数取值，
**只在取值是内联比较时可靠**。实测 `mode` 就不可靠——它的取值分散在
`requestedCreationMode(...)` 这个 helper 里，内联只数得出 2 个（实际 5 个）。
**所以抽不出任何字面量时，本闸报「未能核对这个参数」而不是报「手册写错了」**
——抽不出字面量意味着抽取方式失效，不意味着上游没有取值（纪律 160：
「未能核对」与「不一致」必须返回不同的结果）。

**为什么参数名要用 `has` 也算读点**：`?apiKey=…` 在上游是
`searchParams.has("apiKey")`（只判断在不在，不取值），
只认 `get` 会把它报成「上游查不到」——**而它明明被读了**。
第一版只认 `get`，实测把 `apiKey` 报成不存在；**判据把「另一种读法」当成「没读过」，
就会逼着人改对的东西**（纪律 239 的同一个道理）。

退出码：0 通过；1 有参数名在上游查不到，或取值个数与手册声明不符；
2 未能核对（上游缺失 / 手册里一个参数都没扫到）。
"""

import os
import re
import sys

import beefsrc
from baseline import announce_fallback, baseline_guard

# 手册里出现查询参数的地方：`?名=` / `&名=`。省略号（`?baseUrl=…`）允许。
MANUAL_PARAM = re.compile(r"[?&]([a-zA-Z_][a-zA-Z0-9_]*)=…?")

# 上游的读点。`has` 与 `get` 都要算（见文件头）。
READ_POINT = re.compile(r'searchParams\.(?:get|has)\("([a-zA-Z_][a-zA-Z0-9_]*)"\)')

# 手册里「<参数> = <N> 种」这种可数声明，例如 `fixture=<10 种>`
COUNT_CLAIM = re.compile(r"`([a-zA-Z_][a-zA-Z0-9_]*)\s*=\s*<(\d+)\s*种")

# 扫到的参数名数量下限。**低于它就报「未能核对」，不许报「通过」**
# （纪律 156：一个都没检查与全部通过，必须长得不一样）。
# 真实值 10，取 5 留足余量，又足以抓住「页面集合写错 / 扫空」这类整片失效。
MIN_PARAMS = 5


def strip_fenced(text):
    """挖空围栏代码块但**保留行数**——报错要带 `:行号`，行号必须对得上原文。"""
    out, in_fence, fence = [], False, None
    for line in text.split("\n"):
        m = re.match(r"^[ \t]*(```|~~~)", line)
        if m:
            if not in_fence:
                in_fence, fence = True, m.group(1)
            elif m.group(1) == fence:
                in_fence, fence = False, None
            out.append("")
            continue
        out.append("" if in_fence else line)
    return "\n".join(out)


def manual_pages(root):
    """手册的正文页（与闸 26 同一套范围口径）。"""
    out = []
    for base in ("00-quickstart.md", "20-reference.md", "30-concepts.md", "90-troubleshooting.md"):
        p = os.path.join(root, base)
        if os.path.isfile(p):
            out.append(p)
    task_dir = os.path.join(root, "10-tasks")
    if os.path.isdir(task_dir):
        for name in sorted(os.listdir(task_dir)):
            if name.endswith(".md"):
                out.append(os.path.join(task_dir, name))
    return out


def scan_manual(root):
    """返回 ({参数名: [(相对路径, 行号)]}, {参数名: 手册声明的取值个数}, 读到的页数)。"""
    seen, claims, pages = {}, {}, 0
    for page in manual_pages(root):
        try:
            raw = open(page, encoding="utf-8", errors="ignore").read()
        except OSError:
            continue
        pages += 1
        rel = os.path.relpath(page, root)
        body = strip_fenced(raw)
        for lineno, line in enumerate(body.split("\n"), 1):
            for m in MANUAL_PARAM.finditer(line):
                seen.setdefault(m.group(1), []).append((rel, lineno))
            for m in COUNT_CLAIM.finditer(line):
                claims.setdefault(m.group(1), int(m.group(2)))
    return seen, claims, pages


def upstream_reads(src, ref):
    """{参数名: 出现次数}、{参数名: 内联字面量取值集合}、{参数名: 抽取是否完整}。

    **第三项是本闸最容易出错的地方，反验第 6 例实测撞到过。**
    抽取靠「与该参数比较的字符串字面量」数取值，**这只有在每个读点都是
    内联比较时才完整**。实测 `mode` 不完整：它有两处内联比较
    （`=== "readonly"` / `!== "handoff"`），但还有一处
    `requestedCreationMode(searchParams.get("mode"))`——
    **取值在那个 helper 里，内联只能数出 2 个，而实际是 5 个。**

    第一版只判「抽不出字面量 → 未核对」，于是 `mode` 抽出 2 个、
    手册声明 5 个 → **闸门把「我抽少了」报成了「手册写错了」**，
    而手册是对的。**判据必须能说出「我这次抽全了吗」。**
    判法：逐个读点看它是不是内联比较（`===` / `!==` / `[...].includes(...)`）；
    只要有一个读点把值传去了别处，本参数的取值抽取就**不完整**，
    **报「未能核对这个参数」，不报「手册与上游对不上」**。
    """
    import subprocess
    proc = subprocess.run(
        ["git", "grep", "-n", "-h", "-E", r'searchParams\.(get|has)\("[a-zA-Z_]+"\)',
         ref, "--", "web/src"],
        cwd=src, capture_output=True, text=True,
    )
    reads, literals, complete = {}, {}, {}
    inline_re = re.compile(
        r'searchParams\.get\("%s"\)\s*(?:\|\|\s*"")?\s*'
        r'(?:(?:!==|===|!=|==)\s*"[^"]+"|'
        r'|\)|)'
    )
    for line in proc.stdout.split("\n"):
        for m in READ_POINT.finditer(line):
            reads[m.group(1)] = reads.get(m.group(1), 0) + 1
        for m in re.finditer(r'searchParams\.get\("([a-zA-Z_]+)"\)', line):
            p = m.group(1)
            # 形态一：内联比较  searchParams.get("p") !== "值"
            for c in re.finditer(
                    r'searchParams\.get\("%s"\)\s*(?:!==|===|!=|==)\s*"([^"]+)"' % re.escape(p), line):
                literals.setdefault(p, set()).add(c.group(1))
                complete[p] = True
            # 形态二：数组包含  ["a","b"].includes(searchParams.get("p") || "")
            for c in re.finditer(
                    r'\[([^\]]*)\]\.includes\(\s*searchParams\.get\("%s"\)\s*(?:\|\|\s*"")?\s*\)'
                    % re.escape(p), line):
                for v in re.findall(r'"([^"]+)"', c.group(1)):
                    literals.setdefault(p, set()).add(v)
                complete[p] = True
            # 形态三：值被传去了别处（helper / 变量赋值）→ 本参数抽取不完整
            #
            # ⚠️ 第一版这里写错了：判据是「把内联比较整段抠掉后看还剩不剩读点」，
            # 而**内联比较那一段是可选的**——于是 `const mode = searchParams.get("mode")`
            # 被整段抠掉、什么都不剩，**被判成「内联比较、是完整的」**。
            # 结果 `mode` 明明有一个读点把值传给了 `requestedCreationMode(...)`，
            # 闸门却当它抽取完整，拿 2 个字面量去比手册的 5 个，**报手册写错了**
            #（反验第 6 例当场抓到：手册是对的、闸门是错的）。
            #
            # 正确判法是**看读点后面紧跟什么**：内联比较后面必然是
            # `===` / `!==` / `==` / `!=`；在 `[...].includes(` 里后面必然是
            # `|| ""` 或 `)`，而**它前面**必然是 `.includes(`。
            # 其余形态（赋值、传参）都不是内联比较。
            for occ in re.finditer(r'searchParams\.get\("%s"\)' % re.escape(p), line):
                tail = line[occ.end():]
                if re.match(r'\s*(?:\|\|\s*"")?\s*(?:!==|===|!=|==)', tail):
                    continue                      # 直接比较
                if re.match(r'\s*(?:\|\|\s*"")?\s*\)', tail):
                    # 前面是 .includes( 才算内联；是别的函数调用就不算
                    before = line[:occ.start()]
                    if re.search(r'\[\s*(?:"[^"]*"\s*,\s*)*"[^"]*"\s*\]\.includes\(\s*$', before):
                        continue
                complete[p] = False
    return reads, literals, complete


@baseline_guard
def main():
    root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pages = manual_pages(root)
    if len(pages) < 10:
        print(f"[未能核对] 只找到 {len(pages)} 个正文页（下限 10），输入范围明显不对")
        return 2

    src, is_fallback = beefsrc.resolve_src()
    if src is None:
        print("[skip] 未找到 BeefTV 源码，跳过查询参数核对")
        return 2
    if is_fallback:
        announce_fallback()
    from baseline import resolve_ref
    ref = resolve_ref()

    seen, claims, scanned_pages = scan_manual(root)
    reads, literals, complete = upstream_reads(src, ref)

    if len(seen) < MIN_PARAMS:
        print(f"[未能核对] 手册里只扫到 {len(seen)} 个查询参数（下限 {MIN_PARAMS}，读了 {scanned_pages} 个正文页）"
              f"——本闸本轮什么也没检查，**不能按「参数都对」通过**")
        return 2

    problems, unverifiable = [], []
    for param in sorted(seen):
        if reads.get(param, 0) == 0:
            where = "、".join(f"{f}:{n}" for f, n in seen[param][:3])
            problems.append(
                f"手册让读者手敲「{param}」（{where} 等 {len(seen[param])} 处），"
                f"而上游 web/src 里**没有** searchParams.get/has(\"{param}\") 的读点"
                f"——照着敲会静默失效，没有任何报错"
            )
            continue
        want = claims.get(param)
        if want is None:
            continue
        got = literals.get(param)
        if not got or not complete.get(param):
            # **抽不全 ≠ 上游没有那么多取值**（`mode` 就是这样：一个读点把值传给了
            # `requestedCreationMode(...)`，内联只数得出 2 个而实际 5 个）。
            # 反验第 6 例实测：这里若照报「手册与上游对不上」，**手册是对的、闸门是错的**。
            unverifiable.append(param)
        elif len(got) != want:
            problems.append(
                f"手册声明「{param}=<{want} 种>」，而上游与它比较的字面量是 {len(got)} 个"
                f"（{sorted(got)}）——同一个参数在手册与上游对不上"
            )

    if unverifiable:
        print(f"[部分核对] {len(unverifiable)} 个参数的取值个数**本闸核不了**"
              f"（{'、'.join(unverifiable)}）：它们有读点把值传去了别处"
              f"（helper / 变量赋值），本闸靠内联字面量数取值，**抽不全**。"
              f"**抽不全只说明本方向失效，不说明手册写错了**（实测 `mode` 就是这种情况）")

    if problems:
        print(f"查询参数核对：手册 {len(seen)} 个参数名，{len(problems)} 处对不上上游")
        for x in problems:
            print("  ✗ " + x)
        return 1

    print(f"查询参数核对：手册 {len(seen)} 个参数名在上游均有读点"
          f"（{'/'.join(sorted(seen))}），"
          f"{len(claims)} 处可数声明与上游字面量个数一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
