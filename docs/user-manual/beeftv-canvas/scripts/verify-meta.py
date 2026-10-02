#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""「手册元数据自洽」双向核对闸：手册说自己有多少东西，写的是否还对。

背景（Batch 145）：用三分类框架回头扫「尚未/未开放」措辞时，撞见一批
**从来没人扫过的过期数字**——它们不在 Batch 139–144 任何一道闸的覆盖范围内：

    README.md            「25 篇任务指南 / 账本 32 项」→ 实际 29 篇 / 35 项
    10-tasks/README.md   「共 25 篇」                  → 实际 29 篇
    FINAL-REPORT.md      「33 页 HTML」                → 实际 35 个内容页
    AUDIT-RULES.md       「现有六道闸」且表里没有第七道 → Batch 143 自己加的

**为什么前七道闸都拦不住**：它们查的是「**内容断言**」——
「端点是不是这样注册的」「这个功能是不是真的没入口」。
而这些是「**关于手册自身的元数据**」，是第四种东西：
**它的真值不来自上游源码，而来自本仓库自己的目录和 yml。**

Batch 143 立过一条「六道闸全绿不等于发布物正确」，
本批撞上它的加强版：**七道闸全绿不等于账本自洽**。

**闸门要成对**（Batch 143 第 24 条）：本闸四个方向，
  方向一（登记项是否仍成立）：逐条把手册写的数字与**现场重数的结果**比对；
  方向二（登记表是否完整）：反向扫所有**参与发布的**页面里
    「N 篇 / N 项 / N 张 / N 个内容页」形态的元数据表述，
    命中集合必须与登记集合**完全一致**。
  方向三（Batch 147）：闸门清单表自洽——标题声明数、表行数、`build-site.sh`
    实际调用的脚本三者一致。**这道闸盯着闸门体系自己**。
  方向四（Batch 153）：任务索引 ⇄ 页面标题双向对账——每个任务页都必须在索引里，
    且索引的链接文字与页面 h1 一致（或等于 `h1（……）` 这一有意形态）。
  方向四之二（Batch 154）：任务页还必须在 **vitepress 侧栏**里——侧栏是站点主导航，
    比 README 索引更关键。该方向**只查存在性、不查文字**，因为侧栏用短标题是有意设计。

**方向二为什么只扫「参与发布的」页面**——这是本闸最容易写坏的地方，
Batch 139/141/142/143 已连续四次栽在「判据过严」（详见 AUDIT-RULES 第 23 条）：
  台账文件（`AUDIT.md` / `AUDIT-RULES.md` / `PROGRESS.md`）里**必然**含有历史数字，
  那是**记录「曾经错了什么」**的正当用途。若全库扫，`AUDIT-RULES.md:334`
  那句「README 写着 25 篇」就会被报成「手册说 25 篇而实际 29 篇」——
  **判据把历史引述当成了当前声明。**
  这三份文件本就在 vitepress `srcExclude` 里，不参与发布，
  所以按「是否参与发布」划线，**既收紧了范围又天然豁免了引述**。

不检查什么（明确声明，避免后来者误以为覆盖面更大）：
  · 不检查**业务数字**——「审美批改 4 个检查方向」「灵感墙 22 条创意」
    「快捷键 24 条」这类是**上游产品的事实**，归 `verify-endpoints` 等既有闸门管，
    或需人工核。本闸只管「**关于本手册自己**」的计数。
  · 不检查截图**内容**是否仍对得上界面——那是 `verify-screenshots.py` 的职责。
    本闸只数「有几张」。
  · 不检查 `dist/` 产物——构建产物随构建变化，不该作为真值来源。
    真值一律取自**源目录与 yml**。
  · **不判断括号里的提示是否写得恰当**（方向四）——只认 `h1（……）` 这个形态，
    不看括号里是什么。**这是刻意的**：Batch 150 已经证明「意图无法判定」的判据
    不能建（中文「」有三种用途），而这里能做到零误报，是因为**只判形态不判语义**。
  · **不判断侧栏文字与页面 h1 是否一致**（方向四之二）——侧栏本来就用短标题
    （「上传本地素材」vs「上传本地图片、视频、音频」），这是设计，不是漂移。
  · **不判断页面 h1 是否漏掉了功能词**（方向四）——账本 title 带括号补充、页面 h1
    取短标题是**有意分工**（Batch 152 量过：35 条里 14 条同模式、12 条完全一致）。
    本闸只抓「h1 与 title 完全无关」这种明显破坏，不假装能抓细粒度漏词。
