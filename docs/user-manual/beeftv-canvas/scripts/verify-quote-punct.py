#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十二道闸：手册正文引号文案的**标点漂移**核对（Batch 185 新增）。

背景（Batch 185）：Batch 176 把上游 `generation-error.ts` 的失败文案逐类对账进手册，
闸 15 守着「**类别有没有覆盖**」；但**没有人核过抄下来的字是不是逐字一致**。
本批普查手册正文所有「」引用时抓到两处——都在 `README.md` 的版本增量行里：

  · 手册写「本地任务保存失败（尚未提交生成）」，上游是「本地任务保存失败，**尚未提交生成**」
    （**括号是手册自己加的**）；
  · 手册写「视频已生成但暂时无法取回」，上游是「视频已生成**，**但暂时无法取回」（**少了逗号**）。

**而 `90-troubleshooting.md` 引的一直是对的**——于是同一本手册对同一条消息给了两种写法，
其中一种是错的。**引界面文案的全部意义就是让读者拿去和屏幕上的字比对**，
标点对不上，这条用途就废了；而读者看到对不上时的第一反应是「我的版本不对 / 手册写错了」。

**为什么只查标点漂移，不查「引号里的字在上游存不存在」**（本批量过之后才定的范围）：
手册里 240 条去重引号，扩到全仓搜仍有 94 条不命中，而**逐条读原文后绝大多数不是界面文案**——
「墓碑」「取证基线」「谁的锅」「宁可什么都不写也不写错」全是**手册自己的术语强调**，
这个文档的「」约定被重载成了「引用」与「强调」两用。**硬扫全表的假阳性率约 40%**，
而**判据把不相干的东西报成异常，人就会学会忽略它**（Batch 142 闸 8 第一版的同一课）。

**本闸只报一个精确得多的形态：文字在上游存在、但逐字对不上。**
判据是两步比对——

  1. 把引号里的字**去掉全部标点与空白**，与上游语料的同样归一化结果比；
  2. 若归一化后**能对上**，而归一化前的**逐字比对对不上** → 报「标点漂移」。

这样一来，手册自己的术语**在归一化那一步就落选**（上游根本没有这些字的组合），
根本走不到第 2 步；而**只有「字都是那些字、只是标点不同」才会被抓**。

**一处必须处理的写法**：本手册用 `/` 并列两个独立文案（`「生成失败 / 请查看详情后再决定是否重试」`、
`「已完成 / 失败 / 已取消」`）。所以先按 `/` 拆开、逐半判定——否则 `「生成失败 / ……」`
整体去标点后能对上，会被误报成漂移（本批探针确实误报过这一条）。

**方向二是自检，不是内容判据**：拿一条**只存在于 backend 的**已知文案当探针，
若判据在上游语料里找不到它，说明语料读取这条链路退化了（`read_many` 出问题、
基线 ref 读错、路径写错），此时必须 rc=2「未能核对」——**而不能让判据在一个
空语料上安静地全绿**（纪律 101：解析器退化必须表现为失败，而不是通过）。

**顺带修掉一个覆盖漏洞**：闸 10 核截图文案只搜 `web/src`，而手册引的界面文案**大量来自
后端**。实测把搜索面扩到 `web + backend` 后多命中 **10 条**（`Agent 能力已下线…`、
`云端画布已有更新…`、`本地转写服务未配置：…` 等），**这 10 条是前端搜索永远够不到的**。

**Batch 304 补一条范围纪律：测试文件不进语料。**
这条不是「顺手收紧一下」，是实测出来的**判据形状问题**：本闸的两条臂读的不是同一份东西。

  · 第一臂「`part in corpus`」读的是**整份源码文本**——所以 JSX 渲染的文案（`>新建</Button>`）
    对它是可见的，逐字命中走的就是这一臂；
  · 第二臂「`norm(part) in norm_literals`」读的是**带引号的字符串字面量集合**——
    而 **JSX 文本根本没有引号**，所以第二臂对 JSX 文案**结构性不可见**。

