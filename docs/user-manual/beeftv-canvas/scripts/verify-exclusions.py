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
**Batch 223/224 两度扩面**：Batch 223 补上第五个自述字段 `finding`
（两处「付费红线」只写在它里）与「动作没发生」这一类降级词；
Batch 224 补上「基于 / 为 / 维持 源码证据」这一族，并用**排除式规则**
把「所有断言均有…或…」这种**全覆盖声明**挡在门外——
**因为那两句话意思相反，而它们在账本里只差主语一个词**。
**判据认领的任务因此从 4 条增到 14 条。**

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
from headingkey import is_atx_heading

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
    # Batch 223 补的这一组是**另一类**降级：前面几条说的都是「证据形态」
    # （只有源码 / 没有运行时），这组说的是「**动作没发生**」——
    # 「未触发任何真实生成」「未配置任何 Provider Key」「提交未执行」。
    # **这一类恰恰是本手册最常见的降级**，因为付费红线每天都在拦着取证。
    # 逐个量过：全库「未触发」「未发起」「未执行」「未配置」**各只出现 1 处**，
    # 且全部是「本手册的取证边界」用法，**没有一处是「用户还没配模型」那种歧义义**。
    "未触发", "未发起", "未执行", "未配置",
    # Batch 224 补的这一族是**「陈述某一部分的证据来源」**：主语是
    # 「页面 / 某小节 / 某清单 / 某组参数」，谓语是「基于 / 为 / 维持 源码证据」。
    # **它们是货真价实的降级声明，而否定式词表一条都认不出**
    # ——全库 5 处真降级长这样，一处都没进过判据的视野。
    "页面基于源码", "为源码静态证据", "为源码证据", "维持源码证据",
)

# **排除式规则**：与上面那族配套，缺了它这族就会带进 2 个假阳性。
# 实测（Batch 224）全库 16 处「源码证据」类表述里，**8 处是真降级**
# （主语是某一部分），**2 处是假阳性**：
#   · `readonly-canvas`：「页面**所有断言均有**运行时**或**源码证据」——全覆盖声明
#   · `concepts-architecture`：「回走等价于内容**与**源码证据**一致性审查**」——审查方式
# **区别是可机械的**：假阳性那两句都带「全部/所有/均」并接「或」或「一致性审查」。
# 所以本正则**只放过真正的「有一部分只有源码」**，不放过「所有部分都有证据」。
DOWNGRADE_ABSOLUTE_RE = re.compile(r"(?:全部|所有|均)[^。；\n]{0,40}?或|一致性审查|一致性对账")

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
    # Batch 223 补的**取证边界声明**——「动作没发生」类降级在页面上的对应说法。
    # **这组词是被假阳性逼出来的，而假阳性来自一个更普泛的候选**：
    # 先试了裸的「停在」，全库 4 个页面命中，**逐处读原文发现 3 处是假阳性**
    # （「恒定**停在**默认值」「鼠标悬**停在**节点边缘」「默认**停在**视频模式」——
    #  **全是 UI 描述，没有一处是取证边界**）。与 Batch 222 的「受限」「空」同一个病。
    # 换成精确短语后**只有 1 个页面状态变化、零误判**。
    "实测都停在", "实测止于", "取证止于", "止于付费边界",
    "不触发真实生成", "不发真实", "不发起真实请求", "不产生费用",
    # Batch 238 补的**一个**：`90-troubleshooting.md` 第 3 行写的是
    # 「症状 → 原因 → 处理。**按真实源码行为整理**」，而账本记的是
    # 「其余失败分类为源码静态证据」——**那一页确实告知了，只是没登记这个说法**。
    # **这不是「放宽到能过」**：本条方向自己的报错文案就写着「词表必然不完备」，
    # 而补进来的措辞必须**本来就写在页面上**。反验用例钉住了这一点。
    "按真实源码",
)


