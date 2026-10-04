#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十八道闸：反验必须能被启动，且启动失败要报出来（Batch 179 新增）。

**这道闸看守的是「哨兵有没有上线」**——Batch 178 踩的那个坑的通用解法。

**问题回顾（Batch 178 的实测）**：7 份反验、34 例跨三个批次全部失效，
而 `build-site.sh` 十七道闸一直全绿。因为**反验不在构建路径上**：
闸门本体在真实目录里跑得好好的，只有反验在临时目录里 import 失败。
**「反验坏了」不产生任何构建期信号，它只是安静地不再说话。**

**为什么不能简单地「把反验都加进构建」**（这是本闸的设计前提，必须先量过）：

  · `selftest-unreachable.sh` 走 git plumbing 往**上游仓库**注入并建临时 ref，
    **实测约 25 分钟**——放进每次构建不可接受；
  · `selftest-meta.sh` **登记 97 秒**（**42 例**）——勉强可接受，但它会
    **原地改 15 个真实文件**（含 `AUDIT.md` / `PROGRESS.md` / `build-site.sh`），
    构建中途失败就会把它们留在被改状态；
  · 其余 10 份 python 反验 1–10 秒不等，**可以直接进构建**。

**所以本闸不跑用例，只验「启动」**——即：用例开始之前那些必须成立的条件。
Batch 178 的 34 例失败**全部发生在启动阶段**（import 失败、找不到手册根），
**没有一例是用例逻辑本身出错**。因此：

  方向一：**每份反验都必须真的能被解释器加载**（语法正确、shebang 合法、
    shell 反验 `bash -n` 通过）。**语法坏掉的反验连启动都做不到。**
  方向二：**反验依赖的本地模块必须能被找到**——这正是 Batch 178 的根因，
    闸 17 核的是「有没有搬运」，本闸核的是「**在真实环境下能不能 import**」。
    **两道闸互补：闸 17 看反验的源码，本闸看真实 import。**
  方向三：**每份反验必须声明它自测的是哪道闸**，且该闸脚本真实存在。
    **没有这条，「反验与闸门的对应关系」就只是散文**——而 Batch 169 已经证明
    散文会过期（方向十一就是为了治它才建的）。
  方向四：**耗时超过阈值的反验必须登记在案**，并写明为何不放进构建。
    **「慢」是一个会悄悄变化的性质**：今天 97 秒，明天上游一大就可能变成 10 分钟。
    **不登记，它就会在某天悄悄越过可接受的界线。**

**Batch 179 刻意不做的事，本批（210）部分推翻，理由必须写在这里**：
当时写的是「本闸**不跑任何用例**……构建期只保证『它至少能启动』」，
理由是 `selftest-unreachable.sh` 约 25 分钟、`selftest-meta.sh` 97 秒，**跑不起**。
**那个理由在今天只剩一半成立**：慢的那几份**已经被识别出来并登记进 `SLOW`**，
而**剩下的 21 份实测只要 31.3 / 34.4 / 32.4 / 32.0 秒**（四轮，同一台机器）。
**决定当初是对的——它是在「不知道哪几份慢」这个前提下做的；
前提变了，决定就该跟着变，而不是把前提忘了继续引用那句话。**
于是新增**方向十六：非慢反验必须真的跑通**。
**「能启动」与「跑得对」仍然分开**：方向十六跑的是**反验自己的用例**，
方向一保证的仍然只是「反验能被启动」——**两者不是一回事，本闸两个都做。**

**但真跑带来两个必须一起解决的问题，不解决就不该做**：
  · **递归**：闸 18 的反验 `selftest-selftest-bootable.py` 装的就是闸 18 自己的用例集合，
    **在闸 18 里跑它 = 闸 18 跑闸 18 跑闸 18**。所以方向十六**硬排除**它，
    **并要求它必须在 `SLOW` 里**——不在就报出来（那说明有人把登记删了）。
  · **沙箱**：闸 18 的反验把自己的每一例都放进一个**只有 `scripts/` 与
    `build-site.sh` 的沙箱**，**那里没有手册正文**。
    所以方向十六**先核前提**：手册根下的 `.md` 不足 5 份就**不跑**，
    **并且把「这里不是一棵完整的手册树」说出来**。
    **这一版最初是「用白名单缩到一两份」，实测证明那条路走不通**——
    缩范围并不能让沙箱能跑，而缩了范围还得额外解释一遍「本次只跑了 N 份」；
    **机制多一个，可错的地方就多一个**。核前提更短，也更准。

