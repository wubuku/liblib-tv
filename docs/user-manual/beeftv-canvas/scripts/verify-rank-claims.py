#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十三道闸：序关系断言与快照表指针（Batch 301 新增）。

**起因是纪律 335 查出的两处「从来没人看守」**：

  · `10-tasks/model-channels.md` 页首曾写「本页是产品里源码量第三大的界面页」，
    **而按快照表自己定义的口径，`web/src/pages/settings` 在 v1.6.16 / v1.6.22 /
    `origin/main` 三个 ref 上都是第 5 位**——**它不是漂移，它写下那天就是错的**。
  · 快照表第三列（`model-channels.md`）指向的文件早已搬到 `10-tasks/`，
    **而它写成反引号不是 Markdown 链接，所以闸 6 的链接核对看不见它**。

**闸 11 核的是「表里的数 == 上游的数」；而「第三大」这个词既不在表里、也不在任何判据里。
表管的是数，页面说的是序，两者之间没有任何东西——本闸补的就是那个东西。**

**判据的形状是量出来的，不是想出来的**（纪律 171 / 225：范围是量过才定的）：
宽松措辞全树命中 **11 处**，逐条读原文分成**活断言 4 处 + 引用历史 7 处**，
**而这两种形态可机械区分**：

  | 形态 | 判别条件 | 命中 |
  | --- | --- | --- |
  | **活断言** | 在 Markdown **表格行**里 | 3（快照表第三列自己） |
  | **活断言** | `**加粗**`且带参数括号、且序关系措辞**不被 「」 包住** | 1（`create-workspace.md`） |
  | **引用历史** | 序关系措辞**被 「」 包住**（「原来写的是…」「而不是…」） | 7 |

**刻意不排除历史引用，而是把它们数出来打出来**——
**一个「静默排除的类别」就是 Batch 225 踩过的那个坑（降级声明被当成实测声明）**。

三个方向：

  · 方向一：**每条活断言都必须自带对照集**。只说「第 N 大」而不说对照集是什么，
    就是一个**不可核对的声明**——而 Batch 300 实测那正是错的唯一一条。
    **判据问的是「这句话能不能被核对」，不是「它对不对」**（纪律 287）。
  · 方向二：**能抽出对照集的，现场重数复核**：目标路径必须真的排第 N，
    点名的对照集必须真的是前 N-1 名。抽不出路径或名次 → 记「不可核对」并报出。
  · 方向三：**快照表第三列里凡出现 `.md` 文件名的，那个文件必须真实存在**
    （`20-reference.md` 里有一格已经写成 Markdown 链接，另两格是反引号——
    **两种写法的看守强度不同，而反引号那种闸 6 看不见**，所以本方向不看写法只看存在性）。

**方向三之二（自检探针）**：拿一条**必须能被抽出来**的已知声明当探针；
抽不出来就 rc=2「未能核对」——**不能让判据在语料读空时安静地全绿**（纪律 101）。

退出码：0 无问题；1 有问题；2 未能核对。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beefsrc                                    # noqa: E402
from baseline import resolve_ref, BaselineError, announce_fallback  # noqa: E402
from batchread import read_many                            # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INTERNAL = {"AUDIT.md", "AUDIT-RULES.md", "PROGRESS.md", "FINAL-REPORT.md",
            "SOURCE_OBSERVATIONS.md"}
SKIP_DIRS = {".git", "node_modules", ".vitepress", "dist", ".agents", ".claude"}

CODE_EXT = (".ts", ".tsx")

# 序关系措辞。**刻意宽松**（宁可多命中再分类，也不要先把范围收窄到「我以为的那几个」）。
RANK_PATTERN = (
    r"(最大的页面目录|最大的界面页|位次第[一二三四五六七八九十]|"
    r"体量第[一二三四五六七八九十]大|第[一二三四五六七八九十]大|"
    r"仅次于|排名第|源码量第[一二三四五六七八九十]|第二大门户|"
    r"前两名是|前[一二两三四]名是)")
RANK_WORDS = re.compile(RANK_PATTERN)
# 「被 「」 包住」＝在引用历史，不是活断言
QUOTED = re.compile("[「『][^」』]*" + RANK_PATTERN + "[^」』]*[」』]")
# 「前 N 名是 X 与 Y」这种显式对照集
NAMED_PEERS = re.compile(r"前[一二两三四]名是([^），。]+)")
# 括号里的 `web/src/...` 路径
TARGET_PATH = re.compile(r"`(web/src/[^`]+)`")
CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7,
          "八": 8, "九": 9, "十": 10}
