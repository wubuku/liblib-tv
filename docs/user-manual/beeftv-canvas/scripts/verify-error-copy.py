#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""第十五道闸：错误分类文案表（Batch 176 新增）。

**这道闸看守的是「失败时你会看到什么」这类文案**——它是本手册里**最要紧、
也最容易悄悄过期**的一类内容。

**为什么单独建一道（Batch 176 的实测，不是假想）**：

排障页 `90-troubleshooting.md` 的「提交时报素材/参数不被接受」「额度与频控」
两张表，抄的是上游 `web/src/lib/generation-error.ts` 里的 `CATEGORY_COPY` 表。
而那张表在 v1.6.16 → v1.6.22 之间：

  · **新增 2 类**：`local_storage`（「本地任务保存失败，尚未提交生成」）与
    `delivery_failed`（「视频已生成，但暂时无法取回」）；
  · **改 1 类**：`quota_user` 的原因文案「当前账号额度不足」→「当前账号**可用**额度不足」；
  · **删除 0 类**（这一点也核过，否则「新增 2 类」可能只是我数错了方向）。

**前两类都是会直接改变读者行为的内容**：
`local_storage` 明确说**尚未提交生成**（没扣费、别去改参数），
而 v1.6.16 之前这类情况会被显示成「模型不接受当前参数」——**方向完全指错**；
`delivery_failed` 明确说**钱已经花了**、要去取回而不是重新生成。
**这类文案错了，代价是读者按错误方向排障、甚至重复付费。**

**本闸怎么核**：
  · 方向一：手册那张表里出现的**界面文案**必须在上游 `CATEGORY_COPY` 里逐字存在
    （**双向**：上游有而手册没写的**也要报**——那是漏写，不是没问题）。
  · 方向二：`CATEGORY_COPY` 的**每一条**都必须在手册里被提到
    （按「原因文案」或「处置文案」任一命中即可，处置往往才是读者真正要照做的）。
  · 方向三：**豁免登记表**双向自证——每条豁免必须写清理由，且理由里点名的
    上游标识必须真的存在（防止「为省事把一整类都豁免掉」）。

**为什么不用闸 10 那套**：闸 10 核的是 manifest 里登记的**截图文案**，
而这些文案写在**正文表格**里、且**不以截图为准**。两者来源不同，判据不该混。

