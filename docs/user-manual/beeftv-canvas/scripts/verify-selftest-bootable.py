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

  · **对账**：慢表里的秒数是**一个被抄了两遍的量**（`SLOW.seconds` 与
    `SELFTEST_COSTS` 各一份），Batch 275 新增**方向四e** 核这两遍是否还对得上。

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
import buildrecord  # noqa: E402

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
#: **方向十九的豁免表（**Batch 281 实测登记 27 条，Batch 282 起应当是空的**）。
#:
#: **它为什么曾经有 27 条**：真跑当时跑在**真实手册树**上，
#: **而实测 27 份非慢反验会改那棵树**（见纪律 316 与 317）。
#:
#: **⚠️ Batch 282：真跑搬进完整副本树，于是这张表被清空了，而这不是「删得掉就无所谓」**——
#: **留着那 27 条会正好掩盖我们要的信号**：
#: **反验现在写在副本上，于是一条命中就只可能是「有反验用绝对路径逃出了副本树」**，
#: **而那正是最该报的那一种**（它意味着副本树这道防线漏了）。
#: **纪律 143 说「宁可宽不可删」，而它的前提是「误报的代价更大」——
#: **这一条的前提已经不成立了，所以照搬它就是照搬一条过期理由**（纪律 288）。
#:
#: **这张表是普查的结果，不是设计的结果**——实测手段是
#: 「隔离副本树 + `sys.addaudithook` 逐份真跑，只算基线提交里已跟踪的路径」
#: （探针与它的三次修正见环境记录 244）。**73 份 python 反验里 26 份命中**。
#:
#: **它现在为什么是空的**：见上面那三段。
#:
#: **⚠️ 覆盖面必须写在这里**：**它只罩 python 反验的普查口径**，
#: **而 `selftest-meta.sh` 会原地改 15 个真实文件**（已登记进 `SLOW`，
#: **不在方向十六的真跑名单里**，所以方向十九数不到它）。
#: **`.sh` 反验在方向十九的运行时是罩得住的**（指纹法不看解释器），
#: **而本批的普查没跑它们**——**这是本方向的已知盲区，不装作没有**。
TREE_WRITE_EXEMPT = {
}

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
        "seconds": 240,          # **Batch 279 再改**：210 → 240。**实测 222.9 秒**（方向三单独跑、41 道闸）——**而 200 是按 40 道闸量的**，**闸 41 本身也在方向三里被跑到（+5.4 秒）**。**按纪律 204 取大并留余量，登记 240**。原 190 →：190 → 210。**两份抄本都登记 190、互相印证、方向四e 报绿，而 Batch 278 三次分段实测是 202.02 / 196.36 / 196.56 秒**——**这正是方向四e 注释里自己写下的盲区**（「它抓不到两遍一起过期」，纪律 310 的第三个实例）。**按纪律 204 取大（202.02）并留余量，登记 210**
        "why": "**它变慢不是因为多了检查，是因为被它核的那些闸不再秒退**——"
        "Batch 197 给 `beefsrc` 加了可用的兜底之后，方向三里 `BEEFTV_SRC` 指向非仓的 7 道闸"
        "**回落到真仓把整道闸跑完**；Batch 202 把原本 rc=2 的 2 道闸也接上兜底，"
        "**它们于是也真的跑完了**。已越过 30 秒阈值（**量级可信，具体秒数不可信，见左侧注释**）。"
        "登记 + 提交前跑——**与另外三份慢反验同一类必要成本**："
        "**Batch 279：它现在只核一个极端了**（方向三：正常手册树 + `BEEFTV_SRC` 指向非仓），"
        "**而方向一/二（空手册树）已搬成闸 41 `verify-empty-tree.py`、每次构建都跑**"
        "（实测 5.4 秒）——**\"两个极端\"那句话是 Batch 279 之前的**。"
        "**剩下的这一个之所以还慢，是因为它必须在真实手册树上跑**"
        "（复制出来的树无法同时满足「正常」与「隔离」），"
        "**那半件事的性质决定了它只能登记慢反验。**"
        "**两次变慢都不是它多做了什么，而是被它核的那些闸真的开始做事了。**",
        "anchor": ("selftest-zero-input.py", "def direction_three"),
        #: **Batch 279 收成单项**：方向一/二（空手册树）**已搬成闸 41**
        #: `verify-empty-tree.py`，**每次构建都跑**（实测 5.4 秒）。
        #: **Batch 278 的分段实测**（副本树 / 40 道闸 / 同一台机器 / 三次）：
        #:   方向一/二 **6.63 / 5.27 / 5.37 秒** / 方向三 **195.27 / 190.96 / 191.07 秒**
        #:   （方向三占 96.7% / 97.3% / 97.3%）。
        #: **Batch 279 重测（41 道闸、方向三单独跑）实测 222.9 秒**——
        #: **比 200 高，因为闸 41 本身也在方向三里被跑到**。取大并留余量 → 240。
        "cost_split": {"def direction_three(gates):": 240.0},
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
        #: **Batch 278：单项 = 如实登记「未分拆」**。5 条里只有零输入那份真的分过段；
        #: **其余 4 条本批没有分段实测，因此不编**——判据对它们只有「锚点在场」一颗牙齿。
        "cost_split": {"def run(env=None):": 38.0},
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
        #: **Batch 275 加了 4 例（26 → 30 例）后重测两次：837.8 秒（干净副本树）
        #: 与 802.3 秒（真树，同事的 WIP 让 3 条用例更早返回）**——
        #: **两次都低于登记的 950，故预算不动**（纪律 204：漂的时候倒向安全那侧，
        #: **而这次漂的方向是变小，不需要动**）。
        "seconds": 1810,
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
        #: 单项 = 未分拆（Batch 278 无分段实测，**不编**）。详见上面 `cost_split` 那段说明。
        "cost_split": {"def sandbox():": 1810.0},
    },
    "selftest-unreachable.sh": {
        "seconds": 1500,          # 实测约 25 分钟（Batch 179）
        "why": "走 git plumbing 往上游仓库注入 40 个用例并建临时 ref，"
               "每个用例都要 read-tree / write-tree / commit-tree。"
               "**放进构建会让每次构建多花 25 分钟**。改为登记 + 提交前跑。",
        "anchor": ("selftest-unreachable.sh", "refs/manual-gate-selftest"),
        #: 单项 = 未分拆（Batch 278 无分段实测，**不编**）。
        "cost_split": {"run_case() {": 1500.0},
    },
    "selftest-meta.sh": {
        "seconds": 101,          # **Batch 275 改**：原登记 97 秒，而 Batch 274 真跑实测 **100.8 秒**——**按本条自己写的理由，偏小才是危险方向**
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
        #: 单项 = 未分拆（Batch 278 无分段实测，**不编**）。
        "cost_split": {"run_fail_case() {": 101.0},
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
    "selftest-screenshots-literals.py": 14.0,   # **Batch 275 重测三次：13.33 / 13.16 / 13.82 秒，取大并留余量**。原登记 30.1 秒，**而它已从 SLOW 里移出**（实测早已掉到阈值下）
    "selftest-screenshots.py": 0.7,
    "selftest-selftest-bootable.py": 1668.0,   # **Batch 281 重测：43 例实测 1668.0 秒**（此前 384.0 是 **Batch 210 的 26 例基线**，而 Batch 254 已实测 877 秒**却只改了 `SLOW` 没改这一处**——**方向四e 报绿只是因为那个过期值偏低**，把比值压到了 3.0 倍上限之下，纪律 310 的又一个假绿）。**Batch 282 重测：45 例 1512 秒**（比 43 例的 1668 **更快**——**真跑搬进副本树顺带快了 12 秒**），**按纪律 204 保留较大的那个作为高水位，不下调**。**Batch 283 重测：49 例 1461 秒**（又快了 51 秒——**本批加的 4 例只花 13.3 秒，而用例 24/26 各自要在沙箱里真跑整个闸 18**；**快的那部分来自把 `_real_repo` 做成 `rev-parse`**），**同样保留 1668.0 不下调**——**下调要的是同一套测法重测三遍，不是一次更快的数**。**Batch 284 重测：52 例 1539 秒**（比 49 例的 1461 慢——**本批加的 3 例只花 1.0 秒，慢的那部分来自把方向二十一接进每次闸运行**，而它自己只要 0.022 秒；**余下的是机器波动，同一批的两轮差 5%**））
    #: **Batch 247 重测**：三次实测 7.33 / 6.95 / 7.11 秒，**而原登记值是 0.7——低估了十倍**。
    #: 9 例里每例都 `copytree` 一整份 `scripts/`（103 个 selftest-* 加 36 个闸）再起一个子进程跑被测闸，
    #: **耗时几乎全在重复拷贝上**。**`seconds` 是预算上限而不是实测均值，
    #: 低估是危险方向**（纪律 204/136：漂的时候倒向安全那侧）——
    #: **而这条低估在 Batch 247 之前就存在**，本批只是因为给它加了两例才顺手重测。
    #: **一个「跑得比登记慢十倍却没人发现」的登记，和写错一个数是同一种病。**
    "selftest-selftest-deps.py": 7.5,
    #: **Batch 279 新增**：闸 41 的反验。**实测 11.75 / 11.47 / 11.59 秒（三次）**，
    #: **取大并留余量登记 15**（纪律 204：偏小是危险方向）。
    #: **它比闸 41 本身贵一倍多**（闸 41 实测 5.4 秒）——**因为闸 41 要在空树上
    #: 逐道跑 37 道闸，而它的三例各跑一遍**，**于是「体检体检的那道闸」也被体检了**。
    #: **它不登记为慢**（15 < 30 秒阈值），**所以方向十六每次构建都会真跑它**。
    "selftest-empty-tree.py": 15.0,
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
    #: **Batch 275 新增，只为让方向四e 有可对账的来源**。**它不是第二次测量**——与 `SLOW` 那一份同源（Batch 179 记的「约 25 分钟」）。**如实写下来，是因为「这份耗时只有一个抄本」本身就是缺口**（纪律 112）。
    "selftest-unreachable.sh": 1500.0,
    "selftest-meta.sh": 101.0,     # **Batch 275 新增**：Batch 274 真跑实测 100.8 秒（三次 47 / 48 / 68 / 100.8，漂 2.1 倍）。
    "selftest-zero-input.py": 240.0,  # **Batch 278 再改**：190 → 210，与 SLOW 那一份对齐。**Batch 275 那次两遍都低报（42.1 / 82 → 实测 185.9），Batch 278 又一次两遍一起过期（190 / 190 → 实测 202.02 / 196.36 / 196.56）**——**方向四e 抓的正是前者，抓不到后者**
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


#: **Batch 276 新增**：手册树里**有未提交改动**的文件集合（仓库相对路径）。
#: **返回 `None` 表示问不到（不是 git 检出）——那与「干净」必须长得不一样**。
def _dirty_paths():
    g = subprocess.run(["git", "-C", ROOT, "status", "--porcelain", "--", "."],
                       capture_output=True, text=True)
    if g.returncode != 0:
        return None
    out = set()
    for line in g.stdout.split("\n"):
        if not line.strip():
            continue
        # porcelain 的两列是状态与路径；重命名写成 `R  old -> new`，取后者
        path = line[3:].strip()
        out.add(path.split(" -> ")[-1])
    return out


#: **方向十六真跑时必须留在真实手册树上的反验**（**Batch 282 新增**）。
#:
#: **判据不是「慢」而是「需要真实 git 历史」**——**方向十六早就为前者硬排除过一份**
#: （`selftest-selftest-bootable.py`，防递归），**本表是同一种机制的第二条理由**。
#: **区别必须写清楚**：`SLOW` 的含义是「构建从不跑它，因为太慢」，
#: **而本表的含义是「构建在副本树上跑它，而它要读的那份历史副本树没有」**。
#: **两份合起来才是「本轮一份没跑」的全部理由**，**而只报其中一半
#: 会让人以为另一半也跑了**（纪律 291：数与列出来的东西对不上）。
#: **方向十六真跑时必须留在真实手册树上的反验**——**Batch 283 起本表为空**。
#:
#: **它曾经有一份，而那份的理由本批被证伪了。** 原理由写的是
#: 「实测给它 alternates 之后锚点提交可见，**它却又报出另一个问题，而本批不追**」——
#: **那个「另一个问题」本批追了，答案是：方向三的 OFF_TASK 反向核
#: 报「`24-video-process-menu.png` 最后一次被改动的提交是 `d2eb84a3`，
#: 而免检表登的是 `761106b9`」。**
#: 而 `d2eb84a3` **在真仓里根本不存在**——它是 `git init` 造出来的那棵基线提交。
#: **换句话说，那不是「另一个问题」，而是同一件事的另一半**：
#: alternates 让锚点提交**可见**，却没让**历史**存在，
#: 于是遍历只能停在副本树自己的基线上，**方向三照报不误**。
#:
#: **修法在 `_make_fleet_tree()`**：改用 `git clone --shared` 借对象（0.08 秒），
#: **历史于是是真的**，两个方向同时转绿。**本表因此清空**——
#: **纪律的前提会过期，而照搬前提就是照搬过期理由**（Batch 282 清空豁免表是同一条）。
#:
#: **表本身留着**，因为机制还在：方向十六为「慢」硬排除一份（`SLOW`）、
#: 为「防无限递归」硬排除一份，**本表是第三类理由的登记处**。
#: **而留着空表的价值不在于它现在有几条，而在于下次再加一条时不用重新发明机制。**
FLEET_NEEDS_REAL_HISTORY = {
}


def _real_repo():
    """真仓根与手册树在真仓里的相对路径——`git clone --shared` 两样都要。

    **⚠️ 两边都必须先 `realpath`，否则相对路径会算成一串 `../../..`——
    这是用例 49 撞出来的（Batch 283）**：macOS 上 `tempfile.mkdtemp` 给的是
    `/var/folders/...`，而 `git rev-parse --show-toplevel` 回的是
    `/private/var/folders/...`（**`/var` 是 `/private/var` 的软链**），
    **`relpath("/var/.../X", "/private/var/.../X")` 于是返回一长串 `../..`**
    ——**而那不是一个「路径不对」的报错，它会让 `os.path.join` 指到树外**，
    **后面 `copytree` 与 `git add` 相继失败，最后落到 `return None`**。
    **症状是「建不出副本树」，而真因在两行之前的一个函数里**——
    **这正是纪律 291 说的那种「数与列出来的东西对不上」的近亲。**


    **不用 `ROOT/../../../..` 数层数**：那种写法在手册树被挪位置时
    会静默指到别处，而 `git rev-parse` 是**问出来的**。
    **问不出来就返回 `(None, None)`，而调用方必须把它当成「建不出树」**。
    """
    p = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-toplevel"],
                       capture_output=True, text=True)
    top = p.stdout.strip()
    if p.returncode != 0 or not top or not os.path.isdir(os.path.join(top, ".git")):
        return None, None
    #: **两边都取 `realpath`**——理由见 docstring 那段：`/var` 与 `/private/var`
    #: 是同一个目录的两个名字，**而 git 只回后者**。
    top, here = os.path.realpath(top), os.path.realpath(ROOT)
    rel = os.path.relpath(here, top)
    #: **顺带钉一句**：`rel` 里有 `..` 就说明手册树**不在**那个仓里
    #: （例如它被软链到了外面）。**那种情况下 `manual` 会指到临时目录之外**，
    #: **所以这里宁可返回「建不出」，也不让它去拼一个树外的路径。**
    if rel.startswith(".."):
        return None, None
    return top, rel


