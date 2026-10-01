#!/usr/bin/env python3
"""第十道闸：截图取证文案 ⇄ 上游源码（Batch 162 新建）。

## 它关的是覆盖度表 C 类的哪一条

`AUDIT-RULES.md` 的覆盖度表里，「截图内容是否仍对得上界面」原被记为
「无人覆盖，且**不可机械覆盖**」。本闸**部分**关掉了这一条：

- **能核的**：`screenshots/manifest.yml` 每条记录的 `visible_text` / `alt` 里
  **录下来的界面文案**，是否仍能在上游 `web/src` 找到。**这一项 Batch 161 查实
  是「误指派」——`verify-meta.py` 声明把它让给了 `verify-screenshots.py`，
  而后者只做四方对账、零内容判据。**
- **核不了的**：PNG **像素里画的**是什么。本闸读的是 manifest 的文本登记，
  **不是图像内容**；截图与界面的真正一致性仍取决于重拍。

## 为什么 Batch 150 判「不可建」的同一件事这里能建

Batch 150 试建「界面文案逐字对账」时，抽取的是正文里**任意**「」包裹的短串，
信噪比 54% → 70% → 34，**剩下的全是噪音**，于是如实记「不该建」。

本闸的对象完全不同：`visible_text` 是**为取证而专门记录的字段**，
它的语义就是「这张图上看到的字」。**判据能落在形态上，是因为数据的用途本身就是确定的。**

## 判据口径（实测得出，不是拍的）

对每条 `visible_text` 按 ` / ` 拆成片段，只检查**保守形态**的片段：
长度 ≥ 4、无 ASCII 字母数字、无空白。实测 164 个唯一片段 → 筛出 77 个。

**为什么必须收窄**：不收窄时 60 个片段查不到，其中绝大多数是
**动态计数**（`全部 0`）、**运行时生成名**（`S83-jing2.mp4`）、或
**两条界面文案的拼接**（`从参考图开始 上传风格图，生成同风格画面`）。
**那会是 60 条稳定误报**——误报会让人开始忽略闸门输出，闸门就废了
（Batch 150 判「不可建」用的正是同一条理由）。

收窄后 **77 条里 73 条命中、4 条未命中，且 4 条全部可归因**（见 EXEMPT）。
"""
import os
import re
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("BEEFTV_SRC", "/Users/yangjiefeng/Documents/glanderness/BeefTV")
REF = os.environ.get("BEEFTV_REF", "origin/main")
MANIFEST = os.path.join(ROOT, "screenshots", "manifest.yml")

# 保守形态：长度 ≥ 4、无 ASCII 字母数字、无空白
KEEP = re.compile(r"^[^A-Za-z0-9\s]{4,}$")

# 免检登记表：每一格都必须写清「为什么它不是界面文案」。
# **这是本闸唯一允许漏报的地方，且每条都有实测归因**（Batch 162）。
EXEMPT = {
    "产品片头": "走查时创建的**片段内容名**，不是界面文案；全库 0 命中，"
               "「片头」只出现在 backend/internal/skills/seed/skills.json（技能种子，非界面）",
    "更改时保存到本地工作区": "**两条界面文案的拼接**；上游真实文案是「正在保存到本地」"
                             "（canvas/index.tsx、assets/index.tsx 的 toast）",
    "空镜收集": "**跨组件拼接**：画风「空镜」（canvas-style-picker-modal.tsx / "
               "canvas-style-system.ts）+ 分类「收集」（canvas-resource-references.ts）",
    "音频-新片段": "走查时创建的**片段名**（音频 + 新片段）；「新片段」见 "
                  "canvas-timeline-dialog.tsx",
}


def fragments(path):
    """从 manifest 抽出 (片段, 所属文件) 列表。"""
    text = open(path, encoding="utf-8").read()
    recs = re.findall(r"-\s+file:\s*(\S+)(.*?)(?=\n\s*-\s+file:|\Z)", text, re.S)
    out = []
    for fname, body in recs:
        m = re.search(r"visible_text:\s*'([^']*)'", body)
        if not m:
            continue
        for part in m.group(1).split(" / "):
            part = part.strip()
            if len(part) >= 2:
                out.append((part, os.path.basename(fname)))
    return out


def in_source(text):
    r = subprocess.run(["git", "grep", "-q", "-F", text, REF, "--", "web/src"],
                       cwd=SRC, capture_output=True, text=True)
    if r.returncode >= 128:
        raise RuntimeError("git grep 失败：%s" % (r.stderr or "").strip()[:160])
    return r.returncode == 0


def main():
    if not os.path.isfile(MANIFEST):
        print("截图取证文案核对：未找到 manifest，跳过")
        return 2
    if not os.path.isdir(SRC):
        print("截图取证文案核对：未找到 BeefTV 源码，无法核对")
        return 2
    try:
        pairs = fragments(MANIFEST)
    except Exception as exc:
        print("截图取证文案核对：解析 manifest 失败：%s" % exc)
        return 1

    uniq = sorted({p for p, _ in pairs})
    checked = [p for p in uniq if KEEP.match(p)]
    problems, exempt_used = [], set()
    for frag in checked:
        if frag in EXEMPT:
            exempt_used.add(frag)
            continue
        if not in_source(frag):
            problems.append(frag)

    for frag in problems:
        print("  ✗ 「%s」：manifest 登记为截图上可见的文案，但上游 %s 的 web/src 里已找不到"
              % (frag, REF))
    # 登记表里已不再需要的条目（上游把动态名变成 UI 文案了）——留着就是过期豁免
    for frag in sorted(set(EXEMPT) - exempt_used):
        print("  ✗ 豁免登记「%s」已无对应片段——上游可能已把它变成正式界面文案，请核实后移除"
              % frag)
        problems.append(frag)

    n_skipped = len(uniq) - len(checked)
    if problems:
        print("截图取证文案核对：%d 处需处理（检查 %d 个保守片段、免检 %d 条；"
              "另有 %d 个动态/拼接片段按形态不检查）"
              % (len(problems), len(checked), len(exempt_used), n_skipped))
        return 1
    print("截图取证文案核对：%d 个保守形态片段全部在上游存在（免检 %d 条已登记，"
          "%d 个动态/拼接片段按形态不检查）" % (len(checked), len(exempt_used), n_skipped))
    return 0


if __name__ == "__main__":
    sys.exit(main())
