#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""标签漂移核对闸：同一个 value 在不同界面被叫成不同名字。

背景（Batch 121）：本轮审计连续四次撞上「同一个设置有多个叫法」——
  · Batch 116  视频生成模式：画布叫「首帧/首尾帧」「参考生成」，
               能力配置叫「图生视频」「全模态参考」，任务历史叫「视频局部修改」
               「镜头/运镜调整」「参考音频生成视频」
  · Batch 117  执行策略 strict-assets：风格选择器叫「严格校验」，
               另两处叫「严格阻止」
  · Batch 119  视频设置面板按协议三分派，分组名各不相同
  · Batch 120  图片质量组标题：含 1k/2k/4k 时叫「分辨率」，否则叫「质量」

这不是偶发。产品里有多个文件各自持一份同义枚举表，改一处忘另一处就会漂移。

**本闸要挡的**：新出现的有意分歧没被登记（后人不知道该用哪个名字）。
**本闸不检查的**：
  1. 「哪个名字对不对」——那是产品文案决策，脚本判不了；
  2. 同文件内的多义（不同枚举撞同一个 value 串，如 auto 既是画质自动、
     又是「单镜时长自动」、又是「自动拆分」）——只报**跨文件**的分歧；
  3. 界面上是否真的两处都出现——需要运行时取证，超出静态闸的能力。

已知分歧登记在下方 CLASSIFIED；登记为 REAL 的表示「确实是有意的两套叫法」，
登记为 COINCIDENCE 的表示「不同枚举恰好共用一个 value 串，无需统一」。
两个方向都要查：
  · 出现未登记的新分歧 → 退出码 1，提醒补登记（否则后人会以为已审过）
  · 登记的分歧消失了    → 退出码 1，提醒清理登记（说明上游已收敛）

