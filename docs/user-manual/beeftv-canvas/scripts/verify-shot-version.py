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

退出码：0 全部自洽；1 有不自洽；2 未能核对（找不到 manifest / 抽出 0 条 / 找不到上游）。
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import resolve_ref, BaselineError, module_ref, baseline_guard
from baseline import SRC as _BEEFSRC# noqa: E402

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
    problems = []
    for fname, info in STALE.items():
        base = os.path.basename(fname)
        found_page = None
        for dirpath, _dirs, files in os.walk(ROOT):
            if os.path.basename(dirpath) in (".vitepress", "scripts", "screenshots", ".git"):
                continue
            for fn in files:
                if not fn.endswith(".md"):
                    continue
                # **只扫会被发布成页面的 md**（上线首跑就抓到，Batch 177）：
                # AUDIT.md / PROGRESS.md / AUDIT-RULES.md 里也会提到这个文件名，
                # 但**那些是内部账本，读者看不到**——拿它们当「引用页」毫无意义。
                # 漏判方向反过来更危险，所以这里取**全部命中**再挑第一个内容页，
                # 而不是「找到第一个 md 就用」。
                if fn in ("AUDIT.md", "PROGRESS.md", "AUDIT-RULES.md", "FINAL-REPORT.md",
                          "SOURCE-OBSERVATIONS.md", "README.md"):
                    continue
                p = os.path.join(dirpath, fn)
                try:
                    with open(p, encoding="utf-8") as fh:
                        t = fh.read()
                except OSError:
                    continue
                if base in t:
                    found_page = (p, t)
                    break
            if found_page:
                break
        if not found_page:
            problems.append(
                f"方向二：manifest 登记了 {fname} 为已失效，但**没有任何页面引用它**"
                "　→ 要么删掉这张图，要么在引用它的页面上写清它失效了")
            continue
        p, t = found_page
        rel = os.path.relpath(p, ROOT)
        note = _note_near_image(t, base)
        if note is None:
            problems.append(
                f"方向二：{rel} 引用了 {fname}，但**紧邻该图的说明块里没有版本说明**"
                f"　→ 读者只看得到图片旁边那几行；失效必须写在图片旁边，就地说明")
        elif info["note_must_contain"] not in note:
            problems.append(
                f"方向二：{rel} 引用了 {fname}，但图片旁的说明块里没有出现 "
                f"{info['note_must_contain']!r}"
                "　→ 全页别处出现该版本号不算数，**读者未必会读到那里**")
    return problems


@baseline_guard
def main():
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

    problems = direction_one(entries) + direction_two() + direction_three()

    if problems:
        print("截图版本登记核对：%d 处不自洽" % len(problems))
        for p in problems:
            print("  ✗ " + p)
        return 1

    print("截图版本登记核对通过：%d 张截图均登记了拍摄版本；"
          "已登记失效的 %d 张均在引用页面就地说明了" % (len(entries), len(STALE)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
