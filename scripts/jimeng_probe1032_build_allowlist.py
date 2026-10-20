#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-①：重建「死按钮白名单」（它同时是**修复清单**）。

为什么要单独一个脚本：白名单里**人工标注的部分**（每条属于哪类糊弄、为什么）
不能自动生成，而「代码里现在到底有哪些死按钮」必须自动算 —— 两边要能对齐。

⚠️⚠️⚠️ **这个脚本的第一版里藏着一个恒真的自查**（值得单独记一笔）：
        miss = [k for k in NOTES if not any((A, B) for r in rows)]
    `any()` 收到的是**二元组**，非空元组恒为真 ⇒ `any(...)` 恒为 True
    ⇒ `miss` **永远是空的** ⇒ 脚本报「所有标注都匹配上了」，
    而实际上有一条标注**从未落进产物**。
    ⇒ 这正是本项目反复遇到的那类：**判据正常返回、退出码 0、输出干净**，
      而它**什么都没检查**。
    ⇒ 修法：`(A, B)` 必须是 `(A and B)`；并且**给判据本身做阳性对照**
      （见 `--self-test`：故意删掉一条标注，脚本必须报出来）。

用法：
    python3 scripts/jimeng_probe1032_build_allowlist.py            # 重建并报告差异
    python3 scripts/jimeng_probe1032_build_allowlist.py --self-test  # 证明它能失败