RANK_NUM = re.compile(r"第([一二三四五六七八九十])[大位]")
PEER_NAME = re.compile(r"`([A-Za-z0-9_\-]+)`")

# 快照表：路径列的行（`| `web/src/...` | 数字 | 第三列 |`）
SNAP_ROW = re.compile(r"^\|\s*`(web/src/[^`]+)`\s*\|\s*(\d+)\s*\|\s*(.+?)\s*\|\s*$")

# 方向三之二的自检探针：**全树必须存在的那一条**（内容页里那句自带对照集的活断言）。
#
# **探针必须挑一个与判据触发词不同的字符串。**
# 第一版拿「前两名是」当探针——**而那正是 `NAMED_PEERS` 的触发词**，
# 于是「删掉对照集」这个本该由方向一报出的注入，被探针先接走、rc 变成 2。
# **探针与被测对象撞在同一个 token 上，判据就永远测不到自己**（Batch 290 的跨文件锚点
# 耦合在同一个文件里复发了一次）。
# 改用**目标路径**当探针：删对照集不动它，而删路径才动它。
PROBE_FILE = "10-tasks/create-workspace.md"
PROBE_TEXT = "`web/src/pages/create`"


def cn2int(s):
    return CN_NUM.get(s)


def _nlines(blob_bytes):
    """`wc -l` 语义。**必须与 `verify-line-counts.py` 逐字同口径**
    （Batch 300 实测踩过两次：`split("\\n")` 多算末尾空串、`maxdepth 1` 不递归）。"""
    t = blob_bytes.decode("utf-8", "replace")
    return t.count("\n") + (1 if t and not t.endswith("\n") else 0)


