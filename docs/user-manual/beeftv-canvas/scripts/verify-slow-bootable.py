#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""闸 42「慢反验的可启动性与合计可解析性」——**在一次都跑不动它们的前提下，问它们还能不能跑**。

**它治的病**（Batch 286 取证时量出来的，不是猜的）：

  · 对应关系表有 5 行的「例数」是**慢反验**的，而**构建从不跑慢反验**；
    方向十七要机器对账，于是这 5 行**没有任何机器真值**。
  · **本批把它挨个真跑了一遍**，四份的合计与表里对得上，
    而第 5 份 `selftest-zero-input.py` **整个跑不起来**：rc=2「拒绝开跑」。
  · 破口是 `shutil.rmtree(fleet_root, ignore_errors=True)` 没登记进 `READONLY_EXEMPT`，
    **`git log -S` 查出来由 `e227854b`（Batch 282）引入**——
    **而 Batch 282 / 283 / 284 / 285 四个批次的绿构建全绿**，
    **这道闸从 Batch 282 起一次都没跑起来过**。
  * 被它守着的判据就是**那道闸自己的启动前提**，而那个前提**只要 0.14 秒**就能算：
    `check_readonly()` 是纯 AST 扫描，不执行任何闸。
    **实测比例 0.14 / 274 = 1/1957**。

**所以本闸不去跑那 5 份**（它们登记合计 **3689 秒 = 61.5 分钟**，
  而 Batch 286 写下的「40 分钟量级」那个数**实测偏低 1.5 倍，本批据实订正**）。
  **它问的是三件跑之前就能问的事**：

  ① **装体**：`.py` 走 `ast.parse`、`.sh` 走 `bash -n`——
     **刻意不用 `py_compile`**，因为那会往树里写 `__pycache__`（方向十九的指纹会看见）；
     异常与语法错都当场点出是哪一份的哪一行。
  ② **合计可解析**：每一份慢反验必须**存在一个合计输出点，且那个输出点同时含
     `例` / `通过` / `失败` 三个标签**。
     **这是本闸唯一有历史证据的那一支**：Batch 286 修复前的
     `selftest-zero-input.py`（`675a8c7f`）**一个合计行都没有**——
     而「报不出合计」正是「拒绝开跑」的签名，**那份产物还在**（rc=2 的输出里没有合计行）。
  ③ **SLOW 名单可解析**：从闸 18 的源码里用 `ast` 读出 `SLOW` 的键——
     **不 import 闸 18**（import 会执行对方模块顶层的代码，而两道闸不该互相执行）。

**为什么标签要按「词」认而不按「位置」认**（这不是洁癖，有实测）：
  · `selftest-unreachable.sh` 报的是「通过 / 作废 / 失败」，
  · `selftest-meta.sh` 报的是「通过 / 失败 / 作废」，
  **两处顺序不同，而它们都是对的**。按位置解析的判据会读错其中一份，
  **而读错的方式是「把 3 读成 0」——一个看起来正常的数**（纪律 152）。
  本闸的 `KNOWN_OUTPUT_SHAPES` 把这两句真实输出收在文件里当夹具，
  **顺序无关这件事是每天被跑一遍的断言，不是一句声明**。

**本闸不做什么（边界，明写）**：
  · **不核合计的数值对不对**——那要真跑 61.5 分钟；
  · **不核慢反验的例数与台账是否一致**——那是方向十七的活，而它够不到慢反验，
    **本闸也够不着，本闸只保证「将来够得着的那条路是通的」**；
  · **不保证慢反验能跑完**——只保证它们装得上体、报得出合计。
  **「报得出合计」与「跑得完」是两件事，本闸只买前一件，且明写买的是哪一件。**

退出码：0 五份慢反验都装得上体、都报得出可解析的合计；
        1 至少一份装不上体、或者报不出合计、或者标签不全；
        2 连慢反验名单都没读出来（前提不成立，**不装作核过了**——纪律 101）。