def _make_fleet_tree():
    """为方向十六的真跑建一棵**完整**手册树副本（**Batch 282 新建，283 改造**）。

    **Batch 283 把它从「复制 + `git init`」换成「`git clone --shared` + 覆盖」**，
    唯一的原因是**历史**：

    | 做法 | 代价 | 那 67 张截图「最后一次被改动的提交」 |
    |---|---|---|
    | 复制 + `git init` + 基线提交（282） | 复制全树 | **基线提交自己**（真仓里不存在） |
    | `git clone --shared` + 覆盖 + 提交（283） | **0.60 秒** | **真仓里那个真提交** |

    **`--shared` 借对象不复制，所以 1.4 GB 的历史只付 0.08 秒**——
    **而这一条把 39 份变成 39 份全跑**（实测 `real-67` 由 rc=1 转 rc=0，
    且 109 份非慢反验在新副本树上的 rc 与真树**逐一相同，0 份不同**）。

    **三个环境条件，每一个都是量出来的，不是想出来的**：
      ① **`node_modules` / `dist` / `.git` 不搬**（前者是依赖，后两者是产物与仓）；
      ② **`.vitepress` 必须搬**——实测排除它之后
         `selftest-current-version.py` 与 `selftest-shot-version.py` 直接 rc=1
         （**它们读 `config.mjs`**，而「反验的沙箱里没有手册正文」那个理由
         在这里的具体形态就是「没有发布配置」）；
      ③ **必须有真实历史**——`--shared` 只借对象，
         **副本树的 HEAD 因此就落在真仓 HEAD 上**，
         **「某张图最后一次被改动的提交」查出来是真仓里那个真提交**
         （实测 `24-video-process-menu.png` = `761106b9`，
         **而 `git init` 那种假历史查出来是副本树自己的基线提交，真仓里根本不存在**）；
         **工作区则由下面那次覆盖全量建出来**（手册 499 个文件、35 MB，
         **`node_modules` 不在其内**），
         **而 `git add` + 一次提交把「当前工作区」盖上去**，
         **于是同事那两处未提交 WIP 也在副本里**（它们是文档记录过的注入实验）。

    **返回 `(真仓根的临时目录, 手册目录)` 两个值**：
    **副本树的 git 根与手册根从此不是同一个目录**，而调用方要同时用两个。
    **建不出来就返回 `None`，而调用方必须把它当成「本轮不跑」而不是「放行」**。
    """
    top, rel = _real_repo()
    if top is None:
        return None
    tmp = tempfile.mkdtemp(prefix="beef-fleet.")
    try:
        r = subprocess.run(["git", "clone", "-q", "--shared", "--no-checkout", top, tmp],
                           capture_output=True, text=True)
        if r.returncode != 0:
            raise OSError("clone 失败：%s" % (r.stderr or "")[:200])
        manual = os.path.join(tmp, rel) if rel != "." else tmp
        env = dict(os.environ)
        env.setdefault("GIT_AUTHOR_NAME", "beef-gate")
        env.setdefault("GIT_COMMITTER_NAME", "beef-gate")
        env.setdefault("GIT_AUTHOR_EMAIL", "gate@local")
        env.setdefault("GIT_COMMITTER_EMAIL", "gate@local")
        #: **⚠️ 这里原来有一句 `git checkout <子树>`，本批把它删了，而不是把它修好。**
        #:
        #: **`--no-checkout` 之后索引是空的，于是 pathspec 检出必然失败**——
        #: 实测 `error: pathspec 'docs/user-manual/beeftv-canvas' did not match
        #: any file(s) known to git`。**而它是静默空转**：返回码没查，
        #: **副本照样完全可用**——因为下面那一步覆盖自己就把文件全建出来了
        #: （`copytree` 会连父目录一起建）。
        #:
        #: **删它比修它好，理由是那句纪律本身**：
        #: **一个不做事却让人以为「不覆盖也能用」的步骤，比没有它更坏**——
        #: 下一个人看到「已经有 checkout 了」，就会以为「不覆盖也保险」。
        #: **而真正让副本可信的是覆盖，不是检出**——
        #: **检出只会在「有东西要检出」的时候才做事，而这里恰恰是空的。**
        #: **顺带省掉一次全树写出**（实测 clone + 覆盖 + 提交共 0.60 秒）。
        #: **覆盖：把真树**当前**内容搬进去**（含未提交 WIP），再提交一次。
        #: **`git add` 之后提交是有意的**——它让副本树的 HEAD 落在真仓 HEAD 之上，
        #: **于是「最后一次被改动的提交」对真仓里没动过的文件仍然是真仓那个**。
        for f in os.listdir(ROOT):
            if f in ("node_modules", "dist", ".git"):
                continue
            s = os.path.join(ROOT, f)
            d = os.path.join(manual, f)
            (shutil.copytree if os.path.isdir(s) else shutil.copy)(s, d)
        for cmd in (["git", "add", "-A", "-f", rel],
                    ["git", "commit", "-q", "-m", "闸 18 真跑副本树覆盖"]):
            if subprocess.run(cmd, cwd=tmp, env=env, capture_output=True).returncode != 0:
                raise OSError("提交覆盖层失败：%s" % cmd[0])
        return tmp, manual
    except OSError:
        shutil.rmtree(tmp, ignore_errors=True)
        return None