def page_rankings(src, ref):
    """`web/src/pages` 下各目录行数，降序。

    **一次 `ls-tree` + 一次 `read_many`**，而不是「每个目录各跑一次 `ls-tree`、
    再逐文件 `git show`」——后者实测 **3.0 秒**，而前者实测 **0.1 秒量级**。
    **逐文件 `git show` 是 Batch 181 就已经否掉的写法**（347 个文件发 347 次进程），
    **`batchread` 就是为这件事存在的**——**用它而不是自己手搓 `cat-file` 解析，
    因为那份 docstring 已经把 `--batch` 尾部那个 LF 的坑写清楚了**。
    """
    import subprocess

    r = subprocess.run(["git", "-C", src, "ls-tree", "-r", "--name-only", ref,
                        "--", "web/src/pages"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return []
    groups = {}
    for n in r.stdout.split("\n"):
        if not n.endswith(CODE_EXT):
            continue
        parts = n.split("/")
        if len(parts) > 3:
            groups.setdefault("web/src/pages/" + parts[3], []).append(n)
    if not groups:
        return []
    blobs = read_many(src, ref, [n for names in groups.values() for n in names])
    out = []
    for rel, names in groups.items():
        tot = 0
        ok = True
        for n in names:
            b = blobs.get(n)
            if b is None:
                ok = False
                break
            tot += _nlines(b)
        if ok:
            out.append((rel, tot))
    out.sort(key=lambda x: -x[1])
    return out


def content_lines():
    """→ [(相对路径, 行号, 整行)]，账本与产物目录排除。"""
    for dp, dn, fns in os.walk(ROOT):
        dn[:] = [d for d in dn if d not in SKIP_DIRS]
        for fn in sorted(fns):
            if not fn.endswith(".md") or fn in INTERNAL:
                continue
            p = os.path.join(dp, fn)
            rel = os.path.relpath(p, ROOT)
            with open(p, encoding="utf-8") as fh:
                for i, line in enumerate(fh.read().split("\n"), 1):
                    yield rel, i, line


def main():
    try:
        src, _fb = beefsrc.resolve_src()
        if src is None:
            print("[未能核对] 找不到可用的 BeefTV 源码仓。候选与判真结果：\n"
                  + beefsrc.explain())
            return 2
        announce_fallback()
        ref = resolve_ref()
    except (OSError, BaselineError) as exc:
        print("[未能核对] %s" % exc)
        return 2

    # ---- 语料读空防护：扫不到任何内容页就是读空了 ----
    corpus = list(content_lines())
    if not corpus:
        print("[未能核对] 一个内容页都没扫到——语料读取退化了，"
              "此时判据的「全绿」不可信")
        return 2

    live = []      # 活断言
    quoted = 0     # 引用历史（**数出来打出来，不静默排除**）
    for rel, i, line in corpus:
        if not RANK_WORDS.search(line):
            continue
        # **快照表的行不进方向一/二**：第三列是对页面那句的**转述**，
        # 它的职责是「指针有效」（方向三）与「数对得上」（闸 11），
        # **而要求一个转述格自带对照集是判据越界**——
        # 第一版就是这么把 3 行表全报了一遍，而那 3 行本来就该由闸 11 管。
        if SNAP_ROW.match(line):
            continue
        if QUOTED.search(line):
            quoted += 1
            continue
        live.append((rel, i, line))

    # ---- 方向三之二：自检探针 ----
    if not any(rel == PROBE_FILE and PROBE_TEXT in line
               for rel, _i, line in live):
        if not any(rel == PROBE_FILE and PROBE_TEXT in line
                   for rel, _i, line in corpus):
            print("[未能核对] 自检探针 `%s` 里的「%s」找不到——"
                  "**它要么被改写了，要么语料读空了**，"
                  "此时判据的「全绿」不可信" % (PROBE_FILE, PROBE_TEXT))
            return 2

    problems = []
    checked = 0
    unverifiable = 0
    ranking = page_rankings(src, ref)

    for rel, i, line in live:
        path_m = TARGET_PATH.search(line)
        rank_m = RANK_NUM.search(line)
        peers_m = NAMED_PEERS.search(line)
        where = "%s:%d" % (rel, i)
        if not path_m:
            problems.append(
                "方向一：%s 的序关系断言**没写它在说哪个路径**"
                "（原文：%s）——不可核对的声明等于没有声明" % (where, line.strip()[:60]))
            unverifiable += 1
            continue
        if not peers_m:
            problems.append(
                "方向一：%s 的序关系断言**没有写出它的对照集**"
                "（原文：%s）——**Batch 300 实测那正是唯一错的一条**"
                % (where, line.strip()[:60]))
            unverifiable += 1
            continue
        if not rank_m:
            problems.append(
                "方向二：%s 写出了对照集却读不出名次（原文：%s）"
                % (where, line.strip()[:60]))
            unverifiable += 1
            continue
        want = cn2int(rank_m.group(1))
        target = path_m.group(1)
        peers = PEER_NAME.findall(peers_m.group(1))
        if not want or not peers:
            problems.append("方向二：%s 的名次或对照集读不出来" % where)
            unverifiable += 1
            continue
        if not ranking:
            print("[未能核对] 在 %s 上数不出 web/src/pages 各目录的行数" % ref)
            return 2
        names = [n for n, _ in ranking]
        if target not in names:
            problems.append(
                "方向二：%s 的目标 %s 不在 %s 的 web/src/pages 目录清单里"
                % (where, target, ref))
            unverifiable += 1
            continue
        pos = names.index(target) + 1
        if pos != want:
            problems.append(
                "方向二：%s 声称 %s 排第 %d，**实测第 %d**"
                "（%s）——**行数只能当量级参考，而名次是可以现场数的**"
                % (where, target, want, pos, ref))
            checked += 1
            continue
        # 对照集必须真的是前 N-1 名（按点名顺序）。
        # **两边都归一到 basename 再比**：页面里写的是「画布工作区 `canvas`」，
        # 而现场数出来的是 `web/src/pages/canvas`——**不归一就报一个假的**。
        # 第一版就栽在这里，而那个假报长得像一条真发现。
        ahead = [n.rsplit("/", 1)[-1] for n in names[:want - 1]]
        named = [p.rsplit("/", 1)[-1] for p in peers[:want - 1]]
        if ahead != named:
            problems.append(
                "方向二：%s 写「前%d名是 %s」，**实测前%d名是 %s**"
                % (where, want - 1, "、".join(named), want - 1, "、".join(ahead)))
            checked += 1
            continue
        checked += 1

    # ---- 方向三：快照表第三列里的 `.md` 文件名必须存在 ----
    snap = os.path.join(ROOT, "20-reference.md")
    snap_rows = 0
    bad_refs = 0
    if os.path.isfile(snap):
        # **三种写法都要能落地**：`10-tasks/model-channels.md`（带目录）、
        # `create-workspace.md`（**裸文件名**）、以及纯描述无路径。
        # **裸文件名那条本身就是「对照集没写下来」的同一种病**——
        # 所以判据不猜它在哪，而是要求**全树按 basename 找必须唯一命中**。
        index = {}
        for dp, dn, fns in os.walk(ROOT):
            dn[:] = [d for d in dn if d not in SKIP_DIRS]
            for fn in fns:
                if fn.endswith(".md"):
                    index.setdefault(fn, []).append(
                        os.path.relpath(os.path.join(dp, fn), ROOT))
        with open(snap, encoding="utf-8") as fh:
            for i, line in enumerate(fh.read().split("\n"), 1):
                m = SNAP_ROW.match(line)
                if not m:
                    continue
                snap_rows += 1
                for fmd in re.findall(r"`([^`]+\.md)`", m.group(3)):
                    hits = index.get(os.path.basename(fmd), [])
                    if len(hits) == 1 and hits[0] == fmd:
                        continue          # 带目录且全树唯一：指向准确
                    if len(hits) == 1:
                        problems.append(
                            "方向三：快照表第 %d 行第三列写 `%s`，"
                            "**实际在 `%s`**——这一格是「这个数用在哪句话」的指针，"
                            "而指针自己的路径是过期的"
                            % (i, fmd, hits[0]))
                        bad_refs += 1
                    elif not hits:
                        problems.append(
                            "方向三：快照表第 %d 行第三列指向 `%s`，"
                            "**手册树里没有同名 .md**" % (i, fmd))
                        bad_refs += 1
                    else:
                        problems.append(
                            "方向三：快照表第 %d 行第三列写 `%s`（**裸文件名**），"
                            "而全树有 %d 个同名文件，**无法确定它指哪一个**：%s"
                            % (i, fmd, len(hits), "、".join(sorted(hits)[:4])))
                        bad_refs += 1
    else:
        print("[未能核对] 读不到 20-reference.md，快照表指针无从核对")
        return 2
    if snap_rows == 0:
        print("[未能核对] 快照表一行都没解析出来——解析规则退化了")
        return 2

    print("序关系断言核对：扫 %d 个内容页，活断言 **%d** 条、引用历史 **%d** 条"
          % (len({c[0] for c in corpus}), len(live), quoted))
    print("  方向二实测复核 %d 条（另有 %d 条不可核对）"
          % (checked, unverifiable))
    print("  方向三快照表 %d 行，指针失效 %d 处" % (snap_rows, bad_refs))
    print("  对照 ref = %s" % ref)
    # **Batch 313 新增：把「被观察的那几个数」印出来。**
    # **为什么非印不可**：本闸在两个 ref 上的输出此前**逐字节相同、只差 ref 名**
    # （纪律 334⑤ 记的「差异只有 ref 名」那种形态）——
    # **而输出相同推不出「上游那几样没变」**：
    # 实测 `web/src/pages` 有 **7 个顶层目录的行数在两个 ref 上都变了**
    # （canvas +21.0% / settings +14.4% / assets +13.8% / create +11.3% /
    # projects +5.5% / tasks +2.5% / dev +25.6%），
    # **只是名次没变所以判定无害**——**这是 C 类，不是 B 类**。
    # **而分清 B 与 C 的那些证据当时不在本闸的输出里，得由闸 11 提供**，
    # **一份四类分类表不该依赖另一道闸的输出才能填**。
    # **印出来之后，「它看见了变化」这件事本闸自己就能回答。**
    # **刻意只印前 6 名**：全量目录数会随上游增删而变，
    # **而这一行是给人读证据的，不是给人比对版本的**。
    for i, (n, tot) in enumerate(ranking[:6], 1):
        print("  实测第 %d 名 %s：%d 行" % (i, n.rsplit("/", 1)[-1], tot))
    if problems:
        for x in problems:
            print("  ✗ %s" % x)
        print("序关系断言核对：%d 处问题" % len(problems))
        return 1
    print("序关系断言核对通过：活断言 %d 条全部自带对照集且实测相符，"
          "快照表 %d 行指针全部有效" % (len(live), snap_rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())