"""

import ast
import glob
import os
import re
import sys

try:
    import yaml
except ImportError:  # pragma: no cover
    print("需要 pyyaml", file=sys.stderr)
    sys.exit(2)

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# vitepress 的 srcExclude：这些文件不参与发布，天然不是「读者能看到的元数据」。
# 与 .vitepress/config.mjs 保持一致——**改了那边就要改这里**，这是有意的耦合。
SRC_EXCLUDE_BASENAMES = {
    "AUDIT.md", "AUDIT-RULES.md", "PROGRESS.md",
    "SOURCE_OBSERVATIONS.md", "PUBLISH.md", "FINAL-REPORT.md",
}

# FINAL-REPORT.md 虽被 srcExclude，但它是交付说明文档、明确写了发布物计数，
# 因此**显式纳入**登记与扫描范围（见 REGISTRY 里的条目）。
EXTRA_SCAN_FILES = {"FINAL-REPORT.md"}


# ── 真值：全部从本仓库现场重数 ──────────────────────────────────────

def count_task_pages(root):
    """任务指南页数 = 10-tasks/ 下除索引页（README.md）以外的 md 数。"""
    files = [p for p in glob.glob(os.path.join(root, "10-tasks", "*.md"))
             if os.path.basename(p) != "README.md"]
    return len(files)


def count_content_pages(root):
    """内容页数 = 参与发布的 md 数（顶层 + 10-tasks/）。

    与 dist 的 html 数差 1（404 页），那是 vitepress 自动生成的，
    **不是一篇内容**，所以不进这个计数——手册里说的是「内容页」。
    """
    top = [p for p in glob.glob(os.path.join(root, "*.md"))
           if os.path.basename(p) not in SRC_EXCLUDE_BASENAMES]
    tasks = glob.glob(os.path.join(root, "10-tasks", "*.md"))
    return len(top) + len(tasks)


def _inventory(root):
    with open(os.path.join(root, "task-inventory.yml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    items = data if isinstance(data, list) else data.get("tasks", data)
    if isinstance(items, dict):
        items = list(items.values())
    return items


def count_inventory_total(root):
    return len(_inventory(root))


def count_inventory_status(root, status):
    return sum(1 for i in _inventory(root) if str(i.get("status", "")) == status)


def _manifest(root):
    with open(os.path.join(root, "screenshots", "manifest.yml"), encoding="utf-8") as f:
        data = yaml.safe_load(f)
    items = data if isinstance(data, list) else data.get("screenshots", data)
    if isinstance(items, dict):
        items = list(items.values())
    return items


def count_screenshots(root):
    """截图数以 manifest.yml 为准，并**同时核对磁盘上的 png 数**。

    两者不一致本身就是一种损坏（多一张没登记 / 登记了却不存在），
    但那属于 `verify-screenshots.py` 的职责；本闸只要求二者一致时才认这个数。
    """
    return len(_manifest(root))


# ── 方向三：闸门清单自洽（本闸盯着闸门清单表自己） ──────────────────
#
# **为什么需要这个方向**：Batch 145 抓到 `AUDIT-RULES.md` 的「现有 N 道闸」清单表
# **漏登记了 Batch 143 自己加的第七道**。Batch 146 加第八道时——**又漏了一次**
# （改了脚本、改了纪律条目，唯独没回头改那张表）。
#
# **两次同向的遗漏，足以说明靠人记不住**。而这件事本可以机器查：
# 清单表里列的脚本、`build-site.sh` 里实际调用的脚本、以及标题里的数量，
# **三个都是可数的**。这是第八道闸最该盯的东西——**它盯的是闸门体系自己**。
#
# 口径：
#   · 只统计 `scripts/verify-*.py`：selftest-*.sh 是反向验证，不参与构建期检查。
#   · **Batch 168：偏移从 +1 改成 0**。「站内死链」原本内联在 `build-site.sh` 的
#     heredoc 里、没有独立脚本，才需要那个 +1；它已被抽成 `verify-deadlinks.py`，
#     于是**表行数 = 实际调用的闸数**。
#     这条偏移当初写死在这里是对的（第一版忘了 +1 而自报错），
#     **但它把「内联」当成了永久前提**——前提变了，偏移就得跟着变，
#     否则方向三会报「清单表 10 行 ≠ 10 个闸 + 内联 1 道」这种自相矛盾的话。

INLINE_GATE_SLACK = 0


def gate_inventory(root):
    """返回 (标题声明数, 清单表行数, 表里列出的脚本名集合, build-site 实际调用集合)。"""
    rules_path = os.path.join(root, "AUDIT-RULES.md")
    rules = open(rules_path, encoding="utf-8").read()

    m = re.search(r"###\s*现有\s*([一二三四五六七八九十]+|\d+)\s*道闸", rules)
    declared = _cn_int(m.group(1)) if m else None

    # 清单表：标题之后的第一张表
    #
    # **表头怎么跳不能用关键词**（Batch 157 当场踩到）：第一版写的是
    # `if ... and "脚本" not in line` —— 结果本批我给「手册元数据」那行补了
    # 「**闸门脚本**里 git grep 正则的引擎兼容性」这句话，**说明文字里的「脚本」
    # 二字让这行被当成表头跳过**，清单表凭空少一行、闸门数对不上，
    # 报出来的是「标题写 9 道、清单表却有 8 行」——**离真实原因十万八千里**。
    # **判据必须落在结构上**：第一条 `|` 行是表头，`|---` 是分隔行，其余都是数据行。
    rows, listed, seen_pipe = 0, set(), False
    if m:
        body = rules[m.end():]
        for line in body.split("\n"):
            if line.startswith("## ") or line.startswith("### "):
                break
            if line.startswith("|"):
                if not seen_pipe:
                    seen_pipe = True
                    continue          # 表头：第一条 `|` 行
                if re.match(r"\|\s*:?-{2,}", line):
                    continue          # 分隔行
                rows += 1
                for s in re.findall(r"scripts/(verify-[a-z-]+)\.py", line):
                    listed.add(s)
                continue
            if rows and line.strip() == "":
                break

    build = open(os.path.join(root, "build-site.sh"), encoding="utf-8").read()
    # **两种调用形态都要认**（Batch 160 当场踩到）：原先只认
    # `python3 scripts/verify-x.py`，而 Batch 160 把 6 个闸改走 `run_gate` 包装
    # （为了区分退出码 2「未能核对」），于是 `invoked` 暴跌到 2 个、
    # 方向三立刻报「清单表 9 行 ≠ 实际调用 2 个闸」。
    # **判据锚定「build-site.sh 确实调用了哪些闸」这个事实，不是某一种写法。**
    invoked = set(re.findall(r"python3\s+scripts/(verify-[a-z-]+)\.py", build))
    invoked |= set(re.findall(r"^\s*run_gate\s+(verify-[a-z-]+)\.py", build, re.M))
    return declared, rows, listed, invoked


# ── 方向四：任务索引与页面标题的双向对账 ────────────────────────────
#
# **为什么需要**：Batch 152 顺手做的全量对账里发现
# `asset-library.md` / `create-workspace.md` / `model-channels.md`
# **三个页面根本没进 `10-tasks/README.md` 索引**——而它们正是 Batch 139/140/141
# 连续新建的三页。**建了页面忘了加索引**，其中 `create-workspace.md`（`/create`）
# 是产品**第二大门户**，读者从任务索引**根本找不到那个入口**。
#
# **这与 Batch 147「加了闸忘了改清单表」是同一类**：新增了东西，忘了更新汇总处。
# 三个都在同一批序列里，说明**建页面的流程漏了一步**——所以要交给机器盯。
#
# 判据（**全部是形态判定，不含任何意图判断**——这是能建成的前提）：
#   (a) **反向**：每个任务页都出现在索引里（漏登记 = 报）；
#   (b) **正向**：索引的链接文字与目标页 h1 一致，或等于 `h1（……）` 这一形态。
#       `h1（……）` 是**有意设计**——索引在标题后补一句提示
#       （如「只读画布与画布副本（无入口，副本不上传）」「AI 审美批改（当前无入口）」），
#       让读者在索引上就知道这页有坑。**这不是漂移**，所以判据显式承认这个形态。
#       少了 (b)，那两条会被误报成「索引与标题不一致」。

INDEX_FILE = "10-tasks/README.md"
H1_PAREN = r"^%s（.+）$"


def index_check(root):
    """返回 (漏登记列表, 形态不符列表, 统计行)。"""
    import os as _os
    index_path = _os.path.join(root, INDEX_FILE)
    text = open(index_path, encoding="utf-8").read()
    h1 = {}
    for path in glob.glob(_os.path.join(root, "10-tasks", "*.md")):
        base = _os.path.basename(path)
        if base == "README.md":
            continue
        first = open(path, encoding="utf-8").readline().strip()
        if first.startswith("# "):
            h1[base] = first[2:].strip()

    pairs = re.findall(r"\[([^\]]+)\]\(([a-z0-9-]+\.md)\)", text)
    linked = {t for _l, t in pairs}
    missing = sorted(f for f in h1 if f not in linked)

    mismatched = []
    for label, target in pairs:
        if target not in h1:
            continue
        label = label.strip()
        want = h1[target]
        if label == want:
            continue
        if re.match(H1_PAREN % re.escape(want), label):
            continue          # 有意的「标题（提示）」形态
        mismatched.append((target, label, want))
    return missing, mismatched, len(pairs), len(h1)


def sidebar_check(root):
    """任务页是否都在 vitepress 侧栏里。**只查存在性，不查文字**。

    侧栏 text 用的是**短标题**（「上传本地素材」vs 页面 h1「上传本地图片、视频、音频」），
    **这是设计**（Batch 152 量过差异模式），所以拿文字去比对会误报一片。
    侧栏是站点主导航——**不在侧栏的页面，读者在站点里几乎发现不了**，
    这比漏进 README 索引更严重（索引至少还能从站点首页点进去）。

    Batch 154 的实测：4 个页面不在侧栏，其中 `readonly-canvas.md` 从 Batch 135
    建页起就**一直**不在侧栏，而 `asset-library` / `create-workspace` / `model-channels`
    是 Batch 139/140/141 连续三批新建的。**侧栏比 README 索引漏得更久、也更全。**
    """
    cfg_path = os.path.join(root, ".vitepress", "config.mjs")
    cfg = open(cfg_path, encoding="utf-8").read()
    linked = set(re.findall(r"link:\s*['\"]([^'\"]+)['\"]", cfg))
    pages = []
    for path in glob.glob(os.path.join(root, "10-tasks", "*.md")):
        base = os.path.basename(path)
        if base == "README.md":
            continue
        first = open(path, encoding="utf-8").readline().strip()
        if first.startswith("# "):
            pages.append(base)
    missing = sorted(f for f in pages if "/10-tasks/" + f[:-3] not in linked)
    return missing, len(pages)



def _cn_int(s):
    """中文数字 → int。

    ⚠️ Batch 168：原实现是 `digits.get(s)`，**只认单个汉字**——
    于是闸门数到十一那天，标题「现有十一道闸」解析成 **None**，
    方向三报「找不到「现有 N 道闸」标题」。
    **判据太窄的老问题，而这次的窄是「里程碑可预见」造成的**：
    十一不是意外，它只是**第一次**出现。

    现在支持 十 / X十 / 十X / X十Y（如 二十一）。
    """
    if s.isdigit():
        return int(s)
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9}
    if s == "十":
        return 10
    if "十" in s:
        head, _, tail = s.partition("十")
        tens = digits.get(head, 1) if head else 1
        ones = digits.get(tail, 0) if tail else 0
        if head and head not in digits:
            return None
        if tail and tail not in digits:
            return None
        return tens * 10 + ones
    return digits.get(s)


def screenshots_match_disk(root):
    """manifest 的 `file` 字段是**相对仓库根**的路径（如 `screenshots/01-home.png`）。

    第一版把它和 `os.path.basename(png)` 比，于是 65 vs 65 全报「不一致」——
    **路径基准不同而已，数量完全对得上**。这是本项目连续第六次「判据先坏」
    （139 的 `\\b`、141 的 `\\s*`、142 的竖线奇偶、143 的等宽、145 的粗体、
    以及本条），也是第 23 条纪律的又一次应验：**症状长得像「数据坏了」，
    真因常常是判据比错了基准**。
    """
    listed = {os.path.normpath(str(i.get("file", ""))) for i in _manifest(root)}
    on_disk = {
        os.path.normpath(os.path.relpath(p, root))
        for p in glob.glob(os.path.join(root, "screenshots", "*.png"))
    }
    return listed == on_disk


COUNTERS = {
    "task_pages": count_task_pages,
    "content_pages": count_content_pages,
    "inventory_total": count_inventory_total,
    "verified": lambda r: count_inventory_status(r, "verified"),
    "excluded": lambda r: count_inventory_status(r, "excluded"),
    "screenshots": count_screenshots,
}

COUNTER_LABEL = {
    "task_pages": "任务指南页数",
    "content_pages": "内容页数",
    "inventory_total": "任务账本总项数",
    "verified": "已走查验证项数",
    "excluded": "无法验证项数",
    "screenshots": "截图数",
}


# ── 方向五：闸门脚本里 git grep 正则的引擎兼容性 ──────────────────────
# **为什么需要这个方向**：Batch 157 用例 29 判失败，顺藤摸下去发现是**一类
# 系统性缺陷**，不是孤例：
#
#   `git grep -E` 走的是 POSIX ERE（macOS 上由 git 自己的 regcomp 实现），
#   **它不支持 `\s` / `\d` / `\w` / `\b`——这些会被当成字面字母 s/d/w/b**；
#   而且方括号里的 `\n` 是「反斜杠 + 字母 n」，**排除的是字母 n，不是换行**。
#
# 后果是**最坏的那种失效**：正则永远匹配不上 → 断言永远「通过」→ 闸门一直绿，
# **而实际上它什么都照不到**。本次在 verify-unreachable.py 里一次查出 4 处，
# 其中最严重的一处（`[^"`\n]` 排除字母 n）导致 `"/canvas?readonly=1"` 这种
# 最自然的写法永远抓不到生产者——**那条断言已经这样「通过」了很多个批次**。
#
# **这类缺陷不可能靠 review 发现**（正则看上去完全正常），
# 只能靠机器盯。本方向就是那个机器。
def _strip_comment(line):
    """去掉行尾注释，但不动引号里的 `#`。

    **必须去注释**：本文件解释「`\\s` 在 git grep 里是字面字母 s」的那些注释
    本身就在 git grep 调用的几行之内——不去掉就会**把说明文字当成违规代码**，
    方向五一上线就自我误伤。
    """
    out = []
    quote = None
    i = 0
    while i < len(line):
        ch = line[i]
        if quote:
            out.append(ch)
            if ch == "\\" and i + 1 < len(line):
                out.append(line[i + 1])
                i += 2
                continue
            if ch == quote:
                quote = None
        else:
            if ch in "\"'":
                quote = ch
                out.append(ch)
            elif ch == "#":
                break
            else:
                out.append(ch)
        i += 1
    return "".join(out)


def regex_engine_check(root):
    """扫描闸门脚本里传给 `git grep -E` 的模式，返回不合规项。

    只扫 `git grep` 的模式参数，**不扫 Python `re`**——Python 的 re 支持 \\s，
    那里用 \\s 是对的，混在一起判会误报几十处。

    **窗口取法踩过一次坑，记在这里别再改错**：第一版只取「调用行 + 含 REF 的行」，
    而模式通常**单独成行**夹在两者中间——于是被整段跳过，方向五成了永远通过的闸。
    当初的负向测试之所以「通过」，是因为**注入脚本恰好把模式写在了调用行内**，
    **形状与真实代码不同**（Batch 154「注入点必须落在判据真的管得到的形态上」）。
    现在改为：从调用行往后累积，**直到遇到含 REF 或 `--` 的行为止**。
    """
    bad = []
    unsupported = [r"\s", r"\d", r"\w", r"\b"]
    # 「这一行是模式参数」的形态：字符串字面量（可带 r/f 前缀）开头的续行。
    # **必须只认这些**：手工维护一个 ±N 行窗口会把**附近的 Python re** 一并扫进来——
    #   `re.match(rf"...:(\d+):...")` 是解析 git grep **输出**的正则，用 `\d` 完全正确，
    #   第一版就因为它报了两处假违规。**窗口越宽，误报越多。**
    lit_prefix = ('r"', "r'", 'rf"', "rf'", 'f"', "f'", '"', "'")
    scripts = sorted(p for p in os.listdir(os.path.join(root, "scripts"))
                     if p.startswith("verify-") and p.endswith(".py"))
    for name in scripts:
        path = os.path.join(root, "scripts", name)
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()
        for i, line in enumerate(lines):
            # 必须是**真的调用点**：`["git", "grep", ..., "-E", ...]` 这个列表字面量。
            # 第一版只判「行里有 grep 和 -E」，结果把 `_git_grep_run` **文档字符串里**
            # 那句「`git grep -E` 的模式一旦不合法（`{0,300}` …）」当成了代码——
            # **说明文字被当成违规代码**，方向五一上线就自我误伤。
            # 加上「必须出现带引号的 `"git"`」即可把散文里的反引号排除掉。
            if '"git"' not in line and "'git'" not in line:
                continue
            if '"grep"' not in line and "'grep'" not in line:
                continue
            if '"-E"' not in line and "'-E'" not in line:
                continue
            cands = [_strip_comment(line)]
            for j in range(i + 1, min(i + 8, len(lines))):
                if "REF" in lines[j] or '"--"' in lines[j]:
                    break
                if lines[j].strip().startswith(lit_prefix):
                    cands.append(_strip_comment(lines[j]))
            blob = "".join(cands)
            for m in re.finditer(r"\[\^([^\]]*)\]", blob):
                if r"\n" in m.group(1):
                    bad.append((name, m.group(0), "[^...\\n]"))
            for esc in unsupported:
                if esc in blob:
                    bad.append((name, esc, esc))
            # ── 下面三类是 Batch 157 用例 29 顺藤摸出来的「整条模式被 git 拒绝」型故障 ──
            # 它们比转义类更隐蔽：**git 直接 fatal、stdout 为空**，
            # 而空输出与「零命中」在判据里等价 → 断言恒真、闸门永远绿。
            # 实测确认的三条：
            #   · `{0,N}` 且 N > 255        → `maximum repetition exceeds 255`
            #   · `{0,n}?` 惰性量词（PCRE）  → `repetition-operator operand invalid`
            #   · `\xNN` 十六进制转义         → 不报错，但匹配 0 行（当成字面 xNN）
            for m in re.finditer(r"\{\d+,\s*(\d+)\}", blob):
                if int(m.group(1)) > 255:
                    bad.append((name, m.group(0), "重复数 > 255（git 硬上限）"))
            if re.search(r"\{\d+,\s*\d+\}\?", blob):
                bad.append((name, "惰性量词", "惰性量词 {..}?（POSIX ERE 不支持）"))
            if re.search(r"\\x[0-9a-fA-F]{2}", blob):
                bad.append((name, "\\xNN", "十六进制转义（git 不识别，等于字面 xNN）"))
    return bad


# ── 方向九：风险类别覆盖度表的自洽性 ──────────────────────────────────
# **为什么需要**：Batch 161 的观察是——**九道闸各自都写了自己的「不检查什么」，
# 但从来没有一张表把它们合起来看**。后果是**连着好几个批次都有人以为
# 某类问题有人管**：侧栏漏了 20 批、内链无人守、`fails += 1` 漏了两次、
# 11 处 skip 静默通过。共同形态是**「以为有人管，其实从头到尾没人管」**。
#
# **本方向只判结构，不判内容质量**：
#   ① A/B/C 三类标题都必须存在，且每类的行**两列都非空**（不许留空占位）；
#   ② **A 类的行数必须等于闸门清单的行数**——多一道闸没被认领，或
#      认领了不存在的闸，都说明表与现实脱节；
#   ③ B/C 每一行必须**写明依据**（含批次号或闸名的非空说明），
#      否则那又是一个「看起来有人管」的空格；
#   ④ **小节标题里手写的「（N 类）」必须等于该表实际行数**，且 A 类不许删掉这个计数。
#
# **④ 为什么需要（Batch 168 实锤）**：② 只管「表 vs 闸门清单」，
# **管不到标题里那个手写的数**。实测 `**A 类 · 有闸守着（9 类）**` 写着 9、
# 表里已经 **10 行**——因为 Batch 162 新增闸 10 时加了行、**没改标题**，
# 之后**连过 6 个批次没人发现**。而**这类数最危险**：
# 它长得像结论（「9 类风险有人管」），实际早已过期，**读者据此判断自己有没有被覆盖**。
#
# **④ 的形态选择**：要求 **A 类必须声明计数**。否则「把计数删掉」就成了
# 绕过检查的最短路径——**判据不能给作弊留后门**。
#
# **不判的**：某类风险「该不该建闸」——那是人的判断，写进表里的理由列即可。
def coverage_table_check(root):
    """返回 (缺失标题, 空单元格, A类行数与闸门数的不一致, 缺依据的行, 标题计数不一致)。"""
    path = os.path.join(root, "AUDIT-RULES.md")
    text = open(path, encoding="utf-8").read()
    m = re.search(r"###\s*风险类别覆盖度[^\n]*\n(.*?)(?=\n###\s)", text, re.S)
    if not m:
        return ["风险类别覆盖度"], [], None, [], []
    body = m.group(1)
    classes, empties, no_reason = {}, [], []
    declared_counts = {}
    cur = None
    for line in body.split("\n"):
        if re.match(r"^\*\*[ABC]\s*类", line.strip()):
            cur = line.strip().strip("*").split("类")[0].strip()
            classes[cur] = []
            # 标题里手写的「（N 类）」：解析不出来也是「无法核对」，一并报
            mc = re.search(r"（([0-9零一二三四五六七八九十]+)\s*类\s*）", line)
            declared_counts[cur] = _cn_int(mc.group(1)) if mc else None
            continue
        if not line.startswith("|") or re.match(r"\|\s*:?-", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 2 or cells[0] in ("风险类别", "闸"):
            continue
        if cur is None:
            continue
        classes[cur].append(cells)
        if not cells[0] or not cells[-1]:
            empties.append((cur, cells[0] or "(空)"))
        # B/C 每一行都要有依据：说明列里应含批次号或闸名
        if cur.startswith(("B", "C")) and not re.search(r"(Batch\s*\d+|闸\s*\d|脚本头|声明|实测)", cells[-1]):
            no_reason.append((cur, cells[0]))
    declared, rows, _listed, _invoked = gate_inventory(root)
    n_a = len(classes.get("A", []))
    mismatch = None if n_a == rows else ("A 类 %d 行 vs 闸门清单 %d 行" % (n_a, rows))
    missing = [k for k in ("A", "B", "C") if not any(x.startswith(k) for x in classes)]
    # 标题计数：声明了就必须与实际行数相等；A 类还必须声明
    count_bad = []
    for k in sorted(classes):
        d = declared_counts.get(k)
        if d is None:
            if k == "A":
                count_bad.append("A 类标题没写「（N 类）」计数——删掉它就绕过了检查")
            continue
        if d != len(classes[k]):
            count_bad.append("%s 类标题写「%d 类」但表里只有 %d 行"
                             % (k, d, len(classes[k])))
    return missing, empties, mismatch, no_reason, count_bad


# ── 方向十：闸门的输入范围必须自声明，不得由 cwd 决定 ──────────────────
# **不变式**：闸脚本不得用**裸相对路径**去定位它要核对的文件——
# 不得 `glob.glob("**/*.md")`，也不得 `os.path.join(某个裸相对目录常量, …)`。
#
# **背景（Batch 166 实锤）**：闸 4 用 `glob.glob("**/*.md", recursive=True)`，
# **相对当前工作目录**。在干净空目录里运行时，它扫到 **0 个文件**、0 个问题，
# 输出「快捷键前缀核对通过……手册写法均已带前缀」，**退出码 0**——
# **什么都没查，却判了通过**。这就是 Batch 157「工具失败被当成零命中」的原样重演，
# 也是纪律 101「换一个判据就要重新问一遍它会不会静悄悄什么都查不到」的第一次应验。
#
# **为什么用 AST 而不是正则**：第一版判据是纯文本扫 `glob.glob("`，
# 结果把闸 4 **文档字符串里的示例文字**也匹配上了——**判据太宽的老毛病**。
# 改成解析 AST 看真正的调用节点，文档字符串、注释里的写法一律不算。
# 实测 9 道闸：只标出 `verify-screenshots.py`（真阳性），**零误伤**。
#
# **覆盖不到什么（如实说明）**：`os.listdir(".")`、`open("README.md")`
# 这类不经 glob / os.path.join 的裸路径**照不到**。
# 本批的兜底是**行为实测**（把每道闸在手册根与空目录各跑一次、退出码必须一致），
# 两者互补：静态判据便宜、能进构建；行为实测抓得住静态照不到的形态。
_GLOB_CALL = "glob.glob"


def cwd_dependent_gates(root):
    """返回 [(脚本, 形态, 细节)]：用裸相对路径定位输入的闸脚本。"""
    bad = []
    scripts = os.path.join(root, "scripts")
    for name in sorted(os.listdir(scripts)):
        if not (name.startswith("verify-") and name.endswith(".py")):
            continue
        path = os.path.join(scripts, name)
        try:
            tree = ast.parse(open(path, encoding="utf-8").read())
        except SyntaxError as exc:
            bad.append((name, "无法解析", f"SyntaxError: {exc}"))
            continue

        # 模块级字符串常量：可能是「裸相对目录」
        rel_consts = {}
        for node in tree.body:
            if (isinstance(node, ast.Assign) and isinstance(node.value, ast.Constant)
                    and isinstance(node.value.value, str)
                    and isinstance(node.targets[0], ast.Name)):
                v = node.value.value
                if not v.startswith("/") and "os." not in v and not v.startswith("$"):
                    rel_consts[node.targets[0].id] = v

        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            f = node.func
            is_glob = (f.attr == "glob" and isinstance(f.value, ast.Name) and f.value.id == "glob")
            is_join = (f.attr == "join" and isinstance(f.value, ast.Attribute)
                       and f.value.attr == "path")
            if is_glob and node.args:
                a = node.args[0]
                if isinstance(a, ast.Constant) and isinstance(a.value, str):
                    bad.append((name, "glob 用了裸字面量", f'glob.glob("{a.value}")'))
            if is_join and node.args:
                a = node.args[0]
                if isinstance(a, ast.Name) and a.id in rel_consts:
                    bad.append((name, "join 用了无根目录常量",
                                f'os.path.join({a.id}, …)  # {a.id}="{rel_consts[a.id]}"'))
    return bad


# ── 方向十一：「闸 → 反验对应关系」表必须与现场双向一致 ────────────────
# **为什么需要**：Batch 168 把规约 §4「每道闸都必须做反向验证」拿去对照现状，
# 逐条列「闸 → 反验脚本」的对应关系后才发现**十道闸里 3 道一道反验都没有**——
# **规约写着「必须」，而它在事实上没被满足，而账面看不出区别。**
# 补齐之后建了这张对应关系表，但它**自己就成了一个没人看管的登记处**，
# 于是本方向把它变成常驻守卫（纪律 105：一次性普查的产物要尽快机器化）。
#
# **不变式（四条，全部双向）**：
#   ① 表里每一行认领的反验文件**必须真实存在**（认领了不存在的东西 = 没在管）；
#   ② 现场每一个**驱动**都必须被表认领，且**只被认领一次**（漏认领 = 新的闸没写反验）；
#   ③ 表里的闸编号集合必须**等于实际闸门数**（不多不少、不得重复）；
#   ④ 每行的例数必须是**正整数**——**空格与 0 看起来像有人管，其实没有**（Batch 161）。
#
# **「驱动」怎么判定：靠事实，不靠命名约定**（这是本方向最要紧的一处设计）。
# `scripts/` 下 `selftest-*` 共 64 个文件，其中 **54 个是注入夹具**（被驱动以参数调用），
# **只有 10 个是入口**。若按文件名里有没有 `-fix-` 来分，那是**约定不是事实**，
# 有人取名不照约定，判据就静悄悄失效——正是纪律 101 的形态。
# 改用**事实判定**：**剥掉注释与文档字符串后，没有任何其它 `selftest-*` 引用它的那个，
# 就是入口**。实测：剥注释前只认出 8 个（`selftest-meta.sh` 出现在另一份脚本的**注释**里，
# 是 Batch 167「注释骗过文本判据」的原地重演），剥注释后**正好 10 个，且 54 个夹具全部有主**。
#
# **如实说明覆盖边界**：shell 侧的「剥注释」是行级近似（`#` 之后一律截断，
# 字符串里含 `#` 时会多剥一点）。实测不影响结果——54 个夹具仍全部被识别为夹具。
# 若将来出现「只在一行 shell 注释里被引用」的夹具，它会被误判成入口，**本闸会报一条可修的错**。
def _selftest_code_only(path):
    """只留真正会被执行到的字面量：Python 用 AST 剥注释与文档字符串，shell 剥 # 注释。"""
    src = open(path, encoding="utf-8", errors="ignore").read()
    if path.endswith(".py"):
        try:
            tree = ast.parse(src)
        except SyntaxError:
            return src
        return "\n".join(n.value for n in ast.walk(tree)
                         if isinstance(n, ast.Constant) and isinstance(n, str))
    return "\n".join(re.sub(r"#.*$", "", ln) for ln in src.split("\n"))


