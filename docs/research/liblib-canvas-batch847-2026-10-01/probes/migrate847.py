#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""batch 847：**第七次迁移** —— 把 840／841／842／843 四条门禁与四个探针里的
「**仍未实现的那一段**」断言**换靶**。

## 为什么必须换靶

★ 「断言要盯**当前状态**」：每实现一段，「仍未实现的那一块」就往后挪一位。
batch 846 做完了左列**第四段**「服装造型」⟹ ⟹ 只剩**第五段**「音色音调」。

★★ **batch 847 做完了第五段** ⟹ ⟹ **左列五段全部实现**
⟹ ⟹ 「**仍未实现的那一段**」这个靶子**第一次用完** ⟹ ⟹
⟹ ⟹ 四条旧门禁的断言**照原样跑必然红** ⟹ ⟹ 必须**换靶**。

## 换成的靶子（★ 四条各盯**一枚不同的入口**）

★ 「**未实测的控件只显示如实说明、不编造控件**」这条**纪律没有变**
⟹ ⟹ 只是改由**更细的粒度**承载（★ 页面级，而不是段级）：

| 门禁 | 新靶子 | 入口 |
| --- | --- | --- |
| `840` | 第五段 →「**我的音色**」 | `[data-character-editor-voice-tab="mine"]` |
| `841` | 第五段 →「**AI 生成**」 | `[data-character-editor-voice-tab="ai"]` |
| `842` | 第四段 →「**服装**」 | `[data-character-editor-outfit-tab="clothes"]` |
| `843` | 第四段 →「**AI 生成**」 | `[data-character-editor-outfit-tab="ai"]` |

★ 四条**互不重叠**（★ 四枚不同的按钮 ⟹ ⟹ 读的是四个不同的页面状态）。

## 期望值怎么变（★ 语义换了 ⟹ ⟹ 期望值必须跟着换）

★ 段级那条说明写的是「**已实测**（raw 已入库）⟹ ⟹ 属后续批次」——
⟹ ⟹ 因为**整段**都测过，只是**没实现**。
★ 而**页面级**那四枚的内容是**根本就没测过** ⟹ ⟹ 说明**必须**写「**未实测**」
⟹ ⟹ 所以 840／841／842 的「写了『已实测』」这条期望 ⟹ ⟹ **翻成**
「写了『未实测』」＋「**没有**写『已实测』」。

★ 换句话说：★ **期望值不是随手改的** ⟹ ⟹ 它跟着**语义**走
⟹ ⟹ 「这一页的内容测过没有」⟹ ⟹ 这正是 clone 该如实说明的那件事。

## 改了什么（**逐处精确替换** ⟹ ⟹ 不用正则乱扫）

| 文件 | 改动 |
| --- | --- |
| `clone840.py` | 点完第五段后**再点「我的音色」**；读数键 `F2_第五段` → `F2_第五段_我的音色` |
| `clone841.py` | 同上，点「AI 生成」；`C2_第五段` → `C2_第五段_AI生成` |
| `clone842.py` | 段改成**第四段（服装造型）** ＋ 点「服装」；`D2_第五段` → `D2_第四段_服装` |
| `clone843.py` | 同上，点「AI 生成」；`D_第五段` → `D_第四段_AI生成` |
| `verify-liblib-batch840.py` | 读新键；期望「已实测」→「未实测」；S7 措辞 |
| `verify-liblib-batch841.py` | 同上（且**多**一条「没有写『已实测』」） |
| `verify-liblib-batch842.py` | 同上 |
| `verify-liblib-batch843.py` | 读新键；S6 措辞 |

★ 迁移完必须**四个门禁全绿**（840 7/7、841 6/6、842 7/7、843 7/7）
⟹ ⟹ 否则说明「迁移」把别的东西改坏了。

## 用法

    python3 migrate847.py --dry-run   # 只核对锚点，**不写文件**
    python3 migrate847.py             # 真正改（并**逐处**校验唯一命中）
