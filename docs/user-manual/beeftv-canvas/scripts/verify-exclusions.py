#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""excluded 页解禁条件核对闸：账本里写的「还差什么」是否与上游现状一致。

背景（Batch 111）：手册有 4 个 `excluded` 任务（媒体版本族 / 云端 Agent /
Agent 记忆与技能 / 本地伴随进程），每条都附了「开放条件」。这类条件最危险的
失效方式是**悄悄过期**——上游可能已经解禁（或已彻底移除），而账本仍写着旧的
理由，于是「什么时候能补这一页」这个判断从此失准。

⚠️ Batch 164 补上本闸最大的漏洞：**闸名承诺核对全部 excluded 页，读者理所当然
以为每一条都被盯着，而实际上没有任何机制保证这一点。** 实测 6 条 excluded 里
`art-critique` **从未被本闸提及过一次**——它是 Batch 132 才加进账本的，加的人没
同步这里，而**没有任何东西会提醒**。于是它在 excluded 里躺了三十个批次，
直到 Batch 163 普查才发现它的排除理由整个是错的。
**这与 Batch 161 的覆盖度表同源：空位不可怕，没登记的空位才可怕**——
因为「以为有人管」和「确实有人管」在账面上长得一模一样。

本闸因此增加一条**双向完整性检查**：账本里每一条 `status: excluded`，
要么在 `COVERED` 登记表里（有专属判据），要么在 `EXEMPT` 登记表里（有免检理由），
**两者都没有即报错**；反过来登记表里有、账本里已不是 excluded 的，也报错
（免检表只增不减，几年后又是一张没人敢碰的清单）。

本闸把条件中**可机械判定**的四条拿上游现状逐条比对：
  1. `/agent/*` 路由仍未注册          → cloud-agent / agent-memory-skills 未解禁
  2. `MediaConversion`/`Frame`/`Script` 仍在 `developingNodeTypes` → local-runtime
     的「智能剪辑」节点入口仍关闭
  3. 本地运行时二进制不在仓库内      → local-runtime 无法起服
  4. `isLocalWorkspaceMode()` 仍是无条件 `return true`，且 `LocalAwareProjectRoute`
     的重定向分支仍排在渲染分支之前 → short-drama-project-workbench（短剧/小说
     转视频生产台）仍不可达

第 5 条（真实生成产生版本族）属于付费边界，**不可机械判定**，脚本不检查。

Batch 222 再加第 6 条方向：**账本自述的证据降级，读者必须能在那一页上看到。**
它与本闸已有的「理由完整性」同族而不同层——后者核「理由**写没写**」，
本条核「理由**有没有到达读者眼前**」。理由写在账本里、而页面通篇是确定结论，
**读者会把证据最弱的部分和已截图的部分当成同一种可信度**（纪律 229）。

退出码：0 条件全部仍成立；1 有条件已失效。