退出码：0 全部与登记一致；1 有新增或已消失的分歧。
"""

import os
import re
import sys
import subprocess
import beefsrc
from baseline import announce_fallback
from baseline import resolve_ref, BaselineError, baseline_guard
from batchread import read_many


# value -> 分歧定性
CLASSIFIED = {
    # —— REAL：同一概念的有意两套叫法（v1.6.16 实测存在）——
    "inpaint": ("REAL", "画布/能力配置叫「局部修改」，任务历史叫「视频局部修改」"),
    "camera_motion": ("REAL", "画布/能力配置叫「运镜调整」，任务历史叫「镜头/运镜调整」"),
    "audio_to_video": ("REAL", "画布/能力配置叫「音频生视频」，任务历史叫「参考音频生成视频」"),
    "compare_versions": ("REAL", "画布叫「版本对比」，任务历史叫「结果版本对比」"),
    "1:1": ("REAL", "比例：通用面板叫「方形」，创作类型/任务历史叫「1:1 方形」等写法"),
    "16:9": ("REAL", "比例：通用面板叫「横屏」，另有「16:9 横屏」「16:9 · 横屏」等写法"),
    "9:16": ("REAL", "比例：通用面板叫「竖屏」，另有「9:16 竖屏」「9:16 · 竖屏短剧」等写法"),
    "4:3": ("REAL", "比例：Seedance 叫「标准横屏」，另两处直接用「4:3」"),
    "3:4": ("REAL", "比例：Seedance 叫「标准竖屏」，另两处直接用「3:4」"),
    "21:9": ("REAL", "比例：Seedance 叫「宽银幕」，另两处直接用「21:9」"),
    "active": ("REAL", "任务状态：任务页叫「运行中」，状态筛选器叫「进行中」"),

    # —— COINCIDENCE：不同枚举恰好共用一个 value 串，不应统一 ——
    "auto": ("COINCIDENCE", "画质「自动」/「单镜时长自动」/「自动拆分」是三处无关枚举"),
    "all": ("COINCIDENCE", "各列表页的「全部」筛选项，分属不同页面不同筛选维度"),
    "high": ("COINCIDENCE", "画质「高」与人像纹理「高清锐化」无关"),
    "medium": ("COINCIDENCE", "画质「中」与导演台景别「中景」无关"),
    # 注：人像纹理库里的 natural / soft 曾在登记表中，但它们的多义全部发生在
    # canvas-portrait-texture.ts 单文件内部，跨文件过滤会正确排除，故不登记。
    # 保留这条注释是为了不让人再把它们加回来。
    "creative": ("COINCIDENCE", "批量创作表「创意生图」与技能目录「创意设计」无关"),
    "camera": ("COINCIDENCE", "角度弹窗的图源「摄像头」与脚本单元「镜头设计」无关"),
    "standard": ("COINCIDENCE", "角度弹窗「标准」与人像纹理「标准清晰」无关"),
    "wide": ("COINCIDENCE", "导演台景别「广角」与角度弹窗「远景」无关"),
    "reference": ("COINCIDENCE", "素材种类「参考图组」与提示词优化「结合参考」无关"),
    "assets": ("COINCIDENCE", "脚本单元「资产」与工作流「关联资产」无关"),
    "prompt": ("COINCIDENCE", "素材种类「提示词模块」与工作流字段「任务提示词」无关"),
    "size": ("COINCIDENCE", "能力字段名 size 与其界面标签「画面尺寸」本就不是一类"),
    "text": ("COINCIDENCE", "协议类型「文本」与项目导入源「粘贴文本」无关"),
    "video": ("COINCIDENCE", "协议类型「视频」与脚本单元「镜头视频」无关"),
    "5": ("COINCIDENCE", "「5 章」与「每镜 5 秒」是两个不同单位的枚举"),
    "10": ("COINCIDENCE", "「10 章」与「每镜 10 秒」是两个不同单位的枚举"),
}

# value:label —— 两种书写顺序都认
PAIR_RE = re.compile(
    r'value:\s*"([^"]+)"\s*,\s*label:\s*"([^"]+)"'
    r'|label:\s*"([^"]+)"\s*,\s*value:\s*"([^"]+)"'
)


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


@baseline_guard
def main():
    src = find_source()
    if not src:
        print("[skip] 未找到 BeefTV 源码，跳过标签漂移核对")
        return 2
    # 与闸 7 一致：允许用 BEEFTV_REF 指向合成 ref 做反向验证。
    # Batch 167 普查发现本闸是**十道闸里唯一一道完全没有反向验证的**——
    # 而它恰恰是唯一一道 ref 写死、连注入都做不了的。补上这个口子，
    # 闸门的能力才谈得上被验证。
    ref = os.environ.get("BEEFTV_REF") or resolve_ref()

    tree = subprocess.run(["git", "ls-tree", "-r", ref, "--name-only"],
                          cwd=src, capture_output=True, text=True).stdout.split("\n")
    web_files = [f for f in tree if f.startswith("web/src/") and f.endswith((".ts", ".tsx"))]

    labels = {}   # value -> set(label)
    files = {}    # value -> set(文件名)
    # **Batch 182 改**：原先每个 web 文件一次 `git show` 子进程——
    # **实测 754 个 .ts/.tsx**，单次约 25ms → **闸门本体 15.7 秒**
    #（与 Batch 181 治的闸 5/闸 3 是同一种病，只是文件数从 347 涨到 754）。
    # 改成 `batchread.read_many`：**两次进程调用取代 754 次**。
    # 只改读取方式，`PAIR_RE` 与后面的判据逻辑一步没动。
    for f, body in read_many(src, ref, web_files).items():
        s = body.decode("utf-8", "replace")
        if not s:
            continue
        base = f.split("/")[-1]
        for m in PAIR_RE.finditer(s):
            value, label = (m.group(1), m.group(2)) if m.group(1) else (m.group(4), m.group(3))
            labels.setdefault(value, set()).add(label)
            files.setdefault(value, set()).add(base)

    # 只看跨文件分歧：同一文件内的多义不算漂移
    drift = {v: ls for v, ls in labels.items()
             if len(ls) > 1 and len(files[v]) > 1}

    problems = []
    new_drift, vanished = [], []

    for value, ls in sorted(drift.items()):
        if value not in CLASSIFIED:
            new_drift.append((value, sorted(ls), sorted(files[value])))
        elif CLASSIFIED[value][0] == "REAL":
            print(f"  已登记（有意两套叫法）{value}：{' / '.join(sorted(ls))}")
    for value in sorted(set(CLASSIFIED) - set(drift)):
        vanished.append(value)

    for value, ls, fs in new_drift:
        problems.append(f"未登记的跨文件标签分歧 {value}：{' / '.join(ls)}（{', '.join(fs[:3])}）")
    for value in vanished:
        kind, note = CLASSIFIED[value]
        problems.append(f"登记的 {kind} 分歧「{value}」已消失（{note}）——上游可能已统一，请清理登记")

    for p in problems:
        print("  ⚠ " + p)
    if problems:
        print(f"标签漂移核对：{len(problems)} 项需要处理（未登记 {len(new_drift)}，登记已失效 {len(vanished)}）")
        return 1

    real_n = sum(1 for v in drift if CLASSIFIED.get(v, ("",))[0] == "REAL")
    print(f"标签漂移核对：{len(drift)} 项跨文件分歧全部与登记一致"
          f"（{real_n} 项有意两套叫法 / {len(drift) - real_n} 项同值巧合）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