"""
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[4]

P840 = "docs/research/liblib-canvas-batch840-2026-10-01/probes/clone840.py"
P841 = "docs/research/liblib-canvas-batch841-2026-10-01/probes/clone841.py"
P842 = "docs/research/liblib-canvas-batch842-2026-10-01/probes/clone842.py"
P843 = "docs/research/liblib-canvas-batch843-2026-10-01/probes/clone843.py"
G840 = "scripts/verify-liblib-batch840.py"
G841 = "scripts/verify-liblib-batch841.py"
G842 = "scripts/verify-liblib-batch842.py"
G843 = "scripts/verify-liblib-batch843.py"

# ★★ 每一项都是 (相对路径, [(旧串, 新串), ...]) ⟹ ⟹ **必须唯一命中**
EDITS = [
    # ── clone840.py：第五段 → 再点「我的音色」──
    (P840, [
        ('            # ★★ **batch 846 起**：点左列**第五段**（音色音调）⟹ **页签行应当消失**\n'
         '            #   （★ 846 起第四段「服装造型」已实现 ⟹ ⟹ 未实现的又挪了一位）\n'
         '            #   ⟹ ⟹ 那是**当下仍未实现**的那一块（源站实测有内容 ⟹ ⟹ clone 显示空态说明）\n',
         '            # ★★ **batch 847 起**：左列五段**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了**\n'
         '            #   ⟹ ⟹ 这条断言**换靶**：盯**第五段里那一页内容未实测的页签**（「我的音色」）\n'
         '            #   ⟹ ⟹ ★ 「音色库」那一页**已实现**（20 条音色 ⟹ batch 847）⟹ ⟹ 不再是空态\n'),
        ('            pg.wait_for_timeout(400)\n'
         '            out["F2_第五段"] = pg.evaluate(READ)\n',
         '            pg.wait_for_timeout(400)\n'
         '            # ★ 再点第五段的「我的音色」页签（★ 那一页的控件**源站未实测** ⟹ ⟹ 应显示如实说明）\n'
         '            pg.evaluate("""() => {\n'
         '              const t=document.querySelector(\'[data-character-editor-voice-tab="mine"]\');\n'
         '              if(t)t.click();}""")\n'
         '            pg.wait_for_timeout(400)\n'
         '            out["F2_第五段_我的音色"] = pg.evaluate(READ)\n'),
    ]),
    # ── clone841.py：第五段 → 再点「AI 生成」──
    (P841, [
        ('            # ★★ **batch 846 起**：点左列**第五段**（音色音调）⟹\n'
         '            #   **页签行应当消失**（源站实测：页签行只在「脸部精修」段存在）⟹ ⟹\n'
         '            #   那是**当下仍未实现**的那一块 ⟹ ⟹ 显示**如实说明**而不编造控件\n',
         '            # ★★ **batch 847 起**：左列五段**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了**\n'
         '            #   ⟹ ⟹ 这条断言**换靶**：盯**第五段里那一页内容未实测的页签**（「AI 生成」）\n'
         '            #   ⟹ ⟹ ★ 「音色库」那一页**已实现**（20 条音色 ⟹ batch 847）⟹ ⟹ 不再是空态\n'),
        ('            out["C2_第五段"] = pg.evaluate(READ)\n',
         '            # ★ 再点第五段的「AI 生成」页签（★ 那一页的控件**源站未实测** ⟹ ⟹ 应显示如实说明）\n'
         '            pg.evaluate("""() => {\n'
         '              const t=document.querySelector(\'[data-character-editor-voice-tab="ai"]\');\n'
         '              if(t)t.click();}""")\n'
         '            pg.wait_for_timeout(400)\n'
         '            out["C2_第五段_AI生成"] = pg.evaluate(READ)\n'),
    ]),
    # ── clone842.py：改成第四段 → 再点「服装」──
    (P842, [
        ('            # ★★ **batch 846 起**：点左列**第五段**（音色音调）⟹\n'
         '            #   **页签行应当消失**（源站实测：页签行只在「脸部精修」段存在）⟹ ⟹\n'
         '            #   那是**当下仍未实现**的那一块 ⟹ ⟹ 显示**如实说明**而不编造控件\n',
         '            # ★★ **batch 847 起**：左列五段**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了**\n'
         '            #   ⟹ ⟹ 这条断言**换靶**：盯**第四段里那一页内容未实测的子页签**（「服装」）\n'
         '            #   ⟹ ⟹ ★ 「造型」那一页**已实现**（batch 846）⟹ ⟹ 不再是空态\n'),
        ("              const e=document.querySelector('[data-character-editor-segment=\"voice\"]');\n"
         "              if(!e)return null; const r=e.getBoundingClientRect();\n"
         "              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),\n"
         "                      h:Math.round(r.height)};}\"\"\")\n"
         "            out[\"★点到_第五段\"] = seg2\n",
         "              const e=document.querySelector('[data-character-editor-segment=\"outfit\"]');\n"
         "              if(!e)return null; const r=e.getBoundingClientRect();\n"
         "              return {x:Math.round(r.x),y:Math.round(r.y),w:Math.round(r.width),\n"
         "                      h:Math.round(r.height)};}\"\"\")\n"
         "            out[\"★点到_第四段\"] = seg2\n"),
        ('            out["D2_第五段"] = pg.evaluate(READ)\n',
         '            # ★ 再点第四段的「服装」子页签（★ 那一页的控件**源站未实测** ⟹ ⟹ 应显示如实说明）\n'
         '            pg.evaluate("""() => {\n'
         '              const t=document.querySelector(\'[data-character-editor-outfit-tab="clothes"]\');\n'
         '              if(t)t.click();}""")\n'
         '            pg.wait_for_timeout(400)\n'
         '            out["D2_第四段_服装"] = pg.evaluate(READ)\n'),
    ]),
    # ── clone843.py：改成第四段 → 再点「AI 生成」──
    (P843, [
        ('            # ★ 点左列**第五段**（音色音调）⟹ **页签行应当消失** ＋ 出现空态说明\n'
         '            #   （★ 846 起第四段已实现 ⟹ ⟹ 「仍未实现的那一段」又挪了一位）\n'
         '            out["★点到_第五段"] = click_box(pg,\n'
         "                                           '[data-character-editor-segment=\"voice\"]')\n"
         '            out["D_第五段"] = pg.evaluate(READ)\n',
         '            # ★★ **batch 847 起**：左列五段**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了**\n'
         '            #   ⟹ ⟹ 这条断言**换靶**：盯**第四段里那一页内容未测量的子页签**（「AI 生成」）\n'
         '            out["★点到_第四段"] = click_box(pg,\n'
         "                                           '[data-character-editor-segment=\"outfit\"]')\n"
         '            # ★ 再点第四段的「AI 生成」子页签（★ 那一页的控件**源站未实测** ⟹ ⟹ 应显示如实说明）\n'
         '            out["★点到_服装AI生成"] = click_box(pg,\n'
         "                                             '[data-character-editor-outfit-tab=\"ai\"]')\n"
         '            out["D_第四段_AI生成"] = pg.evaluate(READ)\n'),
    ]),
    # ── verify-liblib-batch840.py ──
    (G840, [
        ('    after_seg5 = rt.get("F2_第五段") or {}',
         '    after_seg5 = rt.get("F2_第五段_我的音色") or {}'),
        ('    # ★★ **batch 846 起**：分段选中态转移的「点后」读数取自 **F2_第五段**',
         '    # ★★ **batch 847 起**：分段选中态转移的「点后」读数取自 **F2_第五段_我的音色**'),
        ('        "★第五段_空态说明里写了「已实测」": bool(seg5_empty and "已实测" in seg5_empty),',
         '        # ★★ **batch 847 起换靶**：★ 现在盯的是**页面级**的未实测入口\n'
         '        #   ⟹ ⟹ 那一页的内容**根本就没测过** ⟹ ⟹ 说明**必须**写「未实测」\n'
         '        #   ⟹ ⟹ （段级那条写「已实测」是因为**整段**测过、只是没实现 ⟹ ⟹ 语义不同）\n'
         '        "★第五段_空态说明里写了「未实测」": bool(seg5_empty and "未实测" in seg5_empty),\n'
         '        "★第五段_空态说明里写了「已实测」": bool(seg5_empty and "已实测" in seg5_empty),'),
        ('         and bool(seg5_empty) and s7["★第五段_空态说明里写了「已实测」"]',
         '         and bool(seg5_empty) and s7["★第五段_空态说明里写了「未实测」"]\n'
         '         and not s7["★第五段_空态说明里写了「已实测」"]'),
        ('        "S7 ★★★ **仍未实现的那一块显示空态说明、不编造控件**：★ **batch 846 起盯"\n'
         '        "「左列第五段（音色音调）」**（★ 第四段在 846 已实现 ⟹ ⟹ 未实现的只剩一段）"\n'
         '        "⟹ 点第五段 ⟹ **页签数 %d**（★ 源站实测：页签行**只在「脸部精修」段存在**）＋ 滑杆 %d 条 "',
         '        "S7 ★★★ **未实测的那一页显示空态说明、不编造控件**：★ **batch 847 起换靶**——"\n'
         '        "左列五段**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯"\n'
         '        "**第五段里那一页内容未实测的页签**（「我的音色」）"\n'
         '        "⟹ 点第五段 ⟹ 再点「我的音色」⟹ **页签数 %d**（★ 源站实测：页签行**只在「脸部精修」段存在**）＋ 滑杆 %d 条 "'),
    ]),
    # ── verify-liblib-batch841.py ──
    (G841, [
        ('    seg5 = rt.get("C2_第五段") or {}',
         '    seg5 = rt.get("C2_第五段_AI生成") or {}'),
        ('        "★第五段_空态说明里还写着「未实测」": bool(seg5_empty and "未实测" in seg5_empty),',
         '        # ★★ **batch 847 起换靶**：★ 现在盯的是**页面级**的未实测入口\n'
         '        #   ⟹ ⟹ 那一页的内容**根本就没测过** ⟹ ⟹ 说明**必须**写「未实测」\n'
         '        "★第五段_空态说明里写了「未实测」": bool(seg5_empty and "未实测" in seg5_empty),'),
        ('         and not s5["★第五段_空态说明里还写着「未实测」"]\n'
         '         and s5["★第五段_空态说明里写了「已实测」"]',
         '         and s5["★第五段_空态说明里写了「未实测」"]\n'
         '         and not s5["★第五段_空态说明里写了「已实测」"]'),
        ('        "S5 ★★★ **仍未实现的那一块仍显示空态说明、0 控件**（★ batch 846 起盯"\n'
         '        "「左列第五段」：第四段在 846 已实现 ⟹ ⟹ 未实现的只剩一段）；★ 且说明文案**不再**说"\n'
         '        "「未实测」—— ★ 那两段**已经实测过**了（raw 已入库）⟹ ⟹ 继续写「未实测」"\n'
         '        "就是**假陈述** ⟹ ⟹ 改成「已实测，但属后续批次」",',
         '        "S5 ★★★ **未实测的那一页仍显示空态说明、0 控件**（★ batch 847 起换靶：左列五段"\n'
         '        "**全部实现** ⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯**第五段里那一页"\n'
         '        "内容未实测的页签**（「AI 生成」）；★ 且说明文案**要**写「未实测」—— ★ 那一页"\n'
         '        "的控件**根本就没测过** ⟹ ⟹ 写「已实测」才是**假陈述**",'),
    ]),
    # ── verify-liblib-batch842.py ──
    (G842, [
        ('    seg5 = rt.get("D2_第五段") or {}',
         '    seg5 = rt.get("D2_第四段_服装") or {}'),
        ('        "★第五段_空态说明里还写着「未实测」": bool(seg5_empty and "未实测" in seg5_empty),',
         '        # ★★ **batch 847 起换靶**：★ 现在盯的是**页面级**的未实测入口\n'
         '        #   ⟹ ⟹ 那一页的内容**根本就没测过** ⟹ ⟹ 说明**必须**写「未实测」\n'
         '        "★第五段_空态说明里写了「未实测」": bool(seg5_empty and "未实测" in seg5_empty),'),
        ('         and not s6["★第五段_空态说明里还写着「未实测」"]\n'
         '         and s6["★第五段_空态说明里写了「已实测」"]',
         '         and s6["★第五段_空态说明里写了「未实测」"]\n'
         '         and not s6["★第五段_空态说明里写了「已实测」"]'),
        ('        "S6 ★★★ **仍未实现的那一块仍是空态说明**（★ batch 846 起盯「左列第五段」："\n'
         '        "第四段在 846 已实现 ⟹ ⟹ 六个页签全部有内容了）⟹ **页签数 %d**（★ 源站实测："\n'
         '        "页签行**只在「脸部精修」段存在**）＋ 滑杆 %d 条 ＋ 卡片 %d 张；★ 且文案**不再**说"\n'
         '        "「未实测」—— ★ 那四段**已经实测过**了（raw 已入库）⟹ ⟹ 继续写「未实测」"\n'
         '        "就是**假陈述** ⟹ ⟹ 改成「已实测，但属后续批次」"',
         '        "S6 ★★★ **未实测的那一页仍是空态说明**（★ batch 847 起换靶：左列五段**全部实现**"\n'
         '        "⟹ ⟹ 「仍未实现的那一段」**没有靶子了** ⟹ ⟹ 改盯**第四段里那一页内容未实测的"\n'
         '        "子页签**（「服装」））⟹ **页签数 %d**（★ 源站实测：页签行**只在「脸部精修」段存在**）"\n'
         '        "＋ 滑杆 %d 条 ＋ 卡片 %d 张；★ 且文案**要**写「未实测」—— ★ 那一页的控件"\n'
         '        "**根本就没测过** ⟹ ⟹ 写「已实测」才是**假陈述**"'),
    ]),
    # ── verify-liblib-batch843.py ──
    (G843, [
        ('    other = rt.get("D_第五段") or {}',
         '    other = rt.get("D_第四段_AI生成") or {}'),
        ('        "S6 ★★★ **结构事实**：源站实测**页签行只在「脸部精修」段存在** ⟹ ⟹ "\n'
         '        "点左列**第五段**（音色音调）⟹ **页签数 %s** ＋ 0 张卡 ＋ 出现空态说明；切回「脸部精修」⟹ "',
         '        "S6 ★★★ **结构事实**：源站实测**页签行只在「脸部精修」段存在** ⟹ ⟹ "\n'
         '        "点左列**第四段**（服装造型）⟹ 再点「AI 生成」子页签 ⟹ **页签数 %s** ＋ 0 张卡 ＋ 出现空态说明；切回「脸部精修」⟹ "'),
    ]),
]


