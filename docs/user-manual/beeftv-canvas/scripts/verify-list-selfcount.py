#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十六道闸：正文里**「这 N 条」回指的是它上面那份列表时，N 必须等于那份列表的行数**。

**为什么要有这道闸（Batch 336 的由来）**：`20-reference.md` 的
「已经对不上的地方（2026-10-07 对 v1.7.3 实测的清单）」小节，
正文两处写「**这 7 条**」，而**那份清单是 6 行**。
更值得记的不是「7 错了」而是**它怎么错的**：
**同一个数词底下压着两个数**——
`7 道红闸`（漂移工具 `verify-upgrade-drift.py` 报的**变红闸数**）在本节上方出现三次，
而清单本身是 6 条，**「这 7 条」是照着 7 道写的**。
**所以这不是随手写错，是指代串了**：
节内既有「7 道」又有「6 条」，用「这 N 条」这种泛指句式时取到了错的那个。

**它为什么值得占一道闸，而不是顺手改掉就算了**：
这份清单正是**升版那一批会逐条改写的东西**——
每处理一条就可能增删条目，**而节内两处自述不会跟着自动变**。
今天改对了，下一批再动这个清单时没有任何东西会提醒。
**同型缺陷有先例且咬过人**：闸 9 方向九盯的「小节标题里手写的『（N 类）』须等于该表实际行数」，
**实测过期了整整 6 个批次而账面全绿**（Batch 161 记）。**同一个病，换了个地方复发。**

**口径为什么这么窄（本批为此专门量了全库，如实说明）**：
本批先做过一次通用普查——把**全部 .md**（含三份工程账本）里
「这 N 条 / 这 N 项 / 这 N 个 / …」这类自述数扫出来，**共 44 处**；
再把每处的「上方最近块」判出来，**22 处**带「这 N 条」，
**其中只有 1 处真错**（就是本闸要守的那 2 行），**其余 21 处全是指代别的东西**：

| 实测形态 | 处数 | 为什么不归本闸管 |
|---|---|---|
| 回指紧邻其上的顶层列表（本批新增的那 2 行） | 2 | **本闸唯一认的形态** |
| 上方是**表格**（`20-reference.md` 的「快捷键中心共 24 条」、闸清单表、批次表…） | 9 | 表行数与自述数**本来就不必相等**——实测那处正文自己写着「故表行数与条数不相等」 |
| 上方是**普通段落**（`AUDIT-RULES.md` 6 处、`AUDIT.md` 6 处…） | 6 | 指的是正文里随手铺开的分述，**不是一个可数的列表** |
| 上方**也是**顶层列表，但在**工程账本**里（`AUDIT.md:1252`「这 16 条」等） | 4 | **那三份是账本不是发布面**——它们数的是**历史批次的事实**（「Batch 129 时环境记录里的 16 条」），**历史就是历史，不该按今天的树重数**；而 `scope.published_paths()` 实测**恰好把 `AUDIT.md` / `AUDIT-RULES.md` / `PROGRESS.md` 全排除在外**（35 个发布页里没有这三份） |

**最后一行是本闸敢建的口径依据**：**发布面 = 读者当场能点着数的地方**，内容必须当场自洽；
**账本 = 只有维护者看的地方**，陈述的是历史，不该被「现在的树长什么样」判红。
**把判据开成「全库」，第一处误伤就是 `AUDIT.md:1252`**——实测确认过。
**一个会误伤的判据比没有判据更坏**（纪律 248），所以本闸**只扫发布面**。

**能力上限（必须说在前面，别让下一个人以为「自述数」整族都归它管）**：
① **只认「这 N 条」这一种量词**。「这 N 项 / N 个 / N 张 / N 类」实测在发布面里另有 2 处
（`20-reference.md` 的「这 12 张」「这 24 条」），**本闸不核它们**——
「12 张」数的是**条件子集**（正文自己写着「不是截图总数」），「24 条」指的是**上游界面**不是手册。
② **只认「上方最近块是顶层列表」这一种指代**。若某天有人在小节中间隔一段普通文字再回指同一份列表，
本闸**核不到**（它只向上找最近的非引用块）。
③ **只数顶层 `- ` 行**；一份列表若被普通段落隔成两段，**本闸会把两段数成一份**（合并计数）。
实测当前树**一处都没有这两种形态**，但那是实测结论、不是保证。

**方向二之二（自检探针，两条）**：
① 正向——人造一份「上面 2 条列表 + 下面「这 2 条」」，必须命中且数出 2；
② 反向——人造一份「上面表格 + 下面「这 24 条」」，必须**不**命中，
否则说明本闸抓的形态比声称的宽。**两条都不中一律 rc=2**——
**判据读空或匹配器退化时绝不许安静地全绿**（纪律 101）。

**下限守卫**：发布面里一处都没命中时报 rc=2——
「本闸此刻没有作用对象」与「全都相符」在 rc 上长得一样，**必须让人看见前者**。