def selftest_drivers(root):
    """返回 (入口列表, 全部 selftest-* 列表)。入口 = 剥注释后无人引用的那个。"""
    scripts = os.path.join(root, "scripts")
    names = sorted(n for n in os.listdir(scripts) if n.startswith("selftest-"))
    bodies = {}
    for n in names:
        if n.endswith((".py", ".sh")):
            bodies[n] = _selftest_code_only(os.path.join(scripts, n))
    referenced = {o for n, b in bodies.items() for o in names if o != n and o in b}
    return [n for n in names if n not in referenced], names


def selftest_coverage_check(root):
    """返回 (问题列表, 未能核对)。"""
    scripts = os.path.join(root, "scripts")
    text = open(os.path.join(root, "AUDIT-RULES.md"), encoding="utf-8").read()
    m = re.search(r"###\s*闸\s*→\s*反验的对应关系[^\n]*\n(.*?)(?=\n###|\n##\s)", text, re.S)
    if not m:
        return [], "找不到「闸 → 反验的对应关系」小节"
    rows = []
    for line in m.group(1).split("\n"):
        if not line.startswith("|") or re.match(r"\|\s*:?-", line):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 3 or cells[0] in ("闸",):
            continue
        rows.append(cells)
    if not rows:
        return [], "对应关系表里没有数据行"

    problems = []
    claimed, nums = [], []
    for cells in rows:
        name = cells[1].strip("`")
        if not os.path.isfile(os.path.join(scripts, name)):
            problems.append(f"「{cells[0]}」认领的反验 {name} **并不存在**——认领一个不存在的东西等于没在管")
        else:
            claimed.append(name)
        g = re.match(r"^(\d+)", cells[0])
        if g:
            nums.append(int(g.group(1)))
        n_cases = _cn_int(cells[2]) if re.match(r"^\d+$", cells[2]) else None
        if n_cases is None or n_cases <= 0:
            problems.append(f"「{cells[0]}」的例数写 [{cells[2] or '(空)'}]，**必须是正整数**"
                            f"——空格与 0 看起来像有人管，其实没有")

    drivers, _all = selftest_drivers(root)
    for d in drivers:
        n = claimed.count(d)
        if n == 0:
            problems.append(f"驱动 `{d}` **没有被对应关系表认领**——新增闸若不写反验，这一行就没人管")
        elif n > 1:
            problems.append(f"驱动 `{d}` 被认领了 {n} 次，应当恰好 1 次")
    n_gates = gate_inventory(root)[1]
    if sorted(nums) != list(range(1, n_gates + 1)):
        problems.append(f"闸编号集合 {sorted(nums)} 与实际闸门数 {n_gates} 不符"
                        f"（应为 1..{n_gates}，不多不少、不得重复）")
    return problems, None