def _check_skip_table():
    """**方向二十一（Batch 284 新增）**：指纹跳过表里**每一项都必须不含已入库文件**。

    **为什么要有这道闸，而不只是把 `.vitepress` 改对一次**：
    **跳过表是一句断言，而断言会过期。**
    **Batch 281 写上 `.vitepress` 的理由是「它看起来像构建产物」**，
    **而那个目录里唯一的已入库文件是一份手维护的发布配置**
    （`config.mjs`：语言 / 部署模式 / 特性开关 / 错误分类，**14 份闸与反验读它**）。
    **跳整目录 = 方向十九对它失明**，
    **而「改它」恰好是会让多个闸的基线前提失效的那种动作**。

    **判据问的是「表里那些名字底下有没有人」，而不是「它们像不像产物」**——
    **「像不像」是判断，「有没有人」是事实，而只有事实能核。**

    **两个方向缺一不可**：
      **能抓**：往表里塞一个装着已入库文件的目录名 → 点名那个文件；
      **不误伤**：现状一条不报，**并且顺带报出「表里有几项在树里根本不存在」**——
      **那不是错，而是一条有用的信息**（**它说明那几项是「防未来」而不是「现在有用」**）。

    **⚠️ 它只核**目录**表，不核后缀表**——**而那一项也查过**：
    六个后缀（`.pyc` / `.pyo` / `.pyd` / `.log` / `.tmp` / `.swp`）实测各 0 份已入库。
    **留一句在这儿，是因为「只查了一半」本身要写出来**
    （**数与列出来的东西要对得上**，纪律 291）。

    **代价**：一次 `git ls-files`（手册树 499 个文件），**毫秒级**。
    """
    r = subprocess.run(["git", "-C", ROOT, "ls-files"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        #: **返回形状不因「问不出来」而改变**——**三段固定，
        #: `covered` 为 `None` 表示整轮没核**（纪律 156：
        #: **「问不出来」不许长得像「核过了」**）。
        #: **⚠️ Batch 284 整轮红了的教训（第一版）**：这里原本返回一条**问题**，
        #: **而那行 `problems` 一非空，闸末尾整个「反验启动核对」明细块就被换成
        #: 「有 1 处问题」+ 一行 ✗**——**于是 6 个毫不相干的检查从输出里一起消失**，
        #: **5 条「必须不报」的反验用例与 2 条前提用例一起变红/作废**。
        #: **一个方向的「本轮没核」不该有能力关掉别人方向的输出。**
        #:
        #: **改法照闸里既有的先例**（方向十五/十六/十七在这同一种环境下的写法）：
        #: **打一行 `[不适用] …本轮没核——如实报出，不装作核过了`，不进 `problems`。**
        #: **纪律 156 的原话是「没核 ≠ 核过」，而它没说「没核 = 查出问题」。**
        return ([], None, None,
                "问不出已入库文件清单（`git ls-files` 失败）")
    tracked = [x for x in r.stdout.splitlines() if x]
    problems = []
    covered = []
    for d in _FP_SKIP_DIRS:
        pre = d.rstrip("/") + "/"
        hit = [x for x in tracked if x == d or x.startswith(pre)]
        if hit:
            problems.append(
                "方向二十一：指纹跳过表里的 `%s` **底下有 %d 份已入库文件**"
                "（%s）　→ 方向十九因此对它失明；"
                "**产物目录请写精确到子目录**（如 `.vitepress/cache`），"
                "**别连父目录一起跳**——**父目录里往往还住着源文件**"
                % (d, len(hit), "、".join(hit[:3])))
        else:
            covered.append(d)
    absent = [d for d in covered
              if not os.path.isdir(os.path.join(ROOT, *d.split("/")))]
    return problems, covered, absent, None


def _check_fleet_env(fleet_repo, fleet_manual):
    """副本树的两条环境性质（**Batch 283 新增**）。返回问题列表，**空 = 通过**。

    **为什么必须是判据而不是注释**：本批的收益是「39 份全跑」，
    而**它的成本是「有人下一次把 clone 改回 `git init`」**——
    **而那个改动的症状是 `real-67` 悄悄变红，别的什么都不变**，
    **足以让人得出「反验坏了」而去找错的方向**。

    **① 历史**：真仓 HEAD 必须是副本树 HEAD 的祖先。
    **`merge-base --is-ancestor` 一条命令分得开真假**——
    **`git init` 造的假历史里，真仓那个提交根本不可达，退出码非 0**。

    **② 内容**：副本树与真树逐文件一致。
    **只比 `sha1` 与大小，不比 `mtime`**——`shutil.copy` 不带 `mtime`
    （`copy2` 才带），**而比 `mtime` 会让这条判据恒为红**。
    **沿用 `_tree_fingerprint()` 的跳过表**，**否则 `.vitepress` 与 `__pycache__`
    会在两边不对称**（前者副本树有、指纹跳过；后者只在跑过之后才出现）。

    **⚠️ 抽样还是全量**：**全量**，实测 0.5 秒/树。
    **一个判据不该为了覆盖边角而把每次构建的墙钟抬起来**——
    **但这条不是边角**：它核的正是「副本能不能代表真树」，
    **而抽样会让「恰好抽到没被覆盖的那几个文件」变成常态。**
    """
    import hashlib
    problems = []
    top, _rel = _real_repo()
    if top is None:
        return ["副本树环境性质：**真仓问不出来**（`git rev-parse --show-toplevel` 失败）"
                "　→ 本轮不跑，不拿「跑不了」当「跑过了」（纪律 156）"]
    real_head = subprocess.run(["git", "-C", top, "rev-parse", "HEAD"],
                               capture_output=True, text=True).stdout.strip()
    anc = subprocess.run(["git", "-C", fleet_repo, "merge-base", "--is-ancestor",
                          real_head, "HEAD"], capture_output=True, text=True)
    if anc.returncode != 0:
        problems.append(
            "方向十六：副本树**没有真实历史**——真仓 HEAD %s 不是副本树 HEAD 的祖先"
            "　→ 用 `git clone --shared` 借对象重建，**不要用 `git init` 造一棵假历史**"
            "（假历史会让方向三把「副本树自己的基线提交」当成那张图最后一次被改动的提交，"
            "**报出一个真仓里根本不存在的提交号**）" % (real_head[:8] or "未知"))

    def _fp(root):
        out = {}
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = [d for d in dirnames if d not in _FP_SKIP_DIRS]
            for fn in filenames:
                if fn.endswith(_FP_SKIP_SUFFIX):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    st = os.stat(p)
                except OSError:
                    continue
                h = None
                if st.st_size <= 65536:
                    try:
                        with open(p, "rb") as fh:
                            h = hashlib.sha1(fh.read()).hexdigest()
                    except OSError:
                        h = None
                out[os.path.relpath(p, root)] = (st.st_size, h)
        return out

    a, b = _fp(ROOT), _fp(fleet_manual)
    only_real = sorted(set(a) - set(b))
    only_fleet = sorted(set(b) - set(a))
    diff = sorted(k for k in set(a) & set(b) if a[k] != b[k])
    if only_real or only_fleet or diff:
        problems.append(
            "方向十六：副本树内容与真树不一致——**只真树有 %d、只副本有 %d、内容不同 %d**"
            "（%s%s%s）"
            "　→ 副本树必须**把真树当前工作区整份覆盖进去**再提交一次，"
            "**否则 39 份真跑核的是上一次提交的手册，而构建照样报绿**"
            % (len(only_real), len(only_fleet), len(diff),
               "、".join(only_real[:2]) or "-",
               "、" + "、".join(only_fleet[:2]) if only_fleet else "",
               "、" + "、".join(diff[:2]) if diff else ""))
    return problems


#: `_check_fleet_env` 与 `_tree_fingerprint` **必须用同一张跳过表**——
#: **两张表不一样的话，「只真树有」会凭空多出一整类**，而那与覆盖有没有生效无关。
#: **Batch 284 把 `.vitepress` 从这里拿掉了**——**它是这张表里唯一一个
#: 装着已入库文件的条目**（`.vitepress/config.mjs`，4808 字节，
#: **手维护的发布配置，14 份闸与反验读它**：语言 / 部署模式 / 特性开关 / 错误分类都在里面）。
#:
#: **当初为什么写上它**：`.vitepress` 这个名字看起来像构建产物，
#: **而 Batch 281 上线首跑撞到的假红确实是 `__pycache__/*.pyc`**，
#: **顺手把 vitepress 的缓存目录也一起跳了**——
#: **于是「跳 `.vitepress/cache`」被写成了「跳 `.vitepress`」**。
#: **目录里现在只剩一个手维护的 `config.mjs`，产物目录一个都没有**
#: （实测 `git ls-files .vitepress/` 只回 1 份，且 `cache` / `dist` 在树里不存在）。
#:
#: **这就是纪律 288 的第四个形态**（前三个：豁免表的前提过期、方向四g 的理由过期、
#: 「已经实现」不等于「已验证」）：**照搬一条过期的理由，就是照搬一个看不见的洞**。
#:
#: **改成精确到产物子目录**——**而这两个目录现在都不存在**，
#: **所以这条改动今天不改变任何指纹结果，它改的是「明天 `.vitepress` 里多一个源文件时」的命运**。
_FP_SKIP_DIRS = (".git", "node_modules", "dist", "__pycache__", ".pytest_cache",
                 ".vitepress/cache", ".vitepress/dist", ".vitepress/.temp",
                 ".vitepress/.vitepress-temp")
#: **Batch 284 补上 `.DS_Store`**——**而它是一个「文档早就写了、代码一直没做」的那一类**：
#: `_tree_fingerprint()` 的 docstring 从 Batch 281 起就列着 `.DS_Store`，
#: **而 `skip_suffix` 里从头到尾没有它**。
#: **实测树里真有两份**（`screenshots/.DS_Store`、`.vitepress/.DS_Store`，均未入库），
#: **而 macOS 会在任何目录列表变化时重写它**——**一次假红的现成配方**。
#: **本批把 `.vitepress` 从跳过表里拿出来之后，这个风险从「理论上」变成「更可能」**：
#: **那份 `.DS_Store` 正在 `.vitepress/` 里**。
#: **文档与代码不一致，是「那句话说了不算」的一种**（纪律 107 的注释版）。
_FP_SKIP_SUFFIX = (".pyc", ".pyo", ".pyd", ".log", ".tmp", ".swp", ".DS_Store")


def _not_run_reasons(fleet_all, fleet):
    """**没跑的每一份，按它**真正**的理由分类列出来**（**Batch 283 新增**）。

    **Batch 282 埋下、本批拆掉的一个雷**：那一行原来硬编码
    「**另有 N 份按 SLOW 登记没跑**」，而列表算的是
    `fleet_all - fleet`——**里面混着三类完全不同的理由**：
    慢（`SLOW`）、需要真实历史（`FLEET_NEEDS_REAL_HISTORY`）、防无限递归。

    **本批实测的伤害**：`selftest-shot-version-source.py` 被报成「按 SLOW 没跑」，
    **而它根本不在 SLOW 里**——
    **一个想给构建提速的人去 `SLOW` 里找它，找不到，
    而日志明明白白写着「按 SLOW 登记」**。**理由与事实对不上，
    排查就从正确的地方岔开了**（纪律 291：数与列出来的东西要对得上）。
    """
    done = set(fleet)
    slow = sorted(n for n in fleet_all if n not in done and n in SLOW)
    hist = sorted(n for n in fleet_all
                  if n not in done and n not in SLOW
                  and n in FLEET_NEEDS_REAL_HISTORY)
    rest = sorted(n for n in fleet_all
                  if n not in done and n not in SLOW
                  and n not in FLEET_NEEDS_REAL_HISTORY)
    parts = []
    if slow:
        parts.append("慢 %d 份（%s）" % (len(slow), "、".join(slow)))
    if hist:
        parts.append("需真实历史 %d 份（%s）" % (len(hist), "、".join(hist)))
    if rest:
        parts.append("**其余 %d 份**（%s）" % (len(rest), "、".join(rest)))
    return "；".join(parts) if parts else "无"


def _tree_fingerprint():
    """手册树的一份指纹：`相对路径 -> (mtime_ns, 大小, 小文件 sha1 或 None)`。

    **为什么要 `mtime` 而不只是内容**：判据要问的是「**它动过没有**」，
    **而绝大多数反验是「改完立刻还原」**——内容一模一样，
    **只比内容的话这一类全部看不见**（而它们恰恰是最危险的一类：
    **被 kill 的那一次不会有还原**）。`mtime` 把「动过又还原」与「没动」分开。

    **为什么小文件还要 sha1**：`shutil.copy2` / `copystat` **会把 mtime 一起搬过去**，
    **于是「用 copy2 覆盖一个真文件」在只比 mtime 时是隐形的**。
    **64 KB 这个上限是量的**：手册里 `.md` 与 `.py` 绝大多数在这个量级内，
    **而截图动辄几百 KB——给 67 张 PNG 算 sha1 是纯浪费**
    （**一个判据不该为了覆盖边角而把每次构建的墙钟抬起来**）。

    **⚠️ 跳过表里为什么必须有 `__pycache__`（**Batch 281 上线首跑当场踩到**）**：
    **本方向第一次跑就报出两份「新命中」，而它们是
    `scripts/__pycache__/*.pyc`**——**Python 每 import 一个模块就自己写一份字节码缓存**，
    **于是每一份反验跑完都会多出几个 `.pyc`**，而副本树里它们一开始根本不存在。
    **把它们算进来是纯噪声**：**不进版本库、被删了立刻重建、且与手册内容毫无关系**。
    **而一个每次都喊「有东西变了」的判据，只会教人学会忽略它**
    ——**这正是纪律 143 的原话，而它这次是本批自己撞上的**。
    **所以跳过表扩成「解释器与构建工具自己产生的产物」**：
    `.git` / `node_modules` / `dist` / `__pycache__` / `*.pyc` / `.DS_Store`。

    **⚠️ Batch 284 从这张表里拿掉了 `.vitepress`**（**Batch 281 写上它时是个静默的错误**）：
    **该目录里唯一的已入库文件是 `.vitepress/config.mjs`——一份手维护的发布配置，
    14 份闸与反验读它**。**跳过整目录等于让方向十九对它失明**，
    **而「改它」正是会让多个闸的基线前提失效的那种动作。**
    **产物目录另有其名**（`cache` / `dist` / `.temp`），已逐个列进 `_FP_SKIP_DIRS`。
    **而方向二十一负责让这张表以后不再骗人**（见 `_check_skip_table()`）。
    **边界照写清楚**：**本方向数的是「手册的原有文件」**，
    **而这三类产物都不在其中**（**真要连未跟踪文件一起管，那是闸 38 的活**）。
    """
    import hashlib
    out = {}
    skip_dirs = _FP_SKIP_DIRS
    #: **`:memory:` 之外的字节码后缀**：不是目录，而是文件名的一部分。
    skip_suffix = _FP_SKIP_SUFFIX
    for dirpath, dirnames, filenames in os.walk(ROOT):
        #: **Batch 284：按**相对路径**过滤，而不是按目录名过滤**——
        #: **表里现在有 `.vitepress/cache` 这种带层级的名字**，
        #: **而 `d not in skip_dirs` 那种写法永远匹配不上它们**
        #: （**`d` 只是最后一段的名字**——**那正是当初把
        #: 「跳 `.vitepress/cache`」写成「跳 `.vitepress`」的技术原因，
        #: 而技术原因最容易伪装成纪律**）。
        rel = os.path.relpath(dirpath, ROOT)
        dirnames[:] = [d for d in dirnames
                       if os.path.normpath(os.path.join(rel, d)) not in skip_dirs]
        for fn in filenames:
            if fn.endswith(skip_suffix):
                continue
            p = os.path.join(dirpath, fn)
            try:
                st = os.stat(p)
            except OSError:
                continue
            h = None
            if st.st_size <= 65536:
                try:
                    with open(p, "rb") as fh:
                        h = hashlib.sha1(fh.read()).hexdigest()
                except OSError:
                    h = None
            out[os.path.relpath(p, ROOT)] = (st.st_mtime_ns, st.st_size, h)
    return out


def _tree_delta(before, after):
    """返回 `(被改的, 被删的, 被新建的)` 三个已排序的列表。"""
    b, a = set(before), set(after)
    changed = sorted(p for p in b & a if before[p] != after[p])
    return changed, sorted(b - a), sorted(a - b)



def _repo_rel(path):
    """把手册树内的路径换成**仓库相对路径**，好与 `_dirty_paths()` 对齐。

    **`git rev-parse --show-prefix` 而不是自己拼前缀**——
    手册树在仓库里的深度是可变的（今天在 `docs/user-manual/beeftv-canvas/`），
    **拼错前缀的后果是「一个都匹配不上」，而那与「都不脏」在行为上一样。**

    **⚠️ Batch 276 实测到的静默失效（本函数第一版就栽在这里）**：
    macOS 的 `/var` 是 `/private/var` 的软链，而
    `os.getcwd()` 返回**解析后**的路径、`ROOT` 由 `__file__` 推得**保持未解析**，
    于是 `relpath` 算出一串 `..`（实测值：
    `../../../../../../private/var/.../10-tasks/asset-library.md`），
    **与脏集合永远匹配不上**。**而那意味着「同事改了 → 报成夹具坏了」——
    失败方向正好是危险的那一侧，而且一个字节都不响。**

    **两处修法，缺一不可**：
      ① **两边都 `realpath`**（对齐比较的基准）；
      ② **算出来的路径一旦以 `..` 开头就返回 `None`**——
         **让「我算不出来」成为一个能被说出来的状态**，
         而不是伪装成「这个文件不脏」**（只做 ① 的话，换一条软链就又失效一次）**。
    """
    p = subprocess.run(["git", "-C", ROOT, "rev-parse", "--show-prefix"],
                       capture_output=True, text=True)
    if p.returncode != 0:
        return None
    try:
        rel = os.path.relpath(os.path.realpath(path), os.path.realpath(ROOT))
    except ValueError:                      # 跨盘（Windows）——同样算不出来
        return None
    if rel.startswith(os.pardir):
        return None                         # ② 它不在手册树里，不能拿来比
    return p.stdout.strip() + rel


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

    # ④e（**Batch 275 新增**）：`SLOW` 的 `seconds` 与**同一份在 `SELFTEST_COSTS`
    # 里的实测登记**必须对得上——**同一个量被抄了两遍，而两遍之间没有任何东西核它们。**
    #
    # **为什么现在才建它**：本批实测 `selftest-screenshots-literals.py`
    # **13.33 / 13.16 / 13.82 秒，而 SLOW 登记 31 秒、`SELFTEST_COSTS` 登记 30.1 秒**
    # ——**两个抄本都还「自洽」，而它们一起错着**。方向四a 读的是 `seconds`，
    # 31 > 30，于是它报绿；**没有任何一条方向问过「这个登记还成立吗」**。
    # 后果不是「多花 17 秒构建时间」：**那份反验被排除在方向十六的真跑名单之外，
    # 于是方向十七的「例数」真值检查够不到它**——
    # **一份过期的排除登记，正在悄悄缩小构建的核验面，而它看起来和一次必要排除一模一样。**
    # 这与 Batch 208 修掉的那个病是**同一个病的两面**：
    # 那次是**低报**（登记 11 / 实测 37.1，方向四d 永远看不见它），
    # 这次是**过期**（登记 31 / 实测 13.3，它其实早就不该被排除）。
    # **低报让守卫瞎掉，过期让守卫白占位置——而两者的方向恰好相反。**
    #
    # **⚠️ 本方向抓不到什么（必须写在这里，否则下一个批次会以为它全包了）**：
    # **它只核「两个抄本还对不对得上」，而上面那个案例里两个抄本一起过期。**
    # **判据无法在构建期知道「三周前量出来的 13.3 秒现在还是不是真的」——
    # 那只能靠有人重测。** 本方向能做的是**让一次重测立刻有地方可写、
    # 且写错会被另一份抓住**；**「没人重测」这件事它管不了**（与 Batch 195
    # 「首跑全绿不是证据，鉴别力验证才是」同源：机械不可判定的部分只能靠人记）。
    #
    # **三条各管一种形状，缺一条就少一种**：
    #   ④e-1 **只有一个抄本** → 「这张表没有任何东西能发现它过期」；
    #   ④e-2 **两个抄本差得说不通** → 必有一份过期；
    #   ④e-3 **实测那侧掉到阈值以下** → 「它慢」这个登记**已被实测否证**，该删。
    #: **允许的倍数**。`seconds` 刻意偏大是安全的（预算上限），
    #: 而偏小是危险的（纪律 204），**所以这条只卡「离群」，不卡「偏大」**。
    #: 实测当前四份的比值 1.02 / 1.95 / 2.47 / 1.0——**3 倍是留过余量的**。
    SLOW_COST_RATIO = 3.0
    for _fn in sorted(SLOW):
        _cost = SELFTEST_COSTS.get(_fn)
        _declared = SLOW[_fn].get("seconds")
        if _cost is None:
            problems.append(
                f"方向四e：SLOW 里登记了 {_fn}，而 `SELFTEST_COSTS` 里**没有它的实测耗时**"
                "　→ 这份耗时的秒数**只有一个抄本，于是没有任何东西能发现它过期**；"
                "**跑一次把实测填进 `SELFTEST_COSTS` 即可，不必改 SLOW 那一份**"
                "（方向四a 只看 SLOW，两边都有它才谈得上「对账」）")
            continue
        if _cost <= SLOW_BUDGET_SEC:
            problems.append(
                f"方向四e：{_fn} 登记在 SLOW 里（`seconds` {_declared} > {SLOW_BUDGET_SEC}），"
                f"**而实测登记只有 {_cost}s——已在阈值之下**"
                "　→ 「它慢」这个登记**已被实测否证**，请把它从 SLOW 里删掉；"
                "**删掉之后方向四d 会接着要一份新实测**（那一步不是多余的："
                "**正是它把「删掉」变成一次有据的删除**）")
            continue
        if not isinstance(_declared, (int, float)) or _declared <= 0:
            continue                      # 方向四a 已经报过，这里不重复
        _ratio = max(_declared, _cost) / float(min(_declared, _cost))
        if _ratio > SLOW_COST_RATIO:
            problems.append(
                f"方向四e：{_fn} 的 `seconds` 登记 {_declared}s，"
                f"而 `SELFTEST_COSTS` 的实测是 {_cost}s"
                f"（**差 {_ratio:.1f} 倍，超过 {SLOW_COST_RATIO:.0f} 倍上限**）"
                "　→ **同一个量被抄了两遍，其中一遍多半已经过期**。"
                "以实测为准改 `SLOW`；**若实测那份也过期（就是开头那个案例），"
                "重测一次再改两边**——**这一条抓不到「两遍一起错」**")

    # ④g（**Batch 280 新增**）：**「构建要多久」这个量的机制必须接得上。**
    #
    # **为什么需要它**：本批实测 `build-site.sh` 的墙钟是 **251 秒（4 分 11 秒）**，
    # **而 `selftest-zero-input.py` 的模块 docstring 从 Batch 192 起写着「只要 25 秒」**
    # ——**低了 10 倍**。**那个数被抄进全树 8 处**，
    # **其中一处是 Batch 279 建闸 41 时的「5.4 秒 vs 25 秒」比较**
    # ——**也就是说，一个过期的数字直接参与过一次真实的决策**。
    # **这是纪律 310 的第五个实例**，而前四个实例过期的都只是**登记表**；
    # **这一次过期的是一条被用来做决策的理由**——**比过期登记表更坏**（纪律 288）。
    #
    # **机制不是又一张表**：`build-site.sh` 在开头记 `BEEF_T0`、末尾算 `BEEF_SECS`，
    # 连同 `--secs` 交给 `record-build-result.py`，由 `buildrecord.write_record`
    # 写进 `.git/beeftv-build-record` 的 `secs=`。
    # **于是这个量有了一个每次构建都刷新的真值，而文档要引用就该去读它**（纪律 244 / 280）。
    #
    # **⚠️ 本方向只问「机制接上了吗」，不问「产出的值对不对」。
    # 而这个分工是被逼出来的，不是设计出来的**：
    # 第一版把「记录里有正的 `secs=`」也算在本方向里，**于是上线后的第一次构建必然红**——
    # 构建中途读到的永远是**上一次**构建写的记录，而那一次还没有 `secs=`；
    # **而记录只在 `fail == 0` 的构建末尾才写**（`record-build-result.py` 的硬条件），
    # **于是一个「要求记录里有 `secs=`」的构建期判据等于永远红**——**那是死锁，不是失败**。
    # **所以分工是**：**构建期问机制**（本方向，静态、必然可判）；
    # **提交时问产出**（`buildrecord.check()` 核最新绿记录里有正 `secs=`，
    # **那时绿记录必然存在**，而纪律 280 本来就在管那一步）。
    #
    # **⚠️ 更早的一版是「扫散文里的秒数」，本批把它否决了，理由必须写在这里**：
    # 它扫 `build-site.sh` 与 `scripts/*.py` 里形如「构建/build-site.sh … N 秒」的行，
    # 拿 N 与 `secs=` 比。**收紧一次之后仍有两个真问题**：
    #   ① **`(\d+)` 把小数读成整数**——「实测 5.4 秒」被读成「4 秒」；
    #   ② **同一行里的数字未必是同一个量**——「本方向让这件事进构建：**97 秒的东西里**
    #      只有 0.6 秒那一段与有没有在验有关**」里的 97 说的是 `selftest-meta.sh`。
    # **这不是把阈值调一下能解决的**：
    # **「一句话里的数字属于哪个量」在散文里机械不可判定**，
    # **而一个只会吵的判据会把「照它改」变成机械动作**（纪律 143：
    # **会误报的守卫比没有守卫更坏**）。**所以只问机制，不问散文。**
    #
    # **它明确不管什么**：**它不核「文档里写的构建秒数对不对」。**
    # **本批把那几处据实订正了，那是一次人工修正——判据不代替它。**
    _g_src = {}
    for _rel in ("build-site.sh", os.path.join("scripts", "record-build-result.py"),
                 os.path.join("scripts", "buildrecord.py")):
        try:
            with open(os.path.join(ROOT, _rel), encoding="utf-8") as _fh:
                _g_src[_rel] = _fh.read()
        except OSError:
            _g_src[_rel] = None
    _bs_flat = re.sub(r"\\\n[ \t]*", " ", _g_src["build-site.sh"] or "")
    #: **七个事实 = 链条上的七个接点**，少一个环就断。**分组按「谁接谁」，
    #: **而报告时只报断掉的那一环的名字**——**「哪一环断了」比「有几个断了」有用**。
    _G_FACTS = [
        ("`build-site.sh` 记构建起点", "build-site.sh", r"BEEF_T0=\$\(date \+%s\)"),
        ("`build-site.sh` 算构建墙钟", "build-site.sh", r"BEEF_SECS=\$\(\("),
        ("`build-site.sh` 把墙钟传给记录脚本", "build-site.sh",
         r"record-build-result\.py[^\n]*--secs"),
        ("`record-build-result.py` 接受 `--secs`", os.path.join("scripts", "record-build-result.py"),
         r"add_argument\(\"--secs\""),
        ("`record-build-result.py` 把 `a.secs` 交给 `write_record`",
         os.path.join("scripts", "record-build-result.py"), r"write_record\([^)]*a\.secs"),
        ("`buildrecord.write_record` 收下 `secs`", os.path.join("scripts", "buildrecord.py"),
         r"def write_record\([^)]*secs"),
        ("`buildrecord` 把 `secs=` 写进记录体", os.path.join("scripts", "buildrecord.py"),
         r"secs=%s"),
    ]
    _unreadable = [r for r, t in _g_src.items() if t is None]
    if _unreadable:
        problems.append(
            "方向四g：读不到 %s"
            "　→ **墙钟这条链的某一环根本没有文件可读**，"
            "于是机制无从核对（**与「机制没接上」是两回事**：前者要补文件，后者要补代码）"
            % "、".join("`%s`" % r for r in _unreadable))
    _broken = [name for name, rel, pat in _G_FACTS
               if _g_src.get(rel) is not None
               and not re.search(pat, _bs_flat if rel == "build-site.sh" else _g_src[rel])]
    if _broken:
        problems.append(
            "方向四g：构建墙钟这条链上断了 %s"
            "　→ **「构建要多久」于是没有任何真值来源**，全树的秒数就都是手抄的，"
            "**而本项目那份手抄低了 10 倍**（Batch 192 写「25 秒」，Batch 280 实测 **251 秒**）。"
            "**修法是让 `build-site.sh` 自己把它测出来传下去，而不是去改某个抄本**"
            % "、".join("**%s**" % b for b in _broken))
    if not _unreadable and not _broken:
        _seen = "-"
        try:
            with open(buildrecord.record_path(), encoding="utf-8") as _fh:
                _m = re.search(r"^secs=(\d+)\s*$", _fh.read(), re.M)
            if _m:
                _seen = "**%s 秒**" % _m.group(1)
        except OSError:
            pass
        print("方向四g：构建墙钟的机制接上了（`build-site.sh` 记起点/算墙钟/传给记录脚本 "
              "→ `record-build-result.py` 收下并透传 → `buildrecord.write_record` 收下并写出 "
              "`secs=`）；上一次绿构建记录里的 `secs=` 是 %s" % _seen)


    # ④f（**Batch 278 新增**）：**SLOW 的成本必须能落到源文件里真实存在的步骤上。**
    #
    # **为什么需要它**：本批实测 `selftest-zero-input.py` 的**两个抄本都是 190、
    # 互相印证、方向四e 报绿**，而**三次分段实测是 202.02 / 196.36 / 196.56 秒**
    # ——**这是纪律 310「同一个量被抄了两遍，而两遍一起过期」的第三个实例**，
    # **也正是方向四e 注释里自己写下的那个盲区**。**四e 抓不到它，因为
    # 「两个抄本都对得上」在它眼里就是一致。**
    #
    # **本方向问的是另一个问题**：**这个成本由哪几步构成，那些步骤还在不在。**
    # **它同样抓不到「两遍一起错」**（**这一条必须写在这里**），
    # **但它保证两件 ④e 做不到的事**：
    #   ① **下一次重测有一个可以逐段落笔的位置**——而 Batch 278 量出来的那件事
    #      （**空树那半只要 5～7 秒，贵的 97% 在另一半**）此前在树上无处可写，
    #      **于是「这份东西整体很慢」读起来像「它每一部分都很慢」**；
    #   ② **写错的那一段会立刻报「锚点不在场」**——与方向五治夹具锚点是同一个病，
    #      **而那个病在 `READONLY_EXEMPT` 上已经真实发生过一次**
    #      （在它上方加 3 行注释，4 条按行号登记的豁免集体错位）。
    #
    # **锚点用源码子串、不用行号**，理由同上。
    # **段和与 `seconds` 的偏离容忍度**：偏大与偏小**两个方向都要报**——
    # 与方向四e 不同（那里偏大是安全的预算余量），
    # **这里偏小意味着「账上这笔钱有一半没交代去处」，偏大意味着「分项把自己算了两遍」**。
    SLOW_SPLIT_LO, SLOW_SPLIT_HI = 0.4, 3.0
    for _fn in sorted(SLOW):
        _split = SLOW[_fn].get("cost_split")
        if not _split:
            problems.append(
                f"方向四f：SLOW 里登记了 {_fn}，而它**没有 `cost_split`**"
                "　→ 「它慢」现在只有一个数，**说不出这个数由哪几步构成**，"
                "于是「贵的是哪一段」只能靠人重读代码——**而人不会重读**。"
                "**单项也算数**（= 如实登记「未分拆」），"
                "**但不许没有**：没有与「未分拆」在账本上是同一种状态")
            continue
        _spath = os.path.join(SCRIPTS, _fn)
        try:
            with open(_spath, encoding="utf-8", errors="ignore") as _fh:
                _ssrc = _fh.read()
        except OSError:
            problems.append(
                f"方向四f：读不到 {_fn} 的源文件，**它的 `cost_split` 本轮没法核**"
                "　→ 读不到就是「核不到」，不是「核过了」（纪律 203）")
            continue
        for _step in sorted(_split):
            if _step not in _ssrc:
                problems.append(
                    f"方向四f：{_fn} 的 `cost_split` 说成本落在「{_step}」，"
                    "**而它那份源文件里没有这一段**"
                    "　→ 成本归属指向了一个不存在的步骤，等于没有归属；"
                    "**改锚点或改那一步的名字**（**不是删掉这条登记**——"
                    "**删掉它，下一个人就会重新编一个归属**）")
        _tot = 0.0
        for _v in _split.values():
            try:
                _tot += float(_v)
            except (TypeError, ValueError):
                problems.append(
                    f"方向四f：{_fn} 的 `cost_split` 里有非数字的段耗时（{_v!r}）"
                    "　→ 秒数必须是数字，否则「段和」这栏本身就是空的")
        _decl = SLOW[_fn].get("seconds")
        if _tot > 0 and isinstance(_decl, (int, float)) and _decl > 0:
            if not (SLOW_SPLIT_LO * _decl <= _tot <= SLOW_SPLIT_HI * _decl):
                problems.append(
                    f"方向四f：{_fn} 的 `cost_split` 段和 {_tot:g}s，"
                    f"而 `seconds` 登记 {_decl}s（{_tot / _decl:.2f} 倍，"
                    f"允许 {SLOW_SPLIT_LO}–{SLOW_SPLIT_HI}）"
                    "　→ 偏小是「这笔钱有一半没交代去处」，"
                    "偏大是「分项把自己算了两遍」；**两个方向都要改**")
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
    fx_checked, fx_skipped, fx_void, fx_stale, fx_unknown = 0, 0, [], [], []
    #: **Batch 276：先问一次「工作区脏不脏」，问不到就当没问**——
    #: **前提无法评估 ≠ 判为夹具坏了**（与这一族其余各方向同一条理由）。
    _dirty = _dirty_paths()
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
            why = (tail[-1] if tail else "无输出")[:70]
            # **Batch 276：失配时先问「它要改的那个文件自己有未提交改动吗」。**
            # **只有这时候才不能归咎于夹具**——实测（同事的注入实验让
            # `asset-library.md` 首行不再是 H1）夹具 46/47 因此报失配，
            # **而错的是目标文件变了，不是夹具坏了**。
            # **条件收到文件粒度而不是整棵树**：整树降级的误伤面太大——
            # **我自己改一句 AUDIT.md 就会把 23 个夹具的真失效一起降级。**
            _rel = _repo_rel(target) if _dirty is not None else None
            if _rel is None:
                # **② 算不出来就说算不出来**——**绝不能当成「不脏」**，
                # 那会让同事那处改动被报成「夹具坏了」（本函数第一版正是这样）。
                #
                # **⚠️ 而这一支的第一版栽在另一侧**：它既不报也不降级，
                # **等于把一个真的夹具失配吞掉了**——
                # **实测：既有用例 12（`m_fixture_anchor_missed`）当场变红**
                # （它用 `sandbox()`，**只搬 `scripts/`、不是 git 检出**，
                # 于是问不到）。**纪律 311 推论二描述的失效，方向相反地又发生了一次：
                # 「算不出来」这一次伪装成了「没问题」。**
                #
                # **所以这里选保守的一侧：照旧报。**
                # **本项目的保守侧是「照报」而不是「放过」**（假阴性比误报危险）。
                # **而这也不会把误诊带回来**：「问不到」只发生在**不是 git 检出**的沙箱里
                # （`sandbox()` 只搬 `scripts/`），**那里根本没有「同事的 WIP」这回事**，
                # **所以「照报」在那一侧既安全又是唯一合理的默认**。
                fx_unknown.append((os.path.basename(fixer), why))
                fx_void.append((os.path.basename(fixer), why))
            elif _rel in _dirty:
                fx_stale.append((os.path.basename(fixer), why))
            else:
                fx_void.append((os.path.basename(fixer), why))
    if not _slow_fixture_triples("selftest-meta.sh"):
        problems.append(
            "方向五：**从 `selftest-meta.sh` 里抽不出任何注入夹具三元组**——"
            "要么它的用例调用格式变了，要么整份脚本被清空"
            "　→ **「一个都没检查」与「全部都检查了」必须长得不一样**（纪律 156/159）")
    if fx_unknown:
        print("  方向五：%d 个夹具失配，而**本闸算不出目标文件的仓库相对路径**（%s）"
              "　→ **归因这一轮问不到，所以按保守侧照旧报成「夹具坏了」**"
              "（**不报才是错的**——实测既有用例 12 就这样被吞掉过一次；"
              "Batch 276 也实测踩过 macOS `/var` → `/private/var` 软链让本函数恒算错）"
              % (len(fx_unknown), "、".join(f for f, _ in fx_unknown)))
    if fx_stale:
        print("  方向五：%d 个夹具**打不中锚点，而它们要改的那个文件本身有未提交改动**（%s）"
              "　→ **这一类是「前提不成立」，不是「夹具坏了」**：按三段约定它属于未能核对，"
              "**不计入不一致**。**丢弃或 stash 别人的改动是被明令禁止的**"
              "（工作区脏不是缺陷，同事正在改东西是正常状态——闸 38 报的就是这个状态）"
              % (len(fx_stale), "、".join("%s（%s）" % (f, w[:40]) for f, w in fx_stale)))
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
    #: **Batch 282：按设计排除的那份必须在这里就出 `fleet`，
    #: 而不是在循环里 `continue`**——
    #: **方向十七的分界是「跑没跑」，出 `fleet` 才算「按设计没跑」**
    #: （Batch 274 踩过同一个坑：「既不在 by_design 也不在 dropped」，
    #: **而输出上一个数与列出来的东西对不上**）。
    #: **在循环里 continue 的后果实测到了**：它被算进
    #: 「本轮真跑失败而掉出覆盖」——**而它一次都没跑过，不是它坏了**。
    fleet = [n for n in fleet if n not in FLEET_NEEDS_REAL_HISTORY]
    if "selftest-selftest-bootable.py" not in SLOW:
        problems.append(
            "方向十六：`selftest-selftest-bootable.py` **不在 SLOW 登记里**——"
            "它是闸 18 自己的反验，被方向十六真跑会**无限递归**"
            "　→ 请把它登记进 SLOW 并写明理由")
    # **前提：真跑不许改现场。** 先记一份 git 状态，跑完再记一份，只比差集。
    # **这不是「现场干不干净」，而是「跑完有没有变」**——
    # 这个仓里别人正在改东西是常态，所以只能比差集，不能比绝对状态。
    def _snapshot():
        # **Batch 276：改为复用 `_dirty_paths()`**——**同一条命令、同一套解析**，
        # 只是搬到了模块级（方向五也要用）。**收敛前量过等价：两边都是
        # `git status --porcelain -- .`，而新增的那点「重命名取 `->` 之后那一半」
        # **只会让它更准**（原来重命名项会原样留着 `old -> new`，永远匹配不上路径）。
        return _dirty_paths()

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
    #: **Batch 276 新增**：退出码 2 = **本轮未能核对**（环境缺口），
    #: **它与 rc=1「核出不一致」必须分开**——本批给 `selftest-link-labels.sh`
    #: 加了基线前提，工作区脏时它返回 2，**而方向十六原来把任何非 0 都写成
    #: 「真跑没跑通」**。**那正是 Batch 275 记下的误诊，本批自己又犯了一次。**
    unverified = []      # fn 列表；方向十七要把它与「真跑失败」分开报
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
    #: **方向十九的账（**Batch 281 新增**）**：`反验名 -> 它动过的手册文件`。
    #: **为什么要在这里顺手量**：方向十六本来就要把每份非慢反验在**真实手册树上**
    #: 真跑一遍，**而「它跑的时候有没有动这棵树」是同一个循环里的另一个观察**——
    #: **另起一遍普查就是同一件事做两遍**（**Batch 281 的普查实测跑了一小时**）。
    tree_writes = {}
    fp_cost = 0.0
    #: **Batch 282：真跑搬进完整副本树**（**实测：109 份里只有 3 份会因环境而不同，
    #: 而 3 份的差别全部来自副本树的两个环境条件，已在建树时补齐**）。
    #: **方向十九因此从「27 份登记在案」升级成「真实手册树一次都不许被碰」**：
    #: **它量的始终是真树（`ROOT`），而反验现在写在副本上**——
    #: **于是一条命中就等于「有反验用绝对路径逃出了副本树」，那才是真信号**。
    #: **`fleet` 已经空的时候不建树**——`sandbox()` 那种只有 `scripts/` 的沙箱
    #: 会在上面被清空，**而这里再搬 15 MB 加一次 git 提交是纯浪费**。
    #: **⚠️ 这行第一版写成 `fleet_root, fleet_manual = _make_fleet_tree() if fleet else (None, None)`**——
    #: **而 `_make_fleet_tree()` 建不出来时返回的是单个 `None`，不是 `(None, None)`**，
    #: **于是解包炸 `TypeError: cannot unpack non-iterable NoneType object`，
    #: 整份闸崩掉、方向十六那一行都没打出来**（用例 49 实测）。
    #: **而 Batch 282 写下的契约原话是「建不出来就返回 `None`，
    #: 而调用方必须把它当成「本轮不跑」而不是「放行」」——
    #: **本批改返回值形状的时候把这条契约一起改了，而没人回头看它。**
    #: **「改了签名」与「改了契约」是两件事，而只有后者会静悄悄地坏掉。**
    _fleet = _make_fleet_tree() if fleet else None
    fleet_root, fleet_manual = _fleet if _fleet else (None, None)
    #: **Batch 283：`cwd` 必须是**手册**目录，而不再是副本树的 git 根**——
    #: 反验一律用 `HERE = dirname(abspath(__file__))` 推 `ROOT`，
    #: **它们读的是自己脚下那份树，与 `cwd` 无关**；但 `cwd` 决定相对路径解析，
    #: **而闸 18 自己就是按 `fleet_cwd` 拼脚本路径的**。
    fleet_cwd = os.path.join(fleet_manual, "scripts") if fleet_manual else None
    #: **⚠️ Batch 282 踩到：`fleet` 已经空的时候**（`sandbox()` 那种只有 `scripts/`
    #: 的沙箱在上面被清空了）**根本不该走到这里报「建不出副本树」**——
    #: **第一版只判 `if not fleet_root`，于是 12 条「必须不报」的用例一起变红**，
    #: **而它们红的理由与它们要验的性质毫无关系**。
    #: **「建不出树」与「本轮没东西要跑」必须分开**（纪律 156：没核不等于核过）。
    if fleet and not fleet_root:
        problems.append(
            "方向十六：**建不出真跑用的副本树**，本轮 %d 份一份都没跑"
            "　→ **不拿「跑不了」当「跑过了」**（纪律 156）" % len(fleet))
        print("  方向十六：[不适用] 建不出真跑副本树，本轮一份不跑——"
              "**「没跑」与「跑了」必须分开**")
    if not fleet_root:
        fleet = []
    if fleet_root:
        #: **Batch 283 新增：真跑之前先核副本树的两条环境性质。**
        #:
        #: **判据问的是「这份副本还能不能代表真树」，而那正是它存在的前提**——
        #: **① 历史**：真仓 HEAD 必须是副本树 HEAD 的祖先（`merge-base --is-ancestor`），
        #: **一条命令就分得开「真历史」与「`git init` 造的假历史」**；
        #: **② 内容**：副本树必须与真树逐文件一致。
        #:
        #: **② 治的是「忘了覆盖」**：只 clone 不覆盖的话，副本里是**上一次提交的状态**，
        #: **于是 39 份真跑核的是上一批的手册，而构建照样报绿**——
        #: **这是比反验坏了更坏的一种错，因为它没有任何症状。**
        _envp = _check_fleet_env(fleet_root, fleet_manual)
        if _envp:
            problems.extend(_envp)
            print("  方向十六：副本树环境性质不成立，本轮一份都不跑——%s"
                  % "；".join(x.split("\n")[0] for x in _envp))
            fleet = []
    for fn in fleet:
        if fn in FLEET_NEEDS_REAL_HISTORY:
            continue
        if budget - fleet_cost <= 0:
            problems.append(
                f"方向十六：整体预算 {budget:.0f} 秒用尽，**剩下 {len(fleet) - ran} 份"
                f"反验没有跑**（本轮已跑 {ok}/{len(fleet)} 份全绿）"
                "　→ **先分清是哪一种**：**这通常意味着机器太慢，而不是反验坏了**"
                "（预算 600 秒 ≈ 观测最大值 84.8 秒的 7 倍）；"
                "真要提速就把慢的那几份登记进 SLOW")
            break
        #: **跑之前拍一张指纹**——判据问的是「它动过没有」，
        #: **而绝大多数反验是「改完立刻还原」**：
        #: **只比跑完之后的内容，这一类一份也看不见**
        #:（**而它们恰恰是最危险的一类：被 kill 的那一次不会有还原**）。
        _f0 = time.time()
        _fp0 = _tree_fingerprint()
        _f1 = time.time()   # 第一张指纹取完
        t0 = time.time()
        try:
            r = subprocess.run(
                ["bash", fn] if fn.endswith(".sh") else [sys.executable, fn],
                cwd=fleet_cwd or SCRIPTS, capture_output=True, text=True,
                timeout=min(per, budget - fleet_cost))
            rc, out = r.returncode, (r.stdout or "") + (r.stderr or "")
        except subprocess.TimeoutExpired:
            rc, out = None, ""
        _a2 = time.time()   # 真跑结束（第二张指纹之前）
        _fp1 = _tree_fingerprint()
        _a3 = time.time()
        #: **Batch 283 修一个记账 bug**：`fp_cost` 原来只算了**跑之前那一张**指纹。
        #: 展开就是 `(a3-a0) - (a3-a1) = a1-a0`——
        #: **而第二张指纹在 `t0` 之后取的，所以它被一并减掉了**；
        #: **与此同时 `d = time.time() - t0`（真跑耗时）却把它算进了总账**。
        #: **于是「指纹代价」这个数恰好是真相的一半**，
        #: **而它正是用来回答「这套机制每次构建要付多少」的那个数**。
        #: **低报的方向是唯一危险的那个**（与 `SELFTEST_COSTS` 同一条纪律，Batch 275）——
        #: **一个让人以为「加指纹很便宜」的数，比没有这个数更坏。**
        fp_cost += (_f1 - _f0) + (_a3 - _a2)
        _chg, _del, _newf = _tree_delta(_fp0, _fp1)
        if _chg or _del or _newf:
            tree_writes[fn] = (_chg + _del + _newf)[:6]
        d = time.time() - t0
        fleet_cost += d
        ran += 1
        if rc == 0:
            ok += 1
            tally[fn] = _tally(out)
            continue
        if rc == 2:
            # **Batch 276：rc=2 单列，不进 `problems`。**
            # **理由是本文件自己定的规矩**：rc=2 的含义是「未能核对」，
            # 而把环境的缺口汇进 `problems` 就是**拿它冒充「反验坏了」**——
            # **反验文件头把这一种列为判据最坏的一种错**（纪律 156 / 204）。
            # **代价要说清楚**（与下面 `env_gap` 同一笔账）：一个**真坏**的反验
            # 若错返回 2，这一轮会被盖住，**而那是可自愈的**——
            # 前提恢复后重跑，它会以 rc=1 自己现身。
            unverified.append(fn)
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
            allran = set(claim) & set(fleet)
            #: **`dropped` 必须再拆一次**（Batch 276）：`tally` 只在 `rc == 0` 时记，
            #: 所以「跑了但没记上」里有**两种**：**真跑失败**与**本轮未能核对（rc=2）**。
            #: **而这两种要修的东西完全不同**——前者是自己的反验坏了，
            #: 后者是前提或环境不成立（**后者最常见的原因是工作区有别人的未提交改动，
            #: 而丢弃它是明令禁止的**）。**把它们并成一个数，就是在教人做那件事。**
            dropped = sorted(allran - set(tally) - set(unverified))   # 真跑失败
            unver17 = sorted(allran & set(unverified))                # 本轮未能核对
            #: **完整性守卫**：本条若照实分完，两类之和必须等于总数。
            #: **对不上就报出来，不许安静地少列一个**（纪律 203）。
            unaccounted = sorted(set(uncovered) - set(by_design)
                                - set(dropped) - set(unver17))
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
            if unver17:
                parts.append("**本轮未能核对（rc=2）而掉出覆盖 %d 份（%s）**——"
                             "**这不是「不一致」，也不在自己的反验上**："
                             "**多半是工作区有未提交的改动让基线前提不成立，"
                             "而丢弃那些改动是被明令禁止的**"
                             % (len(unver17), "、".join(unver17)))
            if unaccounted:
                parts.append("**还有 %d 份两类都没算进去（%s）——**这是判据自己的缺口"
                             % (len(unaccounted), "、".join(unaccounted)))
            print("  方向十七：对应关系表 %d 行里，本方向核到 %d 行"
                  "（%d 处不一致、%d 份解析不出）；%s"
                  % (len(claim), checked, mismatch, unparsed, "；".join(parts)))


    #: **方向十九（**Batch 281 新增**）：真跑期间不得改动手册树。**
    #:
    #: **它治的是 Batch 280 那次事故的根**：那次是「跑闸 18 被前台超时杀掉，
    #: `selftest-shot-drift.py` 的注入留在树上」，**而下一轮闸 18 报的是
    #: 「`selftest-shot-drift.py` 真跑没跑通」——报的是后果不是原因**。
    #:
    #: **实测规模**（隔离副本树 + 审计钩子逐份真跑，只算基线提交里已跟踪的路径）：
    #: **73 份 python 反验里 26 份改动手册树里原有的文件**，
    #: **而 `20-reference.md` 被 8 份碰**——**它是基线声明文件，
    #: 8 道闸靠它解析上游，一次中断就能让全树变成 rc=2「未能核对」**。
    #:
    #: **为什么本批不把它们全改掉，而先立判据**：26 份逐一改是几个批次的活，
    #: **而「第 27 份」今天就能抓**。**豁免表逐条写了理由**——
    #: **一张没有理由的名单，下一个人只会照着它继续加**（纪律 305）。
    _new = sorted(n for n in tree_writes if n not in TREE_WRITE_EXEMPT)
    for _n in _new:
        problems.append(
            "方向十九：反验 `%s` **真跑期间改动了手册树里的文件**（%s）"
            "　→ **反验只该在临时目录里动手脚**。"
            "**它改的是真实手册树，于是「跑完 git status 干净」全靠 finally 兜着，"
            "而 finally 在被 kill / 超时 / Ctrl-C 时不执行**"
            "（Batch 280 实测：一次超时就在树里留下了注入，"
            "而下一轮闸 18 报的是「那份反验没跑通」——**报的是后果不是原因**）。"
            "**修法是给它建沙箱**；确实必须写真树的，登记进 `TREE_WRITE_EXEMPT` 并写明理由"
            % (_n, "、".join(tree_writes[_n][:4])))
    _needhist = sorted(FLEET_NEEDS_REAL_HISTORY)
    if fleet_root:
        shutil.rmtree(fleet_root, ignore_errors=True)
    _stale = sorted(set(TREE_WRITE_EXEMPT) - set(tree_writes))
    #: **方向二十一（Batch 284）**：指纹跳过表本身要被守着。
    _skip_p, _skip_cov, _skip_absent, _skip_note = _check_skip_table()
    problems.extend(_skip_p)
    if _skip_note is not None:
        #: **[不适用] 的措辞照抄方向十五/十六/十七**——**闸里已经有这个先例，
        #: 而一个「新方向」不按已有先例写，就要靠一轮 52 例才发现它会误伤**。
        print("  方向二十一：[不适用] %s，**「跳过表有没有藏人」这一项本轮没核**"
              "——如实报出，不装作核过了" % _skip_note)
    else:
        print("  方向二十一：指纹跳过表 %d 项，**含已入库文件的 %d 项**"
              "（另有 %d 项在树里根本不存在——**那不是错，"
              "那说明它们是「防未来」而不是「现在有用」）"
              % (len(_FP_SKIP_DIRS), len(_skip_p), len(_skip_absent)))
    print("  方向十九：真跑期间 **%d 份**反验改动了手册树"
          "（已登记豁免 %d、新命中 %d）；指纹代价 %.2f 秒；%s%s"
          % (len(tree_writes), len(tree_writes) - len(_new), len(_new), fp_cost,
             "**有新命中**" if _new else "**没有新命中**",
             ("；**豁免表里 %d 份本轮没命中**（%s%s）——"
              "**这不等于它们已经安全**：本方向数的是「真树这一轮有没有动到」，"
              "**而一份反验在什么条件下动树是可以变的**"
              "（实测就有三份在副本树里因环境缺口提前退出、普查量不到，真树上才动到）。"
              "**所以这张表宁可宽，不可删**——**删一条的代价是一次假红，"
              "而留一条的代价只是一行「本轮没命中」**（纪律 143）"
              % (len(_stale), "、".join(_stale[:4]),
                 " 等" if len(_stale) > 4 else "")
              if _stale else "")))

    print("  方向十六：真跑 %d 份非慢反验，%d 份 rc=0，用时 %.1f 秒%s%s"
          % (ran, ok, fleet_cost,
             ("；**另有 %d 份没跑**（%s）"
              % (len(fleet_all) - ran, _not_run_reasons(fleet_all, fleet))
              if fleet else "；**本轮一份都没跑**"),
             ("" if not unverified else
              "；**%d 份本轮未能核对（rc=2，不是不一致）**（%s）"
              "　→ **这一类不是「反验坏了」**：按三段约定 2 = 未能核对，"
              "**多半是前提或环境不成立**（Batch 276：工作区有未提交改动时，"
              "`selftest-link-labels.sh` 的基线前提不成立）。"
              "**它不计入不一致，也更不该用「丢弃别人的改动」去消掉**"
              % (len(unverified), "、".join(sorted(unverified))))))

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