退出码：0 相符；1 有自述条数与所回指的列表行数不符；2 未能核对
（读不到发布面 / 探针不中 / 判据此刻无作用对象 / 匹配到的列表数为 0）。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import scope  # noqa: E402
from baseline import announce_fallback  # noqa: E402

#: **根从 `scope` 取，不从 `__file__` 推**——这是本批实测出来的一个真缺陷，
#: **不是风格问题**（Batch 336 修的第一处）：
#: 第一版写的是 `ROOT = os.path.dirname(HERE)`（脚本所在目录），
#: 而**页面清单来自 `scope.published_paths()`**（那棵树由 `BEEFTV_MANUAL_ROOT` 决定）。
#: 两处根不是同一处，于是**清单按 A 树算、正文按 B 树读**：
#: `BEEFTV_MANUAL_ROOT` 指向夹具时，它列出夹具里的页面、却去读**真手册**的同名文件——
#: **实测反验的 3 个「能抓 / 未能核对」用例全部报绿，因为它们根本没碰到夹具里的那页。**
#: **这是纪律 101 最坏的一种形态**：不是「读空报绿」，是**「核了另一棵树还报绿」**
#: ——**而它报出来的那句话是真的**（真手册那两处确实相符），
#: **所以连输出都看不出异常**。
#: `scope.ROOT` 是「这棵树在哪」的**单一事实源**（`scope.py` 自己让环境变量优先于 `__file__`，
#: Batch 178 的教训）；**判据自己再算一遍根，等于把那份事实抄成两份**（纪律 367⑦ 的同一条精神）。
ROOT = scope.ROOT

HEAD_RE = re.compile(r"^#{1,6}\s")
TOP_RE = re.compile(r"^- ")
TABLE_RE = re.compile(r"^\|")
#: **本闸唯一认的量词是「条」**。理由与覆盖面见模块 docstring 的「能力上限」①。
CLAIM_RE = re.compile(r"这\s*(\d+)\s*条")


def block_above(seg, idx):
    """返回 ``(块类型, 顶层条目数)``：``seg[idx]`` **上方最近的非引用块**。

    **为什么要跳过引用块**：实测 `20-reference.md` 那两行自述都躺在引用块里，
    而它们的上一段引用块又是另一段引用块——**只找「紧邻的上一段」会两处都漏**。
    引用块本身不构成对上一块的引用，**所以一路跳到最近的非引用块为止**。

    类型只有三种：``BULLET``（顶层 ``- `` 列表，带顶层条目数）、
    ``TABLE``（表格）、``TEXT``/``NONE``（普通段落 / 越出小节）。
    """
    j = idx - 1
    while j >= 0 and (not seg[j].strip() or seg[j].startswith(">")):
        j -= 1
    if j < 0 or HEAD_RE.match(seg[j]):
        return ("NONE", 0)
    # 回溯到这一段的起点（空行 / 标题 / 表格行 / 引用块 都不与它连成一段）
    start = j
    while start > 0 and seg[start - 1].strip() \
            and not HEAD_RE.match(seg[start - 1]) \
            and not TABLE_RE.match(seg[start - 1]) \
            and not seg[start - 1].startswith(">"):
        start -= 1
    if TABLE_RE.match(seg[start]):
        return ("TABLE", 0)
    if not TOP_RE.match(seg[start]):
        return ("TEXT", 0)
    # 从段首向下数顶层条目：**跨空行继续**（松散列表），
    # 撞到标题 / 表格 / 引用块 / 顶层普通文本就停（那已经不是这份列表了）。
    count = 0
    k = start
    while k < len(seg) and not HEAD_RE.match(seg[k]) and not TABLE_RE.match(seg[k]):
        line = seg[k]
        if TOP_RE.match(line):
            count += 1
        elif line.strip() and not line.startswith((" ", "\t")):
            break                      # 顶格的引用块或普通文本：列表到此为止
        k += 1
    return ("BULLET", count)


def scan(text, rel):
    """扫一个页面，返回 ``[(行号, 自述数, 实测行数, 摘录)]``，**只收上方是列表的那些**。"""
    lines = text.split("\n")
    bounds = [i for i, l in enumerate(lines) if HEAD_RE.match(l)]
    bounds.append(len(lines))
    hits = []
    for k in range(len(bounds) - 1):
        seg = lines[bounds[k]:bounds[k + 1]]
        for i, line in enumerate(seg):
            m = CLAIM_RE.search(line)
            if not m:
                continue
            kind, count = block_above(seg, i)
            if kind != "BULLET":
                continue
            hits.append((bounds[k] + i + 1, int(m.group(1)), count,
                         line.strip()[:90], rel))
    return hits