# ── 方向八：闸门不得在「无法核对」时返回 0 ────────────────────────────
# **不变式**：闸门打印了 `[skip]`，退出码就**不能是 0**。
#
# **背景（Batch 160 普查）**：**6 个闸共 11 处**在数据不可用时打印 `[skip]`
# 然后 `return 0`——上游源码缺失、上游读取失败、没抽到路由、dist 未构建…
# 而 `build-site.sh` 的闸调用点**只看退出码**。于是**上游目录一改名或一缺失，
# 9 道闸里有 5 道什么都没查却全绿**，而手册账本里「已逐条核实」的声明
# 被无声地跳过。**这与 Batch 157 修的「工具失败被当成零命中」是同一个病：
# 「查不了」与「查过了没问题」返回了同一个码。**
#
# 修法：约定 **0 = 核对过且一致 / 1 = 核对过且不一致 / 2 = 根本没能核对**，
# build-site.sh 用 `run_gate` 把 2 单独分支处理（**报成「未能核对」而不是
# 「核对不一致」**——后者会让人去手册里找根本不存在的问题）。
# 确需在无上游的环境构建时，可显式设 `ALLOW_UNVERIFIED=1` 放行，
# **但那必须是主动决定，不能是默认行为。**
#
# **只判形态**：找「打印 `[skip]` 的块里紧跟的 `return 0`」，纯文本可枚举。
_SKIP_RE = re.compile(r'^\s*return 0\s*$')


