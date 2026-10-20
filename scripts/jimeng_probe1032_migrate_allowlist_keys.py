#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""1032-②b-0：**一次性迁移** —— 把白名单标注的键从「行号」换成「稳定键」

⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐⭐
**为什么必须迁移**：白名单标注（生成器源码里的 `NOTES`）原先按 `(文件名, 行号)` 索引。
**行号是位置，不是身份** —— 1021/1030 已经为这件事栽过一次（在上方插一行代码，
那个判据就「消失」了）；这里是**同一个形状的复发**，只是换了个文件。

⇒ ⇒ ⇒ 后果不是「某条判据失效」，而是**全线崩**：改一处代码 ⇒ 所有标注的
`(文件名, 行号)` 全部对不上 ⇒ ⇒ 每一处都被当成「新增糊弄」⇒ ⇒
**⇒ 修按钮的过程本身会一直误报** ⇒ ⇒ ⇒ 25 条按钮根本没法开始修。

⇒ ⇒ ⇒ 处置：键换成**稳定键** `文件#可访问名#同文件同名出现序号`
（序号按源码顺序、对全部按钮计数 ⇒ 文件内唯一）。
**行号仍然保留在条目里**（便于人读与定位），但**不再用来判等**。

⚠️ 这个迁移是**一次性**的，且必须在「代码还没改、行号还没漂」的那一刻做 ——
⇒ ⇒ 所以它现在就跑，而不是等到开始修按钮时（那时已经漂了）。

⚠️ 迁移**不写任何产物**：它改的是**生成器源码里的 `NOTES` 字典**（真源在源码里，
不在白名单 JSON 里 —— 那是产物）。
"""
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GEN = ROOT / "scripts/jimeng_probe1032_build_allowlist.py"
SCAN = ROOT / "docs/research/jimeng-canvas/inputs/interaction-wiring-1032.json"


def load_notes(src):
    """从生成器源码里取出 NOTES 字典（纯字面量 ⇒ literal_eval 可解）。"""
    tree = ast.parse(src)
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
                getattr(t, "id", "") == "NOTES" for t in node.targets):
            return ast.literal_eval(node.value), node
    raise SystemExit("NOTES 找不到（生成器源码变形了）")


def main():
    if not SCAN.exists():
        raise SystemExit("SCAN_MISSING（先跑 jimeng_probe1032_interaction_wiring.mjs）")
    scan = json.loads(SCAN.read_text(encoding="utf-8"))
    dead = scan.get("dead_buttons") or []
    src = GEN.read_text(encoding="utf-8")
    notes, node = load_notes(src)

    # 现状：短名 + 行号 → stable_key
    by_old = {}
    for b in dead:
        short = b["file"].split("src/components/jimeng/")[-1]
        by_old[(short, b["line"])] = b["stable_key"]

    new_notes = {}
    missing = []
    for (short, line), (kind, note) in notes.items():
        sk = by_old.get((short, line))
        if not sk:
            missing.append("%s:%s" % (short, line))
            continue
        new_notes[sk] = (kind, note)

    if missing:
        print("⚠️ 以下标注在现状里找不到对应死按钮（⇒ 代码已变，行号已漂）：")
        for m in missing:
            print("   ", m)
        print("⇒ ⇒ ⇒ 迁移**中止**（不做半截迁移）")
        return 1

    # 生成新的字典字面量文本
    lines = ["NOTES = {"]
    for sk in sorted(new_notes):
        kind, note = new_notes[sk]
        lines.append("    %r: (%r, %r)," % (sk, kind, note))
    lines.append("}")
    new_block = "\n".join(lines)

    old_block = "\n".join(src.split("\n")[node.lineno - 1:node.end_lineno])
    new_src = src.replace(old_block, new_block, 1)
    assert new_src != src, "替换没生效"
    GEN.write_text(new_src, encoding="utf-8")

    print("迁移完成：%d 条标注 ⇒ 键从 (文件名, 行号) 换成稳定键" % len(new_notes))
    print("样例：")
    for sk in sorted(new_notes)[:3]:
        print("   ", sk)
    return 0


if __name__ == "__main__":
    sys.exit(main())
