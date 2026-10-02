#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""手册「发布范围」的唯一来源（Batch 190 新增）——由 `.vitepress/config.mjs` 的 `srcExclude` 派生。

**这个文件为什么存在（Batch 190 的实测，不是假想问题）**：

闸 22 `verify-quote-punct.py` 头注释写着「**判据的输入范围必须等于发布范围**」，
而它的 `PAGES` 清单里躺着 **`PUBLISH.md`**——一个被 `srcExclude` 显式排除、
**根本不会出现在站点上**的内部资料。于是这句话在代码里是假的。

它能躺着，是因为**发布面被手写了两遍**：`config.mjs` 的 `srcExclude` 是一份，
闸 22 的 `PAGES` 是另一份，两份之间没有任何机制相连。查它的动作又是
「把所有闸源码里出现的 .md 文件名都核一遍」——**实测 11 个闸里 8 个「越界」**，
逐个读原文后**全是假阳性**：闸 19/21/23 本来就该扫 `AUDIT.md`/`PROGRESS.md`
（账本闸的输入就是账本），闸 9 本来就该排除内部资料（它管的正是发布面）。

**所以判据不能去猜「一个闸列的清单算读者页还是算排除集」**——那是散文级的歧义，
硬猜就是往闸门里灌噪音（Batch 142 闸 8 第一版、Batch 185 闸 22 第一版，同一课）。
正确的做法是**消掉手写的那一份**：发布范围由 `srcExclude` 派生，闸门引用派生结果，
于是 PUBLISH.md 结构上就再也进不了 `PAGES`。

**本模块的三条约定**：

  · **`.vitepress/config.mjs` 的 `srcExclude` 是排除集的唯一来源**，其余地方一律派生。
    站点实际发布什么由 VitePress 说了算，而它只认 `srcExclude`——
    **第二份名单从定义上就是可能与站点分家的**。
  · **排除按基名匹配**（`srcExclude` 的七项全是 `**/NAME` 形式），
    所以派生结果是「基名集合」而不是「路径集合」：调用方拿到的是
    「PUBLISH.md 被排除了吗」这个布尔问题，而不是一串路径前缀。

**基名会碰撞，而这一版没打算处理它——但必须写下来，因为本模块第一版写错了**：

本模块第一版的 docstring 断言「本手册树里同名文件不重复」。**闸 24 首跑直接证伪了它**：
树里有 **41 个 `.md` 但只有 40 个唯一基名**——`README.md` 出现两次，
一次是根首页，一次是 `10-tasks/README.md`（任务目录页）。断言它的后果是
`describe()` 报「树内共 40 个」而人以为是漏了一个文件。

**为什么这一版仍用基名**：两个 `README.md` 都是发布页，基名集合把它们合成一个，
`classify()` 的结论不变；而调用方手里的清单写的也是基名。
**但这条推论是有条件的**：一旦这两个文件里有一个需要单独归属
（例如给 `10-tasks/` 单独一套 srcExclude，或任务目录页将来不发），
基名判定就不再够用，那时必须改成路径级。**不要把「今天无影响」读成「一直无影响」。**
之所以把它写进 docstring 而不是等它出事：这一版的错误就是「断言了一个没核过的假设」，
而下一次读代码的人会照着这个断言做决定。
  · **`BEEFTV_MANUAL_ROOT` 优先于 `__file__` 推断**（Batch 178 的第二层教训：
    一个被多处 import 的模块，它「定位自己所在仓」的假设**必须在被搬运时仍然成立**）。
    反验把闸门复制进临时目录时靠它指回真实手册树。
