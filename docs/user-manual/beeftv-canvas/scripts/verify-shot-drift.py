#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第二十三道闸：截图**布局漂移**核对（Batch 189 新增）。

背景：67 张截图里 64 张拍于 v1.6.14，而取证基线是 v1.6.22。闸 10 只核「截图上的**文案**
是否还在上游」、闸 16 只核「**版本**有没有登记」——**布局、控件增减这两类变化两类闸都核不到**，
而 Batch 178 早已把这记成手册与基线之间最大的一处已知落差。Batch 188 把它量了出来，
本批把它变成常驻守卫。

**判据的形状是被三级收窄逼出来的，不是一开始就想好的**（命中率都实测过）：

  ① 「截图的文案是否落在**改过的文件**里」→ 命中 **32/67（48%）**，**毫无用处**：
     「画布」出现在 542 处、「视频」749 处，任何一次大重构都会命中。
  ② 换成「含该文案的**整行源码**在两版之间是否变了」→ 12/67。
  ③ 再按**区分度**加权、并**跳过注释行** → **3 处**：
       31-director-templates.png 「选择镜头模板」：弹窗已在 v1.6.22 整个删除
       33-director-workbench.png 「3D导演台」：顶栏只改布局（Batch 188 逐行核实过）
       36-pose-panel.png 「姿势预设」：单选态逐字未变，**新增了多选「混合」态**
     而 Batch 188 那个假阳性（`摄像机检查器`，变的只是一行注释）**被「跳过注释行」清掉了**。

**所以本闸核的问句不是「这个界面变了吗」，而是「拍摄时那一行源码，在基线里还逐字存在吗」**：
一行 JSX 仍然逐字存在，就说明那个元素**渲染出来的东西没变**——
哪怕同文件里新增了另一个变体（`36-pose-panel` 正是这种情况，而它**不算漂移**）。
这比「有没有变过的行」准得多：**新增不等于改旧**。

三个方向：

  · 方向一：每张截图的**区分度 ≤ `DISTINCT_MAX` 的非注释源码行**，必须在基线树里仍逐字存在；
    不存在的**必须**登记在 `DRIFT` 里（附理由）。
  · 方向二：`DRIFT` 每条必须**仍然漂移**（反向检查，防止登记过期成免死金牌）、
    **对应的截图仍被手册引用**、且**引用处紧邻有就地说明**。
    **「紧邻」是硬要求**——纪律 121 的原话是「全页出现该版本号不算数，读者未必读到那里」，
    **而全页搜恰好会让这条判据恒真**。
  · 方向三：**自检探针**。拿一条**必须能在两棵树里都逐字找到**的已知文案当探针；
    找不到就 rc=2「未能核对」——**不能让判据在语料读空时安静地全绿**
    （纪律 101：解析器退化必须表现为失败，而不是通过）。

输入范围：只核 `screenshots/manifest.yml` 里登记了 `visible_text` 的截图；
**动态拼接的文案（源码里根本没有）天然落在方向一之外**，它们由闸 10 的免检表管。

退出码：0 无未登记的漂移且登记全部有效；1 有未登记漂移或登记失效；2 未能核对。
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import beefsrc
from baseline import resolve_ref, BaselineError   # noqa: E402
from batchread import read_many                    # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")

# 「区分度」上限：一个文案在拍摄时那棵树里出现在**多于这么多个**不同的非注释行上，
# 就当它是常见词，任何一次重构都会命中——**粗信号只能用来决定要不要继续，不能下结论**。
# 取 10 是实测定的：收紧到 10 之后命中从 12 掉到 3，而那 3 条逐条都能解释。
DISTINCT_MAX = 10

# 已知布局漂移登记表。**每条都必须写清「变的是什么」与「什么时候查到的」**——
# 免检表一旦靠「我记得它其实也还好」维持，就等于给判据开后门（Batch 135 的教训）。
DRIFT = {
    "31-director-templates.png":
        "弹窗组件 canvas-director-template-modal.tsx 在 v1.6.22 被整个删除"
        "（Batch 178 升版时闸 10 抓到「选择镜头模板」这一行已不存在）。"
        "图保留是为了说明「以前长什么样」，引用处有就地说明。",
    "33-director-workbench.png":
        "导演台顶栏只改布局、不改文案：标题元素从 min-w-0 flex-1 truncate 变成 shrink-0"
        "（不再截断）、标题右侧新增 aria-live 保存状态指示器、其右侧新增"
        "「展开/折叠场景面板」按钮（Batch 188 逐行比对两版源码确认）。",
    "36-pose-panel.png":
        "「姿势预设」的单选态那一行逐字未变；v1.6.22 **新增了多选形态**，"
        "同时选中多个对象时该栏右侧显示「混合」而非某一个姿势名。"
        "图中拍的是单选，所以看不到这个差异（Batch 189 确认）。",
}