"""
import ast
import io
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SELF = os.path.basename(__file__)
#: **SLOW 名单的来源是闸 18 的源码**——**两处不许各登一份**，否则本闸核的是一个没人跑的集合。
SLOW_SRC = "verify-selftest-bootable.py"

#: 合计输出点必须同时含这两个标签。**只认这两个，是因为实测五份里都含它们**：
#: 两份 `.py` 写「通过 N，失败/作废 K」，两份 `.sh` 写「通过 N / 失败 K / 作废 V」，
#: **而「例」字只有 `.py` 写**（`.sh` 报的是「结果：通过 47 / 失败 0 / 作废 0」，
#: **一个「例」字都没有**）——
#: **本闸第一版把「例」也列进必需要素，而它自己文件里收着的真实句子当场否掉了它**
#: （首跑 rc=2「夹具句自己解析不全」）。**判据要按事实定，不能按「读起来该有什么」定。**
#: 「失败」写成标签而不是「失败/作废」，是因为**四种写法都含「失败」这两个字**。
REQUIRED_LABELS = ("通过", "失败")

#: **闸 18 登记表里那 5 份合计输出的真实句子**（取自 Batch 286 普查的实测输出，
#: **不是照抄源码里的 f-string**）。**前两句顺序不同**——
#: 本闸对它们必须给出**同一个**标签集合，否则本闸自己就是按位置认的。
KNOWN_OUTPUT_SHAPES = (
    "=== 结果：通过 47 / 失败 0 / 作废 0 ===",
    "=== 结果：通过 30 / 作废 0 / 失败 3 ===",
    "闸 22 反验：7 例，通过 7，失败/作废 0",
    "闸 18 反验：54 例，通过 54，失败/作废 0",
    "零输入体检反验：3 例，通过 3，失败 0",
)


#: **标签后面必须紧跟一个「数」才算数**——**判据认事实，不认词**。
#:
#: **第一版只问「句子里有没有『失败』两个字」，首跑就误伤了**：
#: `selftest-zero-input.py:563` 印的是
#: 「**静默降级比直接失败更坏**」——一句散文，被当成了半个合计。
#: **而当时真正的问题在第 611 行**（合计只报「通过」不报「失败」），
#: **两个挤在同一个 `problems` 里，那条真问题就淹没在噪声里**。
#:
#: 所以规则收紧成：**标签之后（允许夹一个 `/作废` 和空白）必须紧跟一个数或一个插值口**——
#: `%d` / `{` / `$` / 数字。实测五份真实输出与四种源码写法都过，而那句散文不过。
#: **「一个判据要多准才算准」这个问题的答案是：先看它误伤了谁。**
#: **注意 `/作废` 是字面串，不是字符类**——`[/作废]` 只匹配其中一个字，
#: 于是 `失败/作废 {failed}` 被判成「失败后面没跟数」，两份 `.py` 全被误报。
#: **这是本闸首跑之后的第二个错，也是正则里最便宜的一个**。
_NUMISH = re.compile(r"^(?:/作废)?\s*[%{$]?\s*(?:\d|[%{$])")


def counted_labels(text):
    """**按词**取「后面跟着数」的标签集合，**不按位置**——
    见模块 docstring 里那两处顺序不同的实测。

    返回 `{标签}`；集合等于 `REQUIRED_LABELS` 才算一个合格的合计输出点。
    """
    got = set()
    for lab in REQUIRED_LABELS:
        for m in re.finditer(re.escape(lab), text):
            if _NUMISH.match(text[m.end():]):
                got.add(lab)
                break
    return got


def labels_in(text):
    """**保留给「夹具句」用**：只问词在不在，不问后面有没有数。"""
    return {lab for lab in REQUIRED_LABELS if lab in text}


def read_slow_names(path):
    """**用 `ast` 从闸 18 的源码里读出 `SLOW` 的键**——不 import 它。

    返回 `(names, seconds)`；读不出来就返回 `(None, None)`，由调用方报 rc=2。
    """
    try:
        tree = ast.parse(io.open(path, encoding="utf-8").read())
    except (OSError, SyntaxError):
        return None, None
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        targets = [t.id for t in node.targets if isinstance(t, ast.Name)]
        if "SLOW" not in targets:
            continue
        if not isinstance(node.value, ast.Dict):
            return None, None
        names, secs = [], {}
        for k, v in zip(node.value.keys, node.value.values):
            if not (isinstance(k, ast.Constant) and isinstance(k.value, str)):
                return None, None
            names.append(k.value)
            secs[k.value] = None
            if isinstance(v, ast.Dict):
                for kk, vv in zip(v.keys, v.values):
                    if (isinstance(kk, ast.Constant) and kk.value == "seconds"
                            and isinstance(vv, ast.Constant)
                            and isinstance(vv.value, int)):
                        secs[k.value] = vv.value
        return names, secs
    return None, None


def boots_ok(name, path):
    """**判据一：装体**。返回 `(ok, 说明)`——`.py` 走 `ast.parse`，`.sh` 走 `bash -n`。"""
    if name.endswith(".py"):
        try:
            ast.parse(io.open(path, encoding="utf-8").read())
        except SyntaxError as exc:
            return False, "语法错：第 %s 行 %s" % (exc.lineno, exc.msg)
        except OSError as exc:
            return False, "读不了：%s" % exc
        return True, "ast.parse 通过"
    if name.endswith(".sh"):
        pr = subprocess.run(["/bin/bash", "-n", path], capture_output=True, text=True)
        if pr.returncode != 0:
            return False, "bash -n 失败：%s" % (pr.stderr.strip().splitlines() or [""])[0]
        return True, "bash -n 通过"
    return False, "**不认识的解释器形态**（既不是 .py 也不是 .sh），本闸不会跑它"


def find_totals(src):
    """**找出源码里所有「合计输出点」**——`print(...)` 或 `echo ...`。

    **按调用切分而不是按行切分**：合计句常常被折成多行（`%` 续行、f-string 拼接），
    按行切会把一句完整的合计切成两半，于是「缺标签」是切出来的而不是真的。
    """
    out = []
    for m in re.finditer(r"\bprint\s*\(", src):
        i, depth = m.end(), 1
        while i < len(src) and depth:
            if src[i] == "(":
                depth += 1
            elif src[i] == ")":
                depth -= 1
            i += 1
        out.append((src.count("\n", 0, m.start()) + 1, src[m.start():i]))
    for m in re.finditer(r"^\s*echo\s+(.*)$", src, re.M):
        out.append((src.count("\n", 0, m.start()) + 1, m.group(0)))
    return out


def main():
    t0 = time.time()
    problems = []
    checked = []

    print("=" * 74)
    print("闸 42 慢反验的可启动性与合计可解析性")
    print("=" * 74)

    # ── 判据零（先核自己）：顺序无关必须是断言，不是声明 ─────────────────────
    sets = [labels_in(s) for s in KNOWN_OUTPUT_SHAPES]
    want = set(REQUIRED_LABELS)
    bad_shapes = [(s, g) for s, g in zip(KNOWN_OUTPUT_SHAPES, sets) if g != want]
    if bad_shapes:
        for s, g in bad_shapes:
            print("  ✗ 夹具句自己解析不全：%s（拿到 %s）" % (s[:46], sorted(g)))
        print("  **本闸连自己的夹具都解析不了，下面那些结论一律不算数**")
        return 2
    print("  ✓ 夹具：%d 句真实合计输出，**顺序不同而标签集合相同**（顺序无关是被断言的）"
          % len(KNOWN_OUTPUT_SHAPES))

    slow_path = os.path.join(HERE, SLOW_SRC)
    names, secs = read_slow_names(slow_path)
    if not names:
        print("  ✗ 前提不成立：读不出 `%s` 里的 `SLOW` 名单" % SLOW_SRC)
        print("     → 本闸核的是「闸 18 登记的那批慢反验」，**读不出那份登记就没有可核的对象**")
        return 2
    print("  慢反验名单（从 `%s` 的源码读出，未执行对方）：%d 份" % (SLOW_SRC, len(names)))
    for n in names:
        print("    · %-36s 登记 %s 秒" % (n, secs.get(n)))

    # ── 判据一 + 判据二 ────────────────────────────────────────────────────
    print()
    for name in sorted(names):
        path = os.path.join(HERE, name)
        if not os.path.exists(path):
            print("  ✗ %s：文件不在 `scripts/` 下" % name)
            problems.append("%s：名单里登了，文件却不存在" % name)
            continue
        ok, why = boots_ok(name, path)
        print("  %s %-36s 装体：%s" % ("✓" if ok else "✗", name, why))
        if not ok:
            problems.append("%s：%s" % (name, why))

        src = io.open(path, encoding="utf-8").read()
        totals = find_totals(src)
        full = [(ln, call) for ln, call in totals if counted_labels(call) == want]
        partial = [(ln, call, counted_labels(call)) for ln, call in totals
                   if counted_labels(call) and counted_labels(call) != want]
        if full:
            print("      合计输出点：第 %s 行，标签齐全"
                  % "、".join(str(ln) for ln, _ in full))
        else:
            if partial:
                for ln, call, got in partial:
                    problems.append(
                        "%s：第 %d 行有个像合计的输出，标签只齐 %s，缺 %s"
                        % (name, ln, "/".join(sorted(got)) or "无",
                           "/".join(sorted(want - got)) or "无"))
            else:
                problems.append(
                    "%s：**源码里没有合计输出点**（既没有同时含 %s 的 print/echo，"
                    "也没有半个）" % (name, "、".join(REQUIRED_LABELS)))
            print("      合计输出点：**没有**")
        checked.append(name)

    # ── 事实无条件打印（纪律 320）──────────────────────────────────────────
    print()
    print("=" * 74)
    print("事实（无条件打印，与「有没有问题」无关）：")
    print("  慢反验名单 %d 份（读自 `%s` 的源码）" % (len(names), SLOW_SRC))
    print("  本轮核到 %d 份 / 名单 %d 份%s"
          % (len(checked), len(names),
             "" if len(checked) == len(names) else "，**有 %d 份没核到**" % (len(names) - len(checked))))
    print("  判据一（装体）与判据二（合计可解析）都已执行；判据零（顺序无关）%d 句夹具全过"
          % len(KNOWN_OUTPUT_SHAPES))
    print("  **本闸不跑慢反验，也不核合计的数值对不对**——那要真跑 %d 秒"
          % sum(v for v in secs.values() if isinstance(v, int)))
    print("耗时 %.2fs" % (time.time() - t0))

    if problems:
        print()
        print("=" * 74)
        print("✗ 查出 %d 处问题：" % len(problems))
        for p in problems:
            print("  · %s" % p)
        return 1
    print()
    print("✓ %d 份慢反验都装得上体、都报得出标签齐全的合计" % len(names))
    return 0


if __name__ == "__main__":
    sys.exit(main())