def skip_returns_zero(root):
    """返回 [(脚本, 行号, 片段)]：打印 [skip] 之后却 return 0 的地方。"""
    bad = []
    for name in sorted(os.listdir(os.path.join(root, "scripts"))):
        if not (name.startswith("verify-") and name.endswith(".py")):
            continue
        path = os.path.join(root, "scripts", name)
        lines = open(path, encoding="utf-8").read().split("\n")
        for i, line in enumerate(lines):
            if line.lstrip().startswith("#"):
                continue
            if "[skip]" not in line or "print(" not in line:
                continue
            j = i + 1
            while j < len(lines) and (lines[j].strip() == "" or
                                      re.match(r"^\s*print\(", lines[j])):
                j += 1
            if j < len(lines) and _SKIP_RE.match(lines[j]):
                bad.append((name, j + 1, lines[j].strip()))
    return bad


# ── 方向七：闸门不得「只报错不失败」 ──────────────────────────────────
# **不变式**：闸门打印了 `✗`，退出码就必须非 0。
#
# **为什么它值得单独立一个方向**：方向五与方向六**各漏过一次计数**——
# 闸门把问题打印出来了、**退出码却是 0**。而 build-site.sh、反验脚本、CI
# **全都只看退出码**，于是构建照样「成功」、反验照样判「通过」。
# **同一个错误犯两次，说明「再加一道记得检查的闸」不可靠**，所以 Batch 159
# 把 `print("✗ …")` 改成了 `fail()`，让二者**在语法上无法分开**；
# 本方向负责**不让有人改回去**。
#
# **只判形态、不判语义，且刻意收窄到本闸自己**：
#   · **锚定「被打印的字符串以 ✗ 开头」**，而不是「这一行出现过 ✗」——
#     第一版写成 `if "✗" in line and "print(" in line`，**误报 5 处**：
#     两条注释里提到 `print("✗ …")`、检查器自己的匹配条件那行、
#     以及一条 `✓` 提示语里顺带出现「✗」字样。**判据必须锚在真正的形态上，
#     否则误报会让人开始忽略闸门输出**（Batch 150 判「不可建」同一条理由）。
#   · **不扫其他闸**：全量普查过一遍（见 AUDIT「环境记录一百一十五」），
#     其余闸用的是**早退 `return 1`** 或**累加器**（`verify-tables.py` 的
#     `total_bad`）两种形态，退出码都对；**没有证据就不扩大范围**。
#   · 豁免两类且都写明理由：① 计数函数自己的打印（内部已计数）；
#     ② 报完立刻 `return 1` 的早退路径。
_BARE_ERROR_RE = re.compile(r'^\s*print\(\s*f?["\']\s*✗')