于是「这条文案在上游存在吗」这件事在第二臂上只能靠**别处恰好有一个同字的带引号字面量**来回答。
而**测试文件正是最容易提供这种巧合字面量的地方**：上游 `web/test/canvas-folder-storage.test.ts`
里有 4 处恰好是 `新建` 的字面量（给测试文件夹起的名字），于是 `norm_literals` 里第一次出现了 `新建`，
把本闸一条**从未触发过**的分支激活，误报 `asset-library.md` 的两处「+ 新建」——
**而上游渲染的是 `{<Plus />}>新建</Button>`，那个 `+` 是图标，不是文案里的字符。**
（实测：`origin/main` 上 `新建` 的带引号字面量**全库只有那一个测试文件里有**，
产品代码里 **0 处**；基线 `bcc3b05` 上则是 **两处都没有**——所以这条误报在基线上一直潜伏着。）

**为什么剔测试文件是修对而不是掩盖**：测试文件**不是产品**，
而本闸问的是「读者拿手册里这句话去和屏幕上的字比对，对不对得上」。
**只在测试里被引号引起来的那条文案，恰恰说明上游是把它当 JSX 文本渲染的**——
**没有引号的源码里不存在标点，于是从那种证人推出来的「标点漂移」，是在一个不可能有标点漂移的源上推的。**

**剔的范围是量过的，不是拍的**（`origin/main`，两个 ref 各量一遍）：

  · 剔掉的 **882** 个文件里有 **76808** 个字面量、**20999** 个归一化文案**只由测试提供**
    （全量去重 46017 → 产品去重 25018，**人口缩 46%**）；
  · **手册 947 段被检文案，剔完之后新增 0 条、消失 2 条**——消失的正是那两处误报，
    **而那两个 ref 上没有任何一条真漂移被顺带削掉**（origin/main 全量语料下本来就只报这 2 条）；
  · 反验 5 条能抓用例的证人**逐条查过在产品侧**（用例 1/2/6 的 norm 都在产品字面量集里），
    方向二的自检 `PROBE` 也在产品语料里——**所以剔测试没有削掉任何一条鉴别力**。

退出码：0 无标点漂移；1 有漂移；2 未能核对（语料读不到或自检探针失配，不等于通过）。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beefsrc
from baseline import resolve_ref, BaselineError, announce_fallback   # noqa: E402
from batchread import read_many                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# 输入范围：读者真正会读的那几个文件。内部资料（AUDIT / PROGRESS / AUDIT-RULES）
# 里的「」大量是纪律编号与自我指涉，**不归本闸管**——判据的输入范围必须等于发布范围。
# 与 verify-label-drift.py 同一写法：环境变量优先 + 硬编码兜底。
# **只认环境变量是不够的**——构建脚本里没人 export 它，闸会一路 rc=2「未能核对」。

# **这五个必须都是会被发布的页面**（Batch 190 加了守卫，见 `verify-scope.py` 方向一）。
# 本清单原先有第六个 `PUBLISH.md`——而它被 `config.mjs` 的 `srcExclude` 排除，
# **根本不会出现在站点上**。它能躺着是因为：本闸「扫过了」这件事是真的，
# 只是它扫的东西里有一份读者读不到；而 `PUBLISH.md` 全篇只有 1 段引号，
# 归一化后匹配不上任何上游文案——**扫了等于没扫**。
# 现在这类混装由闸 24 拦着：清单里只要混进一个被排除的文件，闸就红。
PAGES = ["README.md", "00-quickstart.md", "20-reference.md", "30-concepts.md",
         "90-troubleshooting.md"]

# **Batch 186 扩进来的**：30 个任务页。实测它们含 **662 段**引号引用，
# 而 Batch 185 的范围只有 6 个文件 237 段——**读者最先读的就是任务页，而它们当时完全没进扫描**。
# 扩进来之后实测只多报 1 条（「视频处理 ∨」），**任务页的引用纪律比主干页还好**。
TASK_GLOB = "10-tasks/*.md"