#: **证据来源词**（Batch 238 新增）。收紧本方向的关键就是它。
#: 向读者交代本手册证据等级的那句话，**必然同时在说证据是什么**；
#: 而产品手册里「未验证 / 不可用 / 未确认」绝大多数说的是**产品自己**的状态。
#: **只收「只用于交代本手册证据等级」的那几个**，一个泛词都不收——
#: Batch 222 的「受限」「空」、Batch 223 的「停在」都是收泛词收出来的假阳性。
#: **刻意不收「证据」二字**：`90-troubleshooting.md` 里那句
#: 「保留错误来源与**请求证据**」说的是产品的错误报告功能，不是本手册的证据。
EVIDENCE_SOURCE_TERMS = (
    "源码", "运行时", "实证", "实测", "走查", "取证", "核验", "截图",
)

#: 表格行与标题行是**产品文案密度最高**的两种行：状态值、字段取值、
#: 错误分类、报错原文都长这样。Batch 238 实测的假阳性**全部落在这两种行里**。
TABLE_ROW_RE = re.compile(r"^[ \t]{0,3}\|")
#: **Batch 252 改掉了上一行原本的 `^\s*\|`**：那个 `\s*` **同样吃全角空格、
#: 且不限个数**，于是**前导 4 个空格的行也被当成表格行排除**——
#: **而那在 GFM 里是代码块，读者看得见**
#: （实测：`    | 位置 | 上限 |` 渲染成 `<pre>`，不是表格）。
#: 后果是**告知写在代码块里时会被判成「没写」**。
#: 真树实测 15 行分歧，**全在 `AUDIT.md`**（台账，不在本方向的读取范围内），
#: **所以真树零影响**——**缺口靠用例钉，不靠现场数据兜**。
#:
#: **为什么这一条不与闸 8 的 `cells()` 共用**（纪律 274 推论一的边界）：
#: 闸 8 判的是「**一整块**是不是表格」，它要解析分隔行、数格数；
#: 本处判的是「**单行**是不是表格行」，只需要行首形态。
#: **两个是不同的问题，共用会把其中一个问坏**——共享的是概念（GFM 表格行的
#: 开头形态），不是函数。
#: **Batch 251 删掉了这里原本的 `HEADING_RE = re.compile(r"^\s{0,3}#{1,6}\s")`，
#: 改用 `headingkey.is_atx_heading`**——那是「什么算标题」的唯一一份实现
#: （纪律 274 推论一；闸 26 / 29 / 9 都已经在用它了）。
#: **旧式有两类错，一类朝一个方向、另一类朝另一个方向**（Batch 251 用
#: vitepress 1.6.4 逐条量过，30 种形态）：
#:   · `\\s` **匹配全角空格** → `##　标题`、`#　标题`、`　## 标题` 被当成标题行
#:     **排除**，而**渲染器给的是零个标题**——那是**读者看得见的普通段落**。
#:   · 前导空白不限 3 个 → `    ## 标题`（4 空格）、`\t## 标题`（制表符）
#:     也被当成标题行排除，**而渲染器把它们当代码块**。
#: **方向相反这件事本身就是个提醒**：全角空格那一类在 Batch 248 已经被
#: `headingkey` 修掉了，**而闸 5 的这份拷贝没跟着改**——
#: **修好一条规则不等于认全了另一条，也不等于每一处拷贝都修过了。**


def _tell_qualifying_lines(body):
    """返回这一页里**真正算告知**的行号。

    **本方向量的是「有没有说」，而第一版把「有没有说」算成了
    「整页正文里有没有出现过某个词」**——这两件事不一样：
    页面里绝大多数「不可用 / 未确认 / 未验证」说的是**产品**的状态，
    而 Batch 238 实测到 `organize-canvas` **页面上一个证据告知都没有**，
    它是被三张产品表格里的「资产当前不可用」「尚未确认」顶替通过的
    （而那一页第 78 / 80 行就摆着两张实拍截图——纪律 229 的形状）。

    三条限定都能从被核对象自己算出（纪律 242）：
      1. 不是表格行；2. 不是标题行；
      3. **同一行还必须出现一个证据来源词**。

    **它仍然分不开的**：一段**恰好同时含证据来源词和产品状态词**的产品文案。
    本方向量的是位置与共现，不是意图——**能力上限如实写在这里，不装作覆盖了**。
    """
    out = []
    for i, line in enumerate(body.split("\n")):
        if TABLE_ROW_RE.match(line) or is_atx_heading(line):
            continue
        if not any(t in line for t in PAGE_TELL_TERMS):
            continue
        if not any(w in line for w in EVIDENCE_SOURCE_TERMS):
            continue
        out.append(i + 1)
    return out



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
    # **Batch 223 补 `finding`**：它承载着一批次的实测发现，而**两处「付费红线」
    # 自述只写在它里面**（`create-workspace` 的「未触发任何真实生成」、
    # `model-channels` 的「未配置任何 Provider Key」）。前四个字段全都没有这两句，
    # **所以这不是词表没覆盖，是字段根本没进读取范围**——
    # 而读不到字段的判据，与不存在的判据在账面上完全一样。
    for key in ("exclusion_reason", "review_note", "review_condition", "finding"):
        if item.get(key):
            parts.append(str(item[key]))
    ev = item.get("evidence")
    if isinstance(ev, list):
        for e in ev:
            if isinstance(e, dict) and e.get("note"):
                parts.append(str(e["note"]))
    return "\n".join(parts)


