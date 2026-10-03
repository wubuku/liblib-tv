#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第三十一道闸：正文里的**「当前 X 版本」必须等于取证基线**。

**为什么要有这道闸（Batch 234 的由来）**：`00-quickstart.md` 写着
「有些功能在别的介绍里见过，但**当前 v1.6.16 客户端里打不开**」——
而手册声明的适用版本是 **v1.6.22**（`README.md` 开头 + `20-reference.md` 的「取证基线」）。
**「当前」是指向基线的指针**：读者读这句话时，脑子里那个版本就是「这本手册写的那个版本」，
写成 v1.6.16 就等于手册自己把「当前」指向了一个**已经不是当前的版本**。
而基线是会随升版一路往前走的（Batch 178 就升过 v1.6.16 → v1.6.22），
**每一次升版都会让这句话悄悄过期，而没有任何机制提醒**。

**本闸只管一种形态**：`当前` 后面**紧跟**一个版本号。
实测全库这一形态**只有 1 处**——**所以本闸覆盖面很窄，这一点必须说在前面**，
免得下一个人以为「版本声明」整族都归它管（其实不归，见下）。

**覆盖不到什么，以及为什么（如实说明，本批为此专门查了全族）**：
手册里带版本号的括注约 **50 处**，绝大多数是**功能引入版本**
（`（v1.6.7 起解禁）`、`（v1.6.13 构建实测）`、`（v1.6.16）` 标在 `query-provider` 端点旁）
或**证据出处**（`（v1.6.14 实测）`），**它们与基线分家是正常的**，
`20-reference.md:182` 那个 `（v1.6.16）` 改成 v1.6.22 反而是错的。

真正棘手的是页首那一类**出处型**声明：
`cloud-agent.md` / `local-runtime.md` / `agent-memory-skills.md` 都写着
「**当前状态（v1.6.x 源码核查）**」。本批逐处读过，结论是**三处里只有两处该改**——
判据能不能覆盖它们，取决于「**这个括注罩着的那一句断言，有没有被某道闸在基线上每次构建重验**」，
而**这个事实不在文本里，在闸的输入里**（纪律 242：判据的依据必须能从被核对象自己算出来，
而这里算不出来）。**建一条只会误伤其中一处的判据，比不建更坏**（纪律 248）——
本批差点就那么干，详见 `AUDIT-RULES.md` 纪律 257 与批次 234 的行。

**所以本闸的判据只有一条形态，且刻意不扩张**：宁可只守一句「当前 = 基线」，
也不去猜别的括注罩着什么。**一个判据报出来的每一条，都必须是真的。**

**方向二之二（自检探针）**：拿一句人造的「当前 v0.0.1」喂给判据自己的正则，
确认它真的能匹配上——**判据读空、匹配器退化时必须 rc=2，不许安静地全绿**（纪律 101）。

退出码：0 相符；1 有「当前」指向了非基线版本；2 未能核对（读不到基线 / 发布面 / 探针不中）。
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import scope  # noqa: E402
from baseline import declared_baseline, BaselineError  # noqa: E402
#: **Batch 259 补上**：本闸从 `baseline` 取 `SRC`，
#: **而 19 道碰上游解析的闸里只有它一句都不说走了兜底**——
#: 实测 `BEEFTV_SRC` 指向非仓时它 rc=0、输出是一句干净的「核对通过」，
#: **而核的是用户没指定的另一份检出**。
#: **静默降级比直接失败更坏，因为它还报绿**（纪律 172）。
#: 措辞与判断都在 `baseline.announce_fallback()` 里，**本闸不用自己写一句**。
from baseline import announce_fallback  # noqa: E402

ROOT = os.path.dirname(HERE)

#: 「当前」后面**紧跟**（可隔空格）一个版本号。**「紧跟」是这个判据的全部**——
#: 手册里「在当前版本不存在」「当前客户端」这类不带版本号的写法有几十处，
#: 它们不指向基线（它们指的是「读者手上的那一个」），不该被管。
#: **同样刻意不匹配「当前 v1.6.7 起解禁」这种**——实测全库没有这种写法，
#: 而一旦有，「起」字后面的版本是**功能引入版本**而不是当前版本。
CURRENT_RE = re.compile(r"当前\s*v(\d+\.\d+\.\d+)(?!\s*起)")