# 方向三的自检探针：一条**两棵树里都逐字存在**的源码行片段。
# 取 director-basics.md 之外的公共组件里的一行，确保它与任何具体截图无关。
PROBE = ("<div className=\"min-h-full\" aria-label=\"摄像机检查器")

# 紧邻说明的判定：**图片嵌入行**（`![…](…png)`）之后 8 行内出现「>」引用块开头。
# 为什么用「嵌入」而不是「提到」：判据要在**读者页**里找，而 AUDIT / PROGRESS 里
# 引用这张图的地方（那里也有 `>` 引用块）会让判据恒真——**这正是纪律 121 说的那个错**。
NOTE_WINDOW = 8
# 内部资料不参与「就地说明」的查找：读者不会去 AUDIT.md 里找一张截图的版本说明。
INTERNAL_DOCS = {"AUDIT.md", "PROGRESS.md", "AUDIT-RULES.md", "FINAL-REPORT.md",
                "SOURCE_OBSERVATIONS.md"}

REC_RE = re.compile(
    r"- file: (\S+)(.*?)(?=\n  - file:|\Z)", re.S)


def norm_lines(blobs):
    return {p: {x.strip() for x in b.decode("utf-8", "replace").split("\n")}
            for p, b in blobs.items()}


def is_comment(s):
    s = s.strip()
    return (s.startswith("//") or s.startswith("*") or s.startswith("/*")
            or s.startswith("*/") or s.startswith("#"))


def parse_manifest():
    """→ [(截图名, 拍摄版本, 文案片段列表)]"""
    with open(MANIFEST, encoding="utf-8") as fh:
        text = fh.read()
    out = []
    for fn, body in REC_RE.findall(text):
        mv = re.search(r"captured_version:\s*'?([^'\n]+)'?", body)
        mt = re.search(r"visible_text:\s*'([^']*)'", body)
        if not mv or not mt:
            continue
        frags = [x.strip() for x in mt.group(1).split(" / ") if len(x.strip()) >= 2]
        if frags:
            out.append((os.path.basename(fn), mv.group(1).strip(), frags))
    return out