#: **方向二之二 的探针语料**：**刻意放在模块里而不在 `main()` 里现搭**——
#: 现搭的探针与判据共用同一段拼装逻辑，**那不叫独立**（批次 335 记过「判据对、样本错」那类坑）。
#: **两份语料都自带 `## ` 标题**：小节边界就是靠标题切的（`scan()` 的 `bounds`），
#: **语料里没有标题 → 一个子段都不成立 → 扫出 0 处**——
#: **第一版正是这么写的，于是正向探针报 rc=2**。
#: **值得留着这一条**：它证明**探针是活的**（语料错它真报），
#: 而不是那种「怎么摆弄都命中」的恒真探针。
PROBE_OK = ["## 探针", "", "- 甲", "  甲的续行", "- 乙", "",
            "> 抄在这里：", "> 而这 2 条说的是上面那两行。"]
PROBE_BAD = ["## 探针", "", "| 键 | 行为 |", "|---|---|", "| A | B |", "",
             "> 而这 24 条指的是界面里的条目，与本表行数无关。"]


def probe():
    """跑正反两条探针。返回 ``None`` 即通过，否则返回失败原因。

    **整个函数体包在 ``try`` 里**：第一版没有包，
    **解包位数写错时它直接抛 ``ValueError`` 逃到顶层**，
    而 Python 对未捕获异常的退出码是 **1**——
    **1 在本闸的语义里是「核出不一致」，而这里真实含义是「判据自己没跑起来」**，
    **两者混成同一个码，纪律 101 就地失效**（批次 335 踩过同一个坑：分不清「判据没跑起来」与「判据报了问题」）。
    **所以任何异常都收成 rc=2，不许它走 1。**
    """
    try:
        hit = scan("\n".join(PROBE_OK), "<探针>")
        if len(hit) != 1:
            return f"正向探针应恰好命中 1 处，实测 {len(hit)} 处"
        _, said, count, _, _ = hit[0]
        if said != 2 or count != 2:
            return f"正向探针应数出「说了 2、实有 2」，实测「说了 {said}、实有 {count}」"
        if scan("\n".join(PROBE_BAD), "<探针>"):
            return "反向探针被误命中——**本闸抓的形态比声称的宽**（上方是表格时不该管）"
    except Exception as exc:                       # noqa: BLE001 —— 判据自己坏了即 rc=2
        return f"探针执行时抛出 {type(exc).__name__}（{exc}）——**判据自身不可用**"
    return None


def main():
    #: **必须是 `main()` 的第一句**（纪律 172）：
    #: 放在任何 ``[skip]`` 分支之后，就等于「降级了但读者看不到」，
    #: **而那正是本闸要防的形态自己**。
    announce_fallback()
    try:
        pages = scope.published_paths()
    except Exception as exc:                       # noqa: BLE001 —— 读不到事实源即 rc=2
        print(f"[skip] 读不到发布面（{exc}），本轮未能核对")
        return 2
    if not pages:
        print("[skip] 发布面 0 个 .md，判据读空 —— 不是「没有不一致」")
        return 2

    why = probe()
    if why:
        print(f"[skip] {why}，本轮未能核对")
        return 2

    bad, checked = [], 0
    for rel in pages:
        path = os.path.join(ROOT, rel)
        try:
            with open(path, encoding="utf-8") as fh:
                text = fh.read()
        except OSError as exc:
            print(f"[skip] 读不到 {rel}（{exc}），本轮未能核对")
            return 2
        try:
            hits = scan(text, rel)
        except Exception as exc:                   # noqa: BLE001 —— 同 `probe()` 的理由
            print(f"[skip] 扫 {rel} 时抛出 {type(exc).__name__}（{exc}）"
                  "——**判据自身不可用**，本轮未能核对")
            return 2
        for idx, said, count, snippet, _rel in hits:
            checked += 1
            if count == 0:
                print(f"[skip] {rel}:{idx} 上方那份列表数出 0 条，判据读到空结构，本轮未能核对")
                return 2
            if said != count:
                bad.append(f"{rel}:{idx}  写「这 {said} 条」，而它上面那份清单是 {count} 条：{snippet}")

    if checked == 0:
        print("[skip] 发布面里一处「这 N 条」都没匹配上——"
              "**本闸此刻没有作用对象**，与「全都相符」在 rc 上长得一样，不许报绿")
        return 2
    if bad:
        print(f"清单自述条数核对：{len(bad)}/{checked} 处「这 N 条」与所回指的列表行数不符")
        for b in bad:
            print("  " + b)
        print("→ 改自述的数，或改列表本身；**别改判据**——"
              "放宽等于把这次发现再埋一次（纪律 112）。"
              "另注：本节里若还有一个**别的**数（如「N 道闸变红」），"
              "**那是另一个量，别拿它来校这一处**")
        return 1
    print(f"清单自述条数核对通过：{len(pages)} 个发布页里 {checked} 处「这 N 条」"
          f"与所回指的列表行数一致")
    return 0


if __name__ == "__main__":
    sys.exit(main())
