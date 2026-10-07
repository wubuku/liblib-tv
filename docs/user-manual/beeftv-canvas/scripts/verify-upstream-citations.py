#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第四十七道闸：手册引用的上游文件路径，本身也是**有版本的**——而本手册跨着两个版本。

**为什么要有这道闸（Batch 341 的由来）**：本批把「v1.6.22 为真、v1.7.3 可能已翻面」的
绝对否定断言逐条静态核实，过程中撞见一件手册没写下来的事——
**引用上游文件这件事，本身没有版本**。

手册里这样的引用有形态上的两类：

  · **仓库根起的完整路径**（`web/src/services/api/workspace-assets.ts`）
    ——去重 **16 条**、在发布面上出现 **21 处**、分布在 **4 个页面**；
  · **裸文件名**（`openapi.yaml`、`agent_retired_test.go`、`director-templates.ts`）
    ——去重 **17 个 / 57 处**，**而那 57 处里有 39 处来自 `node_modules`**
    （**本闸第一版量数据用的是 `glob('**/*.md', recursive=True)`，把依赖目录也扫了**——
    见下面「输入为什么是 `published_paths()`」）。

**而本批手工量到的那处坏引用正好落在第二类**：
`10-tasks/asset-library.md` 写「已写进 `openapi.yaml`」，
**而那个文件实际在 `backend/internal/handler/openapi.yaml`**，读者按字面找不到。
本批已把它改成完整路径。

**但本闸只管第一类，这是量过之后定的窄口径（纪律 334）**：

  · **管得了**：`web/` / `backend/` 开头的路径**必须逐字存在于两个 ref 之一**——
    拼错、张冠李戴、指向已删文件，全部抓得到。
  · **管不了**：裸文件名**在任何树上都能按 basename 找到**，
    `openapi.yaml` 确实存在于 `backend/internal/handler/openapi.yaml`——
    **所以「存在即通过」的判据结构上就抓不到它**。
    要抓它只能改成「必须写成仓库根起的完整路径」，
    **而那是 57 处改写、跨 20 个页面**，**收益与本批不相称**。
    **所以这一类留在这里靠人记，并在「本闸不检查什么」里如实标出。**

**实测（`origin/main` = v1.7.3 / `3b4c79a`，基线 = `v1.6.22` / `bcc3b05`）**：
16 条里 **10 条两个版本都有**、**1 条只有基线有**
（`web/src/components/canvas/canvas-creative-interaction.tsx`——
v1.7.3 已把整个文件删掉）、**5 条只有当前版本有**
（`/agents` 那套、`/canvas-folders` 那个后端文件、`/assets` 前端那两个调用）。
**两条方向的判据都成立、且当前手册 0 处不成立**——
**而「今天不报」正是它该有的状态**（纪律 264）：
新闸上线时零差异该做的不是庆祝，是**立刻注入一次看它会不会红**。

**为什么输入是 `scope.published_paths()` 而不是 glob**：
本批第一版量数据时用的是 `glob('**/*.md', recursive=True)`，
**结果 57 条裸引用里有 39 条来自 `node_modules/**/superjson/README.md`**——
**`node_modules` 在工作区里存在，而它是读者看不见的那一面**。
**判据的输入范围必须恰好等于「读者能看见的那一面」**：
`published_paths()` 恰好把三份工程账本与依赖目录一起排除。

**本闸不检查什么**：

  · **不核「点名的版本是不是那个文件所在的那个版本」**——
    只判「这个注记有没有点名一个版本」。
    **判得更紧就得把版本号写死进判据**，而版本号一升版就过期（纪律 371 的同型）。
    **「同一段里说了版本、但说的是另一个版本」这一类靠人记。**
  · **不查裸文件名**（见上）。
  · **不核上游有没有在两个 ref 之间搬家**——
    目录结构的改名不在本闸范围内。