def bare_error_prints(root):
    """返回 [(行号, 片段)]：本闸直接 print ✗ 却不经计数函数的地方。"""
    path = os.path.join(root, "scripts", "verify-meta.py")
    lines = open(path, encoding="utf-8").read().split("\n")
    bad = []
    for i, line in enumerate(lines):
        if line.lstrip().startswith("#"):        # 注释不是代码
            continue
        if not _BARE_ERROR_RE.match(line):
            continue
        window = "\n".join(lines[max(0, i - 3):i + 1])
        if "_FAILS.append" in window:            # ① fail() 自己
            continue
        if re.search(r"return 1", "\n".join(lines[i + 1:i + 5])):   # ② 早退
            continue
        bad.append((i + 1, line.strip()[:70]))
    return bad


# ── 方向六：内链完整性（源文件层） ──────────────────────────────────────
# **为什么需要这个方向**，以及**它和第一道内联闸不重复在哪**：
# 第一道闸在 `build-site.sh` 里逐个解析 **dist 产物里的 href**，管的是
# 「发布后是不是 404」，最常见的成因是指向 `srcExclude` 文件。
# 本方向在**源文件**上管三件第一道闸管不到的事：
#   ① 手册自订的约定「正文内链只能是手册页面间的相对 .md 链接、
#      不带 #fragment」——**这条约定此前没有任何闸在守**，
#      而 `.vitepress/config.mjs` 里 `ignoreDeadLinks: true`，
#      连构建都不会拦；
#   ② **孤儿页**（既没人链它、也不在侧栏）——死链检测查的是「边」，
#      一个没有任何入边的页面在它眼里根本不存在；
#   ③ 在**构建之前**就响，定位到的是源文件行号而不是 dist 里的转义后 href。
#
# **两种语法都必须认**（这是本方向最容易写错的地方）：
# 手册里图片**混用** markdown `![]()` 与 HTML `<img src>`，
# 第一版只认 markdown，于是把 14 张**确实在用**的图判成「未被引用」。
# **只判一种语法 = 稳定误报**，而误报会让人开始忽略闸门输出。
# （与 Batch 150 判「文案逐字对账闸不可建」用的是同一条理由。）
def link_integrity_check(root):
    """返回 (断链, 约定违反, 孤儿页, 统计字典)。"""
    skip = {"AUDIT.md", "AUDIT-RULES.md", "PROGRESS.md", "SOURCE_OBSERVATIONS.md",
            "PUBLISH.md", "FINAL-REPORT.md", "task-inventory.yml"}
    md_link = re.compile(r"\]\(([^)\s]+)\)")
    html_img = re.compile(r"<img\b[^>]*\bsrc=[\"']([^\"']+)[\"']", re.I)

    pages, inbound, dead, viol = [], set(), [], []
    n_links = n_imgs = n_ext = 0
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames
                       if d not in (".vitepress", "node_modules", ".git", "screenshots", "dist")]
        for fn in filenames:
            if not fn.endswith(".md") or fn in skip:
                continue
            full = os.path.join(dirpath, fn)
            rel = os.path.relpath(full, root)
            pages.append(rel)
            text = open(full, encoding="utf-8").read()
            targets = []
            for t in md_link.findall(text):
                if t.startswith(("http://", "https://", "mailto:")):
                    n_ext += 1
                    continue
                targets.append((t, "md"))
            for t in html_img.findall(text):
                if t.startswith(("http://", "https://", "data:")):
                    continue
                targets.append((t, "img"))
            for t, kind in targets:
                if kind == "md":
                    n_links += 1
                else:
                    n_imgs += 1
                if "#" in t:
                    viol.append((rel, t, "链接带 #fragment（手册约定不用页内锚点）"))
                if t.startswith("/"):
                    viol.append((rel, t, "绝对路径内链（手册约定用相对路径）"))
                if "://" in t or t.startswith("mailto:"):
                    continue
                resolved = os.path.normpath(os.path.join(dirpath, t.split("#", 1)[0]))
                if os.path.isfile(resolved):
                    inbound.add(os.path.relpath(resolved, root))
                elif kind == "md":
                    dead.append((rel, t))
                else:
                    dead.append((rel, t + "（<img>）"))

    # 孤儿页：既无人链它，也不在侧栏；站点首页（根 README.md）按约定豁免。
    cfg_path = os.path.join(root, ".vitepress", "config.mjs")
    in_sidebar = set()
    if os.path.isfile(cfg_path):
        cfg = open(cfg_path, encoding="utf-8").read()
        for t in re.findall(r"link:\s*['\"]([^'\"]+)['\"]", cfg):
            t = t.lstrip("/")
            in_sidebar.add(t if t.endswith(".md") else t + ".md")
    home = "README.md"
    orphans = [p for p in sorted(pages) if p not in inbound and p not in in_sidebar and p != home]

    stats = {"pages": len(pages), "links": n_links, "imgs": n_imgs, "external": n_ext}
    return dead, viol, orphans, stats


# ── 方向一：登记表 ─────────────────────────────────────────────────
# (文件名, 计数器, 该文件里用来写这个数的正则)
# 正则**必须容忍 markdown 粗体**——Batch 139 的 `\b` 跨不过 `)` 是同源坑，
# 第一版 `(\d+)\s*项` 匹配不到 `**29 项**`，扫描静默返回空集却不报错。
# **静默失配比误报更危险**，所以每条正则都带一个**自检**：下文 scan_meta 命中数
# 为 0 时，方向二会直接报「登记项扫不到」，不会让它悄悄溜过去。
REGISTRY = [
    ("README.md", "task_pages", r"\**(\d+)\s*篇任务指南\**"),
    ("README.md", "inventory_total", r"任务账本共\s*\**(\d+)\s*项\**"),
    ("README.md", "verified", r"\**(\d+)\s*项\**已在[^*]*逐条走查验证"),
    ("README.md", "excluded", r"\**(\d+)\s*项\**因[^*]*无法验证"),
    ("README.md", "screenshots", r"\**(\d+)\s*张实拍截图\**"),
    ("README.md", "content_pages", r"共\s*\**(\d+)\s*个内容页\**"),
    ("10-tasks/README.md", "task_pages", r"操作页，共\s*\**(\d+)\s*篇"),
    ("FINAL-REPORT.md", "content_pages", r"\**(\d+)\s*个内容页\**"),
]