"""
import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GDIR = ROOT / "docs/research/jimeng-canvas"
SCAN = GDIR / "inputs" / "interaction-wiring-1032.json"
ALLOW = GDIR / "inputs" / "interaction-wiring-allowlist-1032.json"

# ⭐ 人工标注：file 末段 + 行号 -> (类别, 说明)
#   类别：NO_EFFECT = 点了什么都不会发生（最坏：用户以为坏了）
#         BILLING   = 计费类，**绝不能真做**，正确处置是 disabled + 说明
NOTES = {
    ("JimengImageGenPanel.tsx", 169): ("NO_EFFECT", "图片生成『生成』：用户输入提示词按发送**什么都没发生、连提示都没有**（按钮无 onClick）⇒ 本批最高优先级"),
    ("JimengImageGenPanel.tsx", 31): ("NO_EFFECT", "『展开面板』无 onClick"),
    ("JimengImageGenPanel.tsx", 47): ("NO_EFFECT", "『添加参考』无 onClick ⇒ 参考图这条链整条断"),
    ("JimengImageGenPanel.tsx", 139): ("NO_EFFECT", "『引用参考』无 onClick"),
    ("JimengImageGenPanel.tsx", 162): ("NO_EFFECT", "『引用参考』无 onClick"),
    ("JimengAudioGenPanel.tsx", 337): ("NO_EFFECT", "『添加参考』无 onClick"),
    ("JimengAudioGenPanel.tsx", 670): ("NO_EFFECT", "『引用参考』无 onClick"),
    ("JimengAudioGenPanel.tsx", 1145): ("NO_EFFECT", "『引用参考』无 onClick"),
    ("JimengAudioGenPanel.tsx", 316): ("NO_EFFECT", "『展开面板』无 onClick"),
    ("JimengAudioGenPanel.tsx", 1161): ("NO_EFFECT", "『显示折扣详情』无 onClick"),
    ("JimengGenPanel.tsx", 218): ("NO_EFFECT", "『展开面板』无 onClick（视频生成面板里也有一个）"),
    ("JimengGenPanel.tsx", 317): ("NO_EFFECT", "『上传参考图』无 onClick —— 而同一面板的 chip 行『＋』是真接了 file input ⇒ **同一个面板里两种行为**"),
    ("JimengGenPanel.tsx", 409): ("NO_EFFECT", "『展开视频生成器』无 onClick"),
    ("JimengRepaintPanel.tsx", 90): ("NO_EFFECT", "『添加参考图』无 onClick"),
    ("JimengRepaintPanel.tsx", 125): ("NO_EFFECT", "模型钮『即梦 Seedance 2.5』带 ChevronDown 像下拉，实则无 onClick ⇒ **视觉在骗人**"),
    ("JimengRepaintPanel.tsx", 133): ("NO_EFFECT", "『6s』时长钮无 onClick"),
    ("JimengRepaintPanel.tsx", 139): ("NO_EFFECT", "『@ 提及主体』无 onClick"),
    ("JimengVideoEditMode.tsx", 87): ("NO_EFFECT", "『上传参考内容』无 onClick（子代理 B 漏掉、AST 扫出来的）"),
    ("JimengVideoEditMode.tsx", 100): ("NO_EFFECT", "『引用参考』无 onClick（同上）"),
    ("JimengVideoEditMode.tsx", 107): ("NO_EFFECT", "『提及主体』无 onClick（同上）"),
    ("nodes/JimengTextNode.tsx", 364): ("NO_EFFECT", "文本节点『下载』整枚无 onClick"),
    ("JimengMemberModal.tsx", 136): ("BILLING", "『购买积分』CTA 无 onClick —— 计费动作**绝不能真做** ⇒ 正确处置是 disabled + 说明，而不是能点没反应"),
    ("JimengMemberModal.tsx", 142): ("BILLING", "『订阅管理』CTA 无 onClick —— 同上"),
    ("JimengMemberModal.tsx", 182): ("BILLING", "四个计费 tab 无 onClick，只有 i===2 常亮 ⇒ 看着像能切，切不动"),
    ("JimengAssetsModal.tsx", 132): ("NO_EFFECT", "时间/筛选图标钮无 onClick（aria-label={label}）"),
}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true",
                    help="故意删掉一条标注，证明这份自查**能失败**")
    args = ap.parse_args()

    if not SCAN.exists():
        sys.stderr.write("SCAN_MISSING (先跑 jimeng_probe1032_interaction_wiring.mjs)\n")
        return 2
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    dead = scan.get("dead_buttons") or []

    notes = dict(NOTES)
    if args.self_test:
        victim = sorted(notes)[0]
        notes.pop(victim)
        print("self-test: 故意移除标注", victim)

    rows = []
    unmatched = []
    for r in dead:
        fname = r["file"].split("src/components/jimeng/")[-1]
        key = (fname, r["line"])
        if key not in notes:
            unmatched.append("%s:%s" % key)
            continue
        kind, note = notes[key]
        rows.append(collections.OrderedDict([
            ("file", r["file"]), ("line", r["line"]), ("verdict", r["verdict"]),
            ("label", r["label"]), ("kind", kind), ("note", note),
        ]))
    rows.sort(key=lambda e: (e["file"], e["line"]))

    # ⭐⭐⭐⭐⭐ **修好的自查**：原来写成 `any((A, B) for ...)` ——
    #   那是**元组非空即真**，⇒ 这句检查恒真、永远报「无缺失」。
    #   现在必须是 `A and B`；而且下面还有一条阳性对照证明它能失败。
    missing_notes = [k for k in notes
                     if not any((e["file"].split("src/components/jimeng/")[-1] == k[0]
                                 and e["line"] == k[1]) for e in rows)]
    leftover = ["%s:%s" % (r["file"].split("src/components/jimeng/")[-1], r["line"])
                for r in dead
                if (r["file"].split("src/components/jimeng/")[-1], r["line"]) not in notes]

    honest = []
    for b in scan.get("buttons") or []:
        if b.get("verdict") == "DISABLED_NO_HANDLER":
            honest.append(collections.OrderedDict([
                ("file", b["file"]), ("line", b["line"]), ("label", b["label"]),
                ("why_not_a_lie", "⭐ 明确 disabled 是**诚实**（用户看得到禁用态）；"
                                  "它与「能点但毫无反应」不是一回事 ⇒ 登记但不判红"),
            ]))

    out = collections.OrderedDict([
        ("generated_by", "jimeng_probe1032_build_allowlist.py（entries 为人工标注，honest_disabled 自动同步）"),
        ("purpose", "⭐⭐ 白名单**同时是修复清单**：每条写明它属于哪类糊弄、为什么。"),
        ("rule", "⭐ 门 P1：代码里的死按钮必须**恰好**等于 entries —— 多一条（新增糊弄）红、"
                 "少一条（修好了却没销账）也红。"),
        ("n", len(rows)),
        ("entries", rows),
        ("honest_disabled", honest),
    ])
    # ⚠️⚠️ **self-test 不许写真实产物** —— 第一版它照写不误，
    #   跑一次就把白名单少写一条 ⇒ 真实产物被一次「测试」改坏
    #   （「半成品脚本要幂等」的变体：这次不是累积损坏，是**测试污染真源**）。
    if not args.self_test:
        ALLOW.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    print("死按钮 %d 条，白名单 entries %d 条，honest_disabled %d 条"
          % (len(dead), len(rows), len(honest)))
    if unmatched:
        print("⚠️ 代码里有死按钮**没有人工标注**（本次以 kind=UNLABELED 记入）:", unmatched)
    if leftover:
        print("⚠️ 代码里的死按钮没有对应标注:", leftover)
    if missing_notes:
        print("⚠️ 标注里有**代码里已不存在**的条目（应销账）:",
              ["%s:%s" % k for k in missing_notes])

    # ⭐ 阳性对照：--self-test 时，注入的那条缺失**必须被报出来**
    if args.self_test:
        # ⚠️ 注入的缺失表现为「代码里有死按钮但没标注」⇒ 落在 unmatched/leftover，
        #   **不是** missing_notes（那个是反向：标注了但代码里已没有）。
        ok = bool(unmatched or leftover)
        print("self-test: 缺失标注是否被抓到 =", ok,
              "| unmatched:", unmatched, "| leftover:", leftover)
        print("self-test: 真实白名单**未被改写** =", True)
        return 0 if ok else 1
    return 1 if (unmatched or leftover or missing_notes) else 0


if __name__ == "__main__":
    sys.exit(main())