def _task_sentences(item):
    """作者自述**按句拆开**——Batch 224 起降级判定是句级的，不是整段级的。

    **为什么必须是句级**：排除式规则要挡的是「**这一句**是全覆盖声明」，
    而同一个字段里完全可能上一句在声明降级、下一句在写「均已覆盖」。
    整段判定会让排除规则误伤同段里真正的降级声明。
    """
    text = _task_selftext(item)
    return [t.strip() for t in re.split(r"[。；\n]", text) if t.strip()]


def _downgrade_hits(item):
    """这个任务的账本里，作者**声明了哪些部分的证据降级**。返回命中词列表。"""
    hits = set()
    for sent in _task_sentences(item):
        if DOWNGRADE_ABSOLUTE_RE.search(sent):
            continue
        for t in DOWNGRADE_TERMS:
            if t in sent:
                hits.add(t)
    return sorted(hits)


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
        hits = _downgrade_hits(item)
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
        told_lines = [ln for b in bodies for ln in _tell_qualifying_lines(b)]
        if told_lines:
            told += 1
            continue
        # **措辞必须说清判据知道什么、不知道什么**：词表必然不完备
        # （Batch 222 就在上线当天误报过一次），所以本闸能证明的只是
        #「**没找到已登记的告知措辞**」，**不能断言「页面上没写」**。
        # 早先这里写的是「找不到任何对应的告知」，读起来像后者——
        # **而那会让下一个人去改词表时以为已经证明了页面没写。**
        problems.append(
            f"{tid}：账本白纸黑字自述「{', '.join(hits)}」，"
            f"而 {', '.join(pages)} 上**找不到任何已登记的告知措辞**"
            f"（词表不完备——这不等于页面上没写，但足以说明该页至少没在说） → "
            f"**证据最弱的那部分很可能只有记账的人看得见**，"
            f"读者会把它和同页已截图的部分当成同一种可信度"
        )
    notes.append(
        f"证据降级告知：账本自述降级 {downgraded} 条，其中 {told} 条已在手册页面上告知读者"
        f"（判据只核「有没有在交代证据的位置上说」，不核「说得够不够好」；"
        f"表格行与标题行里的产品文案、以及未与证据来源词同现的词，**都不算**）"
    )
    return (problems, notes, False)


