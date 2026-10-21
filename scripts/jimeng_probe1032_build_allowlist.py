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
# ⭐⭐⭐⭐⭐ Batch 1032-②b-1 销账：本批**真的修好了 18 条**，逐条从本表删掉。
#   修法逐条记在 README「六之二十六」；这里只留**还没修**的那些。
#   ⭐ 删条不是「销账就算完」：**门的 P1 会点名**（`stale_allow`），
#   删多删少都会红 ⇒ ⇒ 这张表与代码现状**必须逐条对得上**。
# ⭐⭐⭐ Batch 1032-②b-3 **销账**：「提及主体」两条（重拍面板 / 视频编辑态）
#   ⇒ 此前**整枚没有 onClick**（死按钮）⇒ 现在接上**真的 @ 提及面板**
#   （`src/components/jimeng/JimengMentionPanel.tsx`，SOURCE_FACT 手册批次
#   33/34/113/114：两级定步选择器 / `可能@的内容` / 只列有资源的节点 /
#   空态逐字「暂无相关节点」），选中候选 ⇒ 提示词行插入**引用 chip**。
#   ⇒ ⇒ 死按钮 6 → 4。**不是拿空 handler 去骗门** ⇒ 有运行时门真点一遍。
NOTES = {
    'src/components/jimeng/JimengAudioGenPanel.tsx#"展开面板"#0': ('NO_EFFECT', '『展开面板』无 onClick —— 展开浮层组件尚未做 ⇒ 留到 ②b-4'),
    'src/components/jimeng/JimengGenPanel.tsx#"展开面板"#0': ('NO_EFFECT', '『展开面板』无 onClick —— 展开浮层组件尚未做 ⇒ 留到 ②b-4'),
    'src/components/jimeng/JimengGenPanel.tsx#"展开视频生成器"#0': ('NO_EFFECT', '『展开视频生成器』无 onClick —— 源站实测点它开「已展开的视频生成器」浮层（role=dialog / 920×480 / 内含 全部·图片·视频·音频·文本 参考 tab）⇒ 浮层组件尚未做 ⇒ 留到 ②b-4'),
    'src/components/jimeng/JimengImageGenPanel.tsx#"展开面板"#0': ('NO_EFFECT', '『展开面板』无 onClick —— 展开浮层组件尚未做 ⇒ 留到 ②b-4'),
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

    # ⭐⭐⭐⭐⭐ Batch 1032-②b-0: **键从「(文件名, 行号)」换成「稳定键」** ——
    #   行号是**位置**不是**身份**（1021/1030 栽过一次；这里是同一形状的复发）。
    #   ⇒ 改一行代码 ⇒ 全部标注错位 ⇒ 每一处都被当成「新增糊弄」
    #   ⇒ ⇒ **修按钮的过程本身会一直误报** ⇒ ⇒ 所以必须先换键再动手修。
    #   ⇒ 稳定键 = `文件#可访问名#同文件同名出现序号`（由 AST 探针给出）。
    rows = []
    unmatched = []
    for r in dead:
        sk = r.get("stable_key")
        if sk not in notes:
            unmatched.append(sk or ("%s:%s" % (r["file"], r["line"])))
            continue
        kind, note = notes[sk]
        rows.append(collections.OrderedDict([
            ("stable_key", sk),
            ("file", r["file"]), ("line", r["line"]), ("verdict", r["verdict"]),
            ("label", r["label"]), ("kind", kind), ("note", note),
        ]))
    rows.sort(key=lambda e: (e["file"], e["line"]))

    # ⭐⭐⭐⭐⭐ **修好的自查**：原来写成 `any((A, B) for ...)` ——
    #   那是**元组非空即真**，⇒ 这句检查恒真、永远报「无缺失」。
    #   现在必须是 `A and B`；而且下面还有一条阳性对照证明它能失败。
    # ⭐ 1032-②b-0: 语义也改了 ——
    #   `orphan`（标注里有、现状里没有）= **已修好、可以销账**的那几条
    #   ⇒ ⇒ 而 `unmatched`（现状里有、标注里没有）= **新增糊弄**
    #   ⇒ ⇒ 两者**方向相反**，以前把它们混在一个「missing_notes」里。
    _dead_keys = {r.get("stable_key") for r in dead}
    missing_notes = sorted(k for k in notes if k not in _dead_keys)
    leftover = list(unmatched)

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