_FENCE_RE = re.compile(r"^\s*(```|~~~)")


def strip_fenced(text):
    """把围栏代码块**挖空但保留行数**。

    **Batch 229 的教训**：第一版用 `re.sub` 整段删除围栏内容，
    结果**行号前移**、报错指的行是错的。
    保留行数的做法是逐行替换成空串——**判据报的行号必须能在源文件里对上**。
    """
    out, inside = [], False
    for line in text.split("\n"):
        if _FENCE_RE.match(line):
            inside = not inside
            out.append("")
        elif inside:
            out.append("")
        else:
            out.append(line)
    return out


def find_current_claims(path, rel):
    hits = []
    with open(path, encoding="utf-8") as fh:
        for idx, line in enumerate(strip_fenced(fh.read()), start=1):
            for m in CURRENT_RE.finditer(line):
                hits.append((idx, m.group(1), line.strip()[:90]))
    return [(idx, ver, snippet, rel) for idx, ver, snippet in hits]


def main():
    #: **Batch 259 新增，且必须是 `main()` 的第一句**——
    #: 放在任何 `[skip]` 分支之后，就等于「降级了但读者看不到」，
    #: **而那正是本闸要防的形态自己**（纪律 172）。
    announce_fallback()
    try:
        version, _commit = declared_baseline()
    except BaselineError as exc:
        print(f"[skip] {exc}，「当前版本」核对本轮未能进行")
        return 2
    if not re.match(r"^v\d+\.\d+\.\d+$", version):
        print(f"[skip] 取证基线版本 {version!r} 不是 v主.次.修订 形态，本轮未能核对")
        return 2
    baseline_ver = version[1:]

    try:
        # **`published_paths()` 而不是 `published_md()`**（scope.py 自己的 docstring 写了）：
        # 后者给的是**基名**集合，而 `README.md` 有两个（根首页与 `10-tasks/README.md`），
        # **基名集合把两个不同的页面合成了一个**。判定归属用基名没问题，
        # **要逐个读文件就必须用相对路径**。
        pages = scope.published_paths()
    except Exception as exc:                       # noqa: BLE001 —— 读不到事实源即 rc=2
        print(f"[skip] 读不到发布面（{exc}），本轮未能核对")
        return 2
    if not pages:
        print("[skip] 发布面 0 个 .md，判据读空 —— 不是「没有不一致」")
        return 2

    # ---- 方向二之二：自检探针。判据的正则必须真的能匹配，否则本闸恒真。
    probe = CURRENT_RE.search("反验探针：当前 v0.0.1 客户端里打不开")
    if not probe or probe.group(1) != "0.0.1":
        print("[skip] 自检探针没匹配上——**判据的正则已失效**，本轮未能核对")
        return 2
    # 反向探针：「当前版本不存在」这种**不带版本号**的写法必须**不**被匹配
    if CURRENT_RE.search("在当前版本不存在"):
        print("[skip] 反向探针被误匹配——**判据抓的形态比声称的宽**，本轮未能核对")
        return 2

    bad = []
    seen = 0
    for rel in pages:
        path = os.path.join(ROOT, rel)
        for idx, ver, snippet, rel in find_current_claims(path, rel):
            seen += 1
            if ver != baseline_ver:
                bad.append(f"{rel}:{idx} 写「当前 v{ver}」，而取证基线是 v{baseline_ver}：{snippet}")

    if bad:
        print(f"「当前版本」核对：{len(bad)}/{seen} 处「当前」没有指向取证基线")
        for b in bad:
            print("  " + b)
        print(f"→ 把「当前 v…」改成基线版本 v{baseline_ver}；"
              "**若这处的版本是功能引入版本或证据出处，就别写「当前」**——"
              "「当前」是指向基线的指针，它一动就意味着基线动过")
        return 1
    print(f"「当前版本」核对通过：{len(pages)} 个发布页里 {seen} 处「当前 X 版本」"
          f"全部指向取证基线 v{baseline_ver}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