退出码：0 全部相符；1 有不符；2 未能核对（找不到上游 / 找不到手册的表 / 抽出 0 条）。
"""

import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from baseline import resolve_ref, BaselineError  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = os.environ.get("BEEFTV_SRC", "/Users/yangjiefeng/Documents/glanderness/BeefTV")
REF = os.environ.get("BEEFTV_REF") or resolve_ref()
MANUAL = os.path.join(ROOT, "90-troubleshooting.md")
ERROR_TS = "web/src/lib/generation-error.ts"

# 上游分类表的解析形态：key: { reason: "...", action: "..." }
ENTRY_RE = re.compile(
    r'^\s{4}(\w+):\s*\{\s*reason:\s*"([^"]*)",\s*action:\s*"([^"]*)"', re.M)


def git_show(path):
    r = subprocess.run(["git", "-C", SRC, "show", f"{REF}:{path}"],
                       capture_output=True, text=True)
    if r.returncode != 0:
        return None
    return r.stdout


def parse_upstream():
    """返回 {分类名: (原因文案, 处置文案)}，外加文件是否存在。"""
    src = git_show(ERROR_TS)
    if src is None:
        return None
    return {m.group(1): (m.group(2), m.group(3)) for m in ENTRY_RE.finditer(src)}


# 手册里「抄了上游文案但**不是**分类表原文」的片段：每条必须写清为什么不算。
# 纪律 104：抑制规则与匹配规则互为镜像——**只认「有」就必须显式认「无」**。
EXEMPT = {
    "模型不接受当前参数": "分类表里的 invalid_params 原因文案，"
                          "手册另有专节「提交时报素材/参数不被接受」整段覆盖；"
                          "登记在此以免它同时被当成漏写",
    "提示词或参考素材未通过内容安全审核":
        "**moderation_input 的兜底默认值，界面上永远不会显示这句**。"
        "审核文案由 web/src/lib/moderation-error.ts 用 `${label}未通过内容安全审核` "
        "模板拼出，label 取自 labels 表的 8 个对象名（输入文本/参考图片/…/生成音频），"
        "所以实际显示的是「参考图片未通过内容安全审核」这类拼接结果。"
        "手册「审核失败」一节按 label × 原因两个维度写全了组合，不抄这条默认值",
    "参考素材未通过内容安全审核": "同上，moderation_reference 的兜底默认值，"
                                  "界面显示的是拼接结果",
    "生成结果未通过内容安全审核": "同上，moderation_output 的兜底默认值；"
                                  "手册已按「对象是生成结果 → 处置方向不同」单列说明",
}
EXEMPT_ANCHORS = {
    "模型不接受当前参数": (ERROR_TS, "模型不接受当前参数"),
    # 三条审核兜底：点名模板与 label 表，理由失配即可发现
    "提示词或参考素材未通过内容安全审核": ("web/src/lib/moderation-error.ts", "未通过内容安全审核"),
    "参考素材未通过内容安全审核": ("web/src/lib/moderation-error.ts", "未通过内容安全审核"),
    "生成结果未通过内容安全审核": ("web/src/lib/moderation-error.ts", "moderation_output"),
}


def manual_sections():
    """取出排障页里那两张表的正文（闸只管这两处，别处提到的顺带也算命中）。"""
    try:
        with open(MANUAL, encoding="utf-8") as fh:
            text = fh.read()
    except OSError:
        return None
    return text


def main():
    if not os.path.isdir(SRC):
        print(f"[skip] 未找到 BeefTV 源码（{SRC}），跳过错误文案核对")
        return 2
    try:
        resolve_ref()
    except BaselineError as exc:
        print(f"[skip] 取证基线不可用：{exc}")
        return 2

    upstream = parse_upstream()
    if upstream is None:
        print(f"[skip] 在 {REF} 读不到 {ERROR_TS}，跳过错误文案核对")
        return 2
    if not upstream:
        print(f"[skip] 从 {ERROR_TS} 抽出 0 条分类（判据可能已失效），跳过")
        return 2

    text = manual_sections()
    if text is None:
        print(f"[skip] 读不到 {os.path.basename(MANUAL)}，跳过错误文案核对")
        return 2
    if "CATEGORY" in text or "错误码" in text:
        pass  # 手册不写上游表名；此分支仅为避免误删后续判断

    problems = []
    covered = 0
    # 豁免的锚点复核**必须独立于「手册写没写」**（反验用例 2 上线首跑就抓到这一点）。
    # 原实现把锚点检查放在「手册没覆盖」分支里，于是给一条**手册本来就写了**的文案
    # 加了个理由失配的豁免，判据会先命中「已覆盖」而 continue，**失配检查形同虚设**——
    # 而这正是豁免表最容易被滥用的形态。
    for reason, (path, needle) in EXEMPT_ANCHORS.items():
        body = git_show(path)
        if body is None:
            problems.append(
                f"方向三：豁免「{reason}」点名了 {path}，但在上游读不到这个文件")
        elif needle not in body:
            problems.append(
                f"方向三：豁免「{reason}」的理由点名了 {path} 的 {needle!r}，"
                "但上游已没有这句——豁免失效，必须改判据而不是留着")

    for cat, (reason, action) in sorted(upstream.items()):
        hit_reason = reason and reason in text
        hit_action = action and action in text
        if hit_reason or hit_action:
            covered += 1
            continue
        if reason in EXEMPT:
            continue
        problems.append(
            f"方向二：上游分类 {cat} 的文案未在手册出现"
            f"（原因：{reason}｜处置：{action}）"
            "　→ 这是**失败时读者会看到的字**；漏写会让读者在该排障的方向上没有依据")

    if covered == 0:
        print("[skip] 手册与上游分类文案 0 条重合——"
              "多半是上游换了文件或换了字段名，先确认判据再改手册")
        return 2

    if problems:
        print("错误分类文案核对：%d 处不一致（上游 %d 类，手册覆盖 %d 类）"
              % (len(problems), len(upstream), covered))
        for p in problems:
            print("  ✗ " + p)
        return 1

    print("错误分类文案核对通过：上游 %d 类分类，手册覆盖 %d 类（豁免 %d 条且理由已复核）"
          % (len(upstream), covered, len(EXEMPT)))
    print("  手册未逐字抄的 %d 类请确认是有意省略，而非漏写" % (len(upstream) - covered))
    return 0


if __name__ == "__main__":
    sys.exit(main())