# 去标点：只保留文字类字符（中文、字母、数字）。
STRIP_RE = re.compile(r"[^\w一-鿿]+", re.UNICODE)
QUOTE_RE = re.compile(r"「([^」]{2,60})」")
# 源码里的字符串字面量：引号成对、字面量内不含裸引号与换行，
# 所以这个正则抽出来的**就是**字面量本身，不会跨字面量拼接。
LITERAL_RE = re.compile("[`'\"]" + "([^`'\"\n]{2,80})" + "[`'\"]")
# 本手册用 `/` 与 `→` 并列两个独立文案，两种都要先拆开再逐半判定。
SPLIT_RE = re.compile("[/→]")
SRC_EXT = (".ts", ".tsx", ".go")

# **Batch 304：测试文件不进语料**（理由见文件头）。
# **三种形态都要覆盖，缺一种就等于放行那一类**——实测 `origin/main` 上被判成测试的是
# 882 个文件（`web/test/` 目录型 + `*_test.go` + `*.test.ts(x)` / `*.spec.ts(x)`）。
# **刻意不按「文件名里有没有 test」这种宽形态收**：那会把 `latest.tsx`、
# `contest.ts` 这类正当产品文件一起剔掉，而**误剔的后果是让判据变瞎，且没人会发现**。
TEST_PATH_RE = re.compile(
    r"(^|/)(tests?|__tests__|testdata|e2e)(/|$)"      # 目录型
    r"|(_test\.go$)"                                  # Go 惯例
    r"|(\.(test|spec)\.[cm]?[tj]sx?$)"                # JS/TS 惯例
)

# 方向二的自检探针：**只存在于 backend 的**一条文案。
# 选它是因为它同时证明两件事——语料读到了 backend，且逐字比对这条链路是通的。
PROBE = "云端画布已有更新，已停止覆盖；请保留本地草稿并加载最新版本"


def norm(s):
    return STRIP_RE.sub("", s)


def load_corpus(src, ref):
    """把上游 web/ 与 backend/ 的**产品**源码一次性读进内存（batchread：两次进程调用）。

    返回 `(语料, 参与的文件数, 剔掉的测试文件数)`——**第三个返回值是刻意给的**：
    本批把「剔测试」当成一条范围纪律，而**一条没人能核的收紧就是又一次静默失效**
    （纪律 101：范围变了必须看得见）。剔除量会打进输出。

    **仍然一次 `read_many` 读完再筛，而不是分两次读**：分两次要多两次子进程调用，
    而筛选是纯内存判断——**这里该省的是进程，不是那点字节**（Batch 181 的同一条教训）。
    """
    import subprocess
    r = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref],
                       cwd=src, capture_output=True, text=True)
    if r.returncode != 0:
        raise RuntimeError("git ls-tree 失败：%s" % (r.stderr or "").strip()[:160])
    files = [f for f in r.stdout.split("\n")
             if f.startswith(("web/", "backend/")) and f.endswith(SRC_EXT)]
    if not files:
        raise RuntimeError("按扩展名筛出 0 个源文件——筛选条件退化了")
    blobs = read_many(src, ref, files)
    if not blobs:
        raise RuntimeError("批量读取返回 0 个文件")
    kept = [f for f in files if f in blobs and not TEST_PATH_RE.search(f)]
    dropped = [f for f in files if f in blobs and TEST_PATH_RE.search(f)]
    if not kept:
        raise RuntimeError("剔掉测试文件之后一个产品文件都不剩——剔除条件退化了")
    corpus = "\n".join(blobs[f].decode("utf-8", "replace") for f in kept)
    return corpus, len(kept), len(dropped)


