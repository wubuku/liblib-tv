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
#   · 「站内死链」那道是 `build-site.sh` **内联**的，没有独立脚本，
#     所以 **表行数 = 独立 verify 脚本数 + 1**。这条偏移是**设计如此**，
#     写死在这里而不是靠人去数——第一版就是因为忘了这个 +1 而自报错。
#   · 只统计 `scripts/verify-*.py`：selftest-*.sh 是反向验证，不参与构建期检查。

INLINE_GATE_SLACK = 1


def gate_inventory(root):
    """返回 (标题声明数, 清单表行数, 表里列出的脚本名集合, build-site 实际调用集合)。"""
    rules_path = os.path.join(root, "AUDIT-RULES.md")
    rules = open(rules_path, encoding="utf-8").read()

    m = re.search(r"###\s*现有\s*([一二三四五六七八九十]+|\d+)\s*道闸", rules)
    declared = _cn_int(m.group(1)) if m else None

    # 清单表：标题之后的第一张表，取含「脚本」表头的那张
    rows, listed = 0, set()
    if m:
        body = rules[m.end():]
        for line in body.split("\n"):
            if line.startswith("## ") or line.startswith("### "):
                break
            if line.startswith("|") and "脚本" not in line and not re.match(r"\|\s*-+", line):
                if "`" in line:
                    rows += 1
                    for s in re.findall(r"scripts/(verify-[a-z-]+)\.py", line):
                        listed.add(s)
            if rows and line.strip() == "":
                break

    build = open(os.path.join(root, "build-site.sh"), encoding="utf-8").read()
    invoked = set(re.findall(r"python3\s+scripts/(verify-[a-z-]+)\.py", build))
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
    digits = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5,
              "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
    return int(s) if s.isdigit() else digits.get(s)


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


def main():
    root = ROOT
    print("手册元数据核对：把「本手册有多少东西」逐条现场重数")
    print("=" * 62)

    # 前置：截图 manifest 与磁盘必须一致，否则截图数这个真值本身不可信
    if not screenshots_match_disk(root):
        print("✗ screenshots/manifest.yml 与磁盘 png 不一致——")
        print("    截图数这个真值不可信，先跑 verify-screenshots.py 定位")
        print("元数据核对：0 条可核（截图真值前置不满足）")
        return 1

    fails = 0

    # ── 方向一：逐条重数 ──
    for filename, kind, pat in REGISTRY:
        path = os.path.join(root, filename)
        actual = COUNTERS[kind](root)
        try:
            text = open(path, encoding="utf-8").read()
        except OSError:
            print(f"  ✗ {filename}：登记的文件不存在")
            fails += 1
            continue
        ms = [int(m.group(1)) for m in re.finditer(pat, text)]
        if not ms:
            # 登记的正则扫不到自己的条目 = 手册改了排版而登记表没跟上。
            # **这必须报错，不能当成「没有这条断言」**——静默通过是这类闸门最常见的失效。
            print(f"  ✗ {filename}：{COUNTER_LABEL[kind]} 的登记正则扫不到（手册可能改了写法）")
            fails += 1
            continue
        bad = [v for v in ms if v != actual]
        if bad:
            print(f"  ✗ {filename}：{COUNTER_LABEL[kind]} 写 {sorted(set(bad))}，实际 {actual}")
            fails += 1
        else:
            print(f"  ✓ {filename}：{COUNTER_LABEL[kind]} = {actual}")

    # ── 方向二：反向扫描，与登记表双向一致 ──
    print("-" * 62)
    found = scan_meta(root)
    for kind, pat in SCAN_PATTERNS.items():
        reg = {f: set() for (f, k, _p) in REGISTRY if k == kind}
        for f, vals in found[kind].items():
            if f not in reg:
                print(f"  ✗ 「{sorted(vals)[0]}」形态出现在 {f}，但未登记为 {COUNTER_LABEL[kind]}")
                fails += 1
                continue
            reg[f] |= vals
        for f, vals in sorted(reg.items()):
            if not vals:
                print(f"  ✗ {f}：登记为 {COUNTER_LABEL[kind]}，但扫描命中为空（登记项已失效）")
                fails += 1
            elif found[kind].get(f) != vals:
                print(f"  ✗ {f}：{COUNTER_LABEL[kind]} 扫描值 {sorted(found[kind][f])} ≠ 登记值 {sorted(vals)}")
                fails += 1

    total = len(REGISTRY)

    # ── 方向三：闸门清单三方一致 ──
    print("-" * 62)
    declared, rows, listed, invoked = gate_inventory(root)
    if declared is None:
        print("  ✗ AUDIT-RULES.md 找不到「现有 N 道闸」标题")
        fails += 1
    else:
        if declared != rows:
            print(f"  ✗ AUDIT-RULES.md 标题写「{declared} 道闸」，清单表却有 {rows} 行")
            fails += 1
        expect_rows = len(invoked) + INLINE_GATE_SLACK
        if rows != expect_rows:
            print(f"  ✗ 清单表 {rows} 行 ≠ build-site.sh 实际调用的 {len(invoked)} 个闸"
                  f" + 内联 {INLINE_GATE_SLACK} 道（应 {expect_rows} 行）")
            fails += 1
        for name in sorted(listed - invoked):
            print(f"  ✗ 清单表列了 scripts/verify-{name}.py，但 build-site.sh 从不调用它")
            fails += 1
        for name in sorted(invoked - listed):
            print(f"  ✗ build-site.sh 调用了 scripts/verify-{name}.py，清单表却没有登记")
            fails += 1
        if fails == 0:
            print(f"  ✓ 闸门清单三方一致：标题 {declared} 道 = 表 {rows} 行"
                  f" = build-site 实际 {len(invoked)} 个脚本 + 内联 {INLINE_GATE_SLACK} 道")

    # ── 方向四：任务索引 ⇄ 页面标题 ──
    print("-" * 62)
    missing, mismatched, n_pairs, n_pages = index_check(root)
    for f in missing:
        print(f"  ✗ 任务页 {f} 不在 {INDEX_FILE} 的索引里（建了页面忘了登记）")
        fails += 1
    for target, label, want in mismatched:
        print(f"  ✗ 索引里 {target} 的链接文字「{label}」与页面标题「{want}」既不相同、"
              f"也不是「标题（提示）」形态")
        fails += 1
    if not missing and not mismatched:
        print(f"  ✓ 任务索引双向一致：{n_pages} 个任务页全部登记，"
              f"{n_pairs} 条链接文字与页面标题一致（含有意的「标题（提示）」形态）")

    # ── 方向四之二：任务页必须在 vitepress 侧栏里 ──
    print("-" * 62)
    sb_missing, n_sb = sidebar_check(root)
    for f in sb_missing:
        print(f"  ✗ 任务页 {f} 不在 vitepress 侧栏里（站点主导航缺入口，读者发现不了）")
        fails += 1
    if not sb_missing:
        print(f"  ✓ 侧栏覆盖：{n_sb} 个任务页全部在侧栏"
              f"（只查存在性——侧栏用短标题是设计，不比文字）")

    if fails:
        print(f"元数据核对：{total - fails} 条一致，{fails} 条不一致")
        return 1
    print(f"元数据核对：{total} 条全部与现场重数一致"
          f"（业务数字与台账历史引述不归本闸管，见脚本头）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
