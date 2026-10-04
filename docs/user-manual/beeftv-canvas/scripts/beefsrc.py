#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""**「BeefTV 源码仓在哪」的单一来源**（Batch 197 新增）。

**这个模块是普查 13 道闸之后才决定存在的**——在此之前，同一个问题有 **4 种写法**：

| 写法 | 谁在用 | 判真条件 | 候选数 |
|---|---|---|---|
| A `SRC = os.environ.get("BEEFTV_SRC", <硬编码>)` | 6 道闸 + `baseline.py` | **无** | 1 |
| B `CANDIDATES` + `isdir(c/"backend")` | 5 道闸 | 顶层有 `backend/` | 2（1 道是 3） |
| C `CANDIDATES` + `isdir(c/".git")` | 2 道闸 | `.git` **是目录** | 2 |

**三处都是抄的**：机器专属的绝对路径 `/Users/yangjiefeng/Documents/glanderness/BeefTV`
**在全树被手写 14 处**。而它们**互不一致**——于是同一个 `BEEFTV_SRC`
在不同闸里会解析成**不同的仓**（Batch 190 的那条教训：同一份事实被手写两遍时，
核对一致性不如消灭其中一份）。

**实测出来的三个真缺陷**（不是设想的）：

1. **`baseline.py` 的 `SRC` 没有任何校验**。`BEEFTV_SRC` 指向不存在的路径时，
   这个路径被原样塞进 `git -C <path> rev-parse`，于是 12 道闸的 rc=2 全都说
   「手册声明的取证基线提交 bcc3b05 **在 <你设的那个路径> 里不存在**」——
   **而真正的原因多半是「你设的那个路径不是 BeefTV 仓」**。
   Batch 196 实测：这句话把锅甩给了一个用户**已经设对了**的变量。
2. **`.git` 目录式判真在 git worktree 上必然失败**。实测：
   worktree 里 `.git` 是一个**文件**（`.git/worktrees/<名>` 的指针），不是目录，
   于是 `isdir(c/".git")` 判假 → `BEEFTV_SRC` **被静默忽略**、改用兜底那份——
   **而闸一声不吭**。本项目自己就在用 worktree，所以这不是假想场景。
3. **「顶层有 `backend/` 目录」把两个问题耦在了一起**：
   它问的其实是「这个仓现在长这样吗」，而不是「这是一个 git 仓吗」。
   上游哪天把 `backend/` 改名，5 道闸会一起失效，而原因与它们要做的事毫无关系。

**所以判真改用 `git -C <路径> rev-parse --git-dir`**：它对普通检出、worktree、
子模块一视同仁，**而且不依赖上游的内部目录名**。

**兜底不再静默**：`resolve_src()` 在**没有用 `BEEFTV_SRC` 指定的路径**时会返回
`used_fallback=True`，调用方可以把它写进输出——
**「静默改用另一份检出并报通过」和「明确说用了兜底」的区别，就是本手册整套纪律在说的事。**

零外部依赖，与 `baseline` / `batchread` / `scope` / `pngstat` 一致。
"""

import os
import re
import subprocess

#: 兜底用的**机器专属**绝对路径。**它是候选之一而不是唯一来源**——
#: 换机器的人设 `BEEFTV_SRC` 即可，判据不依赖它存在。
FALLBACK_ABS = "/Users/yangjiefeng/Documents/glanderness/BeefTV"

#: 相对兄弟路径：`liblib-tv` 与 `glanderness` 同在 `Documents` 下时的可移植写法。
#: **比 `FALLBACK_ABS` 好在它不写死用户名与上级目录名。**
_SIBLING = ("..", "..", "..", "..", "glanderness", "BeefTV")


def candidates():
    """按优先级列出候选路径。**顺序即优先级**，第一个判真的就是它。

    ① `BEEFTV_SRC`（显式指定，永远第一）
    ② 相对兄弟路径（可移植，不写死用户名）
    ③ 绝对兜底路径（换机器时可能不存在，无妨）
    """
    here = os.path.dirname(os.path.abspath(__file__))
    out = [os.environ.get("BEEFTV_SRC", "").strip()]
    out.append(os.path.join(here, *_SIBLING))
    out.append(FALLBACK_ABS)
    return [c for c in out if c]


def is_repo(path):
    """**这是不是一个 git 检出**——普通检出、worktree、裸库都算。

    **刻意不问「顶层有没有 `backend/`」**（见文件头缺陷 3）：
    那是上游的内部布局，闸该问的是「能不能当仓用」。
    """
    if not path or not os.path.isdir(path):
        return False
    r = subprocess.run(["git", "-C", path, "rev-parse", "--git-dir"],
                       capture_output=True, text=True)
    return r.returncode == 0


def resolve_src():
    """返回 `(路径, 是否走了兜底)`；一个候选都不成立时返回 `(None, False)`。

    **第二个返回值是本模块存在的理由之一**：`True` 表示**没有采用
    `BEEFTV_SRC` 指定的那个路径**。调用方应把它写进输出，
    否则「核的是用户指定的那份」与「核的是兜底那份」在结果里长得一模一样。
    """
    env = os.environ.get("BEEFTV_SRC", "").strip()
    for c in candidates():
        if is_repo(c):
            return os.path.abspath(c), bool(env) and os.path.abspath(c) != os.path.abspath(env)
    return None, False


def explain():
    """把候选表连同判真结果一并列出——供「为什么没找到」时当诊断用。"""
    lines = []
    for c in candidates():
        lines.append("  %s  %s" % ("✓" if is_repo(c) else "✗", c))
    return "\n".join(lines)


# ── 「从前端 Go 源码里抽路由」的单一来源（Batch 263 收敛）─────────────────
#: **闸 37 登记的跨文件重复之一**（`25eecbe17b93`）：
#: `verify-endpoints.py` 与 `verify-exclusions.py` 各写了一份**逐字相同**的
#: `ROUTE_RE`，**而两处连抽取循环都逐字相同**
#: （`read_many` → `decode` → `finditer` → `group(1)`）——
#: **两份在问同一件事，不是在问两件事**（闸 37 只核「字面量是否一模一样」，
#: **「是不是在问同一件事」得自己判断**——那一半它不管）。
#: **而它们「怎么读」是不同的**（一个自己 `git ls-tree`、一个走本地的 `git_ls`），
#: **所以收敛的切面是「怎么抽」，不是「怎么读」**——
#: **把读法也一起收进来会强迫两个闸共用同一种读法，那是一次语义变更，不是收敛。**
ROUTE_RE = re.compile(r'(?:GET|POST|PUT|DELETE|PATCH)\("([^"]+)"')


def routes_in(blobs):
    """从一批**已读回**的 Go 源码 blob（`{路径: bytes}`）里抽出路由路径的集合。

    **入参刻意是「已经读好的 blob」而不是「仓与 ref」**：
    **读法两个闸不一样，而抽法一模一样**——
    **收敛一个共同的东西，不顺手统一它们不一样的地方**（纪律 250）。

    **逐字保持原样**：`decode("utf-8", "replace")` 而不抛解码错误，
    **因为「切出来的正好是 size 字节」这件事只在 bytes 上成立**，
    所以显式解码、不走 `text=True`（走 text 就得编解码往返，而往返可能改变内容）。
    """
    routes = set()
    for body in blobs.values():
        for m in ROUTE_RE.finditer(body.decode("utf-8", "replace")):
            routes.add(m.group(1))
    return routes