def main():
    try:
        # **Batch 197：路径解析收敛到 `beefsrc` 单一来源。**
        # 原先这里判 `isdir(c/".git")`——**在 git worktree 上必然判假**（那里
        # `.git` 是文件），于是用户显式指定的 `BEEFTV_SRC` 被静默忽略、
        # 改用兜底那份，而闸一声不吭。现在改判「能不能当 git 仓用」。
        src, _is_fallback = beefsrc.resolve_src()
        if src is None:
            print("[未能核对] 找不到可用的 BeefTV 源码仓。候选与判真结果：\n"
                  + beefsrc.explain())
            return 2
        # **Batch 202：措辞收敛到 `baseline.announce_fallback()`。**
        # 原先这里手写 `[兜底]` 两行——**它能过方向三之三纯属巧合**：
        # 判据认的是 `[兜底]` 这个字符串，而这里恰好手写了同样的字符串。
        # **判据认标记，就等于认巧合。** 现在这道闸一句名字都不用写，
        # 那道闸自己从调用栈认出自己。
        announce_fallback()
        # 与 verify-label-drift.py 同一写法：`resolve_ref()` **返回 ref 字符串本身**
        # （不是元组——我第一版写成 `resolve_ref()[1]`，取到的是第二个字符 "c"，
        # 于是 git ls-tree 报「Not a valid object name c」）
        ref = os.environ.get("BEEFTV_REF") or resolve_ref()
        corpus, n_kept, n_dropped = load_corpus(src, ref)
    except (RuntimeError, BaselineError, OSError) as exc:
        print("[未能核对] %s" % exc)
        return 2

    # 方向二（自检）：探针必须逐字在上游语料里，否则判据本身不可信
    if PROBE not in corpus:
        print("[未能核对] 自检探针在上游语料里找不到——语料读取或 ref 有问题，"
              "此时判据的「全绿」不可信")
        return 2

    # **归一化比对必须落在「源码里的字符串字面量」上，而不是整份语料上。**
    # 第一版直接归一化整份语料，于是「画布文件夹」这种**由两个词撞出来的**组合
    # 也能在语料里对上（上游某处「画布」后面紧接着出现「文件夹」），
    # 于是一条**根本没有标点可漂移**的纯文字被误报成漂移。
    # 改成先抽出字面量、各自归一化成集合：字面量内部不会出现拼接，
    # 「两词相邻」这种假匹配就不成立了。
    literals = LITERAL_RE.findall(corpus)
    if len(literals) < 1000:
        print("[未能核对] 从语料里只抽到 %d 个字符串字面量——提取规则退化了" % len(literals))
        return 2
    norm_literals = {norm(x) for x in literals}
    print("  语料字符串字面量 %d 个（产品源文件 %d 个，已剔测试文件 %d 个）"
          % (len(literals), n_kept, n_dropped))
    problems = []
    checked = 0
    import glob as _glob
    pages = list(PAGES) + sorted(
        os.path.relpath(x, ROOT) for x in _glob.glob(os.path.join(ROOT, TASK_GLOB)))
    for page in pages:
        p = os.path.join(ROOT, page)
        if not os.path.isfile(p):
            print("[未能核对] 手册里没有 %s" % page)
            return 2
        with open(p, encoding="utf-8") as fh:
            text = fh.read()
        for i, line in enumerate(text.split("\n"), 1):
            for q in QUOTE_RE.findall(line):
                q = re.sub(r"\*\*", "", q).strip()
                # 本手册用 `/` 并列两个独立文案，必须先拆开逐半判定
                for part in (s.strip() for s in SPLIT_RE.split(q)):
                    part = part.strip()
                    if len(part) < 4:
                        continue
                    checked += 1
                    if part in corpus:
                        continue                      # 逐字命中，没问题
                    if norm(part) in norm_literals:
                        problems.append(
                            f"{page} 第 {i} 行：引号文案「{part}」**文字在上游存在、逐字却对不上**"
                            f"——疑似标点漂移，读者拿它和屏幕上的字比对会失败")

    print(f"标点漂移核对：{len(pages)} 个页面、{checked} 段引号文案"
          f"（语料 {len(corpus)} 字符，ref {ref}）")
    if problems:
        for x in problems:
            print("  ✗ %s" % x)
        print(f"标点漂移核对：{len(problems)} 处")
        return 1
    print("标点漂移核对通过：引号文案凡在上游存在的，逐字都对得上")
    return 0


if __name__ == "__main__":
    sys.exit(main())