⚠️ 上面那句「不可机械判定」**过去只是写在文档里的一句话**——`media-versions` 至少
在 docstring 里被提到过，而 `art-critique` 连提都没提。现在它变成 `EXEMPT` 登记表里
**逐条登记的一行**，漏登记会直接让本闸失败。
"""

import os
import re
import sys
import subprocess
import beefsrc
from baseline import announce_fallback
from baseline import resolve_ref, BaselineError, baseline_guard
from batchread import read_many

try:
    import yaml
except ImportError:  # 完整性检查需要它；缺失时按「未能核对」处理，不静默放行
    yaml = None

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ── 完整性登记表（Batch 164 新增） ────────────────────────────────────
# 键必须是账本 `task-inventory.yml` 里真实的 task id；两侧对不上即报错。
COVERED = {
    "cloud-agent": "条件 1：/agent/* 路由仍未注册",
    "agent-memory-skills": "条件 1：/agent/* 路由仍未注册",
    "local-runtime": "条件 2 + 条件 3：节点仍在 developingNodeTypes；运行时二进制仍不在仓库",
    "short-drama-project-workbench": "条件 4：isLocalWorkspaceMode() 仍无条件 true，"
                                     "且重定向分支仍早于 ProjectDetailPage 渲染分支",
}

# 免检不是「不管」，是「管不了所以写明为什么」。**新增 excluded 任务时必须在这里
# 或 COVERED 里留一条**，否则本闸失败——这正是 art-critique 当初腐烂却无人知晓的原因。
EXEMPT = {
    "media-versions": "版本族需真实生成才能产生，属付费边界，不机械判定",
    "art-critique": "一次批改最多 9 次模型调用（ART_CRITIQUE_MAX_MODEL_CALLS=9），"
                    "属付费边界，不机械判定。Batch 164 补登记——此前它从未被本闸提及，"
                    "而闸名却让人以为它在管（其排除理由本身已在 Batch 163 订正）",
}

# 可机械判定的条件清单。**它同时被两处用到**：结论里报数量，以及下面那条自检。
# 写成列表而不是一个孤零零的数字，是为了让「数量」和「是哪几条」不可能各说各话。
MECHANICAL_CONDITIONS = (
    "条件 1：/agent/* 路由仍未注册",
    "条件 2：节点仍在 developingNodeTypes",
    "条件 3：本地运行时二进制仍不在仓库",
    "条件 4：短剧/小说生产台仍不可达",
)

CONDITION_MARKER = "# —— 条件 "


def condition_blocks():
    """数一遍本文件里真正写了判据的条件块（以 `# —— 条件 N：` 注释起头）。"""
    try:
        with open(os.path.abspath(__file__), encoding="utf-8") as f:
            src_text = f.read()
    except OSError:
        return None
    return len(re.findall(re.escape(CONDITION_MARKER) + r"\d+：", src_text))



AGENT_BRANCH = "origin/codex/agent-product-v1610-20260928"

ROUTE_RE = re.compile(r'(?:GET|POST|PUT|DELETE|PATCH)\("([^"]+)"')


def find_source():
    """**Batch 197：路径解析收敛到 `beefsrc` 单一来源**（含"是否走了兜底"）。

    原先这里各带一张 `CANDIDATES` 表，判真条件还不一样
    （本组问 `isdir(c/"backend")`，`quote-punct`/`shot-drift` 问 `isdir(c/".git")`），
    **而 `baseline.py` 又是第三种**——同一个 `BEEFTV_SRC` 在不同闸里会解析成不同的仓。
    实测缺陷：`.git` 目录式判真在 **git worktree 上必然失败**（那里 `.git` 是文件），
    于是用户显式指定的路径被**静默忽略**、改用兜底那份，而闸一声不吭。
    """
    src, is_fallback = beefsrc.resolve_src()
    if src is None:
        return None
    if is_fallback:
        # **Batch 202：措辞收敛到 `baseline.announce_fallback`**——
        # 纪律 172 要 15 道闸都说出「我读的是哪一份」，
        # **而这份措辞不该被手写 8 遍**（又一次「同一份事实被手写多遍」）。
        announce_fallback()
    return src


def git_show(src, ref, path):
    r = subprocess.run(["git", "show", f"{ref}:{path}"],
                       cwd=src, capture_output=True, text=True)
    return r.stdout if r.returncode == 0 else ""


def git_ls(src, ref):
    r = subprocess.run(["git", "ls-tree", "-r", ref, "--name-only"],
                       cwd=src, capture_output=True, text=True)
    return r.stdout.split("\n") if r.returncode == 0 else []


def excluded_ids(root):
    """账本里所有 `status: excluded` 的 task id。"""
    if yaml is None:
        return None
    path = os.path.join(root, "task-inventory.yml")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    items = data if isinstance(data, list) else (data or {}).get("tasks", data)
    if isinstance(items, dict):
        items = list(items.values())
    out = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("status", "")) == "excluded":
            tid = item.get("id")
            if tid:
                out.append(str(tid))
    return out


def check_reasons(root):
    """每条 excluded 都必须写 `exclusion_reason`（Batch 187 新增）。

    **为什么这条必须存在**：覆盖完整性检查只核「每条 excluded 有没有被 COVERED / EXEMPT
    认领」——**认领的是「有没有东西在看它」，不是「它的理由写没写」**。
    于是一条 excluded 可以被完整地看守着、闸门全绿，**而账本里根本没有它的排除理由**。

    **上线首跑就抓到真缺陷**：`art-critique` 的理由写在 **`review_note`** 里，
    而**没有任何脚本读那个字段**（`exclusion_reason` 才是反验的锚点）。
    它偏偏又是全 6 条里**理由变化最大**的一条——
    `review_note` 里明写「**创建入口已不再是排除理由**」（Batch 163 运行时已证伪入口不存在），
    **而按 `exclusion_reason` 读的人会以为这条根本没有理由。**

    **判据刻意不判「理由写得好不好」**——那不可机械判定。只判：
      · 字段存在；
      · 去掉空白后非空；
      · 长度 ≥ 12 字（短于这个的多半是写了个标题而不是理由）。
    **报的时候把「它实际用了哪个字段」一并打出来**，因为本条缺陷的性质正是
    「写在了别处」，只报「缺字段」会让人去新建一个字段而不是去找原来那个。
    """
    if yaml is None:
        return ["未能读取 task-inventory.yml（缺 PyYAML），理由完整性本轮未核对"], True
    path = os.path.join(root, "task-inventory.yml")
    if not os.path.isfile(path):
        return ["task-inventory.yml 不存在"], True
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    items = data if isinstance(data, list) else (data or {}).get("tasks", data)
    if isinstance(items, dict):
        items = list(items.values())

    problems = []
    for item in items or []:
        if not isinstance(item, dict):
            continue
        if str(item.get("status", "")) != "excluded":
            continue
        tid = item.get("id") or "?"
        reason = item.get("exclusion_reason")
        text = " ".join(str(reason).split()) if reason is not None else ""
        if text and len(text) >= 12:
            continue
        # 报「实际写在了哪个字段」——本条缺陷的性质是「写在了别处」
        elsewhere = [k for k in ("review_note", "note", "comment", "remark")
                     if item.get(k)]
        where = ("，而它写在了 `%s`（**没有任何脚本读那个字段**）" % "`, `".join(elsewhere)
                 if elsewhere else "，且账本里找不到任何替代字段")
        problems.append(
            f"{tid}：excluded 却没写 exclusion_reason"
            f"（{len(text)} 字{where}）——**它被完整地看守着，闸门全绿，"
            f"而接手的下一个人看不到它为什么被排除**")
    return problems, False


def check_coverage(root):
    """双向完整性检查。返回 (problems, notes, unverifiable)。

    正向：账本里每条 excluded 必须在 COVERED 或 EXEMPT 里，否则**没有任何东西在看它**。
    反向：登记表里有、账本里已不是 excluded 的，属于过期条目——免检表只增不减
          就会变成一张「什么都免检、谁都不敢碰」的表（与 Batch 162 的截图豁免表同理）。

    unverifiable=True 表示**账本读不到**。按 Batch 160 立的三段退出码，
    这必须报成「未能核对」（2）而不是「核对不一致」（1）——后者会让人跑去手册里
    找根本不存在的问题，正是 Batch 160 修掉的那个坑。
    """
    ids = excluded_ids(root)
    if ids is None:
        return ([], [], True)

    problems, notes = [], []
    known = set(COVERED) | set(EXEMPT)
    unregistered = [i for i in ids if i not in known]
    if unregistered:
        problems.append(
            f"账本里有 {len(unregistered)} 条 excluded 任务未被本闸认领（COVERED/EXEMPT 都没有）："
            f"{', '.join(unregistered)} → 它们既没有专属判据、也没写明为何免检，"
            f"闸名却让人以为全部 excluded 都被盯着"
        )
    stale = sorted(known - set(ids))
    if stale:
        problems.append(
            f"登记表中已不再 excluded 的条目（过期登记）：{', '.join(stale)} → "
            f"清理它们，或确认账本里的 status 是否被误改"
        )
    if not unregistered and not stale:
        notes.append(
            f"excluded 覆盖完整性：账本 {len(ids)} 条，全部已认领"
            f"（有判据 {len([i for i in ids if i in COVERED])} 条 / 登记免检 {len([i for i in ids if i in EXEMPT])} 条）"
        )

    # 条件块数 vs 清单长度——**两者一旦对不上，「全部核对过」这句话就是假的**。
    # 本批的起因正是「一个写死的数字悄悄过期」，这里把同一类变成自检。
    blocks = condition_blocks()
    if blocks is None:
        problems.append("未能读取本脚本自身，条件块计数本轮未能核对")
    elif blocks != len(MECHANICAL_CONDITIONS):
        problems.append(
            f"条件清单与实际判据块数不符：MECHANICAL_CONDITIONS 列了 {len(MECHANICAL_CONDITIONS)} 条，"
            f"而本文件里实际有 {blocks} 个「# —— 条件 N：」判据块 → "
            f"结论里的条件数会报错，且新增的条件可能根本没进清单"
        )
    else:
        notes.append(f"条件清单自洽：{blocks} 个判据块与 MECHANICAL_CONDITIONS 条目一致")
    return (problems, notes, False)


# ── 降级自述 → 页面告知（Batch 222 新增）────────────────────────────────
# 纪律 228：账本里写着的「哪一部分没验证」，必须出现在读者能读到的那一页上。
#
# **输入侧刻意窄**：只认作者原话里的**否定式缺失声明**（只有源码 / 未取证 /
# 没有运行时…），不推断语气。「页面所有断言均有运行时或源码证据」这类
# **正向的证据构成陈述不算**——实测把它们算进去，14 个输入里会有 2 个变成
# 假阳性（`readonly-canvas` 与 `concepts-architecture` 说的「源码证据」是
# 「证据里有静态成分」，不是「有东西没验证」）。判据一旦误报，人就会开始整段忽略它。
#
# 同理「六内置插件清单**为**源码证据」也不入面：「为」是陈述来源，
# 而入面的是**声明缺失**的「只有 / 仅有 / 未 / 没有 / 无」。这条线是有意的。
DOWNGRADE_TERMS = (
    "只有源码", "仅有源码", "只基于源码", "仅基于源码",
    "无运行时", "没有运行时", "未取证", "未能走查", "没有走查",
    "未在真实", "尚未在真实", "未运行时验证", "未做运行时", "没有实测",
    "未走查", "未验证", "未核实",
)

# 页面侧词表取**宽**——宁可漏检不可误报。
# **而「宽」在这一侧有实测代价，必须记下来**：第一版把「受限」「空」这类泛词
# 算进清单，结果 `asset-library` 这个真缺陷被两条毫不相干的语境双双遮住——
# 「素材库**空**态」（那是一句截图 alt 文字）和「画布库那套还额外**受限**于服务端
# 压根没有画布文件夹这个概念」——判据报了绿。**泛词一律不进清单**，
# 而判据的鉴别力由反验用例一正一反钉死。
PAGE_TELL_TERMS = (
    "未验证", "未核实", "未走查", "未能走查", "没有走查", "未在真实", "尚未在真实",
    "无运行时", "没有运行时", "只基于源码", "仅基于源码", "只有源码", "仅有源码",
    "源码证据", "静态证据", "没有实证", "无实证", "未实测", "未确认",
    "没有入口", "不会上传到", "不可用", "不可达",
    # 下面三个是**上线首跑当天补的**，不是事后想起来的：判据第一次真跑就报
    # `asset-library` 缺告知，而那一页其实已经写了「下面三条依据是**读源码
    # 推出来的**，不是运行时观测」——**词表没有「读源码」这三个字**。
    # 即：判据上线**当天**就有一次真实误报，**靠的是它自己会喊**。
    # 补完复查全库 35 个页面，唯一变化是 asset-library 从「缺」变「已告知」，
    # 其余 34 个状态不变（**没有顺手放宽到别的页面上**）。
    "读源码", "源码推导", "源码结论", "非运行时", "未在界面",
    # 这三个同样是读原文补的：`cloud-agent` / `agent-memory-skills` 的页首写的是
    # 「当前状态（v1.6.x **源码核查**）」，`timeline-editing` 写的是「本节数值**取自源码**」。
    # **判据报「缺」而页面上明明写着，不是因为页面没告知，是因为判据只认一种措辞**——
    # 这与「输入匹配不到判据就等于不存在」（纪律 216）是同一个病的两种长相。
    "源码核查", "取自源码", "源码推演",
)


def _inventory_items(root):
    """读账本任务表。**读不到时返回 `None`，而 `None` 绝不等于「空账本」。**

    纪律 216：判据的输入若匹配不到，它就等于不存在。「账本里 0 个任务」
    与「账本读不出来」在下游会长得一模一样，所以这里必须让两者可区分——
    前者该报不一致，后者只能报「未能核对」。

    **不复用 `excluded_ids`**：那个函数只吐出 `status: excluded` 的 id，
    而本方向要看**全部 35 条**（降级自述不限于 excluded——Batch 221 命中的
    `storage-quota` 恰恰是 verified）。共用一个只能筛 excluded 的函数，
    等于把「账本有哪些任务」和「哪些任务被排除」两件事混成一个。
    """
    if yaml is None:
        return None
    path = os.path.join(root, "task-inventory.yml")
    if not os.path.isfile(path):
        return None
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f)
    items = data if isinstance(data, list) else (data or {}).get("tasks", data)
    if isinstance(items, dict):
        items = list(items.values())
    items = [i for i in (items or []) if isinstance(i, dict)]
    return items or None


def _task_selftext(item):
    """作者在账本里为这个任务写下的全部自述文本。

    **降级声明落在哪个字段是不固定的**——`art-critique` 的理由当年就写在
    没人读的 `review_note` 里（Batch 187）。所以这里读全部已知字段，
    而不是只挑一个「标准字段」。
    """
    parts = []
    for key in ("exclusion_reason", "review_note", "review_condition"):
        if item.get(key):
            parts.append(str(item[key]))
    ev = item.get("evidence")
    if isinstance(ev, list):
        for e in ev:
            if isinstance(e, dict) and e.get("note"):
                parts.append(str(e["note"]))
    return "\n".join(parts)


def check_downgrade_reaches_page(root):
    """账本自述的证据降级，读者必须能在那一页上看到它。返回 (problems, notes, unverifiable)。

    **为什么这条必须存在**：`check_reasons` 是同族的前一条，它核的是
    「排除理由**写没写**」；而本条核的是理由**有没有到达读者眼前**。
    两者之间隔着一整条没人走的路——**账本里写着的、只有记账的人看得见的降级**。
    实测：这类页面读起来和已截图的页面一样确定，因为**证据最强与最弱的
    部分并排出现时，读者只会按最强的那部分理解整页**（纪律 229）。

    **页面上任何一个告知词就算过**——本方向刻意不判「告知写得够不够好」，
    那是不可机械判定的事。判据只回答「有没有说」。
    """
    items = _inventory_items(root)
    if items is None:
        return ([], [], True)

    problems, notes = [], []
    downgraded = told = 0
    for item in items:
        tid = item.get("id") or "?"
        hits = sorted({t for t in DOWNGRADE_TERMS if t in _task_selftext(item)})
        if not hits:
            continue
        downgraded += 1
        pages = item.get("manual_pages") or []
        if not pages:
            problems.append(
                f"{tid}：账本自述证据降级（命中 {', '.join(hits)}）却没登记 manual_pages → "
                f"**读者在手册里找不到任何一页能看到这条说明**，而下一个人只会从页面上读"
            )
            continue
        bodies, unreadable = [], []
        for p in pages:
            path = os.path.join(root, p)
            if not os.path.isfile(path):
                unreadable.append(p)
                continue
            with open(path, encoding="utf-8") as f:
                bodies.append(f.read())
        if unreadable:
            # 页面读不到 = **未能核对**（2），不是「核对不一致」（1）——
            # 后者会让人跑去手册里找根本不存在的问题（Batch 160）。
            return ([], [], True)
        if any(any(t in b for t in PAGE_TELL_TERMS) for b in bodies):
            told += 1
            continue
        problems.append(
            f"{tid}：账本白纸黑字自述「{', '.join(hits)}」，"
            f"而 {', '.join(pages)} 上找不到任何对应的告知 → "
            f"**证据最弱的那部分只有记账的人看得见**，"
            f"读者会把它和同页已截图的部分当成同一种可信度"
        )
    notes.append(
        f"证据降级告知：账本自述降级 {downgraded} 条，其中 {told} 条已在手册页面上告知读者"
        f"（判据只核「有没有说」，不核「说得够不够好」）"
    )
    return (problems, notes, False)


@baseline_guard
def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过 excluded 条件核对")
        return 2
    ref = resolve_ref()

    problems = []
    notes = []
    unverifiable = False

    # —— 完整性检查（不需要上游源码也能跑，所以放在最前面）——
    cov_problems, cov_notes, unverifiable = check_coverage(ROOT)
    problems += cov_problems
    notes += cov_notes
    if unverifiable:
        print("[skip] 未能读取 task-inventory.yml，excluded 覆盖完整性本轮未能核对")

    # —— 理由完整性（Batch 187）：被认领 ≠ 写了理由 ——
    reason_problems, reason_unverifiable = check_reasons(ROOT)
    problems += reason_problems
    if reason_unverifiable:
        print("[skip] 未能读取 task-inventory.yml，excluded 理由完整性本轮未能核对")

    # —— 降级自述是否到达读者眼前（Batch 222）：写了理由 ≠ 读者看得到 ——
    # 上一条 `reason_unverifiable` **只打印、不参与退出码**（Batch 187 遗留）。
    # **本方向不复制这个疏漏**：读不到页面时它必须能把 rc 抬到 2，
    # 否则「没核对成」和「核对过且一致」在账面上完全一样。
    dg_problems, dg_notes, dg_unverifiable = check_downgrade_reaches_page(ROOT)
    problems += dg_problems
    notes += dg_notes
    if dg_unverifiable:
        unverifiable = True
        print("[skip] 未能读取账本或手册页面，证据降级告知本轮未能核对")

    # —— 条件 1：/agent/* 路由仍未注册 ——
    # **Batch 181 改**：原先是 `for f in git_ls(...): git_show(src, ref, f)`，
    # 即**每个 backend 文件一次 `git show` 子进程**——实测 347 个非测试 .go、
    # 单次 25ms → **闸门本体约 9 秒**（反验 5 例就是 35.6 秒）。
    # 改成 `batchread.read_many`：**两次进程调用取代 347 次**，
    # 实测 0.19 秒且与逐个 `git show` **逐字节一致**（抽样 40 个零差异）。
    go_files = [f for f in git_ls(src, ref)
                if f.startswith("backend/") and f.endswith(".go")
                and not f.endswith("_test.go")]
    routes = set()
    for f, body in read_many(src, ref, go_files).items():
        # 批量读回的是 **bytes**（按 size 精确切分的前提），而 ROUTE_RE 是字符串正则。
        # **必须显式解码**——顺带说明为什么不能用 `text=True`：
        # 走 text 就得编解码往返，而「切出来的正好是 size 字节」这件事只在 bytes 上成立。
        for m in ROUTE_RE.finditer(body.decode("utf-8", "replace")):
            routes.add(m.group(1))
    agent_routes = sorted(r for r in routes if "agent" in r)
    if agent_routes:
        problems.append(
            f"/agent 相关路由已注册 {len(agent_routes)} 条（{', '.join(agent_routes[:3])}）"
            f" → cloud-agent / agent-memory-skills 的解禁条件可能已满足，需回走验证"
        )
    else:
        notes.append("cloud-agent / agent-memory-skills：/agent/* 仍未注册，条件成立")

    # —— 条件 2：智能剪辑等节点仍在 developingNodeTypes ——
    avail = git_show(src, ref, "web/src/lib/canvas/canvas-feature-availability.ts")
    if not avail:
        notes.append("未取到 canvas-feature-availability.ts，节点解禁条件本轮未判定")
    else:
        if "developingNodeTypes" in avail and "MediaConversion" in avail:
            notes.append("local-runtime：MediaConversion 仍在 developingNodeTypes，"
                         "「智能剪辑」入口仍关闭，条件成立")
        else:
            problems.append(
                "MediaConversion 已不在 developingNodeTypes 内 → 「智能剪辑」"
                "节点可能已开放，local-runtime 需回走验证"
            )

    # —— 条件 3：本地运行时二进制不在仓库 ——
    files = git_ls(src, ref)
    binary_hits = [
        f for f in files
        if re.search(r"framefield[-_]?local[-_]?runtime|local-runtime\.(exe|dmg|deb|rpm|AppImage)$", f, re.I)
    ]
    if binary_hits:
        problems.append(
            f"本地运行时二进制疑似已入仓 {len(binary_hits)} 条（{', '.join(binary_hits[:3])}）"
            f" → local-runtime 的「无法起服」条件可能已解除"
        )
    else:
        notes.append("local-runtime：运行时二进制仍不在仓库内，本机无法起服，条件成立")

    # —— 条件 4：短剧/小说生产台仍不可达 ——
    # 判据是两段源码同时成立：isLocalWorkspaceMode 无条件 true（LocalAwareProjectRoute
    # 必走重定向分支），且重定向分支排在 ProjectDetailPage 渲染分支之前。
    wsm = git_show(src, ref, "web/src/services/workspace-mode.ts")
    router = git_show(src, ref, "web/src/router.tsx")
    if not wsm or not router:
        notes.append("未取到 workspace-mode.ts / router.tsx，短剧生产台解禁条件本轮未判定")
    else:
        m = re.search(r"export function isLocalWorkspaceMode\s*\(\s*\)\s*\{(.*?)\n\}", wsm, re.S)
        body = m.group(1) if m else ""
        # 无条件 true = 函数体里既没有条件分支，也没有 return false
        hardcoded_true = bool(m) and "return true" in body and "return false" not in body \
            and not re.search(r"\bif\b|\?|&&|\|\|", body)
        nav_pos = router.find('<Navigate to={`/canvas/${projectId}`} replace />')
        render_pos = router.find("deferred(<ProjectDetailPage />)")
        nav_first = nav_pos != -1 and render_pos != -1 and nav_pos < render_pos
        if hardcoded_true and nav_first:
            notes.append("short-drama：isLocalWorkspaceMode() 仍无条件 return true，"
                         "且项目路由仍先重定向回画布，生产台不可达，条件成立")
        else:
            detail = []
            if not hardcoded_true:
                detail.append("isLocalWorkspaceMode() 已出现条件分支")
            if not nav_first:
                detail.append("重定向分支不再早于 ProjectDetailPage 渲染分支")
            problems.append(
                "短剧/小说转视频生产台的不可达前提已变（" + "；".join(detail) + "）"
                " → short-drama-project-workbench 需回走验证"
            )

    # —— 附注：Agent 分支合流进度（只报告，不作为判据）——
    r = subprocess.run(["git", "rev-list", "--count", f"{ref}..{AGENT_BRANCH}"],
                       cwd=src, capture_output=True, text=True)
    if r.returncode == 0 and r.stdout.strip():
        n = r.stdout.strip()
        notes.append(f"Agent 分支仍领先 main {n} 个提交（未合流）" if n != "0"
                     else "Agent 分支已完全合流 main")

    for n in notes:
        print("  " + n)
    if problems:
        print(f"excluded 解禁条件核对：{len(problems)} 条可能已失效")
        for p in problems:
            print("  ⚠ " + p)
        return 2 if unverifiable else 1

    # 计数从登记表推导，**不再写死**——写死的那句「4 条」在账本涨到 6 条时
    # 会安静地继续说 4，读起来像是「全都查过了」的样子。
    print(f"excluded 解禁条件核对：{len(COVERED)} 个任务共 {len(MECHANICAL_CONDITIONS)} 条可机械判定的条件全部仍成立"
          f"（另有 {len(EXEMPT)} 条已登记免检：{', '.join(sorted(EXEMPT))}——付费边界，不机械判定）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
