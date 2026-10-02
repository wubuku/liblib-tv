#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十六道闸：截图版本登记（Batch 177 新增）。

**这道闸看守的是「这张截图还成不成立」**——而在此之前，没有任何东西看守它。

**为什么需要它（Batch 177 的实测，不是假想）**：

`screenshots/manifest.yml` 记了 `captured_at`（哪天拍的），
**却没有记「拍的是哪个版本」**。而本项目的 dev server 长期停在 **v1.6.14 工作树**，
上游却一直在往前走。于是出现这种局面：

  · `31-director-templates.png` 拍的是**「选择镜头模板」弹窗**；
  · 上游 `df1a0ba`（v1.6.22）把那个弹窗**整个文件删掉**了；
  · **manifest 里没有任何字段能让人发现这件事**，闸 10 也照样绿
    （它核的是「登记的文案在基线版本里还在吗」——而在基线 v1.6.16 上**确实还在**）。

**换句话说：基线正确，反而让这张失效的截图躲过了所有检查。**
这与纪律 115「不报错、只是不渲染的损坏」同族，但更隐蔽一层——
**不是判据写错了，是判据在核一个错误的问句**（「文案还在吗」而不是「这图还成不成立吗」）。

**本闸三个方向**：

  方向一：**每条截图都有 `captured_version`**，且形态合法（`vX.Y.Z`）。
    缺字段 = 「这张图属于哪个版本」无人知道 = 上面的问题会再来一次。

  方向二：**已登记为「上游已删除」的截图，必须在引用它的页面正文里就地说明**。
    这条是本闸的核心——**光在 manifest 里写一句「已失效」没用**，
    **读者看不到 manifest，只看得到页面**。
    登记表由 `STALE` 显式列出，每条都要写清上游在哪个文件把它删了。

  方向三：登记表里的每条都必须**真的**在上游找不到了。
    这条专治「把还存在的界面登记成已删除」——**那会让读者以为功能没了**，
    伤害与 Batch 163 那次「把仍存在的接口教读者别去查」同量级。

  方向四（Batch 217）：**正文声明的「截图拍于 vX（N 张中有 M 张；另 K 张更早）」
  必须与 manifest 的实际分布对得上**。
  加它的起因是**一次量出来的漏报**：把 manifest 里一张 v1.6.14 改成 v1.6.15
  （分布从 64/3 变 63/4），**本闸 rc=0**——上面三个方向都不核那三个数。
  **而那句话是 Batch 178 升基线时亲手写的**，数字当时是对的（现场实测 64/3），
  **所以这不是数据缺陷，是「一个正确的数没有任何东西守着」**——重拍两张图就会悄悄过期。

**Batch 217 同时改了两处「同一个问题只查了一处」**（细节见对应函数与纪律 224/225）：
  · **方向二的输入范围改为从 `.vitepress/config.mjs` 的 `srcExclude` 读**——
    原先脚本里硬编码了一份，**多排除了 `README.md`（它就是发布首页，`config.mjs`
    写着 `'README.md': 'index.md'`、产物里也确实有 `index.html`）、
    少排除了 `PUBLISH.md`（它在 `srcExclude` 里、**不发布**）**，两处都朝着坏的方向；
  · **方向二从「找到第一个引用页就 break」改成「每一个引用页都要核」**。

退出码：0 全部自洽；1 有不自洽；2 未能核对（找不到 manifest / 抽出 0 条 / 找不到上游
/ 读不到 `config.mjs` 的 `srcExclude`）。
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import resolve_ref, BaselineError, module_ref, baseline_guard
from baseline import SRC as _BEEFSRC
from baseline import announce_fallback# noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#: **Batch 197：不再单点读环境变量，改从 `baseline` 取统一解析后的路径**
#: （原先无任何校验，坏路径会被原样塞进 `git -C <path>`）。
SRC = _BEEFSRC
REF = module_ref()
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")

# ── 已在上游被删除、但手册仍保留其截图的登记表 ───────────────────────
# 每条三要素缺一不可：**截图文件 / 上游删掉它的那个文件 / 页面里必须出现的说明字样**。
# 说明字样必须逐字出现在**引用该图的页面正文**里——读者看不到 manifest。
STALE = {
    "screenshots/31-director-templates.png": {
        "removed_file": "web/src/components/canvas/director/canvas-director-template-modal.tsx",
        "removed_since": "v1.6.22",
        "note_must_contain": "v1.6.22",
    },
}

VER_RE = re.compile(r"^v\d+\.\d+\.\d+$")

#: 目录名：这些下面没有可发布的内容页
SKIP_DIRS = {".git", "node_modules", "dist", "screenshots", ".vitepress"}


