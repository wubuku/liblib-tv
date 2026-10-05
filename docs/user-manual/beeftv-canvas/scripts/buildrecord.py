#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**「上一次全绿构建是哪一批」的唯一来源**（Batch 255 新增）。

**这个模块存在的理由是一句写在纪律 280 里的话**：
Batch 252 与 253 的构建实测各有一个 `[ FAIL ]`、且都**停在闸 18**
（闸 19 到 36 与全部文档闸一次都没运行），
**而我照常提交并推送了**，批次行里写的验收结论是「构建仍全绿」。
`build-site.sh` 的 `fail()` 是 `exit 1`，**脚本是对的——
是我没有把退出码当回事。**

**整套体系里唯一没有被机械化的一环，就是「有人看了构建的退出码」**，
而它恰好是唯一一个不需要写任何代码的环节。

**本模块提供的那一环**：

| 谁 | 做什么 | 凭什么可信 |
|---|---|---|
| `build-site.sh` 末尾 | 调 `record-build-result.py` 写记录 | **能走到脚本末尾本身就是 rc=0 的证明**——`fail()` 会 `exit 1` |
| `.git/hooks/pre-commit` | 提交前核「本次新增的批次号 ≤ 记录里的批次号」 | 记录是构建写的，不是我手打的 |

**为什么记录落在 `.git/` 里**：它必须**不被跟踪**——
写进手册树会让每次构建都弄脏工作区，
而闸 18 方向三要求「闸只读手册树」，**一份会写树的记录会与它打架**；
写进 `dist/` 又不在版本控制里，闸读不到。
**`.git/` 里的文件天然不被 git 跟踪，是唯一同时满足「不被跟踪」与「可被本地钩子读到」的位置。**

**它明确不做什么**：**它不核「那次构建是不是真的绿」**——
那只能靠人看退出码，而本模块做的事是让「忘了看」在**提交那一刻**就暴露。
**一条依据能被机械兑现才算存在（纪律 178），而这一条兑现的是「提交前必须有过一次绿构建」。**