def main():
    try:
        # **Batch 197：路径解析收敛到 `beefsrc` 单一来源。**
        # 原先这里判 `isdir(c/".git")`——**在 git worktree 上必然判假**（那里
        # `.git` 是文件），于是用户显式指定的 `BEEFTV_SRC` 被静默忽略、
        # 改用兜底那份，而闸一声不吭。现在改判「能不能当 git 仓用」。
        src, is_fallback = beefsrc.resolve_src()
        if src is None:
            print("[未能核对] 找不到可用的 BeefTV 源码仓。候选与判真结果：\n"
                  + beefsrc.explain())
            return 2
        if is_fallback:
            print("[兜底] 未采用 BEEFTV_SRC 指定的路径（它不是一个 git 检出），"
                  "改用候选表里的 %s" % src)
        base = resolve_ref()
    except (OSError, BaselineError) as exc:
        print("[未能核对] %s" % exc)
        return 2

    try:
        shots = parse_manifest()
    except OSError as exc:
        print("[未能核对] 读不到 manifest：%s" % exc)
        return 2
    if not shots:
        print("[未能核对] manifest 里解析出 0 张带 visible_text 的截图——解析规则退化了")
        return 2

    import subprocess

    def load(ref):
        r = subprocess.run(["git", "ls-tree", "-r", "--name-only", ref],
                           cwd=src, capture_output=True, text=True)
        if r.returncode != 0:
            raise RuntimeError("git ls-tree %s 失败：%s" % (ref, (r.stderr or "").strip()[:120]))
        fs = [f for f in r.stdout.split("\n")
              if f.startswith("web/src") and f.endswith((".ts", ".tsx"))]
        if not fs:
            raise RuntimeError("%s 下按扩展名筛出 0 个源文件" % ref)
        return norm_lines(read_many(src, ref, fs))

    # 按拍摄版本分组，只为用到的版本各读一棵树
    versions = sorted({v for _, v, _ in shots})
    trees = {}
    for v in versions:
        r = subprocess.run(["git", "rev-parse", "--verify", "--quiet", v + "^{commit}"],
                           cwd=src, capture_output=True, text=True)
        if r.returncode != 0:
            print("[未能核对] 截图登记的拍摄版本 %s 在上游没有对应 tag——"
                  "**版本号写错或 tag 被删，本闸无法核对那一批**" % v)
            return 2
        trees[v] = load(r.stdout.strip())
        if not any(len(ls) > 100 for ls in trees[v].values()):
            print("[未能核对] %s 那棵树读回来几乎是空的——语料读取退化了" % v)
            return 2
    try:
        base_tree = load(base)
    except RuntimeError as exc:
        print("[未能核对] %s" % exc)
        return 2

    # 方向三：自检探针只核**基线那棵树**——它才决定结论。
    # **不核旧树**：旧树的内容本来就与基线不同（第一版把探针也拿去核 v1.6.0，
    # 于是判据因为「那条 aria-label 还没被加进去」而 rc=2——那是自检探针选错了对象）。
    if not any(PROBE in l for ls in base_tree.values() for l in ls):
        print("[未能核对] 自检探针在基线树里找不到——语料读取或 ref 有问题，"
              "此时判据的「全绿」不可信")
        return 2

    problems = []
    found = {}
    for name, ver, frags in shots:
        old_tree = trees[ver]
        for frag in frags:
            # **必须按 (文件, 行) 实际出现的位置逐对检查。**
            # 第一版写成了 `for p, ls in old_tree.items() for l in lines`——
            # 那个内层循环**不检查 l 是否真在 ls 里**，于是等于要求每一行
            # 在全部 754 个文件里都存活，**67 张里 50 张被误报**。
            hits = [(p, l) for p, ls in old_tree.items() for l in ls
                    if frag in l and not is_comment(l)]
            if not hits:
                continue
            if len({l for _, l in hits}) > DISTINCT_MAX:
                continue
            lost = [(p, l) for p, l in hits if l not in base_tree.get(p, set())]
            if lost:
                found.setdefault(name, []).append(frag)

    for name in sorted(found):
        if name not in DRIFT:
            problems.append(
                f"方向一：{name} 的截图文案 {found[name]} 在基线里**已找不到那一行源码**"
                f"——这属于布局漂移，**要么就地说明这张图偏旧，要么登记进 DRIFT**")
    for name, why in sorted(DRIFT.items()):
        if name not in found:
            problems.append(
                f"方向二：DRIFT 里的 {name} **已经不漂移了**（基线里那一行又回来了）"
                f"——登记过期，请删掉并撤掉它的就地说明")
        shot = os.path.join(ROOT, "screenshots", name)
        if not os.path.isfile(shot):
            problems.append(f"方向二：DRIFT 里的 {name} 对应的截图文件不存在")

    # 方向二之二：就地说明必须**紧邻**图片引用（全页搜会让它恒真）
    md = {}
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames
                       if d not in (".git", "node_modules", ".vitepress", "dist")]
        for fn in filenames:
            if fn.endswith(".md"):
                p = os.path.join(dirpath, fn)
                with open(p, encoding="utf-8") as fh:
                    md[p] = fh.read().split("\n")
    for name in sorted(DRIFT):
        # **只认「图片嵌入」那一行**（`![…](…name.png)`），且**只在读者页里找**。
        # 第一版写的是「任何提到这个文件名的行」，于是 AUDIT / PROGRESS 里
        # 引用这张图的地方（那里当然也有 `>` 引用块）把判据**恒真**了——
        # **反验用例 3/5 首跑就抓到它**，两道都该报错却报 0。
        # **纪律 121 说的是「紧邻该图」，而「该图」是那个 `![](…)`，不是「提到它的任何一行」。**
        cands = []
        for p, ls in md.items():
            if os.path.basename(p) in INTERNAL_DOCS:
                continue
            for i, l in enumerate(ls):
                if ("![" in l) and (name in l):
                    cands.append((p, i))
        if not cands:
            problems.append(f"方向二：DRIFT 里的 {name} **没有任何读者页面嵌入这张图**")
            continue
        ok = any(any(md[p][j].lstrip().startswith(">")
                     for j in range(i + 1, min(i + 1 + NOTE_WINDOW, len(md[p]))))
                 for p, i in cands)
        if not ok:
            problems.append(
                f"方向二：{name} 的引用处**紧邻 {NOTE_WINDOW} 行内没有引用块（就地说明）**"
                f"——**全页搜版本号不算数，读者未必读到那里**")

    print(f"截图布局漂移核对：{len(shots)} 张截图、{len(versions)} 个拍摄版本"
          f"（{'/'.join(versions)} → {base}），区分度上限 {DISTINCT_MAX}")
    print(f"  检出漂移 {len(found)} 张；DRIFT 登记 {len(DRIFT)} 条")
    if problems:
        for x in problems:
            print("  ✗ %s" % x)
        print(f"截图布局漂移核对：{len(problems)} 处问题")
        return 1
    print("截图布局漂移核对通过：未登记的漂移 0 条，登记的 %d 条全部仍有效且就地说明齐备"
          % len(DRIFT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