退出码：0 全部可启动；1 有反验起不来；2 未能核对（找不到 scripts 目录 / 抽出 0 份反验）。
"""

import ast
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import announce_fallback  # noqa: E402
from selftestnames import FIXTURE_RE  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SCRIPTS = os.path.join(ROOT, "scripts")

# 慢反验登记表。
#
# **Batch 180 改的正是这个表**。原样写着「阈值取自实测，不是拍的」——
# **而那个 `SLOW_BUDGET_MS = 30000` 全文件只出现这一次，从没被任何判据读过**：
# 方向四只核「登记了的还在不在」，**从不核「有没有该登记的漏登记了」**。
# **注释在撒谎，而没人发现**——因为注释不产生任何信号。
# 这是纪律 112（「用会变的量当论据之前，先想清楚谁来看着它」）的完整形态：
# **量确实存在，但没有任何机制看着它，于是它等于不存在。**
#
# 改法不是「把 30 改成别的数」——**任何硬编码的秒数都会重蹈覆辙**。
# 改成**由事实推导**：每份慢反验**自己声明实测耗时**，判据核
#  ① 声明的耗时必须真的超过阈值（否则它其实不慢，该从表里删掉）；
#  ② 阈值本身写在表里、且**必须与实测分档对得上**（见 SLOW_BUDGET_SEC）。
# **判据锚的是「谁慢、慢多少」这个可测事实，而不是一个我拍出来的数。**
SLOW_BUDGET_SEC = 30
SLOW = {
    "selftest-zero-input.py": {
        # **Batch 202 把这个数字的来历写清楚，因为它此前一直没人核**
        # （方向四a 只核「是不是正数、是不是 > 30」，**从不核它等于实测值**——
        # 一个从未被核对过的常数，注释里却写着「实测」，见纪律 191）。
        # **82s 是 Batch 202 实施当时的一次快照，不是可复现的值**：
        # 同一天同机交错重测，同一套 25 道闸得 **62.3s / 32.5s**，
        # 单 `verify-unreachable.py` 得 **20.6s / 17.2s**——
        # **绝对值 2 倍漂，连比值都在 1.9～3.0 之间漂**（本机同时有别人的构建在跑）。
        # 所以这里能确定的只有**量级**：「它确实越过 30 秒阈值」，
        # 而 82 这个具体数字**只当历史快照看**。
        # **两次变慢的原因都是同一个，且都不是它多做了什么**：
        # Batch 197 给 `beefsrc` 加了可用的兜底 → 方向三里 7 道闸**回落到真仓把整道闸跑完**；
        # Batch 202 把原本 rc=2 的 2 道闸也接上兜底 → **它们于是也真的跑完了**。
        "seconds": 82,           # 历史快照（方向四a 只看它 > 30，不看它准不准）
        "why": "**它变慢不是因为多了检查，是因为被它核的那些闸不再秒退**——"
        "Batch 197 给 `beefsrc` 加了可用的兜底之后，方向三里 `BEEFTV_SRC` 指向非仓的 7 道闸"
        "**回落到真仓把整道闸跑完**；Batch 202 把原本 rc=2 的 2 道闸也接上兜底，"
        "**它们于是也真的跑完了**。已越过 30 秒阈值（**量级可信，具体秒数不可信，见左侧注释**）。"
        "登记 + 提交前跑——**与另外三份慢反验同一类必要成本**："
        "它核的是「全部闸在两个极端下各自会说什么」，而那只能靠逐道真跑。"
        "**两次变慢都不是它多做了什么，而是被它核的那些闸真的开始做事了。**",
        "anchor": ("selftest-zero-input.py", "def direction_three"),
    },
    # **Batch 208 补登记的两条**：它们此前都在 `SELFTEST_COSTS` 里写着**低报的秒数**
    # （`selftest-quote-punct.py` 登记 11 秒、实测 37.1 秒），于是方向四d
    # 「超过阈值却没登记为慢」**永远看不见它们**——**判据核的正是那个错的数**。
    "selftest-quote-punct.py": {
        "seconds": 38,           # 实测（Batch 208：37.1/30.6 秒，**两次取大**）
        "why": "**它此前登记的是 11 秒，而实测 37.1 秒**——"
               "**低报的方向是唯一危险的那个**：方向四d 用这个数判「你登记为不慢，"
               "到底是不是真的不慢」，而**错的正是这个数本身**，于是判据无从发现。"
               "它是闸 22（引号文案标点漂移）的反验，"
               "而闸 22 要把**四份手册的 900 段引号**逐条回上游语料里找字面出处。",
        "anchor": ("selftest-quote-punct.py", "def m_missing_comma_must_report"),
    },
    "selftest-screenshots-literals.py": {
        "seconds": 31,           # 实测（Batch 208：30.1/24.3 秒，**两次取大**；**恰压 30 秒线，如实记**）
        "why": "**与上一条同一个病**：登记 23 秒、实测 30.1 秒，**刚好越过阈值**。"
               "**这一条是「阈值型守卫」为什么必须取保守方向的最好例子**——"
               "差 0.1 秒，而判据看到的是 23。",
        "anchor": ("selftest-screenshots-literals.py", "def run(manifest_text"),
    },
    "selftest-selftest-bootable.py": {
        # **Batch 210 重测：209.3 秒与 383.7 秒**（两次取大，纪律 204：漂的时候倒向安全那侧）。
        # **同一天同一台机器 1.8 倍漂**（209.3 → 383.7）——纪律 136 早就说过绝对毫秒会漂，
        # **这里再实测一次，数字对得上那条纪律**。
        # 变慢的来源是本批新增的两条用例 23/24：它们各自要建一棵**完整**的手册树副本
        # （15.2 MB、拷贝 0.3 秒）再让方向十六真跑 21 份反验（~30 秒），
        # **两条加起来就是本批新增的那 ~90 秒**。
        #: **Batch 254 重测**：本批加了两条用例（26/27），实测 **877 秒**
        #: （此前 209.3 / 383.7 秒，本批单次实测 461 秒是 24 例的基线）。
        #: **按纪律 204 取大并留余量，登记 950**——
        #: **`seconds` 是预算上限而不是实测均值，低估是危险方向**。
        #: **两条新用例各自要建一棵完整手册树副本再让方向十六真跑 32 份反验**，
        #: 而用例 27 那一侧是**正常环境**（上游在场），**它是本文件里最贵的一条**。
        #: **本轮只有一次测量，而单次测量不足以定预算**——
        #: **如实记下来，而不是假装它准**（纪律 191：方向四a 只看它 > 30）。
        "seconds": 950,
        "why": "每一例都要 `copytree` 整份 `scripts/`（87 个文件）进沙箱再跑一遍闸 18，"
               "**而闸 18 现在还会在沙箱里重放慢反验的夹具前提**。"
               "已越过 30 秒阈值，**放进构建会让每次构建多花三分之一时间**。"
               "登记 + 提交前跑——**这与 `selftest-meta.sh` 是同一类必要成本**："
               "它核的是「反验本身还能不能用」，而反验不在构建路径上。"
               "**登记值此前低报了 88 秒，而低报的方向是唯一危险的那个**（纪律 204）："
               "**「作废的用例」会让反验跑得更快、验得更少**——"
               "用例 9/10 的注入锚点被 Batch 208 那次例行数据刷新弄失效之后，"
               "它们每次都在断言处直接返回，**一秒的闸都不跑**。"
               "**换句话说：那两条用例正是「让这份耗时登记值变好看」的原因。**"
               "已改锚键（锚键不锚值），两条重新真跑，登记值按新实测据实上调。",
        "anchor": ("selftest-selftest-bootable.py", "m_slow_feature_missing"),
    },
    "selftest-unreachable.sh": {
        "seconds": 1500,          # 实测约 25 分钟（Batch 179）
        "why": "走 git plumbing 往上游仓库注入 40 个用例并建临时 ref，"
               "每个用例都要 read-tree / write-tree / commit-tree。"
               "**放进构建会让每次构建多花 25 分钟**。改为登记 + 提交前跑。",
        "anchor": ("selftest-unreachable.sh", "refs/manual-gate-selftest"),
    },
    "selftest-meta.sh": {
        "seconds": 97,            # 实测（Batch 179）
        # **Batch 237 重测三次：47 / 48 / 68 秒（取大 68），例数 36 → 42，但登记值仍留 97。**
        # **这不是忘了更新，是刻意的**——`seconds` 在本闸里是**预算上限**，
        # 拿它去算「这些反验一共要占多少构建时间」，**它偏大只会让人多留余量，
        # 偏小才会让人按一个跑不完的时间做安排**。同一天三次就跑出 47 与 68（1.4 倍漂），
        # 拿单次数字当事实的误差，比保守值本身的误差更大（纪律 136）。
        # **Batch 182 修正了它的登记理由**。原理由写「97 秒 + 会原地改 15 个文件」，
        # 把**风险**当成了**原因**——而实测下来它的安全机制其实是齐的：
        #   · 每例前 `restore`
        #   · `trap 'restore' EXIT`
        #   · 每例核对 15 个文件的 md5 未变（注入空转即作废）
        # **它真的必须原地跑**：它核的是**真实仓**的登记表与侧栏配置，
        # 搬到副本仓就核不到真东西了。**所以 97 秒是必要成本，不是可以优化掉的浪费。**
        "why": "**必须原地跑**——它核的是真实仓的登记表/侧栏/索引，"
               "搬到副本仓就核不到真东西。97 秒是**必要成本**。"
               "安全机制已齐（每例前 restore + trap EXIT + md5 核对），"
               "中途被打断也会还原，不存在「留下脏文件」的实际风险。",
        "anchor": ("selftest-meta.sh", "SNAP_FILES"),
    },



}


# **实测耗时登记表**（Batch 180 新增）。单位：秒，单次实测（含进程启动）。
#
# **为什么需要这张表**：方向四d 要核「没登记为慢的反验，实测是否真的不超过阈值」。
# 而**判据在构建期无法知道谁慢**——除非有人把秒数写进来。
# 于是这里要求：**「我没登记它慢」必须是一个有据的说法，而不是「我没量过它」。**
# 这正是纪律 112 的正面用法：与其指望「量小到大有人在看」，
# 不如**让「没量过」本身成为一个可被看见的状态**。
#
# **怎么维护**：新增反验时跑一次 `time python3 scripts/selftest-<名>.py`，
# 把秒数填进来。**故意留空的值会让构建失败**——
# 因为「空着」和「量过但很快」在账面上长得一模一样，而只有后者是有意义的。
SELFTEST_COSTS = {
    #: **Batch 255 新增**。11 例里 7 例是纯字符串/集合运算（毫秒级），
    #: **但用例 9/11 要起 `bash` 子进程**抠出 `build-site.sh` 的真函数真跑——
    #: **预算按「有子进程」这一侧取，宁大勿小**（纪律 204）。
    "selftest-build-record.py": 3.0,
    #: **Batch 256 新增**。6 例里 4 例是纯字典/字符串运算（毫秒级），
    #: **但每例都要 `copytree` 出 157 份的临时树再起一次子进程跑闸**。
    #: **实测三次 1.27 / 1.15 / 0.95 秒**——**而原注释那套「每例一次全量复制 +
    #: 一次子进程所以要给 6 秒」的理由与实测差了五倍**。
    #: **预算仍留 6.0**：`seconds` 是**上限**，偏大安全（纪律 204/136），
    #: **但理由要按实测写，不能拿一个没量过的推断撑着**（纪律 281 推论三）。
    "selftest-duplication.py": 6.0,
    "selftest-baseline.py": 0.7,
    #: **Batch 268 新增**。闸 38 的反验：5 例里 4 例要 `git init` + 提交 + 改文件
    #: + 起一次子进程跑那道闸，**每次都在临时目录里，与真树无关**
    #: （**这正是它能被放心快跑的原因**——它只读 `git status --porcelain`）。
    #: **实测三次 0.80 / 0.74 / 0.71 秒**，登记 **1.0**（取大，纪律 204）。
    #: **而这一条是方向四d 存在的理由的一次现场应验**：
    #: **新增一份反验却没登记实测耗时，闸 18 当场报出「既没登记为慢、
    #: 也没被构建自动调用，且 `SELFTEST_COSTS` 里没有它的实测耗时」**——
    #: **「我没登记它慢」必须是一个有据的说法，而不是「我没量过它」**。
    "selftest-worktree-state.py": 1.0,
    #: **Batch 270 新增**。闸 39 的反验：5 例，**每一例都在临时目录里造一组小闸、
    #: 把真闸复制进去、再把真闸真跑一遍**（判据自己会逐道注入并执行）。
    #: **实测三次 1.04 / 0.98 / 0.94 秒**，登记 **1.5**（取大，纪律 204）。
    #: **而这份登记是 Batch 268 那条纪律的第二次应验**：
    #: **建文件 → 登记实测耗时 → 过方向四d，三步缺一步就被拦**。
    #: **两次都被拦在同一处，而那正是它该拦的地方**（纪律 112）。
    "selftest-gate-alive.py": 1.5,
    #: **Batch 272 新增，Batch 273 加到 12 例**。闸 40 的反验。
    #: **每例都在临时目录里造一份手册根（`20-reference.md` + 被测闸 + 依赖闭包）再起子进程真跑**。
    #: **耗时改过两次，两次都是因为反验自己变了**：
    #: ①初版手写搬运清单，实测 1.16 / 1.10 / 1.30 秒、登记 1.5；
    #: ②改用 `stagedeps.stage_gate()`（闸 17 在上线构建里当场报出「反验没把依赖搬进临时目录」）
    #: 之后**实测 4.40 / 2.92 / 3.10 秒**，登记 5.0——
    #: **`stage_gate()` 每次都起一个子进程真 import 一遍**来验闭包算对了没有，
    #: **于是同一份反验在两种写法下差了将近三倍**，而账面上的数如果不跟着改，
    #: 方向四d 判的就是一个已经不存在的东西。
    #: ③**Batch 273 加了 3 例**（订阅契约，每例多造一个合成上游 git 仓：
    #: `git init` + 一份 CHANGELOG + 一个 `refs/remotes/origin/main`），
    #: **实测 2.56 / 2.75 / 2.66 秒，登记仍是 5.0**——
    #: **加了 3 例反而比 ② 快**，因为 ② 那次量进去的 4.40 秒是冷缓存那一条。
    #: **而「加了用例耗时反而降了」这件事本身要留着**：
    #: **只涨一次或只降一次的数都不是这个反验的稳定特征**，
    #: 登记值取的是**上限**（纪律 204），5.0 仍高于三次实测的最大值。
    #: **12 例里有 1 例是纯读输出**（用例 5：Unreleased 那条提示必须出现）——
    #: **它不注入任何东西**，所以它比其余 11 例快，**而它守的偏偏是本批真踩到的那条**
    #: （计数恒为 0、提示一次都没打印过，**且不会让闸变红**）。
    #: **一条不注入的用例守着一段不参与判定的逻辑**：这是本闸体系里最容易被
    #: 「用例都在注入」这个印象盖过去的一类（纪律 307 推论三）。
    #: **而 Batch 273 那 3 例连「上游」都不碰**——它们只改手册那一侧，
    #: **「上游多发一版」这件事得靠一个合成 git 仓才造得出来**（纪律 265）。
    "selftest-baseline-landmark.py": 5.0,
    #: **Batch 243 重测**：三次实测 0.62 / 0.53 / 0.44 秒，**而原登记值是 0.1**——低估了六倍。
    #: **`seconds` 是预算上限而不是实测均值，所以低估是危险方向**（纪律 204/136：漂的时候倒向安全那侧）。
    #: 用例从 8 条加到 10 条，而**每条都要把闸真跑一遍**、闸每次都要重读整份 PROGRESS.md——**反验的耗时几乎全在重复读文件上**。
    "selftest-batch-rows.py": 0.8,
    "selftest-beefsrc.py": 0.3,
    "selftest-deadlinks.py": 0.2,
    "selftest-encoding.py": 0.2,
    "selftest-endpoints.py": 0.8,
    "selftest-error-copy.py": 0.8,
    "selftest-exclusions.py": 1.6,
    "selftest-feature-flags.py": 0.4,
    "selftest-label-drift.py": 1.9,
    "selftest-ledger-refs.py": 0.3,
    "selftest-line-counts.py": 4.8,
    "selftest-link-labels.sh": 2.4,
    "selftest-query-params.py": 0.8,
    "selftest-container-closers.py": 1.13,
    "selftest-heading-uniqueness.py": 1.10,
    #: **Batch 233 新增**：三次实测 2.80 / 2.37 / 2.34 秒，**按纪律 204 取最大 2.8**。
    #: 它每例都起一个临时目录、跑一遍被测闸门，而闸门每次要 `git show` + `git grep`
    #: **全树**——9 例 2.8 秒，与闸 13 反验同量级。
    "selftest-quota-tables.py": 2.8,
    #: **Batch 247 新增**：三次实测 2.09 / 2.20 / 1.96 秒，**按纪律 204 取最大 2.2**。
    #: 7 例里 6 例每例 `shutil.copytree` 一整份 `scripts/`（103 个 selftest-* 加 36 个闸），
    #: **而每个被测闸又要把这棵树重新 `ast.parse` 一遍**——耗时几乎全在重复解析上。
    #: **这一条比它的数字更要紧**：新闸的门是**闸脚本自己**，
    #: 所以它的反验必须整份搬 `scripts/`，**不能只搬一个被测文件**。
    "selftest-retracted-claims.py": 2.2,
    #: **Batch 234 新增**：三次实测 0.38 / 0.35 / 0.37 秒，**按纪律 204 取最大 0.4**。
    #: 它每例起一个临时目录并搬 `20-reference.md` + `.vitepress/config.mjs`——
    #: **闸门必须能读出「当前该是哪个版本」与「哪些页会被发布」**，少搬一个则 8 例全 rc=2。
    "selftest-current-version.py": 0.4,
    #: **Batch 235 新增**：三次实测 1.34 / 2.22 / 1.15 秒，**按纪律 204 取最大 2.3**
    #: （2.2 秒那次是它 21 次 `git diff` 撞上磁盘抖动——**漂的方向是往上，所以取大**）。
    #: 它每例都要起临时目录并搬 README + 20-reference + manifest；
    #: 被测闸门每例要对上游跑十几次 `git diff`（整个版本区间逐对相邻 tag）。
    #: **Batch 242 重测**：三次实测 4.37 / 4.17 / 3.12 秒（原 2.3），**按纪律 204 取最大 4.37，登记 5.0**。
    #: 用例从 6 条加到 8 条，**每条都要重跑一遍 15 个版本区间的 diff**，所以耗时几乎翻倍——**反验变贵是加用例的直接代价，必须如实登记而不是沿用旧值**。
    "selftest-version-coverage.py": 5.0,
    #: **Batch 236 新增**：三次实测 1.31 / 1.35 / 1.17 秒，**按纪律 204 取最大 1.4**。
    #: 它每例起临时目录并搬 manifest + 账本 + 参考页；被测闸门每例读一次上游 router.tsx。
    "selftest-route-notation.py": 1.4,
    "selftest-quote-punct.py": 37.1,
    "selftest-runtime-policy.py": 1.0,
    "selftest-scope.py": 0.4,
    "selftest-screenshots-literals.py": 30.1,
    "selftest-screenshots.py": 0.7,
    "selftest-selftest-bootable.py": 384.0,   # Batch 210 重测：209.3 / 383.7 秒（**两次取大**；**同一天 1.8 倍漂**，纪律 136）
    #: **Batch 247 重测**：三次实测 7.33 / 6.95 / 7.11 秒，**而原登记值是 0.7——低估了十倍**。
    #: 9 例里每例都 `copytree` 一整份 `scripts/`（103 个 selftest-* 加 36 个闸）再起一个子进程跑被测闸，
    #: **耗时几乎全在重复拷贝上**。**`seconds` 是预算上限而不是实测均值，
    #: 低估是危险方向**（纪律 204/136：漂的时候倒向安全那侧）——
    #: **而这条低估在 Batch 247 之前就存在**，本批只是因为给它加了两例才顺手重测。
    #: **一个「跑得比登记慢十倍却没人发现」的登记，和写错一个数是同一种病。**
    "selftest-selftest-deps.py": 7.5,
    "selftest-shortcuts.py": 0.7,
    "selftest-shot-drift.py": 10.0,
    "selftest-shot-pixels.py": 7.1,
    #: **Batch 239 新增**：三次实测 1 / <1 / 1 秒，**按纪律 204 取最大 1 秒**，登记 1.5。
    #: 样本全部由 `pngstat` 现场造（纯色 PNG 只有几 KB），只有第 8 例要复制真实 67 张，
    #: **而它不读像素**——本闸只对文件字节做 sha256 与尺寸，所以比 `selftest-shot-pixels.py` 快一个量级。
    "selftest-shot-integrity.py": 1.5,
    "selftest-shot-version.py": 0.8,
    #: **Batch 241 新增**：三次实测 5.41 / 5.44 / 6.06 秒，**按纪律 204 取最大 6.06，登记 6.5**（偏大安全）。
    #: 慢在**每个用例都要 `git init` 造一个真仓**——本闸的输入就是提交历史，而「造一段假的历史」比「造一份假的文件」贵得多。
    #: **Batch 244 加到 13 例后重测**：5.80 / 5.60 / 5.63 秒，**仍在 6.5 这个上限之内，故登记值不变**（新加的两例是纯文本改写，不建新仓）。
    "selftest-shot-version-source.py": 6.5,
    "selftest-tables.sh": 0.8,
    "selftest-zero-input.py": 42.1,
}


# 注入夹具的命名形态：`selftest-<闸>-fix-<序号>-<说明>.py`。
# **它们不是反验**——只是 stdin→stdout 的文本变换器，被反验调用一次。
# 上线首跑时我把 58 份夹具全当成反验、报出 58 处「没有指向被测闸门」——
# **这正是「把两类同名文件当成一类」的错误**。它们的名字都叫 `selftest-*`，
# 光看前缀分不出来，**必须靠 `fix-` 这个中段**。
# （纪律 109：分类判据要锚可观测事实。这里可观测的事实就是文件名里的 `fix-`。）
# **Batch 258 收敛**：本条判据原先在本文件与闸 9 各写一份（**逐字相同**），
# 而闸 9 那份的注释写着「**故意复制而不共用**——闸之间互相 import 会让任一方
# 坏掉时另一方跟着起不来，而那正是 Batch 178 记下的那次失效」。
# **那个理由已经过期**：那次失效的成因是**搬运时漏了模块**，
# 而 `stagedeps.stage_gate()` 已把「该搬哪些」变成算出来的、闸 17 逐份核闭包——
# **为了防那次失效而拒绝 import，代价正是让那次失效有可能重演**。
# 判据本体搬进 `selftestnames.py`，名字 `FIXTURE_RE` 保留不变。

# 标准库：这些 import 不需要在本仓 scripts/ 下存在
STDLIB = set("""abc argparse ast base64 collections contextlib copy csv dataclasses datetime
difflib enum errno filecmp fnmatch functools glob hashlib io itertools json logging math mimetypes
os pathlib platform random re shlex shutil subprocess sys tempfile textwrap time typing unittest
urllib uuid warnings""".split())


def _looks_third_party(mod):
    """这个名字像不像第三方库。

    **为什么这里必须收紧**（反验用例 5 上线首跑就漏报了）：第一版写的是
    「不以下划线开头就算第三方」——于是注入的 `nosuchmodule` 被放过。
    但本仓**不装任何第三方依赖**，所以凡是能 import 成功的非标准库必然是本仓自己的模块；
    剩下那些 import 不了的，**几乎总是笔误而不是库**。
    **判据取严：只放过明确的内置/特殊名，其余一律要求文件存在。**
    误伤一个真第三方库的成本，远小于放过一个笔误——
    **因为笔误的代价是「反验静默失效」，而误报的代价只是多写一个 STDLIB 条目。**
    """
    return mod in ("__future__", "builtins")



def _extract_fn(src, name):
    """把 `build-site.sh` 里的某个 shell 函数**原样抠出来**。

    **为什么不 source 整份脚本**：一 source 它就真的开始建站。
    抠到**行首的单个 `}`** 为止；单行函数（`fail`）就地结束。
    **抠不出来就抛**——让用例作废，而不是拿一个空串继续跑：
    作废的反验比失败的反验更危险，因为它连报红都不报（纪律 178）。
    """
    # **空白不能写死**：`log()` 在脚本里写成 `log()  {`（两个空格），
    # 而 `fail()` 是单行体——两种形态都得抠得出来。
    m = re.search(r"\n%s\(\)\s*\{" % re.escape(name), src)
    assert m, "build-site.sh 里找不到函数 %s" % name
    start = m.start()
    head_end = src.find("\n", start + 1)
    head = src[start + 1:head_end]
    if head.rstrip().endswith("}"):
        return head + "\n"
    end = src.find("\n}\n", head_end)
    assert end > head_end, "函数 %s 找不到行首的收尾花括号" % name
    return src[start + 1:end + 3]


def _run_gate_probe(stub_rc, silent=False):
    """**把 `build-site.sh` 的真 `run_gate` 抠出来跑一遍**，问它一道指定退出码的闸会怎样。

    **为什么不 grep 判写法**：`out="$(...)"` 后面跟不跟 `|| rc=$?` 是写法，
    而「闸失败时构建到底说不说话」是事实（纪律 171）。
    **行为可判、写法不可判**，所以这里用真函数 + stub 闸真跑一遍。
    返回 `(rc, 输出)`；输出含 ANSI 颜色码，判断时只找中文文案。

    **`silent=True`（Batch 267 新增）：造一个 rc=0 却一句话都不说的闸。**
    **为什么原来测不到**：stub **总是会 print 两行**，
    **所以「rc=0 且零输出」这个形态从来没被造出来过**——
    **而它正是「判据崩了却 rc=0」在构建里的样子**
    （Batch 266 实测两次：占位符 `NameError`、正则 `re.error`，
    **两次构建都全绿，因为构建只在 rc≠0 时才说话**）。
    **`silent` 那一支才是本批的真凶**，另三支是「修的时候别把好的弄坏」。
    """
    with open(os.path.join(ROOT, "build-site.sh"), encoding="utf-8") as fh:
        src = fh.read()
    fns = "".join(_extract_fn(src, n) + "\n\n" for n in ("log", "ok", "warn", "fail", "run_gate"))
    tmp = tempfile.mkdtemp(prefix="run-gate-probe.")
    try:
        os.makedirs(os.path.join(tmp, "scripts"), exist_ok=True)
        #: **`silent` 时一个字都不 print**——**而 `main()` 第一行就 `return 0`**，
        #: **所以语法完全合法、`ast.parse` 通过、`rc=0`**：
        #: **这道闸在所有「核写法」的判据眼里都是健康的**。
        body = ("import sys\ndef main():\n    return 0\n"
                "if __name__ == '__main__':\n    sys.exit(main())\n"
                if silent else
                "import sys\nprint('闸的输出：某某与手册对不上')\n"
                "print('第二行')\nsys.exit(%d)\n" % stub_rc)
        with open(os.path.join(tmp, "scripts", "stub.py"), "w", encoding="utf-8") as fh:
            fh.write(body)
        probe = ('set -euo pipefail\nTS="00:00:00"\n' + fns + 'run_gate "stub.py" "试闸"\n')
        p = os.path.join(tmp, "probe.sh")
        with open(p, "w", encoding="utf-8") as fh:
            fh.write(probe)
        r = subprocess.run(["bash", p], cwd=tmp, capture_output=True, text=True, timeout=60)
        return r.returncode, (r.stdout or "") + (r.stderr or "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


#: `$var` 后面**紧跟**一个非 ASCII 字符（Batch 205）。
#: **为什么要盯这个**：macOS 自带的 bash 3.2 在 UTF-8 locale 下
#: 会把那些字节算进变量名，于是报「`desc?: unbound variable`」——
#: **而 `desc` 明明上一行刚 `local` 过**。实测同一份脚本、同一台机器，
#: `LC_CTYPE=C.UTF-8` 时 0/5 通过，不设时 5/5 通过。
#: **这不是编码问题，是变量名边界问题**；`${var}` 是唯一可靠写法。
UNSAFE_VAR_RE = re.compile(r"\$([A-Za-z_][A-Za-z0-9_]*)")


def _shell_files():
    out = [os.path.join(ROOT, "build-site.sh")]
    for fn in sorted(os.listdir(SCRIPTS)):
        if fn.endswith(".sh"):
            out.append(os.path.join(SCRIPTS, fn))
    return [p for p in out if os.path.isfile(p)]


def _locale_breaks_it():
    """**这个判据在本机真的成立吗**——用一段最小样例自己问一遍 bash。

    **样例必须带 `set -u`**：不设它时 `$desc：` 只是被切成一个不存在的变量名、
    展开成空串，**照样 rc=0 打印出来**——第一版探针就漏了它，
    于是它自报「本机实测不复现」，**而真实脚本全都有 `set -u`，一设就炸**。
    **一个不忠实的探针，会让判据给出「它不存在」这个错误结论**（纪律 176 的变体：
    结论错，而理由也对不上）。


    **不这么做的话，这条判据就是一条 superstition**：
    它断言「这种写法会炸」，而本批只在一台机器的一个 bash 上量过一次。
    所以现场跑：设 `LC_CTYPE=C.UTF-8` 执行 `$v：`，**看它是不是真的会报未绑定**。
    返回 `(会不会坏, bash 版本第一行)`——**两样都写进报红信息里**。
    """
    code = ("set -u" + "\n"
            'f() { local desc="值"; echo "$desc：后面"; }' + "\n"
            "f" + "\n")
    try:
        # **errors="replace" 不是可选的**：这条路径上 bash 吐出来的就是坏字节
        # （变量名被切坏之后，错误信息里带着切剩的字节），
        # 而子进程解码失败会让判据自己崩掉——**判据崩了比判据红更难看**。
        r = subprocess.run(["bash", "-c", code], capture_output=True, text=True,
                           errors="replace",
                           env=dict(os.environ, LC_CTYPE="C.UTF-8"), timeout=20)
    except (OSError, subprocess.SubprocessError):
        return None, "?"
    broke = "unbound variable" in ((r.stdout or "") + (r.stderr or ""))
    ver = subprocess.run(["bash", "--version"], capture_output=True, text=True,
                         errors="replace")
    return broke, ((ver.stdout or "").split("\n") or ["?"])[0]


def _build_invokes(fn):
    """build-site.sh **真的执行**了这份反验吗（注释里提到不算）。

    **只看代码、不看注释**（方向四c 上线首跑就误报，Batch 180）：
    `build-site.sh` 的注释里正写着 `selftest-unreachable.sh` 与 `selftest-meta.sh`
    的名字和实测秒数——那是**给人看的说明**，而字面匹配把它们当成了调用。
    **注释不是调用点**，与闸 7「URL 写出点只看代码不看注释」同源。
    """
    path = os.path.join(ROOT, "build-site.sh")
    try:
        with open(path, encoding="utf-8") as fh:
            lines = fh.read().split("\n")
    except OSError:
        return False
    for line in lines:
        if line.lstrip().startswith("#"):
            continue
        if fn in line:
            return True
    return False


#: 反验引用的同层文件名（`selftest-*.py|sh` 与 `verify-*.py`）。
#: **刻意不匹配 glob 形态**：`selftest-*.py`、`selftest-fix-*-fixture.py` 里
#: 那个 `*` 不在字符类里，所以**通配写法不会被当成一个真实文件名**。
DANGLING_RE = re.compile(r"\b((?:selftest|verify)-[A-Za-z0-9._-]+\.(?:py|sh))\b")


def _code_only(path):
    """只留真正会被执行到的字面量：Python 用 AST 剥注释与文档字符串，shell 剥 `#` 注释。

    **与 `verify-meta.py` 的同名函数同一套做法**（方向十一的「驱动按事实判定」
    就靠它）。**重复而不共用是有意的**：闸之间互相 import 会让任一方坏掉时
    另一方跟着起不来——**那正是 Batch 178 记的那次失效**。
    """
    src = open(path, encoding="utf-8", errors="ignore").read()
    if path.endswith(".py"):
        tree = ast.parse(src)
        docs = set()
        for node in ast.walk(tree):
            if isinstance(node, (ast.Module, ast.FunctionDef,
                                 ast.AsyncFunctionDef, ast.ClassDef)):
                b = getattr(node, "body", None)
                if b and isinstance(b[0], ast.Expr) and \
                        isinstance(b[0].value, ast.Constant) and \
                        isinstance(b[0].value.value, str):
                    docs.add(id(b[0].value))
        return "\n".join(n.value for n in ast.walk(tree)
                         if isinstance(n, ast.Constant) and isinstance(n.value, str)
                         and id(n) not in docs)
    return "\n".join(re.sub(r"#.*$", "", ln) for ln in src.split("\n"))


def _deleted_sibling_names():
    """`scripts/` 下**历史上删掉过、现在已不在场**的文件名集合。

    **取不到就返回 `None`（核不了），而不是空集合（没有问题）**——
    纪律 203：一个不记账的「跳过」会让「没查」看起来像「查了没成」。

    **为什么用 git 删除历史，而不是「这个名字看着像不像夹具」**：
    第一版按名字收窄（只认 `selftest-fix-*`）也试过，实测**漏掉真事故**——
    事故那个名字是 `selftest-fix-2-…`，能认出来，可判据一旦这么写，
    下一个被删的夹具换个命名就又漏了。**「删过」是事实，「像什么」是约定**（纪律 101）。
    """
    r = subprocess.run(
        ["git", "-C", ROOT, "log", "--diff-filter=D", "--name-only", "--format=",
         "--", "scripts"],
        capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        return None
    return {os.path.basename(ln.strip()) for ln in r.stdout.split("\n")
            if ln.strip() and ln.strip().endswith((".py", ".sh"))}


#: 从反验的输出末尾解析「它自己报的合计」。
#: **四个形态不是四个约定，是实测出来的四种写法**：
#:   `通过 6 / 失败 0 / 作废 0`（多数）、`6 例，通过 6，失败/作废 0`、
#:   `✅ 5/5 例通过`、以及**末尾没有「作废」那一段的** `通过 6 / 失败 0 ===`。
#: 第四种只有 `selftest-tables.sh` 一份——**而它恰好是本批之前例数唯一过期的那一行**，
#: 所以**漏掉它就等于漏掉唯一需要抓的那一份**。
#: **每一条都写明「是求和」还是「取第几组」**。
#: 第一版把这两件事塞进同一个参数（`pick`），于是 `5/5 例通过` 被当成 5+5 = 10——
#: **上线首跑三份全报「正好 2 倍」的错**（6→12、5→10、6→12）。
#: **那个「正好 2 倍」就是它的签名**：真值不会集体翻倍，而解析器会。
#: **一个可疑的整齐数字，先怀疑解析器，再怀疑数据。**
TALLY_PATS = (
    (re.compile(r"通过\s*(\d+)\s*[/／]\s*失败\s*(\d+)\s*[/／]\s*作废\s*(\d+)"), "sum", 3),
    (re.compile(r"结果：通过\s*(\d+)\s*[/／]\s*失败\s*(\d+)\s*===?"), "sum", 2),
    (re.compile(r"(\d+)\s*例[，,]?\s*通过\s*(\d+)"), "group", 1),
    (re.compile(r"(\d+)\s*/\s*(\d+)\s*例通过"), "group", 2),
)


def _tally(out):
    """返回 (合计, 用了第几条) 或 (None, None)：**从后往前找，取第一个认得的**。"""
    for line in reversed(out.split("\n")):
        for i, (pat, mode, n) in enumerate(TALLY_PATS):
            m = pat.search(line)
            if not m:
                continue
            if mode == "sum":
                return sum(int(x) for x in m.groups()[:n]), i
            return int(m.group(n)), i
    return None, None


def _claimed_case_counts():
    """对应关系表里 `反验名 -> 例数`。**核不到就返回 None**（不是空表）。"""
    path = os.path.join(ROOT, "AUDIT-RULES.md")
    if not os.path.isfile(path):
        return None
    text = open(path, encoding="utf-8").read()
    m = re.search(r"###\s*闸\s*→\s*反验的对应关系[^\n]*\n(.*?)(?=\n###|\n##\s)", text, re.S)
    if not m:
        return None
    out = {}
    for line in m.group(1).split("\n"):
        if not line.startswith("|") or re.match(r"\|\s*:?-", line):
            continue
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) >= 3 and c[0] != "闸":
            out.setdefault(c[1].strip("`"), c[2])
    return out


def is_fixture(fn):
    return bool(FIXTURE_RE.match(fn))


def selftests():
    """只返回**真正的反验**，排除注入夹具。"""
    out = []
    for fn in sorted(os.listdir(SCRIPTS)):
        if not fn.startswith("selftest-"):
            continue
        if not (fn.endswith(".py") or fn.endswith(".sh")):
            continue
        if is_fixture(fn):
            continue
        out.append(fn)
    return out


def fixture_count():
    return sum(1 for fn in os.listdir(SCRIPTS)
               if fn.startswith("selftest-") and is_fixture(fn))


def _imported_modules(path):
    """这份反验**真的 import 了**哪些顶层模块名。

    **为什么是 import 而不是「文本里出现过这个名字」**（Batch 198 实测的两次假阴性）：
    第一版按文本匹配，**模块 docstring 与 `print()` 里的一句说明就足以骗过它**——
    实测把 `import beefsrc` 整行删掉、文档一字不改，判据照样报绿。
    收窄到「剥掉注释与文档字符串后，**AST 里真的有一条 import 语句**」才抓得住。
    这与方向三原有的闸名判据是同一类收紧：**认事实，不认写法**。
    """
    try:
        with open(path, encoding="utf-8", errors="ignore") as fh:
            tree = ast.parse(fh.read())
    except (OSError, SyntaxError):
        return set()
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                out.add(a.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            out.add(node.module.split(".")[0])
    return out


def _shared_modules():
    """`scripts/` 下**不是闸、也不是反验**，且**至少被一道闸 import 过**的本地模块。

    **为什么要现算而不是列名单**：名单是人维护的，会与现实脱节，
    而脱节的方向永远是「多了一条没人管的名字」或「少了一条真被依赖的模块」。
    事实判据只有一条：**它被某道闸 import**——
    **被闸依赖的模块坏掉，影响面就是它依赖它的那些闸**，这个影响面是算得出来的。
    """
    out = set()
    try:
        files = os.listdir(SCRIPTS)
    except OSError:
        return out
    gates = [f for f in files if f.startswith("verify-") and f.endswith(".py")]
    bodies = []
    for g in gates:
        try:
            with open(os.path.join(SCRIPTS, g), encoding="utf-8") as fh:
                bodies.append(fh.read())
        except OSError:
            continue
    for f in files:
        if not f.endswith(".py") or f.startswith(("verify-", "selftest-")):
            continue
        mod = f[:-3]
        pat = re.compile(r"^\s*(?:import\s+%s\b|from\s+%s\s+import)" % (re.escape(mod), re.escape(mod)),
                         re.M)
        if any(pat.search(b) for b in bodies):
            out.add(mod)
    return out


def _build_invoked():
    """`scripts/` 下**被 `build-site.sh` 直接调用**的本地 `.py`（Batch 255 新增）。

    **为什么需要第三种形态**：方向三原来只认「闸」与「被闸 import 的共享模块」，
    **而 `selftest-build-record.py` 测的既不是闸、也不是共享模块**——
    它测的是**提交前的构建记录机制**，而那个机制的两端是
    `build-site.sh` 末尾调用的 `record-build-result.py`
    与 `.git/hooks/pre-commit` 调用的 `--check`。
    **实测后果**：方向三报「找不到任何 `verify-*.py` 的引用」。

    **按什么标准放行**——**和 `_shared_modules()` 同一个纪律：算出来，不列名单**。
    事实判据只有一条：**`build-site.sh` 的文本里出现了它的文件名**。
    **被构建调用的脚本坏掉，那次构建的产物就少了一块**，这个影响面算得出来。
    **它刻意不接受「我在对应关系表里登记了」**——
    **那张表是人维护的，拿它当通行证就等于「登记过就算数」**，
    **而纪律 101 说的正是那种自证。**
    """
    out = set()
    try:
        with open(os.path.join(ROOT, "build-site.sh"), encoding="utf-8") as fh:
            build = fh.read()
    except OSError:
        return out
    try:
        files = os.listdir(SCRIPTS)
    except OSError:
        return out
    #: **只看整行不是注释的行**（`lstrip()` 不以 `#` 开头）。
    #: **实测为什么必须这样**：`baseline` 与 `pngstat` 在 `build-site.sh` 里
    #: **只出现在注释里**（Batch 175 的背景说明、「判据不能因为装不上 Pillow 而崩」），
    #: **第一版「文件名出现过就算」把它们也算成了被构建调用的脚本**——
    #: **而那等于把方向三放宽成「注释里提一句就通过」**。
    #: 收紧后的实测集合是 `{scope, record-build-result}`：
    #: `scope` 出现在 `python3 -c '… import scope …'`（**真调用**），
    #: `record-build-result` 出现在末尾那行（**真调用**）。
    #: **边界的方向要写清楚**：**行尾注释仍算「出现过」**——
    #: `python3 scripts/x.py   # 顺带提一句 y.py` 会把 `y` 算进来。
    #: **这个方向的偏差是「多认一个」，不是「少认一个」**，
    #: **而多认的代价是方向三变松**——**如实记下，不假装它是严的**。
    code = "\n".join(l for l in build.split("\n") if not l.lstrip().startswith("#"))
    for f in files:
        if not f.endswith(".py") or f.startswith(("verify-", "selftest-")):
            continue
        mod = f[:-3]
        # **两种可接受的形态，都必须是「整词」而不是子串**——
        #: **实测为什么必须卡整词**：第二版用 `if f in code`（纯子串），
        #: **而 `run_gate verify-baseline.py` 里含有子串 `baseline.py`**
        #: ——**于是 `baseline` 被算成「被构建调用的脚本」，而它只出现在注释里**。
        # ①`… scripts/<name>.py`（被当脚本调）
        as_script = re.compile(r"(?<![A-Za-z0-9_.-])scripts/%s\b" % re.escape(f))
        # ②`import <name>` / `from <name> import`（被当模块用）
        as_module = re.compile(r"(?<![A-Za-z0-9_.-])(?:import|from)\s+%s\b" % re.escape(mod))
        if as_script.search(code) or as_module.search(code):
            out.add(mod)
    #: **再扩一跳**（Batch 255 实测）：`record-build-result.py` 确实被 `build-site.sh` 调用，
    #: **而它 `import buildrecord`**——**那才是反验真正要测的东西**，
    #: **只认一跳的话方向三仍会报「找不到被测对象」**。
    #: **一跳就够，本批不再往下追**：
    #: **判据的深度要有理由，多追一跳的收益递减而误认的风险递增**
    #: （「构建调用链上的东西」这个集合会迅速长到半个 `scripts/`）。
    direct = set(out)
    for mod in sorted(direct):
        src_path = os.path.join(SCRIPTS, mod + ".py")
        if os.path.isfile(src_path):
            out |= (_imported_modules(src_path) & _local_module_names())
    return out


def _local_module_names():
    """`scripts/` 下**本地模块名**（不含闸与反验）——集合要现算，不能手写。"""
    try:
        files = os.listdir(SCRIPTS)
    except OSError:
        return set()
    return {f[:-3] for f in files
            if f.endswith(".py") and not f.startswith(("verify-", "selftest-"))}


def _unreachable_cases():
    """`selftest-unreachable.sh` 的 `(说明, 上游路径, 夹具, 特征)` 四元组。

    **用 `shlex` 而不是正则**（Batch 201 实测）：那个脚本里
    `feature` 参数**单双引号混用**（用例 21/23 写的是 `'inGroup("more")'`），
    正则只能认出 20 个用例，而实际有 34 个——
    **少认 14 个还报得很绿，正是判据认写法而不认事实的形态**。
    `shlex` 走的是 shell 自己的词法，两种引号一视同仁。
    """
    import shlex as _shlex
    out = []
    for line in open(os.path.join(SCRIPTS, "selftest-unreachable.sh"),
                     encoding="utf-8"):
        st = line.strip()
        if not (st.startswith("run_case ") or st.startswith("run_pass_case ")):
            continue
        argv = _shlex.split(st)
        if len(argv) >= 5:
            # **第 6 个实参是这条用例指向的断言 id**（Batch 207 补取）——
            # 它本来就在命令行上，只是没人取，于是「用例指向的断言还在不在闸里」无从问起。
            out.append((argv[1], argv[2], argv[3].replace("$HERE", SCRIPTS), argv[4],
                        argv[5] if len(argv) >= 6 else ""))
    return out


def _registered_assertions():
    """闸 7 的登记表里**真正登记着**的断言 id 集合。

    **只认代码，不认注释**（与方向四c 同一纪律）：`canvas-library-no-import-entry`
    在 `verify-unreachable.py` 里**只剩一行注释**——
    上游修好之后断言被删了，**可那条注释还留着**。
    纯字面匹配会把它算成「还在」，于是 Batch 207 这条判据第一次跑就报绿。
    """
    path = os.path.join(SCRIPTS, "verify-unreachable.py")
    out = set()
    with open(path, encoding="utf-8") as fh:
        for line in fh:
            st = line.strip()
            if not st or st.startswith("#"):
                continue
            for m in re.finditer(r'"([a-z0-9][a-z0-9-]*)"', st):
                out.add(m.group(1))
    return out


def _slow_fixture_triples(script_name):
    """从慢反验脚本里抽出 `(目标文件, 夹具)` 三元组。

    **刻意只抽注入夹具这一步，不跑闸**：一个用例会不会作废，
    取决于「夹具能不能命中它的锚点」，而这一步**不跑任何闸**——
    实测 23 个三元组重放一遍只要 **0.6 秒**，而整个慢反验要 97 秒（快 160 倍）。
    """
    import re as _re
    text = open(os.path.join(SCRIPTS, script_name), encoding="utf-8").read()
    return [(_t.replace("$HERE", SCRIPTS), _f.replace("$HERE", SCRIPTS))
            for _t, _f in _re.findall(
                r'run_file_(?:case|pass_case)\s+"[^"]*"\s*\\?\s*\n?\s*"([^"]+)"\s+"([^"]+)"',
                text)]


def main():
    announce_fallback()
    if not os.path.isdir(SCRIPTS):
        print(f"[skip] 找不到 {SCRIPTS}，跳过反验启动核对")
        return 2
    names = selftests()
    if not names:
        print("[skip] scripts/ 下没有找到任何反验——判据可能已失效")
        return 2

    problems = []
    py_ok = sh_ok = fx_ok = 0
    # **夹具也要过语法检查**：它们语法坏了，被调用的反验同样起不来/判定作废，
    # 而 Batch 178 那一类失效恰恰是「没人跑所以没人知道」。
    for fn in sorted(os.listdir(SCRIPTS)):
        if not (fn.startswith("selftest-") and is_fixture(fn) and fn.endswith(".py")):
            continue
        try:
            with open(os.path.join(SCRIPTS, fn), encoding="utf-8") as fh:
                ast.parse(fh.read())
            fx_ok += 1
        except SyntaxError as exc:
            problems.append(
                f"方向一：注入夹具 {fn} 语法错误，调用它的反验会作废该用例：{exc}")

    for fn in names:
        p = os.path.join(SCRIPTS, fn)
        if fn.endswith(".py"):
            # 方向一：语法必须能被解释器接受（能启动的前提）
            try:
                with open(p, encoding="utf-8") as fh:
                    ast.parse(fh.read())
                py_ok += 1
            except SyntaxError as exc:
                problems.append(f"方向一：{fn} 语法错误，反验根本起不来：{exc}")
                continue
            # 方向二：它 import 的本地模块必须真实存在且能 import
            try:
                with open(p, encoding="utf-8") as fh:
                    tree = ast.parse(fh.read())
            except OSError:
                continue
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                    mod = node.module.split(".")[0]
                    if mod in STDLIB or _looks_third_party(mod):
                        continue
                    if not os.path.isfile(os.path.join(SCRIPTS, mod + ".py")):
                        problems.append(
                            f"方向二：反验 import 了 `{mod}`，但 scripts/{mod}.py 不存在"
                            "　→ 反验**起不来且没有任何其他信号**")
                        continue
                    r = subprocess.run(
                        [sys.executable, "-c",
                         "import sys; sys.path.insert(0, %r); import %s" % (SCRIPTS, mod)],
                        capture_output=True, text=True)
                    if r.returncode != 0:
                        problems.append(
                            f"方向二：反验 import 的本地模块 {mod} **在真实环境里也 import 不了**："
                            f"{(r.stderr or '').strip().splitlines()[-1][:90]}")
        else:
            # 方向一：shell 反验必须通过 `bash -n`（只查语法，不执行）
            r = subprocess.run(["bash", "-n", p], capture_output=True, text=True)
            if r.returncode != 0:
                problems.append(
                    f"方向一：{fn} 没通过 `bash -n`，反验起不来："
                    f"{(r.stderr or '').strip()[:90]}")
                continue
            sh_ok += 1

    # 方向二之二：**被测闸门** import 的本地模块必须真的能 import。
    # 现场数据（Batch 179 实测）：**没有任何一份反验自己 import 本地模块**——
    # 它们只是把闸门**复制**进临时目录。所以 Batch 178 那 34 例的失败面
    # 并不在「反验起不来」，而在「**反验复制过去的闸门起不来**」。
    # **第一版判据核错了对象**：它去查反验的 import，于是既漏报了真问题、
    # 又让人以为闸 18 已经覆盖了 Batch 178 那次失效。**核错对象等于没核。**
    for gate_fn in sorted(os.listdir(SCRIPTS)):
        if not (gate_fn.startswith("verify-") and gate_fn.endswith(".py")):
            continue
        path = os.path.join(SCRIPTS, gate_fn)
        try:
            with open(path, encoding="utf-8") as fh:
                gtree = ast.parse(fh.read())
        except (OSError, SyntaxError):
            continue
        for node in ast.walk(gtree):
            if isinstance(node, ast.ImportFrom) and not node.level and node.module:
                mod = node.module.split(".")[0]
                if mod in STDLIB or _looks_third_party(mod):
                    continue
                if not os.path.isfile(os.path.join(SCRIPTS, mod + ".py")):
                    problems.append(
                        f"方向二之二：闸门 {gate_fn} import 了 `{mod}`，但 scripts/{mod}.py 不存在"
                        "　→ **任何**跑它的反验都会起不来（Batch 178 实测 34 例）")
                    continue
                r = subprocess.run(
                    [sys.executable, "-c",
                     "import sys; sys.path.insert(0, %r); import %s" % (SCRIPTS, mod)],
                    capture_output=True, text=True)
                if r.returncode != 0:
                    problems.append(
                        f"方向二之二：闸门 {gate_fn} 依赖的本地模块 {mod} import 不了："
                        f"{(r.stderr or '').strip().splitlines()[-1][:90]}")

    # 方向三：每份反验都要能说出自己测的是哪道闸（或哪个被闸依赖的共享模块）
    #
    # **Batch 198 扩了「或哪个共享模块」**：本批给 `beefsrc.py` 配反验时撞上的——
    # `beefsrc` 是 15 道闸共同依赖的路径解析模块，**它不是闸，也不对应任何一道闸**，
    # 而原判据只认 `verify-*.py`，于是它报「找不到被测闸门」。
    # 扩法的关键是**那个集合是算出来的、不是名单**：
    # 「`scripts/` 下不是 verify-/selftest- 的 .py，且**至少被一道闸 import 过**」——
    # **`beefsrc` 改坏时 15 道闸一起失效，这就是「它值得有反验」的事实依据**，
    # 而不是一个我随手维护的白名单（那正是纪律 101 的形态）。
    # 认闸名、认模块名都是「按写法判定」的老毛病；**判据认的仍然是事实**。
    shared = _shared_modules() | _build_invoked()
    for fn in names:
        p = os.path.join(SCRIPTS, fn)
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except OSError:
            continue
        if re.search(r"verify-[a-z0-9-]+\.py", text):
            continue
        if shared & _imported_modules(p):
            continue
        problems.append(
            f"方向三：{fn} 里找不到任何 verify-*.py 的引用，"
            f"也没有提到被闸依赖的共享模块或被构建调用的脚本（现有：{'、'.join(sorted(shared)) or '无'}）"
            "　→ 它没有指向被测对象；「反验 ↔ 闸」的对应关系会退化成散文"
            "（Batch 169 方向十一治的正是这个）")

    # 方向四：慢反验登记表**双向**自证（Batch 180 改）
    #
    # **原来只有一个方向**：核「登记了的，理由是否仍成立」。
    # 漏掉的是「**该登记的没登记**」——于是 `SLOW_BUDGET_MS` 那个阈值
    # **从来没被读过**，却在上方注释里写着「取自实测，不是拍的」。
    # **注释在撒谎，而撒谎不产生任何信号。**
    #
    # 改成三个方向：
    #   ④a 登记项确实存在，且**声明的耗时真的超过阈值**（否则它其实不慢，该删）；
    #   ④b 登记理由点名的判据仍在上游（原有那条，保留）；
    #   ④c **反向**：每份反验若被 build-site.sh 自动调用，就**不该**出现在慢表里
    #       （能自动跑还登记成「只能手动跑」，说明登记过期了）。
    # **④c 是可静态判的**：build-site.sh 里出现了它的名字就是「会自动跑」。
    for fn, info in SLOW.items():
        path = os.path.join(SCRIPTS, fn)
        if not os.path.isfile(path):
            problems.append(f"方向四a：SLOW 里登记了 {fn}，但它不存在（登记已过期，请删）")
            continue
        # ④a：声称慢，就得真的超过阈值
        secs = info.get("seconds")
        if not isinstance(secs, (int, float)) or secs <= 0:
            problems.append(
                f"方向四a：{fn} 的登记里没有正的 seconds 字段"
                "　→ 判据无法核「它到底慢不慢」，等于这张表不受任何约束")
        elif secs <= SLOW_BUDGET_SEC:
            problems.append(
                f"方向四a：{fn} 登记为慢反验（{secs}s），但没超过阈值 {SLOW_BUDGET_SEC}s"
                "　→ 它其实不慢（或阈值该调了），请从表里删掉或更新实测值")
        src, needle = info["anchor"]
        probe = os.path.join(SCRIPTS, src)
        try:
            with open(probe, encoding="utf-8") as fh:
                body = fh.read()
        except OSError:
            problems.append(f"方向四b：{fn} 的登记理由点名了 {src}，但读不到它")
            continue
        if needle not in body:
            problems.append(
                f"方向四b：{fn} 的登记理由点名了 {src} 里的 {needle!r}，但那里已没有它"
                "　→ 登记理由失效，**要么它其实不慢了（该放进构建），要么理由要重写**")
        # ④c：能被构建自动调用的反验，不该登记成「只能手动跑」
        # **只认真正执行的代码，不认注释**（上线首跑就误报，Batch 180）：
        # `build-site.sh` 的注释里**正写着**这两个反验的名字与实测秒数
        # （那是给人看的说明），而纯字面匹配把它们当成了「已被自动调用」。
        # **注释不是调用点**——与闸 7「URL 写出点只看代码不看注释」同一条纪律。
        if _build_invokes(fn):
            problems.append(
                f"方向四c：{fn} 已登记为「慢、只能手动跑」，"
                "但 build-site.sh **真的执行**了它（注释里提到不算）"
                "　→ 登记与现实脱节；要么去掉登记，要么把它从构建里拿掉，二者必须一致")

    # ④d（**本批新增，也是最重要的一条**）：反向核对**没有漏登记**。
    # 为什么这条只能靠人工跑：判据无法在构建期知道谁慢——
    # **除非有人把实测值写进来**。所以本闸要求：
    # **凡是在 SLOW 里没登记、也没被 build-site.sh 自动调用的反验，
    # 必须在 `SELFTEST_COSTS` 里留下一条实测耗时**。
    # 换句话说：**「我没登记它慢」必须是一个有据的说法，而不是「我没量过它」。**
    # 这正是纪律 112 的正面用法：**与其要求量小到大有人在看，
    # 不如让「没量过」本身成为一个可被看见的状态。**
    known = set(SLOW)
    auto = set(fn for fn in names if _build_invokes(fn))
    for fn in sorted(set(names) - known - auto):
        cost = SELFTEST_COSTS.get(fn)
        if cost is None:
            problems.append(
                f"方向四d：反验 {fn} 既没登记为慢、也没被构建自动调用，"
                "**且 `SELFTEST_COSTS` 里没有它的实测耗时**"
                "　→ 「我没登记它慢」现在等于「我没量过它」；"
                "跑一次（多数只需几秒到几十秒）把秒数填进去即可")
        elif cost > SLOW_BUDGET_SEC:
            problems.append(
                f"方向四d：反验 {fn} 实测 {cost}s，**超过阈值 {SLOW_BUDGET_SEC}s 却没登记为慢**"
                "　→ 这正是原判据漏掉的那一整类：新反验变慢时无人提醒")

    # ── 方向五（Batch 200）：慢反验的注入夹具**必须还能命中它的锚点** ──
    #
    # **为什么需要它**（Batch 198 实测到的形态）：
    # `selftest-meta.sh` 跑出来是「通过 34 / 失败 0 / **作废 2**」——
    # 而作废的两条是**方向十一最要紧的两条**。作废的成因是夹具的锚点断言失配，
    # 而那一步**不跑闸、只要 0.6 秒**。**没人跑慢反验，于是没人知道那两条用例
    # 早就在「什么都不验」的状态里待了很久**（纪律 178）。
    # 本方向让这件事进构建：**97 秒的东西里，只有 0.6 秒那一段与「有没有在验」有关。**
    #
    # **边界必须写清楚**：
    #   · **只查前提，不查结果**——「夹具能不能命中锚点」≠「用例会不会通过」；
    #   · **只覆盖 `selftest-meta.sh`**——`selftest-unreachable.sh` 的注入目标是
    #     **上游仓里那个 ref 上的文件**（它先走 git plumbing 造合成 ref），
    #     重放成本与 97 秒那一段同量级，**本方向不覆盖，如实记在这里**。
    # **目标文件不在场就跳过，而不是报问题**——前提无法评估 ≠ 判为失败
    # （闸 9 方向一已经负责「基本输入存在性」）。这一条也是反验沙箱能用的前提：
    # 沙箱只搬 `scripts/`，根目录的 `AUDIT-RULES.md` 本来就不在里面。
    fx_checked, fx_skipped, fx_void = 0, 0, []
    for target, fixer in _slow_fixture_triples("selftest-meta.sh"):
        if not os.path.isfile(fixer) or not os.path.isfile(target):
            fx_skipped += 1
            continue
        try:
            with open(target, encoding="utf-8") as fh:
                r = subprocess.run([sys.executable, fixer], stdin=fh,
                                   capture_output=True, text=True, timeout=30)
        except OSError as exc:
            fx_void.append((os.path.basename(fixer), str(exc)[:60]))
            continue
        fx_checked += 1
        if r.returncode != 0:
            tail = (r.stderr or "").strip().splitlines()
            fx_void.append((os.path.basename(fixer),
                            (tail[-1] if tail else "无输出")[:70]))
    if not _slow_fixture_triples("selftest-meta.sh"):
        problems.append(
            "方向五：**从 `selftest-meta.sh` 里抽不出任何注入夹具三元组**——"
            "要么它的用例调用格式变了，要么整份脚本被清空"
            "　→ **「一个都没检查」与「全部都检查了」必须长得不一样**（纪律 156/159）")
    for fixer, why in fx_void:
        problems.append(
            f"方向五：慢反验的夹具 `{fixer}` **已经打不中它的锚点**（{why}）——"
            "用到它的用例会**作废**，而作废的输出说的是「前提不成立」，"
            "**它不算通过也不算失败**"
            "　→ 用例正在「什么都不验」：锚点多半是文件里某段被改写的文本，"
            "**要么改夹具的锚，要么改那段文本**")

    # ── 方向五之二（Batch 201）：第二份慢反验的两个作废条件 ──────────────
    #
    # **它比方向五多一个条件**：`selftest-unreachable.sh` 的每条用例有
    # **两个**会作废的点（脚本里各有一行 `VOID=$((VOID+1))`）：
    #   ① **合成 ref 失败**——夹具处理不了目标文件；
    #   ② **合成 ref 里找不到「修复特征」**——夹具跑了，但它没真的注入那个特征。
    # **两个都不需要那套 git plumbing**：`build_ref` 的内容来自
    # `git show origin/main:<path> | python3 <夹具>`，
    # **而 plumbing 只是为了产出一个 commit**——前提校验用不到它。
    # 实测 34 个用例重放一遍 **2.1 秒**，而整个慢反验约 25 分钟（快 700 倍）。
    #
    # **刻意用 `origin/main` 而不是手册声明的基线**：慢反验自己就是从
    # `origin/main` 造合成 ref 的，**用别的 ref 重放就答不上
    # 「我下次真跑它会不会作废」这个问题**。代价是上游一动这条方向就可能变红，
    # **而那正是它该说的话**（上游改了路径 → 那条用例会作废 → 去改夹具）。
    # **上游取不到就跳过，不是失败**——前提无法评估 ≠ 判为失败。
    ur_checked, ur_skipped, ur_void = 0, 0, []
    #: **`_gone` / `_labels` 原来只在下面那个 `else:` 分支里赋值，
    #: 而 `if _gone:` 在分支之外**——上游取不到时第 1026 行直接
    #: `UnboundLocalError`（Batch 254 实测，见上面那段注释）。
    _gone = 0
    _labels = 0
    #: **rc=2 而不是 rc=1**：这是**环境的缺口**，不是「不一致」——
    #: 反验文件头把「拿环境的缺口冒充『反验坏了』」列为判据最坏的一种错，
    #: 而 12 行之上那条「一个用例都解析不出来」是**文件坏了**、才用 rc=1。
    #: **两件事长得极像而答案必须不同：谁坏了，决定报什么。**
    env_gap = False
    _cases = _unreachable_cases()
    if not _cases:
        problems.append(
            "方向五之二：**从 `selftest-unreachable.sh` 里一个用例都解析不出来**——"
            "要么调用格式变了，要么脚本被清空"
            "　→ **「一个都没检查」与「全部都检查了」必须长得不一样**（纪律 156/159）")
    #: **Batch 254 实测：这条降级路径在真树上**是**可达的，
    #: 而它走通之后的形态不是「静默跳过」，是 `UnboundLocalError`。**
    #:
    #: **本批在这里犯过一次错，值得记下来**：我先量到「全树被 try 包住的本地 import
    #: 只有这一处」，就给它加了一条「全部跳过必须报 rc=2」的判据，
    #: 又连试三种注入（删 `beefsrc.py` / 改坏它的语法 / 让 `resolve_src` 抛异常），
    #: **三次都是整个脚本崩掉加 Traceback**，于是我判「这条降级路径不可达」，
    #: **把判据撤回了**。**那个结论是错的。**
    #:
    #: **错在哪**：三次注入**全部打在「抛异常」这一支上**，
    #: 而 `resolve_src()` 在**没有候选成立时是 `return (None, False)`——不抛异常**。
    #: `baseline.py` 第 66 行在模块顶层就调它，**返回 None 它照样过**；
    #: 于是脚本活着走到下面这个 `try`，`_up = None`，
    #: **`ur_skipped = len(_cases)` 全部用例被跳过**——
    #: **真正的失效形态是「上游不在场时，这道闸一条都不查却照样收下」。**
    #: 改注入方式之后（把 `FALLBACK_ABS` 指向不存在的路径），
    #: 实测 rc=1，报的是 **`UnboundLocalError: local variable '_gone'
    #: referenced before assignment`**——
    #: **而 `_gone` 只在下面那个 `else:` 分支里赋值，`if _gone:` 却在分支之外。**
    #: **一个指向错处的报错，比不报错更贵：它把人指向第 1026 行的作者，
    #: 而真正的原因是上游不在场。** 本批已把它初始化掉。
    #:
    #: **推论（纪律 279 推论一的反面，也是它真正的样子）**：
    #: **给不可达路径加判据是假账，给可达路径加判据却用「错的那一支」去做实验，
    #: 同样会得出「不可达」的假结论。**
    #: **量一条降级路径的可达性，要分别试「抛异常」与「返回空」两种形态——
    #: 而在 Python 里，「依赖取不到」几乎总是「返回 None」而不是「抛异常」。**
    #:
    #: **留这段 `try` 在这里的理由**：它包的是 `import beefsrc` 与
    #: `beefsrc.resolve_src()`，**而这两个都已经在 `baseline.py` 第 53/54/66 行
    #: 被做过一遍了**（`baseline` 用的就是同一份 `beefsrc.resolve_src`）。
    #: **所以这里不是「保护」而是「重复调用同一份函数」**——
    #: 删掉它会改动 Batch 197 以来一直在跑的行为，
    #: **本批只把「它保护什么、不保护什么」写清楚，并补上缺失的那句报告。**
    _up = None
    try:
        sys.path.insert(0, SCRIPTS)
        import beefsrc
        _up, _ = beefsrc.resolve_src()
    except Exception:                                    # noqa: BLE001
        _up = None
    if _up is None:
        ur_skipped = len(_cases)
        env_gap = True
        print("方向五之二：上游 BeefTV 取不到，"
              "`selftest-unreachable.sh` 的 %d 个用例**全部跳过**——"
              "`beefsrc.resolve_src()` 一个候选都不成立时是 "
              "`return (None, False)`，**不抛异常**，所以这里不会崩。"
              % len(_cases))
        print("  → **这不是「没发现问题」，是「一个都没检查」**（纪律 156/159）："
              "判据返回 2（未能核对）而不是 0——**环境缺口不是不一致**。")
    else:
        registered = _registered_assertions()
        _gone = 0
        _labels = 0
        for desc, path, fixer, feature, assertion in _cases:
            # **第四个参数不一定是指向登记表的 id**（Batch 207 实测）：
            # 34 条里有若干条写的是**闸 7 输出里那句中文标签**（如「9 个参数零写出」，
            # 它来自扫描型检查，根本不在 REGISTRY 里）。**把它们一律当成 id 去核，
            # 就会造出 3 条假阳性**——而假阳性会让人学会忽略这条判据（纪律 166）。
            # 所以：**形态不是 id 的就跳过，并如实报出跳过了几条**——
            # **判据核不了的东西必须说出来，而不是装作核过了。**
            if not re.fullmatch(r"[a-z0-9][a-z0-9-]*", assertion or ""):
                _labels += 1
                # **必须计入「跳过」**（Batch 207 当场修的记账漏洞）：
                # 不计的话汇总行会写成「30/33 成立、**0 个跳过**」，
                # **读起来像 3 条前提不成立**——而它们只是本判据核不了。
                # **一个不记账的跳过，会让「没查」看起来像「查了没成」。**
                ur_skipped += 1
                continue
            if assertion not in registered:
                # **前提成立、夹具跑得通，可这条用例永远不可能过**——
                # 因为它指向的断言**已经不在闸的登记表里了**。
                # 症状是「闸门**未**报失效」，**读起来像闸坏了**，
                # 而真相是「被测的东西被删了，而用例没跟着删」。
                _gone += 1
                ur_void.append((desc[:26],
                                "它指向的断言 `%s` 已不在 `verify-unreachable.py` 的登记表里" % assertion))
                continue
            if not os.path.isfile(fixer):
                ur_void.append((desc[:26], "夹具文件不存在"))
                continue
            show = subprocess.run(["git", "-C", _up, "show", "origin/main:" + path],
                                 capture_output=True, text=True, errors="replace")
            if show.returncode != 0:
                ur_void.append((desc[:26], "读不到 origin/main:%s" % path))
                continue
            r = subprocess.run([sys.executable, fixer], input=show.stdout,
                               capture_output=True, text=True, errors="replace",
                               timeout=30)
            if r.returncode != 0:
                tail = (r.stderr or "").strip().splitlines()
                ur_void.append((desc[:26],
                                "夹具失败：" + (tail[-1] if tail else "?")[:50]))
                continue
            ur_checked += 1
            if feature not in r.stdout:
                ur_void.append((desc[:26],
                                "变换结果里找不到「修复特征」[%s]" % feature[:24]))
    if _gone:
        print("方向五之二：%d 条用例指向的断言**已从闸里删掉**——"
              "前提成立、夹具跑得通，而它们永远不可能过。" % _gone)
        print("  → **删用例，别改闸**：断言没了是因为上游真的修了，"
              "把它加回闸等于把一条已经失效的声明重新立起来。")
    if _labels:
        print("  （另有 %d 条用例的第四个参数是**中文标签**而不是登记表 id，"
              "本判据核不了它们——**如实报出，不装作核过了**）" % _labels)
    for desc, why in ur_void:
        problems.append(
            f"方向五之二：慢反验 `{desc}` 的前提已不成立（{why}）——"
            "**这条用例会作废，而作废的用例什么都不验却不算失败**（纪律 178）"
            "　→ 上游 `origin/main` 改了这段内容或路径：要么改夹具的锚，"
            "要么把该用例移到不再成立的位置")

    # 方向十五（**Batch 209 新增**）：反验引用的**被删掉的**同层文件必须清干净。
    #
    # **背景是一次实测事故，不是推演**：Batch 207 删掉了注入夹具
    # `selftest-fix-2-import-entry.py`，写在账本里的理由是
    # 「**它只被这一条用**」——**而这个理由从来没被核过**：
    # 闸 18 自己的反验 `selftest-selftest-bootable.py` 也引用它。
    # 于是那条用例一跑就 `FileNotFoundError`，
    # 而**反验不在构建路径上**（闸 18 明确写下的设计前提），**账面全绿**。
    # Batch 209 第一次真跑那份反验就撞上了，**而且撞出来的形态比 Batch 207 那次更隐蔽**：
    # 那份反验的 `main()` 只接 `AssertionError`，别的异常一路抛到解释器顶端，
    # 于是**已经跑完的 19 例结果一行都没打印**，整份报告只剩一行 Traceback——
    # **「20 例全过」与「一份报告都没交出来」在退出码上都是非 0，肉眼分不开。**
    #
    # ── **第一版被判据自己的数据推翻，这里必须写下来** ──
    # 第一版核的是「反验代码里引用的每个同层文件名都得在场」。
    # **它一次跑出 10 条，其中 9 条是假的**：注入夹具**本来就该**引用现场不存在的名字
    # （`write(os.path.join(tmp, "scripts", "selftest-orphan.py"))` 是把文件**造出来**，
    #  `s.replace('verify-tables.py', 'verify-foo.py')` 是往**别的文件的内容里**注入字符串，
    #  而 `| scripts/verify-injected.py（并不存在） |` 是**写进手册的表格文本**）。
    # **假阳性率 9/10 的判据不能上线**（纪律 166：首跑全红同样不是证据）。
    #
    # ── **收窄的依据是一个量出来的分界，不是拍脑袋** ──
    # 逐个查那 10 个名字在 git 历史里的下落，结果是**分得干干净净的**：
    # **10 个里只有 1 个真的存在过**（`selftest-fix-2-import-entry.py`，正是事故主角），
    # **其余 9 个从未存在过**——它们是注入夹具**带进来**的名字，不是**丢掉的**引用。
    # 于是判据收窄成「**只报曾经存在过、现在不在场的名字**」：
    # **它精确对准这次事故的形态（被删的引用），实测假阳性 0/9。**
    # **代价也要写清楚**：引用一个**从未存在过**的错名字（打错字、写错版本号）本方向看不见。
    # **判据的盲区要自己写出来，否则下游会把它当成事实**（纪律 196）。
    dang = _deleted_sibling_names()
    _st = [f for f in os.listdir(SCRIPTS)
           if f.startswith("selftest-") and f.endswith((".py", ".sh"))]
    if dang is None:
        # 取不到就是**核不了**，不是「没有问题」——**如实报出，不装作核过了**（纪律 203）
        print("方向十五：[不适用] 本手册目录不在 git 检出里（或读不到删除历史），"
              "**「被删掉的引用」这一项本轮没核**——如实报出，不装作核过了")
    else:
        _hits = 0
        for fn in sorted(_st):
            path = os.path.join(SCRIPTS, fn)
            try:
                body = _code_only(path)
            except (OSError, SyntaxError):
                continue
            for ref in sorted(set(DANGLING_RE.findall(body)) & dang):
                _hits += 1
                problems.append(
                    f"方向十五：{fn} 引用了 `{ref}`，而它**已经被删掉**"
                    "　→ 反验不在构建路径上，引用一个被删掉的文件**只有真跑它才会炸**，"
                    "而炸起来常常是「整份报告只剩一行 Traceback」（Batch 209 实测）"
                    "　→ 删它之前先确认「只被这一处用」：**这句话 Batch 207 写过、"
                    "也从没被核过**，而它就是那次漏网的直接原因")
        if _hits == 0:
            print("  方向十五：%d 份反验与注入夹具的代码里"
                  "**没有引用指向任何一个被删掉的同层文件**"
                  "（`scripts/` 下历史上删过 %d 个文件）"
                  "　→ **看不见的形态也要说清楚**：引用一个**从未存在过**的错名字"
                  "本方向抓不到（判据认的是「删过」这个事实，不是名字长得像不像）"
                  % (len(_st), len(dang)))

    # 方向十三（**Batch 204 新增**）：**闸的失败必须真的被说出来**。
    # 背景是实测出来的：`run_gate` 原来写成 `out="$(python3 ...)"; rc=$?`，
    # 而在 `set -e` 下这一行会让整份构建脚本当场退出——
    # `rc=$?` 与三段分支**一行都执行不到**，`$out` 也随退出被丢掉。
    # 于是闸 21 报红时，构建**只留下一个 rc=1，日志停在闸 20，再无一句话**。
    # **一个从不执行的报错分支，比没有报错分支更坏**：它让人以为构建是透明的。
    # 这里**行为可判**：抠出真函数、配 stub 闸真跑一遍，三种退出码各问一次。
    _try = _run_gate_probe
    rc1, out1 = _try(1)
    if rc1 != 1 or "核对不一致" not in out1 or "试闸" not in out1 or "闸的输出" not in out1:
        problems.append(
            "方向十三：闸报「不一致」时，构建**没有把它说出来**（rc=%d）"
            "　→ `run_gate` 里的 `out=\"$(...)\"` 少了 `|| rc=$?`，"
            "`set -e` 会让它当场退出，三段分支永远执行不到；"
            "**闸名与闸的输出都会一起被丢掉**" % rc1)
    rc2, out2 = _try(2)
    if rc2 != 1 or "未能核对" not in out2 or "核对不一致" in out2:
        problems.append(
            "方向十三：闸报「未能核对」时，构建**没说清楚**（rc=%d）"
            "　→ 退出码 2 **不得**被说成「核对不一致」——那会把人引去手册里"
            "找根本不存在的问题（Batch 160 立这个码的理由）" % rc2)
    # **成功路径不检查闸名**：`ok "$out"` 只打闸自己的输出，
    # 闸名只出现在 `warn`/`fail` 两条分支里——**这是既有设计，不是缺陷**，
    # 而判据要按事实写：第一版这里也查了「试闸」，于是 rc=0 正常却报红。
    # **判据把「没检查过的事实」当成失败，等于自己制造假阳性。**
    rc0, out0 = _try(0)
    if rc0 != 0 or "闸的输出" not in out0 or "[ FAIL " in out0:
        problems.append(
            "方向十三：闸 rc=0 时，构建**没有正常收下它的输出**（rc=%d）——"
            "这一支是**不误伤**：修 run_gate 时最容易把成功路径也弄坏" % rc0)

    # **方向十三之四（Batch 267 新增）：rc=0 却一句话都没说，必须报。**
    # **背景是 Batch 266 的两次实测**：占位符名写错抛 `NameError`、正则 `$$?` 触发
    # `re.error: nothing to repeat`——**两次脚本都零输出、rc=0，而构建全绿**。
    # **为什么前面三支测不到**：`stub` **总是会 print 两行**，
    # **于是「rc=0 且零输出」这个形态从来没被造出来过**。
    #: **`silent=True` 的 stub 是合法的**：它 `import sys`、`def main(): return 0`、
    #: **`sys.exit(main())` 正常退出**——**所有核「写法」的判据都看不出它有病**。
    #: **而它是最坏的一支**：闸声称「26 份已核」，其实一份都没核。
    rcs, outs = _try(0, silent=True)
    if rcs == 0 or "一句话都没说" not in outs:
        problems.append(
            "方向十三之四：闸 **rc=0 却一句话都没说**时，构建**判它通过**（rc=%d）——"
            "　→ `run_gate` 的 rc=0 分支只做 `ok \"$out\"`，**而输出为空时它打印的"
            "就是一个空的 `[ ok ]` 行**；"
            "**「判据崩了」与「判据核过了」在构建输出上完全一样**（Batch 266 实测两次，"
            "两次构建全绿）；"
            "**它属于 rc=2 而不是 rc=1**：这不是「查出问题」，是「根本没查」"
            "（Batch 160 立 rc=2 的理由）" % rcs)

    # 方向十四（**Batch 205 新增**）：**shell 脚本里不得有会在 UTF-8 locale 下炸掉的变量展开**。
    # 背景是实测事故：三份 shell 反验共 33 处 `$var：`，
    # 在 `LC_CTYPE=C.UTF-8` 下 `set -u` 直接报「`desc?: unbound variable`」——
    # **而 `desc` 上一行刚 `local` 过**。同一台机器、不设那个变量时它们全绿，
    # **所以「默认环境下看不出来」正是它藏了这么久的原因**。
    broke, bashver = _locale_breaks_it()
    why = ("**本机实测会坏**（%s，LC_CTYPE=C.UTF-8）" % bashver if broke
           else "**本机 bash 实测不复现**（%s）——仍然按最坏情况要求写 `${}`，"
                "因为出事的是别人的机器" % bashver)
    for path in _shell_files():
        rel = os.path.relpath(path, ROOT)
        with open(path, encoding="utf-8") as fh:
            for n, line in enumerate(fh, 1):
                if line.lstrip().startswith("#"):
                    continue
                for m in UNSAFE_VAR_RE.finditer(line):
                    j = m.end()
                    if j < len(line) and ord(line[j]) > 127:
                        problems.append(
                            "方向十四：`%s` 第 %d 行的 `$%s` 后面紧跟一个非 ASCII 字符"
                            "（%r）——%s"
                            "　→ 改成 `${%s}`：中文全角标点紧跟变量时，"
                            "UTF-8 locale 下的 bash 会把那些字节算进变量名"
                            % (rel, n, m.group(1), line[j], why, m.group(1)))
                        break

    # 方向十六（**Batch 210 新增**）：**非慢反验必须真的跑通**，而不只是「能启动」。
    # **它治的是 Batch 209 那次事故暴露的最后一层**：用例 9/10 的注入锚点
    # 被一次例行的数据刷新弄失效之后，两条都记成「作废」——
    # **而方向一（能启动）、方向十五（引用没悬空）、方向五/五之二（慢反验前提）
    # 全都照样报绿**。**反验不在构建路径上，而「作废」在退出码上与「失败」难以分辨**：
    # 那次只有一次人工普查才撞见。
    # **本方向问的是行为，不是写法**：逐份真跑，看退出码。
    fleet_all = [n for n in names if n != "selftest-selftest-bootable.py"]
    fleet = [n for n in fleet_all if n not in SLOW]
    if "selftest-selftest-bootable.py" not in SLOW:
        problems.append(
            "方向十六：`selftest-selftest-bootable.py` **不在 SLOW 登记里**——"
            "它是闸 18 自己的反验，被方向十六真跑会**无限递归**"
            "　→ 请把它登记进 SLOW 并写明理由")
    # **前提：真跑不许改现场。** 先记一份 git 状态，跑完再记一份，只比差集。
    # **这不是「现场干不干净」，而是「跑完有没有变」**——
    # 这个仓里别人正在改东西是常态，所以只能比差集，不能比绝对状态。
    def _snapshot():
        g = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--", "."],
                           capture_output=True, text=True)
        return None if g.returncode != 0 else {l for l in g.stdout.split("\n") if l.strip()}

    # **先核前提，再跑**（与 `selftest-zero-input.py` 的方向三同一套理由）：
    # 闸 18 的反验把自己的每一例都放进一个**只有 `scripts/` 与 `build-site.sh` 的沙箱**，
    # **那里没有手册正文**。真跑任何一份内容相关的反验都会得到一个
    # **由环境造成的假失败**——而**拿环境的缺口冒充「反验坏了」，
    # 是判据最坏的一种错**：它会让人去改反验，而真正的问题在沙箱。
    # （这一版最初写的是「用白名单缩到一两份」，**实测证明那条路走不通**：
    #  缩了范围并不能让沙箱变得能跑，而缩了范围还得在输出里解释一遍——
    #  **机制多一个，可错的地方就多一个**。改成核前提更短也更准。）
    # **这三条不是猜的，是实测里真实缺过的**（先做了一版「≥5 份 .md」，
    # 结果 `selftest-exclusions.py` 报缺 `task-inventory.yml`、
    # `shot-drift` / `shot-pixels` 报缺真图——**判据把自己的环境缺口
    # 报成了三份反验坏了**）。所以逐条写清缺的是什么、为什么需要。
    need = [("task-inventory.yml", "任务台账（`selftest-exclusions.py` 要读它）"),
            ("10-tasks", "任务页目录"),
            ("screenshots", "截图目录（`shot-pixels` / `shot-drift` 要读真图）")]
    lack = [d for d, _ in need if not os.path.exists(os.path.join(ROOT, d))]
    pngs = 0
    sd = os.path.join(ROOT, "screenshots")
    if os.path.isdir(sd):
        pngs = len([f for f in os.listdir(sd) if f.endswith(".png")])
    if lack or not pngs:
        print("方向十六：[不适用] 这里**不是一棵完整的手册树**（%s），本轮 %d 份一份不跑——"
              "**不拿环境的缺口冒充「反验坏了」**"
              % ("；".join("%s 缺失（%s）" % (d, w) for d, w in need if d in lack)
                 or "screenshots 下 0 张 .png",
                 len(fleet)))
        fleet = []
    tally = {}          # fn -> (合计, 形态)；方向十七直接用方向十六真跑出来的输出
    before = _snapshot()
    ran = ok = 0
    fleet_cost = 0.0
    # **整体预算（秒）**。**Batch 212 改的：原来写 300，那是拍的。**
    # 现在有依据：**同一天同一台机器 8 次实测 29.2 / 29.4 / 29.7 / 30.1 / 30.4 /
    # 35.8 / 42.0 / 84.8 秒**——典型约 30 秒，**而那个 84.8 是 2.8 倍的离群值**。
    # 600 秒 = **观测最大值的 7 倍**，方向取安全那侧（纪律 204 的同一个道理：
    # **守卫阈值的常数，偏差的危险方向只有一边，而这里危险的是「太紧」**——
    # 太紧会让**机器慢的人**替反验背锅）。
    # 单份上限 120 秒防的是另一件事：**某一份卡死**（实测最慢的一份 11.7 秒）。
    budget = 600.0            # **超了要报，不能默默不跑**
    per = 120.0               # 单份上限（秒）：实测最慢的一份 11.7 秒，这里留 10 倍
    for fn in fleet:
        if budget - fleet_cost <= 0:
            problems.append(
                f"方向十六：整体预算 {budget:.0f} 秒用尽，**剩下 {len(fleet) - ran} 份"
                f"反验没有跑**（本轮已跑 {ok}/{len(fleet)} 份全绿）"
                "　→ **先分清是哪一种**：**这通常意味着机器太慢，而不是反验坏了**"
                "（预算 600 秒 ≈ 观测最大值 84.8 秒的 7 倍）；"
                "真要提速就把慢的那几份登记进 SLOW")
            break
        t0 = time.time()
        try:
            r = subprocess.run(
                ["bash", fn] if fn.endswith(".sh") else [sys.executable, fn],
                cwd=SCRIPTS, capture_output=True, text=True,
                timeout=min(per, budget - fleet_cost))
            rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = None, ""
        d = time.time() - t0
        fleet_cost += d
        ran += 1
        if rc == 0:
            ok += 1
            tally[fn] = _tally(out)
            continue
        tail = " / ".join(l.strip() for l in out.strip().split("\n") if l.strip())[-220:]
        why = (f"**超时**（上限 {per:.0f} 秒，实测 {d:.1f} 秒）" if rc is None
               else f"退出码 {rc}")
        problems.append(
            f"方向十六：反验 `{fn}` **真跑没跑通**（{why}，{d:.1f} 秒）"
            "　→ 方向一只保证它「能启动」，**启动得了不等于跑得过**。"
            "**作废的用例在退出码上与失败难以分辨**——Batch 209 实测有两条作废了整整一个批次，"
            f"而闸 18 全绿。实际输出末尾：{tail or '(无输出)'}")

    after = _snapshot()
    if before is None or after is None:
        print("方向十六：[不适用] 本手册目录不在 git 检出里，"
              "**「真跑有没有改现场」这一项本轮没核**（%d 份照跑）——如实报出，不装作核过了"
              % ran)
    else:
        dirty = after - before
        if dirty:
            problems.append(
                f"方向十六：真跑 {ran} 份反验之后**现场多了 {len(dirty)} 处改动**："
                f"{'、'.join(sorted(dirty)[:3])}"
                "　→ **反验只该在临时目录里动手脚**；它改了真实手册，"
                "下一次构建读到的就不是我们以为的那份了"
                "（`selftest-meta.sh` 会原地改 15 个真实文件，**所以它必须留在 SLOW 里**）")
    # 方向十七（**Batch 211 新增**）：**对应关系表登记的「例数」必须等于那份反验真跑时自己报的合计**。
    # **它不额外跑任何东西**——方向十六**已经把输出拿在手里了**，真值就在里面。
    # **为什么不走「让 27 份反验各自声明一个 CASE_COUNT」那条路**：
    # 那要给 27 个文件逐个加常量与断言，而**其中一份的基线用例只在失败时计数**
    # （`selftest-tables.sh`：通过时不计、失败时计），**声明的数会随绿红变化**——
    # **自断言会在真失败时先炸，把真正的失败信息盖住**。而**直接从输出取**没有这个问题：
    # 它用的就是那份反验自己对外报的那句话。
    # **与闸 9 方向十一的关系**：那边核「例数是正整数、闸编号 1..N、认领的文件存在」，
    # **那边没有真值**（它不跑反验）；这边有真值但**核不到慢的那 6 份**
    # （5 份 SLOW + 1 份防递归排除）。
    # **⚠️ Batch 274 订正：所以「各管一半，合起来才是全覆盖」这句话是错的**
    # ——**那 6 份两半都够不着，而它们不是「暂时没人管」，是「按设计就没人管」**。
    # **更要紧的是第三种**：本方向的 `tally` **只在 `rc == 0` 时记**，
    # **所以任何一份非慢反验真跑失败，它就当场掉出覆盖**——
    # **而那一条本方向的注释与台账里都没写**（Batch 272 的构建实测到 7 行时，
    # 那 7 看起来像「注释过期」，而它是「本轮有反验失败了」）。
    # **而这不是理论风险**：那 6 份里藏着 `selftest-zero-input.py`，
    # **它在 Batch 274 真跑时报出闸 39 有 3 处未登记的写操作**
    # ——**一个真缺陷，而它已经躺了三个批次（270 → 274）没人看见**，
    # **因为构建从不跑 SLOW，而「例数这一列」与「只读前提」都由它守着**。
    # **改法**：本方向已把两种「核不到」分开报（见下面 `by_design` / `dropped`），
    # **而根治要等那 6 份有真值检查**——**在那之前，台账必须照实写「这 6 行没有真值检查」**。
    if not ran:
        print("方向十七：[不适用] 本轮方向十六一份反验都没跑，"
              "**例数这一列本轮没有真值可比**——如实报出，不装作核过了")
    else:
        claim = _claimed_case_counts()
        if claim is None:
            print("方向十七：[不适用] 找不到对应关系表或它的表体，**例数这一列本轮没核**")
        else:
            checked = mismatch = unparsed = 0
            for fn, (val, _pick) in sorted(tally.items()):
                if fn not in claim:
                    problems.append(
                        f"方向十七：`{fn}` 真跑跑过了，而对应关系表里**没有认领它**"
                        "　→ 新增反验若不登记，那一行就没人管（方向十一治的是闸侧那一半）")
                    continue
                if val is None:
                    # **解析不到就是核不到，不是核过了**（纪律 203）
                    unparsed += 1
                    problems.append(
                        f"方向十七：`{fn}` 的输出末尾**解析不出合计**，"
                        "所以它的「例数」这一列**本轮没有核**"
                        "　→ 改它的汇总行写法，或在 `TALLY_PATS` 里补上那个形态；"
                        "**别让「解析不到」变成一个没人知道的静默缺口**")
                    continue
                checked += 1
                if str(val) != claim[fn]:
                    mismatch += 1
                    problems.append(
                        f"方向十七：对应关系表里 `{fn}` 登记「例数 {claim[fn]}」，"
                        f"而它**真跑时自己报的是 {val}**"
                        "　→ 两种可能：表过期了（照真值改），"
                        "或者反验真的变了（那就该在备注里说清这次为什么变）")
            covered = set(tally) & set(claim)
            uncovered = sorted(set(claim) - set(tally))
            #: **Batch 274：把「核不到」拆成两种原因**。
            #: 原式只有一句 `set(claim) - set(tally)`，**它把两件完全不同的事并成一个数**：
            #:   ① **按设计没跑**：方向十六跳过 SLOW 登记的与防递归排除的
            #:      ——**这是恒定的**，不管构建红不红；
            #:   ② **跑了但失败**：`tally[fn] = _tally(out)` **只在 `rc == 0` 时记**，
            #:      所以**任何一份非慢反验真跑失败，它就当场掉出覆盖**——
            #:      **而这一种是随构建红绿变的**。
            #: **两种原因在输出上原来完全一样**（只印一个总数 + 一串文件名），
            #: **而本方向的注释里只写了「慢的那 6 份」**——
            #: **于是实测到 7 行时，那 7 看起来像「注释过期了」或「SLOW 名单数错了」，
            #: 而它其实是「本轮有反验失败了」**（Batch 272 的构建里正是如此：
            #: `selftest-label-drift.py` 失败 → 从 6 变 7）。
            #: **一个会变的数配一句不变的说明，读者只能靠猜**（纪律 203：
            #: **「核不到」必须说得清是哪种核不到**）。
            #: **分界是「跑没跑」，不是「在不在 `fleet_all` 里」**——
            #: `fleet_all` **本身就把防递归的那份排除在外**，
            #: 而它**同样属于「按设计没跑」**。
            #: **Batch 274 实测踩到的**：第二版用 `set(fleet_all) - set(fleet)`，
            #: **于是那份防递归排除的反验既不在 `by_design` 也不在 `dropped`**，
            #: 输出变成「另有 **6** 行核不到；按设计没跑 **5** 份（…）」——
            #: **一个数与列出来的东西对不上**。
            #: **而那正是 Batch 271 记下过的形态**：
            #: **一格特别长、一格特别短 = 边界上多/少了一个东西**
            #: （纪律 291/281 推论一）。**所以修法不只是换个集合，还要加一道完整性守卫**——
            #: **「两类加起来必须等于总数」这件事本身要被核，否则下一次又会少一个。**
            not_run = set(names) - set(fleet)                 # SLOW + 防递归排除，恒定
            by_design = sorted(set(claim) & not_run)
            dropped = sorted((set(claim) & set(fleet)) - set(tally))   # 跑了但没记上
            #: **完整性守卫**：本条若照实分完，两类之和必须等于总数。
            #: **对不上就报出来，不许安静地少列一个**（纪律 203）。
            unaccounted = sorted(set(uncovered) - set(by_design) - set(dropped))
            if unaccounted:
                problems.append(
                    "方向十七：**%d 行「核不到」既没被算进「按设计没跑」也没被算进"
                    "「本轮真跑失败而掉出」**（%s）——**这说明本方向把 `uncovered` "
                    "拆成两类时漏了一类**　→ 那个数与列出来的东西对不上，"
                    "**而读者只能靠猜**（纪律 291 的同一个形态）"
                    % (len(unaccounted), "、".join(unaccounted)))
            parts = ["**另有 %d 行本方向核不到**" % len(uncovered)]
            parts.append("按设计没跑 %d 份%s" % (len(by_design),
                                                "（%s）" % "、".join(by_design) if by_design else ""))
            if dropped:
                parts.append("**本轮真跑失败而掉出覆盖 %d 份（%s）**——"
                             "**这几种随构建红绿变，不在 SLOW 名单里**"
                             % (len(dropped), "、".join(dropped)))
            if unaccounted:
                parts.append("**还有 %d 份两类都没算进去（%s）——**这是判据自己的缺口"
                             % (len(unaccounted), "、".join(unaccounted)))
            print("  方向十七：对应关系表 %d 行里，本方向核到 %d 行"
                  "（%d 处不一致、%d 份解析不出）；%s"
                  % (len(claim), checked, mismatch, unparsed, "；".join(parts)))


    print("  方向十六：真跑 %d 份非慢反验，%d 份 rc=0，用时 %.1f 秒%s"
          % (ran, ok, fleet_cost,
             ("；**另有 %d 份按 SLOW 登记没跑**（%s）"
              % (len(fleet_all) - ran,
                 "、".join(sorted(n for n in fleet_all if n not in fleet)))
              if fleet else "；**本轮一份都没跑**")))

    checked = py_ok + sh_ok
    #: **`env_gap` 优先于 `problems`（Batch 254 实测）**：上游不在场时，
    #: 方向十六「真跑反验」那几条**必然**报「真跑没跑通」——
    #: 而那不是「反验坏了」，是「上游没了」，**而用例向闸去问上游是正常行为**。
    #: **让它们汇进 `problems` → rc=1「不一致」，就是拿环境的缺口冒充「反验坏了」**
    #: （反验文件头把它列为判据最坏的一种错，Batch 204 实测过）。
    #: **代价要说清楚**：上游不在场时，一个真坏的夹具也会被这条 rc=2 盖住，
    #: **而那是可自愈的**——指好 `BEEFTV_SRC` 再跑一次，它会自己以 rc=1 现身。
    if env_gap:
        print("反验启动核对：%d 份反验**可启动**，但**上游 BeefTV 不可用**——"
              "`selftest-unreachable.sh` 的 %d 个用例一条都没核过"
              % (len(names), len(_cases)))
        for p in problems:
            print("  ✗ " + p)
        print("  → **本闸本轮返回 2（未能核对）而不是 1**：上面「真跑没跑通」"
              "那几条**由上游不在场这一个原因造成**。指好 `BEEFTV_SRC` 再跑一次，"
              "真有问题的会自己以 rc=1 现身——**这不是把问题藏起来，是先归因**。")
        return 2
    if problems:
        print("反验启动核对：%d 份反验中有 %d 处问题" % (len(names), len(problems)))
        for p in problems:
            print("  ✗ " + p)
        print("→ **反验不在构建路径上，它坏了不会让构建变红**——"
              "所以「它至少能启动」这件事必须由构建来保证（Batch 178 实测 34 例静默失效）")
        return 1

    print("反验启动核对通过：%d 份反验全部可启动"
          "（python %d 份语法可解析且本地依赖可 import、shell %d 份通过 bash -n）"
          % (checked, py_ok, sh_ok))
    print("  另有 %d 份注入夹具（selftest-*-fix-*.py）语法可解析" % fx_ok)
    print("  慢反验 %d 份已登记（%s）——提交前手动跑"
          % (len(SLOW), "、".join(sorted(SLOW))))
    print("  shell 变量展开核对（方向十四）：%d 个 shell 脚本里"
          "**没有「`$var` 紧跟非 ASCII 字符」**（本机 %s）"
          % (len(_shell_files()), "实测会坏" if broke else "实测不复现"))
    print("  构建出口核对（方向十三）：闸 rc=0/1/2 三种结局 + **rc=0 却零输出**"
          "**都被真跑了一遍**"
          "（rc=1 报「不一致」、rc=2 报「未能核对」而不是「不一致」、rc=0 正常收下、"
          "**rc=0 且一句话都没说 → 判未能核对**（Batch 267））")
    print("  慢反验前提核对（方向五/五之二，**只查前提不查结果**）："
          "`selftest-meta.sh` %d 个夹具锚点、%d 个因目标不在场跳过；"
          "`selftest-unreachable.sh` %d/%d 个用例前提成立、%d 个跳过"
          % (fx_checked, fx_skipped, ur_checked, len(_cases), ur_skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