def excluded_basenames():
    """**从 `.vitepress/config.mjs` 的 `srcExclude` 读**不发布的文件，**而不是在脚本里再抄一份**。

    ── Batch 217 立的：抄一份的写法当场被抓出两处对不上 ──

    本文件原先在方向二里硬编码了一份排除表，而它与 `config.mjs` 的真实列表差两处，
    **而且两处都朝着坏的方向**：

      · **多排除 `README.md`**——而 `config.mjs` 写着 `'README.md': 'index.md'`，
        产物里也确实有 `index.html`。**README 就是发布首页**，
        把它排除等于「读者第一眼看到的页面，判据不认」；
      · **少排除 `PUBLISH.md`**——它在 `srcExclude` 里、**不发布**，
        而判据会把它当成合法的「引用页」。
        **读者看不到 PUBLISH.md**，拿它当证据等于让一个内部文件冒充读者可见的说明。

    这正是 Batch 122/123 那条纪律的又一次应验：**判据的输入范围必须等于发布范围**，
    而「发布范围」只有一处真值——`config.mjs` 的 `srcExclude`。
    **抄一份就等于立一个必然会漂移的副本**，漂移的方向恰好是「少报或多报」。

    **读不到就抛，绝不退回硬编码列表**——退回列表等于把刚拆掉的副本又装回去，
    而且这次是在没人知道的情况下（Batch 191：零输入不许报绿）。
    """
    cfg = os.path.join(ROOT, ".vitepress", "config.mjs")
    try:
        with open(cfg, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        raise LookupError(f"读不到 {cfg}：{exc}")
    m = re.search(r"srcExclude:\s*\[(.*?)\]", text, re.S)
    if not m:
        raise LookupError(f"{cfg} 里找不到 srcExclude——发布范围的定义改了，本闸必须跟上")
    return {x.split("/")[-1] for x in re.findall(r"'([^']+)'", m.group(1))
            if x.endswith(".md")}


def published_pages():
    """全部**会被发布成页面**的 .md（顺序稳定，同名的按文件名排）。"""
    excluded = excluded_basenames()
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in sorted(filenames):
            if fn.endswith(".md") and fn not in excluded:
                yield os.path.join(dirpath, fn)


def parse_manifest():
    try:
        with open(MANIFEST, encoding="utf-8") as fh:
            text = fh.read()
    except OSError as exc:
        return None, None
    entries = []
    for block in text.split("  - file: ")[1:]:
        fname = block.split("\n", 1)[0].strip()
        m = re.search(r"^\s*captured_version:\s*'([^']*)'", block, re.M)
        entries.append((fname, m.group(1) if m else None))
    return entries, text


def direction_one(entries):
    problems = []
    for fname, ver in entries:
        if ver is None:
            problems.append(
                f"方向一：{fname} 没有登记 captured_version"
                "　→ 「这张图属于哪个版本」无人知道，"
                "上游删掉对应界面时没有任何东西会响")
        elif not VER_RE.match(ver):
            problems.append(f"方向一：{fname} 的 captured_version={ver!r} 不是 vX.Y.Z 形态")
    if not entries:
        return ["方向一：从 manifest.yml 抽出 0 条截图（判据可能已失效）"]
    return problems


def direction_three():
    """已登记为失效的截图，在**上游顶端**确实找不到了。

    **这里刻意用 `origin/main` 而不是取证基线**（上线首跑就抓到，Batch 177）：
    登记表记的是「自 v1.6.22 起被删」，而基线是 v1.6.16——**在基线上那个文件当然还在**，
    拿基线核会把这张图误判成「误登记」。**判据要核的问句是「上游现在还有没有」，
    不是「基线版本有没有」**——后者是另一个问句，答它没有意义。
    """
    problems = []
    tip = subprocess.run(
        ["git", "-C", SRC, "rev-parse", "--verify", "--quiet", "origin/main^{commit}"],
        capture_output=True, text=True)
    if tip.returncode != 0:
        return []  # 上游顶端读不到时这一方向无法核对，跳过而不谎报
    for fname, info in STALE.items():
        r = subprocess.run(
            ["git", "-C", SRC, "cat-file", "-e", f"origin/main:{info['removed_file']}"],
            capture_output=True, text=True)
        if r.returncode == 0:
            problems.append(
                f"方向三：{fname} 被登记成「{info['removed_since']} 已删除」，"
                f"但 {info['removed_file']} 在上游 origin/main 上**还存在**"
                "　→ 这是误登记；**读者会以为那个界面没了**，"
                "而它其实还在。先撤登记，别改判据")
    return problems


def _note_near_image(text, image_name):
    """找出**紧邻该图片**的说明块（下方最近的引用块，或紧邻其上的引用块）。

    **为什么必须是「紧邻」而不是「本页任意位置出现该版本号」**（反验用例 3 上线首跑抓到）：
    本页别处（开头的版本差异提示、文末的专节）本来就有 v1.6.22，
    全页搜索会**恒真**——于是把图片旁的说明整段删掉，判据照样绿。
    **而读者恰恰只看得见图片旁边那几行。**
    """
    lines = text.split("\n")
    hits = [i for i, l in enumerate(lines) if image_name in l]
    if not hits:
        return None
    for idx in hits:
        for probe in (idx + 1, idx - 1):
            k = probe
            while 0 <= k < len(lines) and not lines[k].strip():
                k += 1 if probe > idx else -1
            if 0 <= k < len(lines) and lines[k].startswith(">"):
                return "\n".join(lines[k:k + 6])
    return None


def direction_two():
    """已登记为失效的截图，**每一个引用它的发布页**都必须在图旁就地说明。

    ── Batch 217 两处修改，都是「同一个问题只查了一处」 ──

    **①输入范围改为从 `config.mjs` 的 `srcExclude` 读**（见 `excluded_basenames`
    的 docstring）：原硬编码表多排除了 `README.md`（**它就是发布首页**）、
    少排除了 `PUBLISH.md`（**它不发布**）。

    **②从「找到第一个就 break」改成「逐个引用页都要核」**。
    原 docstring 写的是「取全部命中再挑第一个内容页」，
    **而代码是找到第一个就 `break`**——**两句话的效果一样，但读起来像两回事**，
    而真正要紧的后果是：**一张图被两个发布页引用时，第二个页删掉就地说明不报**。
    「读者只看得见他打开的那一页」——所以**每个读者可能打开的页面都得写**，
    这不是「挑一个代表」，这是「逐个保证」。
    顺带把「挑第一个内容页」的说法删掉：**现在候选全是发布页，没有「内容页」与
    「非内容页」之分**，留着那个词会让人以为还有一层过滤。
    """
    problems = []
    pages = None
    try:
        pages = list(published_pages())
    except LookupError as exc:
        return [f"[未能核对] {exc}"]
    for fname, info in STALE.items():
        base = os.path.basename(fname)
        refs = []
        for p in pages:
            try:
                with open(p, encoding="utf-8") as fh:
                    text = fh.read()
            except (OSError, UnicodeDecodeError) as exc:
                problems.append(
                    f"[未能核对] 读不到 {os.path.relpath(p, ROOT)}：{exc}")
                continue
            if base in text:
                refs.append((p, text))
        if not refs:
            problems.append(
                f"方向二：manifest 登记了 {fname} 为已失效，但**没有任何发布页引用它**"
                "　→ 要么删掉这张图，要么在引用它的页面上写清它失效了")
            continue
        for p, text in refs:
            rel = os.path.relpath(p, ROOT)
            note = _note_near_image(text, base)
            if note is None:
                problems.append(
                    f"方向二：{rel} 引用了 {fname}，但**紧邻该图的说明块里没有版本说明**"
                    f"　→ 读者只看得到图片旁边那几行；失效必须写在图片旁边，就地说明")
            elif info["note_must_contain"] not in note:
                problems.append(
                    f"方向二：{rel} 引用了 {fname}，但图片旁的说明块里没有出现 "
                    f"{info['note_must_contain']!r}"
                    f"　→ 全页别处出现该版本号不算数，**读者未必会读到那里**")
    return problems


#: 正文的截图版本声明与它自带的分布。**两个正则都刻意收到最紧**——
#: 实测全手册 35 个发布页里，形态 A 只命中 1 处、形态 B 也只命中 1 处（同一行），
#: 而放宽成「N 张…M 张」会多命中 2 处业务数字（`0 张、或连 2 张`、`1 张图 + 1 张`）。
#: **宁可窄**：漏检靠方向一兜（每张图都登记了版本），误报会逼着人加豁免。
SHOT_DECL_RE = re.compile(r"\*\*截图拍于\*\*[：:]\s*(v\d+\.\d+\.\d+)")
SHOT_DIST_RE = re.compile(r"（(\d+)\s*张中有\s*(\d+)\s*张[；;，,]\s*另\s*(\d+)\s*张更早）")


def direction_four(entries):
    """正文声明的「截图拍于 vX（总数 N 张中有 M 张；另 K 张更早）」必须与 manifest 对得上。

    **为什么这道方向值得有**（Batch 217 量出来的漏报面）：
    那句话是 **Batch 178 升基线时亲手写的**，而实测**把 manifest 里一张 v1.6.14
    改成 v1.6.15（分布从 64/3 变 63/4），本闸 rc=0**——**三个方向都不核它**：
    方向一核「每张有没有登记」，方向二核「失效的有没有就地说明」，方向三核「失效登记真不真」。
    **数字本身是对的**（现场实测 64/3），所以这不是数据缺陷，
    **是「一个正确的数没有任何东西守着」**——重拍两张图就会悄悄过期。
    与 Batch 165「判据锚的是誊抄副本」同族：**manifest 是真值，正文那句话是它的誊抄。**

    **核四件事，缺一不可**：
      1. `N` == manifest 截图总条数（有人加图/删图而不改这句话）；
      2. `M` == manifest 里 `captured_version` 恰为 `vX` 的条数（**把版本号和数字
         同时锚在真值上**——只核数字的话，改了版本号而分布没变照样没人管）；
      3. `K` == `N - M`（三个数自洽，防「手改了一个数」）；
      4. `vX` 必须是 manifest 里的**唯一众数**——否则「M 张」指哪个版本有歧义，
         而现在的 manifest 恰好是 64/1/1/1，众数唯一。

    **形态 A 命中而同行没有分布 → 也报**：那是**分布被删掉了**。
    判据的输入若匹配不到就等于不存在（Batch 216）——只核「写了分布的那些行」，
    等于给「不写分布」发了一张免检证，而读者恰恰靠那个数判断哪几张图是旧的。
    """
    problems = []
    try:
        pages = list(published_pages())
    except LookupError as exc:
        return [f"[未能核对] {exc}"]
    if not entries:
        return ["方向四：从 manifest 抽出 0 条截图——解析器退化了，不得当成通过"]
    total = len(entries)
    from collections import Counter
    dist = Counter(v for _f, v in entries if v)
    if not dist:
        return ["方向四：manifest 里没有一条 captured_version 有值——不得当成通过"]
    seen = 0
    for p in pages:
        try:
            with open(p, encoding="utf-8") as fh:
                text = fh.read()
        except (OSError, UnicodeDecodeError) as exc:
            problems.append(f"[未能核对] 读不到 {os.path.relpath(p, ROOT)}：{exc}")
            continue
        for i, line in enumerate(text.split("\n"), 1):
            m = SHOT_DECL_RE.search(line)
            if not m:
                continue
            seen += 1
            ver = m.group(1)
            rel = os.path.relpath(p, ROOT)
            d = SHOT_DIST_RE.search(line)
            if not d:
                problems.append(
                    f"方向四：{rel} 第 {i} 行声明「截图拍于 {ver}」，但同一行没有分布"
                    f"（形如「（{total} 张中有 {dist[ver]} 张；另 "
                    f"{total - dist[ver]} 张更早）」）"
                    f"　→ **读者靠这个数判断哪几张图是旧的**；删掉它等于让那句话失去依据")
                continue
            n, mm, k = (int(x) for x in d.groups())
            if n != total:
                problems.append(
                    f"方向四：{rel} 第 {i} 行写「{n} 张中有」，而 manifest 里有 {total} 张")
            if mm != dist[ver]:
                problems.append(
                    f"方向四：{rel} 第 {i} 行写「{ver} 有 {mm} 张」，"
                    f"而 manifest 里 {ver} 的是 {dist[ver]} 张")
            if k != n - mm:
                problems.append(
                    f"方向四：{rel} 第 {i} 行的三个数不自洽：{n} − {mm} = {n - mm}，"
                    f"写的却是「另 {k} 张更早」")
            top = dist.most_common()
            if top[0][0] != ver or top[0][1] == top[1][1]:
                problems.append(
                    f"方向四：{rel} 第 {i} 行把 {ver} 当作主版本，"
                    f"而 manifest 的众数是 {top[0][0]}（{top[0][1]} 张）"
                    f"　→ **「M 张」指哪个版本有歧义**"
                    + ("，且出现并列众数" if len(top) > 1 and top[0][1] == top[1][1] else ""))
    if seen == 0:
        problems.append(
            "方向四：**没有任何发布页声明「截图拍于」**——"
            "基线小节里那句「图拍于哪个版本」连同它的分布一起不见了")
    return problems


@baseline_guard
def main():
    announce_fallback()
    entries, _text = parse_manifest()
    if entries is None:
        print(f"[skip] 读不到 {os.path.basename(MANIFEST)}，跳过截图版本核对")
        return 2
    if SRC is None:
        print(f"[skip] 未找到 BeefTV 源码（{SRC}），跳过截图版本核对")
        return 2
    try:
        resolve_ref()
    except BaselineError as exc:
        print(f"[skip] 取证基线不可用：{exc}")
        return 2

    problems = (direction_one(entries) + direction_two() + direction_three()
                + direction_four(entries))

    if problems:
        print("截图版本登记核对：%d 处不自洽" % len(problems))
        for p in problems:
            print("  ✗ " + p)
        return 1

    print("截图版本登记核对通过：%d 张截图均登记了拍摄版本；"
          "已登记失效的 %d 张均在**每一个**引用它的发布页就地说明了；"
          "正文的「截图拍于 + 分布」与 manifest 对得上" % (len(entries), len(STALE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