零外部依赖，与 `baseline` / `batchread` / `scope` / `pngstat` / `stagedeps` 一致。
"""

import io
import os
import re
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROGRESS = os.path.join(ROOT, "PROGRESS.md")

#: **记录文件名**。放在 `.git/` 下，**天然不被跟踪**——
#: 手册树必须保持「构建跑完还是干净的」，否则闸 18 方向三与 `git status` 都会有话说。
RECORD_NAME = "beeftv-build-record"

#: **只认纯数字的批次号。**
#:
#: **为什么不能直接用 `verify-ledger-refs.batch_table_numbers()` 的返回值取 max**：
#: 那个集合里**有意**包含 `17a` / `17b` / `17c` / `6a` / `6b` / `6c` / `8a` / `8b`
#: ——**子批次是刻意允许的**（它的 `NUM_RE` 是 `^\d+[a-z]?$`），
#: **所以那不是解析缺陷，本模块不去动它**。
#: 但**「最新批次号」这个问题问的是纯数字的最大值**，
#: 直接 `max()` 会拿到字符串序的 `99`——
#: **因为批次表不是按数字排序的**（254 那一行的下一行是 239，再往下是 137、136）。
_BATCH_NUM = re.compile(r"^\d+$")


def repo_root():
    """手册目录的上级就是 git 仓根**——但本模块不假设它**。

    **实测过的两种可能**：`docs/user-manual/beeftv-canvas` 与手册目录同级。
    找法是**向上找 `.git`**，找不到就用手册目录的祖父目录。
    **写死路径是纪律 243 明确禁过的那件事**（同一份事实被手写几遍就会有几套判真条件）。
    """
    d = ROOT
    for _ in range(6):
        if os.path.isdir(os.path.join(d, ".git")):
            return d
        d = os.path.dirname(d)
    return os.path.dirname(os.path.dirname(ROOT))


def record_path():
    return os.path.join(repo_root(), ".git", RECORD_NAME)


def read_record():
    """读记录；**读不到就返回 `None`，而调用方必须把它当成「没有绿构建」而不是「放行」**。"""
    p = record_path()
    try:
        with io.open(p, encoding="utf-8") as f:
            rec = {}
            for line in f:
                if "=" in line:
                    k, v = line.strip().split("=", 1)
                    rec[k] = v
            return rec or None
    except (OSError, UnicodeDecodeError):
        return None


def write_record(batch, ok, warn, fail, source, secs=None):
    """**只有 `fail == 0` 的构建才该调用它**——而 `build-site.sh` 能走到末尾就意味着这一点。

    **`source` 这个键名是订正过的**：第一版沿用 `log=`，而传进来的其实是
    **`--counts` 的那个字符串**（`"82,0,0"`）——
    **字段叫 log、装的是计数，而 `log` 这个名字会让下一个人去找一个构建日志**
    **（而构建日志在 `/tmp` 下、早就没了）**。
    **判据的键必须与它声称在问的那件事是同一个键**（纪律 172）：
    **一个名字对不上的键，比没有这个键更费时间。**

    **`secs` 是 Batch 280 加的**（墙钟，单位秒）。**它必须由脚本自己写**：
    「构建要多久」这个量在本项目里被手抄进 8 处，**而从 Batch 192 起那份抄本就写着
    25 秒——**实测 251 秒，低了 10 倍**（纪律 310 的第五个实例，
    而这一次过期的是一条**被用来做决策的理由**：Batch 279 建闸 41 时
    「5.4 秒 vs 25 秒」那个比较就出自它）。
    **传 `None` 会写下一个空的 `secs=`**——**那是有意的**：
    **空值让方向四g 报「没有真值」，而缺字段只会被读成「没写这项」**。
    """
    body = (
        "# 由 build-site.sh 在**走到脚本末尾时**写下；能被走到本身就是 rc=0 的证明。\n"
        "# 不要手改：手改它等于把纪律 280 那件事再做一遍。\n"
        "# **计数由 build-site.sh 末尾的 awk 从一个 mktemp 文件读出**——\n"
        "# **不是从日志正则解析的**（那条路试过，与真格式失配会数成 0）。\n"
        "batch=%d\nok=%d\nwarn=%d\nfail=%d\n"
        "source=%s\nsecs=%s\nat=%s\n" % (int(batch), int(ok), int(warn), int(fail),
                                 source, secs,
                                 time.strftime("%Y-%m-%d %H:%M:%S"))
    )
    p = record_path()
    with io.open(p, "w", encoding="utf-8") as f:
        f.write(body)
    return p


def batch_table_numbers():
    """**批次表里的编号集合（含子批次）**——直接复用闸 21 那一份实现。

    **为什么复用而不是自己解析**（纪律 274：共享概念只能有一份实现）：
    `ROW_RE = ^\\|\\s*([^|]*?)\\s*\\|` 现在在 `verify-batch-rows.py` 与
    `verify-ledger-refs.py` 里**各有一份拷贝**，
    **本模块要是再写第三份，就成了同一件事三套判真条件**。
    """
    import importlib.util
    p = os.path.join(ROOT, "scripts", "verify-ledger-refs.py")
    spec = importlib.util.spec_from_file_location("_beef_ledger_refs", p)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m.batch_table_numbers()


def newest_batch():
    """**批次表里最大的纯数字批次号**。**解析不出任何一个就返回 `None`**——
    调用方必须把 `None` 当成「未能核对」，**不得当成 0**（0 会让任何比较都通过）。"""
    try:
        nums = batch_table_numbers()
    except Exception:                                   # noqa: BLE001
        return None
    plain = [int(x) for x in nums if _BATCH_NUM.match(x)]
    return max(plain) if plain else None


def added_batch_numbers(diff_text):
    """**从 `git diff` 的新增行里取批次号，返回前导数字的整数集合。**

    **只看 `+` 行**：已存在的行不是这一批新增的，
    而闸 19 已经在核「每个批次号只登记一次」——
    **本模块不重复那个问题，只问「这一批新登记了哪些批次」**。

    **子批次必须一起抓**（Batch 255 反验用例 7 抓出来的缺口）：
    本树的批次表里**有意**存在 `17a` / `17b` / `17c` / `6a` / `6b` / `6c` /
    `8a` / `8b` 这类带字母后缀的子批次（闸 21 的 `NUM_RE` 是 `^\\d+[a-z]?$`），
    **而第一版只认纯数字，于是 `+| 300a |` 会被整行跳过**——
    **那样「新增一个子批次而没为它跑过绿构建」就抓不到。**
    **所以这里取前导数字、丢掉字母后缀**：比的是数量级，字母后缀不参与比较。
    """
    out = set()
    for line in diff_text.split("\n"):
        if not line.startswith("+") or line.startswith("+++"):
            continue
        m = re.match(r"^\+\|\s*(\d+)[a-z]?\s*\|", line)
        if m:
            out.add(int(m.group(1)))
    return out


def check(diff_text):
    """返回问题清单（空列表 = 放行）。**三段退出码的语义在这里是「有 / 无 / 未能核对」。**

    **Batch 280 加了第四个条件**：**新增批次行时，最新绿记录里必须有正的 `secs=`**
    （构建墙钟）。**为什么是这里而不是某道闸，见下面那段注释**——
    **一句话版本：构建中途读到的永远是上一次的记录，所以那道题只能在这里问。**
    """
    added = added_batch_numbers(diff_text)
    if not added:
        return []                       # **没新增批次行 = 这一笔提交与构建无关**
    rec = read_record()
    if not rec:
        return ["本次提交新增了批次行 %s，而**没有任何一次全绿构建的记录**"
                "（`%s` 不存在）——**先跑一次 `build-site.sh` 并确认退出码是 0**"
                % (sorted(added), record_path())]
    try:
        rb = int(rec["batch"])
    except (KeyError, ValueError):
        return ["构建记录里的 `batch` 读不出来（内容：%r）——**记录已坏，按没有绿构建处理**"
                % rec.get("batch")]
    if max(added) > rb:
        return ["本次提交新增了批次行 %s，而**上一次全绿构建只走到 Batch %d**"
                "（%s ok / %s warn / %s fail，记录于 %s）"
                "——**新增批次却没有为它跑过一次绿构建**（纪律 280）"
                % (sorted(added), rb, rec.get("ok", "?"), rec.get("warn", "?"),
                   rec.get("fail", "?"), rec.get("at", "?"))]
    # ── Batch 280：核「这一次绿构建有没有测出构建墙钟」──────────────────
    #
    # **为什么放在这里，而不放进构建里的某道闸**：构建中途读到的永远是
    # **上一次**构建写的记录，而记录只在 `fail == 0` 时才写——
    # **于是一个构建期判据若要求「记录里有 `secs=`」，上线后的第一次构建必然红，
    # 而那次红又保证记录不会被更新，于是永远红**。**那是死锁，不是失败。**
    # **这里不一样**：走到本行就意味着**本次提交新增了批次行**，
    # **而纪律 280 本来就要求为它跑过一次绿构建**——**所以绿记录此刻必然存在**。
    #
    # **为什么要核它**：本批实测构建墙钟 251 秒，**而全树 8 处手抄都写着「25 秒」**
    # （低了 10 倍，纪律 310 的第五个实例）。
    # **机制是 Batch 280 加的**：每次构建自己把墙钟写进记录。
    # **而机制也会坏**——所以要有一条判据问「它真的写出来了吗」。
    try:
        secs = int(rec.get("secs") or 0)
    except (TypeError, ValueError):
        secs = 0
    if secs <= 0:
        return ["上一次全绿构建的记录里**没有正的 `secs=`**（读到 %r）"
                "——**「构建要多久」这个量于是没有真值**，"
                "全树那些秒数就都只是手抄（**本项目那份手抄低了 10 倍**："
                "Batch 192 写「25 秒」，Batch 280 实测 **251 秒**）。"
                "**修法是再跑一次 `build-site.sh`**，而不是去改某个抄本"
                % rec.get("secs")]
    return []