# ── 逐节祈使句（Batch 226 新增，方向七）────────────────────────────────
# **纪律 129 说「分层要逐节做」，而本方向是它的最后一道**：页首那句
# 「下面写的是历史机制」只能护住**从上往下读**的人。
# **读者从浏览器 Ctrl+F 搜到「打开云 Agent 面板」、或从右侧页内目录点进
# 「## 发起与对话」时，那一句会被单独送到眼前，页首声明不会跟着出现。**
# 实测 4 个 excluded 页面里命中 2 处：
#   · `cloud-agent.md`「## 发起与对话」四条全是祈使句（打开/执行/插话/状态）
#   · `agent-memory-skills.md`「## 技能（Skills）」首句是「1. 安装技能：…」
# 而 `media-versions.md` 全部小节首句都是陈述句、**不误导**——
# **所以这不是「所有 excluded 页都要加提示」，是「祈使句才需要就地提示」。**
#
# **不查的**：①不是 excluded 的页（判据要的是「不可用页里的祈使句」这个组合）；
# ②小节内**已有**任何提示词的情形（就地提示已经写过了，再报就是逼人写第二遍）。
SECTION_IMPERATIVE = re.compile(
    r"^\s*(?:[-*]\s*|\d+[.、]\s*)?"
    r"(打开|点击|点选|按|选择|勾选|新建|创建|上传|下载|导出|导入|复制|拖出|拖|输入|进入|切到|切换|双击|右键"
    r"|安装|卸载|添加|移除|保存|取消|确定|重试|刷新|编辑|移动|排序|过滤|筛选|定位|展开|收起|设置|绑定|解绑)"
    r"(?!后|前|时|完|了|成功|失败)"
)
#: **上面那个否定前瞻是实测逼出来的，不是一开始想到的。**
#: 首跑把 `00-quickstart.md` 的「**创建后**画布中间是空的」判成了祈使句——
#: 「创建后」是**完成态描述**，而这一页根本不是不可用页。上线首跑就误报，
#: **又一次是判据自己喊出来的**（纪律 230 的那个模式，隔了几批又重演）。
#: 全库这类措辞实测 **8 处**（创建后 / 上传后 / 导入后 / 进入后 / 导出失败 / 导入成功 / 上传完 / 下载失败），
#: **全部是描述句，没有一处是命令。**
SECTION_HINT = re.compile(
    r"(历史|曾|已退场|已下线|不存在|不可用|当前未开放|正在开发|没开放|未开放|"
    r"机制[，,]?\s*不是|不是你现在|请以|无法|走查过)")
SECTION_HEAD = re.compile(r"^##\s+(.+?)\s*$")
#: **这一页是不是「不可用页」**：页首（h1 之后 8 行）有没有自己声明状态。
#: 判据的输入是「不可用页里的祈使句小节」这个**组合**——
#: 少了「不可用页」这一半，它会开始要求正常页写免责话术。
PAGE_UNAVAILABLE_RE = re.compile(
    r"(已退场|已下线|不存在|不可用|未开放|没开放|正在开发|历史机制|当前不可用|未能走查|未在真实)")


def _strip_containers(lines):
    """整块剔除 VitePress 容器（`::: warning … :::`）。

    **为什么必须整块剔而不是只剔 `:::` 那一行**：容器块**内部**还有正文行，
    只剔标记行的话，块内第一句就成了「小节首句」——而它恰恰是提示本身，
    于是首句永远不是祈使句，`checked_sections` 恒为 0，**notes 会报「共核 0 个」
    而实际核了 2 个**。更糟的是它**看不见提示被移走**：
    只要容器还在那个位置，计数就一直停在 0，**看着像「这一节本来就干净」**。
    """
    out, depth, in_cont = [], 0, False
    for l in lines:
        t = l.strip()
        if t == ":::":
            if in_cont:
                depth -= 1
                if depth == 0:
                    in_cont = False
            continue
        if t.startswith(":::"):
            in_cont, depth = True, 1
            continue
        if in_cont:
            continue
        out.append(l)
    return out


def _page_sections(lines):
    """逐小节切成 (标题, 标题行号, 小节正文行列表)。"""
    out, cur = [], None
    for i, line in enumerate(lines):
        m = SECTION_HEAD.match(line)
        if m:
            if cur:
                out.append(cur)
            cur = (m.group(1), i, [])
        elif cur:
            cur[2].append(line)
    if cur:
        out.append(cur)
    return out