# 方向二的扫描模式：与 REGISTRY 一一对应，命中集合必须相等。
# **这里不写「共 N 项」这类宽泛形态**——业务数字（审美批改 4 个方向、
# 灵感墙 22 条）会全被扫进来，而它们不归本闸管（见脚本头「不检查什么」）。
# 宁可窄：漏检靠方向一兜（登记项一定被逐条重数），误报会逼着人加豁免，越修越乱。
#
# **粗体一律写成可选 `\**`**：第一版按「README 里的数字都加粗」写死，
# 结果 `10-tasks/README.md` 那句「操作页，共 29 篇」**本来就没有粗体**，
# 扫不到 → 闸门报「登记项失效」。**又是一次判据先坏**（第 23 条纪律的第七次应验），
# 而且是**反向**的：前六次是判据太严，这次是判据**假设了手册的排版习惯**。
# 手册里同一批数字有的加粗有的不加——**别假设一致性**。
SCAN_PATTERNS = {
    "task_pages": r"(?:\**(\d+)\s*篇任务指南\**|操作页，共\s*\**(\d+)\s*篇)",
    "content_pages": r"\**(\d+)\s*个内容页\**",
    "inventory_total": r"任务账本共\s*\**(\d+)\s*项",
    "verified": r"\**(\d+)\s*项\**已在[^*]{0,40}走查验证",
    "excluded": r"\**(\d+)\s*项\**因[^*]{0,60}无法验证",
    "screenshots": r"(\d+)\s*张(?:实拍)?截图",
}


def scan_meta(root):
    """反向扫描参与发布的页面，返回 {计数器: {文件名: 数字集合}}。"""
    targets = [p for p in glob.glob(os.path.join(root, "*.md"))
               if os.path.basename(p) not in SRC_EXCLUDE_BASENAMES]
    targets += [os.path.join(root, f) for f in EXTRA_SCAN_FILES]
    targets += glob.glob(os.path.join(root, "10-tasks", "*.md"))

    found = {k: {} for k in SCAN_PATTERNS}
    for path in sorted(targets):
        name = os.path.relpath(path, root)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            continue
        for kind, pat in SCAN_PATTERNS.items():
            for m in re.finditer(pat, text):
                # 模式里可能带 alternation（多个捕获组），取**第一个非空**的数字组。
                # 直接写 m.group(1) 会在「另一个分支命中」时拿到 None，
                # 而 None 混进数字集合会让比对结果毫无意义却**不报错**——静默失配。
                val = next((g for g in m.groups() if g is not None), None)
                if val is None:
                    continue
                found[kind].setdefault(name, set()).add(int(val))
    return found


def registered_scan_expectation():
    """登记项里、且属于 SCAN_PATTERNS 覆盖范围的那部分。"""
    return {k: {} for k in SCAN_PATTERNS}, {
        (f, k): None for (f, k, _p) in REGISTRY if k in SCAN_PATTERNS
    }


# ── 错误输出与失败计数**合成一个动作**（Batch 159） ────────────────────
# **为什么改结构而不是加一道检查**：方向五与方向六**各漏过一次 `fails += 1`**
# ——闸门把问题打印出来了，**退出码却是 0**；而 build-site.sh、反验脚本、CI
# **全都只看退出码**。同一个错误犯两次，说明「再加一道记得检查的闸」这条路线
# 本身不可靠：**第三次还会犯**。
#
# **正确做法是让「打印报错」在语法上无法脱离「计入失败」**：本闸不再允许
# 直接 `print("✗ …")`，一律走 `fail()`；第九道闸的**方向七**静态核对这一点。
# `fail()` **不自己加 `✗` 标记**——标记留在调用方的字符串里，
# 这样转换只是把 `print(` 换成 `fail(`，**字符串内容一个字都不动**
# （第一版转换去掉了引号与 f 前缀，把隐式拼接的多行 f-string 弄坏了，已回退重做）。
_FAILS = []


def fail(msg):
    """报告一处不一致。**打印与计数在同一个函数里，不可能只做一半。**"""
    _FAILS.append(msg)
    print(msg)


def fail_count():
    return len(_FAILS)