def main() -> int:
    dry = "--dry-run" in sys.argv
    bad = 0
    for rel, pairs in EDITS:
        path = ROOT / rel
        src = path.read_text(encoding="utf-8")
        for old, new in pairs:
            n = src.count(old)
            if n != 1:
                print("✘ %s ⟹ 锚点命中 %d 处（应为 1）：%r" % (rel, n, old[:70]))
                bad += 1
                continue
            src = src.replace(old, new, 1)
        if not dry:
            path.write_text(src, encoding="utf-8")
            print("  ✔ %s（%d 处）" % (rel, len(pairs)))
    if dry:
        print("（dry-run ⟹ **没有写任何文件**）")
        return 1 if bad else 0
    if bad:
        print("✘ 有 %d 处锚点不对 ⟹ 已改动的部分**请人工核对**" % bad)
        return 1
    print("\n迁移完成 ⟹ 现在必须**四个门禁全绿**：")
    for g in (G840, G841, G842, G843):
        r = subprocess.run([sys.executable, str(ROOT / g)], capture_output=True,
                           text=True, timeout=3600, cwd=str(ROOT))
        tail = [ln for ln in (r.stdout or "").strip().split("\n") if ln.strip()]
        print("  %-42s rc=%s  %s" % (g, r.returncode, tail[-1] if tail else ""))
        if r.returncode != 0:
            print("    " + "\n    ".join(tail[-14:]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