**rc 分三段**：0 一致 / 1 不一致 / 2 未能核对（上游取不到、基线读不出来）。
"""
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import scope                                                            # noqa: E402
from baseline import BaselineError, baseline_guard, resolve_ref      # noqa: E402
from baseline import upstream_tip                                # noqa: E402
from baseline import announce_fallback                                  # noqa: E402
from baseline import SRC as _BEEFSRC                                    # noqa: E402

#: **判据的根从事实源取**（纪律 377 的同型推论，Batch 336 已经栽过一次）：
#: 页面清单来自 `scope.published_paths()`，而 `scope.ROOT` 认 `BEEFTV_MANUAL_ROOT`。
#: **本闸自己那一份根若写成 `os.path.dirname(HERE)`，就会出现
#: 「正文读真手册、清单读夹具」那种夹具树**——而它报绿且输出为真。
ROOT = scope.ROOT

#: **「当前版本」那个 ref 刻意是浮动的，而它必须从事实源解析出来**——
#: 闸 14 的方向四会报「任何闸门把 ref 写死成浮动的 origin/main」，
#: **而那一条本批真的报到了本闸（第一次实跑 rc=1，两处）**。
#: **修法不是登记豁免，是让那个 ref 从 `baseline` 出来**：
#: 本闸问的是「**基线之后上游走了多远，那些引用还成不成立**」，
#: **而那个答案不在基线里**（纪律 107：判据锚的必须是事实，
#: 而「上游顶端现在是什么样」的事实源就是上游顶端）。
#: **同一个理由也让 `verify-shot-version.py` 登记了例外**——
#: **而本闸连例外都不用登记，只需要不把 ref 写成字面量。**
#:
#: **另一处被报的是 `VERSION_RE` 里那个 `origin/main`**：
#: **它不是 ref 解析、只是「正文里出现过的版本写法」之一**，
#: **而它作为判据其实没有必要**——**正文该写的是版本号（v1.7.3），不是 ref 名**：
#: **「这条属于 origin/main」对读者没有回答任何问题，因为 origin/main 会走**。
#: **所以直接删掉，而不是换个写法绕开判据**。

#: **窄口径的那个窄**：只认仓库根起的这两棵子树下的源码文件。
#: 写成正则而不是「凡是带点的反引号」，是因为手册里还有
#: `build-site.sh`、`20-reference.md`、`task-inventory.yml` 这类**本手册自己的文件**，
#: 它们不是上游路径，混进来只会让判据天天误报。
CITATION_RE = re.compile(r"`((?:web|backend)/[A-Za-z0-9_./-]+\.[A-Za-z0-9]+)`")

#: **「这个注记点名了一个版本」的判据**。
#: **只认真版本号**——而 **ref 名不算**（见模块 docstring 那一段的解释：
#: 「这一条属于 origin/main」没有回答读者的问题，因为 origin/main 会走）。
#: **刻意只认形态、不认是哪一个版本**——理由写在模块 docstring 的「不检查什么」里。
#:
#: **⚠️ 裸词「基线」也不算，这是本批反验逼出来的收紧**：
#: 第一版把 `基线` 也收进来，**而反验的语料里有一句「基线上没有这个文件」**——
#: **那是叙述，不是版本声明**，可判据照样放行。
#: **判据一旦认了叙述里最常见的那个词，它在真手册上就会一直绿**，
#: **而它绿着的时候，读者拿到的仍然是「这一条属于哪个版本？」这一句没有答案。**
VERSION_RE = re.compile(r"v\d+\.\d+(?:\.\d+)?")

#: 「注记」= 向上到最近的空行为止。
#: **上限 12 行**：没有上限的话，一条引用可以靠上文很远处的某个版本号过关，
#: **那就不是「这个注记说了版本」，是「这一片里某处说了版本」**。
#: **表格行例外**：表格行之间没有空行，按空行切会把**整张表**当成一个注记，
#: 于是上一行写了版本、这一行没写也会放行——**那一行才是读者真正读的那一行**。
NOTE_WINDOW = 12


def _exists(ref, path):
    """`ref:path` 在上游检出里是否存在。取不到就抛，交给上层记 rc=2。"""
    r = subprocess.run(
        ["git", "-C", _BEEFSRC, "cat-file", "-e", "%s:%s" % (ref, path)],
        capture_output=True,
    )
    if r.returncode not in (0, 128):
        raise RuntimeError("git cat-file 失败（rc=%d）：%s:%s" % (r.returncode, ref, path))
    return r.returncode == 0


def _note_of(lines, idx):
    """引用所在的那个「注记」：**向上向下**到空行为止。

    **为什么必须双向（本批的反验第一次就栽在这）**：第一版只向上扫，
    而真实的写法常常把版本声明**放在证据之后**——
    `20-reference.md` 那两处就是「先甩文件路径，下一行才说『基线 bcc3b05 上这个文件根本不存在』」。
    **只向上扫会把这些全判成「没点名版本」，而它们明明点名了。**
    **而一个判据在真手册上误报，比它漏报更难认**——漏报会在注入时露出来，
    误报只会让人怀疑判据、然后去改对的东西。

    表格行例外：表格行之间没有空行，按空行切会把**整张表**当成一个注记，
    于是上一行写了版本、这一行没写也会放行——**而那一行才是读者真正读的那一行**。
    """
    cur = lines[idx]
    if cur.lstrip().startswith("|"):
        return cur
    lo = hi = idx
    while lo > 0 and (idx - lo + 1) < NOTE_WINDOW and lines[lo - 1].strip():
        lo -= 1
    while hi + 1 < len(lines) and (hi - idx + 1) < NOTE_WINDOW and lines[hi + 1].strip():
        hi += 1
    return "\n".join(lines[lo:hi + 1])


def check(base_ref):
    #: **「当前版本」从 `baseline` 解析，而不是本模块写一个 ref**（见模块 docstring）。
    cur_ref = upstream_tip()
    if not cur_ref:
        #: **这一支没有反验用例**，理由如上：**它要的是上游仓里没有 origin/main**。
        #: rc=2 而不是 rc=1——**「上游读不到」与「手册写错了」必须分开报**。
        print("[skip] 解析不出上游顶端，引用核对本轮未能进行")
        return None, None, 2
    cache = {}

    def exists(ref, path):
        key = (ref, path)
        if key not in cache:
            cache[key] = _exists(ref, path)
        return cache[key]

    problems = []
    notes = []
    n_cites = 0
    n_files = 0
    for rel in scope.published_paths():
        if not rel.endswith(".md"):
            continue
        abs_path = os.path.join(ROOT, rel)
        try:
            with open(abs_path, encoding="utf-8") as fh:
                lines = fh.read().split("\n")
        except OSError as exc:
            print("[skip] 读不到 %s：%s" % (rel, exc))
            return None, None, 2
        hit_file = False
        for i, line in enumerate(lines):
            for m in CITATION_RE.finditer(line):
                hit_file = True
                n_cites += 1
                path = m.group(1)
                in_base = exists(base_ref, path)
                in_cur = exists(cur_ref, path)
                if not in_base and not in_cur:
                    problems.append(
                        "%s:%d  引用的上游文件两个版本里都不存在：%s"
                        "（基线 %s 无 / 当前 %s 无）——**读者按这条路径找不到文件**"
                        % (rel, i + 1, path, base_ref, cur_ref)
                    )
                elif in_base != in_cur:
                    side = "只在基线 %s 有" % base_ref if in_base else "只在当前 %s 有" % cur_ref
                    note = _note_of(lines, i)
                    if not VERSION_RE.search(note):
                        problems.append(
                            "%s:%d  这条引用%s，而这一段没有点名任何版本：%s"
                            "——**读者不知道这条证据说的是哪个版本**"
                            % (rel, i + 1, side, path)
                        )
                    else:
                        notes.append("%s:%d  %s，本段已点名版本"
                                     % (rel, i + 1, side))
        if hit_file:
            n_files += 1
    notes.sort()
    print("上游引用核对：%d 条引用 / 分布在 %d 个页面上（窄口径：只认 web/ 与 backend/ 开头的路径）"
          % (n_cites, n_files))
    print("  落点：基线 %s / 当前 %s" % (base_ref, cur_ref))
    for t in notes:
        print("    · %s" % t)
    if problems:
        print("  ✗ 以下 %d 条不成立：" % len(problems))
        for t in problems:
            print("    · %s" % t)
        return problems, n_cites, 1
    print("  ok 每条引用都能在两个 ref 之一逐字找到；只在一边存在的都在本段点名了版本")
    return [], n_cites, 0


@baseline_guard
def main():
    #: 与闸 40 同一条：**本闸读了上游，就必须把自己读的是哪一份说清楚**，
    #: 否则「核过」与「核的是你指定的那一份」在结果里长得一模一样（纪律 172）。
    announce_fallback()
    if _BEEFSRC is None:
        print("[skip] 未找到 BeefTV 源码，引用核对本轮未能进行")
        return 2
    try:
        #: **基线那一侧必须走 `resolve_ref()`，不能走 `declared_baseline()[1]`**——
        #: **本批实测过两者的差别**：第一版用 `declared_baseline()`，
        #: 设 `BEEFTV_REF` 指向一个不存在的哨兵 ref 之后，**它的输出逐字不变**——
        #: **也就是说它对「基线 ref 换了」毫无反应**，
        #: 而 `scripts/upstream-gates-sentinel.json` 正是靠这个反应把闸分成
        #: 「真读上游 / 未变但对漂移有反应 / 两边都无反应」三类。
        #: **用错 API 会被那份实测表误分类成 C 类（两边都无反应），
        #: 而它明明读上游**——**一份量错了的实测表比没有实测表更坏**（纪律 334 的同型）。
        base_ref = resolve_ref()
    except BaselineError as exc:
        print("[skip] %s，引用核对本轮未能进行" % exc)
        return 2
    try:
        _p, _n, rc = check(base_ref)
    except Exception as exc:                                   # noqa: BLE001
        #: **任何未预料的异常都收 rc=2，不是 rc=1**——
        #: rc=2 才是「未能核对」，rc=1 是「核对不一致」，
        #: **把「判据自己崩了」说成「手册写错了」是最坏的一种报法**。
        print("[skip] 上游引用核对未能完成：%s: %s" % (type(exc).__name__, exc))
        return 2
    return rc


if __name__ == "__main__":
    sys.exit(main())