def main():
    root = ROOT
    # **入口先确认基本输入在**（Batch 193 实测加）。
    # 本闸原来第一个动作就是 `open("screenshots/manifest.yml")`——
    # **手册树不在时它抛未捕获的 `FileNotFoundError` 并以 rc=1 退出**，
    # 而 rc=1 意为「核过，且核出不一致」。**实际是「一本手册都没有，本轮根本没开始核」。**
    # 同一批给另外 10 道闸换了 `baseline_guard`，**本闸不读上游、没有基线可读**，
    # 所以要自己认这四样东西：**它们是这个判据的输入，不是它核的内容。**
    _missing = [p for p in ("README.md", "screenshots/manifest.yml",
                            "AUDIT-RULES.md", "PROGRESS.md")
                if not os.path.exists(os.path.join(root, p))]
    if _missing:
        print("[未能核对] 手册基本输入缺失：%s" % "、".join(_missing))
        print("  → 本闸本轮没有核对任何断言。**这不是「核对通过」，也不是「核出不一致」**——"
              "它说的是「手册树本身不在」，修法是恢复手册文件，不在内容上找。")
        return 2
    print("手册元数据核对：把「本手册有多少东西」逐条现场重数")
    print("=" * 62)

    # 前置：截图 manifest 与磁盘必须一致，否则截图数这个真值本身不可信
    if not screenshots_match_disk(root):
        print("✗ screenshots/manifest.yml 与磁盘 png 不一致——")
        print("    截图数这个真值不可信，先跑 verify-screenshots.py 定位")
        print("元数据核对：0 条可核（截图真值前置不满足）")
        return 1

    # ── 方向一：逐条重数 ──
    for filename, kind, pat in REGISTRY:
        path = os.path.join(root, filename)
        actual = COUNTERS[kind](root)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            fail(f"  ✗ {filename}：登记的文件不存在")
            continue
        ms = [int(m.group(1)) for m in re.finditer(pat, text)]
        if not ms:
            # 登记的正则扫不到自己的条目 = 手册改了排版而登记表没跟上。
            # **这必须报错，不能当成「没有这条断言」**——静默通过是这类闸门最常见的失效。
            fail(f"  ✗ {filename}：{COUNTER_LABEL[kind]} 的登记正则扫不到（手册可能改了写法）")
            continue
        bad = [v for v in ms if v != actual]
        if bad:
            fail(f"  ✗ {filename}：{COUNTER_LABEL[kind]} 写 {sorted(set(bad))}，实际 {actual}")
        else:
            print(f"  ✓ {filename}：{COUNTER_LABEL[kind]} = {actual}")

    # ── 方向二：反向扫描，与登记表双向一致 ──
    print("-" * 62)
    found = scan_meta(root)
    for kind, pat in SCAN_PATTERNS.items():
        reg = {f: set() for (f, k, _p) in REGISTRY if k == kind}
        for f, vals in found[kind].items():
            if f not in reg:
                fail(f"  ✗ 「{sorted(vals)[0]}」形态出现在 {f}，但未登记为 {COUNTER_LABEL[kind]}")
                continue
            reg[f] |= vals
        for f, vals in sorted(reg.items()):
            if not vals:
                fail(f"  ✗ {f}：登记为 {COUNTER_LABEL[kind]}，但扫描命中为空（登记项已失效）")
            elif found[kind].get(f) != vals:
                fail(f"  ✗ {f}：{COUNTER_LABEL[kind]} 扫描值 {sorted(found[kind][f])} ≠ 登记值 {sorted(vals)}")

    total = len(REGISTRY)

    # 方向一/二结束时的失败数快照。**必须单独记一个**：
    # 方向三/四/四之二/五的失败不属于「登记表里的 N 条计数」，
    # 共用一个计数器会让汇总行把「闸门清单不一致」说成「某条计数对不上」——
    # **汇总行报错因，比报错本身更难查**（Batch 157 的老毛病又长出一处）。
    count_fails = fail_count()

    # ── 方向三：闸门清单三方一致 ──
    print("-" * 62)
    declared, rows, listed, invoked = gate_inventory(root)
    if declared is None:
        fail("  ✗ AUDIT-RULES.md 找不到「现有 N 道闸」标题")
    else:
        if declared != rows:
            fail(f"  ✗ AUDIT-RULES.md 标题写「{declared} 道闸」，清单表却有 {rows} 行")
        expect_rows = len(invoked) + INLINE_GATE_SLACK
        if rows != expect_rows:
            fail(f"  ✗ 清单表 {rows} 行 ≠ build-site.sh 实际调用的 {len(invoked)} 个闸"
                  f" + 内联 {INLINE_GATE_SLACK} 道（应 {expect_rows} 行）")
        for name in sorted(listed - invoked):
            fail(f"  ✗ 清单表列了 scripts/{name}.py，但 build-site.sh 从不调用它")
        for name in sorted(invoked - listed):
            fail(f"  ✗ build-site.sh 调用了 scripts/{name}.py，清单表却没有登记")
        if not _FAILS:
            print(f"  ✓ 闸门清单三方一致：标题 {declared} 道 = 表 {rows} 行"
                  f" = build-site 实际 {len(invoked)} 个脚本 + 内联 {INLINE_GATE_SLACK} 道")

    # ── 方向四：任务索引 ⇄ 页面标题 ──
    print("-" * 62)
    missing, mismatched, n_pairs, n_pages = index_check(root)
    for f in missing:
        fail(f"  ✗ 任务页 {f} 不在 {INDEX_FILE} 的索引里（建了页面忘了登记）")
    for target, label, want in mismatched:
        fail(f"  ✗ 索引里 {target} 的链接文字「{label}」与页面标题「{want}」既不相同、"
              f"也不是「标题（提示）」形态")
    if not missing and not mismatched:
        print(f"  ✓ 任务索引双向一致：{n_pages} 个任务页全部登记，"
              f"{n_pairs} 条链接文字与页面标题一致（含有意的「标题（提示）」形态）")

    # ── 方向四之二：任务页必须在 vitepress 侧栏里 ──
    print("-" * 62)
    sb_missing, n_sb = sidebar_check(root)
    for f in sb_missing:
        fail(f"  ✗ 任务页 {f} 不在 vitepress 侧栏里（站点主导航缺入口，读者发现不了）")
    if not sb_missing:
        print(f"  ✓ 侧栏覆盖：{n_sb} 个任务页全部在侧栏"
              f"（只查存在性——侧栏用短标题是设计，不比文字）")

    # ── 方向五：闸门脚本里的正则不得含 git grep 不支持的转义 ──
    print("-" * 62)
    bad_escapes = regex_engine_check(root)
    for path, pat, esc in bad_escapes:
        fail(f"  ✗ {path} 的 git grep -E 模式含 {esc}（git grep 的 ERE 不支持它，"
              f"会**静默永不匹配**）：{pat[:60]}")
    if not bad_escapes:
        print(f"  ✓ 正则引擎兼容：闸门脚本的 git grep 模式不含 git 不支持的形态"
              f"（\\s \\d \\w \\b / [^\\n] / 重复数>255 / 惰性量词 / \\xNN）"
              f"——这类写法会让 git 整条拒绝模式或静默匹配 0 行，断言随之恒真")

    # ── 方向六：内链完整性 ──
    print("-" * 62)
    dead, viol, orphans, lst = link_integrity_check(root)
    for rel, tgt in dead:
        fail(f"  ✗ {rel} 的链接指向不存在的文件：{tgt}")
    for rel, tgt, why in viol:
        fail(f"  ✗ {rel}：{why} —— {tgt}")
    for p in orphans:
        fail(f"  ✗ {p} 没有任何入链、也不在侧栏（站点首页除外）——读者在站点里发现不了它")
    if not dead and not viol and not orphans:
        print(f"  ✓ 内链完整：{lst['pages']} 个内容页、{lst['links']} 条 .md 相对链接 + "
              f"{lst['imgs']} 张 <img> 全部可达；无 #fragment、无绝对路径、无孤儿页"
              f"（外链 {lst['external']} 条）")

    # ── 方向七：闸门不得「只报错不失败」 ──
    print("-" * 62)
    bare = bare_error_prints(root)
    for lineno, frag in bare:
        fail(f"verify-meta.py:{lineno} 直接 print ✗ 却不经计数函数，退出码会仍是 0 —— {frag}")
    if not bare:
        print("  ✓ 报错即失败：闸门脚本里所有 ✗ 都经计数函数或紧跟 return 1，"
              "**不存在「只报错不失败」**")

    # ── 方向八：闸门不得在「无法核对」时返回 0 ──
    print("-" * 62)
    zeros = skip_returns_zero(root)
    for name, lineno, frag in zeros:
        fail(f"{name}:{lineno} 打印 [skip] 之后却 return 0——"
             f"**「查不了」被当成「查过了没问题」**（Batch 160 同型共 11 处）")
    if not zeros:
        print("  ✓ 无法核对 ≠ 通过：所有 [skip] 路径的退出码都不是 0"
              "（约定 0 一致 / 1 不一致 / 2 未能核对）")

    # ── 方向十：闸门输入范围不得由 cwd 决定 ──
    print("-" * 62)
    cwd_bad = cwd_dependent_gates(root)
    for name, kind, detail in cwd_bad:
        fail(f"{name}：{kind}（{detail}）——**输入范围由 cwd 决定**："
             f"换个目录运行就会扫到另一个地方，"
             f"Batch 166 实测过这种闸能在「一个文件都没读到」时判定通过")
    if not cwd_bad:
        print("  ✓ 输入范围自声明：所有闸门脚本都不再用裸相对路径定位被核对的文件"
              "（AST 判据，文档字符串与注释里的写法不算）")

    # ── 方向九：风险类别覆盖度表的自洽性 ──
    print("-" * 62)
    miss, empties, mismatch, no_reason, count_bad = coverage_table_check(root)
    for k in miss:
        fail(f"覆盖度表缺少 {k} 类——三类（有闸 / 有意不覆盖 / 无人覆盖）缺一不可")
    for cls, who in empties:
        fail(f"覆盖度表 {cls} 类「{who}」有空格——**空格看起来像有人管，其实没有**")
    if mismatch:
        fail(f"覆盖度表与闸门清单脱节：{mismatch}")
    for cls, who in no_reason:
        fail(f"覆盖度表 {cls} 类「{who}」没写依据（需含批次号或闸名）")
    for why in count_bad:
        fail(f"覆盖度表小节标题的计数与表内容脱节：{why}")
    if not (miss or empties or mismatch or no_reason or count_bad):
        print("  ✓ 覆盖度表自洽：A/B/C 三类齐全、每格都有依据，"
              "A 类认领数与闸门清单一致，小节标题写的类数与表内实际行数也一致")

    # ── 方向十一：「闸 → 反验对应关系」表与现场双向一致 ──
    print("-" * 62)
    st_problems, st_void = selftest_coverage_check(root)
    if st_void:
        # 抽不到表 = 什么都没核对，绝不能算通过（沿用 Batch 160 的三段约定）
        fail(f"[skip] 反验对应关系表{st_void}，本方向本轮未能进行")
    for why in st_problems:
        fail(f"反验对应关系表与现场脱节：{why}")
    if not st_problems and not st_void:
        drivers, allst = selftest_drivers(root)
        print(f"  ✓ 反验对应关系表双向一致：{len(drivers)} 个驱动全部被认领、"
              f"认领的文件全部存在、闸编号 1..{gate_inventory(root)[1]} 无缺漏，"
              f"例数均为正整数（`scripts/` 下 {len(allst)} 个 selftest-* 里，"
              f"其余是注入夹具）")

    if _FAILS:
        print(f"元数据核对：登记表 {total} 条中 {total - count_fails} 条计数一致"
              f"（{count_fails} 条不一致）；另有 {len(_FAILS) - count_fails} 处属方向三/四/四之二/五/六/七/八/九/十")
        return 1
    print(f"元数据核对：登记表 {total} 条计数全部与现场重数一致，"
          f"且方向三/四/四之二/五/六/七/八/九/十/十一亦全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