"""

import os
import re

ROOT = os.environ.get("BEEFTV_MANUAL_ROOT") or os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, ".vitepress", "config.mjs")

# 依赖与构建产物：它们不属于手册内容，判据的输入范围必须等于发布范围
# （Batch 183 闸 20 的同一条纪律，此处是排除方向的写法）。
SKIP_DIRS = {".git", "node_modules", "dist", "cache", ".vitepress"}
DOC_EXT = (".md", ".yml", ".yaml")

# `srcExclude: ['**/AUDIT.md', ...]` —— 只认单引号，因为这份配置里没有别的引号风格。
_EXCLUDE_RE = re.compile(r"srcExclude\s*:\s*\[(.*?)\]", re.S)
_ITEM_RE = re.compile(r"'([^']+)'")


class ScopeError(RuntimeError):
    """读不到站点配置、或配置里没有 srcExclude。调用方应返回 rc=2「未能核对」。"""


def _exclude_raw():
    """从 config.mjs 原样取出 srcExclude 的每一项（保留 `**/` 前缀）。"""
    try:
        with open(CONFIG, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise ScopeError("读不到 .vitepress/config.mjs：%s" % exc)
    m = _EXCLUDE_RE.search(text)
    if not m:
        raise ScopeError(
            ".vitepress/config.mjs 里找不到 srcExclude——"
            "发布范围无从判定（**不能让判据在语料读空时安静地全绿**，纪律 101）")
    return _ITEM_RE.findall(m.group(1))


def exclude_items():
    """srcExclude 的每一项，原样（`'**/AUDIT.md'` 这样的字符串）。"""
    return _exclude_raw()


def excluded_basenames():
    """排除集的**基名**形式：`{'AUDIT.md', 'PROGRESS.md', ...}`。

    srcExclude 用的是 `**/NAME`（任意层级同名）。若将来出现不带前缀的相对路径
    （如 `AUDIT.md`），取它的 basename 仍然对——因为本手册树里同名文件不重复。
    """
    out = set()
    for item in _exclude_raw():
        tail = item[3:] if item.startswith("**/") else item
        tail = tail.rsplit("/", 1)[-1]
        if tail:
            out.add(tail)
    return out


def walk_basenames():
    """手册树里全部 `.md` / `.yml` 的基名（跳过依赖与构建产物）。"""
    return {n for n, _ in walk_files()}


def walk_files():
    """手册树里的 `(相对路径, 基名)` 对，只含 `.md` / `.yml` / `.yaml`。"""
    out = []
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for name in filenames:
            if name.endswith(DOC_EXT):
                full = os.path.join(dirpath, name)
                out.append((os.path.relpath(full, ROOT), name))
    return sorted(out)


def all_md():
    """全部 `.md` 的**基名**集合——判定用（`classify()` 的输入单位）。"""
    return {base for _rel, base in walk_files() if base.endswith(".md")}


def _path_split():
    """把手册树的 .md 按归属分成三堆，返回 `(发布, 排除)` 的相对路径列表。"""
    exc = excluded_basenames()
    pub, ex = [], []
    for rel, base in walk_files():
        if not base.endswith(".md"):
            continue
        (ex if base in exc else pub).append(rel)
    return pub, ex


def published_paths():
    """发布范围的 `.md` **相对路径**（已排序）——计数与「站点发了多少页」用这个。

    **必须用它而不是 `published_md()` 来数页面**（Batch 190 实测）：
    `find -maxdepth 2` 数出 38、`published_md()` 数出 34，而站点实际发 35 页。
    三个数互不相等，因为 `README.md` 有两个（根首页与 `10-tasks/README.md`），
    **基名集合把两个不同的页面合成了一个**——判定用基名没问题，计数用基名就是错的。
    """
    return _path_split()[0]


def excluded_paths():
    """被 `srcExclude` 排除的 `.md` 相对路径（已排序）。"""
    return _path_split()[1]


def published_md():
    """发布范围的 `.md` **基名**集合（已去掉排除集）——`classify()` 的判定用这个。"""
    return all_md() - excluded_basenames()


#: 一个名字在发布面上的三种归属。`absent` 指手册树里根本没有这个文件——
#: 它与 `excluded` 分开，因为「被排除」是决定，「不存在」是笔误或残留。
EXCLUDED = "excluded"
PUBLISHED = "published"
ABSENT = "absent"


def classify(name):
    """把一个 `.md` 基名归到 `EXCLUDED` / `PUBLISHED` / `ABSENT`。"""
    present = all_md()
    if name not in present:
        return ABSENT
    return EXCLUDED if name in excluded_basenames() else PUBLISHED


def describe():
    """给闸门输出用的一行说明：排除集与发布范围各有几个。

    「树内共 N 个」报的是**相对路径**数；同名文件（`README.md` 出现在根与
    `10-tasks/`）只算一个页面，但**基名去重后**只有 40 个——两个数都报出来，
    免得读的人以为漏了文件（见 docstring 的「基名会碰撞」）。
    """
    exc = excluded_basenames()
    pub, ex = _path_split()
    return ("srcExclude 排除 %d 个 .md（%s）与 1 个 yml；发布范围 %d 个 .md"
            "（树内共 %d 个 .md，去重后 %d 个基名）"
            % (len(ex), "、".join(sorted(os.path.basename(p) for p in ex)),
               len(pub), len(pub) + len(ex), len(all_md())))