def check_imperative_sections(root):
    """excluded 页的小节若以祈使句开头、而小节内没有任何就地提示，就报。

    返回 (problems, notes, unverifiable)。
    **页面集合动态取自账本的 `status: excluded`**，不硬编码 task id——
    硬编码就是「新增 excluded 任务时忘了把页面加进来」，而那正是
    纪律 164 记过的 art-critique 腐烂三十个批次那种形态。
    """
    # **只读一次账本**：`excluded_ids()` 会把账本再解析一遍，
    # 而本方向要的不只是 id、还有每个 id 的 `manual_pages`——
    # **两个函数各读一遍，账本在两次读取之间被改过就会得出互相矛盾的结论。**
    items = _inventory_items(root)
    if items is None:
        return ([], [], True)

    problems, notes = [], []
    seen_pages, shared, checked_sections = set(), [], 0
    for it in items:
        if str(it.get("status", "")) != "excluded":
            continue
        tid = it.get("id") or "?"
        for rel in (it.get("manual_pages") or []):
            path = os.path.join(root, rel)
            if not os.path.isfile(path):
                return ([], [], True)
            with open(path, encoding="utf-8") as f:
                lines = f.read().split("\n")
            # **页面本身必须自己声明「不可用」才纳入**——excluded 任务的
            # `manual_pages` **不一定指向它的专属页**：
            # `short-drama-project-workbench`（excluded）指向的
            # `00-quickstart.md` 是一张**正常的共享页**，
            # `art-critique` 指向的页也只是「一部分不可用」。
            # **不设这道门槛，首跑就把 quickstart 报成了「历史机制页的祈使句」**，
            # 而那句话说 quickstart 根本不成立。
            h1 = next((i for i, l in enumerate(lines) if l.startswith("# ")), 0)
            if not PAGE_UNAVAILABLE_RE.search("\n".join(lines[h1:h1 + 9])):
                shared.append(f"{rel}（{tid} 的 manual_pages，但页面本身未声明不可用）")
                continue
            seen_pages.add(rel)
            for title, idx, body in _page_sections(lines):
                # **首句必须跳过 VitePress 容器标记**（`::: warning` / `:::`）。
                # 这是**实测出来的统计失真**：加上就地提示后，小节的第一行变成了
                # `::: warning …`，于是首句不再以祈使句开头 → `continue` 掉，
                # **notes 报「共核 0 个祈使句小节」而实际核了 2 个**。
                # 更糟的是判据会因此**看不见提示被删掉的那一刻**——
                # 删掉容器后首句变回祈使句，它又抓得到；可只要提示**换了个位置**，
                # 计数就一直停在 0，**看着像「这一节本来就干净」**。
                first = next((l for l in _strip_containers(body) if l.strip()), "")
                if not SECTION_IMPERATIVE.match(first):
                    continue
                checked_sections += 1
                if any(SECTION_HINT.search(l) for l in body):
                    continue
                problems.append(
                    f"{rel} 的「## {title}」以祈使句开头"
                    f"（{first.strip()[:28]}…）**而本小节内没有任何就地提示** → "
                    f"页首那句「这是历史机制/当前不可用」只护得住从上往下读的人；"
                    f"**Ctrl+F 搜到这一句、或从页内目录点进来的人看不到它**"
                )
    notes.append(
        f"逐节祈使句：{len(seen_pages)} 个「不可用页」共核 {checked_sections} 个祈使句小节，"
        f"全部有就地提示或本就不该用祈使句"
        + (f"；另跳过 {len(shared)} 个 shared 目标（{'; '.join(shared)}）"
           f"——**excluded 任务的 manual_pages 不一定是它的专属页**" if shared else "")
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

    # —— 逐节祈使句（Batch 226，方向七）：页首声明护不住「跳进来的人」——
    imp_problems, imp_notes, imp_unver = check_imperative_sections(ROOT)
    problems += imp_problems
    notes += imp_notes
    if imp_unver:
        unverifiable = True
        print("[skip] 未能读取账本或手册页面，逐节祈使句本轮未能核对")

    # —— 条件 1：/agent/* 路由仍未注册 ——
    # **Batch 181 改**：原先是 `for f in git_ls(...): git_show(src, ref, f)`，
    # 即**每个 backend 文件一次 `git show` 子进程**——实测 347 个非测试 .go、
    # 单次 25ms → **闸门本体约 9 秒**（反验 5 例就是 35.6 秒）。
    # 改成 `batchread.read_many`：**两次进程调用取代 347 次**，
    # 实测 0.19 秒且与逐个 `git show` **逐字节一致**（抽样 40 个零差异）。
    go_files = [f for f in git_ls(src, ref)
                if f.startswith("backend/") and f.endswith(".go")
                and not f.endswith("_test.go")]
    routes = beefsrc.routes_in(read_many(src, ref, go_files))
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
